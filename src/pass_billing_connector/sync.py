"""One link, one run: registers first, releases by stored form, the verdict
from the final read.

THE ORDER, AND WHY.

1. **Read both, and refuse the link -- writing nothing -- on anything that
   makes "equal" undefined**: a registrar that is not `outside`, garage sets
   that differ, a pass or garage stored unreadable, rows outside either set,
   a covered set whose ids the door's printed line cannot tell apart (one id
   is another plus `: ` plus anything). Each refusal is a finding by name; a
   module that would not answer the read is a finding carrying the module's
   own words.

2. **Register every live identity** (``live.py``), as garage-pass recorded it,
   through ``register-vehicle`` -- idempotent at the door: a row already this
   agreement's is left and its stored form still printed. The printed form
   per garage is COLLECTED, and it is the only source of a stored form the
   connector ever has. The connector never reimplements billing's
   normalisation; the door's answer is the whole of what it knows about forms.

3. **A collision stops the releases.** Two live identities with one stored
   form at one garage (the folded rule makes `AB-123` and `ab123` one billing
   row): releasing either would take out the other, so nothing is released
   for the link, it does not converge, and the report names the garage, the
   form and both identities.

4. **Release by stored form, never by raw identity, AT THE GARAGE THAT
   STORES IT.** Every row billing holds at a garage whose form is not among
   step 2's forms at that garage is released by passing that form back to
   ``release-vehicle --garage`` naming that garage. That relies on billing's
   normalisation being idempotent -- ``n(n(x)) == n(x)`` -- which was measured
   at the pinned commit over every code point under every rule before this
   was built, and which ``tests/test_c7_...`` measures again at the door.

   **AND THE GARAGE IS ALWAYS NAMED.** The door's unnamed release takes ONE
   identity and releases it at EVERY covered garage under each garage's own
   rule -- so releasing a stale exact-rule form `ab123` at garage B would also
   release the live folded-rule row `ab123` at garage A, which is `AB-123`'s,
   and the car would be uncovered at A until it was registered again.
   Measured at the pinned commit, not reasoned about. Naming the garage
   (billing's G46) takes the one row and no other, so no release of this
   connector's ever takes a live car's row, and there is no window to state.

5. **Read both again. The verdict is the final read.** Billing's rows, as
   (garage, form), against every live identity's forms from the door's
   answers. A difference either way is a DIVERGENCE, per garage, per form,
   naming the side that holds it; a live identity whose registration the
   door refused has no known form and cannot converge; a pass that changed
   under the run is named. Every register and release the run made is in the
   report with its reason and the door's own words.

THE CROSS-DATABASE FAILURE STATE IS CONVERGENCE. The two writes are never one
transaction. Nothing here survives between runs, so a run killed half-way is
repaired by the next run from fresh reads, and no state of the connector's
can go stale. Two runs over one link at once are NOT serialised by the
connector; the operator runs one at a time per link, and a run whose final
read disagrees exits 1.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from pass_billing_connector import doors
from pass_billing_connector.findings import (
    FINDING_COLLISION,
    FINDING_DIVERGENCE,
    FINDING_GARAGE_IDS_AMBIGUOUS,
    FINDING_GARAGE_SETS_DIFFER,
    FINDING_PASS_CHANGED_DURING_RUN,
    FINDING_PASS_GARAGE_UNREADABLE,
    FINDING_PASS_ROWS_OUTSIDE_ITS_GARAGES,
    FINDING_PASS_UNREADABLE,
    FINDING_REGISTER_ROWS_OUTSIDE_COVERED_SET,
    FINDING_REGISTRAR_NOT_OUTSIDE,
    FINDING_STORED_FORM_UNKNOWN,
    OUTCOME_DONE,
    REASON_LIVE,
    REASON_NOT_LIVE_FORM,
    SIDE_BILLING_ONLY,
    SIDE_PASS_ONLY,
)
from pass_billing_connector.links import Link
from pass_billing_connector.live import LiveRegister, live_register
from pass_billing_connector.report import Action, Finding, LinkReport, Report, Row

REGISTRAR_OUTSIDE = "outside"


class InstantRefused(Exception):
    """``--at`` is not an ISO instant with an offset. A sentence, exit 2."""


def day_of(at: str) -> date:
    """THE DATE OF THE INSTANT AS WRITTEN -- garage-pass's own convention for
    ``effective_day`` ("the caller's one day at every garage"). Not converted
    to any garage's zone: a pass spans garages in different zones and which
    day is the caller's call, made by writing the instant."""
    try:
        instant = datetime.fromisoformat(at)
    except ValueError:
        raise InstantRefused(f"--at {at!r} is not an ISO instant.") from None
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise InstantRefused(f"--at {at!r} carries no offset; the instant is stated with one.")
    return instant.date()


