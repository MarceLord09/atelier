from fastapi import APIRouter

from app.core.config import Settings


def build_health_router(settings: Settings) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "atelier_backend",
            "environment": settings.environment,
        }

    return router
