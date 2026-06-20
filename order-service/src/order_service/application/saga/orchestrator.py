from uuid import UUID, uuid4

from order_service.application.saga import compensations, steps
from order_service.domain.entities.order import Order
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

    async def confirm_order(self, order_id: UUID) -> Order:
        saga_id = uuid4()
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(str(order_id))

        await steps.record_saga_step(
            self._saga_repo,
            saga_id,
            order_id,
            "VALIDATE_CUSTOMER",
            "RUNNING",
            {},
        )

        try:
            await steps.validate_customer(
                self._customer_gateway, order.customer_id
            )
        except CustomerValidationError:
            await compensations.compensate_customer_validation_failure(
                self._saga_repo, saga_id, order_id
            )
            raise

        await steps.record_saga_step(
            self._saga_repo,
            saga_id,
            order_id,
            "VALIDATE_CATALOG",
            "RUNNING",
            {},
        )

        try:
            prices = await steps.fetch_catalog_prices(
                self._catalog_gateway, order
            )
        except CatalogValidationError:
            await compensations.compensate_catalog_validation_failure(
                self._saga_repo, saga_id, order_id
            )
            raise

        saved = await steps.persist_confirmed_order(
            self._order_repo, order, prices
        )

        await steps.record_saga_step(
            self._saga_repo,
            saga_id,
            order_id,
            "PERSIST_CONFIRMED",
            "COMPLETED",
            {"total": str(saved.total_amount.amount)},
        )
        await steps.publish_order_confirmed(
            self._event_publisher, self._notification_gateway, saved
        )
        return saved
