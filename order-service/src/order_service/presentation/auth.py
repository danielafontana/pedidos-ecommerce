from slowapi import Limiter
from slowapi.util import get_remote_address

from order_service.infrastructure.security.jwt import (
    create_dev_token,
    require_scopes,
)

limiter = Limiter(key_func=get_remote_address)

require_orders_read = require_scopes("orders:read")
require_orders_write = require_scopes("orders:write")
require_payments_read = require_scopes("payments:read")
require_payments_write = require_scopes("payments:write")

__all__ = [
    "create_dev_token",
    "limiter",
    "require_orders_read",
    "require_orders_write",
    "require_payments_read",
    "require_payments_write",
]
