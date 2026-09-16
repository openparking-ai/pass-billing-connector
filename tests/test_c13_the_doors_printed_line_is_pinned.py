"""C13 -- the door's printed line is pinned.

`  at garage {garage}: {form}` is the one piece of prose the connector reads.
It is matched against garage ids the register read already named, so the
form after the garage may contain anything -- `: ` included -- a garage id
that is a prefix of another claims no line, and a line naming no known
garage makes the whole answer unparseable rather than half-read.

The database half runs the real door at the pinned commit and asserts the
exact lines, so a change there reddens this repository before it mis-parses.
"""

from __future__ import annotations

import pytest

from harness import needs_databases, standard_world
from pass_billing_connector import doors
from pass_billing_connector.doors import STORED_FORM_LINE, stored_forms

#: Three ids, one of which CONTAINS the separator and starts with another --
#: the one shape where "which garage is this line's" is ambiguous, and the
#: reason the parser tries the longest known id first.
GARAGES = ("garage-a", "garage-b", "garage-a: 2")


@pytest.mark.guarantee("C13")
def test_the_pinned_line_is_the_published_one():
    assert STORED_FORM_LINE == "  at garage {garage}: {form}"


@pytest.mark.guarantee("C13")
def test_a_well_formed_answer_is_read_per_garage():
    out = ("vehicle registered to agreement ag-1\n"
           "  at garage garage-a: ab123\n  at garage garage-b: AB-123\n")
    assert stored_forms(out, GARAGES) == {"garage-a": "ab123", "garage-b": "AB-123"}


@pytest.mark.guarantee("C13")
def test_a_form_may_contain_the_separator_itself():
    out = "released\n  at garage garage-b: odd: form: here\n"
    assert stored_forms(out, GARAGES) == {"garage-b": "odd: form: here"}


@pytest.mark.guarantee("C13")
def test_a_garage_id_that_is_a_prefix_of_another_claims_no_line():
    """`garage-a: 2` begins with `garage-a` followed by the separator, so a
    first-match parse would read its line as garage-a's with the form
    `2: x1`. The longest known id is tried first, so it is not."""
    out = "registered\n  at garage garage-a: 2: x1\n  at garage garage-a: x2\n"
    assert stored_forms(out, GARAGES) == {"garage-a: 2": "x1", "garage-a": "x2"}
    # And an ordinary prefix -- no separator inside the id -- never needed the
    # sort: the separator itself keeps `garage-a` off `garage-a-2`'s line.
    plain = ("garage-a", "garage-a-2")
    out = "registered\n  at garage garage-a-2: x1\n  at garage garage-a: x2\n"
    assert stored_forms(out, plain) == {"garage-a-2": "x1", "garage-a": "x2"}


@pytest.mark.guarantee("C13")
@pytest.mark.parametrize("out", [
    "registered\n  at garage garage-z: x\n",          # a garage the read did not name
    "registered\nat garage garage-a: x\n",             # the indent is part of the line
    "registered\n  at garage garage-a: x\n  at garage garage-a: y\n",  # a garage twice
    "registered\n  AT GARAGE garage-a: x\n",
    "",
])
def test_a_line_of_another_shape_makes_the_answer_unparseable(out):
    assert stored_forms(out, GARAGES) is None


@pytest.mark.guarantee("C13")
def test_an_answer_with_no_garage_lines_is_empty_not_unparseable():
    assert stored_forms("vehicle registered to agreement ag-1\n", GARAGES) == {}


# ------------------------------------------------------------ the database


@needs_databases
@pytest.mark.guarantee("C13")
def test_the_real_door_prints_exactly_the_pinned_lines(pair):
    standard_world(pair)
    out = pair.mb_register("ag-1", "AB-123").stdout
    assert out == ("vehicle registered to agreement ag-1\n"
                   "  at garage garage-a: ab123\n"
                   "  at garage garage-b: AB-123\n")
    out = pair.mb_release("ag-1", "AB-123").stdout
    assert out == ("vehicle released from agreement ag-1\n"
                   "  at garage garage-a: ab123\n"
                   "  at garage garage-b: AB-123\n")


@needs_databases
@pytest.mark.guarantee("C13")
def test_the_door_module_reads_the_real_answer(pair, monkeypatch):
    standard_world(pair)
    for key, value in pair.env.items():
        if key.endswith("_DSN"):
            monkeypatch.setenv(key, value)
    answer = doors.register_vehicle(pair.mb_tenant, "ag-1", "AB-123",
                                    "2026-09-16T09:00:00-06:00", ("garage-a", "garage-b"))
    assert answer.outcome == "done"
    assert answer.stored == {"garage-a": "ab123", "garage-b": "AB-123"}
