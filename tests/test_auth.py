from __future__ import annotations

from urllib.parse import parse_qs

from pytest_httpx import HTTPXMock

from .conftest import (
    TOKEN_URL,
    add_api_response,
    add_token_response,
    make_client,
    price_payload,
)


def test_token_request_payload_and_endpoint(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    client = make_client()

    token = client.get_access_token()

    request = httpx_mock.get_request(method="POST", url=TOKEN_URL)
    assert request is not None
    payload = parse_qs(request.content.decode())
    assert payload == {
        "grant_type": ["client_credentials"],
        "client_id": ["client-id"],
        "client_secret": ["client-secret"],
    }
    assert request.headers["content-type"] == "application/x-www-form-urlencoded"
    assert token == "access-token"


def test_access_token_is_cached(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock, token="cached-token", expires_in=3600)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/prices?symbols=005930",
        result=[price_payload()],
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/prices?symbols=000660",
        result=[price_payload("000660")],
    )
    client = make_client()

    client.market_data.get_price("005930")
    client.market_data.get_price("000660")

    token_requests = httpx_mock.get_requests(method="POST", url=TOKEN_URL)
    assert len(token_requests) == 1


def test_token_refreshes_after_expiration(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock, token="token-1", expires_in=1)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/prices?symbols=005930",
        result=[price_payload()],
    )
    add_token_response(httpx_mock, token="token-2", expires_in=1)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/prices?symbols=000660",
        result=[price_payload("000660")],
    )
    client = make_client()

    client.market_data.get_price("005930")
    client.market_data.get_price("000660")

    get_requests = httpx_mock.get_requests(method="GET")
    assert get_requests[0].headers["authorization"] == "Bearer token-1"
    assert get_requests[1].headers["authorization"] == "Bearer token-2"
