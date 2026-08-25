#!/usr/bin/env python3
"""
lane.py -- worktree lane isolation.  (AIF-084)

Cross-platform by rule: this project is cross-platform C++ with cross-compatible
libraries, so its tooling is too. No PowerShell, no bash, no shell pipelines. Plain
Python 3 + stdlib, ASCII output, POSIX and Windows alike. Where a platform difference is
unavoidable it is isolated to one small helper, not sprayed through the file.

WHY LANES
  Every session editing the same working tree is why work collides. On 2026-08-02 a
  session worked for hours while 191 commits landed from parallel work; three of four
  queued operations were already done by someone else. git worktree was already in use
  here, but manually and optionally -- so most sessions still defaulted to the shared
  tree. This makes the isolated path the cheap path.

  One .git, many working directories. Objects are shared: a worktree costs a checkout,
  not a clone. Two sessions physically cannot edit the same file.

COMMANDS
  python tools/lanes/lane.py list
  python tools/lanes/lane.py new    AIF-085 ollama-triage [--from development]
  python tools/lanes/lane.py finish AIF-085 [--merge] [--delete]
  python tools/lanes/lane.py prune

  --dry-run works on new/finish/prune.

Owner: member.derald . steward: member.ai.claude.cowork . lane: AIF-084 . status: candidate
"""
import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# R126: an AIF number IS AN INTEGER. The zero padding is a DISPLAY convention.
# Match loosely (any width, any padding) and normalise to int; render with %03d,
# which is a MINIMUM width and widens by itself past 999. Measured 2026-08-25:
# `AIF-\d{3}` read "AIF-1000" as NO MATCH in five readers and, in
# tools/tracking/seed_tracking.py, as "AIF-100" -- a DIFFERENT, ALREADY-TAKEN
# number. Silent identity collision, not a decline.
LANE_RE = re.compile(r'^AIF-\d+$')
SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9-]*$')


def repo_root(start=None):
    """The main worktree, whichever directory we were invoked from."""
    p = start or Path(__file__).resolve().parents[2]
    out = run(['git', '-C', str(p), 'rev-parse', '--path-format=absolute',
               '--git-common-dir'], check=False)
    if out:
        return Path(out.strip()).parent
    return p


def run(args, check=True, cwd=None):
    """Run a git command, return stdout. Never raises on a non-zero exit unless check."""
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                           errors='replace', cwd=cwd, timeout=180)
    except Exception as e:
        if check:
            sys.exit(f"error: {' '.join(args)}: {e}")
        return ''
    if r.returncode != 0:
        if check:
            sys.stderr.write(r.stderr or '')
            sys.exit(f"error: {' '.join(args)} exited {r.returncode}")
        return ''
    return r.stdout


def worktrees(root):
    """Parse `git worktree list --porcelain` into dicts."""
    out = run(['git', '-C', str(root), 'worktree', 'list', '--porcelain'], check=False)
    items, cur = [], {}
    for line in out.splitlines():
        if line.startswith('worktree '):
            if cur:
                items.append(cur)
            cur = {'path': line[9:].strip(), 'branch': None, 'prunable': False}
        elif line.startswith('branch '):
            cur['branch'] = line[7:].strip().replace('refs/heads/', '')
        elif line.startswith('prunable'):
            cur['prunable'] = True
    if cur:
        items.append(cur)
    return items


def branch_exists(root, name):
    return bool(run(['git', '-C', str(root), 'rev-parse', '--verify', '--quiet',
                     'refs/heads/' + name], check=False).strip())


def lane_taken(root, lane):
    """Where a lane id already appears. A check, not a reservation -- two sessions
    seconds apart could still collide (see the lane doc's declared non-goals)."""
    hits = []
    intake = root / 'docs' / 'ai-friendly' / 'AI_INTERACTION_INTAKE_QUEUE_V1.md'
    if intake.is_file():
        for line in intake.read_text(encoding='utf-8', errors='replace').splitlines():
            if re.match(r'^\|\s*' + re.escape(lane) + r'\b', line):
                hits.append('intake queue')
                break
    reg = root / 'labtalk' / 'registries'
    for name in ('ai_runs.yaml', 'proofs.yaml'):
        f = reg / name
        if f.is_file() and lane in f.read_text(encoding='utf-8', errors='replace'):
            hits.append(name)
    for d in reg.glob('*.d'):
        for f in d.glob('*.yaml'):
            if lane in f.read_text(encoding='utf-8', errors='replace'):
                hits.append(d.name + ' fragments')
                break
    return hits


