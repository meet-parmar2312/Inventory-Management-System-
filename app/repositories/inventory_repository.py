from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.stock_movement import StockMovement
from app.utils.enums import StockMovementType


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, product_id: int, warehouse_id: int, for_update: bool = False) -> Optional[Inventory]:
        stmt = select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_create(self, product_id: int, warehouse_id: int, for_update: bool = False) -> Inventory:
        inv = self.get(product_id, warehouse_id, for_update=for_update)
        if not inv:
            inv = Inventory(
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=0,
                reserved_quantity=0,
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(inv)
            self.db.flush()
            if for_update:
                return self.get(product_id, warehouse_id, for_update=True)
        return inv

    def list(
        self,
        offset: int = 0,
        limit: int = 20,
        warehouse_id: Optional[int] = None,
        product_id: Optional[int] = None,
    ) -> Tuple[List[Inventory], int]:
        stmt = select(Inventory)
        count_stmt = select(func.count(Inventory.id))

        if warehouse_id is not None:
            stmt = stmt.where(Inventory.warehouse_id == warehouse_id)
            count_stmt = count_stmt.where(Inventory.warehouse_id == warehouse_id)
        if product_id is not None:
            stmt = stmt.where(Inventory.product_id == product_id)
            count_stmt = count_stmt.where(Inventory.product_id == product_id)

        total = self.db.execute(count_stmt).scalar() or 0
        stmt = stmt.order_by(Inventory.id.asc()).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def get_by_product(self, product_id: int) -> List[Inventory]:
        stmt = select(Inventory).where(Inventory.product_id == product_id).order_by(Inventory.warehouse_id.asc())
        return list(self.db.execute(stmt).scalars().all())

    def create_stock_movement(
        self,
        product_id: int,
        warehouse_id: int,
        movement_type: StockMovementType,
        quantity: int,
        reference_id: Optional[str] = None,
        reason: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> StockMovement:
        movement = StockMovement(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            quantity=quantity,
            reference_id=reference_id,
            reason=reason,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(movement)
        self.db.flush()
        return movement

    def list_stock_movements(
        self,
        offset: int = 0,
        limit: int = 20,
        product_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        movement_type: Optional[StockMovementType] = None,
    ) -> Tuple[List[StockMovement], int]:
        stmt = select(StockMovement)
        count_stmt = select(func.count(StockMovement.id))

        if product_id is not None:
            stmt = stmt.where(StockMovement.product_id == product_id)
            count_stmt = count_stmt.where(StockMovement.product_id == product_id)
        if warehouse_id is not None:
            stmt = stmt.where(StockMovement.warehouse_id == warehouse_id)
            count_stmt = count_stmt.where(StockMovement.warehouse_id == warehouse_id)
        if movement_type is not None:
            stmt = stmt.where(StockMovement.movement_type == movement_type)
            count_stmt = count_stmt.where(StockMovement.movement_type == movement_type)

        total = self.db.execute(count_stmt).scalar() or 0
        stmt = stmt.order_by(StockMovement.created_at.desc()).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def get_low_stock(self) -> List[Dict]:
        stmt = (
            select(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Product.sku.label("sku"),
                Warehouse.id.label("warehouse_id"),
                Warehouse.name.label("warehouse_name"),
                Inventory.quantity.label("quantity"),
                Inventory.reserved_quantity.label("reserved_quantity"),
                (Inventory.quantity - Inventory.reserved_quantity).label("available_quantity"),
                Product.reorder_level.label("reorder_level"),
            )
            .join(Product, Inventory.product_id == Product.id)
            .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
            .where(
                (Inventory.quantity - Inventory.reserved_quantity) <= Product.reorder_level,
                Product.is_active == True,
                Warehouse.is_active == True,
            )
            .order_by((Inventory.quantity - Inventory.reserved_quantity).asc())
        )
        results = self.db.execute(stmt).mappings().all()
        return [dict(r) for r in results]

    def get_summary(self) -> Dict:
        total_products = self.db.execute(select(func.count(Product.id)).where(Product.is_active == True)).scalar() or 0
        total_warehouses = self.db.execute(select(func.count(Warehouse.id)).where(Warehouse.is_active == True)).scalar() or 0

        inv_stats = self.db.execute(
            select(
                func.coalesce(func.sum(Inventory.quantity), 0).label("total_stock"),
                func.coalesce(func.sum(Inventory.reserved_quantity), 0).label("total_reserved"),
            )
        ).one()

        low_stock_count = self.db.execute(
            select(func.count(Inventory.id))
            .join(Product, Inventory.product_id == Product.id)
            .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
            .where(
                (Inventory.quantity - Inventory.reserved_quantity) <= Product.reorder_level,
                Product.is_active == True,
                Warehouse.is_active == True,
            )
        ).scalar() or 0

        total_stock = int(inv_stats.total_stock)
        total_reserved = int(inv_stats.total_reserved)

        return {
            "total_products": total_products,
            "total_stock_units": total_stock,
            "total_reserved_units": total_reserved,
            "total_available_units": total_stock - total_reserved,
            "low_stock_products_count": low_stock_count,
            "total_warehouses": total_warehouses,
        }
