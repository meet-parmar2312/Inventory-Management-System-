from datetime import timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, req: RegisterRequest) -> UserResponse:
        if self.user_repo.get_by_email(req.email):
            raise ConflictException(f"User with email '{req.email}' already exists")

        if self.user_repo.get_by_username(req.username):
            raise ConflictException(f"Username '{req.username}' is already taken")

        hashed_pw = get_password_hash(req.password)
        new_user = User(
            username=req.username,
            email=req.email.lower(),
            password_hash=hashed_pw,
            role=req.role,
            is_active=True,
        )
        self.user_repo.create(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return UserResponse.model_validate(new_user)

    def login(self, req: LoginRequest) -> TokenResponse:
        user = self.user_repo.get_by_identifier(req.username_or_email)
        if not user or not verify_password(req.password, user.password_hash):
            raise UnauthorizedException("Invalid username/email or password")

        if not user.is_active:
            raise UnauthorizedException("User account is inactive. Please contact administrator.")

        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            subject=user.id,
            role=user.role.value,
            expires_delta=expires_delta,
            extra_claims={"username": user.username},
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            username=user.username,
            role=user.role,
        )
