from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from order_service.domain.exceptions.domain_errors import DomainError


async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    status_map = {
        "order_not_found": 404,
        "item_not_found": 404,
        "payment_not_found": 404,
        "customer_validation_error": 422,
        "catalog_validation_error": 422,
        "invalid_order_state": 409,
        "active_order_exists": 409,
        "concurrency_conflict": 409,
        "idempotency_conflict": 409,
        "payment_gateway_error": 503,
    }
    status_code = status_map.get(exc.code, 400)
    return JSONResponse(
        status_code=status_code,
        content={
            "type": f"https://api.orders.example/problems/{exc.code}",
            "title": exc.code.replace("_", " ").title(),
            "status": status_code,
            "detail": exc.message,
        },
        media_type="application/problem+json",
    )


async def validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "type": "https://api.orders.example/problems/validation-error",
            "title": "Validation Error",
            "status": 422,
            "detail": str(exc.errors()),
        },
        media_type="application/problem+json",
    )


async def rate_limit_handler(
    _: Request, exc: RateLimitExceeded
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "type": "https://api.orders.example/problems/rate-limit-exceeded",
            "title": "Rate Limit Exceeded",
            "status": 429,
            "detail": str(exc.detail),
        },
        media_type="application/problem+json",
    )
