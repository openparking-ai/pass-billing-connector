"""C7 -- registers first, releases by stored form, never by raw identity; and
the connector never reimplements billing's normalisation.

§5.1: a pass over two garages whose billing identity rules DIFFER (folded at
garage-a, exact at garage-b -- tests/test_fixture_axes.py holds the control),
linked to an agreement covering the same two: the first sync registers; a
second sync is a no-op -- exit 0, no actions.

§5.2: a car swap, old ended and new started the same day, including a swap
whose two plates fold to ONE form at garage-a. At the door a release fans
out by identity over every covered garage (measured at the pinned commit:
releasing the stale exact form `ab123` at garage-b also releases the live
folded `ab123` at garage-a). The connector names that and registers the new
car again before the final read, so the swap converges in ONE run with the
new car kept.

§5.5: a foreign row written into billing through the door by something else
is released and reported.

And the precondition, measured at the door rather than assumed: billing's
normalisation is idempotent under both rules -- a form registered as an
identity comes back as itself -- which is what makes a release by form sound.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from harness import AT, needs_databases, standard_world

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "pass_billing_connector"

#: The shapes a reimplementation of the folded rule takes, as AST. A `.lower()`
#: call and an `.isalnum()` call in ONE expression is the rule; either alone
#: is ordinary string handling and is not forbidden.
def _has_the_folded_rule(tree: ast.AST) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.Call)):
            continue
        text = ast.unparse(node)
        if ".lower()" in text and ".isalnum()" in text:
            hits.append(text)
    return hits


def reimplementations() -> dict[str, list[str]]:
    return {
        path.name: hits
        for path in sorted(SRC.glob("*.py"))
        if (hits := _has_the_folded_rule(ast.parse(path.read_text())))
    }


@pytest.mark.guarantee("C7")
def test_the_package_holds_no_copy_of_billings_normalisation():
    assert reimplementations() == {}, reimplementations()


@pytest.mark.guarantee("C7")
def test_the_scan_finds_a_planted_copy(tmp_path):
    """The control on the scan, against the exact spelling billing uses."""
    planted = tmp_path / "planted.py"
    planted.write_text(
        "def normalise(identity):\n"
        "    return ''.join(c for c in identity.lower() if c.isalnum())\n"
    )
    assert _has_the_folded_rule(ast.parse(planted.read_text()))


# ------------------------------------------------------------ the database


@needs_databases
@pytest.mark.guarantee("C7")
def test_first_sync_registers_and_a_second_is_a_no_op(pair, monkeypatch):
    standard_world(pair)
    pair.gp_register("pass-1", "garage-a", "AB-123", "2026-09-01")
    pair.gp_register("pass-1", "garage-a", "cd 456", "2026-09-10")
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0, report
    (one,) = report["links"]
    assert [(a["action"], a["identity"], a["outcome"]) for a in one["actions"]] == [
        ("register", "AB-123", "done"), ("register", "cd 456", "done")]
    assert one["actions"][0]["stored"] == {"garage-a": "ab123", "garage-b": "AB-123"}
    assert one["actions"][1]["stored"] == {"garage-a": "cd456", "garage-b": "cd 456"}
    assert pair.mb_rows("ag-1") == {("garage-a", "ab123"), ("garage-b", "AB-123"),
                                    ("garage-a", "cd456"), ("garage-b", "cd 456")}
    assert one["expected"] == [{"form": f, "garage": g} for g, f in sorted(pair.mb_rows("ag-1"))]

    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0
    (one,) = report["links"]
    # Idempotent AT THE DOOR: the registers are made again and are no-ops
    # there; nothing is released, nothing changes.
    assert all(a["action"] == "register" and a["outcome"] == "done" for a in one["actions"])
    assert one["findings"] == []
    assert pair.mb_rows("ag-1") == {("garage-a", "ab123"), ("garage-b", "AB-123"),
                                    ("garage-a", "cd456"), ("garage-b", "cd 456")}


@needs_databases
@pytest.mark.guarantee("C7")
def test_a_car_swap_releases_the_old_and_keeps_the_new(pair, monkeypatch):
    standard_world(pair)
    pair.gp_register("pass-1", "garage-a", "OLD-1", "2026-09-01")
    assert pair.sync([pair.link()], "2026-09-10T09:00:00-06:00", monkeypatch=monkeypatch)[0] == 0
    pair.gp_end("pass-1", "garage-a", "OLD-1", "2026-09-16")
    pair.gp_register("pass-1", "garage-a", "NEW-2", "2026-09-16")
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0, report
    (one,) = report["links"]
    # ONE release: passing the form `OLD-1` fans out to garage-a as `old1`
    # too, so the stale folded row goes with it and `old1` is never passed
    # (the door would refuse it by name, having nothing left to release).
    assert [(a["action"], a.get("identity") or a.get("form")) for a in one["actions"]] == [
        ("register", "NEW-2"), ("release", "OLD-1")]
    assert one["actions"][1]["stored"] == {"garage-a": "old1", "garage-b": "OLD-1"}
    assert one["findings"] == []
    assert pair.mb_rows("ag-1") == {("garage-a", "new2"), ("garage-b", "NEW-2")}


@needs_databases
@pytest.mark.guarantee("C7")
def test_a_swap_whose_plates_fold_to_one_form_converges_with_the_new_car_kept(pair, monkeypatch):
    standard_world(pair)
    pair.gp_register("pass-1", "garage-a", "ab123", "2026-09-01")
    assert pair.sync([pair.link()], "2026-09-10T09:00:00-06:00", monkeypatch=monkeypatch)[0] == 0
    assert pair.mb_rows("ag-1") == {("garage-a", "ab123"), ("garage-b", "ab123")}
    pair.gp_end("pass-1", "garage-a", "ab123", "2026-09-16")
    pair.gp_register("pass-1", "garage-a", "AB-123", "2026-09-16")
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0, report
    (one,) = report["links"]
    assert pair.mb_rows("ag-1") == {("garage-a", "ab123"), ("garage-b", "AB-123")}
    actions = [(a["action"], a.get("identity") or a.get("form"), a["reason"])
               for a in one["actions"]]
    assert actions == [
        ("register", "AB-123", "live on the day"),
        ("release", "ab123", "billing holds this form; no live identity stores in it"),
        ("register", "AB-123", "re-asserted after a release fanned out to a live form"),
    ]
    (finding,) = one["findings"]
    assert finding["code"] == "RELEASE_TOOK_A_LIVE_FORM"
    assert finding["garage"] == "garage-a" and finding["form"] == "ab123"
    assert finding["identities"] == ["AB-123"]


@needs_databases
@pytest.mark.guarantee("C7")
def test_a_foreign_row_written_through_the_door_is_released_and_reported(pair, monkeypatch):
    standard_world(pair)
    pair.gp_register("pass-1", "garage-a", "AB-123", "2026-09-01")
    pair.mb_register("ag-1", "Foreign 9")  # something else, through the door
    assert pair.mb_rows("ag-1") == {("garage-a", "foreign9"), ("garage-b", "Foreign 9")}
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0, report
    (one,) = report["links"]
    (release,) = [a for a in one["actions"] if a["action"] == "release"]
    assert release["form"] == "Foreign 9"  # the exact form; its fan-out takes `foreign9` too
    assert release["stored"] == {"garage-a": "foreign9", "garage-b": "Foreign 9"}
    assert release["reason"] == "billing holds this form; no live identity stores in it"
    assert pair.mb_rows("ag-1") == {("garage-a", "ab123"), ("garage-b", "AB-123")}


@needs_databases
@pytest.mark.guarantee("C7")
@pytest.mark.parametrize("identity", ["AB-123", " ab 123 ", "İSTANBUL 34", "ΑΣ 12", "ẞ1",
                                      "ＡＢＣ１２３", "ÄÖ-9"])
def test_normalisation_is_idempotent_at_the_door_under_both_rules(pair, identity):
    """A form registered as an identity comes back as itself, at the folded
    garage and at the exact one -- the precondition of releasing by form."""
    standard_world(pair)
    first = pair.mb_register("ag-1", identity).stdout.splitlines()[1:]
    forms = dict(line.strip()[len("at garage "):].split(": ", 1) for line in first)
    assert set(forms) == {"garage-a", "garage-b"}
    for garage, form in forms.items():
        again = pair.mb_register("ag-1", form).stdout.splitlines()[1:]
        forms_again = dict(line.strip()[len("at garage "):].split(": ", 1) for line in again)
        assert forms_again[garage] == form, (identity, garage, form, forms_again)
        pair.mb_release("ag-1", form)


@needs_databases
@pytest.mark.guarantee("C7")
def test_releases_pass_forms_never_a_raw_identity(pair, monkeypatch):
    """Billing holds `Foreign 9` at garage-b (exact) and `foreign9` at garage-a
    (folded), and the pass is empty. The release passes a FORM billing printed
    back -- never a raw identity the connector made up -- and both rows go: the
    stale forms are walked sorted by code point, `Foreign 9` first, and its
    fan-out takes `foreign9` at garage-a with it."""
    standard_world(pair)
    pair.mb_register("ag-1", "Foreign 9")
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0
    (one,) = report["links"]
    assert [a["form"] for a in one["actions"]] == ["Foreign 9"]
    assert all(a["identity"] is None for a in one["actions"])
    assert pair.mb_rows("ag-1") == set()


@needs_databases
@pytest.mark.guarantee("C7")
def test_a_stale_folded_form_alone_is_released_by_that_form(pair, monkeypatch):
    """The other order: only the folded form `foreign9` is left at garage-a
    (garage-b's exact row already gone), so THAT is the form passed back."""
    standard_world(pair)
    pair.mb_register("ag-1", "Foreign 9")
    pair.mb_release("ag-1", "Foreign 9")   # fans out: takes both rows
    pair.mb_register("ag-1", "foreign9")   # a: foreign9, b: foreign9
    pair.mb_release("ag-1", "Foreign 9")   # a: foreign9 goes (folds), b: nothing matches
    assert pair.mb_rows("ag-1") == {("garage-b", "foreign9")}
    code, report = pair.sync([pair.link()], AT, monkeypatch=monkeypatch)
    assert code == 0
    (one,) = report["links"]
    assert [(a["form"], a["stored"]) for a in one["actions"]] == [
        ("foreign9", {"garage-b": "foreign9"})]
    assert pair.mb_rows("ag-1") == set()
