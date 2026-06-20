from order_service.domain.value_objects.order_status import OrderStatus

VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.DRAFT: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {
        OrderStatus.PAYMENT_PENDING,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PAYMENT_PENDING: {
        OrderStatus.PAID,
        OrderStatus.PAYMENT_FAILED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PAYMENT_FAILED: {
        OrderStatus.PAYMENT_PENDING,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PAID: set(),
    OrderStatus.CANCELLED: set(),
}


def can_transition(from_status: OrderStatus, to_status: OrderStatus) -> bool:
    return to_status in VALID_TRANSITIONS.get(from_status, set())
