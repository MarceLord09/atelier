from fastapi import APIRouter
from uuid import UUID

from app.api.deps import BrandServiceDep, CurrentUser, CreatorUser
from app.api.schemas import BrandResponse, ComposeBrandRequest
from app.domain.entities import BrandBrief

router = APIRouter(prefix="/brands", tags=["brands"])


async def _to_response(service: BrandServiceDep, brand, *, current: bool) -> BrandResponse:
    return BrandResponse.from_entity(
        brand,
        kit_complete=await service.kit_complete(brand.id),
        current=current,
    )


@router.post("/compose")
async def compose_brand(
    body: ComposeBrandRequest,
    user: CreatorUser,
    service: BrandServiceDep,
) -> BrandResponse:
    brief = BrandBrief(
        product=body.product.strip(),
        audience=body.audience.strip(),
        tone=body.tone.strip(),
        promise=body.promise.strip(),
        forbidden=tuple(word.strip() for word in body.forbidden if word.strip()),
        name=body.name.strip() if body.name else None,
    )
    brand = await service.compose(user, brief)
    return await _to_response(service, brand, current=True)


@router.get("/current")
async def current_brand(user: CurrentUser, service: BrandServiceDep) -> BrandResponse:
    _ = user
    brand = await service.current()
    return await _to_response(service, brand, current=True)


@router.get("/catalog")
async def list_brands(user: CurrentUser, service: BrandServiceDep) -> list[BrandResponse]:
    _ = user
    brands = await service.list_brands()
    current = brands[0] if brands else None
    return [
        await _to_response(service, brand, current=current is not None and brand.id == current.id)
        for brand in brands
    ]


@router.post("/{brand_id}/activate")
async def activate_brand(
    brand_id: UUID,
    user: CurrentUser,
    service: BrandServiceDep,
) -> BrandResponse:
    _ = user
    brand = await service.activate(brand_id)
    return await _to_response(service, brand, current=True)
