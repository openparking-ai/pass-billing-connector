# Contributing to Open Parking AI

Contributions are welcome. This page is short on purpose; everything on it is
enforced mechanically, so there is nothing to remember.

## Before your first pull request: sign the CLA

Read [CLA.md](CLA.md), then open a pull request that adds one entry to
`cla/signatures.json` and changes nothing else:

```json
{ "github": "your-github-login", "name": "Your Full Legal Name", "date": "YYYY-MM-DD" }
```

That pull request is your signature. Once it is merged, your later pull requests
pass the CLA check automatically.

The CLA grants 72 Knots the right to relicense contributions. Section 3 of
[CLA.md](CLA.md) explains why in plain terms. If you are not comfortable with
that clause, please do not contribute — it is not negotiable, and it is better
to know before you spend time on a change.

## How a change gets in

1. Open an issue first for anything larger than a fix. Agreeing on the approach
   is cheaper than reviewing the wrong one.
2. Branch from `main`. Nobody pushes to `main` directly; the branch protection
   refuses it.
3. Open a pull request. Six checks must be green before it can merge: `lint`,
   `test`, `controls`, `docs`, `emails` and `cla`.
4. A maintainer reviews and merges. Opening the pull request is not merging it.

## What gets rejected on sight

**Real personal data, anywhere in the repository.** Fixtures, tests, documents
and examples use invented values — `example.com` addresses, made-up names, plates
that belong to nobody. This applies to git metadata too: commit with a masked
address, not a personal one. The running system stores real vehicle identity;
that is the product, it is governed by retention, and it is a different thing
from what is committed here. Two CI guards enforce it and both ship with a
self-test that proves they can fail.

**Anything personal in the report.** Ids, garages, days, vehicle identities and
stored forms are the whole of what a run prints. A holder's name, phone or
address reaches no read the connector makes, and nothing here may add a field
the reads did not return.

**A dependency on Open Parking AI's platform, or on any hosted service.** This
connector is standalone by definition: it runs with the two console scripts on
PATH and nothing else. A module that reaches for our platform to do its job has
stopped being standalone, and a remote call on the reconciliation path is out
of the question whoever it is to.

**A test that has never been seen to fail.** If you add a control, show it
failing when the thing it protects is removed. The boundary guard in the
lane-controller repository ships with planted positive controls as the worked
example.

**A silent guess.** A link is stated in the links document or it does not
exist; the connector never infers one from matching ids. A stored form comes
from monthly billing's own answer or it is not known; the connector never
reimplements the normalisation that produces it.

**A change to either module from here.** The connector is built against
`garage-pass` and `monthly-billing` at the commits `pyproject.toml` pins and
reaches them through their command lines only. If something here cannot be
built without a change there, that is a finding to report in that repository,
not a patch to carry in this one.

## Style

Match the code already there — its naming, its comment density, its idioms. A
change that reads like the file it lands in is easier to review than a better
one that does not.

Comments should say why, not what.

---

Built by 72 Knots Method by 72Knots.ai
