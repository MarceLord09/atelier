from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Query, UploadFile

from app.api.deps import ApproverAUser, ApproverBUser, GovernanceServiceDep
from app.api.schemas import AssetResponse, AuditResponse, ReviewRequest
from app.core.exceptions import UnprocessableError
from app.domain.enums import AssetStatus

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/queue")
async def approval_queue(
    user: ApproverAUser,
    service: GovernanceServiceDep,
    status: Annotated[AssetStatus | None, Query()] = None,
) -> list[AssetResponse]:
    _ = user
    assets = await service.queue(status=status)
    return [AssetResponse.from_entity(asset) for asset in assets]


@router.post("/assets/{asset_id}/review")
async def review_asset(
    asset_id: UUID,
    body: ReviewRequest,
    user: ApproverAUser,
    service: GovernanceServiceDep,
) -> AssetResponse:
    _ = user
    asset = await service.review(asset_id=asset_id, approve=body.decision == "APPROVE")
    return AssetResponse.from_entity(asset)


@router.post("/audit")
async def audit_image(
    user: ApproverBUser,
    service: GovernanceServiceDep,
    image: Annotated[UploadFile, File()],
) -> AuditResponse:
    data = await image.read()
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise UnprocessableError("Solo se aceptan JPG, PNG o WEBP.")
    result = await service.audit(
        user,
        image_name=image.filename or "upload",
        image=data,
    )
    return AuditResponse.from_entity(result)
