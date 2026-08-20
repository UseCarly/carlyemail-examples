"""Wake the agent when mail actually arrives.

Polling is fine while you are building and wrong once you ship: it is a fixed
cost that mostly finds nothing, and it adds latency proportional to how much you
tried to save. A webhook is the same work, done when there is work.

    uvicorn webhook:app --port 8080

CarlyEmail signs every delivery, and that signature is the only reason to
believe a request came from us. Anyone can POST to a public URL.
`create_email_router` checks it, along with the five other things that have to
be true before an agent should run — see the note on ALLOWED_SENDERS below.

    export CARLYEMAIL_WEBHOOK_SECRET=whsec_...
    export ALLOWED_SENDERS=you@yourcompany.com
"""

from __future__ import annotations

import traceback

from carlyemail.inbound import create_email_router
from fastapi import FastAPI

from agent import main as run_agent

app = FastAPI()


async def on_email(email) -> None:
    """One agent pass over one thread, failures kept off the response path.

    The thread, not the mailbox. Sweeping the inbox here would undo the sender
    check — a sweep reads and answers everything waiting, whoever sent it.
    """
    if not email.thread_id:
        return
    try:
        await run_agent(email.thread_id)
    except Exception:  # noqa: BLE001 - one bad run must not stop the server
        traceback.print_exc()


# ALLOWED_SENDERS is read from the environment. Be clear about which half of it
# does the work: the `From` header is written by whoever sent the mail, so on
# its own the check stops nobody. It holds because of the subscription — mail
# failing SPF, DKIM or DMARC is emitted as `message.received.unauthenticated`,
# a different event type the router does not admit, so a forged sender never
# reaches this handler at all. That is the unforgeable half. This is the "and
# it is from me" half.
app.include_router(create_email_router(on_email, path="/hooks/carlyemail"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
