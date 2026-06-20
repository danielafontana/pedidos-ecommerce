from decimal import Decimal
from uuid import uuid4

import pytest

from order_service.domain.entities.order import Order
from order_service.domain.exceptions.domain_errors import (
    InvalidOrderStateError,
)
from order_service.domain.value_objects.order_status import OrderStatus


def test_create_order_in_draft():
    order = Order(id=uuid4(), customer_id="1", status=OrderStatus.DRAFT)
    assert order.status == OrderStatus.DRAFT
    assert order.can_add_items()


def test_cannot_confirm_without_items():
    order = Order(id=uuid4(), customer_id="1", status=OrderStatus.DRAFT)
    with pytest.raises(InvalidOrderStateError):
        order.confirm_with_prices({})


def test_confirm_with_prices():
    order = Order(id=uuid4(), customer_id="1", status=OrderStatus.DRAFT)
    order.add_item("prod-1", 2)
    order.confirm_with_prices({"prod-1": Decimal("10.00")})
    assert order.status == OrderStatus.CONFIRMED
    assert order.total_amount.amount == Decimal("20.00")
    assert not order.can_add_items()


def test_increment_quantity_for_same_product():
    order = Order(id=uuid4(), customer_id="1", status=OrderStatus.DRAFT)
    order.add_item("prod-1", 1)
    order.add_item("prod-1", 2)
    assert len(order.items) == 1
    assert order.items[0].quantity == 3


def test_payment_rejection_auto_cancel_after_three_attempts():
    order = Order(id=uuid4(), customer_id="1", status=OrderStatus.DRAFT)
    order.add_item("prod-1", 1)
    order.confirm_with_prices({"prod-1": Decimal("10")})
    order.mark_payment_pending()
    for _ in range(2):
        order.apply_payment_rejected()
        order.mark_payment_pending()
    order.apply_payment_rejected()
    assert order.status == OrderStatus.CANCELLED


def test_cannot_cancel_paid_order():
    order = Order(
        id=uuid4(), customer_id="1", status=OrderStatus.PAYMENT_PENDING
    )
    order.apply_payment_approved()
    with pytest.raises(InvalidOrderStateError):
        order.cancel()


def test_can_cancel_while_payment_pending():
    order = Order(
        id=uuid4(), customer_id="1", status=OrderStatus.PAYMENT_PENDING
    )
    assert order.can_cancel()
    order.cancel("customer request")
    assert order.status == OrderStatus.CANCELLED
