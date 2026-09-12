import pytest


def test_create_order_reserves_stock(client, staff_headers, sample_data):
    prod_id = sample_data["product"].id
    wh_id = sample_data["warehouse_a"].id
    cust_id = sample_data["customer"].id

    response = client.post(
        "/api/v1/orders",
        headers=staff_headers,
        json={
            "customer_id": cust_id,
            "warehouse_id": wh_id,
            "items": [{"product_id": prod_id, "quantity": 5}],
        },
    )
    assert response.status_code == 201
    order_data = response.json()
    assert order_data["status"] == "PENDING"
    assert float(order_data["total_amount"]) == 500.00

    inv_resp = client.get(f"/api/v1/inventory/{prod_id}", headers=staff_headers)
    wh_inv = next(i for i in inv_resp.json() if i["warehouse_id"] == wh_id)
    assert wh_inv["quantity"] == 50
    assert wh_inv["reserved_quantity"] == 5
    assert wh_inv["available_quantity"] == 45


def test_create_order_insufficient_stock(client, staff_headers, sample_data):
    prod_id = sample_data["product"].id
    wh_id = sample_data["warehouse_a"].id
    cust_id = sample_data["customer"].id

    response = client.post(
        "/api/v1/orders",
        headers=staff_headers,
        json={
            "customer_id": cust_id,
            "warehouse_id": wh_id,
            "items": [{"product_id": prod_id, "quantity": 1000}],
        },
    )
    assert response.status_code == 409
    assert "Insufficient stock" in response.json()["message"]


def test_order_lifecycle_and_state_transitions(client, staff_headers, manager_headers, sample_data):
    prod_id = sample_data["product"].id
    wh_id = sample_data["warehouse_a"].id
    cust_id = sample_data["customer"].id

    create_resp = client.post(
        "/api/v1/orders",
        headers=staff_headers,
        json={
            "customer_id": cust_id,
            "warehouse_id": wh_id,
            "items": [{"product_id": prod_id, "quantity": 4}],
        },
    )
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]

    confirm_resp = client.post(f"/api/v1/orders/{order_id}/confirm", headers=manager_headers)
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "CONFIRMED"

    ship_resp = client.post(f"/api/v1/orders/{order_id}/ship", headers=manager_headers)
    assert ship_resp.status_code == 200
    assert ship_resp.json()["status"] == "SHIPPED"

    inv_resp = client.get(f"/api/v1/inventory/{prod_id}", headers=staff_headers)
    wh_inv = next(i for i in inv_resp.json() if i["warehouse_id"] == wh_id)
    assert wh_inv["quantity"] == 46
    assert wh_inv["reserved_quantity"] == 0
    assert wh_inv["available_quantity"] == 46

    deliver_resp = client.post(f"/api/v1/orders/{order_id}/deliver", headers=manager_headers)
    assert deliver_resp.status_code == 200
    assert deliver_resp.json()["status"] == "DELIVERED"

    invalid_cancel = client.post(f"/api/v1/orders/{order_id}/cancel", headers=manager_headers)
    assert invalid_cancel.status_code == 400
    assert "Invalid order status transition" in invalid_cancel.json()["message"]


def test_order_cancellation_releases_stock(client, staff_headers, sample_data):
    prod_id = sample_data["product"].id
    wh_id = sample_data["warehouse_a"].id
    cust_id = sample_data["customer"].id

    create_resp = client.post(
        "/api/v1/orders",
        headers=staff_headers,
        json={
            "customer_id": cust_id,
            "warehouse_id": wh_id,
            "items": [{"product_id": prod_id, "quantity": 8}],
        },
    )
    order_id = create_resp.json()["id"]

    inv_before = client.get(f"/api/v1/inventory/{prod_id}", headers=staff_headers).json()
    wh_inv_before = next(i for i in inv_before if i["warehouse_id"] == wh_id)
    assert wh_inv_before["reserved_quantity"] == 8

    cancel_resp = client.post(f"/api/v1/orders/{order_id}/cancel", headers=staff_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    inv_after = client.get(f"/api/v1/inventory/{prod_id}", headers=staff_headers).json()
    wh_inv_after = next(i for i in inv_after if i["warehouse_id"] == wh_id)
    assert wh_inv_after["reserved_quantity"] == 0
    assert wh_inv_after["available_quantity"] == 50
