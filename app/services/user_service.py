from sqlalchemy.orm import Session
from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.pagination import PageParams, PaginatedResponse


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def list_users(self, page_params: PageParams) -> PaginatedResponse[UserResponse]:
        items = self.user_repo.list(offset=page_params.offset, limit=page_params.page_size)
        total = self.user_repo.count()
        responses = [UserResponse.model_validate(u) for u in items]
        return PaginatedResponse.create(responses, total, page_params)

    def get_user(self, user_id: int) -> UserResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")
        return UserResponse.model_validate(user)

    def create_user(self, req: UserCreate) -> UserResponse:
        if self.user_repo.get_by_email(req.email):
            raise ConflictException(f"User with email '{req.email}' already exists")
        if self.user_repo.get_by_username(req.username):
            raise ConflictException(f"Username '{req.username}' is already taken")

        new_user = User(
            username=req.username,
            email=req.email.lower(),
            password_hash=get_password_hash(req.password),
            role=req.role,
            is_active=True,
        )
        self.user_repo.create(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return UserResponse.model_validate(new_user)

    def update_user(self, user_id: int, req: UserUpdate) -> UserResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")

        if req.email and req.email.lower() != user.email:
            existing = self.user_repo.get_by_email(req.email)
            if existing and existing.id != user_id:
                raise ConflictException(f"Email '{req.email}' is already in use")
            user.email = req.email.lower()

        if req.username and req.username != user.username:
            existing = self.user_repo.get_by_username(req.username)
            if existing and existing.id != user_id:
                raise ConflictException(f"Username '{req.username}' is already in use")
            user.username = req.username

        if req.password:
            user.password_hash = get_password_hash(req.password)

        if req.role is not None:
            user.role = req.role

        if req.is_active is not None:
            user.is_active = req.is_active

        self.user_repo.update(user)
        self.db.commit()
        self.db.refresh(user)
        return UserResponse.model_validate(user)

    def delete_user(self, user_id: int) -> None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")
        self.user_repo.delete(user)
        self.db.commit()
