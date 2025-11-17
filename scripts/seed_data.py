import asyncio

from sqlalchemy.future import select

from backend.auth.security import get_password_hash
from backend.config.constants import UserRole
from backend.models.database import async_session_maker
from backend.models.models import User


async def main():
    async with async_session_maker() as db:
        # admin
        result = await db.execute(select(User).filter(User.username == "admin_demo"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                username="admin_demo",
                email="admin_demo@test.com",
                hashed_password=get_password_hash("AdminPass1"),
                role=UserRole.ADMIN,
                is_active=True,
                balance=0.0,
                daily_limit=1000.0,
            )
            db.add(admin)
        # customer
        result = await db.execute(select(User).filter(User.username == "cust_demo"))
        cust = result.scalar_one_or_none()
        if not cust:
            cust = User(
                username="cust_demo",
                email="cust_demo@test.com",
                hashed_password=get_password_hash("CustPass1"),
                role=UserRole.CUSTOMER,
                is_active=True,
                balance=800.0,
                daily_limit=1000.0,
            )
            db.add(cust)
        await db.commit()
    print("Seeded: admin_demo / cust_demo")


if __name__ == "__main__":
    asyncio.run(main())
