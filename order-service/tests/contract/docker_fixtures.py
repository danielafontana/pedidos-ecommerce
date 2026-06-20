"""Docker-backed fixtures for contract API tests."""

from __future__ import annotations

import importlib
import os
import sys
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.postgres import PostgresContainer

REPO_ROOT = Path(__file__).resolve().parents[2]
WIREMOCK_MAPPINGS = REPO_ROOT / "wiremock" / "mappings"


def _reload_infrastructure_modules() -> None:
    module_names = [
        "order_service.infrastructure.config",
        "order_service.infrastructure.persistence.database",
        "order_service.infrastructure.http.gateways",
        "order_service.infrastructure.messaging.sqs_publisher",
        "order_service.presentation.dependencies",
        "order_service.presentation.main",
    ]
    for name in module_names:
        if name in sys.modules:
            importlib.reload(sys.modules[name])
        else:
            importlib.import_module(name)


@pytest.fixture(scope="session")
def docker_available() -> None:
    try:
        import docker

        docker.from_env().ping()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Docker is required for contract API tests: {exc}")


@pytest.fixture(scope="session")
def integration_env(docker_available: None) -> Iterator[dict[str, str]]:
    postgres = PostgresContainer("postgres:16-alpine", driver="asyncpg")
    postgres.start()

    wiremock = DockerContainer("wiremock/wiremock:3.9.1")
    wiremock.with_volume_mapping(
        str(WIREMOCK_MAPPINGS), "/home/wiremock/mappings"
    )
    wiremock.with_exposed_ports(8080)
    wiremock.start()
    wait_for_logs(wiremock, "port:", timeout=60)

    host = wiremock.get_container_host_ip()
    port = wiremock.get_exposed_port(8080)
    base = f"http://{host}:{port}"

    env = {
        "DATABASE_URL": postgres.get_connection_url(),
        "CUSTOMER_SERVICE_URL": f"{base}/customers",
        "CATALOG_SERVICE_URL": f"{base}/products",
        "PAYMENT_GATEWAY_URL": f"{base}/payments",
        "NOTIFICATION_SERVICE_URL": f"{base}/notifications",
        "AWS_ENDPOINT_URL": "http://localhost:4566",
        "APP_ENV": "local",
    }
    os.environ.update(env)
    _reload_infrastructure_modules()

    yield env

    wiremock.stop()
    postgres.stop()


@pytest.fixture(scope="session", autouse=True)
def stub_event_publisher(integration_env: dict[str, str]) -> Iterator[None]:
    import order_service.infrastructure.messaging.sqs_publisher as sqs_mod

    class NoOpEventPublisher:
        async def publish(self, event_type: str, payload: dict) -> None:
            return None

    with patch.object(sqs_mod, "SqsEventPublisher", NoOpEventPublisher):
        yield


@pytest.fixture(autouse=True)
async def reset_database(
    integration_env: dict[str, str],
) -> AsyncIterator[None]:
    from order_service.infrastructure.persistence.database import engine
    from order_service.infrastructure.persistence.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def contract_client(
    integration_env: dict[str, str],
) -> AsyncIterator[AsyncClient]:
    from order_service.presentation.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as http_client:
        yield http_client