def sync(links: tuple[Link, ...], at: str) -> Report:
    day = day_of(at)
    reports = tuple(sync_link(link, at, day) for link in links)
    return Report(at=at, day=day.isoformat(), converged=all(r.converged for r in reports),
                  links=reports)


def _refused(link: Link, findings: list[Finding]) -> LinkReport:
    return LinkReport(
        pass_tenant=link.pass_tenant, pass_id=link.pass_id, pass_garage=link.pass_garage,
        billing_tenant=link.billing_tenant, agreement_id=link.agreement_id,
        converged=False, refused=True, live={}, expected=(), billing=(), actions=(),
        findings=tuple(findings),
    )


def _read_both(link: Link) -> tuple[dict | None, dict | None, list[Finding]]:
    findings: list[Finding] = []
    pass_read = doors.show_pass(link.pass_tenant, link.pass_garage, link.pass_id)
    if not pass_read.ok:
        findings.append(Finding(pass_read.finding, pass_read.detail))
    register_read = doors.show_register(link.billing_tenant, link.agreement_id)
    if not register_read.ok:
        findings.append(Finding(register_read.finding, register_read.detail))
    return pass_read.document, register_read.document, findings


def _link_refusals(shown: dict, register: dict) -> list[Finding]:
    """K5.1: what makes "equal" undefined for this link, each by name."""
    findings: list[Finding] = []
    if register.get("registrar") != REGISTRAR_OUTSIDE:
        findings.append(Finding(
            FINDING_REGISTRAR_NOT_OUTSIDE,
            f"agreement {register.get('agreement')!r} states registrar "
            f"{register.get('registrar')!r}; the connector writes only an `outside` register.",
        ))
    named = set(shown.get("garages") or ())
    covered = set(register.get("covered_garages") or ())
    if named != covered:
        findings.append(Finding(
            FINDING_GARAGE_SETS_DIFFER,
            f"the pass names {sorted(named)}; the agreement covers {sorted(covered)}.",
        ))
    if shown.get("unreadable") is not None:
        findings.append(Finding(FINDING_PASS_UNREADABLE, _text(shown["unreadable"])))
    for garage, refusal in sorted((shown.get("unreadable_garages") or {}).items()):
        findings.append(Finding(FINDING_PASS_GARAGE_UNREADABLE, _text(refusal), garage=garage))
    not_named = list(shown.get("garages_not_named") or ())
    if not_named:
        findings.append(Finding(
            FINDING_PASS_ROWS_OUTSIDE_ITS_GARAGES,
            f"garage-pass shows rows at {sorted(not_named)}, which the pass does not name.",
        ))
    not_covered = list(register.get("garages_not_covered") or ())
    if not_covered:
        findings.append(Finding(
            FINDING_REGISTER_ROWS_OUTSIDE_COVERED_SET,
            f"billing shows rows at {sorted(not_covered)}, which the latest version does not "
            "cover.",
        ))
    for shorter, longer in doors.ambiguous_garage_ids(tuple(sorted(covered))):
        findings.append(Finding(
            FINDING_GARAGE_IDS_AMBIGUOUS,
            f"covered garage {longer!r} is {shorter!r} plus the door's separator plus text, so "
            f"a line the door prints for {shorter!r} can read as one for {longer!r}.",
            garage=longer,
        ))
    return findings


def _text(value: object) -> str:
    import json

    return value if isinstance(value, str) else json.dumps(value, sort_keys=True)


