"""Integration tests for business rules (plano.md / PLANO-IMPLEMENTACAO.md)."""

import pytest
from httpx import AsyncClient

from .api_helpers import (
    add_item,
    cancel_order,
    confirm_order,
    create_confirmed_order,
    create_order,
    get_order,
    initiate_payment,
    payment_callback,
)

pytestmark = pytest.mark.integration


async def test_cannot_confirm_order_without_items(client: AsyncClient) -> None:
    """plano.md: order must have at least one item before confirmation."""
    create_response = await create_order(client)
    order_id = create_response.json()["id"]

    response = await confirm_order(client, order_id)
    assert response.status_code == 409
    assert response.json()["detail"] == "Order cannot be confirmed"


async def test_price_fixed_at_confirmation_not_at_item_addition(
    client: AsyncClient,
) -> None:
    """plano.md: total uses catalog price at confirmation time."""
    create_response = await create_order(client)
    order_id = create_response.json()["id"]

    draft_with_item = await add_item(client, order_id, quantity=1)
    assert draft_with_item.json()["items"][0]["unit_price"] is None

    confirmed = await confirm_order(client, order_id)
    assert confirmed.status_code == 200
    body = confirmed.json()
    assert body["items"][0]["unit_price"] == "99.90"
    assert body["total_amount"] == "99.90"


async def test_confirmed_order_cannot_add_items(client: AsyncClient) -> None:
    """plano.md: confirmed orders are immutable."""
    confirmed = await create_confirmed_order(client)

    response = await add_item(client, confirmed["id"])
    assert response.status_code == 409
    assert "Cannot add items" in response.json()["detail"]


async def test_payment_only_after_confirmation(client: AsyncClient) -> None:
    """plano.md: payment can only start for confirmed orders."""
    create_response = await create_order(client)
    order_id = create_response.json()["id"]
    await add_item(client, order_id)

    response = await initiate_payment(client, order_id)
    assert response.status_code == 409
    assert "confirmed orders" in response.json()["detail"]


async def test_blocked_customer_cannot_create_order(
    client: AsyncClient,
) -> None:
    """WireMock customers-blocked: inactive customers are rejected."""
    response = await create_order(client, customer_id="2")
    assert response.status_code == 422
    assert "blocked" in response.json()["detail"].lower()


async def test_unavailable_product_cannot_be_added(
    client: AsyncClient,
) -> None:
    """WireMock products-unavailable: catalog validation on add item."""
    create_response = await create_order(client)
    order_id = create_response.json()["id"]

    response = await add_item(client, order_id, product_id="prod-unavailable")
    assert response.status_code == 422
    assert "unavailable" in response.json()["detail"].lower()


async def test_only_one_active_order_per_customer(client: AsyncClient) -> None:
    """plano.md: customer cannot have more than one active order."""
    first = await create_order(client, customer_id="1")
    assert first.status_code == 201

    second = await create_order(client, customer_id="1")
    assert second.status_code == 409
    assert second.json()["type"].endswith("/active_order_exists")


async def test_can_cancel_order_while_payment_pending(
    client: AsyncClient,
) -> None:
    confirmed = await create_confirmed_order(client)
    await initiate_payment(client, confirmed["id"])

    response = await cancel_order(client, confirmed["id"])
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


async def test_cannot_cancel_paid_order(client: AsyncClient) -> None:
    confirmed = await create_confirmed_order(client)
    payment_response = await initiate_payment(client, confirmed["id"])
    payment_id = payment_response.json()["id"]
    await payment_callback(client, payment_id)

    response = await cancel_order(client, confirmed["id"])
    assert response.status_code == 409
    assert "cannot be cancelled" in response.json()["detail"].lower()


async def test_three_payment_rejections_auto_cancel_order(
    client: AsyncClient,
) -> None:
    """plano.md: third payment rejection cancels the order."""
    confirmed = await create_confirmed_order(client)
    order_id = confirmed["id"]

    for attempt in range(3):
        payment_response = await initiate_payment(client, order_id)
        assert payment_response.status_code == 201, payment_response.text
        payment_id = payment_response.json()["id"]

        callback_response = await payment_callback(
            client,
            payment_id,
            status="REJECTED",
            transaction_id=f"txn-reject-{attempt}",
        )
        assert callback_response.status_code == 200

        order_response = await get_order(client, order_id)
        body = order_response.json()
        if attempt < 2:
            assert body["status"] == "PAYMENT_FAILED"
            assert body["payment_attempts"] == attempt + 1
        else:
            assert body["status"] == "CANCELLED"
            assert body["payment_attempts"] == 3
            assert "Auto-cancelled" in body["cancellation_reason"]


async def test_confirm_is_idempotent_with_same_key(
    client: AsyncClient,
) -> None:
    """plano.md: confirmation must be idempotent."""
    create_response = await create_order(client)
    order_id = create_response.json()["id"]
    await add_item(client, order_id)
    key = "confirm-key-001"

    first = await confirm_order(client, order_id, idempotency_key=key)
    second = await confirm_order(client, order_id, idempotency_key=key)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "CONFIRMED"
    assert second.json()["id"] == first.json()["id"]


async def test_initiate_payment_is_idempotent_with_same_key(
    client: AsyncClient,
) -> None:
    confirmed = await create_confirmed_order(client)
    key = "payment-key-001"

    first = await initiate_payment(
        client, confirmed["id"], idempotency_key=key
    )
    second = await initiate_payment(
        client, confirmed["id"], idempotency_key=key
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
