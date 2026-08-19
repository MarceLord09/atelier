from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.domain.enums import AssetKind, AssetStatus, Role


HOME_BY_ROLE: dict[Role, str] = {
    Role.CREATOR: "atelier",
    Role.APPROVER_A: "desk",
    Role.APPROVER_B: "lightbox",
}


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    name: str
    role: Role
    is_active: bool = True

    @property
    def home_route(self) -> str:
        return HOME_BY_ROLE[self.role]


@dataclass(frozen=True)
class BrandBrief:
    product: str
    audience: str
    tone: str
    promise: str
    forbidden: tuple[str, ...]
    name: str | None = None


@dataclass(frozen=True)
class BrandBook:
    name: str
    manifesto: str
    tone: str
    colors: tuple[str, ...]
    voice_do: tuple[str, ...]
    voice_dont: tuple[str, ...]
    chunks: tuple["Chunk", ...]


@dataclass(frozen=True)
class Chunk:
    heading: str
    content: str


@dataclass(frozen=True)
class Brand:
    id: UUID
    name: str
    product: str
    audience: str
    tone: str
    promise: str
    manifesto: str
    forbidden: tuple[str, ...]
    colors: tuple[str, ...]
    voice_do: tuple[str, ...]
    voice_dont: tuple[str, ...]
    created_by: UUID
    indexed_at: datetime | None
    created_at: datetime


@dataclass(frozen=True)
class Asset:
    id: UUID
    brand_id: UUID
    created_by: UUID
    kind: AssetKind
    title: str
    body: str
    status: AssetStatus
    citations: tuple[str, ...]
    model: str
    created_at: datetime


@dataclass(frozen=True)
class Finding:
    n: int
    title: str
    detail: str
    rule: str


@dataclass(frozen=True)
class Audit:
    id: UUID
    brand_id: UUID
    created_by: UUID
    passed: bool
    findings: tuple[Finding, ...]
    model: str
    created_at: datetime
    image_name: str = ""


@dataclass(frozen=True)
class AuditDraft:
    passed: bool
    findings: tuple[Finding, ...]
    model: str


@dataclass
class GeneratedCopy:
    title: str
    body: str
    model: str
    citations: tuple[str, ...] = field(default_factory=tuple)
