from datetime import UTC, datetime
from uuid import UUID, uuid4
import unicodedata

from app.core.exceptions import NotFoundError, UnprocessableError
from app.domain.entities import Asset, Audit, Brand, BrandBrief, User
from app.domain.enums import AssetKind, AssetStatus
from app.domain.ports import (
    AssetRepository,
    AuditRepository,
    BrandComposer,
    BrandRepository,
    CopyGenerator,
    Embedder,
    UnitOfWork,
    VisionAuditor,
)
from app.core.observability import tracer

KIT_KINDS = (AssetKind.PRODUCT_SHEET, AssetKind.VIDEO_SCRIPT, AssetKind.IMAGE_PROMPT)


def _name_key(value: str) -> str:
    stripped = unicodedata.normalize("NFKD", value.strip())
    return "".join(char for char in stripped if not unicodedata.combining(char)).casefold()


class BrandService:
    def __init__(
        self,
        *,
        brands: BrandRepository,
        assets: AssetRepository,
        composer: BrandComposer,
        embedder: Embedder,
        uow: UnitOfWork,
    ) -> None:
        self._brands = brands
        self._assets = assets
        self._composer = composer
        self._embedder = embedder
        self._uow = uow

    async def compose(self, actor: User, brief: BrandBrief) -> Brand:
        with tracer.span("brand.compose", product=brief.product, tone=brief.tone) as span:
            book = await self._composer.compose(brief)
            current = await self._brands.get_current()
            now = datetime.now(UTC)
            reuse = (
                current is not None
                and _name_key(book.name) == _name_key(current.name)
            )
            brand = Brand(
                id=current.id if reuse and current else uuid4(),
                name=book.name,
                product=brief.product,
                audience=brief.audience,
                tone=brief.tone,
                promise=brief.promise,
                manifesto=book.manifesto,
                forbidden=brief.forbidden,
                colors=book.colors,
                voice_do=book.voice_do,
                voice_dont=book.voice_dont,
                created_by=actor.id,
                indexed_at=now,
                created_at=current.created_at if reuse and current else now,
            )
            saved = await self._brands.save(brand)
            texts = [f"{chunk.heading}\n{chunk.content}" for chunk in book.chunks]
            embeddings = await self._embedder.embed(texts)
            await self._brands.replace_chunks(saved.id, book.chunks, embeddings)
            await self._uow.commit()
            span.update(
                input={"product": brief.product, "audience": brief.audience, "tone": brief.tone},
                output={
                    "brand": saved.name,
                    "chunks": [chunk.heading for chunk in book.chunks],
                    "embedder": self._embedder.name,
                    "replaced": reuse,
                },
                metadata={"duration_ms": span.duration_ms, "user": str(actor.id)},
            )
            tracer.flush()
            return saved

    async def current(self) -> Brand:
        brand = await self._brands.get_current()
        if brand is None:
            raise NotFoundError("No hay un manual de marca activo.")
        return brand

    async def list_brands(self) -> list[Brand]:
        return await self._brands.list()

    async def activate(self, brand_id: UUID) -> Brand:
        brand = await self._brands.activate(brand_id)
        if brand is None:
            raise NotFoundError("No existe esa marca.")
        await self._uow.commit()
        return brand

    async def kit_complete(self, brand_id: UUID) -> bool:
        assets = await self._assets.list(brand_id=brand_id)
        latest: dict[AssetKind, AssetStatus] = {}
        for asset in assets:
            latest.setdefault(asset.kind, asset.status)
        return all(latest.get(kind) == AssetStatus.APPROVED for kind in KIT_KINDS)


