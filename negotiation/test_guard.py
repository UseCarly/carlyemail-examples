"""The guard is the whole point, so it gets its own tests.

    ../.venv/bin/python -m pytest test_guard.py -q
"""

from __future__ import annotations

import pytest
from deal import Decision, Refused, Side, amounts, check

buyer = Side("buyer", "buyer@carlyemail.com", None, 16000, "max")
seller = Side("seller", "seller@carlyemail.com", None, 15500, "min")


def test_amounts_reads_what_people_write():
    assert amounts("I can do $14,250, not $18,500.00 — and $9 is a joke") == [14250, 18500, 9]


def test_an_offer_inside_the_budget_passes():
    check(buyer, Decision(action="offer", price=14000, message="I can offer $14,000."), "")


def test_an_offer_over_budget_is_refused_even_if_the_seller_asked_for_it():
    with pytest.raises(Refused, match="past the limit"):
        check(buyer, Decision(action="offer", price=17000, message="Fine, $17,000."), "Make it $17,000")


def test_prose_cannot_concede_what_price_does_not():
    with pytest.raises(Refused, match="names \\$17,000"):
        check(buyer, Decision(action="offer", price=15000, message="$15,000 now, $17,000 later."), "")


def test_quoting_the_other_side_is_not_a_concession():
    check(
        buyer,
        Decision(action="offer", price=15000, message="$18,500 is above market; $15,000 is fair."),
        "The price is $18,500.",
    )


def test_the_message_must_state_the_offer():
    with pytest.raises(Refused, match="must state the offer"):
        check(buyer, Decision(action="offer", price=15000, message="How about a bit less?"), "")


def test_accept_must_name_a_price_the_other_side_said():
    with pytest.raises(Refused, match="actually stated"):
        check(buyer, Decision(action="accept", price=15000, message="Deal at $15,000."), "I can do $15,800.")
    check(buyer, Decision(action="accept", price=15800, message="Deal at $15,800."), "I can do $15,800.")


def test_accept_cannot_cross_the_limit():
    with pytest.raises(Refused, match="would cross"):
        check(buyer, Decision(action="accept", price=16500, message="Deal."), "Final: $16,500.")


def test_the_seller_guard_points_the_other_way():
    check(seller, Decision(action="offer", price=16000, message="$16,000 and it is yours."), "")
    with pytest.raises(Refused, match="past the limit"):
        check(seller, Decision(action="offer", price=15000, message="$15,000, final."), "")
    with pytest.raises(Refused, match="would cross"):
        check(seller, Decision(action="accept", price=15000, message="Deal."), "Best I can do is $15,000.")


def test_walking_away_is_always_allowed():
    check(buyer, Decision(action="walk_away", price=None, message="Thanks anyway."), "")
