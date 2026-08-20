#!/usr/bin/env python3
"""Portal check: a document must not cite a repo path it does not ship.

The house calls a pointer whose target does not exist on the surface it ships on a
WIDOW, and section 10 of the working rules says to sweep for them before finishing.
That sweep had no mechanism. AIF-120 R42 measured what the absence costs: a ruling
shipped asserting a fix that was not in tracked code, because `git add` on a
gitignored path is a SILENT no-op -- the commit was clean, every gate passed, and
the file never moved. Nine committed tools were unimportable on a fresh clone for
the same reason.

No existing gate can see this. `prepush-gate` inspects the staged index and an
ignored path never reaches the index; `mandatory-tracked` checks a declared list and
these paths are not on it.

SCOPE: only documents in THIS change set. A gate that reported every pre-existing
widow in the tree would print the same paragraph every commit and stop being read
by the third day -- the reasoning `open-items` already uses.

Exit codes follow the portal convention: 0 clean, 3 advisory. Never 2. A widow is
someone forgetting to stage a file, and blocking the commit that would have carried
the rest of their work is the wrong trade.
"""
import os
import re
import subprocess
import sys

# `gui/` was added by AIF-120 R81.4. AIF-120 R71 promoted that lane out of
# `tools/uidef` into `gui/uidef` and retargeted 251 citations INTO a directory
# this tuple did not list -- so the promotion commit's `cited-paths: OK` was a
# green about the paths that had NOT moved. Measured at the time of the fix: 175
# citations across 66 documents were invisible here, and turning them on costs
# exactly one advisory.
ROOTS = ('docs/', 'tools/', 'src/', 'include/', 'labtalk/', 'coordination/',
         'dottalkpp/', 'scripts/', 'smoke/', 'gui/')
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

PATH_RE = re.compile(r'(?<![\w/.-])((?:%s)[A-Za-z0-9_./-]+)' % '|'.join(ROOTS))


def git(args):
    out = subprocess.run(['git', '--no-optional-locks'] + args,
                         capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else ''


def staged_docs(range_spec):
    if range_spec:
        names = git(['diff', '--name-only', '--diff-filter=ACMR', range_spec])
    else:
        names = git(['diff', '--cached', '--name-only', '--diff-filter=ACMR'])
    return [p for p in names.splitlines() if p.endswith('.md') and os.path.exists(p)]


def cited(doc, rev=None):
    """The paths a document cites -- AS IT READ at `rev`, not as it reads now.

    Reading today's text while resolving targets at an old revision reports every
    document written since as a widow of that commit. Both halves have to come from
    the same moment, which is the same mismatch this check exists to find.
    """
    if rev:
        text = git(['show', '%s:%s' % (rev, doc)])
    else:
        try:
            text = open(doc, encoding='utf-8', errors='replace').read()
        except OSError:
            return set()
    out = set()
    for line in text.replace('\r\n', '\n').split('\n'):
        if SUPPRESS in line:
            continue
        for m in PATH_RE.finditer(line):
            p = m.group(1).rstrip('.,;:)`*')
            if p.endswith(EXTS):
                out.add(p)
    return out


def main(argv):
    rng = argv[0] if argv else None
    docs = staged_docs(rng)
    if not docs:
        print("cited-paths: no documents in scope -- nothing to check")
        return 0

    rev = (rng.split('..')[-1] or 'HEAD') if rng else None
    every = {}
    for d in docs:
        for p in cited(d, rev):
            every.setdefault(p, []).append(d)
    if not every:
        print("cited-paths: %d document(s), no repo paths cited" % len(docs))
        return 0

    paths = sorted(every)
    # Resolve tracked-ness AT THE REVISION, not now. With no range this is the
    # staged index, which is the truth at commit time. With a range it must be
    # that commit's tree -- asking today's index whether a path existed then
    # produces a false CLEAN for every widow since fixed, which is the exact
    # class of false negative this check exists to catch.
    if rng:
        tracked = {p for p in git(['ls-tree', '-r', '--name-only', rev]).splitlines()
                   if p in set(paths)}
    else:
        tracked = {p for p in git(['ls-files', '--'] + paths).splitlines() if p}
    rest = [p for p in paths if p not in tracked]
    ignored = set()
    if rest:
        ignored = {p for p in git(['check-ignore', '--'] + rest).splitlines() if p}

    # In range mode "on disk" means the working tree today, which says nothing
    # about that commit. Report both kinds as WIDOW there rather than guessing.
    widows = [p for p in rest if p not in ignored and (rng or os.path.exists(p))]
    missing = [p for p in rest if p not in ignored and not rng and not os.path.exists(p)]

    print("cited-paths: %d document(s), %d path(s) cited, %d tracked"
          % (len(docs), len(paths), len(tracked)))
    if not (widows or missing or ignored):
        print("cited-paths: OK -- every cited path is tracked")
        return 0

    for p in widows:
        print("  WIDOW   %s -- on disk, NOT tracked" % p)
        for d in every[p]:
            print("          cited by %s" % d)
    for p in missing:
        print("  MISSING %s -- cited, not on disk" % p)
        for d in every[p]:
            print("          cited by %s" % d)
    for p in sorted(ignored):
        print("  IGNORED %s -- `git add` on it is a no-op (R42.1)" % p)
        for d in every[p]:
            print("          cited by %s" % d)
    return 3 if (widows or missing or ignored) else 0


if __name__ == '__main__':
    sys.exit(main([a for a in sys.argv[1:] if not a.startswith('-')]))
