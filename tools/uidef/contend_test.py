#!/usr/bin/env python3
"""Runtime test of R11.4's SERIALIZATION clause, on a real DBF cursor.

R11.4 says: "Commands that move the record pointer or change area, order,
filter, relation, lock or buffer state are serialized against one workspace.
Concurrency in a generated frontend is concurrency against a DBF cursor. The
house rule 'a write may be buffered; navigation discards it' becomes a
data-loss bug the moment two handlers navigate at once."

Nothing had ever contended. dispatch_test.py fired one worker, once. This fires
two handlers that both navigate STUDENTS.dbf -- the same 200-record table VFP 9
opened -- and measures what R11.4 predicts.

Three modes, because the interesting result is not "a lock fixes it":
  none         no lock at all
  per-op       every cursor operation takes the lock  (the naive fix)
  per-handler  the whole handler body takes the lock  (R11.4 as written)
"""
import os, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'vfp'))     # tools/vfp/read_vfp_binary.py
sys.path.insert(0, HERE)
from read_vfp_binary import Dbf

# The workspace under test is the same 200-record table VFP 9 opened.
DBF = os.environ.get('AIF120_STUDENTS') or os.path.join(
    HERE, '..', '..', 'dottalkpp', 'data', 'dbf', 'vfp', 'STUDENTS.dbf')
if not os.path.exists(DBF):
    DBF = 'STUDENTS.dbf'


class Workspace:
    """One DBF work area.

    The record pointer, the pending REPLACE buffer and the order are WORKSPACE
    state, not call state. Two handlers in one work area share one pointer.
    That is the whole reason R11.4 exists, and it is what this class models.
    """

    def __init__(self, path, mode='none'):
        self.rows = list(Dbf(path).rows())
        self.n = len(self.rows)
        self.mode = mode
        self.lock = threading.RLock()
        self.recno = 1
        self.buffer = None          # (recno, field, value) -- a pending REPLACE
        self.expect = {}            # per-thread: the record THIS thread selected
        self.steals = []            # reads of a record another thread selected
        self.discards = []          # buffered writes navigation threw away
        self.applied = []           # writes that actually landed

    # -- lock discipline -------------------------------------------------
    def _op_lock(self):
        return self.lock if self.mode == 'per-op' else _NullLock()

    def handler_lock(self):
        return self.lock if self.mode == 'per-handler' else _NullLock()

    # -- navigation: every one of these discards a pending buffer ---------
    def _navigated(self):
        if self.buffer is not None:
            self.discards.append((threading.get_ident(), self.buffer))
            self.buffer = None      # house rule: navigation discards a write
        self.expect[threading.get_ident()] = self.recno

    def go_top(self):
        with self._op_lock():
            self.recno = 1
            self._navigated()

    def skip(self):
        with self._op_lock():
            self.recno += 1
            self._navigated()

    def goto(self, n):
        with self._op_lock():
            self.recno = n
            self._navigated()

    def seek(self, sid):
        with self._op_lock():
            for i, r in enumerate(self.rows):
                if r['SID'].strip() == str(sid):
                    self.recno = i + 1
                    self._navigated()
                    return True
            return False

    def eof(self):
        return self.recno > self.n

    # -- read: detects a stolen pointer ----------------------------------
    def read(self):
        with self._op_lock():
            me = threading.get_ident()
            want = self.expect.get(me)
            if want is not None and want != self.recno:
                # this thread selected `want`; it is about to read `recno`
                self.steals.append((me, want, self.recno))
            if self.eof():
                return None
            return self.rows[self.recno - 1]

    # -- buffered write --------------------------------------------------
    def replace(self, field, value):
        with self._op_lock():
            self.buffer = (self.recno, field, value)

    def commit(self):
        with self._op_lock():
            if self.buffer is None:
                return False        # silent loss: there is nothing to write
            rec, field, value = self.buffer
            self.rows[rec - 1][field] = value
            self.applied.append((rec, field, value))
            self.buffer = None
            return True


class _NullLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# -- the two handlers.  R14: the table carries these NAMES, not these bodies.

def TotalGpa(ws, slow=0.0):
    """Walks the cursor top to bottom. A multi-operation transaction."""
    with ws.handler_lock():
        ws.go_top()
        total, count = 0.0, 0
        while not ws.eof():
            r = ws.read()
            if r is None:
                break
            try:
                total += float(r['GPA'] or 0)
            except ValueError:
                pass
            count += 1
            if slow:
                time.sleep(slow)
            ws.skip()
        return count, round(total, 2)


