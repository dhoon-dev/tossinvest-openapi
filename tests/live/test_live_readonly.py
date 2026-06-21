from __future__ import annotations

import os
from typing import cast

import pytest

from tossinvest import Account, CurrencyCode, TossInvestClient

pytestmark = [
    pytest.mark.integration,
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("TOSSINVEST_ENABLE_LIVE_TESTS") != "true",
        reason="Set TOSSINVEST_ENABLE_LIVE_TESTS=true to run live TossInvest API tests.",
    ),
]


def test_live_access_token(live_client: TossInvestClient) -> None:
    token = live_client.get_access_token()

    assert token


def test_live_market_prices(live_client: TossInvestClient) -> None:
    symbol = _live_symbol()

    prices = live_client.market_data.get_prices([symbol])

    assert prices
    assert prices[0].symbol == symbol
    assert prices[0].last_price
    assert prices[0].currency


def test_live_market_orderbook(live_client: TossInvestClient) -> None:
    orderbook = live_client.market_data.get_orderbook(_live_symbol())

    assert orderbook.currency
    assert isinstance(orderbook.asks, list)
    assert isinstance(orderbook.bids, list)


def test_live_market_trades(live_client: TossInvestClient) -> None:
    trades = live_client.market_data.get_trades(_live_symbol(), count=5)

    assert isinstance(trades, list)
    if trades:
        assert trades[0].price
        assert trades[0].currency


def test_live_market_price_limit(live_client: TossInvestClient) -> None:
    price_limit = live_client.market_data.get_price_limit(_live_symbol())

    assert price_limit.timestamp
    assert price_limit.currency


def test_live_market_candles(live_client: TossInvestClient) -> None:
    page = live_client.market_data.get_candles(_live_symbol(), interval="1d", count=1)

    assert isinstance(page.candles, list)
    if page.candles:
        assert page.candles[0].close_price
        assert page.candles[0].currency


def test_live_stocks(live_client: TossInvestClient) -> None:
    stocks = live_client.stocks.get_stocks([_live_symbol()])

    assert stocks
    assert stocks[0].symbol == _live_symbol()
    assert stocks[0].name


def test_live_stock_warnings(live_client: TossInvestClient) -> None:
    warnings = live_client.stocks.get_stock_warnings(_live_symbol())

    assert isinstance(warnings, list)
    if warnings:
        assert warnings[0].warning_type


def test_live_exchange_rate(live_client: TossInvestClient) -> None:
    rate = live_client.market_info.get_exchange_rate(
        base_currency="USD",
        quote_currency="KRW",
    )

    assert rate.base_currency == "USD"
    assert rate.quote_currency == "KRW"
    assert rate.rate


def test_live_kr_market_calendar(live_client: TossInvestClient) -> None:
    calendar = live_client.market_info.get_kr_market_calendar()

    assert calendar.today.date
    assert calendar.previous_business_day.date
    assert calendar.next_business_day.date


def test_live_us_market_calendar(live_client: TossInvestClient) -> None:
    calendar = live_client.market_info.get_us_market_calendar()

    assert calendar.today.date
    assert calendar.previous_business_day.date
    assert calendar.next_business_day.date


def test_live_accounts(live_accounts: list[Account]) -> None:
    assert isinstance(live_accounts, list)
    if live_accounts:
        account = live_accounts[0]
        assert account.account_seq >= 0
        assert account.account_type


def test_live_holdings(live_client: TossInvestClient, live_account: str) -> None:
    holdings = live_client.assets.get_holdings(account=live_account)

    assert holdings.market_value.amount.krw
    assert isinstance(holdings.items, list)


def test_live_buying_power(live_client: TossInvestClient, live_account: str) -> None:
    currency = _live_currency()

    buying_power = live_client.orders.get_buying_power(currency=currency, account=live_account)

    assert buying_power.currency == currency
    assert buying_power.cash_buying_power


def test_live_commissions(live_client: TossInvestClient, live_account: str) -> None:
    commissions = live_client.orders.get_commissions(account=live_account)

    assert isinstance(commissions, list)
    assert commissions


def test_live_sellable_quantity(live_client: TossInvestClient, live_account: str) -> None:
    quantity = live_client.orders.get_sellable_quantity(symbol=_live_symbol(), account=live_account)

    assert quantity.sellable_quantity is not None


def test_live_open_orders(live_client: TossInvestClient, live_account: str) -> None:
    page = live_client.orders.list_orders(status="OPEN", account=live_account)

    assert isinstance(page.orders, list)
    assert isinstance(page.has_next, bool)


def _live_symbol() -> str:
    return os.getenv("TOSSINVEST_LIVE_SYMBOL") or "005930"


def _live_currency() -> CurrencyCode:
    currency = os.getenv("TOSSINVEST_LIVE_CURRENCY") or "KRW"
    if currency not in {"KRW", "USD"}:
        msg = "TOSSINVEST_LIVE_CURRENCY must be KRW or USD."
        raise ValueError(msg)
    return cast(CurrencyCode, currency)
