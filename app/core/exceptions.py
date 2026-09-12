from typing import Any, Optional


class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class NotFoundException(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, status_code=404, details=details)


class ConflictException(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, status_code=409, details=details)


class InsufficientStockException(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, status_code=409, details=details)


class InvalidStateTransitionException(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, status_code=400, details=details)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Invalid credentials or authentication required"):
        super().__init__(message=message, status_code=401)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Access forbidden: insufficient role permissions"):
        super().__init__(message=message, status_code=403)
