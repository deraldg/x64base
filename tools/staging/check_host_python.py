#!/usr/bin/env python3
"""check_host_python.py -- gate: host Python commands must use $py12, not bare python.

Why this exists (the gate is the memory, AIF-082): the convention "Windows/host Python that runs
repo tools uses the repo venv `$py12` (D:\\code\\ccode\\.venv312), never bare `python`/`py -3`" is
already in CLAUDE.md, and it STILL gets forgotten when a command is authored -- an application
failure a doc pointer cannot fix. So this converts the rule into a hard-failing gate. A command
that trips this cannot be committed.

Scope of detection (kept tight to avoid false positives on sandbox/Linux examples):
  * `.ps1` / `.psm1` files: every line (these are host scripts).
  * `.md` files: ONLY lines inside a fenced ```powershell / ```pwsh / ```ps1 block (host command
    context). Bash/text/other fences are ignored -- `python3 ...` is correct in the Linux sandbox.
A line is flagged when it invokes a repo tool -- `python` / `python3` / `py -3[.x]` followed by a
`tools/` or `tools\\` path or a `*.py` target -- and does NOT already route through the venv
(`$py12`, `& $py`, or `.venv312`).

Escape hatch (use sparingly, with a reason): append `# host-python-ok: <reason>` to the line.

Exit 0 = clean; exit 2 = at least one violation (blocking).
"""

import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# python / python3 / py -3[.x], then anything, then a repo tool target
INVOKE = re.compile(r'(?<![\w$.])(?:python3?|py\s+-3(?:\.\d+)?)\b[^\n`]*?(?:tools[\\/]|[\w./\\-]+\.py)\b')
# Acceptable: routes through the repo venv var ($py12 / $py) or ANY venv path (venv used, not
# bare system python). "which venv" (.venv vs .venv312) is a softer standards note, not the
# bare-python bug this gate exists to stop.
VENV_OK = re.compile(r'\$py12|\$py\b|[\\/.]venv')
ESCAPE = re.compile(r'#\s*host-python-ok\b')
PS_FENCE = re.compile(r'^\s*```+\s*(powershell|pwsh|ps1)\b', re.I)
ANY_FENCE = re.compile(r'^\s*```+')

SCAN_SUFFIXES = {'.ps1', '.psm1', '.md'}
SKIP_DIRS = {'.git', 'node_modules', 'build', 'build-wsl', '.venv312', 'out', 'dist', '.next'}


def iter_files():
    # Enumerate via `git ls-files` (fast; also scopes the gate to TRACKED files only). This
    # avoids walking the whole tree, which is slow across a mount. Read-only git.
    try:
        out = subprocess.run(
            ['git', 'ls-files', '-z', '*.ps1', '*.psm1', '*.md'],
            cwd=str(REPO), capture_output=True, timeout=60,
            env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
        names = [n for n in out.stdout.decode('utf-8', 'replace').split('\0') if n]
        if names:
            for n in names:
                p = REPO / n
                if not any(part in SKIP_DIRS for part in p.parts):
                    yield p
            return
    except Exception:
        pass
    # Fallback: bounded walk over the doc/script dirs only, never the whole tree.
    for base in ('docs', 'tools', 'labtalk', 'scripts'):
        d = REPO / base
        if d.exists():
            for p in d.rglob('*'):
                if p.suffix.lower() in SCAN_SUFFIXES and not any(part in SKIP_DIRS for part in p.parts):
                    yield p
    for pat in ('*.md', '*.ps1', '*.psm1'):
        for p in REPO.glob(pat):
            yield p


def scan_file(path):
    hits = []
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return hits
    is_ps = path.suffix.lower() in ('.ps1', '.psm1')
    in_ps_fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if not is_ps:
            if PS_FENCE.match(line):
                in_ps_fence = True; continue
            if ANY_FENCE.match(line):
                in_ps_fence = False; continue
            host_context = in_ps_fence
        else:
            host_context = True
        if not host_context:
            continue
        if ESCAPE.search(line) or VENV_OK.search(line):
            continue
        if INVOKE.search(line):
            hits.append((n, line.strip()))
    return hits


def main(argv=None):
    total = 0
    for path in sorted(iter_files()):
        for n, line in scan_file(path):
            total += 1
            rel = path.relative_to(REPO).as_posix()
            print(f"{rel}:{n}: host command uses bare python -- use $py12")
            print(f"    {line}")
    if total:
        print(f"\ncheck-host-python: FAIL -- {total} host command(s) use bare python instead of $py12.")
        print('Fix: `$py12 = "D:\\\\code\\\\ccode\\\\.venv312\\\\Scripts\\\\python.exe"` then `& $py12 <tool> ...`,')
        print('or append `# host-python-ok: <reason>` if the bare form is deliberate.')
        return 2
    print("check-host-python: PASS -- no bare-python host commands.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