class CreativeService:
    def __init__(
        self,
        *,
        brands: BrandRepository,
        assets: AssetRepository,
        generator: CopyGenerator,
        embedder: Embedder,
        uow: UnitOfWork,
    ) -> None:
        self._brands = brands
        self._assets = assets
        self._generator = generator
        self._embedder = embedder
        self._uow = uow

    async def generate(self, actor: User, *, kind: AssetKind, prompt: str) -> Asset:
        with tracer.span("creative.generate", kind=kind.value) as span:
            brand = await self._brands.get_current()
            if brand is None or brand.indexed_at is None:
                raise UnprocessableError(
                    "El motor creativo consulta el manual antes de escribir. Compón el DNA primero.",
                    code="manual_required",
                )
            query = prompt or brand.product
            query_embedding = (await self._embedder.embed([query]))[0]
            context = await self._brands.search_chunks(
                brand.id,
                query,
                query_embedding=query_embedding,
            )
            if not context:
                raise UnprocessableError(
                    "No hay fragmentos indexados del manual. Vuelve a componer el DNA.",
                    code="retrieval_empty",
                )
            copy = await self._generator.generate(
                kind=kind,
                brand=brand,
                context=context,
                prompt=prompt,
            )
            citations = copy.citations or tuple(chunk.heading for chunk in context)
            asset = Asset(
                id=uuid4(),
                brand_id=brand.id,
                created_by=actor.id,
                kind=kind,
                title=copy.title,
                body=copy.body,
                status=AssetStatus.PENDING,
                citations=citations,
                model=copy.model,
                created_at=datetime.now(UTC),
            )
            saved = await self._assets.add(asset)
            await self._uow.commit()
            span.update(
                input={"kind": kind.value, "prompt": prompt, "query": query},
                output={
                    "title": copy.title,
                    "model": copy.model,
                    "citations": list(citations),
                },
                metadata={
                    "duration_ms": span.duration_ms,
                    "retrieved": [chunk.heading for chunk in context],
                    "embedder": self._embedder.name,
                },
            )
            tracer.flush()
            return saved

    async def list_assets(self, *, status: AssetStatus | None = None) -> list[Asset]:
        brand = await self._brands.get_current()
        if brand is None:
            return []
        return await self._assets.list(brand_id=brand.id, status=status)


class GovernanceService:
    def __init__(
        self,
        *,
        assets: AssetRepository,
        brands: BrandRepository,
        audits: AuditRepository,
        auditor: VisionAuditor,
        uow: UnitOfWork,
    ) -> None:
        self._assets = assets
        self._brands = brands
        self._audits = audits
        self._auditor = auditor
        self._uow = uow

    async def queue(self, status: AssetStatus | None = None) -> list[Asset]:
        brand = await self._brands.get_current()
        if brand is None:
            return []
        return await self._assets.list(brand_id=brand.id, status=status)

    async def review(self, *, asset_id: UUID, approve: bool) -> Asset:
        asset = await self._assets.get(asset_id)
        if asset is None:
            raise NotFoundError("No existe esa pieza.")
        if asset.status != AssetStatus.PENDING:
            raise UnprocessableError("Esa pieza ya fue revisada.")
        status = AssetStatus.APPROVED if approve else AssetStatus.REJECTED
        updated = await self._assets.set_status(asset.id, status)
        await self._uow.commit()
        return updated

    async def audit(self, actor: User, *, image_name: str, image: bytes) -> Audit:
        with tracer.span("governance.audit", image_name=image_name) as span:
            brand = await self._brands.get_current()
            if brand is None or brand.indexed_at is None:
                raise UnprocessableError(
                    "La auditoría contrasta contra el manual activo. Compón el DNA primero.",
                    code="manual_required",
                )
            if not image:
                raise UnprocessableError("La imagen está vacía.")
            context = await self._brands.list_chunks(brand.id)
            draft = await self._auditor.audit(
                brand=brand,
                image_name=image_name,
                image=image,
                context=context,
            )
            record = Audit(
                id=uuid4(),
                brand_id=brand.id,
                created_by=actor.id,
                passed=draft.passed,
                findings=draft.findings,
                model=draft.model,
                created_at=datetime.now(UTC),
                image_name=image_name,
            )
            saved = await self._audits.add(record)
            await self._uow.commit()
            span.update(
                input={"image_name": image_name, "bytes": len(image), "brand": brand.name},
                output={
                    "passed": draft.passed,
                    "findings": [finding.title for finding in draft.findings],
                    "model": draft.model,
                },
                metadata={
                    "duration_ms": span.duration_ms,
                    "manual_chunks": [chunk.heading for chunk in context],
                },
            )
            tracer.flush()
            return saved
