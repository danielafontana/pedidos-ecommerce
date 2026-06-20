from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request

from order_service.application.dto.order_dto import (
    InitiatePaymentRequest,
    PaymentCallbackRequest,
)
from order_service.presentation.auth import (
    limiter,
    require_payments_read,
    require_payments_write,
)
from order_service.presentation.dependencies import (
    get_get_payment_uc,
    get_initiate_payment_uc,
    get_payment_callback_uc,
)
from order_service.presentation.serializers import payment_to_dict

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", status_code=201)
@limiter.limit("30/minute")
async def initiate_payment(
    request: Request,
    body: InitiatePaymentRequest,
    uc=Depends(get_initiate_payment_uc),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    _=Depends(require_payments_write),
):
    payment = await uc.execute(body.order_id, idempotency_key)
    return payment_to_dict(payment)


@router.get("/{payment_id}")
@limiter.limit("120/minute")
async def get_payment(
    request: Request,
    payment_id: UUID,
    uc=Depends(get_get_payment_uc),
    _=Depends(require_payments_read),
):
    payment = await uc.execute(payment_id)
    return payment_to_dict(payment)


@router.post("/{payment_id}/callback")
@limiter.limit("60/minute")
async def payment_callback(
    request: Request,
    payment_id: UUID,
    body: PaymentCallbackRequest,
    uc=Depends(get_payment_callback_uc),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    _=Depends(require_payments_write),
):
    payment = await uc.execute(
        payment_id, body.status, body.transaction_id, idempotency_key
    )
    return payment_to_dict(payment)
