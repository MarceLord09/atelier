from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.exceptions import NotFoundError, UnprocessableError
from app.domain.entities import Asset, Audit, Brand, BrandBrief, User
from app.domain.enums import AssetKind, AssetStatus
from app.domain.ports import (
    AssetRepository,
    AuditRepository,
    BrandComposer,
    BrandRepository,
    CopyGenerator,
    UnitOfWork,
    VisionAuditor,
)


class BrandService:
    def __init__(
        self,
        *,
        brands: BrandRepository,
        composer: BrandComposer,
        uow: UnitOfWork,
    ) -> None:
        self._brands = brands
        self._composer = composer
        self._uow = uow

    async def compose(self, actor: User, brief: BrandBrief) -> Brand:
        book = await self._composer.compose(brief)
        current = await self._brands.get_current()
        now = datetime.now(UTC)
        brand = Brand(
            id=current.id if current else uuid4(),
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
            created_at=current.created_at if current else now,
        )
        saved = await self._brands.save(brand)
        await self._brands.replace_chunks(saved.id, book.chunks)
        await self._uow.commit()
        return saved

    async def current(self) -> Brand:
        brand = await self._brands.get_current()
        if brand is None:
            raise NotFoundError("No hay un manual de marca activo.")
        return brand


class CreativeService:
    def __init__(
        self,
        *,
        brands: BrandRepository,
        assets: AssetRepository,
        generator: CopyGenerator,
        uow: UnitOfWork,
    ) -> None:
        self._brands = brands
        self._assets = assets
        self._generator = generator
        self._uow = uow

    async def generate(self, actor: User, *, kind: AssetKind, prompt: str) -> Asset:
        brand = await self._brands.get_current()
        if brand is None or brand.indexed_at is None:
            raise UnprocessableError(
                "El motor creativo consulta el manual antes de escribir. Compón el DNA primero.",
                code="manual_required",
            )
        context = await self._brands.search_chunks(brand.id, prompt or brand.product)
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
        asset = Asset(
            id=uuid4(),
            brand_id=brand.id,
            created_by=actor.id,
            kind=kind,
            title=copy.title,
            body=copy.body,
            status=AssetStatus.PENDING,
            citations=copy.citations or tuple(chunk.heading for chunk in context),
            model=copy.model,
            created_at=datetime.now(UTC),
        )
        saved = await self._assets.add(asset)
        await self._uow.commit()
        return saved

    async def list_assets(self, *, status: AssetStatus | None = None) -> list[Asset]:
        return await self._assets.list(status=status)


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
        return await self._assets.list(status=status)

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
        brand = await self._brands.get_current()
        if brand is None or brand.indexed_at is None:
            raise UnprocessableError(
                "La auditoría contrasta contra el manual activo. Compón el DNA primero.",
                code="manual_required",
            )
        if not image:
            raise UnprocessableError("La imagen está vacía.")
        draft = await self._auditor.audit(brand=brand, image_name=image_name, image=image)
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
        return saved
