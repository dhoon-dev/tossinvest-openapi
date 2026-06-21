"""Official TossInvest OpenAPI version metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from .errors import TossInvestAPIError

SUPPORTED_OPENAPI_VERSION: Final = "1.1.1"
OPENAPI_DOCUMENT_PATH: Final = "/openapi-docs/latest/openapi.json"

__all__ = ["OPENAPI_DOCUMENT_PATH", "SUPPORTED_OPENAPI_VERSION"]


def _parse_openapi_version(document: object, *, endpoint: str = OPENAPI_DOCUMENT_PATH) -> str:
    """Return the ``info.version`` value from an OpenAPI document."""
    if isinstance(document, Mapping):
        info = document.get("info")
        if isinstance(info, Mapping):
            version = info.get("version")
            if isinstance(version, str) and version:
                return version
    raise TossInvestAPIError(
        "TossInvest OpenAPI document did not include info.version.",
        response_body=document,
        endpoint=endpoint,
    )
