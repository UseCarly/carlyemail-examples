"""Email arrives, an agent runs in Anthropic's cloud, the answer comes back.

    uvicorn webhook:app --port 8080

This file is the whole integration, and it is worth being precise about who runs
what. Three parties:

    CarlyEmail   receives the mail and delivers a signed event. Nothing else.
    Anthropic    runs the agent loop and hosts the sandbox it works in.
    You          run these seventy lines, and hold both keys.

Neither vendor holds the other's credential. The CarlyEmail key stays in this
process and is used here, after the agent has finished — it is never handed to
the sandbox, so nothing the agent does with untrusted input can reach for it.

The agent half is `claude-opus-5` on Managed Agents, billed to your Anthropic
account. Swapping it for a LangChain agent on your own box, or the Claude Agent
SDK, changes only `run_agent` below — the email half is identical, which is the
point of the other examples in this directory.
"""

from __future__ import annotations

import os
import traceback

import anthropic
from carlyemail import CarlyEmail
from carlyemail.inbound import create_email_router
from fastapi import FastAPI

INBOX = os.environ["CARLYEMAIL_INBOX"]
AGENT_ID = os.environ["ANTHROPIC_AGENT_ID"]
ENVIRONMENT_ID = os.environ["ANTHROPIC_ENVIRONMENT_ID"]

# Who is allowed to give this agent work is ALLOWED_SENDERS, read from the
# environment by the router. An address that reaches a shell is a public
# endpoint unless something says otherwise, and this is that something.
#
# Note what this check is and is not. It reads the `From` header, which anyone
# can write — on its own it stops nobody. It holds because of what CarlyEmail
# has already done: mail failing SPF/DKIM/DMARC is emitted as
# `message.received.unauthenticated`, a different event type the router does
# not admit, so a forged message never arrives here at all. The unforgeable
# half is that filter; this is the "and it's from me" half.

anthropic_client = anthropic.Anthropic()
carly = CarlyEmail(api_key=os.environ["CARLYEMAIL_API_KEY"])

app = FastAPI()


def _done(event) -> bool:
    """Whether this event means the agent has stopped for good.

    Idle is not the same as finished. A session idles between parallel tool
    calls and whenever it is blocked on something only this process can answer,
    so breaking on the bare status abandons a session that was waiting for us.
    """
    if event.type == "session.status_terminated":
        return True
    return event.type == "session.status_idle" and event.stop_reason.type != "requires_action"


def run_agent(task: str) -> str:
    """One session in Anthropic's sandbox. Returns what the agent wrote."""
    session = anthropic_client.beta.sessions.create(
        agent=AGENT_ID,
        environment_id=ENVIRONMENT_ID,
        # Passing the task here starts the loop in the same call — the session
        # is created directly in `running` and never passes through `idle`, so
        # do not wait for an idle-to-running transition that will not come.
        initial_events=[{"type": "user.message", "content": [{"type": "text", "text": task}]}],
    )
    print(f"https://platform.claude.com/workspaces/default/sessions/{session.id}")

    said: list[str] = []
    with anthropic_client.beta.sessions.events.stream(session_id=session.id) as stream:
        for event in stream:
            if event.type == "agent.message":
                said += [b.text for b in event.content if b.type == "text"]
            elif _done(event):
                break

    return "\n\n".join(said).strip()


def on_email(email) -> None:
    # `email.text` is `extracted_text` where there is one, so the quoted chain
    # is stripped and a reply carries the new message rather than the whole
    # history again.
    if not email.text.strip():
        return
    try:
        answer = run_agent(
            f"This arrived in {INBOX}.\n\n"
            f"Subject: {email.subject or '(no subject)'}\n\n{email.text}"
        )
        if answer:
            carly.messages.reply(email.inbox_id or INBOX, email.message_id, {"text": answer})
    except Exception:  # noqa: BLE001 - one bad run must not stop the server
        traceback.print_exc()


# Answers the delivery, then runs the agent. A delivery held open while an
# agent finishes looks like a dead endpoint, gets retried, and answers the
# sender twice.
app.include_router(create_email_router(on_email, path="/hooks/carlyemail"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
