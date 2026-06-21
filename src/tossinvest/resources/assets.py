"""Asset resource methods."""

from __future__ import annotations

from tossinvest._http import AsyncHTTPClient, SyncHTTPClient
from tossinvest.models import HoldingsOverview, parse_model


class AssetsResource:
    """Synchronous asset endpoints requiring an account header."""

    def __init__(self, http: SyncHTTPClient) -> None:
        self._http = http

    def get_holdings(
        self, *, symbol: str | None = None, account: str | int | None = None
    ) -> HoldingsOverview:
        """Return holdings for the configured or overridden account.

        Requires ``X-Tossinvest-Account``. Pass ``account`` to override the
        client's default account for this call.
        Rate limit group: ``ASSET``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying asset endpoints.

        Args:
            symbol: Optional symbol filter.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET",
            "/api/v1/holdings",
            params={"symbol": symbol},
            account_required=True,
            account=account,
        )
        return parse_model(HoldingsOverview, result)


class AsyncAssetsResource:
    """Asynchronous asset endpoints requiring an account header."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def get_holdings(
        self, *, symbol: str | None = None, account: str | int | None = None
    ) -> HoldingsOverview:
        """Return holdings for the configured or overridden account.

        Requires ``X-Tossinvest-Account``. Pass ``account`` to override the
        client's default account for this call.
        Rate limit group: ``ASSET``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying asset endpoints.

        Args:
            symbol: Optional symbol filter.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET",
            "/api/v1/holdings",
            params={"symbol": symbol},
            account_required=True,
            account=account,
        )
        return parse_model(HoldingsOverview, result)
