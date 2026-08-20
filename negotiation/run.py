"""A whole negotiation, start to finish, over real email.

    python run.py

The buyer opens. Then the two take turns: each waits for the other's reply to
actually arrive in its own inbox, reads the thread, and answers. It ends on an
acceptance, a walk-away, or after MAX_ROUNDS, and the buyer emails its owner a
summary. Every message is a real email; open either inbox and you can watch.
"""

from __future__ import annotations

import asyncio
import os

import buyer
import seller
from deal import dollars, find_thread, wait_for_reply

MAX_ROUNDS = int(os.environ.get("MAX_ROUNDS", "6"))


def count(side, subject) -> int:
    thread = find_thread(side, subject)
    return thread.get("message_count", len(thread["messages"])) if thread else 0


async def main() -> None:
    subject = buyer.SUBJECT
    me, them = buyer.side(), seller.side()
    if find_thread(me, subject) or find_thread(them, subject):
        raise SystemExit(f"a thread with subject {subject!r} already exists; set SUBJECT to something new")

    print(f"buyer budget {dollars(buyer.BUDGET)}, seller floor {dollars(seller.FLOOR)}")
    await buyer.party().open(them.inbox, subject)

    outcome = f"no deal after {MAX_ROUNDS} rounds"
    for round_number in range(1, MAX_ROUNDS + 1):
        # The seller's turn: wait for the buyer's mail to land, then answer.
        wait_for_reply(them, subject, count(them, subject))
        decision = await seller.party().respond(subject)
        if decision.action != "offer":
            outcome = f"seller {'accepted' if decision.action == 'accept' else 'walked away'} in round {round_number}"
            if decision.action == "accept":
                outcome += f" at {dollars(decision.price)}"
            break

        wait_for_reply(me, subject, count(me, subject))
        decision = await buyer.party().respond(subject)
        if decision.action != "offer":
            outcome = f"buyer {'accepted' if decision.action == 'accept' else 'walked away'} in round {round_number}"
            if decision.action == "accept":
                outcome += f" at {dollars(decision.price)}"
            break

    print(outcome)
    await buyer.summarise(subject, outcome)


if __name__ == "__main__":
    asyncio.run(main())
