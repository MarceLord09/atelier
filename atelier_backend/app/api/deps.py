from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.application.auth import AuthService
from app.application.services import BrandService, CreativeService, GovernanceService
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.domain.entities import User
from app.domain.enums import Role
from app.infrastructure.container import Container
from app.infrastructure.repositories import SqlUserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory = request.app.state.session_factory
    async with factory() as session:
        yield session


def get_container(request: Request) -> Container:
    return request.app.state.container


SessionDep = Annotated[AsyncSession, Depends(get_session)]
ContainerDep = Annotated[Container, Depends(get_container)]


def get_auth_service(session: SessionDep, container: ContainerDep) -> AuthService:
    return container.auth_service(session)


def get_brand_service(session: SessionDep, container: ContainerDep) -> BrandService:
    return container.brand_service(session)


def get_creative_service(session: SessionDep, container: ContainerDep) -> CreativeService:
    return container.creative_service(session)


def get_governance_service(session: SessionDep, container: ContainerDep) -> GovernanceService:
    return container.governance_service(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
BrandServiceDep = Annotated[BrandService, Depends(get_brand_service)]
CreativeServiceDep = Annotated[CreativeService, Depends(get_creative_service)]
GovernanceServiceDep = Annotated[GovernanceService, Depends(get_governance_service)]


async def get_current_user(
    session: SessionDep,
    container: ContainerDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Necesitas iniciar sesión.")
    payload = container.jwt.decode_access(credentials.credentials)
    try:
        user_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Token inválido.") from exc
    user = await SqlUserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Sesión inválida.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: Role):
    async def _guard(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ForbiddenError("Tu rol no tiene permiso para este módulo.")
        return user

    return _guard


CreatorUser = Annotated[User, Depends(require_roles(Role.CREATOR))]
ApproverAUser = Annotated[User, Depends(require_roles(Role.APPROVER_A))]
ApproverBUser = Annotated[User, Depends(require_roles(Role.APPROVER_B))]
