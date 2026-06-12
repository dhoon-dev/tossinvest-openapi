"""Shared pagination containers for cursor-based endpoints."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CursorPage[ItemT]:
    """Generic cursor page for future high-level pagination helpers."""

    items: list[ItemT]
    next_cursor: str | None
    has_next: bool
