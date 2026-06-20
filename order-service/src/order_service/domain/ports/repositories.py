from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from order_service.domain.entities.order import Order, Payment


@dataclass
class CustomerInfo:
    id: str
    name: str
    status: str


@dataclass
class ProductInfo:
    id: str
    name: str
    price: Decimal
    available: bool


@dataclass
class PaymentGatewayResult:
    external_id: str
    status: str


@dataclass
class PaginatedResult:
    items: list
    total: int
    page: int
    size: int

    @property
    def total_pages(self) -> int:
        if self.size <= 0:
            return 0
        return (self.total + self.size - 1) // self.size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1


class OrderRepository(ABC):
    @abstractmethod
    async def save(self, order: Order) -> Order:
        pass

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Order | None:
        pass

    @abstractmethod
    async def find_by_customer(
        self, customer_id: str, page: int, size: int
    ) -> PaginatedResult:
        pass

    @abstractmethod
    async def has_active_order(
        self, customer_id: str, exclude_order_id: UUID | None = None
    ) -> bool:
        pass


class PaymentRepository(ABC):
    @abstractmethod
    async def save(self, payment: Payment) -> Payment:
        pass

    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        pass

    @abstractmethod
    async def get_by_order_id(self, order_id: UUID) -> Payment | None:
        pass

    @abstractmethod
    async def find_by_order_ids(
        self, order_ids: list[UUID]
    ) -> dict[UUID, Payment]:
        pass

    @abstractmethod
    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        pass


class IdempotencyStore(ABC):
    @abstractmethod
    async def get(self, key: str, operation: str) -> dict | None:
        pass

    @abstractmethod
    async def save(
        self, key: str, operation: str, request_hash: str, response: dict
    ) -> None:
        pass


class CustomerGateway(ABC):
    @abstractmethod
    async def get_customer(self, customer_id: str) -> CustomerInfo:
        pass


class CatalogGateway(ABC):
    @abstractmethod
    async def get_product(self, product_id: str) -> ProductInfo:
        pass


class PaymentGateway(ABC):
    @abstractmethod
    async def initiate_payment(
        self, order_id: UUID, amount: Decimal, currency: str
    ) -> PaymentGatewayResult:
        pass


class NotificationGateway(ABC):
    @abstractmethod
    async def send_notification(
        self, customer_id: str, event_type: str, payload: dict
    ) -> None:
        pass


class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event_type: str, payload: dict) -> None:
        pass


class SagaRepository(ABC):
    @abstractmethod
    async def save_instance(
        self,
        saga_id: UUID,
        order_id: UUID,
        step: str,
        status: str,
        payload: dict,
    ) -> None:
        pass

    @abstractmethod
    async def get_by_order_id(self, order_id: UUID) -> dict | None:
        pass
