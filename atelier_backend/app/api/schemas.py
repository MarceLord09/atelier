from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.entities import Asset, Audit, Brand, User
from app.domain.enums import AssetKind, AssetStatus, Role


class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    role: Role
    home_route: str

    @classmethod
    def from_entity(cls, user: User) -> "UserPublic":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            home_route=user.home_route,
        )


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=2, max_length=80)
    role: Role | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=16)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=16)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserPublic


class ComposeBrandRequest(BaseModel):
    product: str = Field(min_length=2, max_length=200)
    audience: str = Field(min_length=2, max_length=200)
    tone: str = Field(min_length=2, max_length=40)
    promise: str = Field(min_length=2, max_length=400)
    forbidden: list[str] = Field(default_factory=list)
    name: str | None = Field(default=None, max_length=80)


class BrandResponse(BaseModel):
    id: UUID
    name: str
    product: str
    audience: str
    tone: str
    promise: str
    manifesto: str
    forbidden: list[str]
    colors: list[str]
    voice_do: list[str]
    voice_dont: list[str]
    indexed: bool
    created_at: datetime
    kit_complete: bool = False
    current: bool = False

    @classmethod
    def from_entity(
        cls,
        brand: Brand,
        *,
        kit_complete: bool = False,
        current: bool = False,
    ) -> "BrandResponse":
        return cls(
            id=brand.id,
            name=brand.name,
            product=brand.product,
            audience=brand.audience,
            tone=brand.tone,
            promise=brand.promise,
            manifesto=brand.manifesto,
            forbidden=list(brand.forbidden),
            colors=list(brand.colors),
            voice_do=list(brand.voice_do),
            voice_dont=list(brand.voice_dont),
            indexed=brand.indexed_at is not None,
            created_at=brand.created_at,
            kit_complete=kit_complete,
            current=current,
        )


class GenerateRequest(BaseModel):
    kind: AssetKind = AssetKind.PRODUCT_SHEET
    prompt: str = Field(default="", max_length=240)


class AssetResponse(BaseModel):
    id: UUID
    brand_id: UUID
    kind: AssetKind
    title: str
    body: str
    status: AssetStatus
    citations: list[str]
    model: str
    created_at: datetime

    @classmethod
    def from_entity(cls, asset: Asset) -> "AssetResponse":
        return cls(
            id=asset.id,
            brand_id=asset.brand_id,
            kind=asset.kind,
            title=asset.title,
            body=asset.body,
            status=asset.status,
            citations=list(asset.citations),
            model=asset.model,
            created_at=asset.created_at,
        )


class ReviewRequest(BaseModel):
    decision: Literal["APPROVE", "REJECT"]


class FindingResponse(BaseModel):
    n: int
    title: str
    detail: str
    rule: str
    ok: bool = False
    x: float | None = None
    y: float | None = None


class AuditResponse(BaseModel):
    id: UUID
    brand_id: UUID
    passed: bool
    findings: list[FindingResponse]
    model: str
    image_name: str
    created_at: datetime

    @classmethod
    def from_entity(cls, audit: Audit) -> "AuditResponse":
        return cls(
            id=audit.id,
            brand_id=audit.brand_id,
            passed=audit.passed,
            findings=[FindingResponse(**finding.__dict__) for finding in audit.findings],
            model=audit.model,
            image_name=audit.image_name,
            created_at=audit.created_at,
        )
