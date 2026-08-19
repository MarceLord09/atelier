from fastapi import APIRouter

from app.api.v1 import auth, brands, creative, governance

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(brands.router)
api_router.include_router(creative.router)
api_router.include_router(governance.router)
