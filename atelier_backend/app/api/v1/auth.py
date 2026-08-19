from fastapi import APIRouter

from app.api.deps import AuthServiceDep, CurrentUser
from app.api.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, service: AuthServiceDep) -> TokenResponse:
    user, access, refresh, expires_in = await service.register(
        email=str(body.email),
        password=body.password,
        name=body.name,
        role=body.role,
    )
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=expires_in,
        user=UserPublic.from_entity(user),
    )


@router.post("/login")
async def login(body: LoginRequest, service: AuthServiceDep) -> TokenResponse:
    user, access, refresh, expires_in = await service.login(
        email=str(body.email),
        password=body.password,
    )
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=expires_in,
        user=UserPublic.from_entity(user),
    )


@router.post("/refresh")
async def refresh(body: RefreshRequest, service: AuthServiceDep) -> TokenResponse:
    user, access, refresh_token, expires_in = await service.refresh(body.refresh_token)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=UserPublic.from_entity(user),
    )


@router.post("/logout", status_code=204)
async def logout(body: LogoutRequest, service: AuthServiceDep) -> None:
    await service.logout(body.refresh_token)


@router.get("/me")
async def me(user: CurrentUser) -> UserPublic:
    return UserPublic.from_entity(user)
