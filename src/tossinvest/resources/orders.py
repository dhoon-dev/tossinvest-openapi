"""Order resource methods."""

from __future__ import annotations

from tossinvest._http import AsyncHTTPClient, SyncHTTPClient
from tossinvest.models import (
    BuyingPowerResponse,
    Commission,
    CurrencyCode,
    Order,
    OrderCreateRequest,
    OrderListStatus,
    OrderModifyRequest,
    OrderOperationResponse,
    OrderResponse,
    PaginatedOrderResponse,
    SellableQuantityResponse,
    parse_model,
    parse_model_list,
)

from ._utils import require_non_empty


class OrdersResource:
    """Synchronous order endpoints requiring an account header."""

    def __init__(self, http: SyncHTTPClient) -> None:
        self._http = http

    def list_orders(
        self,
        *,
        status: OrderListStatus,
        symbol: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        account: str | int | None = None,
    ) -> PaginatedOrderResponse:
        """List orders for the configured or overridden account.

        Requires ``X-Tossinvest-Account``. ``status`` must follow the official
        order-history grouping values such as ``"OPEN"`` or ``"CLOSED"``.

        Args:
            status: Official order lifecycle group filter.
            symbol: Optional symbol filter.
            from_date: Optional inclusive start date.
            to_date: Optional inclusive end date.
            cursor: Optional pagination cursor.
            limit: Optional page size for closed-order queries.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET",
            "/api/v1/orders",
            params={
                "status": status,
                "symbol": symbol,
                "from": from_date,
                "to": to_date,
                "cursor": cursor,
                "limit": limit,
            },
            account_required=True,
            account=account,
        )
        return parse_model(PaginatedOrderResponse, result)

    def create_order(
        self, request: OrderCreateRequest, *, account: str | int | None = None
    ) -> OrderResponse:
        """Submit a live order request for the configured or overridden account.

        This method can place a real securities order. Validate the payload,
        account, market session, and all external safeguards before calling it.
        The SDK does not retry this non-idempotent endpoint automatically.

        Args:
            request: Validated order creation body.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API rejects the order or returns another
                error response.

        """
        result = self._http.request(
            "POST",
            "/api/v1/orders",
            json=request,
            account_required=True,
            account=account,
        )
        return parse_model(OrderResponse, result)

    def get_order(self, order_id: str, *, account: str | int | None = None) -> Order:
        """Return one order by server order identifier.

        Args:
            order_id: Server order identifier returned by order APIs.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available or ``order_id``
                is empty.
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET",
            f"/api/v1/orders/{require_non_empty('order_id', order_id)}",
            account_required=True,
            account=account,
        )
        return parse_model(Order, result)

    def modify_order(
        self,
        order_id: str,
        request: OrderModifyRequest,
        *,
        account: str | int | None = None,
    ) -> OrderOperationResponse:
        """Modify an existing order by server order identifier.

        This method can change a real pending order. The SDK does not retry this
        non-idempotent endpoint automatically.

        Args:
            order_id: Server order identifier to modify.
            request: Validated order modification body.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available or ``order_id``
                is empty.
            TossInvestAPIError: The API rejects the modification or returns
                another error response.

        """
        result = self._http.request(
            "POST",
            f"/api/v1/orders/{require_non_empty('order_id', order_id)}/modify",
            json=request,
            account_required=True,
            account=account,
        )
        return parse_model(OrderOperationResponse, result)

    def cancel_order(
        self, order_id: str, *, account: str | int | None = None
    ) -> OrderOperationResponse:
        """Cancel an existing order by server order identifier.

        This method can cancel a real pending order. The SDK does not retry this
        non-idempotent endpoint automatically.

        Args:
            order_id: Server order identifier to cancel.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available or ``order_id``
                is empty.
            TossInvestAPIError: The API rejects the cancellation or returns
                another error response.

        """
        result = self._http.request(
            "POST",
            f"/api/v1/orders/{require_non_empty('order_id', order_id)}/cancel",
            account_required=True,
            account=account,
        )
        return parse_model(OrderOperationResponse, result)

    def get_buying_power(
        self, *, currency: CurrencyCode, account: str | int | None = None
    ) -> BuyingPowerResponse:
        """Return cash buying power for the requested currency.

        Args:
            currency: Currency code supported by the official API.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET",
            "/api/v1/buying-power",
            params={"currency": currency},
            account_required=True,
            account=account,
        )
        return parse_model(BuyingPowerResponse, result)

    def get_sellable_quantity(
        self, *, symbol: str, account: str | int | None = None
    ) -> SellableQuantityResponse:
        """Return the sellable quantity for a symbol.

        Args:
            symbol: Stock symbol accepted by the official API.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET",
            "/api/v1/sellable-quantity",
            params={"symbol": symbol},
            account_required=True,
            account=account,
        )
        return parse_model(SellableQuantityResponse, result)

    def get_commissions(self, *, account: str | int | None = None) -> list[Commission]:
        """Return commission rules for the configured or overridden account.

        Args:
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request(
            "GET",
            "/api/v1/commissions",
            account_required=True,
            account=account,
        )
        return parse_model_list(Commission, result)


class AsyncOrdersResource:
    """Asynchronous order endpoints requiring an account header."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list_orders(
        self,
        *,
        status: OrderListStatus,
        symbol: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        account: str | int | None = None,
    ) -> PaginatedOrderResponse:
        """List orders for the configured or overridden account.

        Requires ``X-Tossinvest-Account``. ``status`` must follow the official
        order-history grouping values such as ``"OPEN"`` or ``"CLOSED"``.

        Args:
            status: Official order lifecycle group filter.
            symbol: Optional symbol filter.
            from_date: Optional inclusive start date.
            to_date: Optional inclusive end date.
            cursor: Optional pagination cursor.
            limit: Optional page size for closed-order queries.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET",
            "/api/v1/orders",
            params={
                "status": status,
                "symbol": symbol,
                "from": from_date,
                "to": to_date,
                "cursor": cursor,
                "limit": limit,
            },
            account_required=True,
            account=account,
        )
        return parse_model(PaginatedOrderResponse, result)

    async def create_order(
        self, request: OrderCreateRequest, *, account: str | int | None = None
    ) -> OrderResponse:
        """Submit a live order request for the configured or overridden account.

        This method can place a real securities order. Validate the payload,
        account, market session, and all external safeguards before calling it.
        The SDK does not retry this non-idempotent endpoint automatically.

        Args:
            request: Validated order creation body.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API rejects the order or returns another
                error response.

        """
        result = await self._http.request(
            "POST",
            "/api/v1/orders",
            json=request,
            account_required=True,
            account=account,
        )
        return parse_model(OrderResponse, result)

    async def get_order(self, order_id: str, *, account: str | int | None = None) -> Order:
        """Return one order by server order identifier.

        Args:
            order_id: Server order identifier returned by order APIs.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available or ``order_id``
                is empty.
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET",
            f"/api/v1/orders/{require_non_empty('order_id', order_id)}",
            account_required=True,
            account=account,
        )
        return parse_model(Order, result)

    async def modify_order(
        self,
        order_id: str,
        request: OrderModifyRequest,
        *,
        account: str | int | None = None,
    ) -> OrderOperationResponse:
        """Modify an existing order by server order identifier.

        This method can change a real pending order. The SDK does not retry this
        non-idempotent endpoint automatically.

        Args:
            order_id: Server order identifier to modify.
            request: Validated order modification body.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available or ``order_id``
                is empty.
            TossInvestAPIError: The API rejects the modification or returns
                another error response.

        """
        result = await self._http.request(
            "POST",
            f"/api/v1/orders/{require_non_empty('order_id', order_id)}/modify",
            json=request,
            account_required=True,
            account=account,
        )
        return parse_model(OrderOperationResponse, result)

    async def cancel_order(
        self, order_id: str, *, account: str | int | None = None
    ) -> OrderOperationResponse:
        """Cancel an existing order by server order identifier.

        This method can cancel a real pending order. The SDK does not retry this
        non-idempotent endpoint automatically.

        Args:
            order_id: Server order identifier to cancel.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available or ``order_id``
                is empty.
            TossInvestAPIError: The API rejects the cancellation or returns
                another error response.

        """
        result = await self._http.request(
            "POST",
            f"/api/v1/orders/{require_non_empty('order_id', order_id)}/cancel",
            account_required=True,
            account=account,
        )
        return parse_model(OrderOperationResponse, result)

    async def get_buying_power(
        self, *, currency: CurrencyCode, account: str | int | None = None
    ) -> BuyingPowerResponse:
        """Return cash buying power for the requested currency.

        Args:
            currency: Currency code supported by the official API.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET",
            "/api/v1/buying-power",
            params={"currency": currency},
            account_required=True,
            account=account,
        )
        return parse_model(BuyingPowerResponse, result)

    async def get_sellable_quantity(
        self, *, symbol: str, account: str | int | None = None
    ) -> SellableQuantityResponse:
        """Return the sellable quantity for a symbol.

        Args:
            symbol: Stock symbol accepted by the official API.
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET",
            "/api/v1/sellable-quantity",
            params={"symbol": symbol},
            account_required=True,
            account=account,
        )
        return parse_model(SellableQuantityResponse, result)

    async def get_commissions(self, *, account: str | int | None = None) -> list[Commission]:
        """Return commission rules for the configured or overridden account.

        Args:
            account: Optional account sequence override.

        Raises:
            TossInvestValidationError: No account is available.
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request(
            "GET",
            "/api/v1/commissions",
            account_required=True,
            account=account,
        )
        return parse_model_list(Commission, result)
