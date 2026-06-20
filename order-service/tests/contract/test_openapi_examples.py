"""Contract tests validating spec examples against OpenAPI schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import jsonschema
import pytest
import yaml
from jsonschema import RefResolver

from order_service.testing.paths import find_repo_root

REPO_ROOT = find_repo_root(Path(__file__))
OPENAPI_PATH = REPO_ROOT / "specs" / "openapi" / "order-service-v1.yaml"
EXAMPLES_DIR = REPO_ROOT / "specs" / "examples"

pytestmark = pytest.mark.contract


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


EXAMPLE_SCHEMA_MAP = {
    "create_order_request.json": "#/components/schemas/CreateOrderRequest",
    "add_item_request.json": "#/components/schemas/AddItemRequest",
    "initiate_payment_request.json": (
        "#/components/schemas/InitiatePaymentRequest"
    ),
    "payment_callback_request.json": (
        "#/components/schemas/PaymentCallbackRequest"
    ),
    "order_draft_response.json": "#/components/schemas/Order",
    "problem_details_409.json": "#/components/schemas/ProblemDetails",
}


@pytest.mark.parametrize(
    "filename,schema_ref", list(EXAMPLE_SCHEMA_MAP.items())
)
def test_example_matches_openapi_schema(
    openapi_spec: dict,
    resolver: RefResolver,
    filename: str,
    schema_ref: str,
) -> None:
    example_path = EXAMPLES_DIR / filename
    payload = json.loads(example_path.read_text(encoding="utf-8"))
    schema = resolver.resolve(schema_ref)[1]
    jsonschema.validate(payload, schema, resolver=resolver)


def test_openapi_spec_has_required_paths(openapi_spec: dict) -> None:
    required_paths = [
        "/orders",
        "/orders/{order_id}",
        "/orders/{order_id}/items",
        "/orders/{order_id}/confirm",
        "/payments",
        "/payments/{payment_id}/callback",
    ]
    for path in required_paths:
        assert path in openapi_spec["paths"], f"Missing path: {path}"
