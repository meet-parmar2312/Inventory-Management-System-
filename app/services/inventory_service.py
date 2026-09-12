from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import AppException, InsufficientStockException, NotFoundException
from app.models.inventory import Inventory
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.schemas.inventory import (
    InventoryResponse,
    InventorySummary,
    LowStockItem,
    StockAdjustRequest,
    StockTransferRequest,
)
from app.schemas.stock_movement import StockMovementResponse
from app.utils.enums import StockMovementType
from app.utils.pagination import PageParams, PaginatedResponse


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.inv_repo = InventoryRepository(db)
        self.prod_repo = ProductRepository(db)
        self.wh_repo = WarehouseRepository(db)

    def list_inventory(
        self,
        page_params: PageParams,
        warehouse_id: Optional[int] = None,
        product_id: Optional[int] = None,
    ) -> PaginatedResponse[InventoryResponse]:
        items, total = self.inv_repo.list(
            offset=page_params.offset,
            limit=page_params.page_size,
            warehouse_id=warehouse_id,
            product_id=product_id,
        )
        responses = [
            InventoryResponse(
                id=i.id,
                product_id=i.product_id,
                warehouse_id=i.warehouse_id,
                quantity=i.quantity,
                reserved_quantity=i.reserved_quantity,
                available_quantity=i.available_quantity,
                updated_at=i.updated_at,
            )
            for i in items
        ]
        return PaginatedResponse.create(responses, total, page_params)

    def get_product_inventory(self, product_id: int) -> List[InventoryResponse]:
        product = self.prod_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException(f"Product with ID {product_id} not found")
        items = self.inv_repo.get_by_product(product_id)
        return [
            InventoryResponse(
                id=i.id,
                product_id=i.product_id,
                warehouse_id=i.warehouse_id,
                quantity=i.quantity,
                reserved_quantity=i.reserved_quantity,
                available_quantity=i.available_quantity,
                updated_at=i.updated_at,
            )
            for i in items
        ]

    def adjust_stock(self, req: StockAdjustRequest, user_id: Optional[int] = None) -> InventoryResponse:
        product = self.prod_repo.get_by_id(req.product_id)
        if not product:
            raise NotFoundException(f"Product with ID {req.product_id} not found")
        warehouse = self.wh_repo.get_by_id(req.warehouse_id)
        if not warehouse or not warehouse.is_active:
            raise NotFoundException(f"Active warehouse with ID {req.warehouse_id} not found")

        inv = self.inv_repo.get_or_create(req.product_id, req.warehouse_id, for_update=True)

        new_quantity = inv.quantity + req.quantity
        if new_quantity < inv.reserved_quantity or new_quantity < 0:
            raise InsufficientStockException(
                f"Cannot adjust stock by {req.quantity}. Current stock is {inv.quantity} "
                f"with {inv.reserved_quantity} units reserved (minimum required: {inv.reserved_quantity})."
            )

        inv.quantity = new_quantity
        inv.updated_at = datetime.now(timezone.utc)

        m_type = StockMovementType.PURCHASE if req.quantity > 0 and "purchase" in req.reason.lower() else StockMovementType.ADJUSTMENT
        self.inv_repo.create_stock_movement(
            product_id=req.product_id,
            warehouse_id=req.warehouse_id,
            movement_type=m_type,
            quantity=req.quantity,
            reference_id="MANUAL_ADJUST",
            reason=req.reason,
            created_by=user_id,
        )

        self.db.commit()
        self.db.refresh(inv)

        return InventoryResponse(
            id=inv.id,
            product_id=inv.product_id,
            warehouse_id=inv.warehouse_id,
            quantity=inv.quantity,
            reserved_quantity=inv.reserved_quantity,
            available_quantity=inv.available_quantity,
            updated_at=inv.updated_at,
        )

    def transfer_stock(self, req: StockTransferRequest, user_id: Optional[int] = None) -> List[InventoryResponse]:
        if req.source_warehouse_id == req.destination_warehouse_id:
            raise AppException("Source and destination warehouses cannot be the same")

        product = self.prod_repo.get_by_id(req.product_id)
        if not product:
            raise NotFoundException(f"Product with ID {req.product_id} not found")

        src_wh = self.wh_repo.get_by_id(req.source_warehouse_id)
        if not src_wh or not src_wh.is_active:
            raise NotFoundException(f"Active source warehouse {req.source_warehouse_id} not found")

        dst_wh = self.wh_repo.get_by_id(req.destination_warehouse_id)
        if not dst_wh or not dst_wh.is_active:
            raise NotFoundException(f"Active destination warehouse {req.destination_warehouse_id} not found")

        # Ordered row-locking to avoid deadlocks
        wh_order = sorted([req.source_warehouse_id, req.destination_warehouse_id])
        locked_invs = {}
        for wh_id in wh_order:
            locked_invs[wh_id] = self.inv_repo.get_or_create(req.product_id, wh_id, for_update=True)

        src_inv = locked_invs[req.source_warehouse_id]
        dst_inv = locked_invs[req.destination_warehouse_id]

        if src_inv.available_quantity < req.quantity:
            raise InsufficientStockException(
                f"Insufficient stock in source warehouse {req.source_warehouse_id}. "
                f"Available: {src_inv.available_quantity}, Requested: {req.quantity}"
            )

        src_inv.quantity -= req.quantity
        src_inv.updated_at = datetime.now(timezone.utc)

        dst_inv.quantity += req.quantity
        dst_inv.updated_at = datetime.now(timezone.utc)

        ref_id = f"TRANSFER-WH{req.source_warehouse_id}-WH{req.destination_warehouse_id}"
        self.inv_repo.create_stock_movement(
            product_id=req.product_id,
            warehouse_id=req.source_warehouse_id,
            movement_type=StockMovementType.TRANSFER_OUT,
            quantity=-req.quantity,
            reference_id=ref_id,
            reason=f"Transferred to warehouse {req.destination_warehouse_id}",
            created_by=user_id,
        )
        self.inv_repo.create_stock_movement(
            product_id=req.product_id,
            warehouse_id=req.destination_warehouse_id,
            movement_type=StockMovementType.TRANSFER_IN,
            quantity=req.quantity,
            reference_id=ref_id,
            reason=f"Transferred from warehouse {req.source_warehouse_id}",
            created_by=user_id,
        )

        self.db.commit()
        self.db.refresh(src_inv)
        self.db.refresh(dst_inv)

        return [
            InventoryResponse(
                id=src_inv.id,
                product_id=src_inv.product_id,
                warehouse_id=src_inv.warehouse_id,
                quantity=src_inv.quantity,
                reserved_quantity=src_inv.reserved_quantity,
                available_quantity=src_inv.available_quantity,
                updated_at=src_inv.updated_at,
            ),
            InventoryResponse(
                id=dst_inv.id,
                product_id=dst_inv.product_id,
                warehouse_id=dst_inv.warehouse_id,
                quantity=dst_inv.quantity,
                reserved_quantity=dst_inv.reserved_quantity,
                available_quantity=dst_inv.available_quantity,
                updated_at=dst_inv.updated_at,
            ),
        ]

    def list_movements(
        self,
        page_params: PageParams,
        product_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        movement_type: Optional[StockMovementType] = None,
    ) -> PaginatedResponse[StockMovementResponse]:
        items, total = self.inv_repo.list_stock_movements(
            offset=page_params.offset,
            limit=page_params.page_size,
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
        )
        responses = [StockMovementResponse.model_validate(m) for m in items]
        return PaginatedResponse.create(responses, total, page_params)

    def get_low_stock(self) -> List[LowStockItem]:
        records = self.inv_repo.get_low_stock()
        return [LowStockItem(**r) for r in records]

    def get_summary(self) -> InventorySummary:
        data = self.inv_repo.get_summary()
        return InventorySummary(**data)
