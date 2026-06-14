"""Credential helper support for the MCP server."""

from __future__ import annotations

import shlex
import subprocess

DEFAULT_CREDENTIAL_HELPER_TIMEOUT = 5.0


class CredentialHelperError(RuntimeError):
    """Raised when a credential helper cannot return a usable credential."""


def resolve_credential(
    value: str | None,
    command_line: str | None,
    *,
    label: str,
    timeout: float = DEFAULT_CREDENTIAL_HELPER_TIMEOUT,
) -> str:
    """Resolve a credential from an explicit value or a helper command.

    Helper command lines are parsed with ``shlex`` and executed without a shell
    so credentials do not need to appear in CLI arguments, environment
    variables, or configuration files.
    """
    if value is not None:
        return value
    if command_line is None:
        raise CredentialHelperError(f"Missing TossInvest {label}.")
    return _run_credential_helper(command_line, label=label, timeout=timeout)


def _run_credential_helper(command_line: str, *, label: str, timeout: float) -> str:
    try:
        command = shlex.split(command_line)
    except ValueError as exc:
        raise CredentialHelperError(
            f"TossInvest {label} credential helper command could not be parsed."
        ) from exc

    if not command:
        raise CredentialHelperError(
            f"TossInvest {label} credential helper command must not be empty."
        )

    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CredentialHelperError(
            f"TossInvest {label} credential helper timed out after {timeout:g} seconds."
        ) from exc
    except OSError as exc:
        raise CredentialHelperError(
            f"TossInvest {label} credential helper could not be started."
        ) from exc

    if completed.returncode != 0:
        raise CredentialHelperError(
            f"TossInvest {label} credential helper failed with exit status {completed.returncode}."
        )

    credential = completed.stdout.strip()
    if not credential:
        raise CredentialHelperError(
            f"TossInvest {label} credential helper returned an empty value."
        )
    return credential
