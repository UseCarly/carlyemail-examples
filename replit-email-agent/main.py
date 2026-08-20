"""An email agent that wires itself up when the repl starts.

    Press Run. Mail sent to the address printed in the console gets answered.

Two things make this work on Replit specifically: the repl has a public HTTPS
URL, which is the step every other quickstart leaves to you, and it can find
that URL from its own environment — so nothing has to be pasted anywhere.
"""

from __future__ import annotations

import os
import traceback
from contextlib import asynccontextmanager

import uvicorn
from bootstrap import SetupError, setup
from carlyemail.inbound import InboundReceiver
from fastapi import FastAPI, Request, Response
from starlette.background import BackgroundTask

from agent import reply_to_thread

# Both filled in at startup. Nothing serves before they are.
CONFIG: dict[str, str] = {}
RECEIVER: InboundReceiver | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global RECEIVER
    try:
        CONFIG.update(setup())
    except SetupError as error:
        # Loud and terminal. A server that starts but never receives mail is a
        # worse thing to debug than one that refuses to start.
        print(f"\n  Setup failed: {error}\n")
        raise

    # Built here rather than at import, because the signing secret does not
    # exist until `setup()` has registered the webhook. ALLOWED_SENDERS is read
    # from the environment.
    #
    # Be clear about which half of that allowlist does the work. The `From`
    # header is written by whoever sent the mail, so on its own it stops
    # nobody. It holds because of the subscription: mail failing SPF, DKIM or
    # DMARC is emitted as `message.received.unauthenticated`, a different event
    # type, and bootstrap.py subscribes to `message.received` alone — so a
    # forged sender never reaches the handler at all. That is the unforgeable
    # half.
    RECEIVER = InboundReceiver(
        CONFIG["webhook_secret"],
        inbox=CONFIG["inbox_id"],
    )

    print("\n  Ready.")
    print(f"  Inbox:   {CONFIG['inbox_id']}")
    print(f"  Webhook: {CONFIG['webhook_url']}")
    if CONFIG["stale_webhooks_removed"] != "0":
        print(f"  Cleaned up {CONFIG['stale_webhooks_removed']} webhook(s) from a previous run.")
    print(f"\n  Send mail to {CONFIG['inbox_id']} and it will reply.\n")
    yield


app = FastAPI(lifespan=lifespan)


async def _run(thread_id: str) -> None:
    """One agent pass, failures kept off the response path."""
    try:
        await reply_to_thread(thread_id, CONFIG["inbox_id"])
        print(f"replied on thread {thread_id}")
    except Exception:  # noqa: BLE001 - one bad run must not stop the server
        traceback.print_exc()


@app.post("/webhook")
async def on_email(request: Request) -> Response:
    # `decide` verifies the signature over the raw bytes, admits
    # `message.received` and not the spam, blocked or unauthenticated variants,
    # drops mail this inbox sent itself, checks the sender, and ignores
    # redeliveries. It returns the status to send: 401 if it was never
    # CarlyEmail, 204 if there is nothing to do.
    decision = RECEIVER.decide(await request.body(), request.headers)
    if decision.email is None:
        print(f"ignored: {decision.reason}")
        return Response(status_code=decision.status)

    if not decision.email.thread_id:
        return Response(status_code=204)

    # Answer now, work after. Deliveries time out, and a model that thinks for
    # thirty seconds looks like a dead endpoint and gets retried.
    return Response(
        status_code=202,
        background=BackgroundTask(_run, decision.email.thread_id),
    )


@app.get("/")
def index() -> dict:
    return {
        "status": "ok",
        "inbox": CONFIG.get("inbox_id"),
        "webhook": CONFIG.get("webhook_url"),
    }


if __name__ == "__main__":
    # 0.0.0.0 so Replit can route to it; localhost would only be reachable from
    # inside the container.
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
