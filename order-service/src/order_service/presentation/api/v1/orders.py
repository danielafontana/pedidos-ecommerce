from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel

from order_service.infrastructure.security.jwt import require_scopes
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


class CreateOrderRequest(BaseModel):
    customer_id: str


class AddItemRequest(BaseModel):
    product_id: str
    quantity: int


@router.post("", status_code=201)
async def create_order(
    body: CreateOrderRequest,
    uc=Depends(get_create_order_uc),
    _=Depends(require_scopes("orders:write")),
):
    order = await uc.execute(body.customer_id)
    return order_to_dict(order)


@router.get("/{order_id}")
async def get_order(
    order_id: UUID,
    uc=Depends(get_get_order_uc),
    _=Depends(require_scopes("orders:read")),
):
    order, payments = await uc.execute(order_id)
    return order_to_dict(order, payments)


@router.get("")
async def list_orders(
    customer_id: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    uc=Depends(get_list_orders_uc),
    _=Depends(require_scopes("orders:read")),
):
    result = await uc.execute(customer_id, page, size)
    payments_by_order = result["payments_by_order"]
    return {
        "items": [
            order_to_dict(
                order,
                [payments_by_order[order.id]] if order.id in payments_by_order else [],
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
async def add_item(
    order_id: UUID,
    body: AddItemRequest,
    uc=Depends(get_add_item_uc),
    _=Depends(require_scopes("orders:write")),
):
    order = await uc.execute(order_id, body.product_id, body.quantity)
    return order_to_dict(order)


@router.delete("/{order_id}/items/{item_id}")
async def remove_item(
    order_id: UUID,
    item_id: UUID,
    uc=Depends(get_remove_item_uc),
    _=Depends(require_scopes("orders:write")),
):
    order = await uc.execute(order_id, item_id)
    return order_to_dict(order)


@router.post("/{order_id}/confirm")
async def confirm_order(
    order_id: UUID,
    uc=Depends(get_confirm_order_uc),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    _=Depends(require_scopes("orders:write")),
):
    order = await uc.execute(order_id, idempotency_key)
    return order_to_dict(order)


@router.delete("/{order_id}")
async def cancel_order(
    order_id: UUID,
    uc=Depends(get_cancel_order_uc),
    _=Depends(require_scopes("orders:write")),
):
    order = await uc.execute(order_id)
    return order_to_dict(order)
