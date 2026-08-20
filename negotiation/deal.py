"""What the buyer and the seller share: the thread, the wire, and the guard.

Two agents, one email thread. Each side runs the same loop — find the thread
in its own inbox, read it, decide, reply — and differs only in which way its
limit points. The buyer may not offer more than BUDGET; the seller may not
accept less than FLOOR. Both limits are enforced here, in code, after the model
has decided. A model can be talked into anything by a sufficiently confident
email; this function cannot.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from email.utils import parseaddr
from pathlib import Path
from typing import Literal

from carlyemail import CarlyEmail
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

MODEL = os.environ.get("MODEL", "gpt-5-mini")

#: Anything that looks like a dollar amount, with or without cents.
MONEY = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{2}))?")


class Decision(BaseModel):
    """What one side wants to do next. The model fills this in; code checks it."""

    action: Literal["offer", "accept", "walk_away"] = Field(
        description=(
            "offer: propose a price. accept: take the other side's latest price "
            "as it stands. walk_away: end the negotiation without a deal."
        )
    )
    price: float | None = Field(
        default=None,
        description=(
            "For offer: the price you are proposing. For accept: the other side's "
            "latest price, exactly as they stated it. Null when walking away."
        ),
    )
    message: str = Field(
        description=(
            "The email body, plain text, written in the persona. For an offer it must "
            "state the price. Sign off with the persona's name."
        )
    )


def amounts(text: str) -> list[float]:
    return [float(f"{whole.replace(',', '')}.{cents or '00'}") for whole, cents in MONEY.findall(text or "")]


def dollars(value: float) -> str:
    return f"${value:,.0f}" if value == int(value) else f"${value:,.2f}"


def address(header: str) -> str:
    return parseaddr(header or "")[1].lower()


def body(message: dict) -> str:
    # The quoted chain stripped, so each message is what was new in it.
    return (message.get("extracted_text") or message.get("text") or "").strip()


@dataclass
class Side:
    """One party: its inbox, its client, and the limit it must not cross."""

    name: str
    inbox: str
    client: CarlyEmail
    limit: float
    #: "max" for a buyer (never above), "min" for a seller (never below).
    direction: Literal["max", "min"]

    def within(self, price: float) -> bool:
        return price <= self.limit if self.direction == "max" else price >= self.limit


# ------------------------------------------------------------------ thread


def find_thread(side: Side, subject: str) -> dict | None:
    """This side's copy of the conversation, complete with messages.

    Threads are per inbox, so each party has its own thread id for the same
    conversation. The subject is what they share.
    """
    page = side.client.threads.list(side.inbox, subject=subject, limit=5)
    for item in page["threads"]:
        return side.client.threads.get(side.inbox, item["thread_id"])
    return None


def wait_for_reply(side: Side, subject: str, seen: int, *, timeout: float = 180.0) -> dict:
    """Poll until this inbox's thread holds more than `seen` messages.

    Real mail takes a few seconds to come back round, and a webhook is how
    production finds out. A loop is fine for a script that exists to watch.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        thread = find_thread(side, subject)
        if thread and thread.get("message_count", len(thread["messages"])) > seen:
            return thread
        time.sleep(5)
    raise TimeoutError(f"no new mail in {side.inbox} after {timeout:.0f}s")


def latest_from_other(thread: dict, me: str) -> dict | None:
    others = [m for m in thread["messages"] if address(m["from"]) != me.lower()]
    return others[-1] if others else None


def transcript(thread: dict, me: str) -> str:
    lines = []
    for m in thread["messages"]:
        who = "You" if address(m["from"]) == me.lower() else m["from"]
        lines.append(f"--- {who}, {m['timestamp']} ---\n{body(m)}")
    return "\n\n".join(lines)


# ------------------------------------------------------------------- guard


class Refused(Exception):
    """A decision the guard would not send, and why."""


def check(side: Side, decision: Decision, other_said: str) -> None:
    """Refuse any decision that crosses this side's limit.

    The rule is about numbers the other party will read. An offer above a
    buyer's budget is refused whether it is in `price` or only in the prose,
    and the prose may not name a figure past the limit unless the other side
    said it first — quoting "your $18,500" back is conversation, inventing
    "$18,500" is a concession.
    """
    quoted = set(amounts(other_said))
    if decision.action == "offer":
        if decision.price is None:
            raise Refused("an offer needs a price")
        if not side.within(decision.price):
            raise Refused(f"{dollars(decision.price)} is past the limit of {dollars(side.limit)}")
        if decision.price not in amounts(decision.message):
            raise Refused(f"the message must state the offer, {dollars(decision.price)}")
        for figure in amounts(decision.message):
            if not side.within(figure) and figure not in quoted:
                raise Refused(f"the message names {dollars(figure)}, past the limit")
    elif decision.action == "accept":
        if decision.price is None or decision.price not in quoted:
            raise Refused("accept must name a price the other side actually stated")
        if not side.within(decision.price):
            raise Refused(f"accepting {dollars(decision.price)} would cross {dollars(side.limit)}")


# -------------------------------------------------------------------- wire


def send_opening(side: Side, to: str, subject: str, text: str) -> dict:
    return side.client.messages.send(side.inbox, {"to": [to], "subject": subject, "text": text})


def reply(side: Side, to_message_id: str, text: str) -> dict:
    # A reply, so the whole negotiation is one thread on both sides. A fresh
    # send with the same subject would be a second conversation.
    return side.client.messages.reply(side.inbox, to_message_id, {"text": text})