def BumpGpa(ws, sid, newgpa, slow=0.0):
    """SEEK, buffered REPLACE, COMMIT. Also a multi-operation transaction."""
    with ws.handler_lock():
        if not ws.seek(sid):
            return False
        ws.replace('GPA', newgpa)
        if slow:
            time.sleep(slow)
        return ws.commit()


def truth():
    rows = list(Dbf(DBF).rows())
    return len(rows), round(sum(float(r['GPA'] or 0) for r in rows), 2)


TRUTH_N, TRUTH_SUM = truth()


def trial(mode, slow_a=0.0, slow_b=0.0):
    ws = Workspace(DBF, mode)
    out = {}
    ta = threading.Thread(target=lambda: out.__setitem__('a', TotalGpa(ws, slow_a)))
    tb = threading.Thread(target=lambda: out.__setitem__('b', BumpGpa(ws, 50000100, 4.00, slow_b)))
    ta.start(); tb.start(); ta.join(); tb.join()
    return ws, out


def report(mode, trials=200, slow_a=0.00002, slow_b=0.0005):
    bad_total = wrote = lost = stole = 0
    for _ in range(trials):
        ws, out = trial(mode, slow_a=slow_a, slow_b=slow_b)
        n, s = out.get('a', (0, 0))
        if (n, s) != (TRUTH_N, TRUTH_SUM):
            bad_total += 1
        if out.get('b'):
            wrote += 1
        else:
            lost += 1
        if ws.steals:
            stole += 1
    print("  %-12s wrong walk %3d/%d   lost write %3d/%d   stolen pointer %3d/%d"
          % (mode, bad_total, trials, lost, trials, stole, trials))
    return bad_total, lost, stole


def forced():
    """One deterministic interleaving, to name the mechanism exactly."""
    ws = Workspace(DBF, 'none')
    gate = threading.Event()
    done = threading.Event()

    def b():
        ws.seek(50000100)
        ws.replace('GPA', 4.00)      # buffered, not yet written
        gate.set()                   # let A navigate now
        done.wait(2)
        ok = ws.commit()
        print("    B: COMMIT returned %s  (buffer was %s)" % (ok, ws.buffer))
        return ok

    tb = threading.Thread(target=b)
    tb.start()
    gate.wait(2)
    print("    A: walks the cursor while B holds a buffered REPLACE")
    ws.go_top()
    r = ws.read()
    print("    A: reads record %d (%s) -- B had positioned record 101"
          % (ws.recno, (r or {}).get('LNAME', '').strip()))
    done.set()
    tb.join()
    print("    discards recorded: %d   writes applied: %d" % (len(ws.discards), len(ws.applied)))
    return len(ws.discards), len(ws.applied)


print("STUDENTS.dbf: %d records, GPA sum %.2f (single-threaded truth)"
      % (TRUTH_N, TRUTH_SUM))
print()
print("PART A -- forced interleaving: the exact mechanism R11.4 names")
d, a = forced()
print()
print("PART B -- free-running race, 200 trials per mode")
print("  B holds its buffer 0.5 ms while A walks ~4 ms -- collision near certain")
r_none = report('none')
r_op = report('per-op')
r_hnd = report('per-handler')
print()
print("R11.4 serialization holds only at handler granularity:",
      r_hnd == (0, 0, 0) and r_op != (0, 0, 0))
print()
print("PART C -- the same race with B fast, to see the INTERMITTENT rate")
print("  (the honest number: a bug that fails 3 percent of the time still ships)")
for sb in (0.0, 0.00005, 0.0002, 0.001):
    print("  buffer held %7.3f ms:" % (sb * 1000), end='')
    report('none', trials=200, slow_a=0.00002, slow_b=sb)

print()
print("PART D -- what the corrupted walk actually REPORTS")
print("  This is the part that matters. The walk does not crash and does not")
print("  raise. It returns a plausible answer that is wrong.")
import collections
seen = collections.Counter()
for _ in range(40):
    ws, out = trial('none', slow_a=0.00002, slow_b=0.0)
    seen[out.get('a')] += 1
print("  truth              : %d students, GPA sum %.2f, mean %.2f"
      % (TRUTH_N, TRUTH_SUM, TRUTH_SUM / TRUTH_N))
for (n, sm), hits in seen.most_common(6):
    print("  observed %2dx       : %d students, GPA sum %.2f, mean %.2f"
          % (hits, n, sm, (sm / n if n else 0)))
print("  B's SEEK landed on record 101 of 200 and took A's walk with it.")
print("  A reported half the roster with a credible mean. Nothing errored.")
