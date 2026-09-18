"""C6 -- the pass's live register on day D.

The pure half runs `live.py` over documents shaped exactly as `show-pass`
prints them at the pinned commit. The database half (§5.3) drives real
passes through garage-pass's command line -- a registration starting
tomorrow, one ending today, a revoked pass, a suspended pass, a pass past its
`valid_to` -- and requires billing to end up holding exactly what the day
says, each edge on both sides of its boundary.
"""

from __future__ import annotations

from datetime import date

import pytest

from harness import AT, needs_databases, standard_world
from pass_billing_connector.live import covers, live_register, row_is_live

D = date(2026, 9, 16)


def shown(*, state="active", valid_from="2026-01-01", valid_to="2026-12-31", rows=()):
    return {
        "pass": "pass-1", "state": state, "valid_from": valid_from, "valid_to": valid_to,
        "garages": ["garage-a", "garage-b"], "garages_not_named": [], "unreadable": None,
        "unreadable_garages": {},
        "registrations": [
            {"vehicle_identity": i, "garage": g, "effective_day": e, "end_day": end,
             "ended_reason": None}
            for i, g, e, end in rows
        ],
    }


@pytest.mark.guarantee("C6")
@pytest.mark.parametrize("state, expected", [
    ("active", True), ("draft", False), ("awaiting_enrolment", False), ("suspended", False),
    ("revoked", False),
])
def test_only_an_active_pass_covers_the_day(state, expected):
    assert covers(shown(state=state), D) is expected


@pytest.mark.guarantee("C6")
@pytest.mark.parametrize("valid_from, valid_to, expected", [
    ("2026-09-16", "2026-09-16", True),   # both bounds inclusive: the day itself
    ("2026-09-17", None, False),          # starts tomorrow
    (None, "2026-09-15", False),          # ended yesterday
    (None, None, True),                   # unbounded both ways
    ("2026-09-16", None, True),
    (None, "2026-09-16", True),
])
def test_the_valid_days_are_inclusive_and_a_null_bound_is_unbounded(valid_from, valid_to, expected):
    assert covers(shown(valid_from=valid_from, valid_to=valid_to), D) is expected


@pytest.mark.guarantee("C6")
@pytest.mark.parametrize("effective, end, expected", [
    ("2026-09-16", None, True),          # effective today
    ("2026-09-17", None, False),         # effective tomorrow
    ("2026-09-01", "2026-09-17", True),  # ends tomorrow: live today
    ("2026-09-01", "2026-09-16", False), # ends today: free FROM today
    ("2026-09-01", "2026-09-15", False), # ended yesterday
])
def test_a_row_is_live_from_its_effective_day_until_its_end_day_exclusive(effective, end, expected):
    row = {"effective_day": effective, "end_day": end}
    assert row_is_live(row, D) is expected


@pytest.mark.guarantee("C6")
def test_a_pass_that_does_not_cover_the_day_has_an_empty_register_whatever_its_rows():
    document = shown(state="suspended", rows=(("AB-123", "garage-a", "2026-09-01", None),))
    live = live_register(document, D)
    assert live.covers_the_day is False
    assert live.by_garage == {"garage-a": (), "garage-b": ()}
    assert live.identities() == ()


@pytest.mark.guarantee("C6")
def test_the_identity_is_byte_for_byte_what_garage_pass_recorded():
    document = shown(rows=(("AB-123", "garage-a", "2026-09-01", None),
                           ("ab123", "garage-a", "2026-09-01", None),
                           ("ÄÖ 9", "garage-b", "2026-09-01", None)))
    live = live_register(document, D)
    assert live.by_garage == {"garage-a": ("AB-123", "ab123"), "garage-b": ("ÄÖ 9",)}


# ------------------------------------------------------------ the database


@needs_databases
@pytest.mark.guarantee("C6")
def test_starting_tomorrow_and_ending_today_on_both_sides_of_the_boundary(pair, monkeypatch):
    standard_world(pair)
    pair.gp_register("pass-1", "garage-a", "TOMORROW-1", "2026-09-17")
    pair.gp_register("pass-1", "garage-a", "ENDS-TODAY", "2026-09-01", "2026-09-16")
    pair.gp_register("pass-1", "garage-a", "ENDS-TOMORROW", "2026-09-01", "2026-09-17")
    code, _ = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0
    assert pair.mb_rows("ag-1") == {("garage-a", "endstomorrow"), ("garage-b", "ENDS-TOMORROW")}
    # The day after: TOMORROW-1 is live, ENDS-TOMORROW is free.
    code, _ = pair.sync([pair.link()], "2026-09-17T09:00:00-06:00", monkeypatch=monkeypatch)
    assert code == 0
    assert pair.mb_rows("ag-1") == {("garage-a", "tomorrow1"), ("garage-b", "TOMORROW-1")}
    # The day before: only ENDS-TODAY and ENDS-TOMORROW were live.
    code, _ = pair.sync([pair.link()], "2026-09-15T09:00:00-06:00", monkeypatch=monkeypatch)
    assert code == 0
    assert pair.mb_rows("ag-1") == {("garage-a", "endstoday"), ("garage-b", "ENDS-TODAY"),
                                    ("garage-a", "endstomorrow"), ("garage-b", "ENDS-TOMORROW")}


@needs_databases
@pytest.mark.guarantee("C6")
@pytest.mark.parametrize("state", ["suspended", "revoked"])
def test_a_suspended_or_revoked_pass_keeps_no_car_in_billing(pair, monkeypatch, state):
    standard_world(pair)
    pair.gp_register("pass-1", "garage-a", "AB-123", "2026-09-01")
    code, _ = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0 and pair.mb_rows("ag-1") == {("garage-a", "ab123"), ("garage-b", "AB-123")}
    pair.gp_state("pass-1", "garage-a", state, "2026-09-16T08:00:00-06:00")
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0, report
    assert pair.mb_rows("ag-1") == set()
    # One release per row, each at its garage.
    assert [(a["action"], a["garage"]) for a in report["links"][0]["actions"]] == [
        ("release", "garage-a"), ("release", "garage-b")]


@needs_databases
@pytest.mark.guarantee("C6")
def test_a_pass_past_its_valid_to_has_an_empty_register(pair, monkeypatch):
    standard_world(pair, valid_from="2026-01-01", valid_to="2026-09-15")
    pair.gp_register("pass-1", "garage-a", "AB-123", "2026-09-01")
    code, _ = pair.sync([pair.link()], "2026-09-15T09:00:00-06:00", monkeypatch=monkeypatch)
    assert code == 0 and pair.mb_rows("ag-1") == {("garage-a", "ab123"), ("garage-b", "AB-123")}
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)  # 09-16: past valid_to
    assert code == 0, report
    assert pair.mb_rows("ag-1") == set()
    assert report["links"][0]["live"] == {"garage-a": [], "garage-b": []}
