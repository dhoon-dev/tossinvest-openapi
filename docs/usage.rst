Usage
=====

Configuration
-------------

The SDK does not read environment variables. Pass credentials explicitly when
constructing a client.

If your application uses environment variables, read them in application code
and pass those values to ``TossInvestClient`` or ``AsyncTossInvestClient``.

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
