#!/usr/bin/env python3
"""Author a UIDEF document whose objects select DIFFERENT fonts. AIF-120, R24.

`FONTREF` had been written by the importer and read by nobody. Every in-repo
fixture declares no font at all, so nothing in the lane could show the mechanism
working. This document selects three fonts by index, and one object deliberately
selects a FONT row that does not exist.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uidef


def main(stem):
    out = [{'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored',
            'PROPS': uidef.props([('SourceFile', '"FONTDEMO"')])}]
    specs = [('Helvetica', 16), ('Courier', 11), ('Times', 13)]
    for i, (fam, size) in enumerate(specs, 1):
        out.append({'RECKIND': 'FONT', 'OBJID': 'FONT%d' % i, 'ORDINAL': i,
                    'PROVENANCE': 'authored',
                    'PROPS': uidef.props([('Name', '"%s"' % fam), ('Size', str(size))])})
    out.append({'RECKIND': 'OBJ', 'OBJID': 'F1', 'PARENT': '', 'KIND': 'form',
                'ORDINAL': 1, 'FLOW': 'column', 'PROVENANCE': 'authored',
                'PROPS': uidef.props([('Caption', '"FONTREF demo"')])})
    n = 0
    for i, (fam, size) in enumerate(specs, 1):
        n += 1
        out.append({'RECKIND': 'OBJ', 'OBJID': 'L%d' % n, 'PARENT': 'F1',
                    'KIND': 'label', 'ORDINAL': n, 'FONTREF': i,
                    'PROVENANCE': 'authored',
                    'PROPS': uidef.props([('Caption', '"FONTREF %d -- %s %d"'
                                          % (i, fam, size))])})
    n += 1
    out.append({'RECKIND': 'OBJ', 'OBJID': 'L%d' % n, 'PARENT': 'F1', 'KIND': 'label',
                'ORDINAL': n, 'FONTREF': 0, 'PROVENANCE': 'authored',
                'PROPS': uidef.props([('Caption', '"FONTREF 0 -- the target default"')])})
    n += 1
    out.append({'RECKIND': 'OBJ', 'OBJID': 'L%d' % n, 'PARENT': 'F1', 'KIND': 'label',
                'ORDINAL': n, 'FONTREF': 9, 'PROVENANCE': 'authored',
                'PROPS': uidef.props([('Caption', '"FONTREF 9 -- no such FONT row"')])})
    nrec, rlen, hlen = uidef.write(stem + '.DBF', stem + '.FPT', out)
    print("%s.DBF records=%d rlen=%d hlen=%d" % (stem, nrec, rlen, hlen))
    v = uidef.validate(out)
    print("  conformance findings:", v if v else "none")
    return out


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'FONTDEMO')
