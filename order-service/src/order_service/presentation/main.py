from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from prometheus_client import make_asgi_app
from slowapi import Limiter
from slowapi.util import get_remote_address

from order_service.domain.exceptions.domain_errors import DomainError
from order_service.infrastructure.persistence.database import init_db
from order_service.infrastructure.security.jwt import create_dev_token
from order_service.presentation.api.v1 import orders, payments
from order_service.presentation.middleware.http_middleware import (
    CorrelationIdMiddleware,
    SecurityHeadersMiddleware,
)
from order_service.presentation.problem_details import (
    domain_error_handler,
    validation_error_handler,
)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Order Service API",
    version="1.0.0",
    docs_url="/swagger-ui.html",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.include_router(orders.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")

app.mount("/metrics", make_asgi_app())


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/dev/token")
async def dev_token():
    """Development helper — returns a JWT for local testing."""
    return {"access_token": create_dev_token(), "token_type": "bearer"}
