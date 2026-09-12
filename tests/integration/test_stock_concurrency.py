import concurrent.futures
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import InsufficientStockException
from app.models.category import Category
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import OrderService
from tests.conftest import TestingSessionLocal


def test_concurrent_order_stock_reservation(db: Session):
    cat = Category(name="Concurrency Cat")
    wh = Warehouse(name="Concurrency WH", location="Test Hub", is_active=True)
    cust_a = Customer(name="Customer A", email="cust_a@test.com")
    cust_b = Customer(name="Customer B", email="cust_b@test.com")
    db.add_all([cat, wh, cust_a, cust_b])
    db.flush()

    product = Product(
        sku="CONCURRENCY-SKU-001",
        name="Concurrent Test Widget",
        category_id=cat.id,
        unit_price=Decimal("50.00"),
        reorder_level=5,
        is_active=True,
    )
    db.add(product)
    db.flush()

    inv = Inventory(
        product_id=product.id,
        warehouse_id=wh.id,
        quantity=10,
        reserved_quantity=0,
    )
    db.add(inv)
    db.commit()

    product_id = product.id
    warehouse_id = wh.id
    cust_a_id = cust_a.id
    cust_b_id = cust_b.id

    def run_order_request(customer_id: int, quantity: int):
        session = TestingSessionLocal()
        try:
            service = OrderService(session)
            req = OrderCreate(
                customer_id=customer_id,
                warehouse_id=warehouse_id,
                items=[OrderItemCreate(product_id=product_id, quantity=quantity)],
            )
            order = service.create_order(req)
            return {"status": "success", "order_id": order.id, "quantity": quantity}
        except InsufficientStockException as e:
            return {"status": "insufficient_stock", "error": str(e), "quantity": quantity}
        except Exception as e:
            return {"status": "error", "error": str(e), "quantity": quantity}
        finally:
            session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(run_order_request, cust_a_id, 7)
        future_b = executor.submit(run_order_request, cust_b_id, 6)

        res_a = future_a.result()
        res_b = future_b.result()

    outcomes = [res_a, res_b]
    successes = [o for o in outcomes if o["status"] == "success"]
    insufficient = [o for o in outcomes if o["status"] == "insufficient_stock"]

    assert len(successes) == 1, f"Expected exactly 1 success, got: {outcomes}"
    assert len(insufficient) == 1, f"Expected exactly 1 insufficient stock error, got: {outcomes}"

    winning_qty = successes[0]["quantity"]

    verification_session = TestingSessionLocal()
    final_inv = verification_session.query(Inventory).filter(
        Inventory.product_id == product_id,
        Inventory.warehouse_id == warehouse_id,
    ).one()

    assert final_inv.quantity == 10
    assert final_inv.reserved_quantity == winning_qty
    assert final_inv.available_quantity == 10 - winning_qty
    assert final_inv.available_quantity >= 0

    verification_session.close()
