# tossinvest-openapi

Unofficial Python SDK for Toss Securities Open API.

This project is not affiliated with, endorsed by, or maintained by Toss Securities. Verify all behavior against the
official API documentation before using this SDK in production.

Trading safety: this API can place real securities orders. Mistakes can cause financial loss. Test thoroughly with
small, controlled requests and review every order payload before enabling live order submission.

## Installation

```bash
uv add tossinvest-openapi
pip install tossinvest-openapi
```

## Configuration

The SDK does not read environment variables. Pass credentials explicitly when
constructing a client.

If your application uses environment variables, read them in your application code and pass the
values to `TossInvestClient` or `AsyncTossInvestClient`.

## MCP Server

The optional Model Context Protocol server exposes read-only SDK operations for
MCP hosts. It is not installed with the base SDK dependencies.

Run it with `uvx --from`:

```bash
uvx --from "tossinvest-openapi[mcp]" tossinvest-mcp \
  --client-id "$TOSSINVEST_API_KEY" \
  --client-secret "$TOSSINVEST_SECRET_KEY" \
  --account "$TOSSINVEST_ACCOUNT"
```

The server does not read `.env` files or discover credentials automatically.
Pass credentials through your MCP host configuration as command arguments. The
default server exposes read-only tools only.

For launchers, prefer credential helper commands so API key and secret values
are not stored in config files, environment variables, or process arguments.
Helper command lines are parsed with `shlex` and run without a shell. The
trimmed stdout value becomes the credential.

Register credentials in macOS Keychain:

```bash
/usr/bin/security add-generic-password -U -a "$USER" -s tossinvest-api-key -w
/usr/bin/security add-generic-password -U -a "$USER" -s tossinvest-secret-key -w
```

macOS Keychain example:

```bash
uvx --from "tossinvest-openapi[mcp]" tossinvest-mcp \
  --client-id-command "/usr/bin/security find-generic-password -a ${USER} -s tossinvest-api-key -w" \
  --client-secret-command "/usr/bin/security find-generic-password -a ${USER} -s tossinvest-secret-key -w" \
  --account "$TOSSINVEST_ACCOUNT"
```

Register credentials in Ubuntu `pass`:

```bash
pass insert tossinvest/api-key
pass insert tossinvest/secret-key
```

Ubuntu `pass` example, assuming each entry contains only the credential value:

```bash
uvx --from "tossinvest-openapi[mcp]" tossinvest-mcp \
  --client-id-command "/usr/bin/pass show tossinvest/api-key" \
  --client-secret-command "/usr/bin/pass show tossinvest/secret-key" \
  --account "$TOSSINVEST_ACCOUNT"
```

To register live order creation, modification, and cancellation tools, pass the
separate `--enable-live-orders` opt-in flag:

```bash
uvx --from "tossinvest-openapi[mcp]" tossinvest-mcp \
  --client-id "$TOSSINVEST_API_KEY" \
  --client-secret "$TOSSINVEST_SECRET_KEY" \
  --account "$TOSSINVEST_ACCOUNT" \
  --enable-live-orders
```

Example MCP configuration:

```json
{
  "command": "uvx",
  "args": [
    "--from",
    "tossinvest-openapi[mcp]",
    "tossinvest-mcp",
    "--client-id",
    "your-client-id",
    "--client-secret",
    "your-client-secret",
    "--account",
    "1"
  ]
}
```

## Sync Quickstart

```python
import os

from tossinvest import TossInvestClient

with TossInvestClient(
    os.environ["TOSSINVEST_API_KEY"],
    os.environ["TOSSINVEST_SECRET_KEY"],
    account=os.getenv("TOSSINVEST_ACCOUNT"),
) as client:
    price = client.market_data.get_price(symbol="005930")
    print(price)
```

## Async Quickstart

```python
import asyncio
import os

from tossinvest import AsyncTossInvestClient


async def main() -> None:
    async with AsyncTossInvestClient(
        os.environ["TOSSINVEST_API_KEY"],
        os.environ["TOSSINVEST_SECRET_KEY"],
        account=os.getenv("TOSSINVEST_ACCOUNT"),
    ) as client:
        price = await client.market_data.get_price(symbol="005930")
        print(price)


asyncio.run(main())
```

## Market Data

```python
import os

from tossinvest import TossInvestClient

with TossInvestClient(
    os.environ["TOSSINVEST_API_KEY"],
    os.environ["TOSSINVEST_SECRET_KEY"],
) as client:
    prices = client.market_data.get_prices(["005930", "000660"])
    candles = client.market_data.get_candles("005930", interval="1d", count=20)
```

The official OpenAPI spec defines market data lookup by `symbol` or `symbols`. It does not define a separate `market`
query parameter for price lookup.

