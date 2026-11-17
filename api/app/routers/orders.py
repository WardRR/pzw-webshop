from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead, OrderStatusUpdate
from app.services import order_service

router = APIRouter()


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await order_service.create_order(db, current_user, body)


@router.get("", response_model=list[OrderRead])
async def list_orders(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await order_service.list_orders(
        db, current_user, limit=limit, offset=offset
    )


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await order_service.get_order(db, order_id, current_user)


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await order_service.cancel_order(db, order_id, current_user)


@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: int,
    body: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    return await order_service.update_order_status(db, order_id, body.status)
