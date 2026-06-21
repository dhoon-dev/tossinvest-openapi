"""Pydantic models for TossInvest requests and API result payloads."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

type CandleInterval = Literal["1m", "1d"]
type CurrencyCode = Literal["KRW", "USD"]
type OrderListStatus = Literal["OPEN", "CLOSED"]
type OrderSide = Literal["BUY", "SELL"]
type OrderTimeInForce = Literal["DAY", "CLS"]
type OrderType = Literal["LIMIT", "MARKET"]


class TossInvestModel(BaseModel):
    """Base model that preserves additive API fields and official aliases."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class TossInvestRequestModel(BaseModel):
    """Base model that rejects unsupported request fields."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ApiError(TossInvestModel):
    """Error object from the official API error envelope."""

    request_id: str = Field(alias="requestId")
    code: str
    message: str
    data: dict[str, object] | None = None


class OAuth2TokenResponse(TossInvestModel):
    """OAuth token endpoint response."""

    access_token: str
    token_type: Literal["Bearer"]
    expires_in: int


class OrderbookEntry(TossInvestModel):
    """Single bid or ask level in an orderbook."""

    price: str
    volume: str


class OrderbookResponse(TossInvestModel):
    """Orderbook result for a requested symbol."""

    currency: str
    asks: list[OrderbookEntry]
    bids: list[OrderbookEntry]
    timestamp: str | None = None


class PriceResponse(TossInvestModel):
    """Current price result for a symbol."""

    symbol: str
    last_price: str = Field(alias="lastPrice")
    currency: str
    timestamp: str | None = None


class Trade(TossInvestModel):
    """Recent trade execution result for a symbol."""

    price: str
    volume: str
    timestamp: str
    currency: str


class PriceLimitResponse(TossInvestModel):
    """Upper and lower price limit result for a symbol."""

    timestamp: str
    currency: str
    lower_limit_price: str | None = Field(default=None, alias="lowerLimitPrice")
    upper_limit_price: str | None = Field(default=None, alias="upperLimitPrice")


class Candle(TossInvestModel):
    """OHLCV candle item."""

    timestamp: str
    open_price: str = Field(alias="openPrice")
    high_price: str = Field(alias="highPrice")
    low_price: str = Field(alias="lowPrice")
    close_price: str = Field(alias="closePrice")
    volume: str
    currency: str


class CandlePageResponse(TossInvestModel):
    """Cursor-like candle page with the next upper-bound timestamp."""

    candles: list[Candle]
    next_before: str | None = Field(default=None, alias="nextBefore")


class KrMarketDetail(TossInvestModel):
    """Additional Korean market flags returned with stock information."""

    liquidation_trading: bool = Field(alias="liquidationTrading")
    nxt_supported: bool = Field(alias="nxtSupported")
    krx_trading_suspended: bool = Field(alias="krxTradingSuspended")
    nxt_trading_suspended: bool | None = Field(default=None, alias="nxtTradingSuspended")


class StockInfo(TossInvestModel):
    """Stock master data returned by the stock information endpoint."""

    symbol: str
    name: str
    english_name: str = Field(alias="englishName")
    isin_code: str = Field(alias="isinCode")
    market: str
    security_type: str = Field(alias="securityType")
    is_common_share: bool = Field(alias="isCommonShare")
    status: str
    currency: str
    shares_outstanding: str = Field(alias="sharesOutstanding")
    list_date: str | None = Field(default=None, alias="listDate")
    delist_date: str | None = Field(default=None, alias="delistDate")
    leverage_factor: str | None = Field(default=None, alias="leverageFactor")
    korean_market_detail: KrMarketDetail | None = Field(default=None, alias="koreanMarketDetail")


class StockWarning(TossInvestModel):
    """Trading warning attached to a stock."""

    warning_type: str = Field(alias="warningType")
    start_date: str | None = Field(default=None, alias="startDate")
    end_date: str | None = Field(default=None, alias="endDate")
    exchange: str | None = None


class ExchangeRateResponse(TossInvestModel):
    """Currency exchange-rate result."""

    base_currency: str = Field(alias="baseCurrency")
    quote_currency: str = Field(alias="quoteCurrency")
    rate: str
    mid_rate: str = Field(alias="midRate")
    basis_point: str = Field(alias="basisPoint")
    rate_change_type: str = Field(alias="rateChangeType")
    valid_from: str = Field(alias="validFrom")
    valid_until: str = Field(alias="validUntil")


class MarketSession(TossInvestModel):
    """Market session window with start and end times."""

    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    single_price_auction_start_time: str | None = Field(
        default=None, alias="singlePriceAuctionStartTime"
    )
    single_price_auction_end_time: str | None = Field(
        default=None, alias="singlePriceAuctionEndTime"
    )


class IntegratedHour(TossInvestModel):
    """Integrated Korean market session hours."""

    pre_market: MarketSession | None = Field(default=None, alias="preMarket")
    regular_market: MarketSession | None = Field(default=None, alias="regularMarket")
    after_market: MarketSession | None = Field(default=None, alias="afterMarket")


class KrMarketDay(TossInvestModel):
    """Korean market calendar day."""

    date: str
    integrated: IntegratedHour | None = None


class KrMarketCalendarResponse(TossInvestModel):
    """Korean market calendar response centered on the requested date."""

    today: KrMarketDay
    previous_business_day: KrMarketDay = Field(alias="previousBusinessDay")
    next_business_day: KrMarketDay = Field(alias="nextBusinessDay")


class UsMarketDay(TossInvestModel):
    """US market calendar day."""

    date: str
    day_market: MarketSession | None = Field(default=None, alias="dayMarket")
    pre_market: MarketSession | None = Field(default=None, alias="preMarket")
    regular_market: MarketSession | None = Field(default=None, alias="regularMarket")
    after_market: MarketSession | None = Field(default=None, alias="afterMarket")


class UsMarketCalendarResponse(TossInvestModel):
    """US market calendar response centered on the requested date."""

    today: UsMarketDay
    previous_business_day: UsMarketDay = Field(alias="previousBusinessDay")
    next_business_day: UsMarketDay = Field(alias="nextBusinessDay")


class Account(TossInvestModel):
    """Account record used to choose the X-Tossinvest-Account value."""

    account_no: str = Field(alias="accountNo")
    account_seq: int = Field(alias="accountSeq")
    account_type: str = Field(alias="accountType")


class Price(TossInvestModel):
    """Currency bucket used by account and asset overview totals."""

    krw: str
    usd: str | None = None


class OverviewMarketValue(TossInvestModel):
    """Portfolio-level market value summary."""

    amount: Price
    amount_after_cost: Price = Field(alias="amountAfterCost")


class OverviewProfitLoss(TossInvestModel):
    """Portfolio-level profit and loss summary."""

    amount: Price
    amount_after_cost: Price = Field(alias="amountAfterCost")
    rate: str
    rate_after_cost: str = Field(alias="rateAfterCost")


class OverviewDailyProfitLoss(TossInvestModel):
    """Portfolio-level daily profit and loss summary."""

    amount: Price
    rate: str


class MarketValue(TossInvestModel):
    """Position-level market value summary."""

    purchase_amount: str = Field(alias="purchaseAmount")
    amount: str
    amount_after_cost: str = Field(alias="amountAfterCost")


class ProfitLoss(TossInvestModel):
    """Position-level profit and loss summary."""

    amount: str
    amount_after_cost: str = Field(alias="amountAfterCost")
    rate: str
    rate_after_cost: str = Field(alias="rateAfterCost")


class DailyProfitLoss(TossInvestModel):
    """Position-level daily profit and loss summary."""

    amount: str
    rate: str


class Cost(TossInvestModel):
    """Commission and tax cost summary."""

    commission: str
    tax: str | None = None


class HoldingsItem(TossInvestModel):
    """Single holding item in the holdings overview."""

    symbol: str
    name: str
    market_country: str = Field(alias="marketCountry")
    currency: str
    quantity: str
    last_price: str = Field(alias="lastPrice")
    average_purchase_price: str = Field(alias="averagePurchasePrice")
    market_value: MarketValue = Field(alias="marketValue")
    profit_loss: ProfitLoss = Field(alias="profitLoss")
    daily_profit_loss: DailyProfitLoss = Field(alias="dailyProfitLoss")
    cost: Cost


class HoldingsOverview(TossInvestModel):
    """Account holdings overview with totals and position items."""

    total_purchase_amount: Price = Field(alias="totalPurchaseAmount")
    market_value: OverviewMarketValue = Field(alias="marketValue")
    profit_loss: OverviewProfitLoss = Field(alias="profitLoss")
    daily_profit_loss: OverviewDailyProfitLoss = Field(alias="dailyProfitLoss")
    items: list[HoldingsItem]


class OrderCreateRequest(TossInvestRequestModel):
    """Request body for creating a live order.

    Exactly one of ``quantity`` or ``order_amount`` must be provided. Limit
    orders require ``price``; market orders must not include ``price``.
    Amount-based orders are constrained by the official API and are intended
    for supported market-order flows only.

    This model validates obvious SDK-side invariants before the HTTP request is
    sent, but it does not guarantee that the exchange, market session, buying
    power, or broker-side business rules will accept the order.
    """

    client_order_id: str | None = Field(default=None, alias="clientOrderId")
    symbol: str
    side: OrderSide
    order_type: OrderType = Field(alias="orderType")
    time_in_force: OrderTimeInForce | None = Field(default=None, alias="timeInForce")
    quantity: str | None = None
    order_amount: str | None = Field(default=None, alias="orderAmount")
    price: str | None = None
    confirm_high_value_order: bool | None = Field(default=None, alias="confirmHighValueOrder")

    @model_validator(mode="after")
    def validate_quantity_or_amount(self) -> Self:
        """Validate SDK-side order invariants before a request is sent."""
        has_quantity = self.quantity is not None
        has_amount = self.order_amount is not None
        if has_quantity == has_amount:
            msg = "Exactly one of quantity or order_amount must be provided."
            raise ValueError(msg)
        if self.order_amount is not None and self.order_type != "MARKET":
            msg = "Amount-based orders require order_type='MARKET'."
            raise ValueError(msg)
        if self.order_type == "LIMIT" and self.price is None:
            msg = "Limit orders require price."
            raise ValueError(msg)
        if self.order_type == "MARKET" and self.price is not None:
            msg = "Market orders must not include price."
            raise ValueError(msg)
        return self


class OrderModifyRequest(TossInvestRequestModel):
    """Request body for modifying an existing order.

    The official API validates market-specific rules such as whether quantity
    or price changes are allowed for the target order. The SDK preserves the
    official field names when serializing this model.
    """

    order_type: OrderType = Field(alias="orderType")
    quantity: str | None = None
    price: str | None = None
    confirm_high_value_order: bool | None = Field(default=None, alias="confirmHighValueOrder")


class OrderResponse(TossInvestModel):
    """Order creation response with the server order identifier."""

    order_id: str = Field(alias="orderId")
    client_order_id: str | None = Field(default=None, alias="clientOrderId")


class OrderOperationResponse(TossInvestModel):
    """Response returned by order modification and cancellation."""

    order_id: str = Field(alias="orderId")


class OrderExecution(TossInvestModel):
    """Execution details embedded in an order response."""

    filled_quantity: str = Field(alias="filledQuantity")
    average_filled_price: str | None = Field(alias="averageFilledPrice")
    filled_amount: str | None = Field(alias="filledAmount")
    commission: str | None
    tax: str | None
    filled_at: str | None = Field(alias="filledAt")
    settlement_date: str | None = Field(alias="settlementDate")


class Order(TossInvestModel):
    """Order detail returned by order history endpoints."""

    order_id: str = Field(alias="orderId")
    symbol: str
    side: str
    order_type: str = Field(alias="orderType")
    time_in_force: str = Field(alias="timeInForce")
    status: str
    quantity: str
    currency: str
    ordered_at: str = Field(alias="orderedAt")
    execution: OrderExecution
    price: str | None = None
    order_amount: str | None = Field(default=None, alias="orderAmount")
    canceled_at: str | None = Field(default=None, alias="canceledAt")


class PaginatedOrderResponse(TossInvestModel):
    """Order list response with cursor metadata."""

    orders: list[Order]
    next_cursor: str | None = Field(alias="nextCursor")
    has_next: bool = Field(alias="hasNext")


class BuyingPowerResponse(TossInvestModel):
    """Buying-power result for the requested currency."""

    currency: str
    cash_buying_power: str = Field(alias="cashBuyingPower")


class SellableQuantityResponse(TossInvestModel):
    """Sellable quantity result for the requested symbol."""

    sellable_quantity: str = Field(alias="sellableQuantity")


class Commission(TossInvestModel):
    """Commission rule returned for an account."""

    market_country: str = Field(alias="marketCountry")
    commission_rate: str = Field(alias="commissionRate")
    start_date: str | None = Field(default=None, alias="startDate")
    end_date: str | None = Field(default=None, alias="endDate")


def parse_model[ModelT: TossInvestModel](model: type[ModelT], data: object) -> ModelT:
    """Validate one API result object as the requested SDK model."""
    return model.model_validate(data)


def parse_model_list[ModelT: TossInvestModel](model: type[ModelT], data: object) -> list[ModelT]:
    """Validate a list API result as a list of SDK models."""
    if not isinstance(data, list):
        msg = "Expected the API result to be a list."
        raise ValueError(msg)
    return [model.model_validate(item) for item in data]
