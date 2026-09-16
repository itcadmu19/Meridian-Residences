"""
Standard response envelope (Project Design Document section 10).

Shared across all four stories - not lease-specific, but placed here since
nothing existed yet. Please reuse rather than reinventing per-story shapes.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    request_id: str | None = None
    page: int | None = None
    page_size: int | None = None
    total: int | None = None


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None
    meta: Meta = Meta()


class ListResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    meta: Meta


class ErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    message: str
    error_code: str
    meta: Meta = Meta()
