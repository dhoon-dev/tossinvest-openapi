"""Synchronous TossInvest OpenAPI client."""

from __future__ import annotations

from types import TracebackType
from typing import Self

import httpx

from ._http import SyncHTTPClient
from .auth import OAuth2TokenProvider
from .config import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    TossInvestConfig,
)
from .openapi import OPENAPI_DOCUMENT_PATH, SUPPORTED_OPENAPI_VERSION, _parse_openapi_version
from .resources.accounts import AccountsResource
from .resources.assets import AssetsResource
from .resources.market_data import MarketDataResource
from .resources.market_info import MarketInfoResource
from .resources.orders import OrdersResource
from .resources.stocks import StocksResource


class TossInvestClient:
    """Synchronous entry point for Toss Securities Open API.

    The client owns resource groups such as ``market_data``, ``accounts``,
    ``assets``, and ``orders``. It never reads environment variables and keeps
    OAuth access tokens in memory only.

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
        http_client: httpx.Client | None = None,
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
        self._http = SyncHTTPClient(self.config, self.token_provider, http_client=http_client)
        self.market_data = MarketDataResource(self._http)
        self.stocks = StocksResource(self._http)
        self.market_info = MarketInfoResource(self._http)
        self.accounts = AccountsResource(self._http)
        self.assets = AssetsResource(self._http)
        self.orders = OrdersResource(self._http)

    @property
    def is_closed(self) -> bool:
        """Return whether this client owns a closed HTTP transport."""
        return self._http.is_closed

    def get_supported_openapi_version(self) -> str:
        """Return the official OpenAPI version modeled by this SDK release."""
        return SUPPORTED_OPENAPI_VERSION

    def get_latest_openapi_version(self) -> str:
        """Fetch and return the latest official TossInvest OpenAPI version.

        This calls ``/openapi-docs/latest/openapi.json`` without OAuth and
        returns the document's ``info.version`` value.

        Raises:
            TossInvestAPIError: The OpenAPI document is missing ``info.version``
                or the API returns an error response.
            TossInvestHTTPError: HTTP transport fails.

        """
        document = self._http.request(
            "GET",
            OPENAPI_DOCUMENT_PATH,
            authenticated=False,
        )
        return _parse_openapi_version(document)

    def get_access_token(self) -> str:
        """Return a valid OAuth access token without printing or persisting it.

        The token is cached in memory until shortly before expiration. Callers
        normally do not need this method because resource requests inject the
        ``Authorization`` header automatically.
        Token issuance uses rate limit group ``AUTH``. On ``429``, respect
        ``Retry-After`` or ``X-RateLimit-Reset`` before retrying auth requests.

        Raises:
            TossInvestAuthError: Token issuance fails.

        """
        return self._http.get_access_token()

    def request(
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
        """Send a lower-level API request through the SDK HTTP layer.

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
        return self._http.request(
            method,
            path,
            params=params,
            json=json,
            authenticated=authenticated,
            account_required=account_required,
            account=account,
        )

    def close(self) -> None:
        """Close the owned HTTP client if this instance created one."""
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
