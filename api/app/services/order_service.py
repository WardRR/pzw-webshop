from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.order import Order
from app.models.user import User
from app.repositories import order_repo, product_repo
from app.schemas.order import OrderCreate


async def create_order(
    db: AsyncSession, current_user: User, payload: OrderCreate
) -> Order:
    # Spajamo duplikate istog product_id ako ih kupac pošalje u više redaka
    quantities: dict[int, int] = {}
    for item in payload.items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity

    total_price = Decimal("0.00")
    items_data: list[dict] = []

    for product_id, qty in quantities.items():
        product = await product_repo.get_by_id(db, product_id)
        if product is None or not product.is_active:
            raise AppError("not_found", f"Proizvod {product_id} nije pronađen", 404)
        if product.stock < qty:
            raise AppError(
                "insufficient_stock",
                f"Nedovoljna zaliha za proizvod '{product.name}' (dostupno: {product.stock})",
                409,
            )

        product.stock -= qty
        line_total = product.price * qty
        total_price += line_total
        items_data.append(
            {
                "product_id": product.id,
                "quantity": qty,
                "unit_price": product.price,
            }
        )

    await db.flush()
    return await order_repo.create_order(
        db,
        user_id=current_user.id,
        total_price=total_price,
        items_data=items_data,
    )


async def list_orders(db: AsyncSession, current_user: User) -> list[Order]:
    if current_user.role == "admin":
        return await order_repo.list_orders(db)
    return await order_repo.list_orders(db, user_id=current_user.id)


async def get_order(
    db: AsyncSession, order_id: int, current_user: User
) -> Order:
    order = await order_repo.get_by_id(db, order_id)
    if order is None:
        raise AppError("not_found", "Narudžba nije pronađena", 404)
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise AppError("forbidden", "Nemate pristup ovoj narudžbi", 403)
    return order


async def _restock_order_items(db: AsyncSession, order: Order) -> None:
    for item in order.items:
        product = await product_repo.get_by_id(db, item.product_id)
        if product is not None:
            product.stock += item.quantity


async def cancel_order(
    db: AsyncSession, order_id: int, current_user: User
) -> Order:
    order = await get_order(db, order_id, current_user)
    if order.status != "pending":
        raise AppError(
            "invalid_status",
            "Moguće je otkazati samo narudžbu u statusu 'pending'",
            409,
        )

    now = datetime.now(timezone.utc)
    created = order.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    if now - created > timedelta(hours=24):
        raise AppError(
            "cancellation_expired",
            "Rok od 24 sata za otkazivanje narudžbe je istekao",
            409,
        )

    await _restock_order_items(db, order)
    order.status = "cancelled"
    await db.flush()
    return await order_repo.get_by_id(db, order.id)  # type: ignore[return-value]


async def update_order_status(
    db: AsyncSession, order_id: int, new_status: str
) -> Order:
    order = await order_repo.get_by_id(db, order_id)
    if order is None:
        raise AppError("not_found", "Narudžba nije pronađena", 404)

    if order.status == "cancelled" and new_status != "cancelled":
        raise AppError(
            "invalid_status",
            "Otkazanu narudžbu nije moguće ponovno aktivirati",
            409,
        )

    if order.status != "cancelled" and new_status == "cancelled":
        await _restock_order_items(db, order)

    order.status = new_status
    await db.flush()
    return await order_repo.get_by_id(db, order.id)  # type: ignore[return-value]
