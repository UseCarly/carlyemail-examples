"""Every `webhook.py` in this repository, against signed deliveries.

The agent half of each example needs a model key and cannot run here. The email
half can, and it is the half that decides whether a stranger gets to spend your
tokens — so it is the half worth holding to a test.

Each example's own `agent.py` is replaced with a stub that records what it was
asked to do. Nothing here opens a socket.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import importlib.util
import json
import sys
import time
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT

SECRET = "whsec_" + base64.b64encode(b"an example signing secret, 32b.").decode()
INBOX = "assistant@carlyemail.com"


def sign(body: bytes, *, at: int | None = None) -> dict[str, str]:
    at = int(time.time()) if at is None else at
    key = base64.b64decode(SECRET.removeprefix("whsec_"))
    signed = f"msg_1.{at}.".encode() + body
    digest = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
    return {
        "webhook-id": "msg_1",
        "webhook-timestamp": str(at),
        "webhook-signature": f"v1,{digest}",
    }


def delivery(
    *,
    event_type: str = "message.received",
    sender: str = "emma@example.com",
    event_id: str = "evt_1",
) -> bytes:
    return json.dumps(
        {
            "event_type": event_type,
            "event_id": event_id,
            "message": {
                "message_id": "msg_abc",
                "thread_id": "thd_abc",
                "inbox_id": INBOX,
                "from": sender,
                "subject": "A question",
                "extracted_text": "What are your hours?",
            },
        }
    ).encode()


def stub(name: str, **attributes) -> types.ModuleType:
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


class Recorder:
    """Stands in for the agent, and remembers being called."""

    def __init__(self, result: str = "an answer"):
        self.calls: list[tuple] = []
        self.result = result

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result

    async def acall(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result


def load(example: str, stubs: dict[str, types.ModuleType], monkeypatch):
    """Import one example's `webhook.py` with its agent half stubbed out."""
    monkeypatch.setenv("CARLYEMAIL_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("CARLYEMAIL_INBOX", INBOX)
    monkeypatch.setenv("CARLYEMAIL_API_KEY", "ce_us_test")
    monkeypatch.setenv("ALLOWED_SENDERS", "emma@example.com")

    # Each example ships its own module named `agent`, so a cached one from a
    # previous example would be imported instead of this example's.
    for name in ("agent", "reply", "webhook", *stubs):
        monkeypatch.delitem(sys.modules, name, raising=False)
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)

    spec = importlib.util.spec_from_file_location("webhook", EXAMPLES / example / "webhook.py")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "webhook", module)
    spec.loader.exec_module(module)
    return module


def client(module):
    from fastapi.testclient import TestClient

    return TestClient(module.app)


def post(module, body: bytes, headers: dict[str, str] | None = None):
    return client(module).post("/hooks/carlyemail", content=body, headers=headers or sign(body))


# --- one loader per example ----------------------------------------------


@pytest.fixture
def openai_agent(monkeypatch):
    agent = Recorder()
    module = load("frameworks/openai", {"agent": stub("agent", main=agent.acall)}, monkeypatch)
    return module, agent


@pytest.fixture
def research_agent(monkeypatch):
    agent = Recorder()
    module = load("research-assistant", {"agent": stub("agent", main=agent.acall)}, monkeypatch)
    return module, agent


@pytest.fixture
def claude_agent(monkeypatch):
    agent = Recorder()
    module = load("frameworks/claude", {"agent": stub("agent", main=agent.acall)}, monkeypatch)
    return module, agent


@pytest.fixture
def langchain_agent(monkeypatch):
    agent = Recorder()

    async def build_agent():
        return "the graph"

    module = load(
        "frameworks/langchain",
        {"agent": stub("agent", build_agent=build_agent, handle=agent.acall)},
        monkeypatch,
    )
    module.app.state.agent = "the graph"
    return module, agent


@pytest.fixture
def just_claude(monkeypatch):
    agent = Recorder()
    module = load(
        "email-claude",
        {"reply": stub("reply", INBOX=INBOX, answer=agent)},
        monkeypatch,
    )
    return module, agent


