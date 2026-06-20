from __future__ import annotations

from typing import Any, cast

from httpx import AsyncClient, Response


async def create_order(
    client: AsyncClient, customer_id: str = "1"
) -> Response:
    return await client.post(
        "/api/v1/orders", json={"customer_id": customer_id}
    )


async def add_item(
    client: AsyncClient,
    order_id: str,
    product_id: str = "prod-1",
    quantity: int = 1,
) -> Response:
    return await client.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": product_id, "quantity": quantity},
    )


async def confirm_order(
    client: AsyncClient,
    order_id: str,
    idempotency_key: str | None = None,
) -> Response:
    headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
    return await client.post(
        f"/api/v1/orders/{order_id}/confirm", headers=headers
    )


async def initiate_payment(
    client: AsyncClient,
    order_id: str,
    idempotency_key: str | None = None,
) -> Response:
    headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
    return await client.post(
        "/api/v1/payments", json={"order_id": order_id}, headers=headers
    )


async def payment_callback(
    client: AsyncClient,
    payment_id: str,
    status: str = "APPROVED",
    transaction_id: str = "txn-integration-001",
    idempotency_key: str | None = None,
) -> Response:
    headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
    return await client.post(
        f"/api/v1/payments/{payment_id}/callback",
        json={"status": status, "transaction_id": transaction_id},
        headers=headers,
    )


async def cancel_order(client: AsyncClient, order_id: str) -> Response:
    return await client.delete(f"/api/v1/orders/{order_id}")


async def get_order(client: AsyncClient, order_id: str) -> Response:
    return await client.get(f"/api/v1/orders/{order_id}")


async def create_confirmed_order(
    client: AsyncClient,
    customer_id: str = "1",
    product_id: str = "prod-1",
    quantity: int = 1,
) -> dict[str, Any]:
    create_response = await create_order(client, customer_id)
    assert create_response.status_code == 201, create_response.text
    order = create_response.json()

    add_response = await add_item(client, order["id"], product_id, quantity)
    assert add_response.status_code == 201, add_response.text

    confirm_response = await confirm_order(client, order["id"])
    assert confirm_response.status_code == 200, confirm_response.text
    return cast(dict[str, Any], confirm_response.json())
