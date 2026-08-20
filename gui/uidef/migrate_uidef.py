#!/usr/bin/env python3
"""AIF-120 R71 -- retarget every cited path from tools/uidef to gui/uidef.

Run AFTER `git mv tools/uidef gui/uidef`, from the repo root, in the SAME commit
as the move. The citation gate (tools/staging/check_cited_paths.py) reads paths
out of prose; if the files move in one commit and the prose in another, the gate
sees 55 widows in between and the ledger is briefly lying.

Measured before writing: 251 occurrences across 54 documents under
docs/maintenance/, plus 31 more inside the tooling's own comments, usage strings
and shell scripts. Nothing in CMake, cmake/, tools/gates, tools/ci or
scripts/ references tools/uidef -- checked, not assumed -- so the build is not
part of this change.

Prints a per-file count and a total, and exits non-zero if the total does not
match what it found, so a partial run cannot look like a clean one.

ALSO WRITES `tmp/r71_stage_list.txt` -- the exact paths it modified, one per
line, for `git add --pathspec-from-file`. Added after the first attempt at this
commit was blocked by the prepush gate: the handoff said `git add
docs/maintenance`, a directory add, which staged 967 paths including 199 data
fixtures and hundreds of other sessions' untracked documents, and failed
house-style on 405 non-ASCII lines that belonged to other lanes. A tool that
knows exactly which files it touched and then leaves the operator to name them
by hand has handed back the one job it was in a position to do.
"""
import os
import re
import sys

OLD = 'tools/uidef'
NEW = 'gui/uidef'
# Two roots, and the second one was nearly missed. The first draft covered only
# the documentation, on the assumption that the tooling does not name its own
# location. It does: 31 times, in usage strings, build comments and shell
# scripts. `cite_check.py` prints `python tools/uidef/cite_check.py` as its own
# usage line -- after the move that instruction would be wrong, printed by the
# gate whose entire job is catching stale paths.
#
# None of the 31 is an executable dependency (no import, open, Path or
# subprocess resolves through them -- checked). They are prose inside code,
# which is exactly the kind of staleness that survives a green test run.
ROOTS = ['docs/maintenance', 'gui/uidef']
EXTS = ('.md', '.py', '.cpp', '.h', '.sh')

# One deliberate exception: this gate's own docstring cites the path as an
# EXAMPLE of a working-copy path and already carries a cite-check:ignore marker.
SKIP = {'tools/staging/check_cited_paths.py',
        'gui/uidef/migrate_uidef.py'}   # this file names both paths on purpose

# Written for `git add --pathspec-from-file`. Under tmp/, which is gitignored,
# so the manifest never becomes a tracked artifact of its own migration.
STAGE_LIST = 'tmp/r71_stage_list.txt'
# Paths that change but are not discovered by the rewrite: the moved directory
# itself, its new README, and the registry row that declares the new root.
EXTRA_STAGE = ['gui/README.md', 'gui/uidef', 'labtalk/registries/projects.yaml']


def main():
    if not os.path.isdir(NEW):
        print('REFUSED: %s does not exist -- run `git mv %s %s` first.'
              % (NEW, OLD, NEW))
        return 2
    if os.path.isdir(OLD):
        print('REFUSED: %s still exists -- the move did not happen, and '
              'rewriting citations now would point them at a directory that '
              'is not the one holding the files.' % OLD)
        return 2

    total = 0
    touched = 0
    changed = []
    for root in ROOTS:
        for dirpath, _dirs, files in os.walk(root):
            for fn in sorted(files):
                if not fn.endswith(EXTS):
                    continue
                if '__pycache__' in dirpath:
                    continue
                p = os.path.join(dirpath, fn).replace('\\', '/')
                if p in SKIP:
                    continue
                with open(p, 'r', encoding='utf-8', newline='') as fh:
                    s = fh.read()
                n = s.count(OLD)
                if not n:
                    continue
                with open(p, 'w', encoding='utf-8', newline='') as fh:
                    fh.write(s.replace(OLD, NEW))
                print('  %-58s %3d' % (p, n))
                changed.append(p)
                total += n
                touched += 1

    print('\n%d occurrence(s) retargeted across %d document(s).' % (total, touched))

    # Assert, do not assume. A green exit code is not proof (Tier 1 seed s4).
    left = 0
    for root in ROOTS:
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                if not fn.endswith(EXTS) or '__pycache__' in dirpath:
                    continue
                p = os.path.join(dirpath, fn).replace('\\', '/')
                if p in SKIP:
                    continue
                with open(p, 'r', encoding='utf-8') as fh:
                    left += fh.read().count(OLD)
    if left:
        print('FAIL: %d occurrence(s) of %s still present.' % (left, OLD))
        return 1
    print('VERIFIED: no occurrence of %s remains under %s.' % (OLD, ', '.join(ROOTS)))

    # The stage list. Only files under docs/ go in from `changed`; everything
    # under gui/uidef is already covered by staging the directory itself.
    stage = list(EXTRA_STAGE) + [p for p in changed if p.startswith('docs/')]
    os.makedirs(os.path.dirname(STAGE_LIST), exist_ok=True)
    with open(STAGE_LIST, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(stage) + '\n')
    print('WROTE %s -- %d path(s). Stage with:' % (STAGE_LIST, len(stage)))
    print('    git add --pathspec-from-file=%s' % STAGE_LIST)
    print('  Do NOT `git add docs/maintenance`. It is a directory add, and the')
    print('  house rule against `git add -A` is about breadth, not spelling.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
