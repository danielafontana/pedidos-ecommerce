from uuid import UUID

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from order_service.infrastructure.security.jwt import require_scopes
from order_service.presentation.dependencies import (
    get_get_payment_uc,
    get_initiate_payment_uc,
    get_payment_callback_uc,
)
from order_service.presentation.serializers import payment_to_dict

router = APIRouter(prefix="/payments", tags=["payments"])


class InitiatePaymentRequest(BaseModel):
    order_id: UUID


class PaymentCallbackRequest(BaseModel):
    status: str
    transaction_id: str


@router.post("", status_code=201)
async def initiate_payment(
    body: InitiatePaymentRequest,
    uc=Depends(get_initiate_payment_uc),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    _=Depends(require_scopes("payments:write")),
):
    payment = await uc.execute(body.order_id, idempotency_key)
    return payment_to_dict(payment)


@router.get("/{payment_id}")
async def get_payment(
    payment_id: UUID,
    uc=Depends(get_get_payment_uc),
    _=Depends(require_scopes("payments:read")),
):
    payment = await uc.execute(payment_id)
    return payment_to_dict(payment)


@router.post("/{payment_id}/callback")
async def payment_callback(
    payment_id: UUID,
    body: PaymentCallbackRequest,
    uc=Depends(get_payment_callback_uc),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    _=Depends(require_scopes("payments:write")),
):
    payment = await uc.execute(
        payment_id, body.status, body.transaction_id, idempotency_key
    )
    return payment_to_dict(payment)
