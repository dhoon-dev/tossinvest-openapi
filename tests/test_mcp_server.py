from __future__ import annotations

import shlex
import sys
from collections.abc import Sequence
from contextlib import AbstractContextManager
from types import TracebackType
from typing import cast

import pytest
from pytest_httpx import HTTPXMock

from tossinvest._mcp.config import TossInvestMCPServerConfig
from tossinvest._mcp.credentials import CredentialHelperError
from tossinvest._mcp.server import config_from_args, create_server, parse_args
from tossinvest._mcp.tools import ClientContextFactory, TossInvestMCPTools
from tossinvest.models import (
    Account,
    BuyingPowerResponse,
    OrderCreateRequest,
    OrderModifyRequest,
    OrderOperationResponse,
    OrderResponse,
    PaginatedOrderResponse,
    PriceResponse,
)

from .conftest import add_api_response, add_token_response


def _python_command(source: str) -> str:
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(source)}"


def _property_enum(schema: dict[str, object], property_name: str) -> list[str]:
    prop_schema = cast(
        dict[str, object], cast(dict[str, object], schema["properties"])[property_name]
    )
    enum = _schema_enum(schema, prop_schema)
    if enum is None:
        msg = f"{property_name} does not expose an enum."
        raise AssertionError(msg)
    return enum


def _schema_enum(schema: dict[str, object], prop_schema: dict[str, object]) -> list[str] | None:
    enum = prop_schema.get("enum")
    if isinstance(enum, list):
        return cast(list[str], enum)
    ref = prop_schema.get("$ref")
    if isinstance(ref, str):
        defs = cast(dict[str, object], schema["$defs"])
        return _schema_enum(schema, cast(dict[str, object], defs[ref.removeprefix("#/$defs/")]))
    for key in ("anyOf", "oneOf"):
        options = prop_schema.get(key)
        if isinstance(options, list):
            for option in options:
                if isinstance(option, dict):
                    nested_enum = _schema_enum(schema, cast(dict[str, object], option))
                    if nested_enum is not None:
                        return nested_enum
    return None


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
    listed_status: str | None = None
    modified_order_id: str | None = None
    modified_request: OrderModifyRequest | None = None

    def list_orders(
        self,
        *,
        status: str = "OPEN",
        symbol: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        account: str | int | None = None,
    ) -> PaginatedOrderResponse:
        del symbol, from_date, to_date, cursor, limit
        self.account = account
        self.listed_status = status
        return PaginatedOrderResponse.model_validate(
            {"orders": [], "nextCursor": None, "hasNext": False}
        )

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
    matched_account = tools.find_account_by_number("12345678901")
    price_result = tools.get_price("005930")
    prices_result = tools.get_prices(["005930", "000660"])

    assert account_result == [
        {"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}
    ]
    assert matched_account == {
        "accountNo": "12345678901",
        "accountSeq": 1,
        "accountType": "BROKERAGE",
    }
    assert price_result == {"symbol": "005930", "lastPrice": "72000", "currency": "KRW"}
    assert prices_result[1]["symbol"] == "000660"
    assert client.closed is True


def test_account_scoped_tools_forward_account_override() -> None:
    client = _FakeClient()
    tools = TossInvestMCPTools(cast(ClientContextFactory, lambda: _FakeClientContext(client)))

    result = tools.get_buying_power(currency="KRW", account_seq="7")

    assert result == {"currency": "KRW", "cashBuyingPower": "100000"}
    assert client.orders.account == "7"


def test_list_orders_tool_defaults_to_open_status() -> None:
    client = _FakeClient()
    tools = TossInvestMCPTools(cast(ClientContextFactory, lambda: _FakeClientContext(client)))

    result = tools.list_orders(account_seq="7")

    assert result == {"orders": [], "hasNext": False}
    assert client.orders.listed_status == "OPEN"
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
            "12345678901",
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
        account_number="12345678901",
        base_url="https://example.test",
        timeout=3.5,
        max_retries=4,
        user_agent="custom-agent",
        enable_live_orders=True,
    )


