from decimal import Decimal

import pytest

from order_service.domain.value_objects.money import Money


def test_money_rejects_negative_amount():
    with pytest.raises(ValueError, match="negative"):
        Money(Decimal("-1"))


def test_money_rejects_currency_mismatch():
    with pytest.raises(ValueError, match="Currency"):
        Money(Decimal("1"), "BRL") + Money(Decimal("1"), "USD")


def test_money_addition_and_zero():
    total = Money(Decimal("10.50")) + Money(Decimal("2.50"))
    assert total.amount == Decimal("13.00")
    assert Money.zero().amount == Decimal("0")
