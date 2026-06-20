from enum import StrEnum


class OrderStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    VOID = "VOID"


ACTIVE_ORDER_STATUSES = frozenset(
    {
        OrderStatus.DRAFT,
        OrderStatus.CONFIRMED,
        OrderStatus.PAYMENT_PENDING,
        OrderStatus.PAYMENT_FAILED,
    }
)

EDITABLE_ORDER_STATUSES = frozenset({OrderStatus.DRAFT})

CANCELLABLE_ORDER_STATUSES = frozenset(
    {
        OrderStatus.DRAFT,
        OrderStatus.CONFIRMED,
        OrderStatus.PAYMENT_PENDING,
        OrderStatus.PAYMENT_FAILED,
    }
)

MAX_PAYMENT_ATTEMPTS = 3
