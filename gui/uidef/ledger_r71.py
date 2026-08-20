#!/usr/bin/env python3
"""AIF-120 R71 -- add this ruling's three rows to the lane ledger.

Why this is a script and not a hand edit: R70 and R71 both amend
AIF120_LANE_STATUS_AND_FIXTURES_V1.md, and R70 commits first. If R71's index row
were already in the file at R70's commit, that commit would ship a ledger citing
AIF120_PROJECT_PROMOTION_V1.md while the document itself is unstaged -- a
cited-paths widow, which is exactly the failure R69's commit caught for R66, R67
and R68. So the R71 rows are applied here, in the R71 sequence, after R70 is in.

Run from the repo root, in the R71 commit, before `git add docs/maintenance`.
Idempotent: refuses if the rows are already present, refuses if R70's anchor rows
are missing. Asserts the result rather than trusting the exit code.
"""
import os
import sys

LEDGER = 'docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md'

INDEX_ANCHOR = (
    '| **R70** -- the generated grid binds `DbTupleStream`; running it found a '
    'relation the document declared and the runtime never made, and a star spec '
    'that dropped every field after the first | '
    '`docs/maintenance/AIF120_GRID_STREAM_BINDING_V1.md` |\n'
)
INDEX_ROW = (
    '| **R71** -- UIDEF promoted from lane to `project.x64base.gui`; the registry '
    'already said where a non-C++ product goes, and the move is a promotion under '
    'AIF-040 rather than a tidy-up | '
    '`docs/maintenance/AIF120_PROJECT_PROMOTION_V1.md` |\n'
)

RANGE_OLD = '| Rulings **R13 through R70** live'
RANGE_NEW = '| Rulings **R13 through R71** live'

LESSON_ANCHOR = '| R70 | a rule that is CHECKED on a declaration'
LESSON_ROW = (
    '| R71 | where a thing lives is a doctrine question the tree usually already '
    'answers -- and a migration\'s real bill is the prose nobody executes '
    '| AIF-040 promotes a lane that "spawns sub-lanes, gains an independent '
    'lifecycle, or becomes a program others build under", and AIF-120 met all '
    'three before the question was asked; `projects.yaml` roots FOUR non-C++ '
    'products inside ccode -- `pycrud`, `dottalk-webui`, `sqlite-gui` '
    '(`kind: gui_project`) and `bindings/pydottalk` -- and roots ZERO outside it, '
    'so "ccode implies C++" is a fair reading of the name and not a description '
    'of the tree; the premise "it\'s not C++ code" measured 13 `.cpp` and 2 `.h` '
    'out of 53 files, a quarter, which is why a Python-product home under '
    '`bindings/` would have been wrong too; NOTHING executable references '
    '`gui/uidef` -- not CMake, not the gates, not the registries -- so the '
    'entire cost is 251 citations in 54 documents PLUS 31 self-references inside '
    'the tooling\'s own usage strings and build comments, which I missed on the '
    'first pass and printed "empty means the move cannot break the tools" '
    'directly above the thirty-one lines that said otherwise; and the move and '
    'the citation rewrite must be ONE commit or the citation gate sees 55 widows '
    'in between |\n'
)


def main():
    if not os.path.isfile(LEDGER):
        print('REFUSED: %s not found -- run from the repo root.' % LEDGER)
        return 2

    with open(LEDGER, 'r', encoding='utf-8', newline='') as fh:
        s = fh.read()

    if '**R71**' in s:
        print('REFUSED: an R71 row is already present. Nothing done.')
        return 2
    if s.count(INDEX_ANCHOR) != 1:
        print('REFUSED: R70 index row not found exactly once -- commit R70 first.')
        return 2
    if s.count(LESSON_ANCHOR) != 1:
        print('REFUSED: R70 lesson row not found exactly once.')
        return 2
    if RANGE_OLD not in s:
        print('REFUSED: the "R13 through R70" range line is not as expected.')
        return 2

    s = s.replace(INDEX_ANCHOR, INDEX_ANCHOR + INDEX_ROW)
    s = s.replace(RANGE_OLD, RANGE_NEW)
    s = s.replace(LESSON_ANCHOR, LESSON_ROW + LESSON_ANCHOR)

    with open(LEDGER, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(s)

    # Assert the result. A zero exit code is not proof (Tier 1 seed, s4).
    with open(LEDGER, 'r', encoding='utf-8') as fh:
        t = fh.read()
    ok = (t.count(INDEX_ROW) == 1 and t.count(LESSON_ROW) == 1
          and RANGE_NEW in t and RANGE_OLD not in t)
    bad = [c for c in t if ord(c) > 127]
    if not ok:
        print('FAIL: rows did not land as expected.')
        return 1
    if bad:
        print('FAIL: %d non-ASCII character(s) present.' % len(bad))
        return 1
    print('VERIFIED: R71 index row, lesson row and range line applied; ASCII clean.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
