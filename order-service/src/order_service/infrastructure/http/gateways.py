from decimal import Decimal
from uuid import UUID

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from order_service.domain.exceptions.domain_errors import (
    CatalogValidationError,
    CustomerValidationError,
    PaymentGatewayError,
)
from order_service.domain.ports.repositories import (
    CatalogGateway,
    CustomerGateway,
    CustomerInfo,
    NotificationGateway,
    PaymentGateway,
    PaymentGatewayResult,
    ProductInfo,
)
from order_service.infrastructure.config import settings


class HttpCustomerGateway(CustomerGateway):
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=settings.customer_service_url, timeout=10.0
        )

    async def get_customer(self, customer_id: str) -> CustomerInfo:
        response = await self._client.get(f"/{customer_id}")
        if response.status_code == 404:
            raise CustomerValidationError(f"Customer {customer_id} not found")
        if response.status_code == 422:
            raise CustomerValidationError(f"Customer {customer_id} is blocked")
        if response.status_code != 200:
            raise CustomerValidationError(
                f"Customer validation failed: {response.status_code}"
            )
        data = response.json()
        return CustomerInfo(
            id=data["id"], name=data["name"], status=data["status"]
        )


class HttpCatalogGateway(CatalogGateway):
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=settings.catalog_service_url, timeout=10.0
        )

    async def get_product(self, product_id: str) -> ProductInfo:
        response = await self._client.get(f"/{product_id}")
        if response.status_code == 404:
            raise CatalogValidationError(f"Product {product_id} not found")
        if response.status_code == 422:
            raise CatalogValidationError(f"Product {product_id} unavailable")
        if response.status_code != 200:
            raise CatalogValidationError(
                f"Catalog validation failed: {response.status_code}"
            )
        data = response.json()
        return ProductInfo(
            id=data["id"],
            name=data["name"],
            price=Decimal(str(data["price"])),
            available=data.get("available", True),
        )


def _is_transient_gateway_error(exc: BaseException) -> bool:
    return (
        isinstance(exc, PaymentGatewayError)
        and "unavailable" in exc.message.lower()
    )


class HttpPaymentGateway(PaymentGateway):
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._url = settings.payment_gateway_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=10.0)

    @retry(
        retry=retry_if_exception(_is_transient_gateway_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        reraise=True,
    )
    async def initiate_payment(
        self, order_id: UUID, amount: Decimal, currency: str
    ) -> PaymentGatewayResult:
        response = await self._client.post(
            self._url,
            json={
                "orderId": str(order_id),
                "amount": str(amount),
                "currency": currency,
            },
        )
        if response.status_code == 503:
            raise PaymentGatewayError("Payment gateway unavailable")
        if response.status_code != 200:
            raise PaymentGatewayError(
                f"Payment gateway error: {response.status_code}"
            )
        data = response.json()
        return PaymentGatewayResult(
            external_id=data["transactionId"], status=data["status"]
        )


class HttpNotificationGateway(NotificationGateway):
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._url = settings.notification_service_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def send_notification(
        self, customer_id: str, event_type: str, payload: dict
    ) -> None:
        await self._client.post(
            self._url,
            json={
                "customerId": customer_id,
                "eventType": event_type,
                "payload": payload,
            },
        )