## Accounts and Assets

```python
import os

from tossinvest import TossInvestClient

with TossInvestClient(
    os.environ["TOSSINVEST_API_KEY"],
    os.environ["TOSSINVEST_SECRET_KEY"],
    account=os.environ["TOSSINVEST_ACCOUNT"],
) as client:
    accounts = client.accounts.list_accounts()
    holdings = client.assets.get_holdings()
```

Account, asset, and order-related operations require the official `X-Tossinvest-Account` header. Pass `account=...`
when constructing the client or per method call.

## Dry-Run Order Example

```python
import os

from tossinvest import OrderCreateRequest, TossInvestClient

request = OrderCreateRequest(
    clientOrderId="example-dry-run-001",
    symbol="005930",
    side="BUY",
    orderType="LIMIT",
    quantity="1",
    price="70000",
)

print(request.model_dump(by_alias=True, exclude_none=True))

# Submit only after your own review and external safeguards.
# with TossInvestClient(
#     os.environ["TOSSINVEST_API_KEY"],
#     os.environ["TOSSINVEST_SECRET_KEY"],
#     account=os.environ["TOSSINVEST_ACCOUNT"],
# ) as client:
#     response = client.orders.create_order(request)
```

The included `examples/place_order_dry_run.py` exits before submitting unless
`TOSSINVEST_ENABLE_LIVE_ORDER=true` is set.

## Error Handling

```python
import os

from tossinvest import TossInvestAPIError, TossInvestClient, TossInvestRateLimitError

try:
    with TossInvestClient(
        os.environ["TOSSINVEST_API_KEY"],
        os.environ["TOSSINVEST_SECRET_KEY"],
        account=os.environ["TOSSINVEST_ACCOUNT"],
    ) as client:
        client.orders.get_buying_power(currency="KRW")
except TossInvestRateLimitError as exc:
    print(f"Rate limited. Retry after: {exc.retry_after}")
except TossInvestAPIError as exc:
    print(f"API error: status={exc.status_code} code={exc.api_code} request_id={exc.request_id}")
```

Exception strings are sanitized and do not include credentials, authorization headers, or client secrets. Raw API error
metadata is available on exception attributes such as `status_code`, `response_body`, `request_id`, `trace_id`,
`retry_after`, `endpoint`, and `api_code`.

## Public API

- `TossInvestClient`
- `AsyncTossInvestClient`
- `TossInvestConfig`
- `OAuth2TokenProvider`
- `client.market_data`
- `client.stocks`
- `client.market_info`
- `client.accounts`
- `client.assets`
- `client.orders`

## Updating the OpenAPI Spec

The raw OpenAPI JSON is ignored by git because it contains upstream documentation text. Fetch it locally when needed:

```bash
uv run python scripts/fetch_openapi.py
uv run python scripts/inspect_openapi.py
```

The SDK implementation should follow the official OpenAPI JSON when documentation sources disagree.

## Development

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest
uv run --group docs sphinx-build -b html docs docs/_build/html
uv build
```

Normal unit tests use mocked HTTP and do not require network access.

Read-only live tests are opt-in and may load local credentials from `.env`.
The SDK itself does not read `.env`; only the live test helper does.

```bash
cp .env.example .env
# Edit .env with TOSSINVEST_API_KEY and TOSSINVEST_SECRET_KEY.
uv run pytest -m live
```

Live tests run only when `TOSSINVEST_ENABLE_LIVE_TESTS=true` is set in `.env`
or the shell environment. Account-scoped live tests call `/api/v1/accounts` and
use the first returned `accountSeq` by default. Set optional `TOSSINVEST_ACCOUNT`
only when you want to force a specific account sequence. It is not an email
address. Live order tests must require the separate
`TOSSINVEST_ENABLE_LIVE_ORDER=true` flag.

## Continuous Integration

The GitHub Actions workflow in `.github/workflows/ci.yml` runs formatting, linting,
type checking, mocked unit tests, documentation builds, and package builds on
pushes and pull requests.

Read-only live tests run on pushes to `main` and on manual `workflow_dispatch`
runs. Configure these repository secrets before enabling live CI:

- `TOSSINVEST_API_KEY`
- `TOSSINVEST_SECRET_KEY`

Optional repository settings:

- `TOSSINVEST_ACCOUNT` as a repository secret, when you want to force a specific
  account sequence.
- `TOSSINVEST_BASE_URL`, `TOSSINVEST_LIVE_SYMBOL`, and
  `TOSSINVEST_LIVE_CURRENCY` as repository variables, when the defaults should
  be overridden.

Local workflow checks can be run with `act`:

```bash
act push -j quality -W .github/workflows/ci.yml
act workflow_dispatch -j live -W .github/workflows/ci.yml --secret-file .env
```
