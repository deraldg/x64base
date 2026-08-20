#!/usr/bin/env python3
"""R21 and R26 proven in the GENERATED runtime, not in a model. AIF-120, R37.

`relate_test.py` drove a workspace by hand. This drives the same two handlers
through `uidef_runtime.Runtime` -- the thing a generated frontend actually runs on
-- with the lock domains read from a document's own `SOURCE` (R36).

Same two configurations, and the difference is one constructor argument:

    granularity='area'    lock the work area the handler NAMES  (R11.4 as written)
    granularity='domain'  lock the relation set                 (R26)
"""
import os, sys, threading, time, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'vfp'))
import uidef_runtime as RT
from relate_test import Workspace, PARENT, CHILD, SID, TRUTH

# The document's own SOURCE, exactly as R36 imports it.
SOURCE = ("Alias = students\r\nTable = students.dbf\r\n"
          "Alias = enroll\r\nTable = enroll.dbf\r\n"
          "Relation = students -> enroll ON sid\r\n")


def build(granularity):
    students = Workspace(PARENT, 'students')
    enroll = Workspace(CHILD, 'enroll')
    students.relate('SID', enroll, 'SID')
    out = {}

    def TotalGpa(scope):
        students.go_top()
        total, n = 0.0, 0
        while not students.eof():
            r = students.read()
            if r is None:
                break
            total += float(r['GPA'] or 0)
            n += 1
            time.sleep(0.00002)
            students.skip()
        return n, round(total, 2)

    def ListEnrolments(scope):
        students.seek('SID', SID)
        got = []
        for _ in range(len(TRUTH)):
            r = enroll.read()
            if r is None:
                break
            got.append((r['SID'].strip(), r['CLS_ID'].strip()))
            time.sleep(0.0004)
            enroll.skip()
        return got

    def Done(scope, result, state):
        out.setdefault('done', []).append((result, state))

    rt = RT.Runtime(RT.domains_from_source(SOURCE),
                    {'TotalGpa': TotalGpa, 'ListEnrolments': ListEnrolments,
                     'Done': Done},
                    granularity=granularity)
    return rt, out


def trial(granularity):
    rt, out = build(granularity)
    scope = RT.Scope('form1')
    # Both handlers are DISPATCH = worker with a completion, exactly as a table
    # would declare them. The runtime decides what each one locks.
    rt.fire('ListEnrolments', 'worker', scope, alias='enroll', completion='Done')
    time.sleep(0.0005)
    rt.fire('TotalGpa', 'worker', scope, alias='students', completion='Done')
    t0 = time.time()
    while time.time() - t0 < 2.0:
        rt.pump()
        if len(out.get('done', [])) >= 2:
            break
        time.sleep(0.002)
    rt.pump()
    child = [r for r, st in out.get('done', []) if isinstance(r, list)]
    return (child[0] if child else []), rt


def run(granularity, n=60):
    wrong = leaked = 0
    for _ in range(n):
        got, rt = trial(granularity)
        names = [c for _, c in got]
        if names != TRUTH:
            wrong += 1
        if any(sid != str(SID) for sid, _ in got):
            leaked += 1
    return wrong, leaked


print("R37 -- R21 and R26 inside the generated runtime")
print()
r, _ = build('domain')
print("  lock domains read from the document's SOURCE:", r.domains.describe())
print("  student %d has %d enrolments" % (SID, len(TRUTH)))
print()
for g, label in (('area', "lock the work area the handler NAMES (R11.4 as written)"),
                 ('domain', "lock the RELATION SET (R26)")):
    w, l = run(g)
    print("  granularity=%-7s %-52s wrong %2d/60   another student's rows %2d/60"
          % (g, label, w, l))
print()
print("  Same document, same two `worker` handlers, same completions.")
print("  One constructor argument between a correct frontend and a corrupt one.")

print()
print("  the other clauses, through the same runtime:")
_log = []


def Slow(scope):
    for i in range(20):
        if scope.cancelled.is_set():
            return 'cancelled at step %d' % i
        time.sleep(0.01)
    return 'finished'


def Boom(scope):
    raise ValueError('handler raised')


def Note(scope, result, state):
    _log.append((result, state))


rt2 = RT.Runtime([{'a'}], {'Slow': Slow, 'Boom': Boom, 'Note': Note})
doomed = RT.Scope('doomed')
rt2.fire('Slow', 'worker', doomed, alias='a', completion='Note')
time.sleep(0.05)
doomed.destroy()
t0 = time.time()
while time.time() - t0 < 1.0:
    rt2.pump(); time.sleep(0.01)
live = RT.Scope('live')
rt2.fire('Boom', 'worker', live, alias='a', completion='Note')
t0 = time.time()
while time.time() - t0 < 0.6 and not _log:
    rt2.pump(); time.sleep(0.01)
rt2.pump()
dropped = [l for l in rt2.log if l[0] == 'dropped']
print("    R21.4 container destroyed mid-flight: completion %s"
      % ("DROPPED, not delivered" if dropped else "delivered -- WRONG"))
print("    failed state reached on the UI thread : %s" % _log)
rt3 = RT.Runtime([{'a'}], {'Slow': Slow})
sc = RT.Scope('x')
print("    R11.3 worker with no ON_COMPLETE      : %s"
      % ("refused" if not rt3.fire('Slow', 'worker', sc, alias='a') else "ACCEPTED -- WRONG"))
print("    R20   host capability not provided    : %s"
      % ("refused" if not rt3.fire('edit.cut', 'host', sc) else "ACCEPTED -- WRONG"))
