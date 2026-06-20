from dataclasses import dataclass
from decimal import Decimal

MONEY_QUANT = Decimal("0.01")


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "BRL"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount + other.amount, self.currency)

    @classmethod
    def zero(cls, currency: str = "BRL") -> "Money":
        return cls(Decimal("0"), currency)

    @staticmethod
    def format_amount(amount: Decimal) -> str:
        return f"{amount.quantize(MONEY_QUANT):.2f}"
