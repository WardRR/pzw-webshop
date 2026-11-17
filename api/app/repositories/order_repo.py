from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem


async def get_by_id(db: AsyncSession, order_id: int) -> Order | None:
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_orders(
    db: AsyncSession,
    *,
    user_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.id.desc())
    )
    if user_id is not None:
        stmt = stmt.where(Order.user_id == user_id)
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_order(
    db: AsyncSession,
    *,
    user_id: int,
    total_price: Decimal,
    items_data: list[dict],
) -> Order:
    order = Order(
        user_id=user_id,
        total_price=total_price,
        items=[OrderItem(**item) for item in items_data],
    )
    db.add(order)
    await db.flush()
    return await get_by_id(db, order.id)  # type: ignore[return-value]