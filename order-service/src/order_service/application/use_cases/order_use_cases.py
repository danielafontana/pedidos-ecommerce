import hashlib
import json
from uuid import UUID, uuid4

from order_service.domain.entities.order import Order, Payment
from order_service.domain.exceptions.domain_errors import (
    ActiveOrderExistsError,
    CatalogValidationError,
    CustomerValidationError,
    IdempotencyConflictError,
    InvalidOrderStateError,
    ItemNotFoundError,
    OrderNotFoundError,
    PaymentGatewayError,
    PaymentNotFoundError,
)
from order_service.domain.ports.repositories import (
    CatalogGateway,
    CustomerGateway,
    EventPublisher,
    IdempotencyStore,
    NotificationGateway,
    OrderRepository,
    PaymentGateway,
    PaymentRepository,
    SagaRepository,
)
from order_service.domain.value_objects.money import Money
from order_service.domain.value_objects.order_status import OrderStatus, PaymentStatus
from order_service.application.saga.orchestrator import OrderSagaOrchestrator


class CreateOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        customer_gateway: CustomerGateway,
    ) -> None:
        self._order_repo = order_repo
        self._customer_gateway = customer_gateway

    async def execute(self, customer_id: str) -> Order:
        customer = await self._customer_gateway.get_customer(customer_id)
        if customer.status != "ACTIVE":
            raise CustomerValidationError(f"Customer {customer_id} is not active")
        if await self._order_repo.has_active_order(customer_id):
            raise ActiveOrderExistsError(customer_id)
        order = Order(id=uuid4(), customer_id=customer_id, status=OrderStatus.DRAFT)
        return await self._order_repo.save(order)


class GetOrderUseCase:
    def __init__(self, order_repo: OrderRepository, payment_repo: PaymentRepository) -> None:
        self._order_repo = order_repo
        self._payment_repo = payment_repo

    async def execute(self, order_id: UUID) -> tuple[Order, list[Payment]]:
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(str(order_id))
        payment = await self._payment_repo.get_by_order_id(order_id)
        payments = [payment] if payment else []
        return order, payments


class ListOrdersUseCase:
    def __init__(self, order_repo: OrderRepository, payment_repo: PaymentRepository) -> None:
        self._order_repo = order_repo
        self._payment_repo = payment_repo

    async def execute(self, customer_id: str, page: int = 1, size: int = 20) -> dict:
        size = min(max(size, 1), 100)
        page = max(page, 1)
        result = await self._order_repo.find_by_customer(customer_id, page, size)
        payments_by_order = await self._payment_repo.find_by_order_ids([o.id for o in result.items])
        return {
            "items": result.items,
            "payments_by_order": payments_by_order,
            "page": result.page,
            "size": result.size,
            "total": result.total,
            "total_pages": result.total_pages,
            "has_next": result.has_next,
            "has_previous": result.has_previous,
        }


class AddItemUseCase:
    def __init__(self, order_repo: OrderRepository, catalog_gateway: CatalogGateway) -> None:
        self._order_repo = order_repo
        self._catalog_gateway = catalog_gateway

    async def execute(self, order_id: UUID, product_id: str, quantity: int) -> Order:
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(str(order_id))
        product = await self._catalog_gateway.get_product(product_id)
        if not product.available:
            raise CatalogValidationError(f"Product {product_id} unavailable")
        order.version += 1
        order.add_item(product_id, quantity)
        return await self._order_repo.save(order)


class RemoveItemUseCase:
    def __init__(self, order_repo: OrderRepository) -> None:
        self._order_repo = order_repo

    async def execute(self, order_id: UUID, item_id: UUID) -> Order:
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(str(order_id))
        try:
            order.version += 1
            order.remove_item(item_id)
        except InvalidOrderStateError as exc:
            if "not in order" in str(exc):
                raise ItemNotFoundError(str(item_id)) from exc
            raise
        return await self._order_repo.save(order)


class ConfirmOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        saga: OrderSagaOrchestrator,
        idempotency: IdempotencyStore,
    ) -> None:
        self._order_repo = order_repo
        self._saga = saga
        self._idempotency = idempotency

    async def execute(self, order_id: UUID, idempotency_key: str | None = None) -> Order:
        request_hash = hashlib.sha256(str(order_id).encode()).hexdigest()
        if idempotency_key:
            cached = await self._idempotency.get(idempotency_key, "confirm_order")
            if cached:
                if cached["request_hash"] != request_hash:
                    raise IdempotencyConflictError()
                cached_order = await self._order_repo.get_by_id(order_id)
                if cached_order:
                    return cached_order

        order = await self._saga.confirm_order(order_id)

        if idempotency_key:
            await self._idempotency.save(
                idempotency_key,
                "confirm_order",
                request_hash,
                {"orderId": str(order.id), "status": order.status.value},
            )
        return order


class CancelOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        payment_repo: PaymentRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._order_repo = order_repo
        self._payment_repo = payment_repo
        self._event_publisher = event_publisher

    async def execute(self, order_id: UUID, reason: str | None = None) -> Order:
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(str(order_id))
        payment = await self._payment_repo.get_by_order_id(order_id)
        if payment and payment.status == PaymentStatus.PENDING:
            payment.void_payment()
            await self._payment_repo.save(payment)
        order.version += 1
        order.cancel(reason)
        saved = await self._order_repo.save(order)
        await self._event_publisher.publish(
            "OrderCancelled", {"orderId": str(order_id), "reason": reason}
        )
        return saved


class InitiatePaymentUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        payment_repo: PaymentRepository,
        payment_gateway: PaymentGateway,
        event_publisher: EventPublisher,
        idempotency: IdempotencyStore,
    ) -> None:
        self._order_repo = order_repo
        self._payment_repo = payment_repo
        self._payment_gateway = payment_gateway
        self._event_publisher = event_publisher
        self._idempotency = idempotency

    async def execute(self, order_id: UUID, idempotency_key: str | None = None) -> Payment:
        request_hash = hashlib.sha256(str(order_id).encode()).hexdigest()
        if idempotency_key:
            existing = await self._payment_repo.get_by_idempotency_key(idempotency_key)
            if existing:
                return existing
            cached = await self._idempotency.get(idempotency_key, "initiate_payment")
            if cached and cached["request_hash"] != request_hash:
                raise IdempotencyConflictError()

        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(str(order_id))
        if not order.can_initiate_payment():
            raise InvalidOrderStateError("Payment can only be initiated for confirmed orders")

        existing_payment = await self._payment_repo.get_by_order_id(order_id)
        if existing_payment and existing_payment.status in {
            PaymentStatus.PENDING,
            PaymentStatus.APPROVED,
        }:
            return existing_payment

        previous_status = order.status
        order.version += 1
        order.mark_payment_pending()
        await self._order_repo.save(order)

        try:
            result = await self._payment_gateway.initiate_payment(
                order_id, order.total_amount.amount, order.total_amount.currency
            )
        except PaymentGatewayError:
            order = await self._order_repo.get_by_id(order_id)
            if order and order.status == OrderStatus.PAYMENT_PENDING:
                order.version += 1
                order.status = previous_status
                await self._order_repo.save(order)
            raise

        if existing_payment and existing_payment.status == PaymentStatus.REJECTED:
            existing_payment.reinitiate(result.external_id)
            saved = await self._payment_repo.save(existing_payment)
        else:
            payment = Payment(
                id=uuid4(),
                order_id=order_id,
                amount=order.total_amount,
                status=PaymentStatus.PENDING,
                external_reference=result.external_id,
                idempotency_key=idempotency_key,
            )
            saved = await self._payment_repo.save(payment)
        await self._event_publisher.publish(
            "PaymentInitiated", {"orderId": str(order_id), "paymentId": str(saved.id)}
        )

        if idempotency_key:
            await self._idempotency.save(
                idempotency_key,
                "initiate_payment",
                request_hash,
                {"paymentId": str(saved.id), "status": saved.status.value},
            )
        return saved


class GetPaymentUseCase:
    def __init__(self, payment_repo: PaymentRepository) -> None:
        self._payment_repo = payment_repo

    async def execute(self, payment_id: UUID) -> Payment:
        payment = await self._payment_repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError(str(payment_id))
        return payment


class PaymentCallbackUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        payment_repo: PaymentRepository,
        event_publisher: EventPublisher,
        notification_gateway: NotificationGateway,
        idempotency: IdempotencyStore,
    ) -> None:
        self._order_repo = order_repo
        self._payment_repo = payment_repo
        self._event_publisher = event_publisher
        self._notification_gateway = notification_gateway
        self._idempotency = idempotency

    async def execute(
        self,
        payment_id: UUID,
        status: str,
        transaction_id: str,
        idempotency_key: str | None = None,
    ) -> Payment:
        request_hash = hashlib.sha256(f"{payment_id}:{status}:{transaction_id}".encode()).hexdigest()
        if idempotency_key:
            cached = await self._idempotency.get(idempotency_key, "payment_callback")
            if cached:
                if cached["request_hash"] != request_hash:
                    raise IdempotencyConflictError()
                payment = await self._payment_repo.get_by_id(payment_id)
                if payment:
                    return payment

        payment = await self._payment_repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError(str(payment_id))
        if payment.status in {PaymentStatus.APPROVED, PaymentStatus.REJECTED, PaymentStatus.VOID}:
            return payment

        order = await self._order_repo.get_by_id(payment.order_id)
        if order is None:
            raise OrderNotFoundError(str(payment.order_id))

        order.version += 1
        if status.upper() == "APPROVED":
            payment.approve(transaction_id)
            order.apply_payment_approved()
            event_type = "PaymentApproved"
        else:
            payment.reject()
            order.apply_payment_rejected()
            event_type = "PaymentRejected"

        await self._payment_repo.save(payment)
        await self._order_repo.save(order)
        await self._event_publisher.publish(
            event_type, {"orderId": str(order.id), "paymentId": str(payment.id)}
        )
        await self._notification_gateway.send_notification(
            order.customer_id,
            event_type,
            {"orderId": str(order.id), "status": order.status.value},
        )

        if idempotency_key:
            await self._idempotency.save(
                idempotency_key,
                "payment_callback",
                request_hash,
                {"paymentId": str(payment.id), "status": payment.status.value},
            )
        return payment
