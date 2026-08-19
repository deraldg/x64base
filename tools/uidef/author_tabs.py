#!/usr/bin/env python3
"""Author a UIDEF document with a `pageset` and two `page` children. AIF-120, R24.

`pageset` is in the contract's KIND vocabulary and `import_scx.py` has always
mapped VFP's `pageframe` onto it, but `uidef_tk.py` had no factory for it -- so the
reference consumer refused every tabbed form it was handed. manifest.py found that
on its first run, against `form1.scx`.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uidef


def main(stem):
    out = [{'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored',
            'PROPS': uidef.props([('SourceFile', '"TABDEMO"')])}]

    def obj(oid, parent, kind, ordinal, flow='', pairs=()):
        out.append({'RECKIND': 'OBJ', 'OBJID': oid, 'PARENT': parent, 'KIND': kind,
                    'ORDINAL': ordinal, 'FLOW': flow, 'PROVENANCE': 'authored',
                    'PROPS': uidef.props(list(pairs))})

    obj('F1', '', 'form', 1, flow='column', pairs=[('Caption', '"pageset demo"')])
    obj('PS', 'F1', 'pageset', 1, flow='free')
    obj('PG1', 'PS', 'page', 1, flow='column', pairs=[('Caption', '"Student"')])
    obj('PG2', 'PS', 'page', 2, flow='row', pairs=[('Caption', '"Enrolment"')])
    for i, cap in enumerate(('Last name', 'First name'), start=1):
        obj('A%d' % i, 'PG1', 'label', i, pairs=[('Caption', '"%s"' % cap)])
    for i, cap in enumerate(('Add', 'Drop', 'Swap'), start=1):
        obj('B%d' % i, 'PG2', 'button', i, pairs=[('Caption', '"%s"' % cap)])

    nrec, rlen, hlen = uidef.write(stem + '.DBF', stem + '.FPT', out)
    print("%s.DBF records=%d rlen=%d hlen=%d" % (stem, nrec, rlen, hlen))
    print("  conformance findings:", uidef.validate(out) or "none")
    return out


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'TABDEMO')
