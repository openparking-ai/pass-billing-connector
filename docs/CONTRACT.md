# The contract — Open Parking AI pass-billing connector

What this module guarantees, in sentences somebody could act on. The marked
blocks below are GENERATED (`scripts/generate_contract.py`) from the registry
in `tests/_guarantees.py` and from `pyproject.toml`; CI fails when the
document and its generator disagree. Nothing in a generated block is typed by
hand.

`main` carries the furniture: the guard on the guarantees, the generated
contract, the fail controls and the CI that runs them. The module itself
lands by pull request, and its own registries join the blocks below when it
does.

## The pinned modules

<!-- GENERATED:pins -->
| module | commit |
|---|---|
| `garage-pass` | `bc46752d2f81309495422c18008921dfec2d10a0` |
| `monthly-billing` | `5f368ce3f3d3604754db65a86c12a0d1a487c638` |

2 modules are pinned, as a DEV dependency for the tests. At runtime the connector needs the two console scripts on PATH and imports neither package; the runtime dependency list is empty.
<!-- END:pins -->

## The guarantees

<!-- GENERATED:guarantees -->
| id | what is guaranteed |
|---|---|
| **C1** | Every test module contributes at least one registered guarantee, derived from the filesystem and read from the AST -- so a module cannot be added, skipped or deleted without a guard noticing. A module that PLANTS a defect may not be excused at all. |
| **C2** | docs/CONTRACT.md is GENERATED from this registry and from the code that implements it -- the pinned commits today, the module's own registries when it lands -- and its prose is derived rather than fixed: a value that contradicts a published sentence changes the sentence, because generation is not verification. |

That is 2 guarantees. Every one of them has a fail control that has been proven to fire, and the count above is derived from the registry rather than typed here.
<!-- END:guarantees -->

---

Built by 72 Knots Method by 72Knots.ai
