#!/usr/bin/env python3
"""Refuse a register row dated in the FUTURE on the host's own clock.

WHY THIS EXISTS, AND IT IS NOT HYPOTHETICAL. Measured 2026-10-21 over every row
ever added to the R register and the open-items register -- 139 rows carrying a
date -- FOUR of them are stamped one day LATER than the commit that introduced
them:

    OI-048  says 2026-10-22, commit 2026-10-21   (caught and corrected)
    R151    says 2026-10-22, commit 2026-10-21   (caught and corrected)
    OI-039  says 2026-09-16, commit 2026-09-15   (shipped, uncorrected)
    R134    says 2026-08-31, commit 2026-08-30   (shipped, uncorrected)
    OI-024  says 2026-08-31, commit 2026-08-30   (shipped, twice)

EVERY DISCREPANCY IS EXACTLY +1 DAY, which is a signature rather than noise: the
steward's environment reports UTC while this tree's clock is local, so for the
last several hours of each working day the two disagree by a day -- and that is
the window the work happens in. Three of the four shipped in August and
September and nothing has ever said so.

THE HOST'S CLOCK IS THE AUTHORITY FOR ANYTHING WRITTEN INTO THIS TREE (R152).
Same
family as "origin/development is a cache, fetch before claiming the remote" and
"dev data is not a specimen": the steward's environment is not this tree's
environment, and a value read from the wrong one is wrong even when it looks
reasonable.

WHY *TODAY* AND NOT THE COMMIT'S AUTHOR DATE. At gate time the commit does not
exist yet, so there is no author date to compare against -- but this gate runs on
the host, moments before the commit is created, so today IS that author date.
Checking against today is the same check, available one step earlier.

WHY ONLY THE FUTURE DIRECTION IS HARD-BLOCKED. A row dated LATER than today is
unambiguously wrong and needs no judgment: nothing has happened tomorrow. A row
dated EARLIER is ordinary and legitimate -- a finding measured on Monday and
written up on Wednesday carries Monday's date on purpose. So the asymmetry is
deliberate, and it is also exactly the direction the UTC offset produces.

SCOPE IS PRINTED, ALWAYS, and the denominator with it. A gate scoped to the
change set cannot see a file nobody changed -- that is the whole lesson of
check_cited_paths.py -- so this one says how many rows it actually read. A green
with no denominator is a green that means "I did not look".

Run:  $py12 tools\\staging\\check_row_dates.py [--selftest]
"""
import datetime
import re
import subprocess
import sys

# The registers whose SECOND column is a date. The intake queue is deliberately
# NOT here: its rows carry no date column, so there is nothing to compare.
DATED_REGISTERS = (
    "docs/ai-friendly/R_RULING_REGISTER_V1.md",   # | R151 | 2026-10-21 | ruling | ...
    "coordination/OPEN_ITEMS.md",                 # | OI-048 | 2026-10-21 | 2026-11-18 | ...
)

# A row as it appears in a `git diff --cached -U0` ADDED line. The id forms are
# the two the registers use; anything else is not a row and is not guessed at.
ADDED_ROW = re.compile(
    r"^\+\|\s*(R\d+|OI-\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|(?:\s*(\d{4}-\d{2}-\d{2})\s*\|)?"
)


def git(args):
    return subprocess.run(["git", "--no-pager"] + args,
                          capture_output=True, text=True).stdout


def staged_registers():
    names = [n for n in git(["diff", "--cached", "--name-only"]).splitlines() if n]
    return [r for r in DATED_REGISTERS if r in names]


def added_rows(paths):
    """(id, raised, next_look_or_None) for every row this change set ADDS."""
    out = []
    if not paths:
        return out
    for line in git(["diff", "--cached", "-U0", "--"] + list(paths)).splitlines():
        m = ADDED_ROW.match(line)
        if m:
            out.append((m.group(1), m.group(2), m.group(3)))
    return out


