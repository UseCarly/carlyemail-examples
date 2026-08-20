"""Run a pass whenever mail arrives, instead of on a timer.

    uvicorn webhook:app --port 8080

The desk is written as one pass over the inbox, so waking it on delivery is
the whole of this file. `create_email_router` verifies the signature over the
raw bytes, admits `message.received` and not the spam, blocked or
unauthenticated variants, drops mail this mailbox sent itself, checks the
sender, ignores redeliveries, and answers the delivery before the pass starts.

No sender allowlist here by default — a support address is meant to be
written to by strangers. Set `ALLOWED_SENDERS` anyway if the desk is internal.

    export CARLYEMAIL_WEBHOOK_SECRET=whsec_...   # printed once when you register
"""

from __future__ import annotations

import asyncio

from carlyemail.inbound import create_email_router
from fastapi import FastAPI

import agent

app = FastAPI()

# One pass at a time. Two deliveries a second apart would otherwise run two
# passes over the same unhandled mail and answer it twice.
_lock = asyncio.Lock()


async def on_email(email) -> None:
    async with _lock:
        await agent.main()


app.include_router(create_email_router(on_email, path="/hooks/carlyemail"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
