#!/usr/bin/env python3
"""Drift guard: the CRUD registry must match the C++ schema headers.

Reparses the FieldSpec declarations in identity_schema.hpp / bbs_schema.hpp /
ruling_schema.hpp / tracking_schema.hpp and asserts schema_registry.py has the same
(name, type, width) sequence per table. This is the dogfood ethos applied to the
tool itself: the registry is DERIVED from the headers, so it cannot quietly drift.
Runs in the sandbox (pure file parsing, no engine).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import schema_registry as reg  # noqa: E402

REPO = HERE.parents[2]
INC = REPO / "include"

HEADER = {
    "identity": INC / "identity" / "identity_schema.hpp",
    "bbs": INC / "bbs" / "bbs_schema.hpp",
    "portal_ruling": INC / "portal" / "ruling_schema.hpp",
    "portal_tracking": INC / "portal" / "tracking_schema.hpp",
}

# Width constants used across the headers (leaf name after '::' -> value).
LEAF = {
    "ID": 20, "KEY": 64, "NAME": 48, "CLS": 24, "TEXT": 160, "CRED": 128,
    "SUBJ": 160, "BODY": 240, "LKEY": 16, "RULEID": 16, "LANE": 12,
    "GROUP": 24, "NOTE": 240,
}

FIELD_RE = re.compile(r'\b([NCL])\("(\w+)"(?:\s*,\s*([^)]+))?\)')

PASS = 0
FAIL = 0


def check(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {msg}")


def resolve_width(tok: str | None) -> int:
    if tok is None:
        return 1  # L
    tok = tok.strip()
    leaf = tok.split("::")[-1]
    if leaf in LEAF:
        return LEAF[leaf]
    return int(tok)


def header_for(spec: reg.TableSpec) -> Path:
    if spec.subdir == "portal":
        return HEADER["portal_ruling"] if spec.name == "SYSRULING" \
            else HEADER["portal_tracking"]
    return HEADER[spec.subdir]


def parse_table_fields(text: str, table: str):
    """Return [(name, type, width), ...] for the {"TABLE", { ... }} block."""
    anchor = text.find(f'{{"{table}",')
    if anchor < 0:
        return None
    # inner field list ends at the first '}}' after the anchor
    end = text.find("}}", anchor)
    block = text[anchor:end]
    out = []
    for m in FIELD_RE.finditer(block):
        typ, name, wtok = m.group(1), m.group(2), m.group(3)
        out.append((name, typ, resolve_width(wtok)))
    return out


def test_every_table_matches_header():
    for name, spec in reg.TABLES.items():
        text = header_for(spec).read_text(encoding="utf-8", errors="replace")
        parsed = parse_table_fields(text, name)
        check(parsed is not None, f"{name}: not found in {header_for(spec).name}")
        if parsed is None:
            continue
        check(tuple(parsed) == tuple(spec.fields),
              f"{name}: registry != header\n    header:   {parsed}\n    "
              f"registry: {list(spec.fields)}")


def test_policy_targets_exist():
    """Every close-policy field/epoch/rowver must be a real field of its table."""
    for name, spec in reg.TABLES.items():
        names = set(spec.field_names())
        p = spec.close
        for attr in ("field", "epoch", "rowver"):
            val = getattr(p, attr)
            if val is not None:
                check(val in names, f"{name}: close.{attr}={val} not a field")
        for k in spec.ckey:
            check(k in names, f"{name}: ckey {k} not a field")
        if spec.pk:
            check(spec.pk in names, f"{name}: pk {spec.pk} not a field")
        if spec.key:
            check(spec.key in names, f"{name}: key {spec.key} not a field")


def test_id_and_epoch_widths():
    """House invariant: ID/AT/VER fields are N(20) (matches test_tracking_schema)."""
    for name, spec in reg.TABLES.items():
        for (fn, typ, ln) in spec.fields:
            if fn == "ID" or fn.endswith("AT") or fn.endswith("VER"):
                check(typ == "N" and ln == 20,
                      f"{name}.{fn} should be N(20), got {typ}({ln})")


def main():
    for nm, fn in sorted(globals().items()):
        if nm.startswith("test_") and callable(fn):
            fn()
    print(f"\ntest_schema_registry: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
