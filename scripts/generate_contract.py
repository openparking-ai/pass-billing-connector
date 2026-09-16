#!/usr/bin/env python3
"""Generate docs/CONTRACT.md from the registries, and check it has not drifted.

    python scripts/generate_contract.py            # write the document
    python scripts/generate_contract.py --check    # fail if it would change

**WHAT ``--check`` WRITES.** Nothing: it renders in memory and compares. This
generator needs no database -- every block is derived from source that is
already on disk: the guarantees from ``tests/_guarantees.py``, the pinned
commits from ``pyproject.toml``. The module's own registries join these
blocks when the module lands. A number or a sentence edited by hand turns
``--check`` red. CI's independent check is ``git diff --exit-code
docs/CONTRACT.md`` after a plain run.

**AND GENERATION IS NOT VERIFICATION.** Moving a sentence from a document into
a template does not stop it being hand-written -- everywhere except the holes
it is still prose nobody checks. A generated block asserts only what it
DERIVES from its values. So ``tests/test_contract_is_generated.py`` plants
values that contradict the prose and requires the prose to change; anything
that survives that plant is a fixed string, and a fixed string is marked as
design documentation rather than left looking measured.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from _guarantees import GUARANTEES, guarantee_ids  # noqa: E402

DOC = ROOT / "docs" / "CONTRACT.md"
BEGIN = "<!-- GENERATED:{name} -->"
END = "<!-- END:{name} -->"


def block_guarantees() -> str:
    rows = ["| id | what is guaranteed |", "|---|---|"]
    for gid in guarantee_ids():
        rows.append(f"| **{gid}** | {GUARANTEES[gid]} |")
    rows.append("")
    rows.append(
        f"That is {len(GUARANTEES)} guarantees. Every one of them has a fail control "
        "that has been proven to fire, and the count above is derived from the "
        "registry rather than typed here."
    )
    return "\n".join(rows)


def block_pins() -> str:
    """The two commits the connector was built against, from pyproject.toml."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    rows = ["| module | commit |", "|---|---|"]
    found = 0
    for requirement in project["optional-dependencies"]["dev"]:
        match = re.fullmatch(
            r"openparking-([a-z-]+)\[store\] @ git\+https://github\.com/openparking-ai/"
            r"([a-z-]+)@([0-9a-f]{40})",
            requirement,
        )
        if match:
            rows.append(f"| `{match.group(1)}` | `{match.group(3)}` |")
            found += 1
    rows.append("")
    rows.append(
        f"{found} module{'s are' if found != 1 else ' is'} pinned, as a DEV dependency for the "
        "tests. At runtime the connector needs the two console scripts on PATH and imports "
        "neither package; the runtime dependency list is "
        f"{'empty' if not project['dependencies'] else project['dependencies']}."
    )
    return "\n".join(rows)


BLOCKS = {
    "guarantees": block_guarantees,
    "pins": block_pins,
}


def render(template: str) -> str:
    out = template
    for name, builder in BLOCKS.items():
        begin, end = BEGIN.format(name=name), END.format(name=name)
        if begin not in out or end not in out:
            raise SystemExit(f"docs/CONTRACT.md has no {begin} ... {end} block")
        head, rest = out.split(begin, 1)
        _stale, tail = rest.split(end, 1)
        out = f"{head}{begin}\n{builder()}\n{end}{tail}"
    return out


def main(argv: list[str]) -> int:
    current = DOC.read_text()
    generated = render(current)
    if "--check" in argv:
        if current != generated:
            print(
                "docs/CONTRACT.md does not match its generator. A number or a "
                "sentence inside a generated block was edited by hand, or the "
                "registry it comes from moved. Run this script with no arguments."
            )
            return 1
        print("docs/CONTRACT.md is the generated one.")
        return 0
    DOC.write_text(generated)
    print(f"wrote {DOC.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
