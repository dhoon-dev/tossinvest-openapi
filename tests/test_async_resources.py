from __future__ import annotations

from pytest_httpx import HTTPXMock

from tossinvest import AsyncTossInvestClient, OrderCreateRequest, OrderModifyRequest

from .conftest import (
    TOKEN_URL,
    add_api_response,
    add_token_response,
    holdings_payload,
    kr_market_calendar_payload,
    order_payload,
    price_payload,
    stock_payload,
    us_market_calendar_payload,
)


async def test_async_market_data_methods(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/orderbook?symbol=005930",
        result={
            "timestamp": "2026-03-25T09:30:00+09:00",
            "currency": "KRW",
            "asks": [{"price": "72000", "volume": "10"}],
            "bids": [{"price": "71900", "volume": "8"}],
        },
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/prices?symbols=005930",
        result=[price_payload()],
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/trades?symbol=005930&count=2",
        result=[
            {
                "price": "72000",
                "volume": "3",
                "timestamp": "2026-03-25T09:30:01+09:00",
                "currency": "KRW",
            }
        ],
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/price-limits?symbol=005930",
        result={
            "timestamp": "2026-03-25T09:30:00+09:00",
            "currency": "KRW",
            "lowerLimitPrice": "50000",
            "upperLimitPrice": "90000",
        },
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/candles?symbol=005930&interval=1d",
        result={
            "candles": [
                {
                    "timestamp": "2026-03-25T00:00:00+09:00",
                    "openPrice": "71000",
                    "highPrice": "73000",
                    "lowPrice": "70000",
                    "closePrice": "72000",
                    "volume": "1000",
                    "currency": "KRW",
                }
            ],
            "nextBefore": "2026-03-24T00:00:00+09:00",
        },
    )

    async with AsyncTossInvestClient("client-id", "client-secret") as client:
        orderbook = await client.market_data.get_orderbook("005930")
        price = await client.market_data.get_price("005930")
        trades = await client.market_data.get_trades("005930", count=2)
        price_limit = await client.market_data.get_price_limit("005930")
        candles = await client.market_data.get_candles("005930", interval="1d")

    assert orderbook.asks[0].price == "72000"
    assert price.last_price == "72000"
    assert trades[0].volume == "3"
    assert price_limit.upper_limit_price == "90000"
    assert candles.candles[0].close_price == "72000"
    assert len(httpx_mock.get_requests(method="POST", url=TOKEN_URL)) == 1


async def test_async_reference_data_methods(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/stocks?symbols=005930",
        result=[stock_payload()],
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/stocks/005930/warnings",
        result=[
            {
                "warningType": "INVESTMENT_WARNING",
                "startDate": "2026-03-01",
                "endDate": None,
                "exchange": "KRX",
            }
        ],
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/exchange-rate?baseCurrency=USD&quoteCurrency=KRW",
        result={
            "baseCurrency": "USD",
            "quoteCurrency": "KRW",
            "rate": "1350.10",
            "midRate": "1350.00",
            "basisPoint": "0.10",
            "rateChangeType": "RISE",
            "validFrom": "2026-03-25T09:00:00+09:00",
            "validUntil": "2026-03-25T09:05:00+09:00",
        },
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/market-calendar/KR?date=2026-03-25",
        result=kr_market_calendar_payload(),
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/market-calendar/US?date=2026-03-25",
        result=us_market_calendar_payload(),
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/accounts",
        result=[{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}],
    )

    async with AsyncTossInvestClient("client-id", "client-secret") as client:
        stocks = await client.stocks.get_stocks("005930")
        warnings = await client.stocks.get_stock_warnings("005930")
        rate = await client.market_info.get_exchange_rate(
            base_currency="USD",
            quote_currency="KRW",
        )
        kr_calendar = await client.market_info.get_kr_market_calendar(date="2026-03-25")
        us_calendar = await client.market_info.get_us_market_calendar(date="2026-03-25")
        accounts = await client.accounts.list_accounts()

    assert stocks[0].english_name == "Samsung Electronics"
    assert warnings[0].warning_type == "INVESTMENT_WARNING"
    assert rate.mid_rate == "1350.00"
    assert kr_calendar.next_business_day.date == "2026-03-26"
    assert us_calendar.previous_business_day.date == "2026-03-24"
    assert accounts[0].account_seq == 1


async def test_async_account_scoped_methods(httpx_mock: HTTPXMock) -> None:
    add_token_response(httpx_mock)
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/holdings?symbol=005930",
        result=holdings_payload(),
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/orders?status=OPEN",
        result={"orders": [order_payload()], "nextCursor": None, "hasNext": False},
    )
    add_api_response(
        httpx_mock,
        method="POST",
        url="https://openapi.tossinvest.com/api/v1/orders",
        result={"orderId": "order-1", "clientOrderId": "client-order-1"},
    )
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/orders/order-1",
        result=order_payload(),
    )
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
    add_api_response(
        httpx_mock,
        method="GET",
        url="https://openapi.tossinvest.com/api/v1/sellable-quantity?symbol=005930",
        result={"sellableQuantity": "10"},
    )
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

    async with AsyncTossInvestClient("client-id", "client-secret", account="1") as client:
        holdings = await client.assets.get_holdings(symbol="005930")
        orders = await client.orders.list_orders(status="OPEN")
        created = await client.orders.create_order(
            OrderCreateRequest(
                clientOrderId="client-order-1",
                symbol="005930",
                side="BUY",
                orderType="LIMIT",
                quantity="1",
                price="70000",
            )
        )
        order = await client.orders.get_order("order-1")
        modified = await client.orders.modify_order(
            "order-1", OrderModifyRequest(orderType="LIMIT", price="71000")
        )
        canceled = await client.orders.cancel_order("order-1")
        buying_power = await client.orders.get_buying_power(currency="KRW")
        sellable_quantity = await client.orders.get_sellable_quantity(symbol="005930")
        commissions = await client.orders.get_commissions()

    holdings_request = httpx_mock.get_requests(method="GET")[0]
    create_request = httpx_mock.get_requests(method="POST")[-3]
    cancel_request = httpx_mock.get_requests(method="POST")[-1]
    assert holdings.items == []
    assert orders.orders[0].order_id == "order-1"
    assert created.client_order_id == "client-order-1"
    assert order.execution.filled_quantity == "0"
    assert modified.order_id == "order-1"
    assert canceled.order_id == "order-1"
    assert buying_power.cash_buying_power == "100000"
    assert sellable_quantity.sellable_quantity == "10"
    assert commissions[0].commission_rate == "0.015"
    assert holdings_request.headers["x-tossinvest-account"] == "1"
    assert create_request.read().decode() == (
        '{"clientOrderId":"client-order-1","symbol":"005930","side":"BUY",'
        '"orderType":"LIMIT","quantity":"1","price":"70000"}'
    )
    assert cancel_request.headers["content-type"] == "application/json"
    assert cancel_request.read() == b""
