"""`verification-codes/codes.py` finds the code and not the order number."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "verification-codes"))

from codes import Code, extract, wait_for_code  # noqa: E402


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Your verification code: 689101\nEnter this code to activate sending.", "689101"),
        ("Your GitHub launch code is 4821 9307", "4821"),  # two groups; the first one
        ("Use 173920 to sign in. This code expires in 10 minutes.", "173920"),
        ("Order #48211 shipped. Confirm receipt with code 557201.", "557201"),  # not the order
        ("One-time passcode\n\n90211", "90211"),
        ("Your invoice total is 48211 EUR, due 2026-09-01.", None),  # digits, no code words
        ("Thanks for signing up! We'll be in touch.", None),
        ("", None),
    ],
)
def test_extract(text, expected):
    assert extract(text) == expected


def fake_client(messages: list[dict]) -> MagicMock:
    client = MagicMock()
    client.messages.list.return_value = {"messages": messages}
    client.messages.get.side_effect = lambda inbox, message_id: next(
        m for m in messages if m["message_id"] == message_id
    )
    return client


def test_wait_for_code_returns_the_first_matching_sender():
    client = fake_client(
        [
            {
                "message_id": "m1",
                "thread_id": "t1",
                "from": "Stripe <notifications@stripe.com>",
                "subject": "Your Stripe verification code",
                "extracted_text": "Your code is 111222.",
            },
            {
                "message_id": "m2",
                "thread_id": "t2",
                "from": "GitHub <noreply@github.com>",
                "subject": "[GitHub] Please verify your device",
                "extracted_text": "Verification code: 333444\n\nOpen GitHub and enter it.",
            },
        ]
    )
    code = wait_for_code(client, "signups@carlyemail.com", sender="@github.com", timeout=1)
    assert code == Code(
        value="333444",
        message_id="m2",
        thread_id="t2",
        sender="GitHub <noreply@github.com>",
        subject="[GitHub] Please verify your device",
        received_at="",
    )


def test_wait_for_code_times_out_rather_than_guessing():
    client = fake_client([])
    with pytest.raises(TimeoutError, match="signups@carlyemail.com"):
        wait_for_code(client, "signups@carlyemail.com", timeout=0.01, every=0.01)


def test_only_received_mail_since_the_call_is_considered():
    client = fake_client([])
    with pytest.raises(TimeoutError):
        wait_for_code(client, "signups@carlyemail.com", timeout=0.01, every=0.01)
    _, kwargs = client.messages.list.call_args
    assert kwargs["labels"] == ["received"]
    assert kwargs["after"]  # an ISO timestamp from just before the call
