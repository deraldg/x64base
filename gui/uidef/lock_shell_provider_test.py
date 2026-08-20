#!/usr/bin/env python3
"""The lock provider against the REAL DotTalk++ shell. AIF-120, R66.

`lock_provider_test.py` drives the provider with a fake `run` and checks the command
TEXT. This drives it against a live `dottalkpp` over a pipe and checks the ENGINE'S
OWN answer, which is the difference R64.1 made necessary: the command layer prints
`UNLOCK: record N unlocked.` whether or not anything was released, so a test that
reads the message tests the message.

Case C is the point of the file. It reproduces correction 34 -- acquire with
`LOCK TABLE`, release with bare `UNLOCK`, the exact shape R47.2, R48 and R49 all
shipped -- and shows the provider REFUSING to report the release, because
`LOCK STATUS` still says the table is held. That defect cost three rulings and was
found by reading `src/cli/cmd_unlock.cpp`. The release path now finds it by itself.

Usage:
    python3 lock_shell_provider_test.py <path-to-dottalkpp> [<DBF subpath>]

Needs a dottalkpp binary with the shipped x64 school tables (STUDENTS, ENROLL)
reachable from its DATA path. Read-only: it takes and releases table locks and does
not append, replace or delete anything.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shell_session import ShellSession
import uidef_runtime as urt

DOMAIN = ['STUDENTS', 'ENROLL']


def main(binary, dbf='dbf/x64'):
    fails = []
    notes = []
    log = notes.append
    s = ShellSession(binary)
    try:
        s.send('SET PATH DBF %s' % dbf)
        for i, a in enumerate(DOMAIN, start=1):
            s.send('SELECT %d' % i)
            if 'Opened' not in s.send('USE %s' % a):
                print('SKIP: %s did not open under %s' % (a, dbf))
                return 0

        def status(alias):
            s.send('SELECT %s' % alias)
            return s.send('LOCK STATUS')

        # A -- all-or-nothing acquire over R26's domain, confirmed area by area.
        p = urt.LockProvider(s.run, 'table', observe=s.observe, log=log)
        ok = p.try_lock(DOMAIN)
        held = ['LOCKED' in status(a) for a in DOMAIN]
        print('A acquire domain %s : %s   confirmed %s'
              % ('{%s}' % ', '.join(DOMAIN), ok, held))
        if not (ok and all(held)):
            fails.append('A: acquire not confirmed on every area of the domain')

        # B -- release, confirmed. An unconfirmed release is the worst state there
        # is: the runtime thinks the domain is free and the engine does not.
        rel = p.unlock(DOMAIN)
        free = ['LOCKED' not in status(a) for a in DOMAIN]
        print('B release confirmed : %s   free %s' % (rel, free))
        if not (rel and all(free)):
            fails.append('B: release not confirmed')

        # C -- correction 34, caught by the methodology instead of by a human.
        p2 = urt.LockProvider(s.run, 'table', observe=s.observe, log=log)
        p2.unverb = 'UNLOCK'                  # the record verb, on a table lock
        got = p2.try_lock(['STUDENTS'])
        bad = p2.unlock(['STUDENTS'])
        still = 'LOCKED' in status('STUDENTS')
        print('C wrong release verb: acquire %s  release reports %s  still held %s'
              % (got, bad, still))
        if not (got and bad is False and still):
            fails.append('C: the wrong release verb was not caught')
        s.send('SELECT STUDENTS')
        s.send('UNLOCK TABLE')               # leave the table as we found it

        # D -- a provider with no observer runs, and SAYS it is unverified.
        quiet = []
        p3 = urt.LockProvider(lambda c: True, 'table', log=quiet.append)
        p3.try_lock(['STUDENTS'])
        print('D unverified provider: warned %s' % bool(quiet))
        if not any('UNVERIFIED' in x for x in quiet):
            fails.append('D: an unverified provider did not say so')
    finally:
        s.close()

    for n in notes:
        print('   note: %s' % n)
    print('\n%s -- %d case(s), %d failure(s)'
          % ('FAIL' if fails else 'PASS', 4, len(fails)))
    for f in fails:
        print('   %s' % f)
    return 1 if fails else 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    sys.exit(main(*sys.argv[1:3]))
