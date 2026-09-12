from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.models.order import Order
from app.models.order_item import OrderItem
from app.utils.enums import OrderStatus


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_id: int) -> Optional[Order]:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list(
        self,
        offset: int = 0,
        limit: int = 20,
        status: Optional[OrderStatus] = None,
        customer_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
    ) -> Tuple[List[Order], int]:
        stmt = select(Order).options(selectinload(Order.items))
        count_stmt = select(func.count(Order.id))

        if status is not None:
            stmt = stmt.where(Order.status == status)
            count_stmt = count_stmt.where(Order.status == status)
        if customer_id is not None:
            stmt = stmt.where(Order.customer_id == customer_id)
            count_stmt = count_stmt.where(Order.customer_id == customer_id)
        if warehouse_id is not None:
            stmt = stmt.where(Order.warehouse_id == warehouse_id)
            count_stmt = count_stmt.where(Order.warehouse_id == warehouse_id)

        total = self.db.execute(count_stmt).scalar() or 0
        stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def create(self, customer_id: int, warehouse_id: int, total_amount: Decimal) -> Order:
        order = Order(
            customer_id=customer_id,
            warehouse_id=warehouse_id,
            status=OrderStatus.PENDING,
            total_amount=total_amount,
        )
        self.db.add(order)
        self.db.flush()
        return order

    def create_item(
        self,
        order_id: int,
        product_id: int,
        quantity: int,
        unit_price: Decimal,
        subtotal: Decimal,
    ) -> OrderItem:
        item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def update_status(self, order: Order, new_status: OrderStatus) -> Order:
        order.status = new_status
        self.db.flush()
        return order
