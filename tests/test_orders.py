from __future__ import annotations

import os

import pytest
from pytest_httpx import HTTPXMock

from tossinvest import OrderCreateRequest, OrderModifyRequest, TossInvestValidationError

from .conftest import add_api_response, add_token_response, make_client, order_payload


def test_create_order_serializes_json_body(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="POST",
        url="https://openapi.tossinvest.com/api/v1/orders",
        result={"orderId": "order-1", "clientOrderId": "client-order-1"},
    )
    client = make_client(account="1")
    request = OrderCreateRequest(
        clientOrderId="client-order-1",
        symbol="005930",
        side="BUY",
        orderType="LIMIT",
        quantity="1",
        price="70000",
    )

    response = client.orders.create_order(request)

    sent = httpx_mock.get_requests(method="POST")[-1]
    assert sent.headers["x-tossinvest-account"] == "1"
    assert sent.read().decode() == (
        '{"clientOrderId":"client-order-1","symbol":"005930","side":"BUY",'
        '"orderType":"LIMIT","quantity":"1","price":"70000"}'
    )
    assert response.order_id == "order-1"


def test_order_request_validates_quantity_or_amount() -> None:
    with pytest.raises(ValueError, match="Exactly one"):
        OrderCreateRequest(symbol="005930", side="BUY", orderType="MARKET")


def test_order_api_requires_account_before_live_request(httpx_mock: HTTPXMock) -> None:
    client = make_client()
    request = OrderCreateRequest(
        symbol="005930",
        side="BUY",
        orderType="LIMIT",
        quantity="1",
        price="70000",
    )

    with pytest.raises(TossInvestValidationError, match="requires an account"):
        client.orders.create_order(request)

    assert httpx_mock.get_requests() == []


def test_list_orders_parses_page(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/orders?status=OPEN&limit=20",
        result={"orders": [order_payload()], "nextCursor": None, "hasNext": False},
    )
    client = make_client(account="1")

    page = client.orders.list_orders(status="OPEN", limit=20)

    assert page.orders[0].order_id == "order-1"
    assert not page.has_next


def test_modify_cancel_and_order_info_methods(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="POST",
        url="https://openapi.tossinvest.com/api/v1/orders/order-1/modify",
        result={"orderId": "order-1"},
    )
    add_api_response(
        httpx_mock,
        method="POST",
        url="https://openapi.tossinvest.com/api/v1/orders/order-1/cancel",
        result={"orderId": "order-1"},
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/buying-power?currency=KRW",
        result={"currency": "KRW", "cashBuyingPower": "100000"},
    )
    client = make_client(account="1")

    modified = client.orders.modify_order(
        "order-1", OrderModifyRequest(orderType="LIMIT", price="71000")
    )
    canceled = client.orders.cancel_order("order-1")
    buying_power = client.orders.get_buying_power(currency="KRW")

    assert modified.order_id == "order-1"
    assert canceled.order_id == "order-1"
    assert buying_power.cash_buying_power == "100000"


def test_get_order_parses_response(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/orders/order-1",
        result=order_payload(),
    )
    client = make_client(account="1")

    order = client.orders.get_order("order-1")

    assert order.order_id == "order-1"
    assert order.execution.filled_quantity == "0"


def test_get_sellable_quantity_parses_response(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/sellable-quantity?symbol=005930",
        result={"sellableQuantity": "10"},
    )
    client = make_client(account="1")

    quantity = client.orders.get_sellable_quantity(symbol="005930")

    assert quantity.sellable_quantity == "10"


def test_get_commissions_parses_response(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/commissions",
        result=[
            {
                "marketCountry": "KR",
                "commissionRate": "0.015",
                "startDate": "2026-01-01",
                "endDate": None,
            }
        ],
    )
    client = make_client(account="1")

    commissions = client.orders.get_commissions()

    assert commissions[0].market_country == "KR"
    assert commissions[0].commission_rate == "0.015"


def test_live_order_tests_are_disabled_by_default() -> None:
    assert os.getenv("TOSSINVEST_ENABLE_LIVE_ORDER") != "true"
