import pytest
from decimal import Decimal


def test_create_product_admin(client, admin_headers, sample_data):
    cat_id = sample_data["category"].id
    sup_id = sample_data["supplier"].id

    response = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "sku": "KB-NEW-001",
            "name": "Custom 65% Keyboard",
            "description": "Hot-swappable wireless keyboard",
            "category_id": cat_id,
            "supplier_id": sup_id,
            "unit_price": 149.99,
            "reorder_level": 5,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "KB-NEW-001"
    assert data["name"] == "Custom 65% Keyboard"
    assert float(data["unit_price"]) == 149.99


def test_create_product_forbidden_for_staff(client, staff_headers, sample_data):
    response = client.post(
        "/api/v1/products",
        headers=staff_headers,
        json={
            "sku": "KB-STAFF-FAIL",
            "name": "Unauthorized Product",
            "unit_price": 20.00,
        },
    )
    assert response.status_code == 403


def test_create_product_duplicate_sku(client, admin_headers, sample_data):
    response = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "sku": sample_data["product"].sku,
            "name": "Another Keyboard",
            "unit_price": 99.00,
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["message"]


def test_product_search(client, staff_headers, sample_data):
    response = client.get(
        "/api/v1/products/search?q=Keyboard",
        headers=staff_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(p["name"] == "Mechanical Keyboard" for p in data["items"])


def test_product_list_filtering(client, staff_headers, sample_data):
    cat_id = sample_data["category"].id
    response = client.get(
        f"/api/v1/products?category_id={cat_id}&min_price=50&max_price=200",
        headers=staff_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert float(item["unit_price"]) >= 50
        assert float(item["unit_price"]) <= 200


def test_update_product(client, manager_headers, sample_data):
    prod_id = sample_data["product"].id
    response = client.patch(
        f"/api/v1/products/{prod_id}",
        headers=manager_headers,
        json={"name": "Updated Keyboard Pro", "unit_price": 119.50},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Keyboard Pro"
    assert float(data["unit_price"]) == 119.50


def test_soft_delete_product(client, admin_headers, staff_headers, sample_data):
    prod_id = sample_data["product"].id
    del_resp = client.delete(f"/api/v1/products/{prod_id}", headers=admin_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_active"] is False

    get_resp = client.get(f"/api/v1/products/{prod_id}", headers=staff_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["is_active"] is False
