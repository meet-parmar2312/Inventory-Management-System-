from typing import List, Optional
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.execute(select(User).where(User.username == username)).scalar_one_or_none()

    def get_by_identifier(self, identifier: str) -> Optional[User]:
        clean_ident = identifier.strip().lower()
        stmt = select(User).where(
            or_(
                func.lower(User.username) == clean_ident,
                func.lower(User.email) == clean_ident,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, offset: int = 0, limit: int = 20) -> List[User]:
        stmt = select(User).order_by(User.id.asc()).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        return self.db.execute(select(func.count(User.id))).scalar() or 0

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def update(self, user: User) -> User:
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()
