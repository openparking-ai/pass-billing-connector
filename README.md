# Open Parking AI — pass-billing connector

**For each stated link — a garage pass on one side, an outside-registrar
agreement in monthly billing on the other — on the day given, make billing's
register for that agreement equal the pass's live register, and say loudly
whatever cannot be made equal.** That one question, and nothing else.

This is the furniture: the guard on the guarantees, the generated contract,
the fail controls and the CI that runs them, copied from `monthly-billing` so
there is one shape and not two. The module lands by pull request.

## No database

The connector will have **no database of its own**: it drives
`openparking-ai/garage-pass` and `openparking-ai/monthly-billing` through
their command lines as subprocesses, imports neither package, opens no
connection and holds no DSN. So there is no `migrations/` directory here and
no row-level-security guard copied from the modules — a guard with nothing to
guard that passes on nothing is a vacuous green, and the CI does not carry
one. The guarantee that there is nothing to guard is stated, tested and
proven able to fail like every other, when the module lands.

## Every guarantee has a control that has been proven to fire

```
python scripts/fail_controls.py --anchors   # every anchor is live, in a second
python scripts/fail_controls.py             # break each guarantee, require RED
```

The guarantees and the pinned commits are generated into `docs/CONTRACT.md`
from the registry and from `pyproject.toml`. No number in it is typed.

## Install

```
pip install -e .              # the connector: no dependencies at all
pip install -e '.[dev]'       # plus pytest, ruff and the two modules at their pinned commits
```

Python 3.11 or newer.

## Contributing

Contributions are welcome under the CLA. See `CONTRIBUTING.md` and `CLA.md`.

## Licence

AGPL-3.0-or-later. See `LICENSE`.

Built by 72 Knots Method by 72Knots.ai
