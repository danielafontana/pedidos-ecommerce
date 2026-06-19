from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from order_service.domain.datetime_utils import now
from order_service.domain.exceptions.domain_errors import InvalidOrderStateError
from order_service.domain.value_objects.money import Money
from order_service.domain.value_objects.order_status import (
    CANCELLABLE_ORDER_STATUSES,
    EDITABLE_ORDER_STATUSES,
    MAX_PAYMENT_ATTEMPTS,
    OrderStatus,
    PaymentStatus,
)


@dataclass
class OrderItem:
    id: UUID
    product_id: str
    quantity: int
    unit_price: Money | None = None

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than zero")


@dataclass
class Order:
    id: UUID
    customer_id: str
    status: OrderStatus
    items: list[OrderItem] = field(default_factory=list)
    total_amount: Money = field(default_factory=Money.zero)
    payment_attempts: int = 0
    version: int = 1
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)
    cancellation_reason: str | None = None

    def can_add_items(self) -> bool:
        return self.status in EDITABLE_ORDER_STATUSES

    def can_remove_items(self) -> bool:
        return self.status in EDITABLE_ORDER_STATUSES

    def can_confirm(self) -> bool:
        return self.status == OrderStatus.DRAFT and len(self.items) > 0

    def can_cancel(self) -> bool:
        return self.status in CANCELLABLE_ORDER_STATUSES

    def can_initiate_payment(self) -> bool:
        return self.status in {OrderStatus.CONFIRMED, OrderStatus.PAYMENT_FAILED}

    def is_modifiable(self) -> bool:
        return self.status not in {OrderStatus.CANCELLED, OrderStatus.PAID}

    def add_item(self, product_id: str, quantity: int) -> OrderItem:
        if not self.can_add_items():
            raise InvalidOrderStateError("Cannot add items to order in current state")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        for item in self.items:
            if item.product_id == product_id:
                item.quantity += quantity
                self.updated_at = now()
                return item

        new_item = OrderItem(id=uuid4(), product_id=product_id, quantity=quantity)
        self.items.append(new_item)
        self.updated_at = now()
        return new_item

    def remove_item(self, item_id: UUID) -> None:
        if not self.can_remove_items():
            raise InvalidOrderStateError("Cannot remove items from order in current state")
        for index, item in enumerate(self.items):
            if item.id == item_id:
                del self.items[index]
                self.updated_at = now()
                return
        raise InvalidOrderStateError(f"Item {item_id} not in order")

    def confirm_with_prices(self, prices: dict[str, Decimal]) -> None:
        if not self.can_confirm():
            raise InvalidOrderStateError("Order cannot be confirmed")
        total = Money.zero()
        for item in self.items:
            if item.product_id not in prices:
                raise InvalidOrderStateError(f"Price missing for product {item.product_id}")
            item.unit_price = Money(prices[item.product_id])
            total = total + Money(item.unit_price.amount * item.quantity)
        self.total_amount = total
        self.status = OrderStatus.CONFIRMED
        self.updated_at = now()

    def mark_payment_pending(self) -> None:
        if not self.can_initiate_payment():
            raise InvalidOrderStateError("Payment cannot be initiated for this order")
        self.status = OrderStatus.PAYMENT_PENDING
        self.updated_at = now()

    def apply_payment_approved(self) -> None:
        if self.status != OrderStatus.PAYMENT_PENDING:
            raise InvalidOrderStateError("Order is not awaiting payment result")
        self.status = OrderStatus.PAID
        self.updated_at = now()

    def apply_payment_rejected(self) -> None:
        if self.status != OrderStatus.PAYMENT_PENDING:
            raise InvalidOrderStateError("Order is not awaiting payment result")
        self.payment_attempts += 1
        if self.payment_attempts >= MAX_PAYMENT_ATTEMPTS:
            self.status = OrderStatus.CANCELLED
            self.cancellation_reason = "Auto-cancelled after 3 payment rejections"
        else:
            self.status = OrderStatus.PAYMENT_FAILED
        self.updated_at = now()

    def cancel(self, reason: str | None = None) -> None:
        if not self.can_cancel():
            raise InvalidOrderStateError("Order cannot be cancelled in current state")
        self.status = OrderStatus.CANCELLED
        self.cancellation_reason = reason
        self.updated_at = now()


@dataclass
class Payment:
    id: UUID
    order_id: UUID
    amount: Money
    status: PaymentStatus
    external_reference: str | None = None
    idempotency_key: str | None = None
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def approve(self, external_reference: str) -> None:
        self.status = PaymentStatus.APPROVED
        self.external_reference = external_reference
        self.updated_at = now()

    def reject(self) -> None:
        self.status = PaymentStatus.REJECTED
        self.updated_at = now()

    def void_payment(self) -> None:
        self.status = PaymentStatus.VOID
        self.updated_at = now()

    def reinitiate(self, external_reference: str) -> None:
        if self.status != PaymentStatus.REJECTED:
            raise InvalidOrderStateError("Only rejected payments can be reinitiated")
        self.status = PaymentStatus.PENDING
        self.external_reference = external_reference
        self.updated_at = now()
