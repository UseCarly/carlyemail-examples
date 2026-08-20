"""Wake on a signed HTTP callback. For production.

    uvicorn webhook:app --port 8080

This needs a URL CarlyEmail can reach, which on a laptop means a tunnel. Use
`listen.py` while building — it dials out instead, so there is no public
address, no registration, and no secret. Use this one on serverless and durable
runtimes, where there is no process running to hold a socket open, and where
retries on failure matter.

Either way `reply.py` does the work. This file only decides when — and most of
that decision is `create_email_router`, which verifies the signature over the
raw bytes, admits `message.received` and not the spam, blocked or
unauthenticated variants, drops mail this mailbox sent itself, checks the
sender, ignores redeliveries, and answers the delivery before Claude starts.

    export CARLYEMAIL_API_KEY=ce_us_...
    export CARLYEMAIL_INBOX=claude@carlyemail.com
    export CARLYEMAIL_WEBHOOK_SECRET=whsec_...
    export ANTHROPIC_API_KEY=sk-ant-...
    export ALLOWED_SENDERS=you@yourcompany.com
"""

from __future__ import annotations

from carlyemail.inbound import create_email_router
from fastapi import FastAPI

from reply import INBOX, answer

app = FastAPI()


async def on_email(email) -> None:
    answer(
        email.inbox_id or INBOX,
        email.thread_id,
        email.message_id,
        email.subject or "(no subject)",
    )


app.include_router(create_email_router(on_email, path="/hooks/carlyemail"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
