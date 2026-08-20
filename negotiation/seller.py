"""The seller. Has a floor, and the same guard pointing the other way.

    python seller.py         # one pass: read the thread, reply once

Ship this so the example runs on its own; in real life the seller is a person,
and the buyer negotiates with them exactly the same way.
"""

from __future__ import annotations

import asyncio
import os

from carlyemail import CarlyEmail

from deal import Side
from party import Party

API_KEY = os.environ.get("SELLER_API_KEY") or os.environ["CARLYEMAIL_API_KEY"]
INBOX = os.environ["SELLER_INBOX"]
FLOOR = float(os.environ.get("FLOOR", "15500"))
SUBJECT = os.environ.get("SUBJECT", "Your Probat P12 listing")

PERSONA = """
You are Marcus Bell of Bell Roasting Equipment in Sacramento. You are selling
a 2019 Probat P12 roaster, single owner, serviced last spring, listed at
$18,500. You have sold a lot of used equipment, you are friendly, and you do
not drop your price without a reason.
""".strip()

STRATEGY = """
Negotiating:
- Hold near the asking price at first and justify it: the service history,
  the drum, what a new one costs.
- Come down in small steps, and only in exchange for something — quick
  collection, payment on collection, no demands on the buyer's freight.
- Never state or hint at your floor.
- Accept when the buyer's number is one you would be glad to take. Walk away
  if they stop moving.
""".strip()


def side() -> Side:
    return Side("Marcus Bell", INBOX, CarlyEmail(api_key=API_KEY), FLOOR, "min")


def party() -> Party:
    return Party(side(), PERSONA, STRATEGY)


async def main(subject: str = SUBJECT):
    return await party().respond(subject)


if __name__ == "__main__":
    asyncio.run(main())
