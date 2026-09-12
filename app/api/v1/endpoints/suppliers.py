from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import require_authenticated, require_manager_or_admin
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.supplier import Supplier
from app.models.user import User
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from app.utils.pagination import PageParams, PaginatedResponse

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", response_model=PaginatedResponse[SupplierResponse], summary="List suppliers")
def list_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    repo = SupplierRepository(db)
    page_params = PageParams(page=page, page_size=page_size)
    items = repo.list(offset=page_params.offset, limit=page_params.page_size)
    total = repo.count()
    responses = [SupplierResponse.model_validate(s) for s in items]
    return PaginatedResponse.create(responses, total, page_params)


@router.get("/{supplier_id}", response_model=SupplierResponse, summary="Get supplier by ID")
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    repo = SupplierRepository(db)
    sup = repo.get_by_id(supplier_id)
    if not sup:
        raise NotFoundException(f"Supplier with ID {supplier_id} not found")
    return SupplierResponse.model_validate(sup)


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED, summary="Create supplier (ADMIN, MANAGER)")
def create_supplier(
    req: SupplierCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager_or_admin),
):
    repo = SupplierRepository(db)
    sup = Supplier(
        name=req.name,
        contact_name=req.contact_name,
        email=req.email.lower(),
        phone=req.phone,
        address=req.address,
    )
    repo.create(sup)
    db.commit()
    db.refresh(sup)
    return SupplierResponse.model_validate(sup)


@router.patch("/{supplier_id}", response_model=SupplierResponse, summary="Update supplier (ADMIN, MANAGER)")
def update_supplier(
    supplier_id: int,
    req: SupplierUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager_or_admin),
):
    repo = SupplierRepository(db)
    sup = repo.get_by_id(supplier_id)
    if not sup:
        raise NotFoundException(f"Supplier with ID {supplier_id} not found")

    if req.name is not None:
        sup.name = req.name
    if req.contact_name is not None:
        sup.contact_name = req.contact_name
    if req.email is not None:
        sup.email = req.email.lower()
    if req.phone is not None:
        sup.phone = req.phone
    if req.address is not None:
        sup.address = req.address

    repo.update(sup)
    db.commit()
    db.refresh(sup)
    return SupplierResponse.model_validate(sup)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete supplier (ADMIN, MANAGER)")
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager_or_admin),
):
    repo = SupplierRepository(db)
    sup = repo.get_by_id(supplier_id)
    if not sup:
        raise NotFoundException(f"Supplier with ID {supplier_id} not found")
    repo.delete(sup)
    db.commit()