def test_config_from_args_preserves_account_seq_override() -> None:
    args = parse_args(
        [
            "--client-id",
            "client-id",
            "--client-secret",
            "client-secret",
            "--account-seq",
            "1",
        ]
    )

    config = config_from_args(args)

    assert config.account == "1"
    assert config.account_number is None


def test_config_create_client_does_not_resolve_account_number() -> None:
    config = TossInvestMCPServerConfig(
        client_id="client-id",
        client_secret="client-secret",
        account_number="12345678901",
    )

    with config.create_client() as client:
        assert client.config.default_account is None


def test_config_resolves_account_number_once(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/accounts",
        result=[{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}],
    )
    config = TossInvestMCPServerConfig(
        client_id="client-id",
        client_secret="client-secret",
        account_number="12345678901",
    )

    assert config.account_seq_for_tool() == 1
    assert config.account_seq_for_tool() == 1

    requests = httpx_mock.get_requests(method="GET")
    assert len(requests) == 1


def test_config_uses_cached_account_before_ttl(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_time = 100.0
    monkeypatch.setattr("tossinvest._mcp.config.time.monotonic", lambda: current_time)
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/accounts",
        result=[{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}],
    )
    config = TossInvestMCPServerConfig(
        client_id="client-id",
        client_secret="client-secret",
        account_number="12345678901",
        account_cache_ttl=60.0,
    )

    assert config.account_seq_for_tool() == 1
    current_time = 159.0
    assert config.account_seq_for_tool() == 1

    account_requests = [
        request
        for request in httpx_mock.get_requests(method="GET")
        if request.url.path == "/api/v1/accounts"
    ]
    assert len(account_requests) == 1


def test_config_refreshes_cached_account_after_ttl(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_time = 100.0
    monkeypatch.setattr("tossinvest._mcp.config.time.monotonic", lambda: current_time)
    add_token_response(httpx_mock, token="token-1")
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/accounts",
        result=[{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}],
    )
    add_token_response(httpx_mock, token="token-2")
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/accounts",
        result=[{"accountNo": "12345678901", "accountSeq": 2, "accountType": "BROKERAGE"}],
    )
    config = TossInvestMCPServerConfig(
        client_id="client-id",
        client_secret="client-secret",
        account_number="12345678901",
        account_cache_ttl=60.0,
    )

    assert config.account_seq_for_tool() == 1
    current_time = 160.0
    assert config.account_seq_for_tool() == 2

    account_requests = [
        request
        for request in httpx_mock.get_requests(method="GET")
        if request.url.path == "/api/v1/accounts"
    ]
    assert len(account_requests) == 2


def test_tools_cache_account_resolution_from_list_accounts(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock, token="token-1")
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/accounts",
        result=[{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}],
    )
    add_token_response(httpx_mock, token="token-2")
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/buying-power?currency=USD",
        result={"currency": "USD", "cashBuyingPower": "100000"},
    )
    config = TossInvestMCPServerConfig(
        client_id="client-id",
        client_secret="client-secret",
        account_number="12345678901",
    )
    tools = TossInvestMCPTools(
        config.create_client,
        account_resolver=config.account_seq_for_tool,
        account_list_cache_getter=config.cached_account_list,
        account_list_observer=config.cache_account_list,
    )

    accounts = tools.list_accounts()
    buying_power = tools.get_buying_power(currency="USD")

    assert accounts == [{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}]
    assert buying_power == {"currency": "USD", "cashBuyingPower": "100000"}
    account_requests = [
        request
        for request in httpx_mock.get_requests(method="GET")
        if request.url.path == "/api/v1/accounts"
    ]
    assert len(account_requests) == 1


