from __future__ import annotations

from pytest_httpx import HTTPXMock

from .conftest import add_api_response, add_token_response, make_client, stock_payload


def test_get_stocks_parses_response(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/stocks?symbols=005930",
        result=[stock_payload()],
    )
    client = make_client()

    stocks = client.stocks.get_stocks("005930")

    assert stocks[0].symbol == "005930"
    assert stocks[0].english_name == "Samsung Electronics"
    assert stocks[0].korean_market_detail is not None
    assert stocks[0].korean_market_detail.nxt_supported


def test_get_stock_warnings_parses_response(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/stocks/005930/warnings",
        result=[
            {
                "warningType": "INVESTMENT_WARNING",
                "startDate": "2026-03-01",
                "endDate": None,
                "exchange": "KRX",
            }
        ],
    )
    client = make_client()

    warnings = client.stocks.get_stock_warnings("005930")

    assert warnings[0].warning_type == "INVESTMENT_WARNING"
    assert warnings[0].exchange == "KRX"