def judge(rows, today):
    """Return (findings, notes). A finding BLOCKS; a note is advisory."""
    findings, notes = [], []
    for rid, raised, nextlook in rows:
        try:
            d_raised = datetime.date.fromisoformat(raised)
        except ValueError:
            notes.append("%s: unparseable date %r -- not judged" % (rid, raised))
            continue
        if d_raised > today:
            findings.append("%s is dated %s and today is %s -- %+d day(s) in the FUTURE"
                            % (rid, raised, today.isoformat(), (d_raised - today).days))
        if nextlook:
            try:
                d_next = datetime.date.fromisoformat(nextlook)
            except ValueError:
                notes.append("%s: unparseable next-look %r -- not judged" % (rid, nextlook))
                continue
            if d_next < d_raised:
                findings.append("%s has a NEXT LOOK of %s before its raised date %s"
                                % (rid, nextlook, raised))
    return findings, notes


# ---- selftest --------------------------------------------------------------
def selftest():
    T = datetime.date(2026, 10, 21)
    cases = []

    def case(name, got, want):
        cases.append((name, got == want, got, want))

    # the parser
    p = lambda s: ADDED_ROW.match(s)
    case("an added R row parses", bool(p("+| R151 | 2026-10-21 | ruling | AIF-163 |")), True)
    case("an added OI row parses both dates",
         p("+| OI-048 | 2026-10-21 | 2026-11-18 | decision |").groups(),
         ("OI-048", "2026-10-21", "2026-11-18"))
    case("an R row has no second date",
         p("+| R151 | 2026-10-21 | ruling |").group(3), None)
    case("a REMOVED row is not an added row", bool(p("-| R151 | 2026-10-99 | ruling |")), False)
    case("a context line is not an added row", bool(p(" | R151 | 2026-10-99 |")), False)
    case("a diff header is not an added row", bool(p("+++ b/coordination/OPEN_ITEMS.md")), False)
    case("an undated row is not matched", bool(p("+| R151 | ruling | AIF-163 |")), False)
    case("an AIF intake row is out of scope", bool(p("+| AIF-172 | THE PREDICATE ... |")), False)

    # the judgment
    f, n = judge([("R151", "2026-10-22", None)], T)
    case("tomorrow BLOCKS", len(f), 1)
    case("the finding says which direction", "FUTURE" in f[0], True)
    case("the finding names both dates", "2026-10-22" in f[0] and "2026-10-21" in f[0], True)

    f, n = judge([("R151", "2026-10-21", None)], T)
    case("today is clean", f, [])

    f, n = judge([("R134", "2026-08-30", None)], T)
    case("an older date is clean -- measured then, written up later", f, [])

    f, n = judge([("OI-048", "2026-10-21", "2026-11-18")], T)
    case("a future next-look is clean", f, [])

    f, n = judge([("OI-048", "2026-10-21", "2026-10-20")], T)
    case("a next-look before the raise date BLOCKS", len(f), 1)

    f, n = judge([("OI-048", "2026-10-99", None)], T)
    case("an unparseable date does not block", f, [])
    case("an unparseable date is still reported", len(n), 1)

    f, n = judge([], T)
    case("no rows, no findings", f, [])

    bad = [c for c in cases if not c[1]]
    for name, ok, got, want in cases:
        print("  %-5s %s" % ("ok" if ok else "FAIL", name))
        if not ok:
            print("        got %r, wanted %r" % (got, want))
    print("row-dates selftest: %d case(s), %d failure(s)" % (len(cases), len(bad)))
    return 0 if not bad else 2


def main():
    if "--selftest" in sys.argv:
        return selftest()

    today = datetime.date.today()          # the HOST's clock -- the authority
    paths = staged_registers()
    if not paths:
        print("row-dates: no dated register in scope -- nothing to check")
        return 0

    rows = added_rows(paths)
    print("row-dates: %d register(s) in scope, %d row(s) added, today is %s on this host"
          % (len(paths), len(rows), today.isoformat()))
    for p in paths:
        print("  %s" % p)

    findings, notes = judge(rows, today)
    for nt in notes:
        print("  advisory: %s" % nt)
    if findings:
        for f in findings:
            print("  %s" % f, file=sys.stderr)
        print("\n  A ROW DATED IN THE FUTURE IS WRONG WITHOUT ARGUMENT -- nothing has\n"
              "  happened tomorrow. This is almost always a UTC clock writing into a\n"
              "  tree that keeps local time; four rows shipped that way before this\n"
              "  gate existed. Take the date from THIS host: git log -1 --date=short.",
              file=sys.stderr)
        return 2
    print("row-dates: PASS -- no row is dated ahead of this host's clock")
    return 0


if __name__ == "__main__":
    sys.exit(main())
