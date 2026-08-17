#!/usr/bin/env python3
"""Drift guard for the SELFDOC catalogs in schema_registry.py.

The identity/bbs/portal tables are checked against the C++ schema headers by
test_schema_registry.py. The selfdoc catalogs have no C++ header -- their source
of truth is the reviewed .dtschema contract under data/schemas/**. This test
reparses the FIELDS: block of each contract and asserts the registry's field
sequence is DERIVED, not re-authored, so it cannot quietly drift. Pure file
parsing, no engine -- runs in the sandbox.

R1 (SELFDOC_PORTAL_SCHEMA_SHARING_STUDY_V1): only SYSCMD is registered so far.
Add a table by (1) adding its TableSpec to SELFDOC in schema_registry.py and
(2) adding its .dtschema path to DTSCHEMA below. A selfdoc table registered
without a DTSCHEMA mapping is a hard failure here -- we do not register a catalog
we cannot check against a contract.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import schema_registry as reg  # noqa: E402

REPO = HERE.parents[2]
SCHEMAS = REPO / "dottalkpp" / "data" / "schemas"

# selfdoc table -> its reviewed .dtschema contract (the source of truth).
DTSCHEMA = {
    "SYSCMD": SCHEMAS / "metadata" / "syscmd_catalog.dtschema",
    # Queued, pending the VER_AT normalization decision (study R5) and, for the
    # locale companions, a confirmed soft-close ladder:
    #   "SYSMSG": SCHEMAS / "metadata" / "sysmsg_catalog.dtschema",
    #   "HELP_TOPIC_LOCALE":   SCHEMAS / "help" / "help_locale_companions.dtschema",
    #   "HELP_SECTION_LOCALE": SCHEMAS / "help" / "help_locale_companions.dtschema",
    #   "HELP_LINE_LOCALE":    SCHEMAS / "help" / "help_locale_companions.dtschema",
    #   "HELP_ARTIFACT_LOCALE":SCHEMAS / "help" / "help_locale_companions.dtschema",
    #   "SYSTEM_MESSAGES":     SCHEMAS / "messaging" / "message_catalog.dtschema",
    #   "SYSTEM_MESSAGE_TEXT": SCHEMAS / "messaging" / "message_catalog.dtschema",
}

FIELD_RE = re.compile(r"^\s+(\w+)\s+TYPE=([CNLMD])\s+LEN=(\d+)")

PASS = 0
FAIL = 0


def check(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {msg}")


def parse_dtschema_fields(path: Path, table: str):
    """Return [(name, type, width), ...] for the `TABLE: <table>` FIELDS block.

    A .dtschema may hold several TABLE blocks (the HELP locale companions do), so
    we locate the requested table first, then read its FIELDS: block up to the
    next blank line or section header.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    i, n = 0, len(lines)
    while i < n and lines[i].strip() != f"TABLE: {table}":
        i += 1
    if i >= n:
        return None
    while i < n and lines[i].strip() != "FIELDS:":
        i += 1
    i += 1
    out = []
    while i < n:
        m = FIELD_RE.match(lines[i])
        if m:
            out.append((m.group(1), m.group(2), int(m.group(3))))
            i += 1
        elif lines[i].strip() == "" and out:
            break
        elif lines[i].strip() == "":
            i += 1
        else:
            break
    return out


def _selfdoc_tables():
    # selfdoc catalogs are the subdir="" entries in the registry.
    return {n: s for n, s in reg.TABLES.items() if s.subdir == ""}


def test_selfdoc_registry_matches_dtschema():
    for name, spec in _selfdoc_tables().items():
        check(name in DTSCHEMA,
              f"{name}: selfdoc table registered with no .dtschema source mapping")
        if name not in DTSCHEMA:
            continue
        parsed = parse_dtschema_fields(DTSCHEMA[name], name)
        check(parsed is not None and len(parsed) > 0,
              f"{name}: no FIELDS parsed from {DTSCHEMA[name].name}")
        if not parsed:
            continue
        check(tuple(parsed) == tuple(spec.fields),
              f"{name}: registry != .dtschema\n    dtschema: {parsed}\n    "
              f"registry: {list(spec.fields)}")


def test_selfdoc_is_read_only():
    """Guard the orthogonality boundary: selfdoc is pipeline-owned; the CRUD must
    not open a second writer into it (same posture as the daemon-owned bbs store).
    """
    for name, spec in _selfdoc_tables().items():
        check(spec.writable is False,
              f"{name}: selfdoc catalog must be writable=False in R1")


def test_selfdoc_close_targets_exist():
    for name, spec in _selfdoc_tables().items():
        names = set(spec.field_names())
        for attr in ("field", "epoch", "rowver"):
            val = getattr(spec.close, attr)
            if val is not None:
                check(val in names, f"{name}: close.{attr}={val} not a field")


def main():
    for nm, fn in sorted(globals().items()):
        if nm.startswith("test_") and callable(fn):
            fn()
    print(f"\ntest_schema_registry_selfdoc: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
