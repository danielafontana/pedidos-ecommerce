from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from order_service.application.saga.orchestrator import OrderSagaOrchestrator
from order_service.application.use_cases.order_use_cases import (
    AddItemUseCase,
    CancelOrderUseCase,
    ConfirmOrderUseCase,
    CreateOrderUseCase,
    GetOrderUseCase,
    GetPaymentUseCase,
    InitiatePaymentUseCase,
    ListOrdersUseCase,
    PaymentCallbackUseCase,
    RemoveItemUseCase,
)
from order_service.infrastructure.http.gateways import (
    HttpCatalogGateway,
    HttpCustomerGateway,
    HttpNotificationGateway,
    HttpPaymentGateway,
)
from order_service.infrastructure.messaging.sqs_publisher import SqsEventPublisher
from order_service.infrastructure.persistence.database import (
    SessionLocal,
    SqlAlchemyIdempotencyStore,
    SqlAlchemySagaRepository,
)
from order_service.infrastructure.persistence.repositories import (
    SqlAlchemyOrderRepository,
    SqlAlchemyPaymentRepository,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


def get_create_order_uc(session: AsyncSession = Depends(get_session)) -> CreateOrderUseCase:
    return CreateOrderUseCase(SqlAlchemyOrderRepository(session), HttpCustomerGateway())


def get_get_order_uc(session: AsyncSession = Depends(get_session)) -> GetOrderUseCase:
    return GetOrderUseCase(SqlAlchemyOrderRepository(session), SqlAlchemyPaymentRepository(session))


def get_list_orders_uc(session: AsyncSession = Depends(get_session)) -> ListOrdersUseCase:
    return ListOrdersUseCase(SqlAlchemyOrderRepository(session), SqlAlchemyPaymentRepository(session))


def get_add_item_uc(session: AsyncSession = Depends(get_session)) -> AddItemUseCase:
    return AddItemUseCase(SqlAlchemyOrderRepository(session), HttpCatalogGateway())


def get_remove_item_uc(session: AsyncSession = Depends(get_session)) -> RemoveItemUseCase:
    return RemoveItemUseCase(SqlAlchemyOrderRepository(session))


def get_confirm_order_uc(session: AsyncSession = Depends(get_session)) -> ConfirmOrderUseCase:
    saga = OrderSagaOrchestrator(
        SqlAlchemyOrderRepository(session),
        HttpCustomerGateway(),
        HttpCatalogGateway(),
        SqsEventPublisher(),
        HttpNotificationGateway(),
        SqlAlchemySagaRepository(session),
    )
    return ConfirmOrderUseCase(
        SqlAlchemyOrderRepository(session), saga, SqlAlchemyIdempotencyStore(session)
    )


def get_cancel_order_uc(session: AsyncSession = Depends(get_session)) -> CancelOrderUseCase:
    return CancelOrderUseCase(
        SqlAlchemyOrderRepository(session),
        SqlAlchemyPaymentRepository(session),
        SqsEventPublisher(),
    )


def get_initiate_payment_uc(session: AsyncSession = Depends(get_session)) -> InitiatePaymentUseCase:
    return InitiatePaymentUseCase(
        SqlAlchemyOrderRepository(session),
        SqlAlchemyPaymentRepository(session),
        HttpPaymentGateway(),
        SqsEventPublisher(),
        SqlAlchemyIdempotencyStore(session),
    )


def get_get_payment_uc(session: AsyncSession = Depends(get_session)) -> GetPaymentUseCase:
    return GetPaymentUseCase(SqlAlchemyPaymentRepository(session))


def get_payment_callback_uc(session: AsyncSession = Depends(get_session)) -> PaymentCallbackUseCase:
    return PaymentCallbackUseCase(
        SqlAlchemyOrderRepository(session),
        SqlAlchemyPaymentRepository(session),
        SqsEventPublisher(),
        HttpNotificationGateway(),
        SqlAlchemyIdempotencyStore(session),
    )
