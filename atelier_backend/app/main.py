from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import build_health_router
from app.api.v1 import api_router
from app.application.seed import seed_demo_users
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.infrastructure.container import Container
from app.infrastructure.database import build_engine, build_session_factory, create_schema
from app.core.observability import tracer
from app.infrastructure.repositories import SqlAlchemyUnitOfWork, SqlUserRepository


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    if settings.is_production and settings.jwt_secret.startswith("dev-only"):
        raise RuntimeError("Define JWT_SECRET antes de arrancar en producción.")
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    container = Container(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        tracer.configure(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        await create_schema(engine)
        if settings.seed_demo_users:
            async with session_factory() as session:
                await seed_demo_users(
                    users=SqlUserRepository(session),
                    hasher=container.hasher,
                    uow=SqlAlchemyUnitOfWork(session),
                )
        yield
        tracer.flush()
        await engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.container = container

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"https://([a-z0-9-]+\.)*(vercel\.app|onrender\.com|workers\.dev|pages\.dev)",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    app.include_router(build_health_router(settings))
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
