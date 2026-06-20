from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from order_service.domain.entities.order import Order, OrderItem, Payment
from order_service.domain.exceptions.domain_errors import (
    ConcurrencyError,
    OrderNotFoundError,
)
from order_service.domain.ports.repositories import (
    OrderRepository,
    PaginatedResult,
    PaymentRepository,
)
from order_service.domain.value_objects.money import Money
from order_service.domain.value_objects.order_status import (
    ACTIVE_ORDER_STATUSES,
    OrderStatus,
    PaymentStatus,
)
from order_service.infrastructure.persistence.models import (
    OrderItemModel,
    OrderModel,
    PaymentModel,
)


def _to_domain_order(model: OrderModel) -> Order:
    items = [
        OrderItem(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=Money(Decimal(str(item.unit_price)))
            if item.unit_price is not None
            else None,
        )
        for item in model.items
    ]
    return Order(
        id=model.id,
        customer_id=model.customer_id,
        status=OrderStatus(model.status),
        items=items,
        total_amount=Money(Decimal(str(model.total_amount)), model.currency),
        payment_attempts=model.payment_attempts,
        version=model.version,
        created_at=model.created_at,
        updated_at=model.updated_at,
        cancellation_reason=model.cancellation_reason,
    )


def _apply_order_to_model(order: Order, model: OrderModel) -> None:
    model.customer_id = order.customer_id
    model.status = order.status.value
    model.total_amount = float(order.total_amount.amount)
    model.currency = order.total_amount.currency
    model.payment_attempts = order.payment_attempts
    model.version = order.version
    model.cancellation_reason = order.cancellation_reason
    model.updated_at = order.updated_at
    model.items.clear()
    for item in order.items:
        model.items.append(
            OrderItemModel(
                id=item.id,
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=float(item.unit_price.amount)
                if item.unit_price
                else None,
            )
        )


class SqlAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, order: Order) -> Order:
        if order.version == 1 and not await self.get_by_id(order.id):
            model = OrderModel(
                id=order.id,
                customer_id=order.customer_id,
                status=order.status.value,
                total_amount=float(order.total_amount.amount),
                currency=order.total_amount.currency,
                payment_attempts=order.payment_attempts,
                version=order.version,
                cancellation_reason=order.cancellation_reason,
                created_at=order.created_at,
                updated_at=order.updated_at,
            )
            for item in order.items:
                model.items.append(
                    OrderItemModel(
                        id=item.id,
                        order_id=order.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        unit_price=float(item.unit_price.amount)
                        if item.unit_price
                        else None,
                    )
                )
            self._session.add(model)
        else:
            result = await self._session.execute(
                select(OrderModel)
                .where(OrderModel.id == order.id)
                .options(selectinload(OrderModel.items))
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                raise OrderNotFoundError(str(order.id))
            if existing.version != order.version - 1:
                raise ConcurrencyError()
            _apply_order_to_model(order, existing)
        await self._session.commit()
        return order

    async def get_by_id(self, order_id: UUID) -> Order | None:
        result = await self._session.execute(
            select(OrderModel)
            .where(OrderModel.id == order_id)
            .options(selectinload(OrderModel.items))
        )
        model = result.scalar_one_or_none()
        return _to_domain_order(model) if model else None

    async def find_by_customer(
        self, customer_id: str, page: int, size: int
    ) -> PaginatedResult:
        offset = (page - 1) * size
        count_result = await self._session.execute(
            select(func.count())
            .select_from(OrderModel)
            .where(OrderModel.customer_id == customer_id)
        )
        total = count_result.scalar_one()
        result = await self._session.execute(
            select(OrderModel)
            .where(OrderModel.customer_id == customer_id)
            .options(selectinload(OrderModel.items))
            .order_by(OrderModel.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        items = [_to_domain_order(m) for m in result.scalars().all()]
        return PaginatedResult(items=items, total=total, page=page, size=size)

    async def has_active_order(
        self, customer_id: str, exclude_order_id: UUID | None = None
    ) -> bool:
        query = (
            select(func.count())
            .select_from(OrderModel)
            .where(
                OrderModel.customer_id == customer_id,
                OrderModel.status.in_(
                    [s.value for s in ACTIVE_ORDER_STATUSES]
                ),
            )
        )
        if exclude_order_id:
            query = query.where(OrderModel.id != exclude_order_id)
        result = await self._session.execute(query)
        return result.scalar_one() > 0


def _to_domain_payment(model: PaymentModel) -> Payment:
    return Payment(
        id=model.id,
        order_id=model.order_id,
        amount=Money(Decimal(str(model.amount)), model.currency),
        status=PaymentStatus(model.status),
        external_reference=model.external_reference,
        idempotency_key=model.idempotency_key,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyPaymentRepository(PaymentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, payment: Payment) -> Payment:
        result = await self._session.execute(
            select(PaymentModel).where(PaymentModel.id == payment.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            model = PaymentModel(
                id=payment.id,
                order_id=payment.order_id,
                amount=float(payment.amount.amount),
                currency=payment.amount.currency,
                status=payment.status.value,
                external_reference=payment.external_reference,
                idempotency_key=payment.idempotency_key,
                created_at=payment.created_at,
                updated_at=payment.updated_at,
            )
            self._session.add(model)
        else:
            model.status = payment.status.value
            model.external_reference = payment.external_reference
            model.updated_at = payment.updated_at
        await self._session.commit()
        return payment

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        result = await self._session.execute(
            select(PaymentModel).where(PaymentModel.id == payment_id)
        )
        model = result.scalar_one_or_none()
        return _to_domain_payment(model) if model else None

    async def get_by_order_id(self, order_id: UUID) -> Payment | None:
        result = await self._session.execute(
            select(PaymentModel).where(PaymentModel.order_id == order_id)
        )
        model = result.scalar_one_or_none()
        return _to_domain_payment(model) if model else None

    async def find_by_order_ids(
        self, order_ids: list[UUID]
    ) -> dict[UUID, Payment]:
        if not order_ids:
            return {}
        result = await self._session.execute(
            select(PaymentModel).where(PaymentModel.order_id.in_(order_ids))
        )
        return {
            model.order_id: _to_domain_payment(model)
            for model in result.scalars().all()
        }

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        result = await self._session.execute(
            select(PaymentModel).where(PaymentModel.idempotency_key == key)
        )
        model = result.scalar_one_or_none()
        return _to_domain_payment(model) if model else None
