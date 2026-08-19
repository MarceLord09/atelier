from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def make_client(tmp_path) -> TestClient:
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{tmp_path}/test.db",
        jwt_secret="test-secret-key-which-is-long-enough-32",
        environment="development",
        allow_self_assign_role=True,
    )
    return TestClient(create_app(settings))


def register(client: TestClient, email: str, role: str = "CREATOR", name: str = "Lucía Torres"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "secret123",
            "name": name,
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
