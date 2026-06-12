"""Configuration defaults and immutable client configuration."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from ._version import __version__

DEFAULT_BASE_URL = "https://openapi.tossinvest.com"
DEFAULT_TIMEOUT = 10.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_USER_AGENT = f"tossinvest-openapi/{__version__}"


@dataclass(frozen=True, slots=True)
class TossInvestConfig:
    """Resolved settings shared by sync and async TossInvest clients.

    The configuration is immutable after client construction. Secrets are kept
    only in memory and are not printed by SDK exceptions.
    """

    client_id: str
    client_secret: str
    base_url: str = DEFAULT_BASE_URL
    timeout: float | httpx.Timeout = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    user_agent: str = DEFAULT_USER_AGENT
    default_account: str | int | None = None

    def account_header_value(self, override: str | int | None = None) -> str | None:
        """Return the account header value for an override or the configured default."""
        account = self.default_account if override is None else override
        if account is None:
            return None
        return str(account)
