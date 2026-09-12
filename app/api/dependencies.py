from typing import Callable, Optional
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.enums import UserRole

security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authentication token is missing")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise UnauthorizedException(str(e))

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Malformed token payload")

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(int(user_id))

    if not user:
        raise UnauthorizedException("User associated with token does not exist")

    if not user.is_active:
        raise UnauthorizedException("User account has been deactivated")

    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    def role_verifier(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            role_names = [r.value for r in allowed_roles]
            raise ForbiddenException(
                f"Operation forbidden for role '{current_user.role.value}'. Required one of: {role_names}"
            )
        return current_user

    return role_verifier


require_admin = require_roles(UserRole.ADMIN)
require_manager_or_admin = require_roles(UserRole.ADMIN, UserRole.MANAGER)
require_authenticated = require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.STAFF)
