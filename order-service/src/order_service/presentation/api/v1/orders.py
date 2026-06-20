from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request

from order_service.application.dto.order_dto import (
    AddItemRequest,
    CreateOrderRequest,
)
from order_service.presentation.auth import (
    limiter,
    require_orders_read,
    require_orders_write,
)
from order_service.presentation.dependencies import (
    get_add_item_uc,
    get_cancel_order_uc,
    get_confirm_order_uc,
    get_create_order_uc,
    get_get_order_uc,
    get_list_orders_uc,
    get_remove_item_uc,
)
from order_service.presentation.serializers import order_to_dict

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", status_code=201)
@limiter.limit("60/minute")
async def create_order(
    request: Request,
    body: CreateOrderRequest,
    uc=Depends(get_create_order_uc),
    _=Depends(require_orders_write),
):
    order = await uc.execute(body.customer_id)
    return order_to_dict(order)


@router.get("/{order_id}")
@limiter.limit("120/minute")
async def get_order(
    request: Request,
    order_id: UUID,
    uc=Depends(get_get_order_uc),
    _=Depends(require_orders_read),
):
    order, payments = await uc.execute(order_id)
    return order_to_dict(order, payments)


@router.get("")
@limiter.limit("120/minute")
async def list_orders(
    request: Request,
    customer_id: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    uc=Depends(get_list_orders_uc),
    _=Depends(require_orders_read),
):
    result = await uc.execute(customer_id, page, size)
    payments_by_order = result["payments_by_order"]
    return {
        "items": [
            order_to_dict(
                order,
                [payments_by_order[order.id]]
                if order.id in payments_by_order
                else [],
            )
            for order in result["items"]
        ],
        "page": result["page"],
        "size": result["size"],
        "total": result["total"],
        "total_pages": result["total_pages"],
        "has_next": result["has_next"],
        "has_previous": result["has_previous"],
    }


@router.post("/{order_id}/items", status_code=201)
@limiter.limit("60/minute")
async def add_item(
    request: Request,
    order_id: UUID,
    body: AddItemRequest,
    uc=Depends(get_add_item_uc),
    _=Depends(require_orders_write),
):
    order = await uc.execute(order_id, body.product_id, body.quantity)
    return order_to_dict(order)


@router.delete("/{order_id}/items/{item_id}")
@limiter.limit("60/minute")
async def remove_item(
    request: Request,
    order_id: UUID,
    item_id: UUID,
    uc=Depends(get_remove_item_uc),
    _=Depends(require_orders_write),
):
    order = await uc.execute(order_id, item_id)
    return order_to_dict(order)


@router.post("/{order_id}/confirm")
@limiter.limit("30/minute")
async def confirm_order(
    request: Request,
    order_id: UUID,
    uc=Depends(get_confirm_order_uc),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    _=Depends(require_orders_write),
):
    order = await uc.execute(order_id, idempotency_key)
    return order_to_dict(order)


@router.delete("/{order_id}")
@limiter.limit("30/minute")
async def cancel_order(
    request: Request,
    order_id: UUID,
    uc=Depends(get_cancel_order_uc),
    _=Depends(require_orders_write),
):
    order = await uc.execute(order_id)
    return order_to_dict(order)
