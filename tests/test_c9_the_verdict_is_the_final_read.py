"""C9 -- the verdict is the final read.

After the run's writes both sides are read again and the verdict is taken
from THAT read, not from the calls. A door refusal on the way -- a car held
by ANOTHER agreement at a garage (§5.6) -- is recorded on its action with
the door's own sentence, the identity has no known form, and the link does
not converge, exit 1, named. A door that exited 0 with lines the connector
cannot read is recorded as `unparseable` on its action, carrying what it
printed, and the final read decides what it did. A divergence names the
garage, the form and the side that holds it. A pass that changed under the
run is named.

A REGISTER THE DOOR DID NOT ANSWER STOPS THE LINK'S RELEASES. Measured before
the rule existed (the C1 gate): a car billing already held, whose register
answered one transient failure, had every one of its rows released by the
same run -- its forms were unknown, so they looked stale. The connector
cannot tell "not registered" from "the door did not tell me"; an incomplete
picture of the desired set is never a licence to delete. THE REFUSALS ARE
CHECKED AGAIN ON THE FINAL READ: a covered set or a registrar that moved
under the run is named and the link does not converge.

The pure half fakes the two doors (`sync.doors`) so the connector's own logic
can be driven through states the real modules cannot be made to produce on
cue -- a pass changing between the first and the final read.
"""

from __future__ import annotations

import json
import os
from datetime import date

import pytest

from harness import AT, needs_databases, standard_world
from pass_billing_connector import doors as doors_module
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
    the door says to each write. Records every call. The parser's own pure
    helper is the real one: the fake stands in for the doors, not for the
    reading of their line."""

    ambiguous_garage_ids = staticmethod(doors_module.ambiguous_garage_ids)

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

    def release_vehicle(self, tenant, agreement, form, garage, garages):
        self.calls.append(("release-vehicle", form, garage))
        return Answer("done", {garage: form}, None)


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
def test_a_door_that_exited_0_unreadably_is_recorded_as_unparseable_and_the_final_read_decides(
    monkeypatch,
):
    """`doors._run` is faked to exit 0 with a line of another shape for the
    release; the register answers normally. The action says `unparseable`
    with what the door printed, nothing is guessed about what was released,
    and the final read -- the stale row still there -- decides: exit 1."""
    import subprocess

    stale = register([("garage-a", "ab123"), ("garage-b", "AB-123"), ("garage-b", "stale")])
    reads = {"show-pass": [shown([("AB-123", "garage-a"), ("AB-123", "garage-b")])] * 2,
             "show-register": [stale] * 3}

    def run(argv):
        verb = argv[1]
        if verb in reads:
            return subprocess.CompletedProcess(argv, 0, json.dumps(reads[verb].pop(0)), "")
        if verb == "register-vehicle":
            return subprocess.CompletedProcess(
                argv, 0, "vehicle registered to agreement ag-1\n  at garage garage-a: ab123\n"
                "  at garage garage-b: AB-123\n", "")
        assert verb == "release-vehicle" and argv[-2:] == ["--garage", "garage-b"], argv
        return subprocess.CompletedProcess(argv, 0, "vehicle released from agreement ag-1\n"
                                           "  at garage garage-z: stale\n", "")

    monkeypatch.setattr(doors_module, "_run", run)
    result = sync_link(LINK, AT, D)
    (release,) = [a for a in result.actions if a.action == "release"]
    assert release.outcome == "unparseable" and release.stored == {}
    assert release.garage == "garage-b" and release.form == "stale"
    assert release.detail == ("exit 0: vehicle released from agreement ag-1\n"
                              "  at garage garage-z: stale")
    assert result.converged is False
    assert [(f.code, f.garage, f.form, f.side) for f in result.findings] == [
        ("DIVERGENCE", "garage-b", "stale", "billing_only")]


@pytest.mark.guarantee("C9")
def test_the_report_is_json_with_sorted_keys():
    from pass_billing_connector.report import Report

    rendered = Report(at=AT, day="2026-09-16", converged=True, links=()).rendered()
    assert rendered == json.dumps(json.loads(rendered), sort_keys=True, indent=2)


@pytest.mark.guarantee("C9")
@pytest.mark.parametrize("outcome, words", [
    ("refused", "exit 2: REFUSED — REFUSAL_VEHICLE_ALREADY_REGISTERED: held by ag-2"),
    ("failed", "exit 1: a store command needs --dsn or MONTHLY_BILLING_DSN."),
    ("unparseable", "exit 0: vehicle registered to agreement ag-1\n  something else"),
])
def test_a_register_the_door_did_not_answer_stops_the_links_releases(monkeypatch, outcome,
                                                                      words):
    """Billing already holds HELD-1's rows and one stale row. HELD-1's
    register does not come back `done`; FREE-2's does. NOTHING is released --
    not the stale row, and not HELD-1's rows, which would have looked stale
    with its forms unknown. The finding names the identity and the door's
    words; FREE-2's register stands; the link does not converge."""
    pass_ = shown([("HELD-1", "garage-a"), ("HELD-1", "garage-b"),
                   ("FREE-2", "garage-a"), ("FREE-2", "garage-b")])
    held = [("garage-a", "held1"), ("garage-b", "HELD-1"), ("garage-a", "stale")]
    after = register(held + [("garage-a", "free2"), ("garage-b", "FREE-2")])
    fake = FakeDoors([pass_, pass_], [register(held), after, after],
                     register_answers={"HELD-1": Answer(outcome, {}, words)})
    monkeypatch.setattr(sync_module, "doors", fake)
    result = sync_link(LINK, AT, D)
    assert [c for c in fake.calls if c[0] == "release-vehicle"] == []
    assert [(a.action, a.identity, a.outcome) for a in result.actions] == [
        ("register", "FREE-2", "done"), ("register", "HELD-1", outcome)]
    (unknown,) = [f for f in result.findings if f.code == "STORED_FORM_UNKNOWN"]
    assert unknown.identity == "HELD-1"
    assert words in unknown.detail and outcome in unknown.detail
    assert "nothing is released" in unknown.detail
    assert result.converged is False
    # The verdict still comes from the final read: the stale row is a
    # divergence there, HELD-1's rows are not (its forms are unknown, not wrong).
    assert [(f.garage, f.form, f.side) for f in result.findings if f.code == "DIVERGENCE"] == [
        ("garage-a", "held1", "billing_only"), ("garage-a", "stale", "billing_only"),
        ("garage-b", "HELD-1", "billing_only")]


