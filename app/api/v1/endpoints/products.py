from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import require_admin, require_authenticated, require_manager_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService
from app.utils.pagination import PageParams, PaginatedResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "",
    response_model=PaginatedResponse[ProductResponse],
    summary="List products with filtering and pagination",
)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    sort_by: str = Query("id"),
    sort_dir: str = Query("asc"),
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    service = ProductService(db)
    return service.list_products(
        page_params=PageParams(page=page, page_size=page_size),
        category_id=category_id,
        supplier_id=supplier_id,
        is_active=is_active,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get(
    "/search",
    response_model=PaginatedResponse[ProductResponse],
    summary="Database-level product search",
)
def search_products(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    service = ProductService(db)
    return service.search_products(
        q=q,
        page_params=PageParams(page=page, page_size=page_size),
        category_id=category_id,
        supplier_id=supplier_id,
        min_price=min_price,
        max_price=max_price,
        is_active=is_active,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product details by ID",
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    service = ProductService(db)
    return service.get_product(product_id)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product (ADMIN or MANAGER)",
)
def create_product(
    req: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager_or_admin),
):
    service = ProductService(db)
    return service.create_product(req)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product details (ADMIN or MANAGER)",
)
def update_product(
    product_id: int,
    req: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager_or_admin),
):
    service = ProductService(db)
    return service.update_product(product_id, req)


@router.delete(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Soft-delete product by marking inactive (ADMIN only)",
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    service = ProductService(db)
    return service.soft_delete_product(product_id)
