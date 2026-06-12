from __future__ import annotations

from typing import Any

import httpx
from pytest_httpx import HTTPXMock

from tossinvest import TossInvestClient

BASE_URL = "https://openapi.tossinvest.com"
TOKEN_URL = f"{BASE_URL}/oauth2/token"


def add_token_response(
    httpx_mock: HTTPXMock, *, token: str = "access-token", expires_in: int = 3600
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=TOKEN_URL,
        json={"access_token": token, "token_type": "Bearer", "expires_in": expires_in},
    )


def add_api_response(httpx_mock: HTTPXMock, *, method: str, url: str, result: Any) -> None:
    httpx_mock.add_response(method=method, url=url, json={"result": result})


def make_client(
    *,
    account: str | int | None = None,
    base_url: str = BASE_URL,
    timeout: float | httpx.Timeout = 10.0,
    max_retries: int = 2,
    user_agent: str = "tossinvest-openapi/0.1.0",
    http_client: httpx.Client | None = None,
) -> TossInvestClient:
    return TossInvestClient(
        "client-id",
        "client-secret",
        account=account,
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        user_agent=user_agent,
        http_client=http_client,
    )


def price_payload(symbol: str = "005930") -> dict[str, object]:
    return {
        "symbol": symbol,
        "timestamp": "2026-03-25T09:30:00.123+09:00",
        "lastPrice": "72000",
        "currency": "KRW",
    }


def stock_payload(symbol: str = "005930") -> dict[str, object]:
    return {
        "symbol": symbol,
        "name": "Samsung Electronics",
        "englishName": "Samsung Electronics",
        "isinCode": "KR7005930003",
        "market": "KOSPI",
        "securityType": "STOCK",
        "isCommonShare": True,
        "status": "ACTIVE",
        "currency": "KRW",
        "sharesOutstanding": "5969782550",
        "listDate": "1975-06-11",
        "delistDate": None,
        "leverageFactor": None,
        "koreanMarketDetail": {
            "liquidationTrading": False,
            "nxtSupported": True,
            "krxTradingSuspended": False,
            "nxtTradingSuspended": False,
        },
    }


def holdings_payload() -> dict[str, object]:
    return {
        "totalPurchaseAmount": {"krw": "1000"},
        "marketValue": {
            "amount": {"krw": "1100"},
            "amountAfterCost": {"krw": "1090"},
        },
        "profitLoss": {
            "amount": {"krw": "100"},
            "amountAfterCost": {"krw": "90"},
            "rate": "10",
            "rateAfterCost": "9",
        },
        "dailyProfitLoss": {"amount": {"krw": "10"}, "rate": "1"},
        "items": [],
    }


def kr_market_calendar_payload() -> dict[str, object]:
    return {
        "today": {
            "date": "2026-03-25",
            "integrated": {
                "regularMarket": {
                    "startTime": "09:00",
                    "endTime": "15:30",
                }
            },
        },
        "previousBusinessDay": {"date": "2026-03-24"},
        "nextBusinessDay": {"date": "2026-03-26"},
    }


def us_market_calendar_payload() -> dict[str, object]:
    return {
        "today": {
            "date": "2026-03-25",
            "regularMarket": {
                "startTime": "09:30",
                "endTime": "16:00",
            },
        },
        "previousBusinessDay": {"date": "2026-03-24"},
        "nextBusinessDay": {"date": "2026-03-26"},
    }


def order_payload() -> dict[str, object]:
    return {
        "orderId": "order-1",
        "symbol": "005930",
        "side": "BUY",
        "orderType": "LIMIT",
        "timeInForce": "DAY",
        "status": "PENDING",
        "price": "70000",
        "quantity": "1",
        "orderAmount": None,
        "currency": "KRW",
        "orderedAt": "2026-03-29T09:30:00+09:00",
        "canceledAt": None,
        "execution": {
            "filledQuantity": "0",
            "averageFilledPrice": None,
            "filledAmount": None,
            "commission": None,
            "tax": None,
            "filledAt": None,
            "settlementDate": None,
        },
    }
