"""Integration tests for the full order lifecycle (plano.md steps 1-5)."""

import pytest
from httpx import AsyncClient

from .api_helpers import (
    add_item,
    confirm_order,
    create_order,
    initiate_payment,
    payment_callback,
)

pytestmark = pytest.mark.integration


async def test_full_order_lifecycle_create_confirm_pay(
    client: AsyncClient,
) -> None:
    create_response = await create_order(client, customer_id="1")
    assert create_response.status_code == 201
    order = create_response.json()
    assert order["status"] == "DRAFT"

    add_response = await add_item(client, order["id"], quantity=2)
    assert add_response.status_code == 201

    confirm_response = await confirm_order(client, order["id"])
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()
    assert confirmed["status"] == "CONFIRMED"
    assert confirmed["total_amount"] == "199.80"
    assert confirmed["items"][0]["unit_price"] == "99.90"

    payment_response = await initiate_payment(client, order["id"])
    assert payment_response.status_code == 201
    payment = payment_response.json()
    assert payment["status"] == "PENDING"

    order_after_payment = await client.get(f"/api/v1/orders/{order['id']}")
    assert order_after_payment.json()["status"] == "PAYMENT_PENDING"

    callback_response = await payment_callback(client, payment["id"])
    assert callback_response.status_code == 200
    assert callback_response.json()["status"] == "APPROVED"

    final_order = await client.get(f"/api/v1/orders/{order['id']}")
    body = final_order.json()
    assert body["status"] == "PAID"
    assert body["payments"][0]["status"] == "APPROVED"


async def test_get_order_includes_payments(client: AsyncClient) -> None:
    create_response = await create_order(client)
    order_id = create_response.json()["id"]
    await add_item(client, order_id)
    await confirm_order(client, order_id)
    payment_response = await initiate_payment(client, order_id)
    payment_id = payment_response.json()["id"]

    get_response = await client.get(f"/api/v1/orders/{order_id}")
    assert get_response.status_code == 200
    body = get_response.json()
    assert len(body["payments"]) == 1
    assert body["payments"][0]["id"] == payment_id
