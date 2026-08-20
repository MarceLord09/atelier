from enum import StrEnum


class Role(StrEnum):
    CREATOR = "CREATOR"
    APPROVER_A = "APPROVER_A"
    APPROVER_B = "APPROVER_B"


class AssetKind(StrEnum):
    PRODUCT_SHEET = "PRODUCT_SHEET"
    VIDEO_SCRIPT = "VIDEO_SCRIPT"
    IMAGE_PROMPT = "IMAGE_PROMPT"


class AssetStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReviewDecision(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
