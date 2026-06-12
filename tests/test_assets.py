from __future__ import annotations

from pytest_httpx import HTTPXMock

from .conftest import add_api_response, add_token_response, make_client


def test_get_holdings_with_account_header(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/holdings?symbol=005930",
        result={
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
            "items": [
                {
                    "symbol": "005930",
                    "name": "Samsung Electronics",
                    "marketCountry": "KR",
                    "currency": "KRW",
                    "quantity": "1",
                    "lastPrice": "72000",
                    "averagePurchasePrice": "70000",
                    "marketValue": {
                        "purchaseAmount": "70000",
                        "amount": "72000",
                        "amountAfterCost": "71900",
                    },
                    "profitLoss": {
                        "amount": "2000",
                        "amountAfterCost": "1900",
                        "rate": "2.85",
                        "rateAfterCost": "2.71",
                    },
                    "dailyProfitLoss": {"amount": "100", "rate": "0.13"},
                    "cost": {"commission": "100", "tax": "0"},
                }
            ],
        },
    )
    client = make_client(account="1")

    holdings = client.assets.get_holdings(symbol="005930")

    assert holdings.items[0].symbol == "005930"
    request = httpx_mock.get_requests(method="GET")[0]
    assert request.headers["x-tossinvest-account"] == "1"
