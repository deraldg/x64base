#!/usr/bin/env python3
"""
restore_lfs.py -- materialise tracked files whose committed blob is an LFS pointer.

Cross-platform by rule: plain Python 3 + stdlib, ASCII output, no shell. Replaces an
earlier PowerShell version.

THE PROBLEM IT SOLVES (measured in this repo, 2026-08-02)
  Eight files under tools/*.zip are committed as LFS POINTER blobs, but .gitattributes
  declares:

      *.zip       binary          <- NOT: *.zip filter=lfs diff=lfs merge=lfs -text

  With no filter attribute, nothing converts pointer -> content on checkout, so the files
  never appear. git reports them as ' D' (deleted).

  Notes on what does NOT work here:
    - `git lfs checkout` -- no attribute routes these paths, so it has nothing to do.
    - `git checkout -- tools/` -- writes the 129-byte POINTER TEXT into the files, which
      is worse than missing because it looks fixed.
  Whether git-lfs is installed is irrelevant to this particular failure.

  THE HAZARD: `git add -A` / `git commit -a` records the DELETION of those files.

WHY COPYING IS THE CORRECT FIX, NOT A WORKAROUND
  .git/lfs/objects already holds the objects at exactly the sizes their pointers declare.
  Reading the pointer and copying the object into place is precisely what a smudge filter
  would do -- done explicitly, because no filter is configured.

  python tools/git/restore_lfs.py            # report only (default: safe)
  python tools/git/restore_lfs.py --write    # actually restore

Owner: member.derald . steward: member.ai.claude.cowork . lane: AIF-084 . status: candidate
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

PTR_SPEC = 'git-lfs.github.com/spec'
OID_RE = re.compile(r'^oid sha256:([0-9a-f]{64})\s*$', re.M)
SIZE_RE = re.compile(r'^size (\d+)\s*$', re.M)
# only bother reading blobs for paths that could plausibly be pointers
CANDIDATE = re.compile(r'\.(zip|7z|gz|tar|png|jpg|jpeg|gif|pdf|mp4|mov|bin|exe|dll|so|dylib)$', re.I)


def git(root, *args, binary=False):
    r = subprocess.run(['git', '-C', str(root)] + list(args),
                       capture_output=True, timeout=180)
    if r.returncode != 0:
        return None
    return r.stdout if binary else r.stdout.decode('utf-8', 'replace')


def repo_root(start=None):
    p = start or Path(__file__).resolve().parents[2]
    out = git(p, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    return Path(out.strip()).parent if out else p


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', default=None)
    ap.add_argument('--write', action='store_true', help='restore (default is report only)')
    a = ap.parse_args()
    root = Path(a.root).resolve() if a.root else repo_root()

    listing = git(root, 'ls-files')
    if listing is None:
        sys.exit("error: not a git repository: %s" % root)

    print("\nLFS pointer restore")
    print("  repo: %s" % root)
    print("  mode: %s\n" % ('WRITE' if a.write else 'report only (pass --write to restore)'))

    restored = already = 0
    problems = []

    for rel in listing.splitlines():
        rel = rel.strip()
        if not rel or not CANDIDATE.search(rel):
            continue
        blob = git(root, 'show', 'HEAD:' + rel)
        if not blob or PTR_SPEC not in blob:
            continue                                   # not an LFS pointer
        m_oid, m_size = OID_RE.search(blob), SIZE_RE.search(blob)
        if not (m_oid and m_size):
            problems.append("%s (pointer present but unparseable)" % rel)
            continue
        oid, size = m_oid.group(1), int(m_size.group(1))

        target = root / rel
        on_disk = target.stat().st_size if target.exists() else -1
        if on_disk == size:
            already += 1
            continue

        obj = root / '.git' / 'lfs' / 'objects' / oid[:2] / oid[2:4] / oid
        if not obj.is_file():
            problems.append("%s (object %s... not in local store; needs `git lfs pull`)"
                            % (rel, oid[:12]))
            continue
        obj_size = obj.stat().st_size
        if obj_size != size:
            problems.append("%s (local object %d B, pointer says %d B -- refusing)"
                            % (rel, obj_size, size))
            continue

        was = 'missing' if on_disk < 0 else ('%d B' % on_disk)
        if not a.write:
            print("  would restore  %8d B  %s   (was %s)" % (size, rel, was))
            restored += 1
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(obj, target)
        now = target.stat().st_size
        if now != size:
            problems.append("%s (copied but size %d != %d)" % (rel, now, size))
            continue
        print("  restored       %8d B  %s   (was %s)" % (size, rel, was))
        restored += 1

    print("\n  %s %d file(s); %d already correct."
          % ('would restore' if not a.write else 'restored', restored, already))
    if problems:
        print("\n  COULD NOT RESTORE:")
        for p in problems:
            print("    %s" % p)

    if a.write and restored:
        print("""
  EXPECT `git status` TO NOW SHOW THESE AS MODIFIED, NOT CLEAN.
  That is correct. The committed blob is the ~129-byte POINTER; the working file is now
  the real content, and with no filter attribute git compares raw bytes. Verified by test.
  Nothing is wrong -- the state simply moved from 'deleted' to 'differs from the pointer'.""")

    print("""
THE DURABLE FIX -- a repository-shape decision, not this tool's call

  A. Let LFS actually manage them. In .gitattributes:
         *.zip  filter=lfs diff=lfs merge=lfs -text
     then: git add --renormalize tools && git lfs checkout
     Right if large binaries are expected here later.

  B. Stop using LFS for these. At 1-4 KB each LFS buys nothing, and a pointer-without-
     attribute state is what produced these phantom deletions in the first place.
     Restore with this tool, then commit -- the 'modified' state above IS option B
     half-done: committing it replaces each pointer with the real bytes.
         python tools/git/restore_lfs.py --write
         git add -- tools/*.zip          # explicit paths, never -A
         git commit -m "restore tools/*.zip as ordinary blobs (drop stray LFS pointers)"

  Until one of those is done, do not run `git add -A` or `git commit -a` here while any
  of these files are missing -- it records their deletion.
""")
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
