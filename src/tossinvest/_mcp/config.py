"""Configuration for the optional TossInvest MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from tossinvest._mcp.accounts import find_account_by_number
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
    account_number: str | None = None
    base_url: str = DEFAULT_BASE_URL
    timeout: float | httpx.Timeout = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    user_agent: str = DEFAULT_USER_AGENT
    enable_live_orders: bool = False
    _resolved_account: int | None = field(default=None, init=False, repr=False, compare=False)

    def create_client(self) -> TossInvestClient:
        """Create a synchronous SDK client for one MCP tool call."""
        return TossInvestClient(
            self.client_id,
            self.client_secret,
            account=self._default_account_seq(),
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            user_agent=self.user_agent,
        )

    def _default_account_seq(self) -> str | int | None:
        if self.account_number is None:
            return self.account
        if self._resolved_account is None:
            object.__setattr__(self, "_resolved_account", self._resolve_account_number())
        return self._resolved_account

    def _resolve_account_number(self) -> int:
        account_number = self.account_number
        if account_number is None:
            msg = "Account number is required before resolving accountSeq."
            raise ValueError(msg)
        with TossInvestClient(
            self.client_id,
            self.client_secret,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            user_agent=self.user_agent,
        ) as client:
            account = find_account_by_number(
                client.accounts.list_accounts(),
                account_number,
            )
        return account.account_seq
