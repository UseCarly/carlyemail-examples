"""The buyer. Wants the roaster, has a budget, and will not say what it is.

    python buyer.py          # one pass: read the thread, reply once

`run.py` drives a whole negotiation against `seller.py`; `webhook.py` runs this
pass each time the seller's reply arrives. Either way the budget lives in
`deal.check`, not in the prompt.
"""

from __future__ import annotations

import asyncio
import os

from agents import Agent, Runner
from carlyemail import CarlyEmail

from deal import MODEL, Side, dollars, find_thread, transcript
from party import Party

API_KEY = os.environ["CARLYEMAIL_API_KEY"]
INBOX = os.environ.get("BUYER_INBOX", os.environ.get("CARLYEMAIL_INBOX", ""))
SELLER = os.environ["SELLER_EMAIL"]
OWNER = os.environ["OWNER_EMAIL"]
BUDGET = float(os.environ.get("BUDGET", "16000"))
SUBJECT = os.environ.get("SUBJECT", "Your Probat P12 listing")

PERSONA = """
You are Priya Natarajan, operations lead at Hollow Oak Coffee Roasters in
Portland. You are buying a used 2019 Probat P12 roaster that Bell Roasting
Equipment has listed at $18,500. You have roasted on a P12 before, you know
the market, and you are polite, brief and direct.
""".strip()

STRATEGY = """
Negotiating:
- Open low but credibly — around three quarters of the asking price — with a
  reason (comparable sales, the freight you are paying, the age of the drum).
- Concede in shrinking steps. Never repeat an offer the seller has already
  declined, and never jump to your limit.
- Never state or hint at your limit. Everything you can spend is a number you
  have not said yet.
- Accept when the seller's price is one you would be pleased with; walk away
  if they will not move or start to insist on terms you cannot meet.
""".strip()

OPENING = f"""
Write to the seller about the listing, subject "{SUBJECT}". Mention you can
collect within two weeks and pay on collection, and make an opening offer.
""".strip()


def side() -> Side:
    return Side("Priya Natarajan", INBOX, CarlyEmail(api_key=API_KEY), BUDGET, "max")


def party() -> Party:
    return Party(side(), PERSONA, STRATEGY, OPENING)


async def main(subject: str = SUBJECT):
    """One pass: read what the seller said, reply once."""
    return await party().respond(subject)


async def summarise(subject: str = SUBJECT, outcome: str = "") -> None:
    """One paragraph to the owner: what was asked, what was offered, where it ended."""
    me = side()
    thread = find_thread(me, subject)
    writer = Agent(
        name="Summary",
        instructions=(
            f"{PERSONA}\n\nWrite one paragraph of plain text to your manager summarising "
            "a negotiation: the listing, how the offers moved on both sides, and how it "
            "ended. State the final price if there was a deal. No preamble, no subject."
        ),
        model=MODEL,
    )
    result = await Runner.run(
        writer,
        f"Outcome: {outcome or 'see transcript'}. Budget was {dollars(BUDGET)}.\n\n"
        f"Transcript:\n\n{transcript(thread, me.inbox)}",
    )
    me.client.messages.send(
        me.inbox,
        {"to": [OWNER], "subject": f"Summary: {subject}", "text": result.final_output},
    )
    print(f"[Priya Natarajan] summary sent to {OWNER}")


if __name__ == "__main__":
    asyncio.run(main())
