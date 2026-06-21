from __future__ import annotations

import json
from pathlib import Path

from tossinvest.async_client import AsyncTossInvestClient
from tossinvest.client import TossInvestClient
from tossinvest.resources import IMPLEMENTED_OPERATIONS
from tossinvest.resources.accounts import AccountsResource, AsyncAccountsResource
from tossinvest.resources.assets import AssetsResource, AsyncAssetsResource
from tossinvest.resources.market_data import AsyncMarketDataResource, MarketDataResource
from tossinvest.resources.market_info import AsyncMarketInfoResource, MarketInfoResource
from tossinvest.resources.orders import AsyncOrdersResource, OrdersResource
from tossinvest.resources.stocks import AsyncStocksResource, StocksResource


def test_implemented_operations_match_snapshot() -> None:
    snapshot_path = Path(__file__).with_name("openapi_operations_snapshot.json")
    snapshot = json.loads(snapshot_path.read_text())
    implemented = {
        operation_id: {
            "method": method,
            "path": path,
            "account_required": account_required,
        }
        for operation_id, (method, path, account_required) in IMPLEMENTED_OPERATIONS.items()
    }
    expected = {
        operation_id: {
            "method": details["method"],
            "path": details["path"],
            "account_required": details["account_required"],
        }
        for operation_id, details in snapshot.items()
        if operation_id != "issueOAuth2Token"
    }

    assert implemented == expected


def test_snapshot_records_required_parameters() -> None:
    snapshot_path = Path(__file__).with_name("openapi_operations_snapshot.json")
    snapshot = json.loads(snapshot_path.read_text())

    assert snapshot["getPrices"]["required_query"] == ["symbols"]
    assert snapshot["getCandles"]["required_query"] == ["symbol", "interval"]
    assert snapshot["getOrders"]["required_query"] == ["status"]
    assert snapshot["getBuyingPower"]["required_query"] == ["currency"]


def test_public_api_docstrings_include_rate_limit_groups() -> None:
    docstring_groups = {
        (TossInvestClient, "get_access_token"): "AUTH",
        (TossInvestClient, "request"): "depends on the target endpoint",
        (AsyncTossInvestClient, "get_access_token"): "AUTH",
        (AsyncTossInvestClient, "request"): "depends on the target endpoint",
        (AccountsResource, "list_accounts"): "ACCOUNT",
        (AccountsResource, "get_accounts"): "ACCOUNT",
        (AsyncAccountsResource, "list_accounts"): "ACCOUNT",
        (AsyncAccountsResource, "get_accounts"): "ACCOUNT",
        (MarketDataResource, "get_orderbook"): "MARKET_DATA",
        (MarketDataResource, "get_prices"): "MARKET_DATA",
        (MarketDataResource, "get_price"): "MARKET_DATA",
        (MarketDataResource, "get_trades"): "MARKET_DATA",
        (MarketDataResource, "get_price_limit"): "MARKET_DATA",
        (MarketDataResource, "get_candles"): "MARKET_DATA_CHART",
        (AsyncMarketDataResource, "get_orderbook"): "MARKET_DATA",
        (AsyncMarketDataResource, "get_prices"): "MARKET_DATA",
        (AsyncMarketDataResource, "get_price"): "MARKET_DATA",
        (AsyncMarketDataResource, "get_trades"): "MARKET_DATA",
        (AsyncMarketDataResource, "get_price_limit"): "MARKET_DATA",
        (AsyncMarketDataResource, "get_candles"): "MARKET_DATA_CHART",
        (StocksResource, "get_stocks"): "STOCK",
        (StocksResource, "get_stock"): "STOCK",
        (StocksResource, "get_stock_warnings"): "STOCK",
        (AsyncStocksResource, "get_stocks"): "STOCK",
        (AsyncStocksResource, "get_stock"): "STOCK",
        (AsyncStocksResource, "get_stock_warnings"): "STOCK",
        (MarketInfoResource, "get_exchange_rate"): "MARKET_INFO",
        (MarketInfoResource, "get_kr_market_calendar"): "MARKET_INFO",
        (MarketInfoResource, "get_us_market_calendar"): "MARKET_INFO",
        (AsyncMarketInfoResource, "get_exchange_rate"): "MARKET_INFO",
        (AsyncMarketInfoResource, "get_kr_market_calendar"): "MARKET_INFO",
        (AsyncMarketInfoResource, "get_us_market_calendar"): "MARKET_INFO",
        (AssetsResource, "get_holdings"): "ASSET",
        (AsyncAssetsResource, "get_holdings"): "ASSET",
        (OrdersResource, "list_orders"): "ORDER_HISTORY",
        (OrdersResource, "create_order"): "ORDER",
        (OrdersResource, "get_order"): "ORDER_HISTORY",
        (OrdersResource, "modify_order"): "ORDER",
        (OrdersResource, "cancel_order"): "ORDER",
        (OrdersResource, "get_buying_power"): "ORDER_INFO",
        (OrdersResource, "get_sellable_quantity"): "ORDER_INFO",
        (OrdersResource, "get_commissions"): "ORDER_INFO",
        (AsyncOrdersResource, "list_orders"): "ORDER_HISTORY",
        (AsyncOrdersResource, "create_order"): "ORDER",
        (AsyncOrdersResource, "get_order"): "ORDER_HISTORY",
        (AsyncOrdersResource, "modify_order"): "ORDER",
        (AsyncOrdersResource, "cancel_order"): "ORDER",
        (AsyncOrdersResource, "get_buying_power"): "ORDER_INFO",
        (AsyncOrdersResource, "get_sellable_quantity"): "ORDER_INFO",
        (AsyncOrdersResource, "get_commissions"): "ORDER_INFO",
    }

    for (resource_class, method_name), group in docstring_groups.items():
        docstring = getattr(resource_class, method_name).__doc__ or ""
        assert group in docstring
        assert "429" in docstring
        assert "Retry-After" in docstring
        assert "X-RateLimit-Reset" in docstring
