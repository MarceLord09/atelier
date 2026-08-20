from app.domain.enums import Role

DEMO_PASSWORD = "Atelier2026!"

DEMO_USERS: tuple[dict[str, str], ...] = (
    {
        "email": "lucia@atelier.app",
        "name": "Lucía Torres",
        "role": Role.CREATOR.value,
    },
    {
        "email": "mateo@atelier.app",
        "name": "Mateo Salazar",
        "role": Role.APPROVER_A.value,
    },
    {
        "email": "ines@atelier.app",
        "name": "Inés Vargas",
        "role": Role.APPROVER_B.value,
    },
)
