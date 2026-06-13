"""Configuration for the optional TossInvest MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from tossinvest.client import TossInvestClient
from tossinvest.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
)


@dataclass(frozen=True, slots=True)
class TossInvestMCPServerConfig:
    """Settings used to construct SDK clients for MCP tool calls."""

    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)
    account: str | int | None = None
    base_url: str = DEFAULT_BASE_URL
    timeout: float | httpx.Timeout = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    user_agent: str = DEFAULT_USER_AGENT
    enable_live_orders: bool = False

    def create_client(self) -> TossInvestClient:
        """Create a synchronous SDK client for one MCP tool call."""
        return TossInvestClient(
            self.client_id,
            self.client_secret,
            account=self.account,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            user_agent=self.user_agent,
        )