def cmd_list(root, _args):
    print("\nworktrees")
    main = str(root)
    any_stale = False
    for w in worktrees(root):
        is_main = Path(w['path']).resolve() == Path(main).resolve()
        kind = 'integration' if is_main else 'lane'
        tag = ''
        if w['prunable']:
            any_stale = True
            tag = '   [reported STALE from here]'
        print("  {:<12} {:<44} {}{}".format(kind, w['branch'] or '(detached)', w['path'], tag))
    if any_stale:
        # Staleness is judged by whether git can reach the path FROM THIS PROCESS. An agent
        # sandbox and the maintainer's machine mount different filesystems, so a worktree on
        # an unreachable drive is reported prunable even when it is perfectly healthy. This
        # bit us once already: a lane doc claimed two worktrees were abandoned when one was
        # live. Confirm on the machine that owns the paths before pruning.
        print("\n  NOTE: 'STALE' means git could not reach that path from HERE.")
        print("        A path on a drive this process cannot see is reported stale even when")
        print("        it is healthy. Verify on the machine that owns the path, then:")
        print("          python tools/lanes/lane.py prune --dry-run")
    print()
    return 0


def cmd_prune(root, args):
    cmd = ['git', '-C', str(root), 'worktree', 'prune', '-v']
    if args.dry_run:
        cmd.append('--dry-run')
    out = run(cmd, check=False)
    print(out.rstrip() or ('nothing to prune' if not args.dry_run else 'nothing would be pruned'))
    return 0


def cmd_new(root, args):
    lane, slug = args.lane, args.slug
    if not LANE_RE.match(lane):
        sys.exit("lane must look like AIF-085 (got '%s')" % lane)
    if not SLUG_RE.match(slug):
        sys.exit("slug must be lower-kebab, e.g. ollama-triage (got '%s')" % slug)

    branch = 'lane/%s-%s' % (lane, slug)
    wt_root = root.parent / (root.name + '.worktrees')
    path = wt_root / ('%s-%s' % (lane, slug))

    if not args.force:
        hits = lane_taken(root, lane)
        if hits:
            sys.exit("%s already appears in: %s\n"
                     "Pick a free number, or pass --force if you are resuming that lane."
                     % (lane, ', '.join(sorted(set(hits)))))
    if branch_exists(root, branch):
        sys.exit("branch '%s' already exists.\nResume it with:\n  git worktree add \"%s\" %s"
                 % (branch, path, branch))
    if path.exists():
        sys.exit("path already exists: %s" % path)
    if not branch_exists(root, args.base):
        avail = run(['git', '-C', str(root), 'branch', '--format=%(refname:short)'],
                    check=False).split()
        sys.exit("base branch '%s' not found. Local branches: %s" % (args.base, ', '.join(avail)))

    base_sha = run(['git', '-C', str(root), 'rev-parse', '--short', args.base]).strip()

    print("\nplan")
    print("  lane    %s" % lane)
    print("  branch  %s" % branch)
    print("  path    %s" % path)
    print("  from    %s @ %s" % (args.base, base_sha))
    if args.dry_run:
        print("\ndry run: nothing created.\n")
        return 0

    wt_root.mkdir(parents=True, exist_ok=True)
    run(['git', '-C', str(root), 'worktree', 'add', '-b', branch, str(path), args.base])

    (path / 'LANE.md').write_text(LANE_MD.format(
        lane=lane, slug=slug, branch=branch, base=args.base, sha=base_sha,
        created=datetime.now().strftime('%Y-%m-%d %H:%M'), root=root, path=path,
    ), encoding='utf-8')

    print("\nlane ready")
    print("  cd %s" % path)
    print("  finish:  python tools/lanes/lane.py finish %s" % lane)
    print()
    return 0


