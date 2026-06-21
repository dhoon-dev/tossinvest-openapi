from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from tossinvest import (
    SUPPORTED_OPENAPI_VERSION,
    AsyncTossInvestClient,
    TossInvestAPIError,
    TossInvestClient,
    TossInvestValidationError,
)

from .conftest import add_api_response, add_token_response, make_client, price_payload


def test_authorization_and_user_agent_headers(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock, token="header-token")
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/prices?symbols=005930",
        result=[price_payload()],
    )
    client = make_client(user_agent="test-agent/1.0")

    client.market_data.get_price("005930")

    request = httpx_mock.get_requests(method="GET")[0]
    assert request.headers["authorization"] == "Bearer header-token"
    assert request.headers["user-agent"] == "test-agent/1.0"


def test_account_header_injection(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/holdings",
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
            "items": [],
        },
    )
    client = make_client(account="1")

    client.assets.get_holdings()

    request = httpx_mock.get_requests(method="GET")[0]
    assert request.headers["x-tossinvest-account"] == "1"


def test_missing_account_fails_before_request(httpx_mock: HTTPXMock) -> None:
    client = make_client()

    with pytest.raises(TossInvestValidationError, match="requires an account"):
        client.assets.get_holdings()

    assert httpx_mock.get_requests() == []


def test_base_url_joining_and_timeout_configuration(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://example.test/root/oauth2/token",
        json={"access_token": "token", "token_type": "Bearer", "expires_in": 3600},
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://example.test/root/api/v1/prices?symbols=005930",
        result=[price_payload()],
    )
    client = TossInvestClient(
        "client-id",
        "client-secret",
        base_url="https://example.test/root/",
        timeout=5.0,
    )

    client.market_data.get_price("005930")

    assert client.config.timeout == 5.0


def test_query_parameter_serialization(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url=(
            "https://openapi.tossinvest.com/api/v1/candles"
            "?symbol=005930&interval=1d&count=2&before=2026-03-25T09%3A00%3A00%2B09%3A00"
            "&adjusted=false"
        ),
        result={"candles": [], "nextBefore": None},
    )
    client = make_client()

    page = client.market_data.get_candles(
        "005930",
        interval="1d",
        count=2,
        before="2026-03-25T09:00:00+09:00",
        adjusted=False,
    )

    assert page.candles == []


def test_sync_context_manager_closes_owned_client() -> None:
    with make_client() as client:
        assert not client.is_closed
    assert client.is_closed


def test_sync_openapi_version_methods_do_not_require_auth(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://openapi.tossinvest.com/openapi-docs/latest/openapi.json",
        json={"openapi": "3.1.0", "info": {"title": "TossInvest OpenAPI", "version": "9.9.9"}},
    )
    client = make_client()

    supported = client.get_supported_openapi_version()
    latest = client.get_latest_openapi_version()

    request = httpx_mock.get_request(method="GET")
    assert supported == SUPPORTED_OPENAPI_VERSION == "1.1.1"
    assert latest == "9.9.9"
    assert request is not None
    assert "authorization" not in request.headers


def test_latest_openapi_version_requires_info_version(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://openapi.tossinvest.com/openapi-docs/latest/openapi.json",
        json={"openapi": "3.1.0", "info": {}},
    )
    client = make_client()

    with pytest.raises(TossInvestAPIError, match=r"info\.version"):
        client.get_latest_openapi_version()


async def test_async_context_manager_closes_owned_client() -> None:
    async with AsyncTossInvestClient("client-id", "client-secret") as client:
        assert not client.is_closed
    assert client.is_closed
