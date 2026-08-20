#!/usr/bin/env python3
"""Read a DTSHEMA workspace the way the engine reads one. AIF-120 R83.

R82 ruled that LOCATION is a workspace fact, and R82.3 corrected which workspace:
a `DTSHEMA 2` row declares WHICH table, not WHERE. `dbf=STUDENTS.dbf` is a bare
name the engine resolves against `Slot::DBF`, which `SETPATH` sets -- the ambient
state contract section 10 forbids. `DTSHEMA 3` records `DBFROOT`, `IDXROOT` and
`LMDBROOT` and resolves against those instead, which is why it and not v2 can
satisfy section 10.

This reader encodes that difference rather than smoothing it: a v2 workspace
returns `dbf_root is None` and every resolution through it reports UNRESOLVED.
A reader that quietly fell back to an environment variable would reproduce the
exact defect R82 exists to name.

Written from the engine, not from a sample -- `src/cli/cmd_workspace.cpp`,
`schema_load_from_stream` at :1800 and the v3 writer at :1542. Two behaviours
come from there and would not have been guessable:

  * ROOT LINES APPLY IN LINE ORDER. `DBFROOT` re-points resolution for the AREA
    lines that FOLLOW it (:1759). The writer always emits roots first, so in
    practice it does not show; a hand-edited posture with them reordered means
    what the engine says it means, not what looks tidy.
  * AN INDEX RESOLVES AGAINST IDXROOT FIRST AND FALLS BACK TO DBFROOT (:1820),
    and only if the first candidate EXISTS. A table gets no such fallback.

NOT YET CHECKED AGAINST A REAL v3 FILE. Every `.dtschema` in the tree is v2 --
v3 is opt-in through a trailing `V3` on `WORKSPACE SAVE` and nothing has used it.
`selftest()` builds a synthetic v3 and proves the parse, which is a proof about
this reader and NOT about the engine's output. Section R83 open.

    python workspace.py <file.dtschema>     # dump what it read
    python workspace.py --selftest
"""
import os
import sys


class Area(object):
    __slots__ = ('n', 'dbf', 'index', 'indextype', 'tag', 'alias')

    def __init__(self, n, dbf, index, indextype, tag, alias):
        self.n, self.dbf, self.index = n, dbf, index
        self.indextype, self.tag, self.alias = indextype, tag, alias

    def __repr__(self):
        return 'Area(%d, %r, alias=%r, tag=%r)' % (self.n, self.dbf, self.alias, self.tag)


NONE_WORDS = ('', 'none')


def ci_path(p):
    """Contract 10: resolution is CASE-INSENSITIVE (R28.3).

    On Windows the filesystem grants that for free and this function is a
    normpath. On Linux it is the whole rule -- the corpus says `STUDENTS.DBF`
    and the tables on disk are `STUDENTS.dbf`, so an exact-match resolver
    reports every table missing and looks like a policy finding rather than a
    filename mistake. This lane has walked into that four times in one session
    and a resolver that did not implement section 10's own case rule was going
    to be the fifth. Measured here, not cited: `ls` says `STUDENTS.dbf`, the
    corpus says `STUDENTS.DBF`, and the fixture set proves the difference.

    Returns the real on-disk path when a case-insensitive match exists, and the
    normalized requested path when it does not -- so the caller's `os.path.exists`
    still answers False and the message still names what was asked for.
    """
    p = os.path.normpath(p)
    if os.path.exists(p):
        return p
    d, base = os.path.split(p)
    if not d or not os.path.isdir(d):
        return p
    low = base.lower()
    for entry in os.listdir(d):
        if entry.lower() == low:
            return os.path.join(d, entry)
    return p


class Workspace(object):
    """A parsed posture. `dbf_root is None` means the file does not say where."""

    def __init__(self, path=None):
        self.path = path
        self.version = 0
        self.wsid = None
        self.flavor = None
        self.dbf_root = None
        self.idx_root = None
        self.lmdb_root = None
        self.areas = []
        self.notes = []

    @property
    def self_locating(self):
        """True when the FILE says where its tables are -- contract 10's test."""
        return self.dbf_root is not None

    def by_alias(self, alias):
        a = (alias or '').strip().lower()
        for ar in self.areas:
            if (ar.alias or '').strip().lower() == a:
                return ar
        return None

    def resolve_dbf(self, name):
        """Resolve a table the way `schema_load_from_stream` does, or None.

        None is a real answer here and means 'this posture cannot say'. It is
        returned rather than a guess because a guess is what section 10 forbids.
        """
        if not name:
            return None
        if os.path.isabs(name):
            return ci_path(name)
        if self.dbf_root is None:
            return None
        return ci_path(os.path.join(self.dbf_root, name))

    def resolve_index(self, name):
        """IDXROOT first and only if it EXISTS, then DBFROOT (cmd_workspace.cpp:1820)."""
        if not name or name.strip().lower() in NONE_WORDS:
            return None
        if os.path.isabs(name):
            return os.path.normpath(name)
        if self.idx_root is not None:
            cand = ci_path(os.path.join(self.idx_root, name))
            if os.path.exists(cand):
                return cand
        if self.dbf_root is None:
            return None
        return ci_path(os.path.join(self.dbf_root, name))

    def describe(self):
        out = ['DTSHEMA %d  %s' % (self.version, self.path or '(text)')]
        out.append('  self-locating : %s' % ('yes' if self.self_locating else
                                             'NO -- the file does not say where'))
        for k in ('wsid', 'flavor', 'dbf_root', 'idx_root', 'lmdb_root'):
            v = getattr(self, k)
            out.append('  %-13s : %s' % (k, v if v is not None else '(absent)'))
        out.append('  areas         : %d' % len(self.areas))
        for a in self.areas:
            out.append('    %2d %-18s %-18s %-5s tag=%-8s alias=%s'
                       % (a.n, a.dbf, a.index or 'none', a.indextype or '-',
                          a.tag or 'none', a.alias))
        for n in self.notes:
            out.append('  ' + n)
        return '\n'.join(out)


