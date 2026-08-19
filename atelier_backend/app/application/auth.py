import asyncio
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID, uuid4

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import JwtIssuer, PasswordHasher
from app.domain.entities import User
from app.domain.enums import Role
from app.domain.ports import RefreshTokenRepository, UnitOfWork, UserRepository


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepository,
        tokens: RefreshTokenRepository,
        uow: UnitOfWork,
        hasher: PasswordHasher,
        jwt: JwtIssuer,
        refresh_days: int,
        allow_self_assign_role: bool,
        is_production: bool,
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._uow = uow
        self._hasher = hasher
        self._jwt = jwt
        self._refresh_days = refresh_days
        self._allow_self_assign_role = allow_self_assign_role
        self._is_production = is_production

    async def register(
        self,
        *,
        email: str,
        password: str,
        name: str,
        role: Role | None,
    ) -> tuple[User, str, str, int]:
        if await self._users.get_by_email(email) is not None:
            raise ConflictError("Ese correo ya está registrado.")
        assigned = self._resolve_role(role)
        hashed = await asyncio.to_thread(self._hasher.hash, password)
        user = await self._users.add(
            email=email.lower(),
            name=name.strip(),
            role=assigned,
            hashed_password=hashed,
        )
        access, refresh, expires_in = await self._issue_session(user)
        await self._uow.commit()
        return user, access, refresh, expires_in

    async def login(self, *, email: str, password: str) -> tuple[User, str, str, int]:
        user = await self._users.get_by_email(email.lower())
        hashed = await self._users.get_password_hash(email.lower())
        valid = bool(hashed) and await asyncio.to_thread(self._hasher.verify, password, hashed or "")
        if user is None or not user.is_active or not valid:
            raise UnauthorizedError("Correo o contraseña incorrectos.")
        access, refresh, expires_in = await self._issue_session(user)
        await self._uow.commit()
        return user, access, refresh, expires_in

    async def refresh(self, refresh_token: str) -> tuple[User, str, str, int]:
        user = await self._user_from_refresh(refresh_token)
        await self._tokens.revoke(_hash_token(refresh_token))
        access, refresh, expires_in = await self._issue_session(user)
        await self._uow.commit()
        return user, access, refresh, expires_in

    async def logout(self, refresh_token: str) -> None:
        await self._tokens.revoke(_hash_token(refresh_token))
        await self._uow.commit()

    async def me(self, user_id: UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Sesión inválida.")
        return user

    def _resolve_role(self, role: Role | None) -> Role:
        if role is None:
            return Role.CREATOR
        if self._allow_self_assign_role and not self._is_production:
            return role
        return Role.CREATOR

    async def _issue_session(self, user: User) -> tuple[str, str, int]:
        access = self._jwt.issue_access(user_id=user.id, role=user.role)
        refresh = uuid4().hex + uuid4().hex
        expires_at = datetime.now(UTC) + timedelta(days=self._refresh_days)
        await self._tokens.add(
            user_id=user.id,
            token_hash=_hash_token(refresh),
            expires_at=expires_at,
        )
        return access, refresh, self._jwt.access_seconds

    async def _user_from_refresh(self, refresh_token: str) -> User:
        user_id = await self._tokens.get_user_id(_hash_token(refresh_token))
        if user_id is None:
            raise UnauthorizedError("Refresh token inválido.")
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Refresh token inválido.")
        return user


def _hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
