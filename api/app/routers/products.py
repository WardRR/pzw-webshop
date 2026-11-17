from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_role
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import product_service

router = APIRouter()


@router.get("", response_model=list[ProductRead])
async def list_products(
    search: str | None = Query(default=None, min_length=1, max_length=100),
    in_stock: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.list_products(
        db,
        search=search,
        in_stock_only=in_stock,
        limit=limit,
        offset=offset,
    )


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    return await product_service.get_product(db, product_id)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    return await product_service.create_product(db, body)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    return await product_service.update_product(db, product_id, body)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    await product_service.deactivate_product(db, product_id)