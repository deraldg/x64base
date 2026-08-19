#!/usr/bin/env python3
"""Lock semantics: FLOCK(), not a queue. AIF-120, R47.

Until R47 the runtime held `threading.RLock`s and BLOCKED. x64base has had
`xbase::locks` the whole time -- owner-aware, sidecar-file based, cross-process --
and its `try_lock_table` is a SINGLE non-blocking attempt that returns false.
That is FLOCK()'s semantic, and it changes two things:

  1. a busy domain REFUSES the handler; it does not queue it
  2. nothing waits, so no circular wait can form -- the AB-BA deadlock a blocking
     implementation reaches in four seconds cannot be constructed at all

Four cases: the two that must be refused, and the two that must not.
"""
import os, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import uidef_runtime as urt


def drain(rt, seconds=2.5):
    t0 = time.time()
    while time.time() - t0 < seconds:
        rt.pump()
        time.sleep(0.02)


def live():
    return [t for t in threading.enumerate()
            if t is not threading.main_thread() and t.is_alive()]


def case_ab_ba():
    """Each worker holds one domain and synchronously wants the other. Under a
    blocking lock this is a permanent hang. Under try-semantics one of the two
    inner acquisitions is refused and BOTH outer handlers still complete."""
    both = threading.Barrier(2, timeout=3)

    def outer(other_alias):
        def h(scope):
            try:
                both.wait()
            except threading.BrokenBarrierError:
                pass
            rt.fire('Inner', 'ui', scope, alias=other_alias)
            return 'returned'
        return h

    reg = {'Inner': lambda s: None, 'Done': lambda s, r, st: None}
    rt = urt.Runtime([['a'], ['b']], reg)
    reg['AB'], reg['BA'] = outer('b'), outer('a')
    sc = urt.Scope('W')
    rt.fire('AB', 'worker', sc, alias='a', completion='Done')
    rt.fire('BA', 'worker', sc, alias='b', completion='Done')
    drain(rt)
    blocked = len(live())
    done = len([l for l in rt.log if l[0] == 'complete'])
    print("  AB-BA           : threads blocked=%d  completions=%d" % (blocked, done))
    return blocked == 0 and done == 2


def case_contention():
    """Two workers on ONE domain. R38 recorded the second one QUEUED behind the
    first. Under FLOCK() semantics it is refused, and the app is told."""
    marks = []

    def slow(scope):
        marks.append('enter')
        time.sleep(0.25)
        marks.append('leave')
        return 'ok'

    reg = {'Slow': slow, 'Done': lambda s, r, st: marks.append('complete ' + st)}
    rt = urt.Runtime([['enroll', 'students']], reg)      # ONE domain (R26)
    sc = urt.Scope('W')
    rt.fire('Slow', 'worker', sc, alias='students', completion='Done')
    time.sleep(0.05)
    rt.fire('Slow', 'worker', sc, alias='enroll', completion='Done')
    drain(rt, 1.5)
    refused = [l for l in rt.log if l[0] == 'refused']
    print("  one domain      : %s" % ' / '.join(marks))
    return len(refused) == 1 and 'complete refused' in marks


def case_unrelated():
    """Two workers on DIFFERENT domains must still overlap. Refusing is only
    correct when there is something to be refused BY."""
    marks, gate = [], threading.Barrier(2, timeout=2)

    def h(n):
        def f(scope):
            marks.append(n + ' in')
            try:
                gate.wait()
            except threading.BrokenBarrierError:
                marks.append(n + ' ALONE')
            marks.append(n + ' out')
            return n
        return f

    reg = {'A': h('A'), 'B': h('B'), 'Done': lambda s, r, st: None}
    rt = urt.Runtime([['a'], ['b']], reg)
    sc = urt.Scope('W')
    rt.fire('A', 'worker', sc, alias='a', completion='Done')
    rt.fire('B', 'worker', sc, alias='b', completion='Done')
    drain(rt, 2.0)
    ok = not any('ALONE' in m for m in marks)
    print("  unrelated pair  : overlapped=%s  (%s)" % (ok, ' '.join(marks)))
    return ok


def case_reentry():
    """A handler calling a handler on ITS OWN domain is not contention -- R21.1
    already says the lock spans the whole handler. Must not be refused."""
    seen = []
    reg = {'Inner': lambda s: seen.append('inner'),
           'Done': lambda s, r, st: seen.append('complete ' + st)}
    rt = urt.Runtime([['a', 'b']], reg)
    reg['Outer'] = lambda s: (rt.fire('Inner', 'ui', s, alias='b'), 'outer')[1]
    rt.fire('Outer', 'worker', urt.Scope('W'), alias='a', completion='Done')
    drain(rt, 1.0)
    refused = len([l for l in rt.log if l[0] == 'refused'])
    print("  same domain     : inner ran=%s  refusals=%d"
          % ('inner' in seen, refused))
    return 'inner' in seen and refused == 0


def main():
    results = [('AB-BA cannot hang', case_ab_ba()),
               ('busy domain refuses, not queues', case_contention()),
               ('unrelated domains still overlap', case_unrelated()),
               ('same-domain re-entry allowed', case_reentry())]
    print()
    for label, ok in results:
        print("  %-33s : %s" % (label, ok))
    return 0 if all(ok for _, ok in results) else 1


if __name__ == '__main__':
    sys.exit(main())
