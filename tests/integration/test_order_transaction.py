from decimal import Decimal
import pytest
from app.core.exceptions import InsufficientStockException
from app.models.category import Category
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import OrderService


def test_order_creation_atomic_rollback(db):
    cat = Category(name="Tx Category")
    wh = Warehouse(name="Tx WH", location="Central", is_active=True)
    cust = Customer(name="Tx Customer", email="tx@cust.com")
    db.add_all([cat, wh, cust])
    db.flush()

    prod1 = Product(
        sku="TX-PROD-1",
        name="Abundant Stock Item",
        category_id=cat.id,
        unit_price=Decimal("20.00"),
        reorder_level=5,
        is_active=True,
    )
    prod2 = Product(
        sku="TX-PROD-2",
        name="Scarce Stock Item",
        category_id=cat.id,
        unit_price=Decimal("50.00"),
        reorder_level=5,
        is_active=True,
    )
    db.add_all([prod1, prod2])
    db.flush()

    inv1 = Inventory(product_id=prod1.id, warehouse_id=wh.id, quantity=10, reserved_quantity=0)
    inv2 = Inventory(product_id=prod2.id, warehouse_id=wh.id, quantity=2, reserved_quantity=0)
    db.add_all([inv1, inv2])
    db.commit()

    service = OrderService(db)
    req = OrderCreate(
        customer_id=cust.id,
        warehouse_id=wh.id,
        items=[
            OrderItemCreate(product_id=prod1.id, quantity=5),
            OrderItemCreate(product_id=prod2.id, quantity=5),
        ],
    )

    with pytest.raises(InsufficientStockException):
        service.create_order(req)

    db.rollback()

    inv1_recheck = db.query(Inventory).filter(Inventory.id == inv1.id).one()
    inv2_recheck = db.query(Inventory).filter(Inventory.id == inv2.id).one()

    assert inv1_recheck.reserved_quantity == 0
    assert inv1_recheck.available_quantity == 10

    assert inv2_recheck.reserved_quantity == 0
    assert inv2_recheck.available_quantity == 2
