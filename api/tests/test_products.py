from decimal import Decimal


async def test_admin_can_create_and_list_products(client, admin_auth):
    resp = await client.post(
        "/products",
        headers=admin_auth,
        json={
            "name": "Mehanička tipkovnica",
            "description": "RGB, smeđi switchevi",
            "price": "89.99",
            "stock": 10,
        },
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["name"] == "Mehanička tipkovnica"
    assert Decimal(created["price"]) == Decimal("89.99")
    assert created["is_active"] is True

    list_resp = await client.get("/products")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


async def test_customer_cannot_create_update_or_delete_product(
    client, admin_auth, customer_auth
):
    create_resp = await client.post(
        "/products",
        headers=customer_auth,
        json={"name": "Miš", "price": "25.00", "stock": 5},
    )
    assert create_resp.status_code == 403

    admin_create = await client.post(
        "/products",
        headers=admin_auth,
        json={"name": "Miš", "price": "25.00", "stock": 5},
    )
    product_id = admin_create.json()["id"]

    patch_resp = await client.patch(
        f"/products/{product_id}",
        headers=customer_auth,
        json={"price": "19.99"},
    )
    assert patch_resp.status_code == 403

    del_resp = await client.delete(f"/products/{product_id}", headers=customer_auth)
    assert del_resp.status_code == 403


async def test_search_and_soft_delete_product(client, admin_auth):
    r1 = await client.post(
        "/products",
        headers=admin_auth,
        json={"name": "Monitor 27", "price": "249.00", "stock": 3},
    )
    await client.post(
        "/products",
        headers=admin_auth,
        json={"name": "USB-C kabel", "price": "9.50", "stock": 0},
    )
    monitor_id = r1.json()["id"]

    search_resp = await client.get("/products", params={"search": "monitor"})
    assert len(search_resp.json()) == 1

    stock_resp = await client.get("/products", params={"in_stock": True})
    assert len(stock_resp.json()) == 1

    del_resp = await client.delete(f"/products/{monitor_id}", headers=admin_auth)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/products/{monitor_id}")
    assert get_resp.status_code == 404


async def test_products_pagination(client, admin_auth):
    for i in range(1, 6):
        await client.post(
            "/products",
            headers=admin_auth,
            json={"name": f"Proizvod {i}", "price": "10.00", "stock": 5},
        )

    page1 = await client.get("/products", params={"limit": 2, "offset": 0})
    assert page1.status_code == 200
    assert [p["name"] for p in page1.json()] == ["Proizvod 1", "Proizvod 2"]

    page2 = await client.get("/products", params={"limit": 2, "offset": 2})
    assert page2.status_code == 200
    assert [p["name"] for p in page2.json()] == ["Proizvod 3", "Proizvod 4"]
