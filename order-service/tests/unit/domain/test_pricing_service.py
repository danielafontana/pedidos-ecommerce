from decimal import Decimal

from order_service.domain.services.pricing_service import PricingService


def test_calculate_total_from_line_items():
    total = PricingService.calculate_total(
        [("prod-1", 2)], {"prod-1": Decimal("10.00")}
    )
    assert total.amount == Decimal("20.00")
