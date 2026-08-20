#!/usr/bin/env python3
"""Author a UIDEF document that uses every FLOW value, with NO ORIGIN anywhere.

AIF-120. R19 measured that `free` is what most imported documents ARE, and closed
the question of what imports look like. It left the other three values rendered by
nothing: 11 `row` groups and 3 `column` groups in the corpus, and no consumer had
ever laid one out.

This document is pure intent -- FLOW and ORDINAL and SPAN, and not one coordinate.
If the design table's central claim is true, a target can lay this out with no
geometry at all.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uidef

def props(pairs):
    return uidef.props(pairs)

def main(stem):
    out = []
    out.append({'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored',
                'PROPS': props([('SourceFile', '"FLOWDEMO"'),
                                ('Contract', '"AIF120-UIDEF-V1"')])})
    def obj(oid, parent, kind, ordinal, flow='', span='', pairs=()):
        out.append({'RECKIND': 'OBJ', 'OBJID': oid, 'PARENT': parent, 'KIND': kind,
                    'ORDINAL': ordinal, 'FLOW': flow, 'SPAN': span,
                    'PROVENANCE': 'authored', 'PROPS': props(list(pairs))})

    obj('F1', '', 'form', 1, flow='column',
        pairs=[('Caption', '"FLOW demo -- no coordinates anywhere"')])

    # a ROW of buttons
    obj('P1', 'F1', 'panel', 1, flow='row')
    for i, cap in enumerate(('First', 'Prior', 'Next', 'Last'), start=1):
        obj('B%d' % i, 'P1', 'button', i, pairs=[('Caption', '"%s"' % cap)])

    # a COLUMN of checks
    obj('P2', 'F1', 'panel', 2, flow='column')
    for i, cap in enumerate(('Taxable', 'Active', 'Archived'), start=1):
        obj('C%d' % i, 'P2', 'check', i, pairs=[('Caption', '"%s"' % cap)])

    # a GRID: two columns of label + field, and one control that SPANs both
    # `Columns` states where the grid wraps. Section 5 says `grid` wraps and never
    # says at what width, so a target that is not allowed to default an absent
    # dimension has to be told. G2 below omits it on purpose.
    obj('G1', 'F1', 'group', 3, flow='grid',
        pairs=[('Caption', '"Grid, Columns = 2, one spanning row"'),
               ('Columns', '2')])
    pairs = (('Last name', 'T1'), ('First name', 'T2'), ('Major', 'T3'))
    n = 0
    for lbl, tid in pairs:
        n += 1
        obj('L%d' % n, 'G1', 'label', n * 2 - 1, pairs=[('Caption', '"%s"' % lbl)])
        obj(tid, 'G1', 'text', n * 2)
    obj('T9', 'G1', 'text', 7, span='2')     # spans both grid columns

    # a GRID that does not say where it wraps -- must be refused, not guessed
    obj('G2', 'F1', 'group', 4, flow='grid',
        pairs=[('Caption', '"Grid with no Columns -- must be refused"')])
    for i, cap in enumerate(('alpha', 'beta', 'gamma'), start=1):
        obj('X%d' % i, 'G2', 'label', i, pairs=[('Caption', '"%s"' % cap)])

    # a FREE group with no ORIGIN at all -- the degenerate case the contract allows
    obj('P3', 'F1', 'panel', 5, flow='free')
    obj('L9', 'P3', 'label', 1,
        pairs=[('Caption', '"free with no ORIGIN: order is all a target has"')])

    nrec, rlen, hlen = uidef.write(stem + '.DBF', stem + '.FPT', out)
    print("%s.DBF records=%d rlen=%d hlen=%d" % (stem, nrec, rlen, hlen))
    v = uidef.validate(out)
    print("  conformance findings:", v if v else "none")
    print("  rows carrying ORIGIN (this document must have 0):",
          len([r for r in out if r.get('ORIGIN')]))
    flows = {}
    for r in out:
        f = (r.get('FLOW') or '').strip()
        if f:
            flows[f] = flows.get(f, 0) + 1
    print("  FLOW values exercised:", flows)
    return out

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'FLOWDEMO')
