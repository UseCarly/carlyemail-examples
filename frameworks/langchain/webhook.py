"""Invoke the graph when mail arrives, one graph thread per email thread.

The difference from a plain "run the agent" webhook is one line: the CarlyEmail
thread id becomes the LangGraph thread id, so a reply to a reply resumes the
same conversation instead of starting a stranger's.

    uvicorn webhook:app --port 8080

    export CARLYEMAIL_WEBHOOK_SECRET=whsec_...
    export ALLOWED_SENDERS=you@yourcompany.com
"""

from __future__ import annotations

import os
import traceback
from contextlib import asynccontextmanager

from carlyemail.inbound import create_email_router
from fastapi import FastAPI

from agent import build_agent, handle

INBOX = os.environ["CARLYEMAIL_INBOX"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Built once. Constructing it per request would re-fetch the tool schemas
    # over MCP on every email and throw away the checkpointer holding the
    # conversations — which is the one thing this example exists to show.
    app.state.agent = await build_agent()
    yield


app = FastAPI(lifespan=lifespan)


async def on_email(email) -> None:
    if not email.thread_id:
        # Nothing to key the conversation on.
        return
    try:
        answer = await handle(
            app.state.agent,
            f"A new message arrived in {INBOX} on thread {email.thread_id}, message "
            f"{email.message_id}. Read the thread and either reply or draft.",
            thread_id=email.thread_id,
        )
        print(answer)
    except Exception:  # noqa: BLE001 - one bad run must not stop the server
        traceback.print_exc()


app.include_router(create_email_router(on_email, path="/hooks/carlyemail"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
