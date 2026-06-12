"""Market information resource methods."""

from __future__ import annotations

from tossinvest._http import AsyncHTTPClient, SyncHTTPClient
from tossinvest.models import (
    ExchangeRateResponse,
    KrMarketCalendarResponse,
    UsMarketCalendarResponse,
    parse_model,
)


class MarketInfoResource:
    """Synchronous market info endpoints that require OAuth but no account."""

    def __init__(self, http: SyncHTTPClient) -> None:
        self._http = http

    def get_exchange_rate(
        self,
        *,
        base_currency: str,
        quote_currency: str,
        date_time: str | None = None,
    ) -> ExchangeRateResponse:
        """Return an exchange rate between two supported currencies.

        Args:
            base_currency: Base currency code supported by the API.
            quote_currency: Quote currency code supported by the API.
            date_time: Optional timestamp for a historical or point-in-time
                lookup when supported by the API.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET",
            "/api/v1/exchange-rate",
            params={
                "baseCurrency": base_currency,
                "quoteCurrency": quote_currency,
                "dateTime": date_time,
            },
        )
        return parse_model(ExchangeRateResponse, result)

    def get_kr_market_calendar(self, *, date: str | None = None) -> KrMarketCalendarResponse:
        """Return Korean market calendar information.

        Args:
            date: Optional date to center the calendar response.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request("GET", "/api/v1/market-calendar/KR", params={"date": date})
        return parse_model(KrMarketCalendarResponse, result)

    def get_us_market_calendar(self, *, date: str | None = None) -> UsMarketCalendarResponse:
        """Return US market calendar information.

        Args:
            date: Optional date to center the calendar response.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request("GET", "/api/v1/market-calendar/US", params={"date": date})
        return parse_model(UsMarketCalendarResponse, result)


class AsyncMarketInfoResource:
    """Asynchronous market info endpoints that require OAuth but no account."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def get_exchange_rate(
        self,
        *,
        base_currency: str,
        quote_currency: str,
        date_time: str | None = None,
    ) -> ExchangeRateResponse:
        """Return an exchange rate between two supported currencies.

        Args:
            base_currency: Base currency code supported by the API.
            quote_currency: Quote currency code supported by the API.
            date_time: Optional timestamp for a historical or point-in-time
                lookup when supported by the API.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET",
            "/api/v1/exchange-rate",
            params={
                "baseCurrency": base_currency,
                "quoteCurrency": quote_currency,
                "dateTime": date_time,
            },
        )
        return parse_model(ExchangeRateResponse, result)

    async def get_kr_market_calendar(self, *, date: str | None = None) -> KrMarketCalendarResponse:
        """Return Korean market calendar information.

        Args:
            date: Optional date to center the calendar response.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET", "/api/v1/market-calendar/KR", params={"date": date}
        )
        return parse_model(KrMarketCalendarResponse, result)

    async def get_us_market_calendar(self, *, date: str | None = None) -> UsMarketCalendarResponse:
        """Return US market calendar information.

        Args:
            date: Optional date to center the calendar response.

        Raises:
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET", "/api/v1/market-calendar/US", params={"date": date}
        )
        return parse_model(UsMarketCalendarResponse, result)
