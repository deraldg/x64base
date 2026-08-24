#!/usr/bin/env python3
"""Fixtures for the R-number allocator and gate.

EVERY GATE IS SEEN TO FAIL ON A KNOWN-BAD INPUT BEFORE ITS GREEN IS TRUSTED.
That rule was earned in the AIF-090 D1-D4 repairs, where a bound written
specifically so a number could fail turned out to be anchored to a stale
constant and could not fire. A gate that has only ever been observed passing is
indistinguishable from a gate that cannot fail.

    python tools/coordination/test_r_gate.py
"""
from __future__ import annotations

import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import next_r            # noqa: E402
import r_collision_gate  # noqa: E402

FAILURES: list[str] = []


def check(name: str, got, want) -> None:
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}: got {got!r}")
    if not ok:
        FAILURES.append(f"{name}: got {got!r}, want {want!r}")


def with_register(text: str):
    """Point BOTH modules at a fixture register. Both, deliberately: the gate
    imports the allocator's population, and a test that repointed only one
    would prove the two agree when they had not been asked the same question."""
    tmp = pathlib.Path(tempfile.mkdtemp()) / "R_REG.md"
    tmp.write_text(text, encoding="utf-8")
    next_r.REGISTER = tmp
    r_collision_gate.REGISTER = tmp
    return tmp


GOOD = """| R | date | kind | lane |
|---|---|---|---|
| R1 | -- | doctrine | AIF-078 |
| R7 | 2026-08-06 | ruling | AIF-090 |
| R119 | 2026-08-24 | ruling | AIF-078 |
"""

DUPE = GOOD + "| R7 | 2026-08-24 | ruling | AIF-078 | oops |\n"

PADDED = """| R095 | -- | ruling | x |
| R95 | -- | ruling | x |
"""


def main() -> int:
    print("=== R gate fixtures ===")

    print("\n1. clean register -- the gate must NOT fire")
    with_register(GOOD)
    check("duplicates found", r_collision_gate.duplicate_rows(), [])
    check("declared set", sorted(next_r.declared()), [1, 7, 119])

    print("\n2. duplicate declared row -- the gate MUST fire (this is the "
          "known-bad input)")
    with_register(DUPE)
    check("duplicates found", r_collision_gate.duplicate_rows(), [7])

    print("\n3. zero-padding is display, not identity -- R095 and R95 are the "
          "SAME number, so this register declares one number twice")
    with_register(PADDED)
    check("R095 and R95 collapse", sorted(next_r.declared()), [95])
    check("and are seen as a duplicate", r_collision_gate.duplicate_rows(), [95])

    print("\n4. a passing MENTION is not a declaration -- only the first cell "
          "of a row declares")
    with_register("| R1 | -- | doctrine | x |\n\nProse discussing R112 and R7.\n")
    check("declared set", sorted(next_r.declared()), [1])

    print("\n5. THE R7 SHAPE: a number new to the register but already cited "
          "elsewhere in the tree")
    fresh = [7, 120]
    cited_elsewhere = {7, 110, 112}          # what the tree carries
    stolen = sorted(n for n in fresh if n in cited_elsewhere)
    check("stolen numbers", stolen, [7])
    check("R120 survives", 120 in stolen, False)

    print("\n6. THE FIRST-USE FALSE POSITIVE, which a whole-tree comparison "
          "would have produced on the very next commit")
    # Declaring R119 and citing it at its code sites in the SAME change is the
    # correct flow -- allocate, declare, cite. A gate that compared against the
    # whole working tree would see the change's own citations and hard-fail it.
    fake_map = {
        "docs/ai-friendly/R_RULING_REGISTER_V1.md": {119, 7, 1},   # the register
        "include/xbase_64.hpp": {119},        # cited BY this change
        "src/xbase/dbf_create.cpp": {119},    # cited BY this change
        "docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md": {7},       # pre-existing
    }
    r_collision_gate.cited_map = lambda: fake_map
    r_collision_gate.REGISTER_REL = "docs/ai-friendly/R_RULING_REGISTER_V1.md"
    changed = {"docs/ai-friendly/R_RULING_REGISTER_V1.md",
               "include/xbase_64.hpp", "src/xbase/dbf_create.cpp"}

    elsewhere = r_collision_gate.occupied_elsewhere(changed)
    check("R119 is NOT occupied elsewhere", 119 in elsewhere, False)
    check("R7 IS occupied elsewhere", 7 in elsewhere, True)

    # And the naive version, kept so the difference is visible rather than
    # asserted: comparing against every file would have flagged R119.
    naive = set()
    for rel, nums in fake_map.items():
        if rel != "docs/ai-friendly/R_RULING_REGISTER_V1.md":
            naive |= nums
    check("the naive whole-tree compare WOULD have flagged R119",
          119 in naive, True)

    print("\n7. SEEDING the register: base high-water is 0, so every row is an "
          "allocation and none needs a marker")
    seed = [(1, "| R1 | -- | doctrine | AIF-078 |"),
            (7, "| R7 | 2026-08-06 | ruling | AIF-090 |"),
            (119, "| R119 | 2026-08-24 | ruling | AIF-078 |")]
    check("blocked rows", r_collision_gate.unmarked_allocations(seed, 0), [])

    print("\n8. a normal ALLOCATION above the high-water needs no marker")
    check("blocked rows",
          r_collision_gate.unmarked_allocations(
              [(120, "| R120 | 2026-08-25 | ruling | x |")], 119), [])

    print("\n9. THE R7 SHAPE ITSELF -- a decision made NOW claiming a number "
          "that has already passed. MUST fire.")
    check("blocked rows",
          r_collision_gate.unmarked_allocations(
              [(7, "| R7 | 2026-08-24 | ruling | AIF-078 | autoq stays unwired |")],
              119),
          [7])

    print("\n10. the SAME number, declared as a back-fill and saying so. "
          "MUST NOT fire -- back-filling is what the register asks for.")
    check("blocked rows",
          r_collision_gate.unmarked_allocations(
              [(7, "| R7 | 2026-08-06 | ruling (backfill) | AIF-090 | CONVERT |")],
              119),
          [])

    print("\n11. a back-fill marker does NOT license a fresh number to skip "
          "the allocator -- it is only consulted at or below the high-water")
    check("R120 with a stray marker still passes (it is an allocation)",
          r_collision_gate.unmarked_allocations(
              [(120, "| R120 | -- | ruling (backfill) | x |")], 119), [])

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print("  " + f)
        return 1
    print("all fixtures pass, including the five that had to fail first")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
