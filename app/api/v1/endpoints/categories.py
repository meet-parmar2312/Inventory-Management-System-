from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import require_authenticated, require_manager_or_admin
from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import get_db
from app.models.category import Category
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.utils.pagination import PageParams, PaginatedResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=PaginatedResponse[CategoryResponse], summary="List categories")
def list_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    repo = CategoryRepository(db)
    page_params = PageParams(page=page, page_size=page_size)
    items = repo.list(offset=page_params.offset, limit=page_params.page_size)
    total = repo.count()
    responses = [CategoryResponse.model_validate(c) for c in items]
    return PaginatedResponse.create(responses, total, page_params)


@router.get("/{category_id}", response_model=CategoryResponse, summary="Get category by ID")
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    repo = CategoryRepository(db)
    cat = repo.get_by_id(category_id)
    if not cat:
        raise NotFoundException(f"Category with ID {category_id} not found")
    return CategoryResponse.model_validate(cat)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, summary="Create category (ADMIN, MANAGER)")
def create_category(
    req: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager_or_admin),
):
    repo = CategoryRepository(db)
    if repo.get_by_name(req.name):
        raise ConflictException(f"Category with name '{req.name}' already exists")
    cat = Category(name=req.name, description=req.description)
    repo.create(cat)
    db.commit()
    db.refresh(cat)
    return CategoryResponse.model_validate(cat)


@router.patch("/{category_id}", response_model=CategoryResponse, summary="Update category (ADMIN, MANAGER)")
def update_category(
    category_id: int,
    req: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager_or_admin),
):
    repo = CategoryRepository(db)
    cat = repo.get_by_id(category_id)
    if not cat:
        raise NotFoundException(f"Category with ID {category_id} not found")
    if req.name and req.name.lower() != cat.name.lower():
        existing = repo.get_by_name(req.name)
        if existing and existing.id != category_id:
            raise ConflictException(f"Category with name '{req.name}' already exists")
        cat.name = req.name
    if req.description is not None:
        cat.description = req.description
    repo.update(cat)
    db.commit()
    db.refresh(cat)
    return CategoryResponse.model_validate(cat)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete category (ADMIN, MANAGER)")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager_or_admin),
):
    repo = CategoryRepository(db)
    cat = repo.get_by_id(category_id)
    if not cat:
        raise NotFoundException(f"Category with ID {category_id} not found")
    dep_count = repo.count_dependent_products(category_id)
    if dep_count > 0:
        raise ConflictException(f"Cannot delete category: {dep_count} products currently depend on this category")
    repo.delete(cat)
    db.commit()
