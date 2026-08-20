import asyncio

from app.core.demo import DEMO_PASSWORD, DEMO_USERS
from app.core.security import PasswordHasher
from app.domain.enums import Role
from app.domain.ports import UnitOfWork, UserRepository


async def seed_demo_users(
    *,
    users: UserRepository,
    hasher: PasswordHasher,
    uow: UnitOfWork,
) -> int:
    created = 0
    for item in DEMO_USERS:
        email = item["email"].lower()
        if await users.get_by_email(email) is not None:
            continue
        hashed = await asyncio.to_thread(hasher.hash, DEMO_PASSWORD)
        await users.add(
            email=email,
            name=item["name"],
            role=Role(item["role"]),
            hashed_password=hashed,
        )
        created += 1
    if created:
        await uow.commit()
    return created
