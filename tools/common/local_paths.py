#!/usr/bin/env python3
"""Machine-absolute path detection, from one authority.

Loads `local_paths.json` (same directory) and exposes the compiled patterns.
The JSON is the single source of truth because `rebuild-staging.ps1` reads the
same file -- a Python-only module would have left the PowerShell guard as a
tenth private copy, which is the defect this replaces.

Usage:

    from local_paths import windows_drive, posix_host, dev_roots_only, any_local
    hits = any_local().findall(text)

Run it directly to execute the test table in the JSON:

    python tools/common/local_paths.py        # exit 0 = every case agrees

Why report-only: some absolute paths are legitimate -- `ops/Setup-VDisk.ps1`
documents host disk layout, prose quotes engine output, SFTP examples name
`/home/<user>` on example.com. These functions FIND; the caller decides. A
guard that fires on correct input trains people to bypass it, which is how the
2026-08-13 'https as drive s:' false positive went unnoticed long enough to
mangle a published URL.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = json.loads((_HERE / "local_paths.json").read_text(encoding="utf-8"))


def _compile(name: str) -> re.Pattern:
    return re.compile(_SPEC["patterns"][name]["regex"])


def windows_drive() -> re.Pattern:
    """Drive-rooted Windows paths. Excludes URL schemes."""
    return _compile("windows_drive")


def posix_host() -> re.Pattern:
    """Host paths as WSL or a mounted sandbox sees them."""
    return _compile("posix_host")


def dev_roots_only() -> re.Pattern:
    """Only paths under a known development/staging root. Narrower, less noise."""
    return _compile("dev_roots_only")


def any_local() -> re.Pattern:
    """Windows OR POSIX. Use this unless you have a reason to be narrower.

    Most callers want this one. The predecessors defaulted to Windows-only,
    which is why 23 tracked files carrying /mnt/d/code/ccode were invisible to
    every guard except the gptbase bundler.
    """
    return re.compile(
        "(?:" + _SPEC["patterns"]["windows_drive"]["regex"]
        + "|" + _SPEC["patterns"]["posix_host"]["regex"] + ")"
    )


def selftest() -> int:
    """Run the JSON's own test table. Returns 0 on full agreement."""
    bad = 0
    for name in _SPEC["patterns"]:
        pat = _compile(name)
        for s in _SPEC["tests"]["must_match"].get(name, []):
            if not pat.search(s):
                print(f"FAIL {name}: should MATCH but did not -- {s}")
                bad += 1
        for s in _SPEC["tests"]["must_not_match"].get(name, []):
            if pat.search(s):
                print(f"FAIL {name}: should NOT match but did -- {s}")
                bad += 1
    total = sum(len(v) for v in _SPEC["tests"]["must_match"].values())
    total += sum(len(v) for v in _SPEC["tests"]["must_not_match"].values())
    print(f"local_paths selftest: {total - bad}/{total} cases agree"
          + ("" if bad else "  OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(selftest())
