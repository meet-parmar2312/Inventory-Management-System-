from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import require_authenticated, require_manager_or_admin
from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import get_db
from app.models.user import User
from app.models.warehouse import Warehouse
from app.repositories.warehouse_repository import WarehouseRepository
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseResponse
from app.utils.pagination import PageParams, PaginatedResponse

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


@router.get("", response_model=PaginatedResponse[WarehouseResponse], summary="List warehouses")
def list_warehouses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    repo = WarehouseRepository(db)
    page_params = PageParams(page=page, page_size=page_size)
    items = repo.list(offset=page_params.offset, limit=page_params.page_size, active_only=active_only)
    total = repo.count(active_only=active_only)
    responses = [WarehouseResponse.model_validate(w) for w in items]
    return PaginatedResponse.create(responses, total, page_params)


@router.get("/{warehouse_id}", response_model=WarehouseResponse, summary="Get warehouse by ID")
def get_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_authenticated),
):
    repo = WarehouseRepository(db)
    wh = repo.get_by_id(warehouse_id)
    if not wh:
        raise NotFoundException(f"Warehouse with ID {warehouse_id} not found")
    return WarehouseResponse.model_validate(wh)


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED, summary="Create warehouse (ADMIN, MANAGER)")
def create_warehouse(
    req: WarehouseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager_or_admin),
):
    repo = WarehouseRepository(db)
    if repo.get_by_name(req.name):
        raise ConflictException(f"Warehouse with name '{req.name}' already exists")
    wh = Warehouse(name=req.name, location=req.location, is_active=req.is_active)
    repo.create(wh)
    db.commit()
    db.refresh(wh)
    return WarehouseResponse.model_validate(wh)


@router.patch("/{warehouse_id}", response_model=WarehouseResponse, summary="Update warehouse (ADMIN, MANAGER)")
def update_warehouse(
    warehouse_id: int,
    req: WarehouseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager_or_admin),
):
    repo = WarehouseRepository(db)
    wh = repo.get_by_id(warehouse_id)
    if not wh:
        raise NotFoundException(f"Warehouse with ID {warehouse_id} not found")
    if req.name and req.name.lower() != wh.name.lower():
        existing = repo.get_by_name(req.name)
        if existing and existing.id != warehouse_id:
            raise ConflictException(f"Warehouse with name '{req.name}' already exists")
        wh.name = req.name
    if req.location is not None:
        wh.location = req.location
    if req.is_active is not None:
        wh.is_active = req.is_active
    repo.update(wh)
    db.commit()
    db.refresh(wh)
    return WarehouseResponse.model_validate(wh)
