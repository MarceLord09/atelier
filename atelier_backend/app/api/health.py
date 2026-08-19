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
            "llm": settings.llm_provider,
            "model": settings.groq_model if settings.llm_provider == "live" else "template",
            "vision": settings.gemini_model
            if settings.llm_provider == "live" and settings.gemini_api_key
            else "template",
        }

    return router
