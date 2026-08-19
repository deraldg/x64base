#!/usr/bin/env python3
"""Author a UIDEF document that describes the browse dottalk++ already ships. R66.

R65 measured `ERSATZ GRID` -- root detail, relation tree, descendant summary, tuple
grid, status footer -- and found the design table could not name a single region of
it. R66 added the five kinds. This is the first document that uses them, and it is
deliberately the SAME screen: if the language works, this document and the engine's
own frame describe the same thing.

The grid's columns span two work areas (students.lname, enroll.grade), which is the
case the whole vocabulary exists for and the case contract 10c requires a Relation
for.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uidef

SOURCE = "\n".join([
    "Alias = students",
    "Table = STUDENTS.DBF",
    "Alias = enroll",
    "Table = ENROLL.DBF",
    "Relation = students -> enroll ON SID",
])


def main(stem):
    out = [{'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored',
            'SOURCE': SOURCE,
            'PROPS': uidef.props([('SourceFile', '"ERSATZ FRAME"')])}]

    def obj(oid, parent, kind, ordinal, flow='', binding='', pairs=()):
        out.append({'RECKIND': 'OBJ', 'OBJID': oid, 'PARENT': parent, 'KIND': kind,
                    'ORDINAL': ordinal, 'FLOW': flow, 'BINDING': binding,
                    'PROVENANCE': 'authored', 'PROPS': uidef.props(list(pairs))})

    obj('F1', '', 'form', 1, flow='column',
        pairs=[('Caption', '"Relational Browser"')])

    # CURRENT ROOT RECORD -- one record as label : value. ReadOnly is stated as true
    # on purpose: contract 4b(b) refuses false, and a document that says nothing is
    # read-only anyway, so saying it is the honest form rather than the required one.
    obj('D1', 'F1', 'detail', 1, binding='students.*',
        pairs=[('Caption', '"CURRENT ROOT RECORD"'), ('ReadOnly', '.T.')])

    # RELATION TREE -- shape comes from SOURCE, so no child rows (4b(a)).
    obj('T1', 'F1', 'tree', 2, binding='students',
        pairs=[('Caption', '"RELATION TREE"')])

    # DESCENDANT SUMMARY -- per-child counts over the closure.
    obj('S1', 'F1', 'summary', 3, binding='students',
        pairs=[('Caption', '"DESCENDANT SUMMARY"')])

    # TUPLE GRID -- the columns SPAN two work areas, which is legal here only
    # because SOURCE relates them (contract 10c).
    obj('G1', 'F1', 'grid', 4,
        binding='students.lname,students.fname,enroll.cls_id,enroll.grade',
        pairs=[('Caption', '"TUPLE GRID"'), ('RowLimit', '3'),
               ('Order', '"physical"'), ('ReadOnly', '.T.')])

    # The frame's own state line.
    obj('B1', 'F1', 'statusbar', 5,
        pairs=[('Shows', '"rows limit order root recno status"')])

    nrec, rlen, hlen = uidef.write(stem + '.DBF', stem + '.FPT', out)
    print("%s.DBF records=%d rlen=%d hlen=%d" % (stem, nrec, rlen, hlen))
    print("  conformance findings:", uidef.validate(out) or "none")
    return out


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'FRAMEDEMO')
