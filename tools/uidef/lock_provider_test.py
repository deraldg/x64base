#!/usr/bin/env python3
"""What the runtime actually says to the engine. AIF-120, R48.

R47 gave the runtime a seam onto x64base's locks and never watched it speak. This
test reads the exact command text, because two things live in that text:

  1. the GRANULARITY -- `LOCK TABLE` locks the area, bare `LOCK` locks the current
     record, and R26's closure is what makes the record form correct
  2. the AIF-116 surface -- a record number rendered into a command under a
     grouping locale becomes `LOCK 16,984`, which parses back as 16

The house verb that needs no number is what removes the second one, so the test
asserts that the runtime never puts a digit in a command at all.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import uidef_runtime as urt


class Sink:
    """Records every command, and can refuse a chosen one."""

    def __init__(self, fail_on=None):
        self.cmds, self.fail_on = [], fail_on

    def __call__(self, cmd):
        self.cmds.append(cmd)
        return cmd != self.fail_on


def case_verbs():
    ok = True
    for gran, verb in (('table', 'LOCK TABLE'), ('record', 'LOCK')):
        s = Sink()
        p = urt.LockProvider(s, granularity=gran)
        assert p.try_lock(['students', 'enroll'])
        got = list(s.cmds)
        want = ['SELECT enroll', verb, 'SELECT students', verb]
        s.cmds.clear()
        p.unlock(['students', 'enroll'])
        rel = list(s.cmds)
        want_rel = ['SELECT students', 'UNLOCK', 'SELECT enroll', 'UNLOCK']
        good = got == want and rel == want_rel
        ok = ok and good
        print("  %-6s acquire : %s" % (gran, ' ; '.join(got)))
        print("  %-6s release : %s   %s" % (gran, ' ; '.join(rel), 'OK' if good else 'MISMATCH'))
    return ok


def case_rollback():
    """All-or-nothing. If the second area refuses, the first must be released --
    otherwise a refused acquisition leaves a lock behind and the next attempt
    deadlocks against a lock nobody thinks they hold."""
    s = Sink(fail_on=None)
    s.fail_on = 'LOCK TABLE'          # refuse the FIRST area outright
    p = urt.LockProvider(s)
    first = p.try_lock(['a', 'b'])

    s2 = Sink()
    calls = {'n': 0}

    def run(cmd):
        s2.cmds.append(cmd)
        if cmd == 'LOCK TABLE':
            calls['n'] += 1
            return calls['n'] == 1        # first area succeeds, second refuses
        return True
    p2 = urt.LockProvider(run)
    second = p2.try_lock(['a', 'b'])
    released = s2.cmds.count('UNLOCK')
    print("  refuse first  : returned %s, commands=%d" % (first, len(s.cmds)))
    print("  refuse second : returned %s, rolled back %d lock(s)  (%s)"
          % (second, released, ' ; '.join(s2.cmds)))
    return first is False and second is False and released == 1


def case_no_numbers():
    """AIF-116's surface. Nothing the runtime emits may contain a digit it put
    there -- an alias may legitimately have one, so the check is on the VERBS."""
    bad = []
    for gran in ('table', 'record'):
        s = Sink()
        p = urt.LockProvider(s, granularity=gran)
        p.try_lock(['students', 'enroll'])
        p.unlock(['students', 'enroll'])
        for c in s.cmds:
            if c.startswith('SELECT '):
                continue                    # the alias is the document's, not ours
            if any(ch.isdigit() for ch in c):
                bad.append((gran, c))
    print("  commands carrying a runtime-rendered number: %s" % (bad or 'none'))
    return not bad


def case_runtime_refuses():
    """A provider that says no must refuse the handler, not run it anyway."""
    ran = []
    reg = {'H': lambda s: ran.append('ran') or 'ok',
           'Done': lambda s, r, st: ran.append('complete ' + st)}
    p = urt.LockProvider(lambda c: not c.startswith('LOCK'))   # engine refuses
    rt = urt.Runtime([['a']], reg, provider=p)
    rt.fire('H', 'worker', urt.Scope('W'), alias='a', completion='Done')
    import time
    t0 = time.time()
    while time.time() - t0 < 1.0:
        rt.pump(); time.sleep(0.02)
    refused = [l for l in rt.log if l[0] == 'refused']
    print("  engine refuses: handler ran=%s  refusals=%d  marks=%s"
          % ('ran' in ran, len(refused), ran))
    return 'ran' not in ran and len(refused) == 1


def main():
    results = [('verbs and order', case_verbs()),
               ('all-or-nothing rollback', case_rollback()),
               ('no runtime-rendered numbers', case_no_numbers()),
               ('engine refusal refuses the handler', case_runtime_refuses())]
    print()
    for label, ok in results:
        print("  %-36s : %s" % (label, ok))
    return 0 if all(ok for _, ok in results) else 1


if __name__ == '__main__':
    sys.exit(main())