def test_account_resolution_populates_list_accounts_cache(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_time = 100.0
    monkeypatch.setattr("tossinvest._mcp.config.time.monotonic", lambda: current_time)
    add_token_response(httpx_mock, token="token-1")
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/accounts",
        result=[{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}],
    )
    add_token_response(httpx_mock, token="token-2")
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/buying-power?currency=USD",
        result={"currency": "USD", "cashBuyingPower": "100000"},
    )
    config = TossInvestMCPServerConfig(
        client_id="client-id",
        client_secret="client-secret",
        account_number="12345678901",
    )
    tools = TossInvestMCPTools(
        config.create_client,
        account_resolver=config.account_seq_for_tool,
        account_list_cache_getter=config.cached_account_list,
        account_list_observer=config.cache_account_list,
    )

    buying_power = tools.get_buying_power(currency="USD")
    current_time = 100.5
    accounts = tools.list_accounts()

    assert buying_power == {"currency": "USD", "cashBuyingPower": "100000"}
    assert accounts == [{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}]
    account_requests = [
        request
        for request in httpx_mock.get_requests(method="GET")
        if request.url.path == "/api/v1/accounts"
    ]
    assert len(account_requests) == 1


def test_tools_return_cached_accounts_before_rate_limit_window(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_time = 100.0
    monkeypatch.setattr("tossinvest._mcp.config.time.monotonic", lambda: current_time)
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/accounts",
        result=[{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}],
    )
    config = TossInvestMCPServerConfig(
        client_id="client-id",
        client_secret="client-secret",
        account_number="12345678901",
    )
    tools = TossInvestMCPTools(
        config.create_client,
        account_resolver=config.account_seq_for_tool,
        account_list_cache_getter=config.cached_account_list,
        account_list_observer=config.cache_account_list,
    )

    first_accounts = tools.list_accounts()
    current_time = 100.5
    cached_accounts = tools.list_accounts()

    assert first_accounts == cached_accounts
    account_requests = [
        request
        for request in httpx_mock.get_requests(method="GET")
        if request.url.path == "/api/v1/accounts"
    ]
    assert len(account_requests) == 1


def test_tools_refresh_cached_accounts_after_rate_limit_window(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_time = 100.0
    monkeypatch.setattr("tossinvest._mcp.config.time.monotonic", lambda: current_time)
    add_token_response(httpx_mock, token="token-1")
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/accounts",
        result=[{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}],
    )
    add_token_response(httpx_mock, token="token-2")
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/accounts",
        result=[{"accountNo": "12345678901", "accountSeq": 2, "accountType": "BROKERAGE"}],
    )
    config = TossInvestMCPServerConfig(
        client_id="client-id",
        client_secret="client-secret",
        account_number="12345678901",
    )
    tools = TossInvestMCPTools(
        config.create_client,
        account_resolver=config.account_seq_for_tool,
        account_list_cache_getter=config.cached_account_list,
        account_list_observer=config.cache_account_list,
    )

    first_accounts = tools.list_accounts()
    current_time = 101.0
    refreshed_accounts = tools.list_accounts()

    assert first_accounts[0]["accountSeq"] == 1
    assert refreshed_accounts[0]["accountSeq"] == 2
    account_requests = [
        request
        for request in httpx_mock.get_requests(method="GET")
        if request.url.path == "/api/v1/accounts"
    ]
    assert len(account_requests) == 2


def test_config_from_args_resolves_credentials_from_helpers() -> None:
    args = parse_args(
        [
            "--client-id-command",
            _python_command("print('helper-client-id')"),
            "--client-secret-command",
            _python_command("print('helper-client-secret')"),
            "--account",
            "12345678901",
        ]
    )

    config = config_from_args(args)

    assert config.client_id == "helper-client-id"
    assert config.client_secret == "helper-client-secret"
    assert config.account_number == "12345678901"


def test_credential_helper_error_does_not_include_output() -> None:
    args = parse_args(
        [
            "--client-id-command",
            _python_command("print('helper-client-id')"),
            "--client-secret-command",
            _python_command("print('leaked-secret'); raise SystemExit(2)"),
        ]
    )

    with pytest.raises(CredentialHelperError) as exc_info:
        config_from_args(args)

    message = str(exc_info.value)
    assert "client secret" in message
    assert "leaked-secret" not in message


