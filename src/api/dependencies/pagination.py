"""
Pagination dependencies for FastAPI.
"""


from fastapi import Query

from src.schemas.common import OrderDirection, PaginationParams


async def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    order_by: str | None = Query(None, description="Field to order by"),
    order_direction: OrderDirection = Query(OrderDirection.DESC, description="Order direction"),
) -> PaginationParams:
    """
    Get pagination parameters from query params.

    Args:
        page: Page number
        page_size: Items per page
        order_by: Field to order by
        order_direction: Order direction

    Returns:
        PaginationParams: Pagination parameters
    """
    return PaginationParams(
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_direction=order_direction,
    )


def calculate_offset(page: int, page_size: int) -> int:
    """
    Calculate offset for pagination.

    Args:
        page: Page number
        page_size: Items per page

    Returns:
        int: Offset value
    """
    return (page - 1) * page_size


def calculate_pages(total: int, page_size: int) -> int:
    """
    Calculate total number of pages.

    Args:
        total: Total number of items
        page_size: Items per page

    Returns:
        int: Total pages
    """
    return (total + page_size - 1) // page_size if total > 0 else 0
