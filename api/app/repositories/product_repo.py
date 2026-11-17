from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


async def list_products(
    db: AsyncSession,
    *,
    include_inactive: bool = False,
    search: str | None = None,
    in_stock_only: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> list[Product]:
    stmt = select(Product).order_by(Product.id)
    if not include_inactive:
        stmt = stmt.where(Product.is_active.is_(True))
    if search:
        stmt = stmt.where(Product.name.ilike(f"%{search.strip()}%"))
    if in_stock_only:
        stmt = stmt.where(Product.stock > 0)
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, product_id: int) -> Product | None:
    return await db.get(Product, product_id)


async def create(db: AsyncSession, data: dict) -> Product:
    product = Product(**data)
    db.add(product)
    await db.flush()
    return product


async def update(db: AsyncSession, product: Product, data: dict) -> Product:
    for field, value in data.items():
        setattr(product, field, value)
    await db.flush()
    return product
