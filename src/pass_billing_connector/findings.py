"""Every name the report can carry, and the sentence each one means.

**ONE REGISTRY, READ BY THE CONTRACT.** ``docs/CONTRACT.md`` renders these
tables from this file, and ``tests/test_c12_the_report_shape_is_published.py``
requires every code the connector emits to be listed here -- a finding nobody
published is refused by the test that scans the source for emitted codes.

A finding is a fact about one link on this run. A refusal of the link
(``REFUSES_THE_LINK``) is a finding that stopped the connector before it wrote
anything for that link; the rest are recorded and the final read decides.
"""

from __future__ import annotations

#: The link was refused before any write, by name. Each one names what differed.
FINDING_REGISTRAR_NOT_OUTSIDE = "REGISTRAR_NOT_OUTSIDE"
FINDING_GARAGE_SETS_DIFFER = "GARAGE_SETS_DIFFER"
FINDING_PASS_UNREADABLE = "PASS_UNREADABLE"
FINDING_PASS_GARAGE_UNREADABLE = "PASS_GARAGE_UNREADABLE"
FINDING_PASS_ROWS_OUTSIDE_ITS_GARAGES = "PASS_ROWS_OUTSIDE_ITS_GARAGES"
FINDING_REGISTER_ROWS_OUTSIDE_COVERED_SET = "REGISTER_ROWS_OUTSIDE_COVERED_SET"
FINDING_GARAGE_IDS_AMBIGUOUS = "GARAGE_IDS_AMBIGUOUS"
#: A module answered the READ with a refusal or a configuration sentence.
FINDING_GARAGE_PASS_REFUSED = "GARAGE_PASS_REFUSED"
FINDING_GARAGE_PASS_CONFIGURATION = "GARAGE_PASS_CONFIGURATION"
FINDING_MONTHLY_BILLING_REFUSED = "MONTHLY_BILLING_REFUSED"
FINDING_MONTHLY_BILLING_CONFIGURATION = "MONTHLY_BILLING_CONFIGURATION"
FINDING_GARAGE_PASS_UNPARSEABLE = "GARAGE_PASS_UNPARSEABLE"
FINDING_MONTHLY_BILLING_UNPARSEABLE = "MONTHLY_BILLING_UNPARSEABLE"
#: Recorded on the way; the final read decides.
FINDING_COLLISION = "COLLISION"
FINDING_STORED_FORM_UNKNOWN = "STORED_FORM_UNKNOWN"
FINDING_PASS_CHANGED_DURING_RUN = "PASS_CHANGED_DURING_RUN"
#: The verdict.
FINDING_DIVERGENCE = "DIVERGENCE"

FINDINGS: dict[str, str] = {
    FINDING_REGISTRAR_NOT_OUTSIDE: (
        "The agreement's registrar is not `outside`, so its register is monthly "
        "billing's own to write and the connector writes nothing for this link. "
        "Refused before any write."
    ),
    FINDING_GARAGE_SETS_DIFFER: (
        "The garages the pass names and the garages the agreement covers are not "
        "the same set, compared as exact text. A link whose two sides disagree on "
        "WHERE has no register to make equal. Refused before any write; the finding "
        "carries both sets."
    ),
    FINDING_PASS_UNREADABLE: (
        "garage-pass holds the pass but cannot read it (`unreadable` on the read is "
        "not null), so its valid days are not known. Refused before any write; the "
        "finding carries garage-pass's own refusal."
    ),
    FINDING_PASS_GARAGE_UNREADABLE: (
        "A garage the pass names is stored unreadable in garage-pass "
        "(`unreadable_garages`). Refused before any write, naming the garage and "
        "garage-pass's own refusal."
    ),
    FINDING_PASS_ROWS_OUTSIDE_ITS_GARAGES: (
        "garage-pass shows a registration row at a garage the pass does not name "
        "(`garages_not_named`). Refused before any write, naming the garages."
    ),
    FINDING_REGISTER_ROWS_OUTSIDE_COVERED_SET: (
        "monthly billing shows a registration row at a garage the agreement's latest "
        "version does not cover (`garages_not_covered`). Refused before any write, "
        "naming the garages."
    ),
    FINDING_GARAGE_IDS_AMBIGUOUS: (
        "One covered garage's id is another covered garage's id plus the door's "
        "separator (`: `) plus anything -- `g` and `g: 2` -- so the door's printed "
        "line `  at garage {id}: {form}` has two readings and no parser can tell "
        "them apart. Refused before any write, naming each such pair; the parser is "
        "never asked the question."
    ),
    FINDING_GARAGE_PASS_REFUSED: (
        "garage-pass refused the read by name (its exit 3): a wrong tenant, a garage "
        "the pass does not name, a pass it does not hold. The finding carries the "
        "module's own refusal code and detail. Nothing was written for this link."
    ),
    FINDING_GARAGE_PASS_CONFIGURATION: (
        "garage-pass answered with a configuration sentence (its exit 2: no DSN, a "
        "database that did not connect). The finding carries the sentence. Nothing "
        "was written for this link."
    ),
    FINDING_MONTHLY_BILLING_REFUSED: (
        "monthly-billing refused or could not find what the read named (its exit 2: "
        "REFUSED or NOT FOUND on stderr) -- a wrong tenant, an agreement it does not "
        "hold. The finding carries the module's own sentence. Nothing was written for "
        "this link."
    ),
    FINDING_MONTHLY_BILLING_CONFIGURATION: (
        "monthly-billing exited with a status the connector does not read as a "
        "refusal (no DSN, a database that did not connect). The finding carries what "
        "it printed. Nothing was written for this link."
    ),
    FINDING_GARAGE_PASS_UNPARSEABLE: (
        "garage-pass exited 0 but what it printed is not the JSON the connector "
        "reads. The finding carries the output. Nothing was written for this link."
    ),
    FINDING_MONTHLY_BILLING_UNPARSEABLE: (
        "monthly-billing exited 0 but what it printed is not the JSON, or not the "
        "`  at garage {id}: {form}` lines, the connector reads. The finding carries "
        "the output."
    ),
    FINDING_COLLISION: (
        "Two live identities of the pass have ONE stored form at one garage under "
        "that garage's rule. Releasing either would take out the other, so NOTHING "
        "is released for this link and it does not converge. The finding names the "
        "garage, the form and both identities."
    ),
    FINDING_STORED_FORM_UNKNOWN: (
        "A live identity's registration was refused by the door, so its stored form "
        "at the covered garages is not known to this run. The finding names the "
        "identity; the door's refusal is on the action. The link does not converge."
    ),
    FINDING_PASS_CHANGED_DURING_RUN: (
        "The final read of the pass shows a live register different from the one the "
        "run started from. The run wrote for the register it read first; the verdict "
        "is against the final one, so the link may not converge until the next run."
    ),
    FINDING_DIVERGENCE: (
        "After the run's writes, the final read of billing's register differs from "
        "the pass's live register: one (garage, form) that is on one side only. "
        "Exit 1. The finding names the garage, the form and which side holds it."
    ),
}

