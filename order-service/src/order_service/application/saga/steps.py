from decimal import Decimal
from uuid import UUID

from order_service.domain.entities.order import Order
from order_service.domain.events.order_events import OrderEventType
from order_service.domain.exceptions.domain_errors import (
    CatalogValidationError,
    CustomerValidationError,
)
from order_service.domain.ports.repositories import (
    CatalogGateway,
    CustomerGateway,
    EventPublisher,
    NotificationGateway,
    OrderRepository,
    SagaRepository,
)


async def validate_customer(
    customer_gateway: CustomerGateway,
    customer_id: str,
) -> None:
    customer = await customer_gateway.get_customer(customer_id)
    if customer.status != "ACTIVE":
        raise CustomerValidationError(f"Customer {customer_id} is not active")


async def fetch_catalog_prices(
    catalog_gateway: CatalogGateway,
    order: Order,
) -> dict[str, Decimal]:
    prices: dict[str, Decimal] = {}
    for item in order.items:
        product = await catalog_gateway.get_product(item.product_id)
        if not product.available:
            raise CatalogValidationError(
                f"Product {item.product_id} unavailable"
            )
        prices[item.product_id] = product.price
    return prices


async def persist_confirmed_order(
    order_repo: OrderRepository,
    order: Order,
    prices: dict[str, Decimal],
) -> Order:
    order.version += 1
    order.confirm_with_prices(prices)
    return await order_repo.save(order)


async def publish_order_confirmed(
    event_publisher: EventPublisher,
    notification_gateway: NotificationGateway,
    order: Order,
) -> None:
    payload = {"orderId": str(order.id), "customerId": order.customer_id}
    await event_publisher.publish(OrderEventType.ORDER_CONFIRMED, payload)
    await notification_gateway.send_notification(
        order.customer_id,
        OrderEventType.ORDER_CONFIRMED,
        {"orderId": str(order.id), "total": str(order.total_amount.amount)},
    )


async def record_saga_step(
    saga_repo: SagaRepository,
    saga_id: UUID,
    order_id: UUID,
    step: str,
    status: str,
    payload: dict,
) -> None:
    await saga_repo.save_instance(saga_id, order_id, step, status, payload)
