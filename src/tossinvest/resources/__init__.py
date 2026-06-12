"""Operation metadata used to keep resource methods aligned with OpenAPI."""

from __future__ import annotations

from types import MappingProxyType

IMPLEMENTED_OPERATIONS = MappingProxyType(
    {
        "getOrderbook": ("GET", "/api/v1/orderbook", False),
        "getPrices": ("GET", "/api/v1/prices", False),
        "getTrades": ("GET", "/api/v1/trades", False),
        "getPriceLimit": ("GET", "/api/v1/price-limits", False),
        "getCandles": ("GET", "/api/v1/candles", False),
        "getStocks": ("GET", "/api/v1/stocks", False),
        "getStockWarnings": ("GET", "/api/v1/stocks/{symbol}/warnings", False),
        "getExchangeRate": ("GET", "/api/v1/exchange-rate", False),
        "getKrMarketCalendar": ("GET", "/api/v1/market-calendar/KR", False),
        "getUsMarketCalendar": ("GET", "/api/v1/market-calendar/US", False),
        "getAccounts": ("GET", "/api/v1/accounts", False),
        "getHoldings": ("GET", "/api/v1/holdings", True),
        "getOrders": ("GET", "/api/v1/orders", True),
        "createOrder": ("POST", "/api/v1/orders", True),
        "getOrder": ("GET", "/api/v1/orders/{orderId}", True),
        "modifyOrder": ("POST", "/api/v1/orders/{orderId}/modify", True),
        "cancelOrder": ("POST", "/api/v1/orders/{orderId}/cancel", True),
        "getBuyingPower": ("GET", "/api/v1/buying-power", True),
        "getSellableQuantity": ("GET", "/api/v1/sellable-quantity", True),
        "getCommissions": ("GET", "/api/v1/commissions", True),
    }
)

__all__ = ["IMPLEMENTED_OPERATIONS"]
