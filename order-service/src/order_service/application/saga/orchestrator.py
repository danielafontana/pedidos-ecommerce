from decimal import Decimal
from uuid import UUID, uuid4

from order_service.domain.exceptions.domain_errors import (
    CatalogValidationError,
    CustomerValidationError,
    OrderNotFoundError,
)
from order_service.domain.ports.repositories import (
    CatalogGateway,
    CustomerGateway,
    EventPublisher,
    NotificationGateway,
    OrderRepository,
    SagaRepository,
)


class OrderSagaOrchestrator:
    """Orchestrated saga for order confirmation with compensations."""

    def __init__(
        self,
        order_repo: OrderRepository,
        customer_gateway: CustomerGateway,
        catalog_gateway: CatalogGateway,
        event_publisher: EventPublisher,
        notification_gateway: NotificationGateway,
        saga_repo: SagaRepository,
    ) -> None:
        self._order_repo = order_repo
        self._customer_gateway = customer_gateway
        self._catalog_gateway = catalog_gateway
        self._event_publisher = event_publisher
        self._notification_gateway = notification_gateway
        self._saga_repo = saga_repo

    async def confirm_order(self, order_id: UUID):
        saga_id = uuid4()
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(str(order_id))

        await self._saga_repo.save_instance(
            saga_id, order_id, "VALIDATE_CUSTOMER", "RUNNING", {}
        )

        try:
            customer = await self._customer_gateway.get_customer(order.customer_id)
            if customer.status != "ACTIVE":
                raise CustomerValidationError(f"Customer {order.customer_id} is not active")
        except CustomerValidationError:
            await self._saga_repo.save_instance(
                saga_id, order_id, "VALIDATE_CUSTOMER", "FAILED", {"reason": "customer_invalid"}
            )
            raise

        await self._saga_repo.save_instance(
            saga_id, order_id, "VALIDATE_CATALOG", "RUNNING", {}
        )

        prices: dict[str, str] = {}
        try:
            for item in order.items:
                product = await self._catalog_gateway.get_product(item.product_id)
                if not product.available:
                    raise CatalogValidationError(f"Product {item.product_id} unavailable")
                prices[item.product_id] = str(product.price)
        except CatalogValidationError:
            await self._saga_repo.save_instance(
                saga_id, order_id, "VALIDATE_CATALOG", "COMPENSATED", {"action": "keep_draft"}
            )
            raise

        order.version += 1
        order.confirm_with_prices({k: Decimal(v) for k, v in prices.items()})
        saved = await self._order_repo.save(order)

        await self._saga_repo.save_instance(
            saga_id,
            order_id,
            "PERSIST_CONFIRMED",
            "COMPLETED",
            {"total": str(saved.total_amount.amount)},
        )
        await self._event_publisher.publish(
            "OrderConfirmed",
            {"orderId": str(saved.id), "customerId": saved.customer_id},
        )
        await self._notification_gateway.send_notification(
            saved.customer_id,
            "OrderConfirmed",
            {"orderId": str(saved.id), "total": str(saved.total_amount.amount)},
        )
        return saved
