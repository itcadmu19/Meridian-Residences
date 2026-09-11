from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    """Shared response metadata (Design Contract §10)."""

    request_id: str | None = None
    page: int | None = None
    page_size: int | None = None
    total: int | None = None


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None
    meta: Meta = Meta()


class ErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    message: str
    error_code: str
    meta: Meta = Meta()
