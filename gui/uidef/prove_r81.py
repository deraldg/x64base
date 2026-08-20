#!/usr/bin/env python3
"""Prove the character-cell weight allocation, remainder included. R81.

The three pixel backends hand slack to a toolkit and the toolkit owns the
rounding. A character grid has no toolkit: the renderer divides a DISCRETE
resource and must own the halves itself. This authors one row whose slack is
deliberately NOT divisible by the total weight, renders it, measures the cells
each field actually occupies, and asserts the documented rule:

    floor(slack * weight / total_weight) each, remainder ONE CELL AT A TIME
    to the weighted children in ORDINAL order.

    python prove_r81.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uidef
import uidef_text

STEM = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'R81_REMAINDER')
WIDTH = 100

ROWS = [
    {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored',
     'PROPS': 'SourceFile = "R81"'},
    {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form',
     'FLOW': 'column', 'PROVENANCE': 'authored',
     'PROPS': 'Caption = "R81"'},
    {'RECKIND': 'OBJ', 'OBJID': 'R1', 'PARENT': 'F1', 'ORDINAL': '1',
     'KIND': 'panel', 'FLOW': 'row', 'PROVENANCE': 'authored'},
    {'RECKIND': 'OBJ', 'OBJID': 'A', 'PARENT': 'R1', 'ORDINAL': '1',
     'KIND': 'text', 'PROVENANCE': 'authored', 'PROPS': 'Weight = 3'},
    {'RECKIND': 'OBJ', 'OBJID': 'B', 'PARENT': 'R1', 'ORDINAL': '2',
     'KIND': 'text', 'PROVENANCE': 'authored', 'PROPS': 'Weight = 1'},
    {'RECKIND': 'OBJ', 'OBJID': 'C', 'PARENT': 'R1', 'ORDINAL': '3',
     'KIND': 'text', 'PROVENANCE': 'authored', 'PROPS': 'Weight = 1'},
]


def expected(nat, weights, avail):
    """The rule, written a second time and independently, so the assertion is a
    CHECK and not an echo of the implementation."""
    used = sum(nat) + 2 * (len(nat) - 1)
    slack = max(0, avail - used)
    total = sum(weights)
    out = [nat[i] + (slack * weights[i]) // total for i in range(len(nat))]
    rem = slack - sum(out[i] - nat[i] for i in range(len(nat)))
    for i in range(rem):
        out[i % len(out)] += 1
    return out, slack


def main():
    uidef.write(STEM + '.DBF', STEM + '.FPT', ROWS)
    txt, notes, used = uidef_text.render(STEM + '.DBF', width=WIDTH)

    for n in notes:
        if n.startswith('DROPPED Weight'):
            print('FAIL -- weight was dropped: %s' % n)
            return 1

    row = [ln for ln in txt.splitlines() if '[' in ln and ln.count('[') == 3]
    if len(row) != 1:
        print('FAIL -- expected exactly one three-field row, got %d' % len(row))
        print(txt)
        return 1
    got = [len(m) for m in re.findall(r'\[_*\]', row[0])]
    if len(got) != 3:
        print('FAIL -- could not measure three fields in: %r' % row[0])
        return 1

    # The panel is a container inside the form: the form grants `WIDTH - 3`,
    # the panel grants its own content `that - 3`.
    avail = WIDTH - uidef_text.BOX_OVERHEAD * 2
    nat = [12, 12, 12]                     # `[__________]`, the default mask
    want, slack = expected(nat, [3, 1, 1], avail)

    print('avail    %d cells for the row' % avail)
    print('natural  %s  (+ %d cells of gap)' % (nat, 2 * (len(nat) - 1)))
    print('slack    %d cells, weights 3:1:1 -- 54/5 is NOT whole' % slack)
    print('rule     %s' % want)
    print('rendered %s' % got)
    print(txt)

    if got != want:
        print('FAIL -- allocation does not follow the documented rule')
        return 1
    if sum(got) + 2 * (len(got) - 1) != avail:
        print('FAIL -- the row does not fill its budget exactly')
        return 1
    if len(set(want)) != 3:
        print('FAIL -- the case no longer exercises the remainder')
        return 1
    print('OK -- %d cells allocated, remainder %d given earliest-first'
          % (avail, slack - sum((slack * w) // 5 for w in (3, 1, 1))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
