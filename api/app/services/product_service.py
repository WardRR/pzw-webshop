from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.product import Product
from app.repositories import product_repo
from app.schemas.product import ProductCreate, ProductUpdate


async def list_products(
    db: AsyncSession,
    *,
    include_inactive: bool = False,
    search: str | None = None,
    in_stock_only: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> list[Product]:
    return await product_repo.list_products(
        db,
        include_inactive=include_inactive,
        search=search,
        in_stock_only=in_stock_only,
        limit=limit,
        offset=offset,
    )


async def get_product(
    db: AsyncSession, product_id: int, *, include_inactive: bool = False
) -> Product:
    product = await product_repo.get_by_id(db, product_id)
    if product is None or (not include_inactive and not product.is_active):
        raise AppError("not_found", "Proizvod nije pronađen", 404)
    return product


async def create_product(db: AsyncSession, payload: ProductCreate) -> Product:
    return await product_repo.create(db, payload.model_dump())


async def update_product(
    db: AsyncSession, product_id: int, payload: ProductUpdate
) -> Product:
    product = await get_product(db, product_id, include_inactive=True)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return product
    return await product_repo.update(db, product, changes)


async def deactivate_product(db: AsyncSession, product_id: int) -> None:
    product = await get_product(db, product_id, include_inactive=True)
    await product_repo.update(db, product, {"is_active": False})
