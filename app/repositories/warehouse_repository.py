from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.warehouse import Warehouse


class WarehouseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, warehouse_id: int) -> Optional[Warehouse]:
        return self.db.execute(select(Warehouse).where(Warehouse.id == warehouse_id)).scalar_one_or_none()

    def get_by_name(self, name: str) -> Optional[Warehouse]:
        return self.db.execute(select(Warehouse).where(func.lower(Warehouse.name) == name.strip().lower())).scalar_one_or_none()

    def list(self, offset: int = 0, limit: int = 20, active_only: bool = False) -> List[Warehouse]:
        stmt = select(Warehouse)
        if active_only:
            stmt = stmt.where(Warehouse.is_active == True)
        stmt = stmt.order_by(Warehouse.id.asc()).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self, active_only: bool = False) -> int:
        stmt = select(func.count(Warehouse.id))
        if active_only:
            stmt = stmt.where(Warehouse.is_active == True)
        return self.db.execute(stmt).scalar() or 0

    def create(self, warehouse: Warehouse) -> Warehouse:
        self.db.add(warehouse)
        self.db.flush()
        return warehouse

    def update(self, warehouse: Warehouse) -> Warehouse:
        self.db.flush()
        return warehouse
