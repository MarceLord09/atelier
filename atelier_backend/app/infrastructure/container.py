from sqlmodel.ext.asyncio.session import AsyncSession

from app.application.auth import AuthService
from app.application.services import BrandService, CreativeService, GovernanceService
from app.core.config import Settings
from app.core.security import JwtIssuer, PasswordHasher
from app.infrastructure.adapters import (
    TemplateBrandComposer,
    TemplateCopyGenerator,
    TemplateVisionAuditor,
)
from app.infrastructure.repositories import (
    SqlAlchemyUnitOfWork,
    SqlAssetRepository,
    SqlAuditRepository,
    SqlBrandRepository,
    SqlRefreshTokenRepository,
    SqlUserRepository,
)


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.hasher = PasswordHasher()
        self.jwt = JwtIssuer(
            secret=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
            access_minutes=settings.access_token_minutes,
        )
        self.composer = TemplateBrandComposer()
        self.generator = TemplateCopyGenerator()
        self.auditor = TemplateVisionAuditor()

    def auth_service(self, session: AsyncSession) -> AuthService:
        return AuthService(
            users=SqlUserRepository(session),
            tokens=SqlRefreshTokenRepository(session),
            uow=SqlAlchemyUnitOfWork(session),
            hasher=self.hasher,
            jwt=self.jwt,
            refresh_days=self.settings.refresh_token_days,
            allow_self_assign_role=self.settings.allow_self_assign_role,
            is_production=self.settings.is_production,
        )

    def brand_service(self, session: AsyncSession) -> BrandService:
        return BrandService(
            brands=SqlBrandRepository(session),
            composer=self.composer,
            uow=SqlAlchemyUnitOfWork(session),
        )

    def creative_service(self, session: AsyncSession) -> CreativeService:
        brands = SqlBrandRepository(session)
        return CreativeService(
            brands=brands,
            assets=SqlAssetRepository(session),
            generator=self.generator,
            uow=SqlAlchemyUnitOfWork(session),
        )

    def governance_service(self, session: AsyncSession) -> GovernanceService:
        return GovernanceService(
            assets=SqlAssetRepository(session),
            brands=SqlBrandRepository(session),
            audits=SqlAuditRepository(session),
            auditor=self.auditor,
            uow=SqlAlchemyUnitOfWork(session),
        )
