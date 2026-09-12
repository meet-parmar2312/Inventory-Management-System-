import pytest


def test_stock_adjustment_positive(client, manager_headers, sample_data):
    prod_id = sample_data["product"].id
    wh_id = sample_data["warehouse_a"].id

    response = client.post(
        "/api/v1/inventory/adjust",
        headers=manager_headers,
        json={
            "product_id": prod_id,
            "warehouse_id": wh_id,
            "quantity": 25,
            "reason": "Restock batch #104",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 75
    assert data["available_quantity"] == 75


def test_stock_adjustment_negative_exceeding_stock(client, manager_headers, sample_data):
    prod_id = sample_data["product"].id
    wh_id = sample_data["warehouse_a"].id

    response = client.post(
        "/api/v1/inventory/adjust",
        headers=manager_headers,
        json={
            "product_id": prod_id,
            "warehouse_id": wh_id,
            "quantity": -100,
            "reason": "Inventory write-off",
        },
    )
    assert response.status_code == 409
    assert "Cannot adjust" in response.json()["message"] or "Insufficient stock" in response.json()["error"]


def test_stock_adjustment_forbidden_for_staff(client, staff_headers, sample_data):
    response = client.post(
        "/api/v1/inventory/adjust",
        headers=staff_headers,
        json={
            "product_id": sample_data["product"].id,
            "warehouse_id": sample_data["warehouse_a"].id,
            "quantity": 10,
        },
    )
    assert response.status_code == 403


def test_warehouse_transfer_success(client, admin_headers, sample_data):
    prod_id = sample_data["product"].id
    src_wh = sample_data["warehouse_a"].id
    dst_wh = sample_data["warehouse_b"].id

    response = client.post(
        "/api/v1/inventory/transfer",
        headers=admin_headers,
        json={
            "product_id": prod_id,
            "source_warehouse_id": src_wh,
            "destination_warehouse_id": dst_wh,
            "quantity": 15,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    src_inv = next(i for i in data if i["warehouse_id"] == src_wh)
    dst_inv = next(i for i in data if i["warehouse_id"] == dst_wh)

    assert src_inv["quantity"] == 35
    assert dst_inv["quantity"] == 35


def test_warehouse_transfer_insufficient_stock(client, admin_headers, sample_data):
    prod_id = sample_data["product"].id
    src_wh = sample_data["warehouse_a"].id
    dst_wh = sample_data["warehouse_b"].id

    response = client.post(
        "/api/v1/inventory/transfer",
        headers=admin_headers,
        json={
            "product_id": prod_id,
            "source_warehouse_id": src_wh,
            "destination_warehouse_id": dst_wh,
            "quantity": 999,
        },
    )
    assert response.status_code == 409
    assert "Insufficient stock" in response.json()["message"]


def test_low_stock_endpoint(client, staff_headers, sample_data, manager_headers):
    prod_id = sample_data["product"].id
    wh_b = sample_data["warehouse_b"].id

    client.post(
        "/api/v1/inventory/adjust",
        headers=manager_headers,
        json={
            "product_id": prod_id,
            "warehouse_id": wh_b,
            "quantity": -15,
            "reason": "Damaged goods removal",
        },
    )

    response = client.get("/api/v1/inventory/low-stock", headers=staff_headers)
    assert response.status_code == 200
    items = response.json()
    assert any(i["warehouse_id"] == wh_b and i["product_id"] == prod_id for i in items)


def test_inventory_summary(client, manager_headers, sample_data):
    response = client.get("/api/v1/inventory/summary", headers=manager_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_products"] >= 1
    assert data["total_warehouses"] >= 2
    assert data["total_stock_units"] >= 70
