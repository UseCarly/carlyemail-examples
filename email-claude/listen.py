"""The same thing as webhook.py, without needing a public address.

    python listen.py

A webhook is CarlyEmail calling you, so you need a URL it can reach — which on
a laptop means a tunnel, a registered endpoint, and a signing secret to verify
that callers really are us. A WebSocket is you calling CarlyEmail. Nothing has
to reach your machine, so none of that exists: no tunnel, no registration, no
secret, and no signature check, because you opened the connection.

Use this while building, and on anything already running as a long-lived
process. Use `webhook.py` in production on serverless or durable runtimes,
where there is nothing running to hold a socket open and retries matter.

    export CARLYEMAIL_API_KEY=ce_us_...
    export CARLYEMAIL_INBOX=claude@carlyemail.com
    export ANTHROPIC_API_KEY=sk-ant-...
    export ALLOWED_SENDERS=you@yourcompany.com
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import random
from urllib.parse import quote

import websockets

from reply import ALLOWED_SENDERS, INBOX, _allowed, answer

API_KEY = os.environ["CARLYEMAIL_API_KEY"]

# Never logged, and never printed on the way to an error message: the key is in
# the query string, because a browser WebSocket handshake cannot set a header.
URL = f"wss://ws.carlyemail.com/v0?api_key={quote(API_KEY)}"

MAX_BACKOFF = 30.0


async def _handle(frame: dict, seen: set[str]) -> None:
    if frame.get("type") != "event" or frame.get("event_type") != "message.received":
        return

    # At least once, so the same event can arrive twice — on a reconnect that
    # replays, or a redelivery. Answering twice sends two emails.
    event_id = frame.get("event_id")
    if event_id in seen:
        return
    if event_id:
        seen.add(event_id)

    message = frame.get("message") or {}
    sender = message.get("from") or ""

    if sender.lower() == INBOX:
        return  # our own reply, or the mailbox answers itself forever
    if not _allowed(sender):
        print(f"ignoring mail from {sender!r}")
        return

    # Off the read loop. Awaiting the model here stops us reading frames for as
    # long as it thinks, and the socket's keepalives go unanswered.
    asyncio.create_task(
        asyncio.to_thread(
            answer,
            message.get("inbox_id", INBOX),
            message.get("thread_id", ""),
            message.get("message_id", ""),
            message.get("subject") or "(no subject)",
        )
    )


async def main() -> None:
    if not ALLOWED_SENDERS:
        print("! ALLOWED_SENDERS is empty — anyone who learns the address can write to it")
    print(f"listening on {INBOX}")

    seen: set[str] = set()
    backoff = 0.25

    while True:
        try:
            async with websockets.connect(URL) as socket:
                await socket.send(
                    json.dumps(
                        {
                            "type": "subscribe",
                            "event_types": ["message.received"],
                            "inbox_ids": [INBOX],
                        }
                    )
                )
                # Reset only after a connection that worked. Resetting on the
                # attempt turns a server rejecting every connect into a tight
                # reconnect loop rather than a backoff.
                backoff = 0.25

                async for raw in socket:
                    frame = json.loads(raw)
                    if frame.get("type") == "subscribed":
                        print(f"subscribed to {frame.get('event_types')}")
                        continue
                    await _handle(frame, seen)
        except (OSError, websockets.WebSocketException) as error:
            # The URL carries the key, and some libraries put it in the
            # exception text. Print the class, never the message.
            print(f"disconnected ({type(error).__name__}), retrying in {backoff:.1f}s")

        await asyncio.sleep(backoff + random.random() * backoff)
        backoff = min(backoff * 2, MAX_BACKOFF)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
