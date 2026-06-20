from decimal import Decimal

from order_service.domain.value_objects.money import Money


class PricingService:
    @staticmethod
    def calculate_total(
        line_items: list[tuple[str, int]],
        prices: dict[str, Decimal],
    ) -> Money:
        total = Money.zero()
        for product_id, quantity in line_items:
            if product_id not in prices:
                raise ValueError(f"Price missing for product {product_id}")
            unit = Money(prices[product_id])
            total = total + Money(unit.amount * quantity)
        return total
