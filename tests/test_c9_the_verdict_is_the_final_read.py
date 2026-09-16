"""C9 -- the verdict is the final read.

After the run's writes both sides are read again and the verdict is taken
from THAT read, not from the calls. A door refusal on the way -- a car held
by ANOTHER agreement at a garage (§5.6) -- is recorded on its action with
the door's own sentence, the identity has no known form, and the link does
not converge, exit 1, named. A divergence names the garage, the form and
the side that holds it. A pass that changed under the run is named.

The pure half fakes the two doors (`sync.doors`) so the connector's own logic
can be driven through states the real modules cannot be made to produce on
cue -- a pass changing between the first and the final read.
"""

from __future__ import annotations

import json
from datetime import date

import pytest

from harness import AT, needs_databases, standard_world
from pass_billing_connector import sync as sync_module
from pass_billing_connector.doors import Answer, Read
from pass_billing_connector.links import Link
from pass_billing_connector.sync import sync_link

LINK = Link("11111111-1111-1111-1111-111111111111", "pass-1", "garage-a",
            "22222222-2222-2222-2222-222222222222", "ag-1")
D = date(2026, 9, 16)


def shown(rows):
    return {"pass": "pass-1", "state": "active", "valid_from": "2026-01-01",
            "valid_to": "2026-12-31", "garages": ["garage-a", "garage-b"],
            "garages_not_named": [], "unreadable": None, "unreadable_garages": {},
            "registrations": [{"vehicle_identity": i, "garage": g, "effective_day": "2026-09-01",
                               "end_day": None, "ended_reason": None} for i, g in rows]}


def register(rows):
    return {"agreement": "ag-1", "version": 1, "registrar": "outside", "status": "active",
            "cancelled_effective_day": None, "home_garage": "garage-a",
            "covered_garages": ["garage-a", "garage-b"], "garages_not_covered": [],
            "registrations": [{"garage": g, "identity_normalised": f} for g, f in rows]}


class FakeDoors:
    """Two doors with a script: what each read returns, in order, and what
    the door says to each write. Records every call."""

    def __init__(self, passes, registers, register_answers=None):
        self.passes, self.registers = list(passes), list(registers)
        self.register_answers = register_answers or {}
        self.calls: list[tuple] = []

    def show_pass(self, tenant, garage, pass_id):
        self.calls.append(("show-pass",))
        return Read(self.passes.pop(0), None, None)

    def show_register(self, tenant, agreement):
        self.calls.append(("show-register",))
        return Read(self.registers.pop(0), None, None)

    def register_vehicle(self, tenant, agreement, identity, at, garages):
        self.calls.append(("register-vehicle", identity, at))
        folded = "".join(c for c in identity.lower() if c.isalnum())
        default = Answer("done", {"garage-a": folded, "garage-b": identity}, None)
        return self.register_answers.get(identity, default)

    def release_vehicle(self, tenant, agreement, form, garages):
        self.calls.append(("release-vehicle", form))
        return Answer("done", {"garage-b": form}, None)


@pytest.mark.guarantee("C9")
def test_a_pass_that_changed_under_the_run_is_named_and_judged_on_the_final_read(monkeypatch):
    first = shown([("AB-123", "garage-a"), ("AB-123", "garage-b")])
    changed = shown([("AB-123", "garage-a"), ("AB-123", "garage-b"),
                     ("NEW-2", "garage-a"), ("NEW-2", "garage-b")])
    billing_after = register([("garage-a", "ab123"), ("garage-b", "AB-123")])
    fake = FakeDoors([first, changed], [register([]), billing_after, billing_after])
    monkeypatch.setattr(sync_module, "doors", fake)
    result = sync_link(LINK, AT, D)
    assert result.converged is False
    codes = [f.code for f in result.findings]
    assert "PASS_CHANGED_DURING_RUN" in codes
    unknown = [f for f in result.findings if f.code == "STORED_FORM_UNKNOWN"]
    assert [f.identity for f in unknown] == ["NEW-2"]
    assert result.live == {"garage-a": ("AB-123", "NEW-2"), "garage-b": ("AB-123", "NEW-2")}


