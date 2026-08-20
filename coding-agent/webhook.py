"""Run a pass whenever mail arrives.

    uvicorn webhook:app --port 8080

`create_email_router` verifies the signature over the raw bytes, admits
`message.received` and not the spam, blocked or unauthenticated variants,
drops mail this mailbox sent itself, checks the sender against
`ALLOWED_SENDERS`, ignores redeliveries, and answers the delivery before the
agent starts — a coding task can take minutes, and a timed-out delivery is
retried into a second run.

    export CARLYEMAIL_WEBHOOK_SECRET=whsec_...
    export ALLOWED_SENDERS=you@yourcompany.com
"""

from __future__ import annotations

import asyncio

from carlyemail.inbound import create_email_router
from fastapi import FastAPI

import agent

app = FastAPI()

# One pass at a time: two deliveries in quick succession must not both start
# work on the same unhandled mail.
_lock = asyncio.Lock()


async def on_email(email) -> None:
    async with _lock:
        await agent.main()


app.include_router(create_email_router(on_email, path="/hooks/carlyemail"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
