"""Wake the buyer when the seller's reply actually arrives.

    uvicorn webhook:app --port 8080

`create_email_router` is the whole receiving half: it verifies the signature
over the raw bytes, admits `message.received` and not the spam, blocked or
unauthenticated variants, drops mail this inbox sent itself, checks the sender
against ALLOWED_SENDERS, ignores redeliveries, and answers the delivery before
the agent starts. Set ALLOWED_SENDERS to the seller, so nobody else can open
a negotiation with your buyer.

    export CARLYEMAIL_WEBHOOK_SECRET=whsec_...
    export ALLOWED_SENDERS=marcus@bellroasting.com
"""

from __future__ import annotations

import traceback

from carlyemail.inbound import create_email_router
from fastapi import FastAPI

from buyer import main as run_buyer

app = FastAPI()


async def on_email(email) -> None:
    """One buyer pass on the thread that just got a reply."""
    try:
        await run_buyer(email.subject.removeprefix("Re: ").strip() or None)
    except Exception:  # noqa: BLE001 - one bad run must not stop the server
        traceback.print_exc()


app.include_router(create_email_router(on_email, path="/hooks/carlyemail"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
