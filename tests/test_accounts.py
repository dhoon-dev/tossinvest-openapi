from __future__ import annotations

from pytest_httpx import HTTPXMock

from .conftest import add_api_response, add_token_response, make_client


def test_list_accounts(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/accounts",
        result=[{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}],
    )
    client = make_client()

    accounts = client.accounts.list_accounts()

    assert accounts[0].account_seq == 1
    assert accounts[0].account_type == "BROKERAGE"
