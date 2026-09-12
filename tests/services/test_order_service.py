from decimal import Decimal
import pytest
from app.core.exceptions import InsufficientStockException, InvalidStateTransitionException
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import OrderService
from app.utils.enums import OrderStatus


def test_create_order_service_reserves_stock(db, sample_data):
    service = OrderService(db)
    prod_id = sample_data["product"].id
    wh_id = sample_data["warehouse_a"].id
    cust_id = sample_data["customer"].id

    req = OrderCreate(
        customer_id=cust_id,
        warehouse_id=wh_id,
        items=[OrderItemCreate(product_id=prod_id, quantity=3)],
    )
    order = service.create_order(req)
    assert order.status == OrderStatus.PENDING
    assert order.total_amount == Decimal("300.00")
    assert len(order.items) == 1
    assert order.items[0].quantity == 3


def test_create_order_insufficient_stock_service(db, sample_data):
    service = OrderService(db)
    prod_id = sample_data["product"].id
    wh_id = sample_data["warehouse_a"].id
    cust_id = sample_data["customer"].id

    req = OrderCreate(
        customer_id=cust_id,
        warehouse_id=wh_id,
        items=[OrderItemCreate(product_id=prod_id, quantity=100)],
    )
    with pytest.raises(InsufficientStockException):
        service.create_order(req)


def test_order_state_machine_transitions(db, sample_data):
    service = OrderService(db)
    prod_id = sample_data["product"].id
    wh_id = sample_data["warehouse_a"].id
    cust_id = sample_data["customer"].id

    req = OrderCreate(
        customer_id=cust_id,
        warehouse_id=wh_id,
        items=[OrderItemCreate(product_id=prod_id, quantity=2)],
    )
    order = service.create_order(req)
    assert order.status == OrderStatus.PENDING

    confirmed = service.confirm_order(order.id)
    assert confirmed.status == OrderStatus.CONFIRMED

    processed = service.process_order(order.id)
    assert processed.status == OrderStatus.PROCESSING

    shipped = service.ship_order(order.id)
    assert shipped.status == OrderStatus.SHIPPED

    delivered = service.deliver_order(order.id)
    assert delivered.status == OrderStatus.DELIVERED

    with pytest.raises(InvalidStateTransitionException):
        service.cancel_order(order.id)
