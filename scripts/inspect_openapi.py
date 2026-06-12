from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

DEFAULT_INPUT = Path("openapi/openapi.json")
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a cached TossInvest OpenAPI document.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    document = json.loads(args.input.read_text())
    components = document.get("components", {})
    parameters = components.get("parameters", {})
    tags = [tag.get("name") for tag in document.get("tags", []) if isinstance(tag, dict)]
    print("Tags:")
    for tag in tags:
        print(f"- {tag}")
    print()
    print("Operations:")
    for path, path_item in document.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            resolved_params = [
                _resolve_ref(parameter, parameters)
                for parameter in operation.get("parameters", [])
                if isinstance(parameter, dict)
            ]
            query_params = [
                _param_name(parameter)
                for parameter in resolved_params
                if parameter.get("in") == "query"
            ]
            header_params = [
                _param_name(parameter)
                for parameter in resolved_params
                if parameter.get("in") == "header"
            ]
            request_schema = _schema_ref(operation.get("requestBody"))
            response_schema = _schema_ref(
                operation.get("responses", {}).get("200")
                or operation.get("responses", {}).get("201")
                or {}
            )
            auth_required = bool(operation.get("security"))
            account_required = any(
                parameter.get("name") == "X-Tossinvest-Account" for parameter in resolved_params
            )
            print(f"- {operation.get('operationId')} {method.upper()} {path}")
            print(f"  tags: {', '.join(operation.get('tags', []))}")
            print(f"  auth: {auth_required}")
            print(f"  account_header: {account_required}")
            print(f"  query: {', '.join(query_params) or '-'}")
            print(f"  headers: {', '.join(header_params) or '-'}")
            print(f"  request_schema: {request_schema or '-'}")
            print(f"  response_schema: {response_schema or '-'}")


def _resolve_ref(
    parameter: Mapping[str, object], parameters: Mapping[str, object]
) -> Mapping[str, object]:
    ref = parameter.get("$ref")
    if not isinstance(ref, str):
        return parameter
    name = ref.rsplit("/", 1)[-1]
    resolved = parameters.get(name)
    return cast(Mapping[str, object], resolved) if isinstance(resolved, dict) else parameter


def _param_name(parameter: Mapping[str, object]) -> str:
    suffix = "*" if parameter.get("required") is True else ""
    return f"{parameter.get('name')}{suffix}"


def _schema_ref(node: object) -> str | None:
    if not isinstance(node, dict):
        return None
    content = node.get("content")
    if isinstance(content, dict):
        media = content.get("application/json") or content.get("application/x-www-form-urlencoded")
        if isinstance(media, dict):
            return _schema_ref(media.get("schema"))
    ref = node.get("$ref")
    if isinstance(ref, str):
        return ref
    all_of = node.get("allOf")
    if isinstance(all_of, list):
        refs = [_schema_ref(item) for item in all_of]
        return ", ".join(ref for ref in refs if ref)
    one_of = node.get("oneOf")
    if isinstance(one_of, list):
        refs = [_schema_ref(item) for item in one_of]
        return ", ".join(ref for ref in refs if ref)
    properties = node.get("properties")
    result = properties.get("result") if isinstance(properties, dict) else None
    if isinstance(result, dict):
        ref = result.get("$ref")
        if isinstance(ref, str):
            return ref
        items = result.get("items")
        item_ref = items.get("$ref") if isinstance(items, dict) else None
        if isinstance(item_ref, str):
            return f"array[{item_ref}]"
    return None


if __name__ == "__main__":
    main()
