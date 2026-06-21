# AGENTS.md

## Project Scope

This repository is an unofficial Python SDK for the Toss Securities Open API.
Keep the public API explicit, typed, and conservative. Prefer small, direct
resource methods that mirror the official OpenAPI operation shape over clever
abstractions.

Generated source, documentation, comments, test names, and commit-facing text in
this repository must be written in English unless a user explicitly asks for a
translation.

## Sources of Truth

- Follow the official TossInvest OpenAPI JSON and official developer
  documentation when modeling endpoints, headers, request bodies, and response
  schemas.
- If local docs, examples, and official upstream docs disagree, verify against
  the OpenAPI JSON before changing SDK behavior.
- Account-scoped APIs require the official `X-Tossinvest-Account` header. The
  value is `accountSeq` from `/api/v1/accounts`; it is not an email address.
- Treat order APIs as real trading APIs. Do not add live order tests or examples
  that submit orders unless they are behind a separate explicit opt-in flag.

## Dependency and Tooling Rules

- This project targets Python 3.12+.
- Use `uv` for project commands. Prefer locked commands in CI-like validation:
  `uv sync --locked --all-extras --group docs`.
- Before changing behavior that depends on third-party packages, GitHub Actions,
  Sphinx, pytest, Ruff, ty, uv, httpx, Pydantic, or other external tools,
  consult current documentation first.
- Keep GitHub Actions on `astral-sh/setup-uv` unless there is a concrete
  incompatibility with hosted GitHub runners.

## Quality Gate

Run the focused command for the change first. Before handing off broad changes,
run the full local gate:

```bash
uv sync --locked --all-extras --group docs
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked ty check
uv run --locked pytest -m "not live"
uv run --locked --group docs sphinx-build -W -b html docs docs/_build/html
uv build
```

Ruff is configured with `select = ["ALL"]`. Do not remove ignores casually; each
global or per-file ignore in `pyproject.toml` must keep a short justification
comment.

## Credentials and Live Tests

- The SDK must not read environment variables or `.env` files. Credentials are
  passed explicitly to `TossInvestClient` and `AsyncTossInvestClient`.
- The live test helper may read `.env` for local developer convenience.
- Never commit `.env` or real credentials. Keep `.env.example` credential values
  empty.
- Read-only live tests require:
  - `TOSSINVEST_ENABLE_LIVE_TESTS=true`
  - `TOSSINVEST_API_KEY`
  - `TOSSINVEST_SECRET_KEY`
- Optional live-test settings:
  - `TOSSINVEST_ACCOUNT`
  - `TOSSINVEST_BASE_URL`
  - `TOSSINVEST_LIVE_SYMBOL`
  - `TOSSINVEST_LIVE_CURRENCY`
- `TOSSINVEST_ACCOUNT` is optional. If it is not provided, live tests should use
  the first account returned by `/api/v1/accounts`.

## CI and act

The GitHub Actions workflow is `.github/workflows/ci.yml`.

- `quality` runs formatting, linting, type checking, non-live tests, Sphinx docs,
  and package build on `main`, pull requests, manual runs, and `v*` tag pushes.
- Tag pushes validate that the `v`-prefixed tag version matches
  `pyproject.toml`, `uv.lock`, `src/tossinvest/_version.py`, and
  `docs/conf.py`.
- `.github/workflows/release.yml` is manually dispatched by maintainers after a
  tag passes validation. It checks out the tag, reruns the quality gate, builds
  the package, archives Sphinx HTML docs, creates the GitHub Release, and deploys
  non-draft, non-prerelease docs to GitHub Pages as the latest documentation.
- `live` depends on `quality` but is disabled in CI because it currently fails
  on GitHub-hosted runners. It is skipped for pushes, pull requests, and manual
  `workflow_dispatch` runs.
- GitHub repository secrets required before re-enabling live CI:
  - `TOSSINVEST_API_KEY`
  - `TOSSINVEST_SECRET_KEY`
- Optional live CI values should be repository variables unless they are
  sensitive.

Local `act` validation on Apple Silicon/Docker Desktop should use arm64:

```bash
act push -j quality -W .github/workflows/ci.yml --container-architecture linux/arm64
```

The `linux/amd64` act image may fail in `astral-sh/setup-uv` post-steps because
the Node executable is not found in that local image PATH. Hosted GitHub runners
are still expected to use their normal x64 environment.

## Documentation

- Sphinx/autodoc is the documentation generator.
- Keep public classes, functions, resources, exceptions, and Pydantic models
  documented with useful docstrings.
- Build docs with warnings as errors before completing docstring or public API
  changes:

```bash
uv run --locked --group docs sphinx-build -W -b html docs docs/_build/html
```

## Commit Messages

- Use Conventional Commits-style titles:
  - `feat: add live account discovery`
  - `fix: preserve default live API base URL`
  - `chore: update CI workflow`
- Write a title, then one blank line, then a body:

```text
fix: preserve default live API base URL

Ensure empty optional CI variables do not override the SDK default base URL
during live tests.
```

- Use these default types:
  - `feat` for user-visible SDK features or supported API additions.
  - `fix` for bug fixes, schema corrections, and behavioral regressions.
  - `chore` for tooling, CI, dependency, repository, or maintenance changes.
  - `docs` for documentation-only changes.
  - `test` for test-only changes.
  - `refactor` for internal code changes that do not alter behavior.
  - `ci` for GitHub Actions and CI configuration changes.
- Keep the title in English, concise, specific, and no longer than 50
  characters.
- Wrap body lines at 72 characters or fewer. Use the body to explain the
  reason, impact, or notable verification for the change.
- Validate commit messages with:

```bash
uv run --locked python scripts/check_commit_messages.py --message-file <path>
```

- Local checkouts should enable the shared commit hook with:

```bash
git config core.hooksPath .githooks
```

## Implementation Guidelines

- Keep sync and async clients behaviorally aligned.
- Keep exception messages sanitized; do not include credentials, authorization
  headers, or client secrets.
- Prefer Pydantic v2 model aliases over manual key conversion.
- Preserve explicit account override behavior: a client-level account can be
  overridden per method when the API supports account-scoped calls.
- Unit tests should use mocked HTTP and must not require network access.
- Live tests should be read-only by default and should not place, amend, or
  cancel real orders.
