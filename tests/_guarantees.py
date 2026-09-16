"""The canonical registry of what this module guarantees.

**ONE SOURCE, THREE CONSUMERS.** ``conftest.py`` requires every registered id to
have RUN; ``scripts/fail_controls.py`` requires every registered id to have a
control PROVEN TO FAIL and refuses to run if one has none; ``docs/CONTRACT.md``
is generated from this file. A guarantee therefore cannot be quietly dropped from
any of the three, and a number of them cannot go stale in a comment, because
nothing types the number anywhere.

**A GUARANTEE IS A SENTENCE SOMEBODY COULD ACT ON.** Not "the connector
validates the links document" -- that is a mechanism. "A pass appearing in two
links is refused before anything is read" is a claim with a failing case, and
the failing case is what the control plants.
"""

from __future__ import annotations

GUARANTEES: dict[str, str] = {
    "C1": (
        "Every test module contributes at least one registered guarantee, derived "
        "from the filesystem and read from the AST -- so a module cannot be added, "
        "skipped or deleted without a guard noticing. A module that PLANTS a defect "
        "may not be excused at all."
    ),
    "C2": (
        "docs/CONTRACT.md is GENERATED from this registry and from the code that "
        "implements it -- the finding codes, the exit codes, the report's keys, the "
        "links document's keys, the verbs, the door's pinned line, the pinned commits "
        "-- and its prose is derived rather than fixed: a value that contradicts a "
        "published sentence changes the sentence, because generation is not "
        "verification."
    ),
    "C3": (
        "THE COMMAND LINES ARE THE ONLY DOOR, AND THERE IS NO DATABASE. The runtime "
        "package imports neither module and no database driver, reads no environment "
        "variable at all (so no DSN), and has no `migrations/` directory and no runtime "
        "dependency -- each read from the source, the tree and the dependency list, "
        "never from prose. It runs the two console scripts as subprocesses with the "
        "operator's environment passed through untouched, refuses by name (exit 2) "
        "when either script is not on PATH, and the two packages installed for the "
        "tests are the commits pyproject.toml pins."
    ),
    "C4": (
        "LINKS ARE STATED, NEVER INFERRED. A link carries exactly the published keys, "
        "every one non-blank text and the two tenants uuids; an unknown key, a missing "
        "key, a pass in two links or an agreement in two links is refused by name "
        "before anything is read from either module; and no link is ever guessed from "
        "matching ids. `pass_garage` is an access key, not a scope: a garage the pass "
        "does not name is garage-pass's own refusal, surfaced by name, and the garage "
        "sets compared are the pass's whole set and the agreement's whole covered set."
    ),
    "C5": (
        "ONE VERB, THE INSTANT REQUIRED, THE DAY AS WRITTEN. `sync --links FILE --at "
        "INSTANT` is the whole command line; a missing or naive instant is refused, "
        "exit 2; the day compared with garage-pass's days is the DATE OF THE INSTANT AS "
        "WRITTEN, not converted to any zone; the same instant reaches billing's "
        "`register-vehicle --at`. Exit 0 when every link converged on the final read, "
        "1 when at least one did not, 2 only for the connector's own configuration -- "
        "a module's refusal or configuration sentence is a finding on its link, exit 1. "
        "Links are independent: one broken link stops nothing for the others."
    ),
    "C6": (
        "THE LIVE REGISTER ON DAY D. A pass whose stored state is `active` and whose "
        "valid days (inclusive; a null bound unbounded) contain D has live every "
        "registration with effective_day <= D and (end_day null or D < end_day); a "
        "draft, awaiting-enrolment, suspended, revoked or out-of-days pass has an EMPTY "
        "live register and keeps no car in billing. A registration effective tomorrow "
        "is not registered today; one ending today is released today. The identity "
        "sent to billing is the identity as garage-pass recorded it, byte for byte."
    ),
    "C7": (
        "REGISTERS FIRST, RELEASES BY STORED FORM, NEVER BY RAW IDENTITY. Every live "
        "identity is registered through the door (idempotent there) and the stored "
        "form per garage is taken from the door's printed answer -- the connector "
        "never reimplements billing's normalisation, and a copy of the folded rule in "
        "the package is refused by a scan of the source. Then every row billing holds "
        "whose (garage, form) no live identity produced is released by passing that "
        "form back, which is sound because the normalisation is idempotent at the "
        "door. A release fans out by identity over every covered garage; a release "
        "that takes a row the run had just registered is named and the identities "
        "that produced it are registered again before the final read, so a car swap "
        "whose two plates fold to one form converges in one run with the new car kept."
    ),
    "C8": (
        "A COLLISION RELEASES NOTHING. Two live identities with one stored form at one "
        "garage are reported by name -- garage, form, both identities -- nothing is "
        "released for that link, it does not converge, and the run exits 1."
    ),
    "C9": (
        "THE VERDICT IS THE FINAL READ. After the run's writes both sides are read "
        "again and billing's rows, as (garage, form), are compared with every live "
        "identity's forms from the door's answers: each difference is a DIVERGENCE "
        "naming the garage, the form and the side that holds it; a live identity the "
        "door refused to register has no known form and cannot converge; a pass whose "
        "live register changed under the run is named. A door refusal on the way -- a "
        "car held by another agreement -- is recorded on its action with the door's "
        "own sentence, and the final read decides. Every register and release the "
        "run made is in the report with its reason."
    ),
    "C10": (
        "CONVERGENCE, NOT A JOURNAL. Nothing the connector needs survives between runs "
        "-- the package writes no file and keeps no state -- so a run killed between "
        "the registers and the releases is repaired by the next run from fresh reads, "
        "and a run over a link billing already holds correctly makes no write. Two "
        "runs over one link at once are not serialised by the connector; the contract "
        "says so, and a run whose final read disagrees exits 1."
    ),
    "C11": (
        "REFUSE THE LINK, WRITING NOTHING. An agreement whose registrar is not "
        "`outside`, garage sets that differ (exact text, as sets), a pass or a garage "
        "stored unreadable, rows at garages outside either set, and a module that "
        "would not answer the read -- including a WRONG TENANT on either side, which "
        "is that module's own refusal by name and never an empty register -- each stop "
        "the link before any write, by name, and the link's action list is empty."
    ),
    "C12": (
        "THE REPORT'S SHAPE IS PUBLISHED AND GENERATED. Its keys are derived from the "
        "dataclasses that render it and every key is present on every instance; every "
        "finding code, side, action, outcome and reason the connector emits is in the "
        "registry the contract is generated from, read from the source by AST; a key "
        "or a code the contract does not list reddens the suite."
    ),
    "C13": (
        "THE DOOR'S PRINTED LINE IS PINNED. The one piece of prose the connector reads "
        "-- `  at garage {garage}: {form}`, one line per covered garage after the "
        "first -- is matched against the garage ids the register read already named, "
        "so a form may contain anything, a garage id that another id begins with -- "
        "separator included -- claims no line, and a line naming no known garage is "
        "reported unparseable "
        "rather than guessed at. Measured against the pinned module, so a change "
        "there reddens this repository."
    ),
    "C14": (
        "NOTHING PERSONAL TRAVELS. The report carries ids, garages, days, identities "
        "and stored forms and nothing else: a holder's name, phone or address stored "
        "on the pass reaches no read the connector makes and appears nowhere in a "
        "report rendered from a real pass that carries one."
    ),
    "C15": (
        "THE EXIT GUARANTEE. The connector touches registrations only: its subprocess "
        "calls are exactly `show-pass`, `show-register`, `register-vehicle` and "
        "`release-vehicle`, read from the source; it has no exit verb and no field of "
        "its report could deny one; and garage-pass's own access answer at a lane is "
        "the same before and after a run."
    ),
    "C16": (
        "Every fixture carries its own control asserting it holds the property it "
        "claims to represent, and those controls run as tests: the two garages of "
        "every linked fixture DIFFER in billing identity rule, and the swap plates "
        "fold to one form under the folded rule and to two under the exact rule."
    ),
}


def guarantee_ids() -> tuple[str, ...]:
    """Sorted numerically, not lexically -- C10 follows C9, not C1."""
    return tuple(sorted(GUARANTEES, key=lambda g: int(g[1:])))


#: Naming an id here lets the suite finish with that guarantee unproven. It is a
#: DECISION somebody writes down, never a default -- CI names nothing, and a
#: guarantee that did not run and pass fails the run.
ALLOW_ENV = "PASS_BILLING_CONNECTOR_ALLOW_UNRUN"
