"""Read the thread, write a reply, send it.

The thread is fetched rather than trusting the webhook payload alone: payloads
above 1 MB arrive with the body dropped, and a reply written from a subject line
is worse than a slow one.
"""

from __future__ import annotations

import os

import httpx
from anthropic import AsyncAnthropic

BASE_URL = os.environ.get("CARLYEMAIL_BASE_URL", "https://api.carlyemail.com").rstrip("/")

SYSTEM = """You are answering email on behalf of the person who set up this \
assistant. You are writing the body of a reply that will be sent as-is.

Write the reply and nothing else. No subject line, no "Here is a draft", no \
placeholders in brackets. Plain text, no markdown — this is going into an email \
client, where asterisks and backticks show up literally.

Keep it to what the message actually asked for. If you cannot answer something, \
say so plainly rather than guessing or promising a follow-up you cannot make."""


def _client(api_key: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=BASE_URL,
        headers={"authorization": f"Bearer {api_key}"},
        timeout=60.0,
    )


def _transcript(messages: list[dict], inbox_id: str) -> str:
    """Flatten the thread into something a model can read.

    Ordered oldest first, and each turn labelled by who sent it, so the model
    can tell its own previous replies from the correspondent's.
    """
    lines = []
    for message in messages:
        sender = (message.get("from") or "").strip()
        who = "You" if inbox_id.lower() in sender.lower() else sender or "Unknown sender"
        body = message.get("extracted_text") or message.get("text") or "(no text)"
        lines.append(f"--- From: {who}\n{body.strip()}")
    return "\n\n".join(lines)


async def reply_to_thread(thread_id: str, inbox_id: str) -> str:
    """One pass over one thread. Returns the reply that was sent."""
    carly_key = os.environ["CARLYEMAIL_API_KEY"]
    inbox_path = f"/v0/inboxes/{inbox_id}"

    async with _client(carly_key) as carly:
        response = await carly.get(f"{inbox_path}/threads/{thread_id}")
        response.raise_for_status()
        thread = response.json()

        messages = thread.get("messages") or []
        anchor = thread.get("last_message_id")
        if not anchor:
            raise RuntimeError(f"thread {thread_id} has no message to reply to")

        subject = thread.get("subject") or "(no subject)"
        prompt = (
            f"Subject: {subject}\n\n"
            f"{_transcript(messages, inbox_id)}\n\n"
            "Write the reply to the most recent message."
        )

        anthropic = AsyncAnthropic()
        # Streaming so a long reply cannot trip the SDK's non-streaming timeout;
        # nothing here consumes tokens as they arrive, so take the final message.
        async with anthropic.messages.stream(
            model="claude-opus-5",
            max_tokens=16000,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            message = await stream.get_final_message()

        if message.stop_reason == "refusal":
            raise RuntimeError(f"model declined to answer thread {thread_id}")

        text = "".join(block.text for block in message.content if block.type == "text").strip()
        if not text:
            raise RuntimeError(f"model returned no text for thread {thread_id}")

        sent = await carly.post(f"{inbox_path}/messages/{anchor}/reply", json={"text": text})
        sent.raise_for_status()

    return text