#: Which side of a divergence holds the row.
SIDE_BILLING_ONLY = "billing_only"
SIDE_PASS_ONLY = "pass_only"
SIDES: dict[str, str] = {
    SIDE_BILLING_ONLY: "billing holds a row at this garage in this form; the pass has no "
    "live identity that stores in it",
    SIDE_PASS_ONLY: "the pass has a live identity storing in this form at this garage; "
    "billing holds no such row",
}

#: What an action can report.
ACTION_REGISTER = "register"
ACTION_RELEASE = "release"
ACTIONS: dict[str, str] = {
    ACTION_REGISTER: "`monthly-billing register-vehicle` for one live identity of the pass, "
    "as garage-pass recorded it, at the instant given",
    ACTION_RELEASE: "`monthly-billing release-vehicle --garage` for one stored form billing "
    "holds at ONE covered garage that no live identity stores in there; the action names "
    "the garage",
}
OUTCOME_DONE = "done"
OUTCOME_REFUSED = "refused"
OUTCOME_FAILED = "failed"
OUTCOME_UNPARSEABLE = "unparseable"
OUTCOMES: dict[str, str] = {
    OUTCOME_DONE: "the door answered, exit 0, in lines the connector reads; `stored` carries "
    "what it printed per garage",
    OUTCOME_REFUSED: "the door refused by name, exit 2; `detail` carries its sentence",
    OUTCOME_FAILED: "the door exited with a status that is neither 0 nor 2 (no DSN, a database "
    "that did not connect); `detail` carries what it printed",
    OUTCOME_UNPARSEABLE: "the door exited 0 but what it printed is not the `  at garage {id}: "
    "{form}` lines the connector reads, so nothing is known about what it did; `detail` "
    "carries what it printed and the final read decides",
}

#: Why a register action was made.
REASON_LIVE = "live on the day"
REASON_NOT_LIVE_FORM = "billing holds this form; no live identity stores in it"
REASONS: dict[str, str] = {
    REASON_LIVE: "the identity is in the pass's live register on the day",
    REASON_NOT_LIVE_FORM: "billing's register holds the form at this garage and no live "
    "identity of the pass stores in it there",
}

#: The connector's exit codes.
EXIT_CONVERGED = 0
EXIT_DIVERGED = 1
EXIT_CONFIGURATION = 2
EXITS: dict[int, str] = {
    EXIT_CONVERGED: "every link's billing register equals its pass's live register on the "
    "final read",
    EXIT_DIVERGED: "at least one link's does not -- a refusal, a collision, a divergence, or "
    "a module that would not answer. The report says which, per link",
    EXIT_CONFIGURATION: "the connector itself could not run: the links document is missing, "
    "not JSON, or not of the published shape; `--at` is not an ISO instant with an "
    "offset; a console script is not on PATH. A sentence on stderr, no report",
}
