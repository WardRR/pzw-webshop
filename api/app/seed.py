"""Početni podatci za razvoj i obranu webshopa.

Pokreće se iz mape api/, nakon alembic upgrade head:
    python -m app.seed

Idempotentna skripta: smije se pokrenuti bilo koliko puta bez duplikata.
"""

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models.product import Product
from app.models.user import User

ADMIN_ACCOUNT = ("admin@webshop.hr", "admin123", "admin")

DEMO_CUSTOMERS = [
    ("kupac1@webshop.hr", "kupac123", "customer"),
    ("kupac2@webshop.hr", "kupac123", "customer"),
]

DEMO_PRODUCTS = [
    (
        "Mehanička tipkovnica",
        "Kompaktna 75% tipkovnica, RGB osvjetljenje",
        Decimal("89.99"),
        15,
    ),
    ("Bežični miš", "Ergonomski optički miš, USB-C punjenje", Decimal("45.50"), 25),
    ('27" IPS Monitor', "QHD 1440p, 165Hz, DisplayPort i HDMI", Decimal("279.00"), 8),
    (
        "USB-C Hub 7-u-1",
        "HDMI, 3x USB 3.0, SD čitač i PD punjenje",
        Decimal("34.90"),
        30,
    ),
    (
        "Studijske slušalice",
        "Zatvorene over-ear slušalice za rad",
        Decimal("119.00"),
        12,
    ),
]


async def get_or_create_user(
    session: AsyncSession, username: str, password: str, role: str
) -> User:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        session.add(user)
        await session.flush()
    return user


async def get_or_create_product(
    session: AsyncSession,
    name: str,
    description: str,
    price: Decimal,
    stock: int,
) -> Product:
    result = await session.execute(select(Product).where(Product.name == name))
    product = result.scalar_one_or_none()
    if product is None:
        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
        )
        session.add(product)
        await session.flush()
    return product


async def seed() -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await get_or_create_user(session, *ADMIN_ACCOUNT)
        for account in DEMO_CUSTOMERS:
            await get_or_create_user(session, *account)
        for item in DEMO_PRODUCTS:
            await get_or_create_product(session, *item)

    await engine.dispose()
    print("Seed webshopa uspješno dovršen.")
    print(f"  admin:  {ADMIN_ACCOUNT[0]} / {ADMIN_ACCOUNT[1]}")
    for username, password, _ in DEMO_CUSTOMERS:
        print(f"  kupac:  {username} / {password}")
    print(f"  proizvoda u katalogu: {len(DEMO_PRODUCTS)}")


if __name__ == "__main__":
    asyncio.run(seed())
