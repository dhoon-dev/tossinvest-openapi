from __future__ import annotations

from pytest_httpx import HTTPXMock

from .conftest import add_api_response, add_token_response, make_client, price_payload


def test_get_price_parses_successful_response(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/prices?symbols=005930",
        result=[price_payload()],
    )
    client = make_client()

    price = client.market_data.get_price("005930")

    assert price.symbol == "005930"
    assert price.last_price == "72000"
    assert price.model_dump(by_alias=True)["lastPrice"] == "72000"


def test_get_orderbook_parses_response(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/orderbook?symbol=005930",
        result={
            "timestamp": "2026-03-25T09:30:00+09:00",
            "currency": "KRW",
            "asks": [{"price": "72000", "volume": "10"}],
            "bids": [{"price": "71900", "volume": "8"}],
        },
    )
    client = make_client()

    orderbook = client.market_data.get_orderbook("005930")

    assert orderbook.asks[0].price == "72000"
    assert orderbook.bids[0].volume == "8"


def test_get_trades_parses_response(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/trades?symbol=005930&count=2",
        result=[
            {
                "price": "72000",
                "volume": "3",
                "timestamp": "2026-03-25T09:30:01+09:00",
                "currency": "KRW",
            }
        ],
    )
    client = make_client()

    trades = client.market_data.get_trades("005930", count=2)

    assert trades[0].price == "72000"
    assert trades[0].volume == "3"


def test_get_price_limit_parses_response(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/price-limits?symbol=005930",
        result={
            "timestamp": "2026-03-25T09:30:00+09:00",
            "currency": "KRW",
            "lowerLimitPrice": "50000",
            "upperLimitPrice": "90000",
        },
    )
    client = make_client()

    price_limit = client.market_data.get_price_limit("005930")

    assert price_limit.lower_limit_price == "50000"
    assert price_limit.upper_limit_price == "90000"