def sync_link(link: Link, at: str, day: date) -> LinkReport:
    shown, register, findings = _read_both(link)
    if shown is None or register is None:
        return _refused(link, findings)
    findings = _link_refusals(shown, register)
    if findings:
        return _refused(link, findings)

    garages = tuple(sorted(register["covered_garages"]))
    actions: list[Action] = []
    first_live = live_register(shown, day)

    # 2. Registers, collecting the door's forms. forms[(garage, form)] is the
    #    set of live identities the door stored in that form there.
    identity_forms: dict[str, dict[str, str]] = {}
    forms: dict[tuple[str, str], set[str]] = defaultdict(set)
    for identity in first_live.identities():
        _register(link, identity, at, garages, REASON_LIVE, actions, identity_forms, forms,
                  findings)

    # 3. A collision stops the releases.
    collisions = {key: ids for key, ids in forms.items() if len(ids) > 1}
    for (garage, form), identities in sorted(collisions.items()):
        findings.append(Finding(
            FINDING_COLLISION,
            f"identities {sorted(identities)} both store as {form!r} at {garage!r}; nothing "
            "is released for this link.",
            garage=garage, form=form, identities=tuple(sorted(identities)),
        ))

    # 4. Releases by stored form, each at the one garage that stores it.
    if not collisions:
        _release_stale(link, garages, actions, forms, findings)

    # 5. The final read decides.
    final_shown, final_register, read_findings = _read_both(link)
    findings.extend(read_findings)
    if final_shown is None or final_register is None:
        return LinkReport(
            pass_tenant=link.pass_tenant, pass_id=link.pass_id, pass_garage=link.pass_garage,
            billing_tenant=link.billing_tenant, agreement_id=link.agreement_id,
            converged=False, refused=False, live=dict(first_live.by_garage), expected=(),
            billing=(), actions=tuple(actions), findings=tuple(findings),
        )
    final_live = live_register(final_shown, day)
    if final_live.pairs() != first_live.pairs():
        findings.append(Finding(
            FINDING_PASS_CHANGED_DURING_RUN,
            f"the run started from {_pairs(first_live)} and the final read shows "
            f"{_pairs(final_live)}.",
        ))
    expected: set[tuple[str, str]] = set()
    for identity in final_live.identities():
        stored = identity_forms.get(identity)
        if stored is None:
            if not any(f.code == FINDING_STORED_FORM_UNKNOWN and f.identity == identity
                       for f in findings):
                findings.append(Finding(
                    FINDING_STORED_FORM_UNKNOWN,
                    f"identity {identity!r} is live on the final read and was not registered "
                    "by this run, so its stored form is not known.",
                    identity=identity,
                ))
            continue
        expected |= {(g, f) for g, f in stored.items()}
    billing = {(row["garage"], row["identity_normalised"])
               for row in final_register.get("registrations") or ()}
    for garage, form in sorted(billing - expected):
        findings.append(Finding(
            FINDING_DIVERGENCE, f"billing holds {form!r} at {garage!r}; the pass's live "
            "register stores nothing in that form there.", garage=garage, form=form,
            side=SIDE_BILLING_ONLY,
        ))
    for garage, form in sorted(expected - billing):
        findings.append(Finding(
            FINDING_DIVERGENCE, f"the pass's live register stores {form!r} at {garage!r}; "
            "billing holds no such row.", garage=garage, form=form, side=SIDE_PASS_ONLY,
        ))
    unknown = any(f.code == FINDING_STORED_FORM_UNKNOWN for f in findings)
    converged = billing == expected and not collisions and not unknown
    return LinkReport(
        pass_tenant=link.pass_tenant, pass_id=link.pass_id, pass_garage=link.pass_garage,
        billing_tenant=link.billing_tenant, agreement_id=link.agreement_id,
        converged=converged, refused=False, live=dict(final_live.by_garage),
        expected=tuple(Row(g, f) for g, f in sorted(expected)),
        billing=tuple(Row(g, f) for g, f in sorted(billing)),
        actions=tuple(actions), findings=tuple(findings),
    )


def _pairs(live: LiveRegister) -> list[list[str]]:
    return [list(p) for p in sorted(live.pairs())]


def _register(link: Link, identity: str, at: str, garages: tuple[str, ...], reason: str,
              actions: list[Action], identity_forms: dict[str, dict[str, str]],
              forms: dict[tuple[str, str], set[str]], findings: list[Finding]) -> None:
    answer = doors.register_vehicle(link.billing_tenant, link.agreement_id, identity, at, garages)
    actions.append(Action(
        action="register", outcome=answer.outcome, reason=reason, identity=identity,
        stored=dict(answer.stored), detail=answer.reason,
    ))
    if answer.outcome != OUTCOME_DONE:
        if reason == REASON_LIVE:
            findings.append(Finding(
                FINDING_STORED_FORM_UNKNOWN,
                f"the door did not register {identity!r}: {answer.reason}", identity=identity,
            ))
        return
    identity_forms[identity] = dict(answer.stored)
    for garage, form in answer.stored.items():
        forms[(garage, form)].add(identity)


def _release_stale(link: Link, garages: tuple[str, ...], actions: list[Action],
                   forms: dict[tuple[str, str], set[str]], findings: list[Finding]) -> None:
    mid = doors.show_register(link.billing_tenant, link.agreement_id)
    if not mid.ok:
        findings.append(Finding(mid.finding, mid.detail))
        return
    held = {(row["garage"], row["identity_normalised"])
            for row in mid.document.get("registrations") or ()}
    # The stale rows, as (garage, form), each released at ITS garage by ITS
    # form: one row per door call, and the door's answer is that one row. A
    # row whose form another garage's live car also stores in is no different
    # -- the release named the garage, so the other garage's row is not
    # reached. The final read decides what was taken.
    stale = {(garage, form) for (garage, form) in held if (garage, form) not in forms}
    for garage, form in sorted(stale):
        answer = doors.release_vehicle(link.billing_tenant, link.agreement_id, form, garage,
                                       garages)
        actions.append(Action(
            action="release", outcome=answer.outcome, reason=REASON_NOT_LIVE_FORM, form=form,
            garage=garage, stored=dict(answer.stored), detail=answer.reason,
        ))
