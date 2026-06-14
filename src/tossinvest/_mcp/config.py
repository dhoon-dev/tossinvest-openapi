"""Configuration for the optional TossInvest MCP server."""

from __future__ import annotations

import time
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
from tossinvest.models import Account

DEFAULT_ACCOUNT_CACHE_TTL = 1.0


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
    account_cache_ttl: float = DEFAULT_ACCOUNT_CACHE_TTL
    enable_live_orders: bool = False
    _account_list: tuple[Account, ...] | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _account_list_cached_at: float | None = field(
        default=None, init=False, repr=False, compare=False
    )

    def create_client(self) -> TossInvestClient:
        """Create a synchronous SDK client for one MCP tool call.

        Account numbers are resolved only when an account-scoped tool needs the
        header. This keeps account discovery and market-data tools from spending
        the ACCOUNT rate-limit bucket just by constructing a client.
        """
        return TossInvestClient(
            self.client_id,
            self.client_secret,
            account=self.account,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            user_agent=self.user_agent,
        )

    def account_seq_for_tool(self, override: str | int | None = None) -> str | int | None:
        """Return the accountSeq for an account-scoped MCP tool call."""
        if override is not None:
            return override
        if self.account_number is None:
            return self.account
        return self._resolve_account_number()

    def cached_account_list(self) -> list[Account] | None:
        """Return cached accounts while the ACCOUNT rate-limit window is active."""
        if self._account_list is None or self._account_list_cache_expired():
            return None
        return list(self._account_list)

    def cache_account_list(self, accounts: list[Account]) -> None:
        """Cache accounts from an already fetched account list."""
        object.__setattr__(self, "_account_list", tuple(accounts))
        object.__setattr__(self, "_account_list_cached_at", time.monotonic())

    def _resolve_account_number(self) -> int:
        account_number = self.account_number
        if account_number is None:
            msg = "Account number is required before resolving accountSeq."
            raise ValueError(msg)
        cached_accounts = self.cached_account_list()
        if cached_accounts is not None:
            return find_account_by_number(cached_accounts, account_number).account_seq
        with TossInvestClient(
            self.client_id,
            self.client_secret,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            user_agent=self.user_agent,
        ) as client:
            accounts = client.accounts.list_accounts()
            self.cache_account_list(accounts)
            account = find_account_by_number(accounts, account_number)
        return account.account_seq

    def _account_list_cache_expired(self) -> bool:
        cached_at = self._account_list_cached_at
        if cached_at is None:
            return True
        return time.monotonic() - cached_at >= self.account_cache_ttl
