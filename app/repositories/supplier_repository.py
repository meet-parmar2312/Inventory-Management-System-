from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.supplier import Supplier


class SupplierRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        return self.db.execute(select(Supplier).where(Supplier.id == supplier_id)).scalar_one_or_none()

    def list(self, offset: int = 0, limit: int = 20) -> List[Supplier]:
        stmt = select(Supplier).order_by(Supplier.id.asc()).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        return self.db.execute(select(func.count(Supplier.id))).scalar() or 0

    def create(self, supplier: Supplier) -> Supplier:
        self.db.add(supplier)
        self.db.flush()
        return supplier

    def update(self, supplier: Supplier) -> Supplier:
        self.db.flush()
        return supplier

    def delete(self, supplier: Supplier) -> None:
        self.db.delete(supplier)
        self.db.flush()
