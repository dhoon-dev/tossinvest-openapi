"""Shared helpers for resource input handling."""

from __future__ import annotations

from collections.abc import Sequence

from tossinvest.errors import TossInvestValidationError


def comma_separated(value: str | Sequence[str]) -> str:
    if isinstance(value, str):
        return value
    if not value:
        raise TossInvestValidationError("At least one symbol is required.")
    return ",".join(value)


def require_non_empty(name: str, value: str) -> str:
    if not value:
        raise TossInvestValidationError(f"{name} must not be empty.")
    return value
