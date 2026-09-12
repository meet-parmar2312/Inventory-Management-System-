from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.product import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self.db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()

    def get_by_sku(self, sku: str) -> Optional[Product]:
        return self.db.execute(select(Product).where(func.upper(Product.sku) == sku.strip().upper())).scalar_one_or_none()

    def list(
        self,
        offset: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        sort_by: str = "id",
        sort_dir: str = "asc",
    ) -> Tuple[List[Product], int]:
        stmt = select(Product)
        count_stmt = select(func.count(Product.id))

        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
            count_stmt = count_stmt.where(Product.category_id == category_id)
        if supplier_id is not None:
            stmt = stmt.where(Product.supplier_id == supplier_id)
            count_stmt = count_stmt.where(Product.supplier_id == supplier_id)
        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)
            count_stmt = count_stmt.where(Product.is_active == is_active)
        if min_price is not None:
            stmt = stmt.where(Product.unit_price >= min_price)
            count_stmt = count_stmt.where(Product.unit_price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.unit_price <= max_price)
            count_stmt = count_stmt.where(Product.unit_price <= max_price)

        total = self.db.execute(count_stmt).scalar() or 0

        sort_column = getattr(Product, sort_by, Product.id)
        if sort_dir.lower() == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        stmt = stmt.offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def search(
        self,
        q: str,
        offset: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Product], int]:
        search_pattern = f"%{q.strip()}%"
        search_filter = or_(
            Product.name.ilike(search_pattern),
            Product.sku.ilike(search_pattern),
            Product.description.ilike(search_pattern),
        )

        stmt = select(Product).where(search_filter)
        count_stmt = select(func.count(Product.id)).where(search_filter)

        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
            count_stmt = count_stmt.where(Product.category_id == category_id)
        if supplier_id is not None:
            stmt = stmt.where(Product.supplier_id == supplier_id)
            count_stmt = count_stmt.where(Product.supplier_id == supplier_id)
        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)
            count_stmt = count_stmt.where(Product.is_active == is_active)
        if min_price is not None:
            stmt = stmt.where(Product.unit_price >= min_price)
            count_stmt = count_stmt.where(Product.unit_price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.unit_price <= max_price)
            count_stmt = count_stmt.where(Product.unit_price <= max_price)

        total = self.db.execute(count_stmt).scalar() or 0
        stmt = stmt.order_by(Product.name.asc()).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.flush()
        return product

    def update(self, product: Product) -> Product:
        self.db.flush()
        return product

    def soft_delete(self, product: Product) -> Product:
        product.is_active = False
        self.db.flush()
        return product
