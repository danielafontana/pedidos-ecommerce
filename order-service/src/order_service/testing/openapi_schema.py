from __future__ import annotations

import copy
from typing import Any


def openapi_schema_for_jsonschema(schema: dict[str, Any]) -> dict[str, Any]:
    """Convert OpenAPI 3.0 nullable fields for jsonschema validation."""
    schema = copy.deepcopy(schema)
    if schema.get("nullable") and "type" in schema:
        field_type = schema.pop("type")
        schema.pop("nullable", None)
        if isinstance(field_type, str):
            schema["type"] = [field_type, "null"]
        else:
            schema["type"] = [*field_type, "null"]

    for key, value in list(schema.items()):
        if isinstance(value, dict):
            schema[key] = openapi_schema_for_jsonschema(value)
        elif isinstance(value, list):
            schema[key] = [
                openapi_schema_for_jsonschema(item)
                if isinstance(item, dict)
                else item
                for item in value
            ]

    return schema
