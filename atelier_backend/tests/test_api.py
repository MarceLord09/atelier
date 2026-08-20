from tests.conftest import auth_header, make_client, register


def test_health(tmp_path):
    client = make_client(tmp_path)
    with client:
        response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["langfuse"] == "off"


def test_register_login_me_and_refresh(tmp_path):
    client = make_client(tmp_path)
    with client:
        created = register(client, "creator@atelier.app")
        assert created["user"]["role"] == "CREATOR"
        assert created["user"]["home_route"] == "atelier"
        me = client.get("/api/v1/auth/me", headers=auth_header(created["access_token"]))
        assert me.status_code == 200
        assert me.json()["email"] == "creator@atelier.app"

        login = client.post(
            "/api/v1/auth/login",
            json={"email": "creator@atelier.app", "password": "secret123"},
        )
        assert login.status_code == 200

        rotated = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": created["refresh_token"]},
        )
        assert rotated.status_code == 200
        reused = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": created["refresh_token"]},
        )
        assert reused.status_code == 401


def test_login_rejects_wrong_password(tmp_path):
    client = make_client(tmp_path)
    with client:
        register(client, "creator@atelier.app")
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "creator@atelier.app", "password": "nope-nope"},
        )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_duplicate_email(tmp_path):
    client = make_client(tmp_path)
    with client:
        register(client, "creator@atelier.app")
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "creator@atelier.app",
                "password": "secret123",
                "name": "Otra",
            },
        )
    assert response.status_code == 409


def test_compose_and_generate_require_auth_and_role(tmp_path):
    client = make_client(tmp_path)
    with client:
        creator = register(client, "creator@atelier.app", "CREATOR")
        approver = register(
            client,
            "approver.a@atelier.app",
            "APPROVER_A",
            name="Mateo Salazar",
        )
        denied = client.post(
            "/api/v1/brands/compose",
            headers=auth_header(approver["access_token"]),
            json={
                "product": "Crocante de kiwicha",
                "audience": "Pausa simple",
                "tone": "cercano",
                "promise": "Lo bueno de aquí.",
                "forbidden": ["milagroso"],
            },
        )
        assert denied.status_code == 403

        before = client.post(
            "/api/v1/creative/generate",
            headers=auth_header(creator["access_token"]),
            json={"kind": "PRODUCT_SHEET", "prompt": "Ficha"},
        )
        assert before.status_code == 422

        composed = client.post(
            "/api/v1/brands/compose",
            headers=auth_header(creator["access_token"]),
            json={
                "product": "Crocante de kiwicha con cacao",
                "audience": "Personas que buscan una pausa simple",
                "tone": "cercano",
                "promise": "Lo bueno de aquí, para todos los días.",
                "forbidden": ["milagroso", "superalimento"],
                "name": "Kiwicha Viva",
            },
        )
        assert composed.status_code == 200
        assert composed.json()["indexed"] is True

        generated = client.post(
            "/api/v1/creative/generate",
            headers=auth_header(creator["access_token"]),
            json={"kind": "PRODUCT_SHEET", "prompt": "Crocante de Kiwicha"},
        )
        assert generated.status_code == 200
        assert generated.json()["status"] == "PENDING"
        assert generated.json()["citations"]

        image_prompt = client.post(
            "/api/v1/creative/generate",
            headers=auth_header(creator["access_token"]),
            json={"kind": "IMAGE_PROMPT", "prompt": "Packshot de mesa"},
        )
        assert image_prompt.status_code == 200
        assert image_prompt.json()["kind"] == "IMAGE_PROMPT"

        queue = client.get(
            "/api/v1/governance/queue?status=PENDING",
            headers=auth_header(approver["access_token"]),
        )
        assert queue.status_code == 200
        kinds = {item["kind"] for item in queue.json()}
        assert "PRODUCT_SHEET" in kinds
        assert "IMAGE_PROMPT" in kinds
        first_count = len(queue.json())

        second = client.post(
            "/api/v1/brands/compose",
            headers=auth_header(creator["access_token"]),
            json={
                "product": "Alitas a la parrilla",
                "audience": "Bar de barrio",
                "tone": "cercano",
                "promise": "Sabor de casa.",
                "forbidden": ["milagroso"],
                "name": "Primitivo",
            },
        )
        assert second.status_code == 200
        assert second.json()["id"] != composed.json()["id"]

        isolated = client.get(
            "/api/v1/governance/queue?status=PENDING",
            headers=auth_header(approver["access_token"]),
        )
        assert isolated.status_code == 200
        assert isolated.json() == []

        catalog = client.get(
            "/api/v1/brands/catalog",
            headers=auth_header(approver["access_token"]),
        )
        assert catalog.status_code == 200
        assert len(catalog.json()) == 2

        switched = client.post(
            f"/api/v1/brands/{composed.json()['id']}/activate",
            headers=auth_header(approver["access_token"]),
        )
        assert switched.status_code == 200
        restored = client.get(
            "/api/v1/governance/queue?status=PENDING",
            headers=auth_header(approver["access_token"]),
        )
        assert len(restored.json()) == first_count
