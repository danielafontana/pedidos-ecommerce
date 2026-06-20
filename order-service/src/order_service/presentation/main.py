from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from order_service.domain.exceptions.domain_errors import DomainError
from order_service.infrastructure.observability import (
    configure_logging,
    configure_tracing,
    create_metrics_app,
)
from order_service.presentation.api.v1 import orders, payments
from order_service.presentation.auth import create_dev_token, limiter
from order_service.presentation.bootstrap import startup
from order_service.presentation.middleware.http_middleware import (
    CorrelationIdMiddleware,
    SecurityHeadersMiddleware,
)
from order_service.presentation.problem_details import (
    domain_error_handler,
    rate_limit_handler,
    validation_error_handler,
)

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await startup()
    yield


app = FastAPI(
    title="Order Service API",
    version="1.0.0",
    docs_url="/swagger-ui.html",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(orders.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")

app.mount("/metrics", create_metrics_app())

configure_tracing(app)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/dev/token")
async def dev_token():
    """Development helper — returns a JWT for local testing."""
    return {"access_token": create_dev_token(), "token_type": "bearer"}