@pytest.mark.guarantee("C9")
@pytest.mark.parametrize("moved, codes", [
    ({"covered_garages": ["garage-a"]}, ["GARAGE_SETS_DIFFER"]),
    ({"registrar": "self"}, ["REGISTRAR_NOT_OUTSIDE"]),
    ({"covered_garages": ["garage-a", "garage-b", "garage-a: 2"]},
     ["GARAGE_SETS_DIFFER", "GARAGE_IDS_AMBIGUOUS"]),
    ({"garages_not_covered": ["garage-c"]}, ["REGISTER_ROWS_OUTSIDE_COVERED_SET"]),
])
def test_a_refusal_that_appears_on_the_final_read_is_named_and_the_link_does_not_converge(
    monkeypatch, moved, codes,
):
    """The first reads pass every check and the run writes; the FINAL read of
    billing shows something step 1 would have refused. Named exactly as at
    the start, and not converged -- even though the rows themselves are
    equal."""
    pass_ = shown([("AB-123", "garage-a"), ("AB-123", "garage-b")])
    rows = [("garage-a", "ab123"), ("garage-b", "AB-123")]
    final = register(rows)
    final.update(moved)
    fake = FakeDoors([pass_, pass_], [register([]), register(rows), final])
    monkeypatch.setattr(sync_module, "doors", fake)
    result = sync_link(LINK, AT, D)
    assert result.refused is False
    assert [f.code for f in result.findings] == codes
    assert result.converged is False
    assert [(r.garage, r.form) for r in result.billing] == rows


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
    # And the unanswered register stopped the releases: none was made.
    assert [a for a in one["actions"] if a["action"] == "release"] == []


@needs_databases
@pytest.mark.guarantee("C9")
def test_every_register_and_release_is_in_the_report_with_its_reason(pair, monkeypatch):
    standard_world(pair)
    pair.mb_register("ag-1", "Foreign 9")
    pair.gp_register("pass-1", "garage-a", "AB-123", "2026-09-01")
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0
    (one,) = report["links"]
    assert [(a["action"], a["reason"], a["outcome"], a["garage"]) for a in one["actions"]] == [
        ("register", "live on the day", "done", None),
        ("release", "billing holds this form; no live identity stores in it", "done", "garage-a"),
        ("release", "billing holds this form; no live identity stores in it", "done", "garage-b"),
    ]
    assert one["actions"][0]["identity"] == "AB-123"
    assert [a["form"] for a in one["actions"][1:]] == ["foreign9", "Foreign 9"]


