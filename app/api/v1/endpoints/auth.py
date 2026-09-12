from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register(req)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and retrieve JWT access token",
)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.login(req)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
