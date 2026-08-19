#!/usr/bin/env python3
"""Every path a document cites must be tracked. AIF-120, R42.3.

The house calls a pointer whose target does not exist on the surface it ships on a
WIDOW, and section 10 of the working rules says to sweep for them before finishing.
That sweep was done once, by hand, after 21 rulings -- and found three defects that
every gate had passed, because `git add` on a gitignored path is a silent no-op and
an ignored path never reaches the staged index a gate inspects.

This is that sweep as one command. It resolves every repo path a document cites
against `git ls-files` and reports what is cited but not shipped.

    python tools/uidef/cite_check.py                     # every AIF120 ruling
    python tools/uidef/cite_check.py docs/maintenance/X.md ...

Exit status is 1 if anything is cited and not tracked, so it can be wired into a
gate by whoever owns gates. It is deliberately NOT a gate here: portal gates are
AIF-082's area and installing one uninvited is not this lane's call.
"""
import glob
import os
import re
import subprocess
import sys

ROOTS = ('docs/', 'tools/', 'src/', 'include/', 'labtalk/', 'coordination/',
         'dottalkpp/', 'scripts/', 'smoke/')
EXTS = ('.md', '.py', '.png', '.txt', '.h', '.hpp', '.cpp', '.csv', '.yaml',
        '.yml', '.dts', '.html', '.json', '.dbf', '.scx', '.mnx', '.vcx', '.frx',
        '.sh', '.ps1')
# A document that DOCUMENTS an ignored path -- R33 and R42 do exactly that, and so
# does any handoff explaining why a file cannot be staged -- would otherwise be
# flagged on every commit that touches it. A permanent advisory trains people to
# skip the whole check, which is the failure `open-items` was written to avoid.
# So a line may opt out explicitly, and the marker is greppable rather than magic:
#
#     the working copy at `tools/uidef/read_vfp_binary.py`  <!-- cite-check:ignore -->
#
# It suppresses only the line it appears on, so it cannot silence a document.
SUPPRESS = 'cite-check:ignore'

PATH_RE = re.compile(r'(?<![\w/.-])((?:%s)[A-Za-z0-9_./-]+)' % '|'.join(
    r.replace('/', r'/') for r in ROOTS))


def tracked(paths):
    """One `git ls-files` for the whole set, rather than one per path."""
    if not paths:
        return set()
    out = subprocess.run(['git', '--no-optional-locks', 'ls-files', '-z', '--'] + sorted(paths),
                         capture_output=True, text=True)
    return {p for p in out.stdout.split('\0') if p}


def ignored(paths):
    """Paths git is configured to ignore.

    These are not widows and they are worse in one specific way: `git add` on one
    is a SILENT no-op (R42.1), so a handoff that stages it produces a clean commit
    and no change. R33 shipped that way. They get their own category because the
    remedy is different -- a widow needs committing, an ignored citation needs the
    document to stop promising it.
    """
    if not paths:
        return set()
    out = subprocess.run(['git', '--no-optional-locks', 'check-ignore', '--'] + sorted(paths),
                         capture_output=True, text=True)
    return {p for p in out.stdout.splitlines() if p}


def cited(doc):
    text = open(doc, encoding='utf-8', errors='replace').read()
    found = set()
    for line in text.replace('\r\n', '\n').split('\n'):
        if SUPPRESS in line:
            continue
        for m in PATH_RE.finditer(line):
            p = m.group(1).rstrip('.,;:)`*')
            if p.endswith(EXTS):
                found.add(p)
    return found


def main(argv):
    docs = argv or sorted(glob.glob('docs/maintenance/AIF120_*.md'))
    if not docs:
        print('no documents given and no AIF120 rulings found -- run from the repo root')
        return 2
    every = {}
    for d in docs:
        for p in cited(d):
            every.setdefault(p, []).append(d)
    live = tracked(set(every))
    skip = ignored(set(every) - live)
    widows, missing, ign = [], [], []
    for p, where in sorted(every.items()):
        if p in live:
            continue
        if p in skip:
            ign.append((p, where))
        elif not os.path.exists(p):
            missing.append((p, where))
        else:
            widows.append((p, where))

    print('cite_check: %d document(s), %d distinct path(s) cited, %d tracked'
          % (len(docs), len(every), len(live)))
    for label, rows in (('WIDOW   (on disk, NOT tracked)', widows),
                        ('MISSING (cited, not on disk)', missing),
                        ('IGNORED (cited, and `git add` on it is a no-op)', ign)):
        for p, where in rows:
            print('  %s: %s' % (label, p))
            for d in where:
                print('      cited by %s' % d)
    if not (widows or missing or ign):
        print('  every cited path is tracked')
    # An ignored citation is a warning, not a failure: R33 and R42 cite one ON
    # PURPOSE, as the defect they are about. A widow or a missing file is a failure.
    return 1 if (widows or missing) else 0


if __name__ == '__main__':
    sys.exit(main([a for a in sys.argv[1:] if not a.startswith('-')]))
