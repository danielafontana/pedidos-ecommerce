from enum import StrEnum


class OrderEventType(StrEnum):
    ORDER_CONFIRMED = "OrderConfirmed"
    ORDER_CANCELLED = "OrderCancelled"
    PAYMENT_INITIATED = "PaymentInitiated"
    PAYMENT_APPROVED = "PaymentApproved"
    PAYMENT_REJECTED = "PaymentRejected"
