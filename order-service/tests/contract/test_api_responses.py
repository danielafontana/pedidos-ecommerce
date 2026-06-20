"""Contract tests validating live API responses against OpenAPI schemas."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import jsonschema
import pytest
import yaml
from httpx import AsyncClient
from jsonschema import RefResolver

from order_service.testing.openapi_schema import openapi_schema_for_jsonschema
from order_service.testing.paths import find_repo_root

pytestmark = pytest.mark.contract

REPO_ROOT = find_repo_root(Path(__file__))
OPENAPI_PATH = REPO_ROOT / "specs" / "openapi" / "order-service-v1.yaml"


@pytest.fixture(scope="module")
def openapi_spec() -> dict[str, Any]:
    with OPENAPI_PATH.open(encoding="utf-8") as handle:
        return cast(dict[str, Any], yaml.safe_load(handle))


@pytest.fixture(scope="module")
def resolver(openapi_spec: dict) -> RefResolver:
    return RefResolver(
        base_uri=f"file://{OPENAPI_PATH.parent.as_posix()}/",
        referrer=openapi_spec,
    )


def _validate(
    payload: dict, schema_ref: str, openapi_spec: dict, resolver: RefResolver
) -> None:
    schema = openapi_schema_for_jsonschema(resolver.resolve(schema_ref)[1])
    jsonschema.validate(payload, schema, resolver=resolver)


@pytest.mark.asyncio
async def test_create_order_response_matches_order_schema(
    contract_client: AsyncClient,
    openapi_spec: dict,
    resolver: RefResolver,
) -> None:
    response = await contract_client.post(
        "/api/v1/orders", json={"customer_id": "1"}
    )
    assert response.status_code == 201
    _validate(
        response.json(), "#/components/schemas/Order", openapi_spec, resolver
    )


@pytest.mark.asyncio
async def test_confirm_without_items_returns_problem_details(
    contract_client: AsyncClient,
    openapi_spec: dict,
    resolver: RefResolver,
) -> None:
    create = await contract_client.post(
        "/api/v1/orders", json={"customer_id": "1"}
    )
    order_id = create.json()["id"]
    response = await contract_client.post(f"/api/v1/orders/{order_id}/confirm")
    assert response.status_code == 409
    _validate(
        response.json(),
        "#/components/schemas/ProblemDetails",
        openapi_spec,
        resolver,
    )
