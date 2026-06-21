"""Asynchronous TossInvest OpenAPI client."""

from __future__ import annotations

from types import TracebackType
from typing import Self

import httpx

from ._http import AsyncHTTPClient
from .auth import OAuth2TokenProvider
from .config import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    TossInvestConfig,
)
from .resources.accounts import AsyncAccountsResource
from .resources.assets import AsyncAssetsResource
from .resources.market_data import AsyncMarketDataResource
from .resources.market_info import AsyncMarketInfoResource
from .resources.orders import AsyncOrdersResource
from .resources.stocks import AsyncStocksResource


class AsyncTossInvestClient:
    """Asynchronous entry point for Toss Securities Open API.

    The client mirrors ``TossInvestClient`` but uses ``httpx.AsyncClient`` and
    async resource groups. It never reads environment variables, and OAuth
    access tokens are cached in memory only.

    Order, asset, and order-info methods require an account. Provide
    ``account`` here as the default account or pass an account override to an
    account-scoped method.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        account: str | int | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        user_agent: str = DEFAULT_USER_AGENT,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = TossInvestConfig(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            user_agent=user_agent,
            default_account=account,
        )
        self.token_provider = OAuth2TokenProvider(client_id, client_secret)
        self._http = AsyncHTTPClient(self.config, self.token_provider, http_client=http_client)
        self.market_data = AsyncMarketDataResource(self._http)
        self.stocks = AsyncStocksResource(self._http)
        self.market_info = AsyncMarketInfoResource(self._http)
        self.accounts = AsyncAccountsResource(self._http)
        self.assets = AsyncAssetsResource(self._http)
        self.orders = AsyncOrdersResource(self._http)

    @property
    def is_closed(self) -> bool:
        """Return whether this client owns a closed HTTP transport."""
        return self._http.is_closed

    async def get_access_token(self) -> str:
        """Return a valid OAuth access token without printing or persisting it.

        The token is cached in memory until shortly before expiration. Callers
        normally do not need this method because resource requests inject the
        ``Authorization`` header automatically.
        Token issuance uses rate limit group ``AUTH``. On ``429``, respect
        ``Retry-After`` or ``X-RateLimit-Reset`` before retrying auth requests.

        Raises:
            TossInvestAuthError: Token issuance fails.

        """
        return await self._http.get_access_token()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, object | None] | None = None,
        json: object | None = None,
        authenticated: bool = True,
        account_required: bool = False,
        account: str | int | None = None,
    ) -> object | None:
        """Send a lower-level API request through the async SDK HTTP layer.

        Prefer resource methods for stable public APIs. This method is exposed
        for advanced use cases that need an endpoint before an ergonomic wrapper
        exists.
        Rate limit group depends on the target endpoint. On ``429``, respect
        ``Retry-After`` or ``X-RateLimit-Reset`` before retrying that endpoint's
        group.

        Args:
            method: HTTP method to send.
            path: API path relative to ``base_url``.
            params: Optional query parameters. ``None`` values are omitted.
            json: Optional JSON request body or Pydantic model.
            authenticated: Whether to inject an OAuth bearer token.
            account_required: Whether the request must include
                ``X-Tossinvest-Account``.
            account: Per-request account override.

        Raises:
            TossInvestValidationError: ``account_required`` is true and no
                account is available.
            TossInvestAuthError: Authentication fails.
            TossInvestRateLimitError: The API returns a 429 response.
            TossInvestAPIError: The API returns another error response.
            TossInvestHTTPError: HTTP transport fails.

        """
        return await self._http.request(
            method,
            path,
            params=params,
            json=json,
            authenticated=authenticated,
            account_required=account_required,
            account=account,
        )

    async def close(self) -> None:
        """Close the owned async HTTP client if this instance created one."""
        await self._http.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()
