from uuid import UUID

from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    customer_id: str


class AddItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)


class InitiatePaymentRequest(BaseModel):
    order_id: UUID


class PaymentCallbackRequest(BaseModel):
    status: str
    transaction_id: str
