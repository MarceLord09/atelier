from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.exceptions import UnauthorizedError
from app.domain.enums import Role

TokenType = Literal["access"]


class PasswordHasher:
    def __init__(self) -> None:
        self._pwd = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._pwd.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        return self._pwd.verify(password, hashed)


class JwtIssuer:
    def __init__(self, *, secret: str, algorithm: str, access_minutes: int) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._access_minutes = access_minutes

    @property
    def access_seconds(self) -> int:
        return self._access_minutes * 60

    def issue_access(self, *, user_id: UUID, role: Role) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "role": role.value,
            "typ": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._access_minutes)).timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_access(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError as exc:
            raise UnauthorizedError("El token expiró.") from exc
        except jwt.InvalidTokenError as extra:
            raise UnauthorizedError("Token inválido.") from extra
        if payload.get("typ") != "access":
            raise UnauthorizedError("Token inválido.")
        return payload
