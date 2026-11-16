from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


async def list_products(
    db: AsyncSession,
    *,
    include_inactive: bool = False,
    search: str | None = None,
    in_stock_only: bool = False,
) -> list[Product]:
    stmt = select(Product).order_by(Product.id)
    if not include_inactive:
        stmt = stmt.where(Product.is_active.is_(True))
    
    if search:
        stmt = stmt.where(Product.name.ilike(f"%{search}%"))
    
    if in_stock_only:
        stmt = stmt.where(Product.stock > 0)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, data: dict) -> Product:
    product = Product(**data)
    db.add(product)
    await db.flush()
    return product


async def update(db: AsyncSession, product: Product, data: dict) -> Product:
    for key, value in data.items():
        setattr(product, key, value)
    await db.flush()
    return product