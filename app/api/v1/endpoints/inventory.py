from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import require_authenticated, require_manager_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.inventory import (
    InventoryResponse,
    InventorySummary,
    LowStockItem,
    StockAdjustRequest,
    StockTransferRequest,
)
from app.schemas.stock_movement import StockMovementResponse
from app.services.inventory_service import InventoryService
from app.utils.enums import StockMovementType
from app.utils.pagination import PageParams, PaginatedResponse

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get(
    "",
    response_model=PaginatedResponse[InventoryResponse],
    summary="List inventory across warehouses",
)
def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    warehouse_id: Optional[int] = Query(None),
    product_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    service = InventoryService(db)
    return service.list_inventory(
        page_params=PageParams(page=page, page_size=page_size),
        warehouse_id=warehouse_id,
        product_id=product_id,
    )


@router.get(
    "/summary",
    response_model=InventorySummary,
    summary="Aggregated inventory summary metrics (ADMIN, MANAGER)",
)
def get_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_manager_or_admin),
):
    service = InventoryService(db)
    return service.get_summary()


@router.get(
    "/low-stock",
    response_model=List[LowStockItem],
    summary="List products with stock at or below reorder level",
)
def get_low_stock(
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    service = InventoryService(db)
    return service.get_low_stock()


@router.get(
    "/movements",
    response_model=PaginatedResponse[StockMovementResponse],
    summary="List auditable stock movement history",
)
def list_movements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    movement_type: Optional[StockMovementType] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    service = InventoryService(db)
    return service.list_movements(
        page_params=PageParams(page=page, page_size=page_size),
        product_id=product_id,
        warehouse_id=warehouse_id,
        movement_type=movement_type,
    )


@router.get(
    "/{product_id}",
    response_model=List[InventoryResponse],
    summary="Get inventory levels for a product across all warehouses",
)
def get_product_inventory(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    service = InventoryService(db)
    return service.get_product_inventory(product_id)


@router.post(
    "/adjust",
    response_model=InventoryResponse,
    summary="Manually adjust stock quantity with audit tracking (ADMIN, MANAGER)",
)
def adjust_stock(
    req: StockAdjustRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
):
    service = InventoryService(db)
    return service.adjust_stock(req, user_id=current_user.id)


@router.post(
    "/transfer",
    response_model=List[InventoryResponse],
    summary="Atomic warehouse-to-warehouse stock transfer (ADMIN, MANAGER)",
)
def transfer_stock(
    req: StockTransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
):
    service = InventoryService(db)
    return service.transfer_stock(req, user_id=current_user.id)
