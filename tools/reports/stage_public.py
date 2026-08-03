#!/usr/bin/env python3
"""
stage_public.py -- regenerate the reports in PUBLIC mode and stage them to the website.

Cross-platform by rule: Python 3 + stdlib, ASCII output, no shell. Replaces an earlier
PowerShell version.

WHY THIS EXISTS
  The site's public/reports/ was once populated by a plain COPY of the full internal
  build. A copy cannot apply --public, so nothing enforced the `sensitivity:` marks in
  portal.yaml -- it only happened to be correct that day. Feeding the site by
  REGENERATION means the registry actually governs what ships.

WHAT IS AND IS NOT WITHHELD
  Withheld: anything marked `sensitivity: private` in labtalk/registries/portal.yaml --
  currently the BBS access report (an authentication-surface map) and the rulings report.
  NOT withheld: board.worklog and the RUN=AIPR- agent handoffs. This is an alpha
  open-source project and the agent-coordination surface is the point of the BBS lane
  being visible at all. Per-board redaction, if ever needed, is registry-driven via
  `redacted_boards:` under portal.reports.

  python tools/reports/stage_public.py                      # dry run
  python tools/reports/stage_public.py --write
  python tools/reports/stage_public.py --site <path> --write

Owner: member.derald . steward: member.ai.claude.cowork . lane: AIF-084 . status: candidate
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Content that must never reach the published copy. Deliberately short: each entry is a
# thing we have a concrete reason to withhold, not a guess.
LEAK_PATTERNS = [
    (re.compile(r'[A-Za-z]:[\\/](code|dev)[\\/]'), 'internal absolute path'),
    (re.compile(r'token set'),                     'credential-state marker'),
]
# Files that must not appear at all, whatever their content.
FORBIDDEN = {'BBS_ACCESS_REPORT.html': 'authentication-surface map (member keys, permission matrix, port)'}


def repo_root(start=None):
    p = start or Path(__file__).resolve().parents[2]
    try:
        r = subprocess.run(['git', '-C', str(p), 'rev-parse', '--path-format=absolute',
                            '--git-common-dir'], capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return Path(r.stdout.strip()).parent
    except Exception:
        pass
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', default=None, help='repo root (default: auto-detect)')
    ap.add_argument('--site', default=None,
                    help='site public/reports dir (default: <repo>/../../dev/x64base-site/public/reports)')
    ap.add_argument('--write', action='store_true', help='actually stage (default: dry run)')
    a = ap.parse_args()

    root = Path(a.root).resolve() if a.root else repo_root()
    builder = root / 'tools' / 'reports' / 'build_reports.py'
    if not builder.is_file():
        sys.exit("error: %s not found" % builder)

    site = Path(a.site).resolve() if a.site else \
        (root.parent.parent / 'dev' / 'x64base-site' / 'public' / 'reports')
    if not site.parent.exists():
        sys.exit("error: site public/ not found: %s\n       pass --site <path>" % site.parent)

    print("\nstage public reports")
    print("  repo:  %s" % root)
    print("  site:  %s" % site)
    print("  mode:  %s\n" % ('WRITE' if a.write else 'dry run (pass --write to stage)'))

    # 1. Build into a clean temp dir. Never generate straight into the site -- a failed
    #    run would leave a half-updated published directory.
    with tempfile.TemporaryDirectory(prefix='x64base-public-') as tmp:
        staging = Path(tmp)
        r = subprocess.run([sys.executable, str(builder), '--root', str(root),
                            '--out', str(staging), '--public'],
                           capture_output=True, text=True, errors='replace', timeout=600)
        sys.stdout.write(r.stdout)
        if r.returncode != 0:
            sys.stderr.write(r.stderr)
            sys.exit("error: build_reports.py exited %d" % r.returncode)

        produced = sorted(p for p in staging.iterdir() if p.is_file())
        if not produced:
            sys.exit("error: the public build produced nothing")

        # 2. Guards. Fail loudly rather than publish something sensitive.
        leaks = []
        for f in produced:
            if f.name in FORBIDDEN:
                leaks.append("%s present -- %s" % (f.name, FORBIDDEN[f.name]))
            if f.suffix.lower() not in ('.html', '.css', '.js', '.md'):
                continue
            text = f.read_text(encoding='utf-8', errors='replace')
            for rx, why in LEAK_PATTERNS:
                if rx.search(text):
                    leaks.append("%s: %s" % (f.name, why))
        if leaks:
            print("REFUSING TO STAGE -- sensitive content in the public build:")
            for l in leaks:
                print("  %s" % l)
            sys.exit("\nNothing was copied.")
        print("guards passed: no forbidden report, no internal paths, no credential markers")

        print("\nwould stage:" if not a.write else "\nstaging:")
        for f in produced:
            print("  %-34s %8d bytes" % (f.name, f.stat().st_size))

        if not a.write:
            print("\ndry run: site not modified.\n")
            return 0

        # 3. Replace wholesale, so a report deleted upstream also disappears here.
        if site.exists():
            shutil.rmtree(site)
        site.mkdir(parents=True)
        for f in produced:
            shutil.copy2(f, site / f.name)

    print("\nstaged %d file(s) to %s" % (len(produced), site))
    print("""
LOCAL PREVIEW CAVEAT
  next.config.mjs sets trailingSlash:true, so `next dev` redirects /reports/index.html
  to /reports/index.html/ and 404s. That is DEV ONLY -- Apache and GitHub Pages serve
  the file and honour DirectoryIndex. To view locally, open the file directly:
    %s

  Deploying to the live site is a separate step in the site repo.
""" % (site / 'index.html'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
