"""An address your agent can sign up for things with.

Most sign-ups end the same way: "we emailed you a code". An agent with no inbox
stops there. Give it one, and the code is a function call away:

    from carlyemail import CarlyEmail
    from codes import wait_for_code

    carly = CarlyEmail()                                   # reads CARLYEMAIL_API_KEY
    inbox = carly.inboxes.create({"username": "signups"})  # signups@carlyemail.com

    # ... the agent fills in a form with inbox["email"] ...

    code = wait_for_code(carly, inbox["email"], sender="@github.com")
    print(code.value)                                      # "482913"

No model is involved. This is the part of a sign-up agent that is plain code,
and it is the part people rewrite badly: polling too fast, matching the wrong
six digits, reading a code that arrived before the form was even submitted.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from carlyemail import CarlyEmail

#: Four to eight digits on their own, which is what every site sends. Anchored
#: on word boundaries so a phone number or an order id does not pass as one.
CODE = re.compile(r"(?<![\d-])(\d{4,8})(?![\d-])")

#: Words that sit next to a real code. A message that has one of these and a
#: run of digits is a code; a message with digits alone might be an invoice.
NEARBY = re.compile(r"\b(code|verification|verify|confirm|one-time|otp|passcode|pin)\b", re.I)

#: Six-digit codes dominate, so when a message holds several candidates — an
#: order number, a year, the code — prefer the one that looks most like one.
PREFERRED_LENGTH = 6


@dataclass(frozen=True)
class Code:
    value: str
    message_id: str
    thread_id: str
    sender: str
    subject: str
    received_at: str


def extract(text: str) -> str | None:
    """The verification code in a piece of text, or None.

    Looks first in the sentence that mentions a code, then anywhere. A message
    with no code-shaped digits near a code-shaped word is not a code email, even
    if it is full of numbers.
    """
    if not text or not NEARBY.search(text):
        return None
    # Candidates in the lines that talk about a code, before candidates elsewhere.
    nearby = [m for line in text.splitlines() if NEARBY.search(line) for m in CODE.findall(line)]
    anywhere = CODE.findall(text)
    for pool in (nearby, anywhere):
        if not pool:
            continue
        sixes = [c for c in pool if len(c) == PREFERRED_LENGTH]
        return (sixes or pool)[0]
    return None


def wait_for_code(
    client: CarlyEmail,
    inbox_id: str,
    *,
    sender: str | None = None,
    after: datetime | None = None,
    timeout: float = 120.0,
    every: float = 2.0,
) -> Code:
    """Block until a code arrives, and return it.

    `sender` narrows to one address (`noreply@github.com`) or one domain
    (`@github.com`). Set it: an inbox that signs up for several things at once
    will hold several codes, and the wrong one is worse than none.

    `after` defaults to now, so a code that was already sitting in the inbox
    when you asked — from an earlier attempt, say — is not mistaken for the
    one you are waiting on.

    Polls rather than opening a webhook or a socket, because the caller is
    already blocked in the middle of a sign-up and a two-second delay is
    nothing next to the form it is filling in.
    """
    since = (after or datetime.now(UTC)).isoformat()
    deadline = time.monotonic() + timeout
    while True:
        # `list` is an index with no body — the preview is usually enough to
        # spot a code email, but the code itself is read from the full message.
        page = client.messages.list(inbox_id, labels=["received"], after=since, limit=20)
        for item in page["messages"]:
            if sender and not _from(item["from"], sender):
                continue
            full = client.messages.get(inbox_id, item["message_id"])
            text = full.get("extracted_text") or full.get("text") or ""
            value = extract(f"{full.get('subject') or ''}\n{text}")
            if value:
                return Code(
                    value=value,
                    message_id=full["message_id"],
                    thread_id=full["thread_id"],
                    sender=full["from"],
                    subject=full.get("subject") or "",
                    received_at=full.get("created_at") or full.get("timestamp") or "",
                )
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"No verification code arrived at {inbox_id} within {timeout:.0f}s"
                + (f" from {sender}" if sender else "")
            )
        time.sleep(every)


def _from(header: str, wanted: str) -> bool:
    """Whether a From header is the wanted address or domain."""
    address = header.rsplit("<", 1)[-1].rstrip(">").strip().lower()
    wanted = wanted.lower()
    if wanted.startswith("@"):
        return address.endswith(wanted)
    return address == wanted


if __name__ == "__main__":
    import os
    import sys

    carly = CarlyEmail()
    inbox = os.environ["CARLYEMAIL_INBOX"]
    sender = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"Waiting for a code at {inbox}" + (f" from {sender}" if sender else "") + " …")
    code = wait_for_code(carly, inbox, sender=sender)
    print(f"{code.value}  (from {code.sender}, subject {code.subject!r})")
