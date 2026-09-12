from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total: int
    total_pages: int

    @classmethod
    def create(cls, items: List[T], total: int, page_params: PageParams):
        total_pages = (total + page_params.page_size - 1) // page_params.page_size if total > 0 else 0
        return cls(
            items=items,
            page=page_params.page,
            page_size=page_params.page_size,
            total=total,
            total_pages=total_pages,
        )
