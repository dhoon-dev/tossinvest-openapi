"""Entrypoint for the optional TossInvest MCP server."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from typing import TYPE_CHECKING

from pydantic import Field

from tossinvest._mcp.config import TossInvestMCPServerConfig
from tossinvest._mcp.credentials import (
    DEFAULT_CREDENTIAL_HELPER_TIMEOUT,
    CredentialHelperError,
    resolve_credential,
)
from tossinvest._mcp.tools import ClientContextFactory, TossInvestMCPTools
from tossinvest.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
)

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

ACCOUNT_SEQ_DESCRIPTION = (
    "Optional accountSeq override. Omit when the server was started with --account or "
    "--account-seq. Use list_accounts or find_account_by_number only when no default "
    "account is configured or when selecting a different account; do not pass accountNo."
)
ACCOUNT_NO_DESCRIPTION = (
    "Official accountNo from list_accounts. Resolving accountNo calls the ACCOUNT-rate-limited "
    "accounts endpoint."
)


def create_server(
    config: TossInvestMCPServerConfig,
    *,
    client_factory: ClientContextFactory | None = None,
) -> FastMCP:
    """Create a read-only TossInvest MCP server."""
    from mcp.server.fastmcp import FastMCP

    tools = TossInvestMCPTools(
        client_factory or config.create_client,
        account_resolver=config.account_seq_for_tool,
        account_list_cache_getter=config.cached_account_list,
        account_list_observer=config.cache_account_list,
    )
    server = FastMCP("TossInvest OpenAPI")

    _register_account_tools(server, tools)
    _register_stock_tools(server, tools)
    _register_market_data_tools(server, tools)
    _register_market_info_tools(server, tools)
    _register_account_scoped_tools(server, tools)
    if config.enable_live_orders:
        _register_live_order_tools(server, tools)
    return server


def _register_account_tools(server: FastMCP, tools: TossInvestMCPTools) -> None:
    """Register account lookup tools."""

    @server.tool()
    def list_accounts() -> list[dict[str, object]]:
        """List accounts only when account discovery is needed.

        Account-scoped tools use the configured default accountSeq when account_seq is omitted.
        Use accountSeq as account_seq for overrides, not accountNo.
        """
        return tools.list_accounts()

    @server.tool()
    def find_account_by_number(
        account_no: str = Field(description=ACCOUNT_NO_DESCRIPTION),
    ) -> dict[str, object]:
        """Return the account matching accountNo, including its accountSeq."""
        return tools.find_account_by_number(account_no)


def _register_stock_tools(server: FastMCP, tools: TossInvestMCPTools) -> None:
    """Register stock information tools."""

    @server.tool()
    def get_stock(symbol: str) -> dict[str, object]:
        """Return one stock master record."""
        return tools.get_stock(symbol)

    @server.tool()
    def get_stocks(symbols: list[str]) -> list[dict[str, object]]:
        """Return stock master records for one or more symbols."""
        return tools.get_stocks(symbols)

    @server.tool()
    def get_stock_warnings(symbol: str) -> list[dict[str, object]]:
        """Return trading warnings for a symbol."""
        return tools.get_stock_warnings(symbol)


def _register_market_data_tools(server: FastMCP, tools: TossInvestMCPTools) -> None:
    """Register market data tools."""

    @server.tool()
    def get_orderbook(symbol: str) -> dict[str, object]:
        """Return the current orderbook for a symbol."""
        return tools.get_orderbook(symbol)

    @server.tool()
    def get_price(symbol: str) -> dict[str, object]:
        """Return the current price for one symbol."""
        return tools.get_price(symbol)

    @server.tool()
    def get_prices(symbols: list[str]) -> list[dict[str, object]]:
        """Return current prices for one or more symbols."""
        return tools.get_prices(symbols)

    @server.tool()
    def get_trades(symbol: str, count: int | None = None) -> list[dict[str, object]]:
        """Return recent trades for a symbol."""
        return tools.get_trades(symbol, count=count)

    @server.tool()
    def get_price_limit(symbol: str) -> dict[str, object]:
        """Return upper and lower price limits for a symbol."""
        return tools.get_price_limit(symbol)

    @server.tool()
    def get_candles(
        symbol: str,
        interval: str,
        *,
        count: int | None = None,
        before: str | None = None,
        adjusted: bool | None = None,
    ) -> dict[str, object]:
        """Return candle data for a symbol and interval."""
        return tools.get_candles(
            symbol,
            interval=interval,
            count=count,
            before=before,
            adjusted=adjusted,
        )


def _register_market_info_tools(server: FastMCP, tools: TossInvestMCPTools) -> None:
    """Register market information tools."""

    @server.tool()
    def get_exchange_rate(
        base_currency: str,
        quote_currency: str,
        date_time: str | None = None,
    ) -> dict[str, object]:
        """Return an exchange rate between two supported currencies."""
        return tools.get_exchange_rate(
            base_currency=base_currency,
            quote_currency=quote_currency,
            date_time=date_time,
        )

    @server.tool()
    def get_kr_market_calendar(date: str | None = None) -> dict[str, object]:
        """Return Korean market calendar information."""
        return tools.get_kr_market_calendar(date=date)

    @server.tool()
    def get_us_market_calendar(date: str | None = None) -> dict[str, object]:
        """Return US market calendar information."""
        return tools.get_us_market_calendar(date=date)


def _register_account_scoped_tools(server: FastMCP, tools: TossInvestMCPTools) -> None:
    """Register read-only account-scoped tools."""

    @server.tool()
    def get_holdings(
        symbol: str | None = None,
        account_seq: str | None = Field(default=None, description=ACCOUNT_SEQ_DESCRIPTION),
    ) -> dict[str, object]:
        """Return holdings using the configured default accountSeq or an account_seq override."""
        return tools.get_holdings(symbol=symbol, account_seq=account_seq)

    @server.tool()
    def list_orders(
        status: str,
        symbol: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        account_seq: str | None = Field(default=None, description=ACCOUNT_SEQ_DESCRIPTION),
    ) -> dict[str, object]:
        """List orders using the configured default accountSeq or an account_seq override."""
        return tools.list_orders(
            status=status,
            symbol=symbol,
            from_date=from_date,
            to_date=to_date,
            cursor=cursor,
            limit=limit,
            account_seq=account_seq,
        )

    @server.tool()
    def get_order(
        order_id: str,
        account_seq: str | None = Field(default=None, description=ACCOUNT_SEQ_DESCRIPTION),
    ) -> dict[str, object]:
        """Return one order using the configured default accountSeq or an account_seq override."""
        return tools.get_order(order_id, account_seq=account_seq)

    @server.tool()
    def get_buying_power(
        currency: str,
        account_seq: str | None = Field(default=None, description=ACCOUNT_SEQ_DESCRIPTION),
    ) -> dict[str, object]:
        """Return cash buying power using the configured default accountSeq or an override."""
        return tools.get_buying_power(currency=currency, account_seq=account_seq)

    @server.tool()
    def get_sellable_quantity(
        symbol: str,
        account_seq: str | None = Field(default=None, description=ACCOUNT_SEQ_DESCRIPTION),
    ) -> dict[str, object]:
        """Return sellable quantity using the configured default accountSeq or an override."""
        return tools.get_sellable_quantity(symbol=symbol, account_seq=account_seq)

    @server.tool()
    def get_commissions(
        account_seq: str | None = Field(default=None, description=ACCOUNT_SEQ_DESCRIPTION),
    ) -> list[dict[str, object]]:
        """Return commissions using the configured default accountSeq or an account_seq override."""
        return tools.get_commissions(account_seq=account_seq)


def _register_live_order_tools(server: FastMCP, tools: TossInvestMCPTools) -> None:
    """Register opt-in live order mutation tools."""

    @server.tool()
    def create_order(
        symbol: str,
        side: str,
        order_type: str,
        *,
        quantity: str | None = None,
        order_amount: str | None = None,
        price: str | None = None,
        time_in_force: str | None = None,
        client_order_id: str | None = None,
        confirm_high_value_order: bool | None = None,
        account_seq: str | None = Field(default=None, description=ACCOUNT_SEQ_DESCRIPTION),
    ) -> dict[str, object]:
        """Submit a live order using the configured default accountSeq or an override."""
        return tools.create_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            order_amount=order_amount,
            price=price,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
            confirm_high_value_order=confirm_high_value_order,
            account_seq=account_seq,
        )

    @server.tool()
    def modify_order(
        order_id: str,
        order_type: str,
        *,
        quantity: str | None = None,
        price: str | None = None,
        confirm_high_value_order: bool | None = None,
        account_seq: str | None = Field(default=None, description=ACCOUNT_SEQ_DESCRIPTION),
    ) -> dict[str, object]:
        """Modify a live order using the configured default accountSeq or an override."""
        return tools.modify_order(
            order_id,
            order_type=order_type,
            quantity=quantity,
            price=price,
            confirm_high_value_order=confirm_high_value_order,
            account_seq=account_seq,
        )

    @server.tool()
    def cancel_order(
        order_id: str,
        account_seq: str | None = Field(default=None, description=ACCOUNT_SEQ_DESCRIPTION),
    ) -> dict[str, object]:
        """Cancel a live order using the configured default accountSeq or an override."""
        return tools.cancel_order(order_id, account_seq=account_seq)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the MCP server."""
    parser = argparse.ArgumentParser(description="Run the TossInvest MCP server.")
    client_id_group = parser.add_mutually_exclusive_group(required=True)
    client_id_group.add_argument(
        "--client-id",
        help="TossInvest OpenAPI OAuth client ID.",
    )
    client_id_group.add_argument(
        "--client-id-command",
        help=(
            "Command that prints the TossInvest OpenAPI OAuth client ID to stdout. "
            "The command is parsed with shlex and is not run through a shell."
        ),
    )
    client_secret_group = parser.add_mutually_exclusive_group(required=True)
    client_secret_group.add_argument(
        "--client-secret",
        help="TossInvest OpenAPI OAuth client secret.",
    )
    client_secret_group.add_argument(
        "--client-secret-command",
        help=(
            "Command that prints the TossInvest OpenAPI OAuth client secret to stdout. "
            "The command is parsed with shlex and is not run through a shell."
        ),
    )
    parser.add_argument(
        "--credential-helper-timeout",
        default=DEFAULT_CREDENTIAL_HELPER_TIMEOUT,
        type=float,
        help="Credential helper timeout in seconds.",
    )
    account_group = parser.add_mutually_exclusive_group()
    account_group.add_argument(
        "--account",
        dest="account_number",
        help="Default TossInvest accountNo for account-scoped tools.",
    )
    account_group.add_argument(
        "--account-seq",
        help="Default TossInvest accountSeq for account-scoped tools.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="TossInvest OpenAPI base URL.",
    )
    parser.add_argument(
        "--timeout",
        default=DEFAULT_TIMEOUT,
        type=float,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--max-retries",
        default=DEFAULT_MAX_RETRIES,
        type=int,
        help="Maximum retries for idempotent HTTP requests.",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="User-Agent header for TossInvest API requests.",
    )
    parser.add_argument(
        "--enable-live-orders",
        action="store_true",
        help="Register live order creation, modification, and cancellation tools.",
    )
    return parser.parse_args(argv)


def config_from_args(args: argparse.Namespace) -> TossInvestMCPServerConfig:
    """Build MCP server configuration from parsed arguments."""
    client_id = resolve_credential(
        args.client_id,
        args.client_id_command,
        label="client ID",
        timeout=args.credential_helper_timeout,
    )
    client_secret = resolve_credential(
        args.client_secret,
        args.client_secret_command,
        label="client secret",
        timeout=args.credential_helper_timeout,
    )
    return TossInvestMCPServerConfig(
        client_id=client_id,
        client_secret=client_secret,
        account=args.account_seq,
        account_number=args.account_number,
        base_url=args.base_url,
        timeout=args.timeout,
        max_retries=args.max_retries,
        user_agent=args.user_agent,
        enable_live_orders=args.enable_live_orders,
    )


def main(argv: Sequence[str] | None = None) -> None:
    """Run the TossInvest MCP server over stdio."""
    try:
        config = config_from_args(parse_args(argv))
    except CredentialHelperError as exc:
        raise SystemExit(str(exc)) from exc
    create_server(config).run(transport="stdio")
