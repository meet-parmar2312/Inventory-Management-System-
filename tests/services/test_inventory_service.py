import pytest
from app.core.exceptions import InsufficientStockException
from app.schemas.inventory import StockAdjustRequest, StockTransferRequest
from app.services.inventory_service import InventoryService


def test_adjust_stock_service_success(db, sample_data):
    service = InventoryService(db)
    prod_id = sample_data["product"].id
    wh_id = sample_data["warehouse_a"].id

    req = StockAdjustRequest(product_id=prod_id, warehouse_id=wh_id, quantity=15, reason="Batch restock")
    res = service.adjust_stock(req)
    assert res.quantity == 65
    assert res.available_quantity == 65


def test_adjust_stock_insufficient(db, sample_data):
    service = InventoryService(db)
    prod_id = sample_data["product"].id
    wh_id = sample_data["warehouse_a"].id

    req = StockAdjustRequest(product_id=prod_id, warehouse_id=wh_id, quantity=-999, reason="Mass damage")
    with pytest.raises(InsufficientStockException):
        service.adjust_stock(req)


def test_transfer_stock_service(db, sample_data):
    service = InventoryService(db)
    prod_id = sample_data["product"].id
    src_wh = sample_data["warehouse_a"].id
    dst_wh = sample_data["warehouse_b"].id

    req = StockTransferRequest(
        product_id=prod_id,
        source_warehouse_id=src_wh,
        destination_warehouse_id=dst_wh,
        quantity=10,
    )
    res = service.transfer_stock(req)
    assert len(res) == 2
    src_inv = next(i for i in res if i.warehouse_id == src_wh)
    dst_inv = next(i for i in res if i.warehouse_id == dst_wh)
    assert src_inv.quantity == 40
    assert dst_inv.quantity == 30
