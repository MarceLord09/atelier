from fastapi import APIRouter

from app.api.deps import CreativeServiceDep, CreatorUser
from app.api.schemas import AssetResponse, GenerateRequest

router = APIRouter(prefix="/creative", tags=["creative"])


@router.post("/generate")
async def generate_asset(
    body: GenerateRequest,
    user: CreatorUser,
    service: CreativeServiceDep,
) -> AssetResponse:
    asset = await service.generate(user, kind=body.kind, prompt=body.prompt)
    return AssetResponse.from_entity(asset)


@router.get("/assets")
async def list_assets(user: CreatorUser, service: CreativeServiceDep) -> list[AssetResponse]:
    _ = user
    assets = await service.list_assets()
    return [AssetResponse.from_entity(asset) for asset in assets]
