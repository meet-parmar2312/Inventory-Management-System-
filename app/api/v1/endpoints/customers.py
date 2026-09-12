from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import require_authenticated
from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import get_db
from app.models.customer import Customer
from app.models.user import User
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.utils.pagination import PageParams, PaginatedResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=PaginatedResponse[CustomerResponse], summary="List customers")
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    repo = CustomerRepository(db)
    page_params = PageParams(page=page, page_size=page_size)
    items = repo.list(offset=page_params.offset, limit=page_params.page_size)
    total = repo.count()
    responses = [CustomerResponse.model_validate(c) for c in items]
    return PaginatedResponse.create(responses, total, page_params)


@router.get("/{customer_id}", response_model=CustomerResponse, summary="Get customer by ID")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    repo = CustomerRepository(db)
    c = repo.get_by_id(customer_id)
    if not c:
        raise NotFoundException(f"Customer with ID {customer_id} not found")
    return CustomerResponse.model_validate(c)


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, summary="Create customer")
def create_customer(
    req: CustomerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    repo = CustomerRepository(db)
    if repo.get_by_email(req.email):
        raise ConflictException(f"Customer with email '{req.email}' already exists")
    cust = Customer(
        name=req.name,
        email=req.email.lower(),
        phone=req.phone,
        address=req.address,
    )
    repo.create(cust)
    db.commit()
    db.refresh(cust)
    return CustomerResponse.model_validate(cust)


@router.patch("/{customer_id}", response_model=CustomerResponse, summary="Update customer")
def update_customer(
    customer_id: int,
    req: CustomerUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    repo = CustomerRepository(db)
    cust = repo.get_by_id(customer_id)
    if not cust:
        raise NotFoundException(f"Customer with ID {customer_id} not found")
    if req.email and req.email.lower() != cust.email:
        existing = repo.get_by_email(req.email)
        if existing and existing.id != customer_id:
            raise ConflictException(f"Customer with email '{req.email}' already exists")
        cust.email = req.email.lower()
    if req.name is not None:
        cust.name = req.name
    if req.phone is not None:
        cust.phone = req.phone
    if req.address is not None:
        cust.address = req.address

    repo.update(cust)
    db.commit()
    db.refresh(cust)
    return CustomerResponse.model_validate(cust)
