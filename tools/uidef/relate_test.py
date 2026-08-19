#!/usr/bin/env python3
"""Two workers, two work areas, one SET RELATION. AIF-120.

R21 tested one worker against the UI thread and left two open items:

    Two workers, not one worker and the UI thread.
    Contention across work areas. R11.4 serializes "against one workspace".
    Two workspaces with a SET RELATION between them is a second sharing
    channel and nothing has touched it.

They are the same experiment, and the relation is what makes it interesting.
`SET RELATION TO sid INTO enroll` means moving the PARENT pointer moves the CHILD
pointer. So a handler can mutate a work area it never names, never opens and never
locks -- which is exactly the case R11.4's wording does not cover.

Parent: STUDENTS.dbf, 200 records. Child: ENROLL.dbf, 686 records, 200 distinct
SIDs. Both are the real tables in this tree.
"""
import os, sys, threading, time, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'vfp'))
sys.path.insert(0, HERE)
from read_vfp_binary import Dbf

PARENT = os.environ.get('AIF120_STUDENTS') or os.path.join(HERE, 'STUDENTS.dbf')
CHILD = os.environ.get('AIF120_ENROLL') or os.path.join(HERE, 'ENROLL.dbf')


class _Null:
    def __enter__(self): return self
    def __exit__(self, *a): return False


class Workspace:
    def __init__(self, path, name):
        self.rows = list(Dbf(path).rows())
        self.n = len(self.rows)
        self.name = name
        self.lock = threading.RLock()
        self.recno = 1
        self.relations = []          # (my_field, child_ws, child_field)

    def relate(self, field, child, child_field):
        """SET RELATION TO <field> INTO <child>."""
        self.relations.append((field, child, child_field))

    def _follow(self):
        """The whole point. Navigating me repositions my children -- and NOTHING
        takes the child's lock, because from the child's side no call happened."""
        for fld, child, cfld in self.relations:
            if self.recno < 1 or self.recno > self.n:
                continue
            key = self.rows[self.recno - 1][fld].strip()
            for i, r in enumerate(child.rows):
                if r[cfld].strip() == key:
                    child.recno = i + 1
                    break
            else:
                child.recno = child.n + 1        # EOF: no matching child

    def go_top(self):
        self.recno = 1; self._follow()

    def skip(self):
        self.recno += 1; self._follow()

    def seek(self, field, value):
        for i, r in enumerate(self.rows):
            if r[field].strip() == str(value):
                self.recno = i + 1; self._follow(); return True
        return False

    def eof(self):
        return self.recno > self.n

    def read(self):
        return None if self.eof() else self.rows[self.recno - 1]


# -- the two handlers ------------------------------------------------------

def TotalGpa(students, enroll, hold, slow):
    """Walks the PARENT. Locks the parent. Never mentions the child."""
    with hold(students):
        students.go_top()
        total, count = 0.0, 0
        while not students.eof():
            r = students.read()
            if r is None:
                break
            total += float(r['GPA'] or 0)
            count += 1
            time.sleep(slow)
            students.skip()
        return count, round(total, 2)


def ListEnrolments(students, enroll, hold, slow, sid):
    """Reads the CHILD for one student. Locks the child. Does everything right.

    It walks the child with the child's own cursor -- SKIP until the key changes,
    which is how you read a related child set. It never mentions the parent.
    """
    with hold(enroll):
        students.seek('SID', sid)             # position the relation
        out = []
        while not enroll.eof():
            r = enroll.read()
            if r is None or r['SID'].strip() != str(sid):
                break
            out.append(r['CLS_ID'].strip())
            time.sleep(slow)
            enroll.skip()
        return out


def ListTrusting(students, enroll, hold, slow, sid, want):
    """The same read, by a handler that TRUSTS the relation.

    It was told how many child rows there are and reads that many, instead of
    re-checking the key on every row. That is not a straw man -- re-checking the
    parent key inside a related child walk is redundant work a careful programmer
    removes. The careful handler above was protected by a guard it did not know it
    needed.
    """
    with hold(enroll):
        students.seek('SID', sid)
        out = []
        for _ in range(want):
            r = enroll.read()
            if r is None:
                break
            out.append((r['SID'].strip(), r['CLS_ID'].strip()))
            time.sleep(slow)
            enroll.skip()
        return out


def truth(sid):
    rows = list(Dbf(CHILD).rows())
    return [r['CLS_ID'].strip() for r in rows if r['SID'].strip() == str(sid)]


SID = 50000002                                  # the student with the most rows
TRUTH = truth(SID)


def run(mode, slow_p=0.00002, slow_c=0.0004, trusting=False):
    students = Workspace(PARENT, 'students')
    enroll = Workspace(CHILD, 'enroll')
    students.relate('SID', enroll, 'SID')

    if mode == 'per-workspace':
        def hold(ws):
            return ws.lock                       # lock what you touch
    elif mode == 'relation-set':
        shared = threading.RLock()
        def hold(ws):
            return shared                        # lock the whole relation graph
    else:
        def hold(ws):
            return _Null()

    out = {}
    tp = threading.Thread(target=lambda: out.__setitem__(
        'p', TotalGpa(students, enroll, hold, slow_p)))
    body = (ListEnrolments if not trusting else
            (lambda s_, e_, h_, sl_, sid_: ListTrusting(s_, e_, h_, sl_, sid_, len(TRUTH))))
    tc = threading.Thread(target=lambda: out.__setitem__(
        'c', body(students, enroll, hold, slow_c, SID)))
    tc.start(); time.sleep(0.0005); tp.start()
    tp.join(); tc.join()
    return out


def trials(mode, n=100, trusting=False):
    wrong = leaked = 0
    seen = collections.Counter()
    for _ in range(n):
        o = run(mode, trusting=trusting)
        got = o.get('c') or []
        if trusting:
            leak = any(sid != str(SID) for sid, _ in got)
            got = [c for _, c in got]
        else:
            leak = any(c not in TRUTH for c in got)
        seen[tuple(got)] += 1
        if got != TRUTH:
            wrong += 1
            if leak:
                leaked += 1
    return wrong, leaked, seen


print("SET RELATION TO sid INTO enroll")
print("  parent STUDENTS.dbf 200 records; child ENROLL.dbf 686 records")
print("  student %d has %d enrolments: %s" % (SID, len(TRUTH), ', '.join(TRUTH)))
print()
for mode, label in (('none', 'no lock at all'),
                    ('per-workspace', 'each handler locks the work area it touches'),
                    ('relation-set', 'each handler locks the whole relation set')):
    w, l, seen = trials(mode)
    print("  %-14s %-44s wrong %3d/100   other students' rows %3d/100"
          % (mode, label, w, l))
    if w and mode == 'per-workspace':
        for got, hits in seen.most_common(3):
            mark = 'CORRECT' if list(got) == TRUTH else 'wrong'
            print("        %-8s x%-3d %s" % (mark, hits, ', '.join(got) or '(empty)'))
print()
print("  the SAME read by a handler that TRUSTS the relation instead of")
print("  re-checking the parent key on every child row:")
for mode in ('per-workspace', 'relation-set'):
    w, l, seen = trials(mode, trusting=True)
    print("  %-14s wrong %3d/100   rows belonging to ANOTHER student %3d/100"
          % (mode, w, l))
    for got, hits in seen.most_common(2):
        print("        x%-3d %s" % (hits, ', '.join(got) or '(empty)'))
print()
print("The child handler locked the child, read the child, and never touched the")
print("parent's lock. The parent walk moved the child anyway, through the relation.")
