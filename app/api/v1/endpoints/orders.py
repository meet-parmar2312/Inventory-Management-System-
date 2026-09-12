from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import require_authenticated, require_manager_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import OrderService
from app.utils.enums import OrderStatus
from app.utils.pagination import PageParams, PaginatedResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get(
    "",
    response_model=PaginatedResponse[OrderResponse],
    summary="List customer orders with status filtering",
)
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatus] = Query(None),
    customer_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    service = OrderService(db)
    return service.list_orders(
        page_params=PageParams(page=page, page_size=page_size),
        status=status,
        customer_id=customer_id,
        warehouse_id=warehouse_id,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details and items by ID",
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    service = OrderService(db)
    return service.get_order(order_id)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order and reserve stock",
)
def create_order(
    req: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    service = OrderService(db)
    return service.create_order(req, user_id=current_user.id)


@router.post(
    "/{order_id}/confirm",
    response_model=OrderResponse,
    summary="Confirm order (MANAGER or ADMIN)",
)
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
):
    service = OrderService(db)
    return service.confirm_order(order_id, user_id=current_user.id)


@router.post(
    "/{order_id}/ship",
    response_model=OrderResponse,
    summary="Ship order (MANAGER or ADMIN)",
)
def ship_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
):
    service = OrderService(db)
    return service.ship_order(order_id, user_id=current_user.id)


@router.post(
    "/{order_id}/deliver",
    response_model=OrderResponse,
    summary="Deliver order (MANAGER or ADMIN)",
)
def deliver_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
):
    service = OrderService(db)
    return service.deliver_order(order_id, user_id=current_user.id)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel order and release reserved stock",
)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    service = OrderService(db)
    return service.cancel_order(order_id, user_id=current_user.id)
