from decimal import Decimal

from freezegun import freeze_time

from tests.conftest import auth_header


async def test_create_order_decrements_stock_and_calculates_total(
    client, admin_auth, customer_auth
):
    p = await client.post(
        "/products",
        headers=admin_auth,
        json={"name": "Slušalice", "price": "50.00", "stock": 10},
    )
    product_id = p.json()["id"]

    order_resp = await client.post(
        "/orders",
        headers=customer_auth,
        json={"items": [{"product_id": product_id, "quantity": 3}]},
    )
    assert order_resp.status_code == 201
    order = order_resp.json()
    assert Decimal(order["total_price"]) == Decimal("150.00")
    assert order["status"] == "pending"

    prod_after = await client.get(f"/products/{product_id}")
    assert prod_after.json()["stock"] == 7


async def test_insufficient_stock_returns_409_without_changing_stock(
    client, admin_auth, customer_auth
):
    p = await client.post(
        "/products",
        headers=admin_auth,
        json={"name": "SSD 1TB", "price": "80.00", "stock": 2},
    )
    product_id = p.json()["id"]

    resp = await client.post(
        "/orders",
        headers=customer_auth,
        json={"items": [{"product_id": product_id, "quantity": 5}]},
    )
    assert resp.status_code == 409

    prod_after = await client.get(f"/products/{product_id}")
    assert prod_after.json()["stock"] == 2


async def test_customer_cannot_view_other_users_order(
    client, admin_auth, customer_auth, customer_b_user
):
    p = await client.post(
        "/products",
        headers=admin_auth,
        json={"name": "Podloga", "price": "15.00", "stock": 5},
    )
    order_resp = await client.post(
        "/orders",
        headers=customer_auth,
        json={"items": [{"product_id": p.json()["id"], "quantity": 1}]},
    )
    order_id = order_resp.json()["id"]

    customer_b_auth = await auth_header(client, customer_b_user.username, "kupac123")
    forbidden_resp = await client.get(
        f"/orders/{order_id}", headers=customer_b_auth
    )
    assert forbidden_resp.status_code == 403


async def test_cancel_order_restocks_and_blocks_after_24h_with_freezegun(
    client, admin_auth, customer_user
):
    p = await client.post(
        "/products",
        headers=admin_auth,
        json={"name": "Web kamera", "price": "40.00", "stock": 4},
    )
    product_id = p.json()["id"]

    # 1. Narudžba stvorena u 10:00, otkazana nakon 23 sata -> prolazi (200)
    with freeze_time("2026-11-17 10:00:00+00:00"):
        headers_t0 = await auth_header(client, customer_user.username, "kupac123")
        o1 = await client.post(
            "/orders",
            headers=headers_t0,
            json={"items": [{"product_id": product_id, "quantity": 2}]},
        )
        assert o1.status_code == 201
        o1_id = o1.json()["id"]

    with freeze_time("2026-11-18 09:00:00+00:00"):
        headers_t23 = await auth_header(client, customer_user.username, "kupac123")
        cancel_resp = await client.post(
            f"/orders/{o1_id}/cancel", headers=headers_t23
        )
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"

    prod_after = await client.get(f"/products/{product_id}")
    assert prod_after.json()["stock"] == 4

    # 2. Druga narudžba stvorena u 10:00, pokušaj otkazivanja nakon 24h 1min -> 409
    with freeze_time("2026-11-17 10:00:00+00:00"):
        headers_t0_2 = await auth_header(client, customer_user.username, "kupac123")
        o2 = await client.post(
            "/orders",
            headers=headers_t0_2,
            json={"items": [{"product_id": product_id, "quantity": 1}]},
        )
        assert o2.status_code == 201
        o2_id = o2.json()["id"]

    with freeze_time("2026-11-18 10:01:00+00:00"):
        headers_t24 = await auth_header(client, customer_user.username, "kupac123")
        late_cancel = await client.post(
            f"/orders/{o2_id}/cancel", headers=headers_t24
        )
        assert late_cancel.status_code == 409
        assert late_cancel.json()["code"] == "cancellation_expired"
