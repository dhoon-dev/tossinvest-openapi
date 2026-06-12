"""Market data resource methods."""

from __future__ import annotations

from collections.abc import Sequence

from tossinvest._http import AsyncHTTPClient, SyncHTTPClient
from tossinvest.models import (
    CandlePageResponse,
    OrderbookResponse,
    PriceLimitResponse,
    PriceResponse,
    Trade,
    parse_model,
    parse_model_list,
)

from ._utils import comma_separated, require_non_empty


class MarketDataResource:
    """Synchronous market data endpoints that require OAuth but no account."""

    def __init__(self, http: SyncHTTPClient) -> None:
        self._http = http

    def get_orderbook(self, symbol: str) -> OrderbookResponse:
        """Return the current orderbook for a symbol.

        Args:
            symbol: Stock symbol accepted by the official API.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request("GET", "/api/v1/orderbook", params={"symbol": symbol})
        return parse_model(OrderbookResponse, result)

    def get_prices(self, symbols: str | Sequence[str]) -> list[PriceResponse]:
        """Return current prices for one or more symbols.

        The official API accepts up to 200 comma-separated symbols.

        Args:
            symbols: One symbol, a comma-separated symbol string, or a sequence
                of symbols.

        Raises:
            TossInvestValidationError: An empty symbol sequence is provided.
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET", "/api/v1/prices", params={"symbols": comma_separated(symbols)}
        )
        return parse_model_list(PriceResponse, result)

    def get_price(self, symbol: str) -> PriceResponse:
        """Return the first current price result for one symbol.

        Args:
            symbol: Stock symbol accepted by the official API.

        Raises:
            TossInvestValidationError: ``symbol`` is empty.
            ValueError: The API returns an empty result list.
            TossInvestAPIError: The API returns an error response.

        """
        prices = self.get_prices(require_non_empty("symbol", symbol))
        if not prices:
            msg = "The API returned no price for the requested symbol."
            raise ValueError(msg)
        return prices[0]

    def get_trades(self, symbol: str, *, count: int | None = None) -> list[Trade]:
        """Return recent trades for a symbol.

        Args:
            symbol: Stock symbol accepted by the official API.
            count: Optional number of trades to return.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET", "/api/v1/trades", params={"symbol": symbol, "count": count}
        )
        return parse_model_list(Trade, result)

    def get_price_limit(self, symbol: str) -> PriceLimitResponse:
        """Return the upper and lower price limits for a symbol.

        Args:
            symbol: Stock symbol accepted by the official API.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request("GET", "/api/v1/price-limits", params={"symbol": symbol})
        return parse_model(PriceLimitResponse, result)

    def get_candles(
        self,
        symbol: str,
        *,
        interval: str,
        count: int | None = None,
        before: str | None = None,
        adjusted: bool | None = None,
    ) -> CandlePageResponse:
        """Return candle data for a symbol and interval.

        Args:
            symbol: Stock symbol accepted by the official API.
            interval: Candle interval supported by the API, such as ``"1m"``
                or ``"1d"``.
            count: Optional number of candles to return.
            before: Optional exclusive upper-bound timestamp for pagination.
            adjusted: Whether to request adjusted price data.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET",
            "/api/v1/candles",
            params={
                "symbol": symbol,
                "interval": interval,
                "count": count,
                "before": before,
                "adjusted": adjusted,
            },
        )
        return parse_model(CandlePageResponse, result)


class AsyncMarketDataResource:
    """Asynchronous market data endpoints that require OAuth but no account."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def get_orderbook(self, symbol: str) -> OrderbookResponse:
        """Return the current orderbook for a symbol.

        Args:
            symbol: Stock symbol accepted by the official API.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request("GET", "/api/v1/orderbook", params={"symbol": symbol})
        return parse_model(OrderbookResponse, result)

    async def get_prices(self, symbols: str | Sequence[str]) -> list[PriceResponse]:
        """Return current prices for one or more symbols.

        The official API accepts up to 200 comma-separated symbols.

        Args:
            symbols: One symbol, a comma-separated symbol string, or a sequence
                of symbols.

        Raises:
            TossInvestValidationError: An empty symbol sequence is provided.
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET", "/api/v1/prices", params={"symbols": comma_separated(symbols)}
        )
        return parse_model_list(PriceResponse, result)

    async def get_price(self, symbol: str) -> PriceResponse:
        """Return the first current price result for one symbol.

        Args:
            symbol: Stock symbol accepted by the official API.

        Raises:
            TossInvestValidationError: ``symbol`` is empty.
            ValueError: The API returns an empty result list.
            TossInvestAPIError: The API returns an error response.

        """
        prices = await self.get_prices(require_non_empty("symbol", symbol))
        if not prices:
            msg = "The API returned no price for the requested symbol."
            raise ValueError(msg)
        return prices[0]

    async def get_trades(self, symbol: str, *, count: int | None = None) -> list[Trade]:
        """Return recent trades for a symbol.

        Args:
            symbol: Stock symbol accepted by the official API.
            count: Optional number of trades to return.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET", "/api/v1/trades", params={"symbol": symbol, "count": count}
        )
        return parse_model_list(Trade, result)

    async def get_price_limit(self, symbol: str) -> PriceLimitResponse:
        """Return the upper and lower price limits for a symbol.

        Args:
            symbol: Stock symbol accepted by the official API.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request("GET", "/api/v1/price-limits", params={"symbol": symbol})
        return parse_model(PriceLimitResponse, result)

    async def get_candles(
        self,
        symbol: str,
        *,
        interval: str,
        count: int | None = None,
        before: str | None = None,
        adjusted: bool | None = None,
    ) -> CandlePageResponse:
        """Return candle data for a symbol and interval.

        Args:
            symbol: Stock symbol accepted by the official API.
            interval: Candle interval supported by the API, such as ``"1m"``
                or ``"1d"``.
            count: Optional number of candles to return.
            before: Optional exclusive upper-bound timestamp for pagination.
            adjusted: Whether to request adjusted price data.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET",
            "/api/v1/candles",
            params={
                "symbol": symbol,
                "interval": interval,
                "count": count,
                "before": before,
                "adjusted": adjusted,
            },
        )
        return parse_model(CandlePageResponse, result)
