from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import (
    AppException,
    InsufficientStockException,
    InvalidStateTransitionException,
    NotFoundException,
)
from app.models.order import Order
from app.repositories.customer_repository import CustomerRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.schemas.order import OrderCreate, OrderResponse
from app.utils.enums import OrderStatus, StockMovementType
from app.utils.pagination import PageParams, PaginatedResponse

VALID_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
    OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
    OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.inv_repo = InventoryRepository(db)
        self.prod_repo = ProductRepository(db)
        self.cust_repo = CustomerRepository(db)
        self.wh_repo = WarehouseRepository(db)

    def get_order(self, order_id: int) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundException(f"Order with ID {order_id} not found")
        return OrderResponse.model_validate(order)

    def list_orders(
        self,
        page_params: PageParams,
        status: Optional[OrderStatus] = None,
        customer_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
    ) -> PaginatedResponse[OrderResponse]:
        items, total = self.order_repo.list(
            offset=page_params.offset,
            limit=page_params.page_size,
            status=status,
            customer_id=customer_id,
            warehouse_id=warehouse_id,
        )
        responses = [OrderResponse.model_validate(o) for o in items]
        return PaginatedResponse.create(responses, total, page_params)

    def create_order(self, req: OrderCreate, user_id: Optional[int] = None) -> OrderResponse:
        customer = self.cust_repo.get_by_id(req.customer_id)
        if not customer:
            raise NotFoundException(f"Customer with ID {req.customer_id} not found")

        warehouse = self.wh_repo.get_by_id(req.warehouse_id)
        if not warehouse or not warehouse.is_active:
            raise NotFoundException(f"Active warehouse with ID {req.warehouse_id} not found")

        if not req.items:
            raise AppException("Order must contain at least one item")

        product_quantities = {}
        for item in req.items:
            product_quantities[item.product_id] = product_quantities.get(item.product_id, 0) + item.quantity

        sorted_prod_ids = sorted(product_quantities.keys())
        order_items_data = []
        total_amount = Decimal("0.00")

        for prod_id in sorted_prod_ids:
            qty = product_quantities[prod_id]

            product = self.prod_repo.get_by_id(prod_id)
            if not product or not product.is_active:
                raise NotFoundException(f"Active product with ID {prod_id} not found")

            inv = self.inv_repo.get_or_create(prod_id, req.warehouse_id, for_update=True)

            if inv.available_quantity < qty:
                raise InsufficientStockException(
                    f"Insufficient stock for product '{product.name}' (SKU: {product.sku}) in warehouse {warehouse.name}. "
                    f"Available: {inv.available_quantity}, Requested: {qty}"
                )

            inv.reserved_quantity += qty
            inv.updated_at = datetime.now(timezone.utc)

            subtotal = product.unit_price * qty
            total_amount += subtotal
            order_items_data.append({
                "product_id": prod_id,
                "quantity": qty,
                "unit_price": product.unit_price,
                "subtotal": subtotal,
            })

        order = self.order_repo.create(
            customer_id=req.customer_id,
            warehouse_id=req.warehouse_id,
            total_amount=total_amount,
        )

        for item_data in order_items_data:
            self.order_repo.create_item(
                order_id=order.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                subtotal=item_data["subtotal"],
            )

        self.db.commit()
        self.db.refresh(order)
        return OrderResponse.model_validate(order)

    def transition_status(self, order_id: int, target_status: OrderStatus, user_id: Optional[int] = None) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundException(f"Order with ID {order_id} not found")

        current_status = order.status
        allowed_next = VALID_TRANSITIONS.get(current_status, [])
        if target_status not in allowed_next:
            raise InvalidStateTransitionException(
                f"Invalid order status transition from {current_status.value} to {target_status.value}. "
                f"Allowed transitions from {current_status.value}: {[s.value for s in allowed_next]}"
            )

        if target_status == OrderStatus.SHIPPED:
            sorted_items = sorted(order.items, key=lambda x: x.product_id)
            for item in sorted_items:
                inv = self.inv_repo.get(item.product_id, order.warehouse_id, for_update=True)
                if inv:
                    inv.quantity -= item.quantity
                    inv.reserved_quantity -= item.quantity
                    inv.updated_at = datetime.now(timezone.utc)

                    self.inv_repo.create_stock_movement(
                        product_id=item.product_id,
                        warehouse_id=order.warehouse_id,
                        movement_type=StockMovementType.SALE,
                        quantity=-item.quantity,
                        reference_id=f"ORDER-{order.id}",
                        reason=f"Fulfilled and shipped for order #{order.id}",
                        created_by=user_id,
                    )

        elif target_status == OrderStatus.CANCELLED:
            sorted_items = sorted(order.items, key=lambda x: x.product_id)
            for item in sorted_items:
                inv = self.inv_repo.get(item.product_id, order.warehouse_id, for_update=True)
                if inv:
                    inv.reserved_quantity = max(0, inv.reserved_quantity - item.quantity)
                    inv.updated_at = datetime.now(timezone.utc)

        self.order_repo.update_status(order, target_status)
        self.db.commit()
        self.db.refresh(order)
        return OrderResponse.model_validate(order)

    def cancel_order(self, order_id: int, user_id: Optional[int] = None) -> OrderResponse:
        return self.transition_status(order_id, OrderStatus.CANCELLED, user_id=user_id)

    def confirm_order(self, order_id: int, user_id: Optional[int] = None) -> OrderResponse:
        return self.transition_status(order_id, OrderStatus.CONFIRMED, user_id=user_id)

    def process_order(self, order_id: int, user_id: Optional[int] = None) -> OrderResponse:
        return self.transition_status(order_id, OrderStatus.PROCESSING, user_id=user_id)

    def ship_order(self, order_id: int, user_id: Optional[int] = None) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundException(f"Order with ID {order_id} not found")
        if order.status == OrderStatus.CONFIRMED:
            self.transition_status(order_id, OrderStatus.PROCESSING, user_id=user_id)
        return self.transition_status(order_id, OrderStatus.SHIPPED, user_id=user_id)

    def deliver_order(self, order_id: int, user_id: Optional[int] = None) -> OrderResponse:
        return self.transition_status(order_id, OrderStatus.DELIVERED, user_id=user_id)