@pytest.mark.guarantee("C9")
def test_a_divergence_names_garage_form_and_side(monkeypatch):
    """The final read shows a row the run did not expect and lacks one it
    did: two divergences, one per side, and the link does not converge."""
    pass_ = shown([("AB-123", "garage-a"), ("AB-123", "garage-b")])
    final = register([("garage-a", "ab123"), ("garage-b", "stray")])
    fake = FakeDoors([pass_, pass_], [register([]), register([]), final])
    monkeypatch.setattr(sync_module, "doors", fake)
    result = sync_link(LINK, AT, D)
    assert result.converged is False
    divergences = sorted((f.garage, f.form, f.side) for f in result.findings
                         if f.code == "DIVERGENCE")
    assert divergences == [("garage-b", "AB-123", "pass_only"),
                           ("garage-b", "stray", "billing_only")]
    assert [(r.garage, r.form) for r in result.expected] == [("garage-a", "ab123"),
                                                              ("garage-b", "AB-123")]
    assert [(r.garage, r.form) for r in result.billing] == [("garage-a", "ab123"),
                                                             ("garage-b", "stray")]


@pytest.mark.guarantee("C9")
def test_the_verdict_comes_from_the_final_read_not_from_the_calls(monkeypatch):
    """Every call said `done`, and the final read still disagrees: exit 1.
    A verdict taken from the calls would have said converged."""
    pass_ = shown([("AB-123", "garage-a"), ("AB-123", "garage-b")])
    fake = FakeDoors([pass_, pass_], [register([]), register([]), register([])])
    monkeypatch.setattr(sync_module, "doors", fake)
    result = sync_link(LINK, AT, D)
    assert all(a.outcome == "done" for a in result.actions)
    assert result.converged is False
    assert {f.code for f in result.findings} == {"DIVERGENCE"}


@pytest.mark.guarantee("C9")
def test_the_report_is_json_with_sorted_keys():
    from pass_billing_connector.report import Report

    rendered = Report(at=AT, day="2026-09-16", converged=True, links=()).rendered()
    assert rendered == json.dumps(json.loads(rendered), sort_keys=True, indent=2)


# ------------------------------------------------------------ the database


@needs_databases
@pytest.mark.guarantee("C9")
def test_a_car_held_by_another_agreement_is_recorded_and_named_exit_1(pair, monkeypatch):
    from harness import mb_agreement

    standard_world(pair)
    pair.mb_seed((), (mb_agreement("ag-2", "garage-a", ("garage-a",), payer="payer-2"),))
    pair.mb_register("ag-2", "HELD-1")
    pair.gp_register("pass-1", "garage-a", "held 1", "2026-09-01")
    pair.gp_register("pass-1", "garage-a", "FREE-2", "2026-09-01")
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 1
    (one,) = report["links"]
    assert one["converged"] is False
    refused = [a for a in one["actions"] if a["outcome"] == "refused"]
    assert [a["identity"] for a in refused] == ["held 1"]
    assert "REFUSAL_VEHICLE_ALREADY_REGISTERED" in refused[0]["detail"]
    assert "ag-2" in refused[0]["detail"]
    unknown = [f for f in one["findings"] if f["code"] == "STORED_FORM_UNKNOWN"]
    assert [f["identity"] for f in unknown] == ["held 1"]
    # The other car converged on its own: the final read holds it.
    assert pair.mb_rows("ag-1") == {("garage-a", "free2"), ("garage-b", "FREE-2")}
    assert [f["code"] for f in one["findings"] if f["code"] == "DIVERGENCE"] == []


@needs_databases
@pytest.mark.guarantee("C9")
def test_every_register_and_release_is_in_the_report_with_its_reason(pair, monkeypatch):
    standard_world(pair)
    pair.mb_register("ag-1", "Foreign 9")
    pair.gp_register("pass-1", "garage-a", "AB-123", "2026-09-01")
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0
    (one,) = report["links"]
    assert [(a["action"], a["reason"], a["outcome"]) for a in one["actions"]] == [
        ("register", "live on the day", "done"),
        ("release", "billing holds this form; no live identity stores in it", "done"),
    ]
    assert one["actions"][0]["identity"] == "AB-123"
    assert one["actions"][1]["form"] == "Foreign 9"
