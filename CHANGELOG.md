# Changelog

## 1.0.1

- Fixed MCP account lookup caching to avoid duplicate `list_accounts` calls
  within the TossInvest `ACCOUNT` rate-limit window.
- Updated retry handling to honor TossInvest rate-limit retry headers.

## 0.1.0

- Initial unofficial SDK scaffold for Toss Securities Open API.
- Added synchronous and asynchronous clients.
- Added OAuth 2.0 client-credentials token handling with in-memory caching.
- Added market data, stock, market info, account, asset, and order resources.
- Added network-free unit tests and safe examples.