def parse(text, path=None):
    ws = Workspace(path)
    first = True
    for raw in text.replace('\r\n', '\n').split('\n'):
        line = raw.strip()
        if not line:
            continue
        if first:
            first = False
            head = line.split()
            if len(head) >= 2 and head[0].upper() == 'DTSHEMA':
                try:
                    ws.version = int(head[1])
                except ValueError:
                    ws.version = 0
                if ws.version not in (2, 3):
                    ws.notes.append('UNKNOWN version %r -- parsed as far as it goes'
                                    % head[1])
                continue
            ws.notes.append('NO DTSHEMA header; first line was %r' % line[:40])
            # fall through: parse it anyway rather than returning an empty object
            # that looks like an empty workspace.
        up = line.upper()
        if up.startswith('WSID '):
            ws.wsid = line[5:].strip()
        elif up.startswith('FLAVOR '):
            ws.flavor = line[7:].strip()
        elif up.startswith('DBFROOT '):
            ws.dbf_root = line[8:].strip()
        elif up.startswith('IDXROOT '):
            ws.idx_root = line[8:].strip()
        elif up.startswith('LMDBROOT '):
            ws.lmdb_root = line[9:].strip()
        elif up.startswith('AREA '):
            ws.areas.append(_area(line, ws))
    if ws.version == 3 and ws.dbf_root is None:
        ws.notes.append('DECLARED v3 with no DBFROOT -- the version claims '
                        'self-location and the file does not provide it')
    if ws.version == 2 and ws.dbf_root is not None:
        ws.notes.append('v2 carrying DBFROOT -- read and used, but the engine '
                        'writes roots only for v3')
    return ws


def _area(line, ws):
    parts = [p.strip() for p in line.split('|')]
    n = -1
    head = parts[0].split()
    if len(head) >= 2:
        try:
            n = int(head[1])
        except ValueError:
            n = -1
    kv = {}
    for p in parts[1:]:
        if '=' in p:
            k, v = p.split('=', 1)
            kv[k.strip().lower()] = v.strip()
    tag = kv.get('tag', '')
    if tag.lower() in NONE_WORDS:
        tag = ''
    idx = kv.get('index', '')
    if idx.lower() in NONE_WORDS:
        idx = ''
    return Area(n, kv.get('dbf', ''), idx, kv.get('indextype', ''),
                tag, kv.get('alias', ''))


def load(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        return parse(fh.read(), path)


SYNTHETIC_V3 = """DTSHEMA 3
WSID F20260820T235959Z
FLAVOR X64
DBFROOT /data/DBF/x64
IDXROOT /data/INDEXES/x64
LMDBROOT /data/LMDB/x64
AREA 0 | dbf=STUDENTS.dbf | index=STUDENTS.cdx | indextype=CDX | tag=SID | alias=STUDENTS
AREA 1 | dbf=ENROLL.dbf | index=none | indextype=NONE | tag=none | alias=ENROLL
"""

SYNTHETIC_V2 = """DTSHEMA 2
WSID F20260812T121051Z
AREA 0 | dbf=STUDENTS.dbf | index=STUDENTS.cdx | indextype=CDX | tag=none | alias=STUDENTS
"""


def selftest():
    fails = []

    v3 = parse(SYNTHETIC_V3)
    if v3.version != 3: fails.append('v3 version %r' % v3.version)
    if not v3.self_locating: fails.append('v3 should be self-locating')
    if v3.flavor != 'X64': fails.append('v3 flavor %r' % v3.flavor)
    if len(v3.areas) != 2: fails.append('v3 areas %d' % len(v3.areas))
    if v3.resolve_dbf('STUDENTS.dbf') != os.path.normpath('/data/DBF/x64/STUDENTS.dbf'):
        fails.append('v3 resolve_dbf -> %r' % v3.resolve_dbf('STUDENTS.dbf'))
    if v3.by_alias('enroll') is None: fails.append('v3 by_alias is case-sensitive')
    if v3.by_alias('ENROLL').tag != '': fails.append('tag=none should read as empty')
    if v3.by_alias('ENROLL').index != '': fails.append('index=none should read as empty')

    v2 = parse(SYNTHETIC_V2)
    if v2.version != 2: fails.append('v2 version %r' % v2.version)
    if v2.self_locating: fails.append('v2 must NOT be self-locating -- R82.3')
    if v2.resolve_dbf('STUDENTS.dbf') is not None:
        fails.append('v2 resolve_dbf must be None, got %r' % v2.resolve_dbf('STUDENTS.dbf'))
    if v2.wsid != 'F20260812T121051Z': fails.append('v2 wsid %r' % v2.wsid)

    # An absolute member resolves without any root at all, in either version.
    if v2.resolve_dbf('/elsewhere/X.dbf') != os.path.normpath('/elsewhere/X.dbf'):
        fails.append('absolute member should resolve without a root')

    for f in fails:
        print('FAIL -- %s' % f)
    print('%s -- %d check(s)' % ('FAIL' if fails else 'OK', 15))
    return 1 if fails else 0


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--selftest':
        sys.exit(selftest())
    if len(sys.argv) < 2:
        print(__doc__.strip().split('\n\n')[-1])
        sys.exit(2)
    print(load(sys.argv[1]).describe())
