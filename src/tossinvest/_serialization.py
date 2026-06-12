from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from enum import Enum
from typing import cast

from pydantic import BaseModel


def join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def serialize_query(params: Mapping[str, object | None] | None) -> dict[str, str]:
    if not params:
        return {}
    return {key: _serialize_value(value) for key, value in params.items() if value is not None}


def json_body(data: object | None) -> object | None:
    if data is None:
        return None
    if isinstance(data, BaseModel):
        return cast(object, data.model_dump(by_alias=True, exclude_none=True))
    return data


def _serialize_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, str):
        return value
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return ",".join(_serialize_value(item) for item in value)
    return str(value)
