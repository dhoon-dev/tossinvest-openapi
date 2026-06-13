"""Read-only MCP tool implementations backed by the TossInvest SDK."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import cast

from pydantic import BaseModel

from tossinvest.client import TossInvestClient
from tossinvest.models import OrderCreateRequest, OrderModifyRequest

type ClientContextFactory = Callable[[], AbstractContextManager[TossInvestClient]]


@dataclass(frozen=True, slots=True)
class TossInvestMCPTools:
    """Read-only TossInvest operations exposed through MCP."""

    client_factory: ClientContextFactory

    def list_accounts(self) -> list[dict[str, object]]:
        """List accounts available to the authenticated OAuth client."""
        with self.client_factory() as client:
            return _dump_model_list(client.accounts.list_accounts())

    def get_stock(self, symbol: str) -> dict[str, object]:
        """Return one stock master record."""
        with self.client_factory() as client:
            return _dump_model(client.stocks.get_stock(symbol))

    def get_stocks(self, symbols: Sequence[str]) -> list[dict[str, object]]:
        """Return stock master records for one or more symbols."""
        with self.client_factory() as client:
            return _dump_model_list(client.stocks.get_stocks(symbols))

    def get_stock_warnings(self, symbol: str) -> list[dict[str, object]]:
        """Return trading warnings for a symbol."""
        with self.client_factory() as client:
            return _dump_model_list(client.stocks.get_stock_warnings(symbol))

    def get_orderbook(self, symbol: str) -> dict[str, object]:
        """Return the current orderbook for a symbol."""
        with self.client_factory() as client:
            return _dump_model(client.market_data.get_orderbook(symbol))

    def get_price(self, symbol: str) -> dict[str, object]:
        """Return the current price for one symbol."""
        with self.client_factory() as client:
            return _dump_model(client.market_data.get_price(symbol))

    def get_prices(self, symbols: Sequence[str]) -> list[dict[str, object]]:
        """Return current prices for one or more symbols."""
        with self.client_factory() as client:
            return _dump_model_list(client.market_data.get_prices(symbols))

    def get_trades(self, symbol: str, count: int | None = None) -> list[dict[str, object]]:
        """Return recent trades for a symbol."""
        with self.client_factory() as client:
            return _dump_model_list(client.market_data.get_trades(symbol, count=count))

    def get_price_limit(self, symbol: str) -> dict[str, object]:
        """Return upper and lower price limits for a symbol."""
        with self.client_factory() as client:
            return _dump_model(client.market_data.get_price_limit(symbol))

    def get_candles(
        self,
        symbol: str,
        *,
        interval: str,
        count: int | None = None,
        before: str | None = None,
        adjusted: bool | None = None,
    ) -> dict[str, object]:
        """Return candle data for a symbol and interval."""
        with self.client_factory() as client:
            return _dump_model(
                client.market_data.get_candles(
                    symbol,
                    interval=interval,
                    count=count,
                    before=before,
                    adjusted=adjusted,
                )
            )

    def get_exchange_rate(
        self,
        *,
        base_currency: str,
        quote_currency: str,
        date_time: str | None = None,
    ) -> dict[str, object]:
        """Return an exchange rate between two supported currencies."""
        with self.client_factory() as client:
            return _dump_model(
                client.market_info.get_exchange_rate(
                    base_currency=base_currency,
                    quote_currency=quote_currency,
                    date_time=date_time,
                )
            )

    def get_kr_market_calendar(self, date: str | None = None) -> dict[str, object]:
        """Return Korean market calendar information."""
        with self.client_factory() as client:
            return _dump_model(client.market_info.get_kr_market_calendar(date=date))

    def get_us_market_calendar(self, date: str | None = None) -> dict[str, object]:
        """Return US market calendar information."""
        with self.client_factory() as client:
            return _dump_model(client.market_info.get_us_market_calendar(date=date))

    def get_holdings(
        self,
        symbol: str | None = None,
        account_seq: str | int | None = None,
    ) -> dict[str, object]:
        """Return holdings for the configured or overridden accountSeq."""
        with self.client_factory() as client:
            return _dump_model(client.assets.get_holdings(symbol=symbol, account=account_seq))

    def list_orders(
        self,
        *,
        status: str,
        symbol: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        account_seq: str | int | None = None,
    ) -> dict[str, object]:
        """List orders for the configured or overridden accountSeq."""
        with self.client_factory() as client:
            return _dump_model(
                client.orders.list_orders(
                    status=status,
                    symbol=symbol,
                    from_date=from_date,
                    to_date=to_date,
                    cursor=cursor,
                    limit=limit,
                    account=account_seq,
                )
            )

    def get_order(self, order_id: str, account_seq: str | int | None = None) -> dict[str, object]:
        """Return one order by server order identifier."""
        with self.client_factory() as client:
            return _dump_model(client.orders.get_order(order_id, account=account_seq))

    def get_buying_power(
        self,
        *,
        currency: str,
        account_seq: str | int | None = None,
    ) -> dict[str, object]:
        """Return cash buying power for the requested currency."""
        with self.client_factory() as client:
            return _dump_model(
                client.orders.get_buying_power(currency=currency, account=account_seq)
            )

    def get_sellable_quantity(
        self,
        *,
        symbol: str,
        account_seq: str | int | None = None,
    ) -> dict[str, object]:
        """Return the sellable quantity for a symbol."""
        with self.client_factory() as client:
            return _dump_model(
                client.orders.get_sellable_quantity(symbol=symbol, account=account_seq)
            )

    def get_commissions(self, account_seq: str | int | None = None) -> list[dict[str, object]]:
        """Return commission rules for the configured or overridden accountSeq."""
        with self.client_factory() as client:
            return _dump_model_list(client.orders.get_commissions(account=account_seq))

    def create_order(
        self,
        *,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str | None = None,
        order_amount: str | None = None,
        price: str | None = None,
        time_in_force: str | None = None,
        client_order_id: str | None = None,
        confirm_high_value_order: bool | None = None,
        account_seq: str | int | None = None,
    ) -> dict[str, object]:
        """Submit a live order request for the configured or overridden accountSeq."""
        request = OrderCreateRequest.model_validate(
            {
                "clientOrderId": client_order_id,
                "symbol": symbol,
                "side": side,
                "orderType": order_type,
                "timeInForce": time_in_force,
                "quantity": quantity,
                "orderAmount": order_amount,
                "price": price,
                "confirmHighValueOrder": confirm_high_value_order,
            }
        )
        with self.client_factory() as client:
            return _dump_model(client.orders.create_order(request, account=account_seq))

    def modify_order(
        self,
        order_id: str,
        *,
        order_type: str,
        quantity: str | None = None,
        price: str | None = None,
        confirm_high_value_order: bool | None = None,
        account_seq: str | int | None = None,
    ) -> dict[str, object]:
        """Modify an existing live order by server order identifier and accountSeq."""
        request = OrderModifyRequest.model_validate(
            {
                "orderType": order_type,
                "quantity": quantity,
                "price": price,
                "confirmHighValueOrder": confirm_high_value_order,
            }
        )
        with self.client_factory() as client:
            return _dump_model(client.orders.modify_order(order_id, request, account=account_seq))

    def cancel_order(
        self, order_id: str, account_seq: str | int | None = None
    ) -> dict[str, object]:
        """Cancel an existing live order by server order identifier and accountSeq."""
        with self.client_factory() as client:
            return _dump_model(client.orders.cancel_order(order_id, account=account_seq))


def _dump_model(value: object) -> dict[str, object]:
    dumped = _dump_value(value)
    if not isinstance(dumped, dict):
        msg = "Expected a model-like SDK result."
        raise TypeError(msg)
    return cast(dict[str, object], dumped)


def _dump_model_list(value: object) -> list[dict[str, object]]:
    dumped = _dump_value(value)
    if not isinstance(dumped, list):
        msg = "Expected a list-like SDK result."
        raise TypeError(msg)
    return cast(list[dict[str, object]], dumped)


def _dump_value(value: object) -> object:
    if isinstance(value, BaseModel):
        return cast(object, value.model_dump(by_alias=True, exclude_none=True))
    if isinstance(value, list | tuple):
        return [_dump_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _dump_value(item) for key, item in value.items()}
    return value
