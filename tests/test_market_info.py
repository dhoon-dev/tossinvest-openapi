from __future__ import annotations

from pytest_httpx import HTTPXMock

from .conftest import (
    add_api_response,
    add_token_response,
    kr_market_calendar_payload,
    make_client,
    us_market_calendar_payload,
)


def test_get_exchange_rate_parses_response(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url=(
            "https://openapi.tossinvest.com/api/v1/exchange-rate"
            "?baseCurrency=USD&quoteCurrency=KRW&dateTime=2026-03-25T09%3A00%3A00%2B09%3A00"
        ),
        result={
            "baseCurrency": "USD",
            "quoteCurrency": "KRW",
            "rate": "1350.10",
            "midRate": "1350.00",
            "basisPoint": "0.10",
            "rateChangeType": "RISE",
            "validFrom": "2026-03-25T09:00:00+09:00",
            "validUntil": "2026-03-25T09:05:00+09:00",
        },
    )
    client = make_client()

    rate = client.market_info.get_exchange_rate(
        base_currency="USD",
        quote_currency="KRW",
        date_time="2026-03-25T09:00:00+09:00",
    )

    assert rate.base_currency == "USD"
    assert rate.mid_rate == "1350.00"


def test_get_market_calendars_parse_response(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/market-calendar/KR?date=2026-03-25",
        result=kr_market_calendar_payload(),
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/market-calendar/US?date=2026-03-25",
        result=us_market_calendar_payload(),
    )
    client = make_client()

    kr_calendar = client.market_info.get_kr_market_calendar(date="2026-03-25")
    us_calendar = client.market_info.get_us_market_calendar(date="2026-03-25")

    assert kr_calendar.today.integrated is not None
    assert kr_calendar.today.integrated.regular_market is not None
    assert kr_calendar.today.integrated.regular_market.start_time == "09:00"
    assert us_calendar.today.regular_market is not None
    assert us_calendar.today.regular_market.end_time == "16:00"
