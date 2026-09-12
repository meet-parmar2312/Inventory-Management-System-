from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictException, NotFoundException
from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.utils.pagination import PageParams, PaginatedResponse


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)
        self.supplier_repo = SupplierRepository(db)

    def get_product(self, product_id: int) -> ProductResponse:
        prod = self.product_repo.get_by_id(product_id)
        if not prod:
            raise NotFoundException(f"Product with ID {product_id} not found")
        return ProductResponse.model_validate(prod)

    def list_products(
        self,
        page_params: PageParams,
        category_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        sort_by: str = "id",
        sort_dir: str = "asc",
    ) -> PaginatedResponse[ProductResponse]:
        items, total = self.product_repo.list(
            offset=page_params.offset,
            limit=page_params.page_size,
            category_id=category_id,
            supplier_id=supplier_id,
            is_active=is_active,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        responses = [ProductResponse.model_validate(p) for p in items]
        return PaginatedResponse.create(responses, total, page_params)

    def search_products(
        self,
        q: str,
        page_params: PageParams,
        category_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        is_active: Optional[bool] = None,
    ) -> PaginatedResponse[ProductResponse]:
        items, total = self.product_repo.search(
            q=q,
            offset=page_params.offset,
            limit=page_params.page_size,
            category_id=category_id,
            supplier_id=supplier_id,
            min_price=min_price,
            max_price=max_price,
            is_active=is_active,
        )
        responses = [ProductResponse.model_validate(p) for p in items]
        return PaginatedResponse.create(responses, total, page_params)

    def create_product(self, req: ProductCreate) -> ProductResponse:
        if self.product_repo.get_by_sku(req.sku):
            raise ConflictException(f"Product with SKU '{req.sku}' already exists")

        if req.category_id:
            if not self.category_repo.get_by_id(req.category_id):
                raise NotFoundException(f"Category with ID {req.category_id} does not exist")

        if req.supplier_id:
            if not self.supplier_repo.get_by_id(req.supplier_id):
                raise NotFoundException(f"Supplier with ID {req.supplier_id} does not exist")

        product = Product(
            sku=req.sku.upper(),
            name=req.name,
            description=req.description,
            category_id=req.category_id,
            supplier_id=req.supplier_id,
            unit_price=req.unit_price,
            reorder_level=req.reorder_level,
            is_active=req.is_active,
        )
        self.product_repo.create(product)
        self.db.commit()
        self.db.refresh(product)
        return ProductResponse.model_validate(product)

    def update_product(self, product_id: int, req: ProductUpdate) -> ProductResponse:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException(f"Product with ID {product_id} not found")

        if req.category_id is not None:
            if not self.category_repo.get_by_id(req.category_id):
                raise NotFoundException(f"Category with ID {req.category_id} does not exist")
            product.category_id = req.category_id

        if req.supplier_id is not None:
            if not self.supplier_repo.get_by_id(req.supplier_id):
                raise NotFoundException(f"Supplier with ID {req.supplier_id} does not exist")
            product.supplier_id = req.supplier_id

        if req.name is not None:
            product.name = req.name
        if req.description is not None:
            product.description = req.description
        if req.unit_price is not None:
            product.unit_price = req.unit_price
        if req.reorder_level is not None:
            product.reorder_level = req.reorder_level
        if req.is_active is not None:
            product.is_active = req.is_active

        self.product_repo.update(product)
        self.db.commit()
        self.db.refresh(product)
        return ProductResponse.model_validate(product)

    def soft_delete_product(self, product_id: int) -> ProductResponse:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException(f"Product with ID {product_id} not found")
        self.product_repo.soft_delete(product)
        self.db.commit()
        self.db.refresh(product)
        return ProductResponse.model_validate(product)
