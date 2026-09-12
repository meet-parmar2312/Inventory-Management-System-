from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.product import Product


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.db.execute(select(Category).where(Category.id == category_id)).scalar_one_or_none()

    def get_by_name(self, name: str) -> Optional[Category]:
        return self.db.execute(select(Category).where(func.lower(Category.name) == name.strip().lower())).scalar_one_or_none()

    def list(self, offset: int = 0, limit: int = 20) -> List[Category]:
        stmt = select(Category).order_by(Category.id.asc()).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        return self.db.execute(select(func.count(Category.id))).scalar() or 0

    def count_dependent_products(self, category_id: int) -> int:
        return self.db.execute(select(func.count(Product.id)).where(Product.category_id == category_id)).scalar() or 0

    def create(self, category: Category) -> Category:
        self.db.add(category)
        self.db.flush()
        return category

    def update(self, category: Category) -> Category:
        self.db.flush()
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.flush()
