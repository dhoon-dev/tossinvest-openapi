from __future__ import annotations

from collections.abc import Sequence
from contextlib import AbstractContextManager
from types import TracebackType
from typing import cast

import pytest

from tossinvest._mcp.config import TossInvestMCPServerConfig
from tossinvest._mcp.server import config_from_args, create_server, parse_args
from tossinvest._mcp.tools import ClientContextFactory, TossInvestMCPTools
from tossinvest.models import (
    Account,
    BuyingPowerResponse,
    OrderCreateRequest,
    OrderModifyRequest,
    OrderOperationResponse,
    OrderResponse,
    PriceResponse,
)


class _Accounts:
    def list_accounts(self) -> list[Account]:
        return [
            Account.model_validate(
                {"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}
            )
        ]


class _MarketData:
    def get_price(self, symbol: str) -> PriceResponse:
        return PriceResponse.model_validate(
            {"symbol": symbol, "lastPrice": "72000", "currency": "KRW"}
        )

    def get_prices(self, symbols: Sequence[str]) -> list[PriceResponse]:
        return [
            PriceResponse.model_validate(
                {"symbol": symbol, "lastPrice": "72000", "currency": "KRW"}
            )
            for symbol in symbols
        ]


class _Orders:
    account: str | int | None = None
    canceled_order_id: str | None = None
    created_request: OrderCreateRequest | None = None
    modified_order_id: str | None = None
    modified_request: OrderModifyRequest | None = None

    def get_buying_power(
        self,
        *,
        currency: str,
        account: str | int | None = None,
    ) -> BuyingPowerResponse:
        self.account = account
        return BuyingPowerResponse.model_validate(
            {"currency": currency, "cashBuyingPower": "100000"}
        )

    def create_order(
        self,
        request: OrderCreateRequest,
        *,
        account: str | int | None = None,
    ) -> OrderResponse:
        self.account = account
        self.created_request = request
        return OrderResponse.model_validate(
            {"orderId": "order-1", "clientOrderId": request.client_order_id}
        )

    def modify_order(
        self,
        order_id: str,
        request: OrderModifyRequest,
        *,
        account: str | int | None = None,
    ) -> OrderOperationResponse:
        self.account = account
        self.modified_order_id = order_id
        self.modified_request = request
        return OrderOperationResponse.model_validate({"orderId": order_id})

    def cancel_order(
        self,
        order_id: str,
        *,
        account: str | int | None = None,
    ) -> OrderOperationResponse:
        self.account = account
        self.canceled_order_id = order_id
        return OrderOperationResponse.model_validate({"orderId": order_id})


class _FakeClient:
    def __init__(self) -> None:
        self.accounts = _Accounts()
        self.market_data = _MarketData()
        self.orders = _Orders()
        self.closed = False


class _FakeClientContext(AbstractContextManager[_FakeClient]):
    def __init__(self, client: _FakeClient) -> None:
        self.client = client

    def __enter__(self) -> _FakeClient:
        return self.client

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.client.closed = True


def test_tools_dump_sdk_models_with_official_aliases() -> None:
    client = _FakeClient()

    tools = TossInvestMCPTools(cast(ClientContextFactory, lambda: _FakeClientContext(client)))

    account_result = tools.list_accounts()
    price_result = tools.get_price("005930")
    prices_result = tools.get_prices(["005930", "000660"])

    assert account_result == [
        {"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}
    ]
    assert price_result == {"symbol": "005930", "lastPrice": "72000", "currency": "KRW"}
    assert prices_result[1]["symbol"] == "000660"
    assert client.closed is True


def test_account_scoped_tools_forward_account_override() -> None:
    client = _FakeClient()
    tools = TossInvestMCPTools(cast(ClientContextFactory, lambda: _FakeClientContext(client)))

    result = tools.get_buying_power(currency="KRW", account_seq="7")

    assert result == {"currency": "KRW", "cashBuyingPower": "100000"}
    assert client.orders.account == "7"


def test_live_order_tools_build_sdk_requests_and_forward_account_override() -> None:
    client = _FakeClient()
    tools = TossInvestMCPTools(cast(ClientContextFactory, lambda: _FakeClientContext(client)))

    created = tools.create_order(
        symbol="005930",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
        price="70000",
        time_in_force="DAY",
        client_order_id="client-order-1",
        confirm_high_value_order=True,
        account_seq="7",
    )
    modified = tools.modify_order(
        "order-1",
        order_type="LIMIT",
        quantity="1",
        price="71000",
        account_seq="7",
    )
    canceled = tools.cancel_order("order-1", account_seq="7")

    assert created == {"orderId": "order-1", "clientOrderId": "client-order-1"}
    assert modified == {"orderId": "order-1"}
    assert canceled == {"orderId": "order-1"}
    assert client.orders.account == "7"
    assert client.orders.created_request is not None
    assert client.orders.created_request.model_dump(by_alias=True, exclude_none=True) == {
        "clientOrderId": "client-order-1",
        "symbol": "005930",
        "side": "BUY",
        "orderType": "LIMIT",
        "timeInForce": "DAY",
        "quantity": "1",
        "price": "70000",
        "confirmHighValueOrder": True,
    }
    assert client.orders.modified_order_id == "order-1"
    assert client.orders.modified_request is not None
    assert client.orders.modified_request.model_dump(by_alias=True, exclude_none=True) == {
        "orderType": "LIMIT",
        "quantity": "1",
        "price": "71000",
    }
    assert client.orders.canceled_order_id == "order-1"


def test_config_from_args_preserves_explicit_credentials() -> None:
    args = parse_args(
        [
            "--client-id",
            "client-id",
            "--client-secret",
            "client-secret",
            "--account",
            "1",
            "--base-url",
            "https://example.test",
            "--timeout",
            "3.5",
            "--max-retries",
            "4",
            "--user-agent",
            "custom-agent",
            "--enable-live-orders",
        ]
    )

    config = config_from_args(args)

    assert config == TossInvestMCPServerConfig(
        client_id="client-id",
        client_secret="client-secret",
        account="1",
        base_url="https://example.test",
        timeout=3.5,
        max_retries=4,
        user_agent="custom-agent",
        enable_live_orders=True,
    )


async def test_create_server_registers_read_only_tools_only() -> None:
    pytest.importorskip("mcp.server.fastmcp")

    server = create_server(TossInvestMCPServerConfig("client-id", "client-secret"))

    tool_names = {tool.name for tool in await server.list_tools()}

    assert "list_accounts" in tool_names
    assert "get_price" in tool_names
    assert "get_buying_power" in tool_names
    assert {"create_order", "modify_order", "cancel_order"}.isdisjoint(tool_names)


async def test_account_scoped_tool_schema_uses_account_seq() -> None:
    pytest.importorskip("mcp.server.fastmcp")

    server = create_server(TossInvestMCPServerConfig("client-id", "client-secret"))

    tools = {tool.name: tool for tool in await server.list_tools()}
    schema = tools["get_buying_power"].inputSchema

    assert "account_seq" in schema["properties"]
    assert "account" not in schema["properties"]
    assert "accountSeq" in schema["properties"]["account_seq"]["description"]
    assert "accountNo" in schema["properties"]["account_seq"]["description"]


async def test_create_server_registers_live_order_tools_when_enabled() -> None:
    pytest.importorskip("mcp.server.fastmcp")

    server = create_server(
        TossInvestMCPServerConfig("client-id", "client-secret", enable_live_orders=True)
    )

    tool_names = {tool.name for tool in await server.list_tools()}

    assert {"create_order", "modify_order", "cancel_order"}.issubset(tool_names)


async def test_live_order_tool_schema_uses_account_seq_when_enabled() -> None:
    pytest.importorskip("mcp.server.fastmcp")

    server = create_server(
        TossInvestMCPServerConfig("client-id", "client-secret", enable_live_orders=True)
    )

    tools = {tool.name: tool for tool in await server.list_tools()}
    schema = tools["create_order"].inputSchema

    assert "account_seq" in schema["properties"]
    assert "account" not in schema["properties"]
    assert "accountSeq" in schema["properties"]["account_seq"]["description"]
    assert "accountNo" in schema["properties"]["account_seq"]["description"]
