Usage
=====

Configuration
-------------

The SDK does not read environment variables. Pass credentials explicitly when
constructing a client.

If your application uses environment variables, read them in application code
and pass those values to ``TossInvestClient`` or ``AsyncTossInvestClient``.

MCP Server
----------

The optional Model Context Protocol server exposes read-only SDK operations for
MCP hosts. Install it only when needed by using the ``mcp`` extra:

.. code-block:: bash

   uvx --from "tossinvest-openapi[mcp]" tossinvest-mcp \
     --client-id "$TOSSINVEST_API_KEY" \
     --client-secret "$TOSSINVEST_SECRET_KEY" \
     --account "$TOSSINVEST_ACCOUNT_NO"

The server does not read ``.env`` files or discover credentials automatically.
Pass credentials through your MCP host configuration as command arguments. The
default server exposes read-only tools only.
For the MCP server, ``--account`` accepts the official account number
(``accountNo``) and resolves it to ``accountSeq`` internally when an
account-scoped tool first needs the account header. The resolved value is
cached for the server process. Use ``--account-seq`` only when you already know
the sequence value. The accounts endpoint is in the ``ACCOUNT`` rate-limit
group, so ``list_accounts`` results and accountNo resolution are cached for 1
second by default, matching the documented one-request-per-second limit. Avoid
calling ``list_accounts`` just to use a configured default account.

For launchers, prefer credential helper commands so API key and secret values
are not stored in config files, environment variables, or process arguments.
Helper command lines are parsed with ``shlex`` and run without a shell. The
trimmed stdout value becomes the credential.

Register credentials in macOS Keychain:

.. code-block:: bash

   /usr/bin/security add-generic-password -U -a "$USER" -s tossinvest-api-key -w
   /usr/bin/security add-generic-password -U -a "$USER" -s tossinvest-secret-key -w

macOS Keychain example:

.. code-block:: bash

   uvx --from "tossinvest-openapi[mcp]" tossinvest-mcp \
     --client-id-command "/usr/bin/security find-generic-password -a ${USER} -s tossinvest-api-key -w" \
     --client-secret-command "/usr/bin/security find-generic-password -a ${USER} -s tossinvest-secret-key -w" \
     --account "$TOSSINVEST_ACCOUNT_NO"

Register credentials in Ubuntu ``pass``:

.. code-block:: bash

   pass insert tossinvest/api-key
   pass insert tossinvest/secret-key

Ubuntu ``pass`` example, assuming each entry contains only the credential
value:

.. code-block:: bash

   uvx --from "tossinvest-openapi[mcp]" tossinvest-mcp \
     --client-id-command "/usr/bin/pass show tossinvest/api-key" \
     --client-secret-command "/usr/bin/pass show tossinvest/secret-key" \
     --account "$TOSSINVEST_ACCOUNT_NO"

Register the server with Codex by adding a STDIO MCP server to
``~/.codex/config.toml``. Credential helper options can be passed directly in
``args``; Codex passes ``args`` as literal process arguments, so do not rely on
shell expansion inside this list.

.. code-block:: toml

   [mcp_servers.tossinvest]
   command = "uvx"
   args = [
     "--from",
     "tossinvest-openapi[mcp]",
     "tossinvest-mcp",
     "--client-id-command",
     "/usr/bin/security find-generic-password -s tossinvest-api-key -w",
     "--client-secret-command",
     "/usr/bin/security find-generic-password -s tossinvest-secret-key -w",
     "--account",
     "12345678901",
   ]
   startup_timeout_sec = 30
   tool_timeout_sec = 60
   default_tools_approval_mode = "approve"

   [mcp_servers.tossinvest.tools.create_order]
   approval_mode = "prompt"

   [mcp_servers.tossinvest.tools.modify_order]
   approval_mode = "prompt"

   [mcp_servers.tossinvest.tools.cancel_order]
   approval_mode = "prompt"

Replace the ``--account`` value with your account number (``accountNo``). If
you already know the ``accountSeq``, you can use ``--account-seq`` instead.
You can also remove the option and pass ``account_seq`` to each account-scoped
tool call. For Ubuntu ``pass``, use the helper command values shown in the
Ubuntu example above. A separate launcher is only needed if you want shell
behavior such as expanding environment variables before starting the MCP
server. In Codex, start a new session after editing the config and use
``/mcp`` to check that the server is connected.

To register live order creation, modification, and cancellation tools, pass the
separate ``--enable-live-orders`` opt-in flag:

.. code-block:: bash

   uvx --from "tossinvest-openapi[mcp]" tossinvest-mcp \
     --client-id "$TOSSINVEST_API_KEY" \
     --client-secret "$TOSSINVEST_SECRET_KEY" \
     --account "$TOSSINVEST_ACCOUNT_NO" \
     --enable-live-orders

Synchronous Client
------------------

.. code-block:: python

   import os

   from tossinvest import TossInvestClient

   with TossInvestClient(
       os.environ["TOSSINVEST_API_KEY"],
       os.environ["TOSSINVEST_SECRET_KEY"],
       account=os.getenv("TOSSINVEST_ACCOUNT"),
   ) as client:
       price = client.market_data.get_price(symbol="005930")
       print(price)

Asynchronous Client
-------------------

.. code-block:: python

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

Account-Scoped Operations
-------------------------

Account, asset, and order endpoints require the official
``X-Tossinvest-Account`` header. Configure a default account on the client or
pass ``account=...`` to an account-scoped method.

Order Safety
------------

Examples in this repository do not submit live orders by default. The order
example requires ``TOSSINVEST_ENABLE_LIVE_ORDER=true`` before it can submit a
request.
