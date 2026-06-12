from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from tossinvest import TossInvestAPIError, TossInvestAuthError, TossInvestRateLimitError

from .conftest import add_api_response, add_token_response, make_client, price_payload


def test_error_response_parsing_and_secret_redaction(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/prices?symbols=005930",
        status_code=400,
        json={
            "error": {
                "requestId": "request-1",
                "code": "invalid-request",
                "message": "Upstream message",
                "data": {"field": "symbols"},
            }
        },
        headers={"X-Request-Id": "request-1", "cf-ray": "trace-1"},
    )
    client = make_client()

    with pytest.raises(TossInvestAPIError) as exc_info:
        client.market_data.get_price("005930")

    exc = exc_info.value
    assert exc.status_code == 400
    assert exc.api_code == "invalid-request"
    assert exc.request_id == "request-1"
    assert exc.trace_id == "trace-1"
    assert "client-secret" not in str(exc)


def test_401_refreshes_token_once(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock, token="token-1")
    httpx_mock.add_response(
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/prices?symbols=005930",
        status_code=401,
        json={"error": {"requestId": "r1", "code": "expired-token", "message": "Expired"}},
    )
    add_token_response(httpx_mock, token="token-2")
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/prices?symbols=005930",
        result=[price_payload()],
    )
    client = make_client()

    price = client.market_data.get_price("005930")

    assert price.symbol == "005930"
    get_requests = httpx_mock.get_requests(method="GET")
    assert get_requests[0].headers["authorization"] == "Bearer token-1"
    assert get_requests[1].headers["authorization"] == "Bearer token-2"


def test_rate_limit_exception_mapping(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/prices?symbols=005930",
        status_code=429,
        json={
            "error": {
                "requestId": "request-2",
                "code": "rate-limit-exceeded",
                "message": "Rate limited",
            }
        },
        headers={"Retry-After": "1", "X-RateLimit-Remaining": "0"},
    )
    client = make_client(max_retries=0)

    with pytest.raises(TossInvestRateLimitError) as exc_info:
        client.market_data.get_price("005930")

    assert exc_info.value.retry_after == "1"
    assert exc_info.value.api_code == "rate-limit-exceeded"


def test_token_failure_raises_auth_error_without_secret(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://openapi.tossinvest.com/oauth2/token",
        status_code=401,
        json={"error": "invalid_client"},
    )
    client = make_client()

    with pytest.raises(TossInvestAuthError) as exc_info:
        client.get_access_token()

    assert "client-secret" not in str(exc_info.value)
