from pydantic import BaseModel, EmailStr, Field
from app.utils.enums import UserRole


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., min_length=6, description="User password")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    role: UserRole = Field(default=UserRole.STAFF, description="Initial role assignment")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    username: str
    role: UserRole