async def test_create_server_registers_read_only_tools_only() -> None:
    pytest.importorskip("mcp.server.fastmcp")

    server = create_server(TossInvestMCPServerConfig("client-id", "client-secret"))

    tool_names = {tool.name for tool in await server.list_tools()}

    assert "list_accounts" in tool_names
    assert "find_account_by_number" in tool_names
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


async def test_list_orders_tool_schema_exposes_lifecycle_status_enum() -> None:
    pytest.importorskip("mcp.server.fastmcp")

    server = create_server(TossInvestMCPServerConfig("client-id", "client-secret"))

    tools = {tool.name: tool for tool in await server.list_tools()}
    schema = tools["list_orders"].inputSchema
    status_schema = schema["properties"]["status"]

    assert status_schema["default"] == "OPEN"
    assert _property_enum(schema, "status") == ["OPEN", "CLOSED"]
    assert "status" not in schema.get("required", [])


async def test_mcp_tool_descriptions_expose_rate_limit_groups() -> None:
    pytest.importorskip("mcp.server.fastmcp")

    server = create_server(
        TossInvestMCPServerConfig("client-id", "client-secret", enable_live_orders=True)
    )

    tools = {tool.name: tool for tool in await server.list_tools()}
    expected_groups = {
        "list_accounts": "ACCOUNT",
        "find_account_by_number": "ACCOUNT",
        "get_stock": "STOCK",
        "get_stocks": "STOCK",
        "get_stock_warnings": "STOCK",
        "get_orderbook": "MARKET_DATA",
        "get_price": "MARKET_DATA",
        "get_prices": "MARKET_DATA",
        "get_trades": "MARKET_DATA",
        "get_price_limit": "MARKET_DATA",
        "get_candles": "MARKET_DATA_CHART",
        "get_exchange_rate": "MARKET_INFO",
        "get_kr_market_calendar": "MARKET_INFO",
        "get_us_market_calendar": "MARKET_INFO",
        "get_holdings": "ASSET",
        "list_orders": "ORDER_HISTORY",
        "get_order": "ORDER_HISTORY",
        "get_buying_power": "ORDER_INFO",
        "get_sellable_quantity": "ORDER_INFO",
        "get_commissions": "ORDER_INFO",
        "create_order": "ORDER",
        "modify_order": "ORDER",
        "cancel_order": "ORDER",
    }

    for tool_name, group in expected_groups.items():
        description = tools[tool_name].description or ""
        assert f"Rate limit group: {group}" in description
        assert "429" in description
        assert "Retry-After" in description
        assert "X-RateLimit-Reset" in description


async def test_mcp_tool_schemas_expose_official_request_enums() -> None:
    pytest.importorskip("mcp.server.fastmcp")

    server = create_server(
        TossInvestMCPServerConfig("client-id", "client-secret", enable_live_orders=True)
    )

    tools = {tool.name: tool for tool in await server.list_tools()}

    assert _property_enum(tools["get_candles"].inputSchema, "interval") == ["1m", "1d"]
    assert _property_enum(tools["get_exchange_rate"].inputSchema, "base_currency") == [
        "KRW",
        "USD",
    ]
    assert _property_enum(tools["get_exchange_rate"].inputSchema, "quote_currency") == [
        "KRW",
        "USD",
    ]
    assert _property_enum(tools["get_buying_power"].inputSchema, "currency") == ["KRW", "USD"]
    assert _property_enum(tools["create_order"].inputSchema, "side") == ["BUY", "SELL"]
    assert _property_enum(tools["create_order"].inputSchema, "order_type") == [
        "LIMIT",
        "MARKET",
    ]
    assert _property_enum(tools["create_order"].inputSchema, "time_in_force") == ["DAY", "CLS"]
    assert _property_enum(tools["modify_order"].inputSchema, "order_type") == [
        "LIMIT",
        "MARKET",
    ]


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
