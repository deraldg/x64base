#!/usr/bin/env python3
"""Read a `.VCX` as a CLASS LIBRARY. AIF-120, R31 -- mechanism A of R30.

R30 separated two mechanisms behind the dotted property names on an object:

  B  inline composition -- the members are on the composite. Implemented in R30.
  A  inheritance -- the object is an INSTANCE of a class defined in a `.VCX`,
     and the dotted properties are OVERRIDES to that class's members.

A is 637 member names behind 118 class references in the corpus, and until now the
lane had measured `.VCX` as a container and never read one as a library.

STRUCTURE, measured on `solution.vcx` (52 records, 12 class blocks):

    rec 10  WINDOWS  vcr           PARENT=            RESERVED2=6
    rec 11  WINDOWS  cmdTop        PARENT=vcr
    rec 12  WINDOWS  cmdPrior      PARENT=vcr
    rec 13  WINDOWS  cmdNext       PARENT=vcr
    rec 14  WINDOWS  cmdBottom     PARENT=vcr
    rec 15  WINDOWS  Datachecker1  PARENT=vcr
    rec 16  COMMENT  vcr                                <- block terminator

A library is a sequence of BLOCKS. A block is one root record whose `PARENT` is
empty and whose `RESERVED2` is the number of records in the block including
itself, then `RESERVED2 - 1` members, then a `COMMENT` record repeating the name.
Verified on every block in the file: 1, 1, 1, 1, 6, 5, 7, 1, 1, 7, 1, 7.

Resolution is by BLOCK, not by name. `solution.vcx` holds three blocks named
`frmsolution`; two are DELETED and one is live. Matching on name alone picks an
arbitrary one -- the same trap R18 found in `.MNX`, where the fix was also
"position and a declared count, never a field that can repeat or be blank".

31% of `.VCX` records in this corpus are deleted, against 0% of `.SCX`, `.MNX` and
`.FRX`. That is why nothing in this lane had to care about the deleted flag until
it opened a class library.
"""
import os


def read_library(path, dbf_reader):
    """Return {classname_lower: block} for every LIVE class in a .VCX.

    `block` is {'name', 'baseclass', 'root', 'members'} where members are raw
    records. A later live block with the same name wins, which is what VFP's
    append-on-edit behaviour means.
    """
    rows = list(dbf_reader(path).rows())
    classes = {}
    i = 0
    n = len(rows)
    while i < n:
        r = rows[i]
        plat = (r.get('PLATFORM') or '').strip().upper()
        parent = (r.get('PARENT') or '').strip()
        if plat == 'COMMENT' or parent:
            i += 1
            continue
        try:
            count = int(float((r.get('RESERVED2') or '0').strip() or 0))
        except ValueError:
            count = 1
        count = max(count, 1)
        block = rows[i:i + count]
        i += count
        if r.get('_DELETED'):
            continue                      # an edited class leaves its old block behind
        name = (r.get('OBJNAME') or '').strip()
        members = [m for m in block[1:] if not m.get('_DELETED')]
        # RESERVED2 is a declared count, so check it -- R13's principle again.
        declared_ok = len(block) == count
        classes[name.lower()] = {
            'name': name,
            'baseclass': (r.get('BASECLASS') or '').strip().lower(),
            'root': r,
            'members': members,
            'declared': count,
            'declared_ok': declared_ok,
        }
    return classes


def resolve_classloc(classloc, document_path):
    """Where a `CLASSLOC` points, relative to the DOCUMENT (4b, R12).

    Returns (path_or_None, reason). An absolute path is refused rather than
    tried: measured, the corpus is 412 relative and 0 absolute, and the only
    absolute values in this lane are in fixtures it generated itself, pointing
    into a vendor install on a machine that is not the reader's.
    """
    cl = (classloc or '').strip()
    if not cl:
        return None, 'no CLASSLOC'
    norm = cl.replace('\\', '/')
    if len(norm) > 1 and norm[1] == ':' or norm.startswith('//'):
        return None, 'absolute path -- addressing is relative to the document (4b)'
    base = os.path.dirname(os.path.abspath(document_path))
    cand = os.path.normpath(os.path.join(base, norm))
    if os.path.exists(cand):
        return cand, 'ok'
    # case-insensitive retry: R28.3 ruled this for SOURCE.Table and the same
    # argument applies here -- the source was written on a case-folding filesystem.
    d, want = os.path.dirname(cand), os.path.basename(cand).lower()
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.lower() == want:
                return os.path.join(d, f), 'ok (case-insensitive)'
    return None, 'not found relative to the document'
