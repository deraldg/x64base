#!/usr/bin/env python3
"""Compatibility launcher for the canonical CMDHELPCHK v2 scanner.

Canonical implementation:
    dottalkpp/tools/help/cmdhelpchk_v2_scan.py

The prior divergent implementation is preserved under tools/help/attic.
This launcher performs no scanning or mutation of its own.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SCANNER = REPO_ROOT / "dottalkpp" / "tools" / "help" / "cmdhelpchk_v2_scan.py"


def main() -> int:
    if not CANONICAL_SCANNER.is_file():
        print(f"canonical CMDHELPCHK v2 scanner missing: {CANONICAL_SCANNER}", file=sys.stderr)
        return 2
    sys.argv[0] = str(CANONICAL_SCANNER)
    runpy.run_path(str(CANONICAL_SCANNER), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