@pytest.fixture
def managed_agent(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_AGENT_ID", "agt_test")
    monkeypatch.setenv("ANTHROPIC_ENVIRONMENT_ID", "env_test")
    agent = Recorder()
    anthropic = stub("anthropic", Anthropic=lambda *a, **k: object())
    module = load("sandbox-assistant", {"anthropic": anthropic}, monkeypatch)
    monkeypatch.setattr(module, "run_agent", agent)
    replies = Recorder()
    monkeypatch.setattr(module.carly, "messages", types.SimpleNamespace(reply=replies))
    return module, agent, replies


ALL = ["openai_agent", "research_agent", "claude_agent", "langchain_agent", "just_claude", "negotiation_buyer",
    "support_desk",
]


@pytest.fixture
def support_desk(monkeypatch):
    agent = Recorder()
    monkeypatch.setenv("HUMAN", "priya@example.com")
    module = load("support-desk", {"agent": stub("agent", main=agent.acall)}, monkeypatch)
    return module, agent


@pytest.fixture
def example(request):
    """Every example except managed-agent, which needs a third stub."""
    return request.getfixturevalue(request.param)


# --- the behaviour every example must have --------------------------------


@pytest.mark.parametrize("example", ALL, indirect=True)
def test_a_signed_delivery_reaches_the_agent(example):
    module, agent = example
    body = delivery()
    assert post(module, body).status_code == 202
    assert len(agent.calls) == 1


@pytest.mark.parametrize("example", ALL, indirect=True)
def test_a_forged_delivery_gets_401_and_no_agent_run(example):
    module, agent = example
    body = delivery()
    headers = sign(body) | {"webhook-signature": "v1,ZmFrZQ=="}
    assert post(module, body, headers).status_code == 401
    assert agent.calls == []


@pytest.mark.parametrize("example", ALL, indirect=True)
def test_a_malformed_signature_gets_401_rather_than_500(example):
    """Not valid base64, so the decode raises `binascii.Error` rather than a
    tidy verification error — the case that otherwise returns 500 to anyone who
    posts junk at a public URL."""
    module, agent = example
    body = delivery()
    headers = sign(body) | {"webhook-signature": "v1,!!!not base64!!!"}
    assert post(module, body, headers).status_code == 401
    assert agent.calls == []


@pytest.mark.parametrize("example", ALL, indirect=True)
@pytest.mark.parametrize(
    "event_type",
    ["message.received.spam", "message.received.blocked", "message.received.unauthenticated"],
)
def test_hostile_mail_never_reaches_the_agent(example, event_type):
    module, agent = example
    body = delivery(event_type=event_type)
    assert post(module, body).status_code == 204
    assert agent.calls == []


@pytest.mark.parametrize("example", ALL, indirect=True)
def test_a_sender_off_the_allowlist_is_dropped(example):
    module, agent = example
    body = delivery(sender="stranger@example.net")
    assert post(module, body).status_code == 204
    assert agent.calls == []


@pytest.mark.parametrize("example", ALL, indirect=True)
def test_a_lookalike_domain_is_dropped(example):
    module, agent = example
    body = delivery(sender="emma@example.com.attacker.net")
    assert post(module, body).status_code == 204
    assert agent.calls == []


@pytest.mark.parametrize("example", ALL, indirect=True)
def test_the_mailbox_does_not_answer_itself(example):
    module, agent = example
    body = delivery(sender=f"Assistant <{INBOX}>")
    assert post(module, body).status_code == 204
    assert agent.calls == []


@pytest.mark.parametrize("example", ALL, indirect=True)
def test_a_redelivery_runs_the_agent_once(example):
    module, agent = example
    body = delivery()
    assert post(module, body).status_code == 202
    assert post(module, body).status_code == 204
    assert len(agent.calls) == 1


@pytest.mark.parametrize("example", ALL, indirect=True)
def test_health_is_still_served(example):
    module, _ = example
    assert client(module).get("/health").json() == {"status": "ok"}


# --- managed-agent, which also mails the answer back ----------------------


def test_managed_agent_replies_with_what_the_agent_wrote(managed_agent):
    module, agent, replies = managed_agent
    body = delivery()

    assert post(module, body).status_code == 202

    assert len(agent.calls) == 1
    assert "What are your hours?" in agent.calls[0][0][0]
    assert replies.calls == [((INBOX, "msg_abc", {"text": "an answer"}), {})]


def test_managed_agent_does_not_run_on_a_forged_delivery(managed_agent):
    module, agent, replies = managed_agent
    body = delivery()
    headers = sign(body) | {"webhook-signature": "v1,!!!not base64!!!"}

    assert post(module, body, headers).status_code == 401
    assert agent.calls == []
    assert replies.calls == []


def test_managed_agent_does_not_run_for_a_sender_off_the_allowlist(managed_agent):
    module, agent, replies = managed_agent
    body = delivery(sender="stranger@example.net")

    assert post(module, body).status_code == 204
    assert agent.calls == []
    assert replies.calls == []


def test_managed_agent_sends_nothing_when_the_agent_says_nothing(managed_agent):
    module, agent, replies = managed_agent
    agent.result = ""
    body = delivery()

    assert post(module, body).status_code == 202
    assert replies.calls == []


# --- negotiation, whose buyer runs one pass per seller reply ---------------


@pytest.fixture
def negotiation_buyer(monkeypatch):
    monkeypatch.setenv("SELLER_EMAIL", "emma@example.com")
    monkeypatch.setenv("OWNER_EMAIL", "owner@example.com")
    agent = Recorder()
    module = load("negotiation", {"buyer": stub("buyer", main=agent.acall)}, monkeypatch)
    return module, agent


def test_the_buyer_is_handed_the_thread_subject(negotiation_buyer):
    """The buyer finds its thread by subject, so the subject is what the
    webhook passes on — with the reply prefix the seller's client added
    taken off."""
    module, agent = negotiation_buyer
    body = json.dumps(
        {
            "event_type": "message.received",
            "event_id": "evt_neg",
            "message": {
                "inbox_id": INBOX,
                "thread_id": "t_neg",
                "message_id": "m_neg",
                "from": "Emma <emma@example.com>",
                "subject": "Re: Your Probat P12 listing",
                "text": "I could do $16,200.",
            },
        }
    ).encode()
    assert post(module, body).status_code in (200, 202, 204)
    assert agent.calls == [(("Your Probat P12 listing",), {})]


# --- approval-inbox, added with the example -------------------------------
#
# Its own block rather than a line in ALL, because concurrent work on this
# file appends; behaviourally it is held to the same bar.


@pytest.fixture
def approval_inbox(monkeypatch):
    monkeypatch.setenv("APPROVER", "sarah@example.com")
    agent = Recorder()
    module = load("approval-inbox", {"agent": stub("agent", main=agent.acall)}, monkeypatch)
    return module, agent


def test_approval_inbox_runs_on_a_signed_delivery_once(approval_inbox):
    module, agent = approval_inbox
    body = delivery()
    assert post(module, body).status_code == 202
    assert post(module, body).status_code == 204  # redelivery
    assert len(agent.calls) == 1


def test_approval_inbox_rejects_a_forged_delivery(approval_inbox):
    module, agent = approval_inbox
    body = delivery()
    headers = sign(body) | {"webhook-signature": "v1,ZmFrZQ=="}
    assert post(module, body, headers).status_code == 401
    assert agent.calls == []


@pytest.mark.parametrize(
    "event_type",
    ["message.received.spam", "message.received.blocked", "message.received.unauthenticated"],
)
def test_approval_inbox_drops_hostile_mail(approval_inbox, event_type):
    module, agent = approval_inbox
    assert post(module, delivery(event_type=event_type)).status_code == 204
    assert agent.calls == []


def test_approval_inbox_drops_senders_off_the_allowlist(approval_inbox):
    module, agent = approval_inbox
    assert post(module, delivery(sender="stranger@example.net")).status_code == 204
    assert post(module, delivery(sender="emma@example.com.attacker.net")).status_code == 204
    assert agent.calls == []


def test_approval_inbox_does_not_answer_itself(approval_inbox):
    module, agent = approval_inbox
    assert post(module, delivery(sender=f"Approvals <{INBOX}>")).status_code == 204
    assert agent.calls == []
