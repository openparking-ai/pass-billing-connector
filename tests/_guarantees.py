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
        "implements it -- the pinned commits today, the module's own registries when "
        "it lands -- and its prose is derived rather than fixed: a value that "
        "contradicts a published sentence changes the sentence, because generation "
        "is not verification."
    ),
}


def guarantee_ids() -> tuple[str, ...]:
    """Sorted numerically, not lexically -- C10 follows C9, not C1."""
    return tuple(sorted(GUARANTEES, key=lambda g: int(g[1:])))


#: Naming an id here lets the suite finish with that guarantee unproven. It is a
#: DECISION somebody writes down, never a default -- CI names nothing, and a
#: guarantee that did not run and pass fails the run.
ALLOW_ENV = "PASS_BILLING_CONNECTOR_ALLOW_UNRUN"
