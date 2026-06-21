"""Stock information resource methods."""

from __future__ import annotations

from collections.abc import Sequence

from tossinvest._http import AsyncHTTPClient, SyncHTTPClient
from tossinvest.models import StockInfo, StockWarning, parse_model_list

from ._utils import comma_separated, require_non_empty


class StocksResource:
    """Synchronous stock information endpoints."""

    def __init__(self, http: SyncHTTPClient) -> None:
        self._http = http

    def get_stocks(self, symbols: str | Sequence[str]) -> list[StockInfo]:
        """Return stock master records for one or more symbols.

        Rate limit group: ``STOCK``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying stock info endpoints.

        Args:
            symbols: One symbol, a comma-separated symbol string, or a sequence
                of symbols.

        Raises:
            TossInvestValidationError: An empty symbol sequence is provided.
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET", "/api/v1/stocks", params={"symbols": comma_separated(symbols)}
        )
        return parse_model_list(StockInfo, result)

    def get_stock(self, symbol: str) -> StockInfo:
        """Return the first stock master record for one symbol.

        Rate limit group: ``STOCK``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying stock info endpoints.

        Args:
            symbol: Stock symbol accepted by the official API.

        Raises:
            TossInvestValidationError: ``symbol`` is empty.
            ValueError: The API returns an empty result list.
            TossInvestAPIError: The API returns an error response.

        """
        stocks = self.get_stocks(require_non_empty("symbol", symbol))
        if not stocks:
            msg = "The API returned no stock for the requested symbol."
            raise ValueError(msg)
        return stocks[0]

    def get_stock_warnings(self, symbol: str) -> list[StockWarning]:
        """Return trading warnings for a symbol.

        Rate limit group: ``STOCK``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying stock info endpoints.

        Args:
            symbol: Stock symbol accepted by the official API.

        Raises:
            TossInvestValidationError: ``symbol`` is empty.
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET", f"/api/v1/stocks/{require_non_empty('symbol', symbol)}/warnings"
        )
        return parse_model_list(StockWarning, result)


class AsyncStocksResource:
    """Asynchronous stock information endpoints."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def get_stocks(self, symbols: str | Sequence[str]) -> list[StockInfo]:
        """Return stock master records for one or more symbols.

        Rate limit group: ``STOCK``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying stock info endpoints.

        Args:
            symbols: One symbol, a comma-separated symbol string, or a sequence
                of symbols.

        Raises:
            TossInvestValidationError: An empty symbol sequence is provided.
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET", "/api/v1/stocks", params={"symbols": comma_separated(symbols)}
        )
        return parse_model_list(StockInfo, result)

    async def get_stock(self, symbol: str) -> StockInfo:
        """Return the first stock master record for one symbol.

        Rate limit group: ``STOCK``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying stock info endpoints.

        Args:
            symbol: Stock symbol accepted by the official API.

        Raises:
            TossInvestValidationError: ``symbol`` is empty.
            ValueError: The API returns an empty result list.
            TossInvestAPIError: The API returns an error response.

        """
        stocks = await self.get_stocks(require_non_empty("symbol", symbol))
        if not stocks:
            msg = "The API returned no stock for the requested symbol."
            raise ValueError(msg)
        return stocks[0]

    async def get_stock_warnings(self, symbol: str) -> list[StockWarning]:
        """Return trading warnings for a symbol.

        Rate limit group: ``STOCK``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying stock info endpoints.

        Args:
            symbol: Stock symbol accepted by the official API.

        Raises:
            TossInvestValidationError: ``symbol`` is empty.
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET", f"/api/v1/stocks/{require_non_empty('symbol', symbol)}/warnings"
        )
        return parse_model_list(StockWarning, result)
