from order_service.domain.services.state_machine import can_transition
from order_service.domain.value_objects.order_status import OrderStatus


def test_draft_to_confirmed():
    assert can_transition(OrderStatus.DRAFT, OrderStatus.CONFIRMED)


def test_confirmed_to_payment_pending():
    assert can_transition(OrderStatus.CONFIRMED, OrderStatus.PAYMENT_PENDING)


def test_paid_has_no_transitions():
    assert not can_transition(OrderStatus.PAID, OrderStatus.CANCELLED)


def test_payment_pending_to_cancelled():
    assert can_transition(OrderStatus.PAYMENT_PENDING, OrderStatus.CANCELLED)
