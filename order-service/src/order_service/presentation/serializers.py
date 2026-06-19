from order_service.domain.datetime_utils import format_datetime
from order_service.domain.entities.order import Order, Payment


def order_to_dict(order: Order, payments: list[Payment] | None = None) -> dict:
    return {
        "id": str(order.id),
        "customer_id": order.customer_id,
        "status": order.status.value,
        "items": [
            {
                "id": str(item.id),
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price.amount) if item.unit_price else None,
            }
            for item in order.items
        ],
        "total_amount": str(order.total_amount.amount),
        "currency": order.total_amount.currency,
        "payment_attempts": order.payment_attempts,
        "payments": [payment_to_dict(payment) for payment in (payments or [])],
        "version": order.version,
        "cancellation_reason": order.cancellation_reason,
        "created_at": format_datetime(order.created_at),
        "updated_at": format_datetime(order.updated_at),
    }


def payment_to_dict(payment: Payment) -> dict:
    return {
        "id": str(payment.id),
        "order_id": str(payment.order_id),
        "amount": str(payment.amount.amount),
        "currency": payment.amount.currency,
        "status": payment.status.value,
        "external_reference": payment.external_reference,
        "created_at": format_datetime(payment.created_at),
        "updated_at": format_datetime(payment.updated_at),
    }
