"""Answer a question the moment it arrives, rather than on a timer.

    uvicorn webhook:app --port 8080

Research takes longer than a mailbox sweep — several searches and a page or two
before the first word is written — which makes the reply-then-work split
load-bearing rather than tidy. A delivery that waits for the model times out,
gets retried, and the sender is answered twice. `create_email_router` acks
first for exactly that reason.

    export CARLYEMAIL_WEBHOOK_SECRET=whsec_...
    export ALLOWED_SENDERS=you@yourcompany.com
"""

from __future__ import annotations

import os
import traceback

from carlyemail.inbound import create_email_router
from fastapi import FastAPI

from agent import main as run_agent

INBOX = os.environ["CARLYEMAIL_INBOX"]

app = FastAPI()


async def on_email(email) -> None:
    """Research one thread, with failures kept off the response path."""
    if not email.thread_id:
        return
    try:
        await run_agent(
            f"A new message arrived in {INBOX} on thread {email.thread_id}, message "
            f"{email.message_id}. Read the thread with `get_thread`, research the "
            f"question, and reply in that thread."
        )
    except Exception:  # noqa: BLE001 - one bad run must not stop the server
        traceback.print_exc()


app.include_router(create_email_router(on_email, path="/hooks/carlyemail"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