def cmd_finish(root, args):
    lane = args.lane
    if not LANE_RE.match(lane):
        sys.exit("lane must look like AIF-085 (got '%s')" % lane)

    wt = None
    for w in worktrees(root):
        if (w['branch'] or '').startswith('lane/%s-' % lane) or ('%s-' % lane) in Path(w['path']).name:
            wt = w
            break
    if not wt:
        print("no open worktree for %s" % lane)
        return cmd_list(root, args)

    path, branch = Path(wt['path']), wt['branch']
    print("\n%s" % lane)
    print("  branch  %s" % branch)
    print("  path    %s" % path)

    if not path.exists():
        print("  directory is gone -- the record is stale. Run: lane.py prune")
        return 0

    # REFUSE on uncommitted work. Report it; never discard it.
    dirty = [l for l in run(['git', '-C', str(path), 'status', '--porcelain'],
                            check=False).splitlines() if l.strip()]
    if dirty:
        print("\nREFUSING -- uncommitted work in this lane (%d entr%s):"
              % (len(dirty), 'y' if len(dirty) == 1 else 'ies'))
        for l in dirty[:20]:
            print("    %s" % l)
        if len(dirty) > 20:
            print("    ... and %d more" % (len(dirty) - 20))
        print("\nNothing was removed. Commit it, or deliberately discard it, then re-run:")
        print("    cd %s" % path)
        print("    git add -- <paths>       # stage explicitly; never `git add -A` here")
        print("    git commit")
        return 1
    print("  clean (no uncommitted work)")

    ahead_s = run(['git', '-C', str(path), 'rev-list', '--count',
                   '%s..%s' % (args.into, branch)], check=False).strip() or '0'
    ahead = int(ahead_s or 0)
    print("  commits ahead of %s: %d" % (args.into, ahead))

    if args.dry_run:
        print("\ndry run: would %sremove the worktree%s.\n"
              % ('merge then ' if args.merge else '', ' and delete the branch' if args.delete else ''))
        return 0

    if args.merge and ahead:
        on = run(['git', '-C', str(root), 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
        if on != args.into:
            sys.exit("integration tree is on '%s', expected '%s'. Switch it first." % (on, args.into))
        main_dirty = [l for l in run(['git', '-C', str(root), 'status', '--porcelain'],
                                     check=False).splitlines() if l.strip()]
        if main_dirty:
            sys.exit("integration tree has %d uncommitted change(s). Merging into a dirty "
                     "tree is how work gets lost. Commit or stash there first." % len(main_dirty))
        print("\nmerging %s -> %s ..." % (branch, args.into))
        run(['git', '-C', str(root), 'merge', '--no-ff', branch,
             '-m', 'merge %s into %s (%s)' % (branch, args.into, lane)])
        print("merged.")
    elif ahead and not args.merge:
        print("\n  NOTE: %d commit(s) on '%s' are not in %s." % (ahead, branch, args.into))
        print("  The branch is kept, so nothing is lost. Merge later, or re-run with --merge.")

    print("\nremoving worktree ...")
    run(['git', '-C', str(root), 'worktree', 'remove', str(path)])
    run(['git', '-C', str(root), 'worktree', 'prune'], check=False)
    print("removed.")

    if args.delete:
        still = run(['git', '-C', str(root), 'rev-list', '--count',
                     '%s..%s' % (args.into, branch)], check=False).strip() or '0'
        if int(still or 0) > 0:
            print("\nNOT deleting '%s': %s commit(s) not in %s. That would lose them."
                  % (branch, still, args.into))
        else:
            run(['git', '-C', str(root), 'branch', '-d', branch], check=False)
            print("branch '%s' deleted (fully merged)." % branch)

    print("\n%s closed" % lane)
    return cmd_list(root, args)


LANE_MD = """# {lane} -- {slug}

Working lane. This directory is a **git worktree**, not a clone: it shares
`{root}/.git`. Edits here cannot collide with any other session.

| | |
|---|---|
| Lane | `{lane}` |
| Branch | `{branch}` |
| Based on | `{base}` @ `{sha}` |
| Created | {created} |
| Integration tree | `{root}` (do not edit it from here) |

## Rules

- Work and commit **on this branch only**. Do not switch branches in this directory.
- Do not edit the integration tree while this lane is open -- that is the collision this
  exists to prevent.
- Registry records go in `labtalk/registries/*.d/` as ONE NEW FILE, never by editing a
  flat `.yaml`. Then: `python tools/registries/registry_fragments.py merge --write`
- Read `labtalk/ai_portal/AI_ENGINEERING_STANDARDS_SEED_V1.md` before changing source.
- Tooling here is cross-platform Python by rule. No PowerShell, no bash.

## Finish

```
python tools/lanes/lane.py finish {lane}            # remove the worktree (branch kept)
python tools/lanes/lane.py finish {lane} --merge    # merge into {base} first
```

Leaving this lying around is how the previous attempt decayed. Close it when done.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', default=None, help='repo root (default: auto-detect)')
    sub = ap.add_subparsers(dest='cmd', required=True)

    sub.add_parser('list', help='show worktrees, marking stale ones')

    p = sub.add_parser('prune', help='clear stale worktree records')
    p.add_argument('--dry-run', action='store_true')

    p = sub.add_parser('new', help='create a lane worktree')
    p.add_argument('lane'); p.add_argument('slug')
    p.add_argument('--from', dest='base', default='development')
    p.add_argument('--force', action='store_true', help='allow a lane id already in use')
    p.add_argument('--dry-run', action='store_true')

    p = sub.add_parser('finish', help='close a lane worktree')
    p.add_argument('lane')
    p.add_argument('--merge', action='store_true')
    p.add_argument('--delete', action='store_true', help='delete the branch if fully merged')
    p.add_argument('--into', default='development')
    p.add_argument('--dry-run', action='store_true')

    a = ap.parse_args()
    if not hasattr(a, 'dry_run'):
        a.dry_run = False
    root = Path(a.root).resolve() if a.root else repo_root()
    return {'list': cmd_list, 'prune': cmd_prune, 'new': cmd_new, 'finish': cmd_finish}[a.cmd](root, a)


if __name__ == '__main__':
    raise SystemExit(main())