@needs_databases
@pytest.mark.guarantee("C9")
@pytest.mark.parametrize("answer", ["failed", "unparseable"])
def test_a_held_car_whose_register_did_not_answer_keeps_its_rows_and_nothing_is_released(
    pair, monkeypatch, tmp_path, answer,
):
    """THE GATE'S CASE, BY ITS METHOD. The console script as a subprocess; a
    shim `monthly-billing` ahead of the real one on PATH intercepts exactly
    ONE call -- the first `register-vehicle` -- and forwards every other call
    to the real door. `failed` is the real door with its DSN dropped for that
    call (its own exit 1); `unparseable` is exit 0 with lines the connector
    cannot read. LIVE-1 is live on the pass and ALREADY in billing from a
    previous run, beside one stale row. After the run: billing still holds
    LIVE-1 at both garages, billing's own barrier answers COVERED at both,
    the stale row is still there (nothing was released), exit 1 with the
    finding; the next run, real door throughout, converges."""
    import shutil
    import subprocess

    standard_world(pair)
    pair.gp_register("pass-1", "garage-a", "LIVE-1", "2026-09-01")
    pair.mb_register("ag-1", "LIVE-1", AT)
    pair.mb_register("ag-1", "old1", AT)
    held = {("garage-a", "live1"), ("garage-b", "LIVE-1"), ("garage-a", "old1"),
            ("garage-b", "old1")}
    assert pair.mb_rows("ag-1") == held

    real = shutil.which("monthly-billing")
    assert real
    marker = tmp_path / "intercepted"
    shim = tmp_path / "monthly-billing"
    body = {
        "failed": f'unset MONTHLY_BILLING_DSN; exec "{real}" "$@"',
        "unparseable": 'echo "vehicle registered"; echo "  a line the connector cannot read"; '
                       'exit 0',
    }[answer]
    shim.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = "register-vehicle" ] && [ ! -e "{marker}" ]; then\n'
        f'  : > "{marker}"\n'
        f"  {body}\n"
        "fi\n"
        f'exec "{real}" "$@"\n'
    )
    shim.chmod(0o700)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")

    def covered(garage: str) -> str:
        done = pair.mb_run("covered-in-store", "--garage", garage, "--vehicle", "LIVE-1",
                           "--at", AT, check=False)
        return done.stdout.split()[0]

    code, report, err = pair.sync_script([pair.link()], AT)
    assert marker.exists(), "the shim did not intercept the register"
    assert code == 1, err
    (one,) = report["links"]
    (reg,) = [a for a in one["actions"] if a["action"] == "register"]
    assert reg["identity"] == "LIVE-1" and reg["outcome"] == answer
    assert [a for a in one["actions"] if a["action"] == "release"] == []
    (unknown,) = [f for f in one["findings"] if f["code"] == "STORED_FORM_UNKNOWN"]
    assert unknown["identity"] == "LIVE-1" and reg["detail"] in unknown["detail"]
    assert one["converged"] is False
    assert pair.mb_rows("ag-1") == held
    assert (covered("garage-a"), covered("garage-b")) == ("COVERED", "COVERED")

    # The next run, the real door throughout: the stale row goes, LIVE-1 stays.
    monkeypatch.setenv("PATH", os.environ["PATH"].split(":", 1)[1])
    code, report, err = pair.sync_script([pair.link()], AT)
    assert code == 0, err
    assert [(a["action"], a["form"], a["garage"]) for a in report["links"][0]["actions"]] == [
        ("register", None, None), ("release", "old1", "garage-a"), ("release", "old1", "garage-b")]
    assert pair.mb_rows("ag-1") == {("garage-a", "live1"), ("garage-b", "LIVE-1")}
    assert (covered("garage-a"), covered("garage-b")) == ("COVERED", "COVERED")
    assert subprocess.run(["which", "monthly-billing"], capture_output=True,
                          text=True).stdout.strip() == real


@needs_databases
@pytest.mark.guarantee("C9")
@pytest.mark.parametrize("covered_after", [("garage-a",), ("garage-a", "garage-b", "garage-c")])
def test_a_covered_set_that_moved_under_the_run_is_named_on_the_final_read(
    pair, monkeypatch, covered_after,
):
    """Billing's operator stores version 2 of the agreement -- fewer garages,
    or more -- between the connector's first read and its first write. The
    first read passed; the final read shows sets that differ, and the link
    is named `GARAGE_SETS_DIFFER` and does not converge, exit 1. The next
    run refuses it by name before any write."""
    from harness import mb_agreement, mb_garage

    standard_world(pair)
    if "garage-c" in covered_after:
        pair.mb_seed((mb_garage("garage-c", "Pacific/Auckland", "exact"),), ())
    pair.gp_register("pass-1", "garage-a", "LIVE-1", "2026-09-01")
    pair.mb_register("ag-1", "old1", AT)
    original = doors_module._run
    reads = {"n": 0}

    def run_and_revise(argv):
        done = original(argv)
        if argv[1] == "show-register":
            reads["n"] += 1
            if reads["n"] == 1:
                version_2 = mb_agreement("ag-1", "garage-a", covered_after)
                version_2["version"] = 2
                pair.mb_revise(version_2)
        return done

    monkeypatch.setattr(doors_module, "_run", run_and_revise)
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 1
    (one,) = report["links"]
    assert one["refused"] is False and one["converged"] is False
    assert "GARAGE_SETS_DIFFER" in [f["code"] for f in one["findings"]]
    monkeypatch.setattr(doors_module, "_run", original)
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 1
    (one,) = report["links"]
    assert one["refused"] is True and one["actions"] == []
    assert [f["code"] for f in one["findings"]] == ["GARAGE_SETS_DIFFER"]
