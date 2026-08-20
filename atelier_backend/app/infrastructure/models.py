from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, String, Text, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.domain.enums import AssetKind, AssetStatus, Role


def _uuid() -> UUID:
    return uuid4()


class UserRow(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=_uuid, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=320)
    name: str = Field(max_length=120)
    hashed_password: str
    role: Role
    is_active: bool = True
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))


class RefreshTokenRow(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: UUID = Field(default_factory=_uuid, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(unique=True, index=True, max_length=64)
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    revoked_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))


class BrandRow(SQLModel, table=True):
    __tablename__ = "brands"

    id: UUID = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(max_length=120)
    product: str = Field(sa_column=Column(Text, nullable=False))
    audience: str = Field(sa_column=Column(Text, nullable=False))
    tone: str = Field(max_length=80)
    promise: str = Field(sa_column=Column(Text, nullable=False))
    manifesto: str = Field(sa_column=Column(Text, nullable=False))
    forbidden: list[str] = Field(sa_column=Column(JSON, nullable=False))
    colors: list[str] = Field(sa_column=Column(JSON, nullable=False))
    voice_do: list[str] = Field(sa_column=Column(JSON, nullable=False))
    voice_dont: list[str] = Field(sa_column=Column(JSON, nullable=False))
    created_by: UUID = Field(foreign_key="users.id")
    indexed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    activated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class ChunkRow(SQLModel, table=True):
    __tablename__ = "brand_chunks"

    id: UUID = Field(default_factory=_uuid, primary_key=True)
    brand_id: UUID = Field(foreign_key="brands.id", index=True)
    heading: str = Field(max_length=160)
    content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))


class AssetRow(SQLModel, table=True):
    __tablename__ = "assets"

    id: UUID = Field(default_factory=_uuid, primary_key=True)
    brand_id: UUID = Field(foreign_key="brands.id", index=True)
    created_by: UUID = Field(foreign_key="users.id")
    kind: AssetKind
    title: str = Field(max_length=200)
    body: str = Field(sa_column=Column(Text, nullable=False))
    status: AssetStatus = Field(
        default=AssetStatus.PENDING,
        sa_column=Column(String(16), nullable=False, index=True),
    )
    citations: list[str] = Field(sa_column=Column(JSON, nullable=False))
    model: str = Field(max_length=80)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))


class AuditRow(SQLModel, table=True):
    __tablename__ = "audits"

    id: UUID = Field(default_factory=_uuid, primary_key=True)
    brand_id: UUID = Field(foreign_key="brands.id", index=True)
    created_by: UUID = Field(foreign_key="users.id")
    passed: bool
    findings: list[dict] = Field(sa_column=Column(JSON, nullable=False))
    model: str = Field(max_length=80)
    image_name: str = Field(default="", max_length=255)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))


class ReviewRow(SQLModel, table=True):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("asset_id", "reviewer_id", name="uq_review_asset_reviewer"),)

    id: UUID = Field(default_factory=_uuid, primary_key=True)
    asset_id: UUID = Field(foreign_key="assets.id", index=True)
    reviewer_id: UUID = Field(foreign_key="users.id")
    decision: str = Field(max_length=16)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
