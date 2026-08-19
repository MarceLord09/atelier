from fastapi import APIRouter

from app.api.deps import BrandServiceDep, CurrentUser, CreatorUser
from app.api.schemas import BrandResponse, ComposeBrandRequest
from app.domain.entities import BrandBrief

router = APIRouter(prefix="/brands", tags=["brands"])


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
    return BrandResponse.from_entity(brand)


@router.get("/current")
async def current_brand(user: CurrentUser, service: BrandServiceDep) -> BrandResponse:
    _ = user
    brand = await service.current()
    return BrandResponse.from_entity(brand)
