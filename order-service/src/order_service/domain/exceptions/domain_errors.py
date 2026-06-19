class DomainError(Exception):
    """Base domain exception."""

    def __init__(self, message: str, code: str = "domain_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class OrderNotFoundError(DomainError):
    def __init__(self, order_id: str) -> None:
        super().__init__(f"Order {order_id} not found", "order_not_found")


class ItemNotFoundError(DomainError):
    def __init__(self, item_id: str) -> None:
        super().__init__(f"Item {item_id} not found", "item_not_found")


class PaymentNotFoundError(DomainError):
    def __init__(self, payment_id: str) -> None:
        super().__init__(f"Payment {payment_id} not found", "payment_not_found")


class InvalidOrderStateError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "invalid_order_state")


class CustomerValidationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "customer_validation_error")


class CatalogValidationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "catalog_validation_error")


class PaymentGatewayError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "payment_gateway_error")


class ActiveOrderExistsError(DomainError):
    def __init__(self, customer_id: str) -> None:
        super().__init__(
            f"Customer {customer_id} already has an active order",
            "active_order_exists",
        )


class ConcurrencyError(DomainError):
    def __init__(self) -> None:
        super().__init__("Concurrent modification detected", "concurrency_conflict")


class IdempotencyConflictError(DomainError):
    def __init__(self) -> None:
        super().__init__(
            "Idempotency key reused with different payload",
            "idempotency_conflict",
        )
