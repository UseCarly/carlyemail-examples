"""Wake the agent when mail actually arrives.

Polling is fine while you are building and wrong once you ship: it is a fixed
cost that mostly finds nothing, and it adds latency proportional to how much you
tried to save. A webhook is the same work, done when there is work.

    uvicorn webhook:app --port 8080

`create_email_router` is the whole receiving half. It verifies the signature
over the raw bytes, admits `message.received` and not the spam, blocked or
unauthenticated variants, drops mail this inbox sent itself, checks the sender
against ALLOWED_SENDERS, ignores redeliveries, and answers the delivery before
the agent starts — a model that thinks for twenty seconds looks like a dead
endpoint, gets retried, and runs the agent twice on one message.

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
    """One agent pass, with failures kept off the response path."""
    try:
        await run_agent()
    except Exception:  # noqa: BLE001 - one bad run must not stop the server
        traceback.print_exc()


app.include_router(create_email_router(on_email, path="/hooks/carlyemail"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
