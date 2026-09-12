from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.utils.pagination import PageParams, PaginatedResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List all users (ADMIN only)",
)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    service = UserService(db)
    return service.list_users(PageParams(page=page, page_size=page_size))


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user details by ID (ADMIN only)",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    service = UserService(db)
    return service.get_user(user_id)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (ADMIN only)",
)
def create_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    service = UserService(db)
    return service.create_user(req)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user details (ADMIN only)",
)
def update_user(
    user_id: int,
    req: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    service = UserService(db)
    return service.update_user(user_id, req)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (ADMIN only)",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    service = UserService(db)
    service.delete_user(user_id)
