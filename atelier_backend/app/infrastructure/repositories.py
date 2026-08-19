from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import select
from sqlalchemy import delete
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.entities import Asset, Audit, Brand, Chunk, Finding, User
from app.domain.enums import AssetKind, AssetStatus, Role
from app.infrastructure.models import (
    AssetRow,
    AuditRow,
    BrandRow,
    ChunkRow,
    RefreshTokenRow,
    UserRow,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.exec(select(UserRow).where(UserRow.email == email.lower()))
        row = result.first()
        return _to_user(row) if row else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        row = await self._session.get(UserRow, user_id)
        return _to_user(row) if row else None

    async def add(self, *, email: str, name: str, role: Role, hashed_password: str) -> User:
        row = UserRow(
            email=email.lower(),
            name=name,
            role=role,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC),
        )
        self._session.add(row)
        await self._session.flush()
        return _to_user(row)

    async def get_password_hash(self, email: str) -> str | None:
        result = await self._session.exec(select(UserRow).where(UserRow.email == email.lower()))
        row = result.first()
        return row.hashed_password if row else None


class SqlRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, *, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self._session.add(
            RefreshTokenRow(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                created_at=datetime.now(UTC),
            )
        )

    async def get_user_id(self, token_hash: str) -> UUID | None:
        result = await self._session.exec(
            select(RefreshTokenRow).where(RefreshTokenRow.token_hash == token_hash)
        )
        row = result.first()
        if row is None or row.revoked_at is not None:
            return None
        if row.expires_at.tzinfo is None:
            expires = row.expires_at.replace(tzinfo=UTC)
        else:
            expires = row.expires_at
        if expires <= datetime.now(UTC):
            return None
        return row.user_id

    async def revoke(self, token_hash: str) -> None:
        result = await self._session.exec(
            select(RefreshTokenRow).where(RefreshTokenRow.token_hash == token_hash)
        )
        row = result.first()
        if row is None or row.revoked_at is not None:
            return
        row.revoked_at = datetime.now(UTC)
        self._session.add(row)

    async def revoke_all(self, user_id: UUID) -> None:
        result = await self._session.exec(
            select(RefreshTokenRow).where(
                RefreshTokenRow.user_id == user_id, RefreshTokenRow.revoked_at.is_(None)
            )
        )
        now = datetime.now(UTC)
        for row in result.all():
            row.revoked_at = now
            self._session.add(row)


class SqlBrandRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_current(self) -> Brand | None:
        result = await self._session.exec(select(BrandRow).order_by(BrandRow.created_at.desc()))
        row = result.first()
        return _to_brand(row) if row else None

    async def get(self, brand_id: UUID) -> Brand | None:
        row = await self._session.get(BrandRow, brand_id)
        return _to_brand(row) if row else None

    async def save(self, brand: Brand) -> Brand:
        row = await self._session.get(BrandRow, brand.id)
        if row is None:
            row = BrandRow(id=brand.id, created_at=brand.created_at)
            self._session.add(row)
        row.name = brand.name
        row.product = brand.product
        row.audience = brand.audience
        row.tone = brand.tone
        row.promise = brand.promise
        row.manifesto = brand.manifesto
        row.forbidden = list(brand.forbidden)
        row.colors = list(brand.colors)
        row.voice_do = list(brand.voice_do)
        row.voice_dont = list(brand.voice_dont)
        row.created_by = brand.created_by
        row.indexed_at = brand.indexed_at
        await self._session.flush()
        return _to_brand(row)

    async def replace_chunks(self, brand_id: UUID, chunks: Sequence[Chunk]) -> None:
        await self._session.exec(delete(ChunkRow).where(ChunkRow.brand_id == brand_id))
        now = datetime.now(UTC)
        for chunk in chunks:
            self._session.add(
                ChunkRow(
                    brand_id=brand_id,
                    heading=chunk.heading,
                    content=chunk.content,
                    created_at=now,
                )
            )

    async def list_chunks(self, brand_id: UUID) -> list[Chunk]:
        result = await self._session.exec(select(ChunkRow).where(ChunkRow.brand_id == brand_id))
        return [Chunk(heading=row.heading, content=row.content) for row in result.all()]

    async def search_chunks(self, brand_id: UUID, query: str, k: int = 4) -> list[Chunk]:
        chunks = await self.list_chunks(brand_id)
        if not chunks:
            return []
        terms = {term.lower() for term in query.split() if len(term) > 2}
        if not terms:
            return chunks[:k]

        def score(chunk: Chunk) -> int:
            haystack = f"{chunk.heading} {chunk.content}".lower()
            return sum(1 for term in terms if term in haystack)

        ranked = sorted(chunks, key=score, reverse=True)
        return ranked[:k]


class SqlAssetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, asset: Asset) -> Asset:
        row = AssetRow(
            id=asset.id,
            brand_id=asset.brand_id,
            created_by=asset.created_by,
            kind=asset.kind,
            title=asset.title,
            body=asset.body,
            status=asset.status,
            citations=list(asset.citations),
            model=asset.model,
            created_at=asset.created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _to_asset(row)

    async def get(self, asset_id: UUID) -> Asset | None:
        row = await self._session.get(AssetRow, asset_id)
        return _to_asset(row) if row else None

    async def list(self, *, status: AssetStatus | None = None) -> list[Asset]:
        statement = select(AssetRow).order_by(AssetRow.created_at.desc())
        if status is not None:
            statement = statement.where(AssetRow.status == status)
        result = await self._session.exec(statement)
        return [_to_asset(row) for row in result.all()]

    async def set_status(self, asset_id: UUID, status: AssetStatus) -> Asset:
        row = await self._session.get(AssetRow, asset_id)
        if row is None:
            raise LookupError(asset_id)
        row.status = status
        await self._session.flush()
        return _to_asset(row)


class SqlAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, audit: Audit) -> Audit:
        row = AuditRow(
            id=audit.id,
            brand_id=audit.brand_id,
            created_by=audit.created_by,
            passed=audit.passed,
            findings=[finding.__dict__ for finding in audit.findings],
            model=audit.model,
            image_name=audit.image_name,
            created_at=audit.created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _to_audit(row)


def _to_user(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        name=row.name,
        role=Role(row.role),
        is_active=row.is_active,
    )


def _to_brand(row: BrandRow) -> Brand:
    return Brand(
        id=row.id,
        name=row.name,
        product=row.product,
        audience=row.audience,
        tone=row.tone,
        promise=row.promise,
        manifesto=row.manifesto,
        forbidden=tuple(row.forbidden or ()),
        colors=tuple(row.colors or ()),
        voice_do=tuple(row.voice_do or ()),
        voice_dont=tuple(row.voice_dont or ()),
        created_by=row.created_by,
        indexed_at=row.indexed_at,
        created_at=row.created_at,
    )


def _to_asset(row: AssetRow) -> Asset:
    return Asset(
        id=row.id,
        brand_id=row.brand_id,
        created_by=row.created_by,
        kind=AssetKind(row.kind),
        title=row.title,
        body=row.body,
        status=AssetStatus(row.status),
        citations=tuple(row.citations or ()),
        model=row.model,
        created_at=row.created_at,
    )


def _to_audit(row: AuditRow) -> Audit:
    findings = tuple(
        Finding(
            n=int(item["n"]),
            title=str(item["title"]),
            detail=str(item["detail"]),
            rule=str(item["rule"]),
        )
        for item in (row.findings or [])
    )
    return Audit(
        id=row.id,
        brand_id=row.brand_id,
        created_by=row.created_by,
        passed=row.passed,
        findings=findings,
        model=row.model,
        created_at=row.created_at,
        image_name=row.image_name,
    )
