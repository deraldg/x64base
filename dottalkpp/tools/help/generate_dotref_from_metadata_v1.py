#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: help
# layer: tool
# owns:
# project: project.x64base.runtime
# lane: help/reference authority (Phase 3B dotref generator)
# owner: member.derald
# status: candidate
"""
generate_dotref_from_metadata_v1.py -- Phase 3B reference-header generator.

Turns the canonical command-metadata lanes (SYSCMD + SYSARGS) back into
include/dotref.hpp, per the authority model:

  dottalkpp/docs/authority/help_message_reference_authority_model_v1.md
  dottalkpp/docs/authority/help_message_reference_implementation_backlog_v1.md  (Phase 3B)

Doctrine this obeys:
  - metadata (SYSCMD/SYSARGS) is the canonical authoring lane
  - dotref.hpp is a GENERATED artifact, kept compiled as a bootstrap/search surface
  - source stays implementation truth; this tool never touches source

The honest gaps (surfaced, not hidden):
  - SYSCMD/SYSARGS as seeded today do NOT carry a one-line summary. dotref's
    curated summaries are therefore carried forward from the existing header
    (curated prose is a legitimate HELP input; a summary lane can replace this
    later). Emitted rows record which fields came from metadata vs were carried.
  - SYSCMD covers only the seeded command subset. In the default `merge` mode,
    commands present in dotref.hpp but not yet in SYSCMD are carried forward
    unchanged so nothing regresses. `--pure` mode emits ONLY metadata-backed
    rows, which QUANTIFIES exactly how much of dotref the tables reproduce today.

Field mapping:
  name      <- SYSCMD.CAN_NAME
  supported <- SYSCMD.ACTIVE == 'T'
  syntax    <- SYSARGS: the distinct `usage=` clauses in NOTES, joined with ' | '
               (fallback: the existing header syntax when no args rows exist)
  summary   <- carried forward from the existing dotref.hpp by name
               (no summary lane seeded yet)

Default behavior is DRY-RUN: it writes a candidate file and prints a unified
diff + a coverage report. It only overwrites include/dotref.hpp with --write.

Usage:
  python dottalkpp/tools/help/generate_dotref_from_metadata_v1.py            # dry-run merge
  python dottalkpp/tools/help/generate_dotref_from_metadata_v1.py --pure     # coverage probe
  python dottalkpp/tools/help/generate_dotref_from_metadata_v1.py --report   # counts only
  python dottalkpp/tools/help/generate_dotref_from_metadata_v1.py --write    # regenerate header

No third-party deps. Owner: member.derald  authored_by: member.ai.claude.cowork  lane: AIF (help/reference).
"""
from __future__ import annotations

import argparse
import csv
import difflib
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEF_HEADER = "include/dotref.hpp"
DEF_SYSCMD = "dottalkpp/data/scripts/metadata/SYSCMD_IMPORT_v1.csv"
DEF_SYSARGS = "dottalkpp/data/scripts/metadata/SYSARGS_IMPORT_v1.csv"

ANCHOR = "std::vector<Item> k = {"   # start of the generated row region
RETURN = "return k;"                 # marks the end of catalog()


# --------------------------------------------------------------------------- #
# C++ string-literal + entry parsing (brace/quote aware, no regex fragility)
# --------------------------------------------------------------------------- #
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "'": "'", "0": "\0"}


def _read_cstr(s: str, i: int) -> tuple[str, int]:
    """Read one C string literal starting at s[i]=='"'; return (value, next_index)."""
    assert s[i] == '"', "expected opening quote"
    i += 1
    buf: list[str] = []
    while i < len(s):
        c = s[i]
        if c == "\\":
            nxt = s[i + 1] if i + 1 < len(s) else ""
            buf.append(_ESCAPES.get(nxt, nxt))
            i += 2
        elif c == '"':
            return "".join(buf), i + 1
        else:
            buf.append(c)
            i += 1
    raise ValueError("unterminated string literal")


def _read_cstr_concat(s: str, i: int) -> tuple[str, int]:
    """Read one or more adjacent C string literals (C concatenation) from s[i]."""
    val, i = _read_cstr(s, i)
    while True:
        j = i
        while j < len(s) and s[j] in " \t\r\n":
            j += 1
        if j < len(s) and s[j] == '"':
            more, i = _read_cstr(s, j)
            val += more
        else:
            return val, i


def _iter_entries(blob: str):
    """Yield the text inside each top-level {...} group, skipping string bodies."""
    i, n, depth, start, in_str = 0, len(blob), 0, None, False
    while i < n:
        c = blob[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == "{":
            if depth == 0:
                start = i + 1
            depth += 1
            i += 1
            continue
        if c == "}":
            depth -= 1
            if depth == 0 and start is not None:
                yield blob[start:i]
                start = None
            i += 1
            continue
        i += 1


@dataclass
class Item:
    name: str
    syntax: str
    summary: str
    supported: bool
    source: str = ""   # provenance label, generator-internal


def _parse_entry(entry: str) -> Item:
    """Parse `"NAME", "SYNTAX", "SUMMARY", true` (3 strings + bool)."""
    i = 0
    fields: list[str] = []
    for _ in range(3):
        q = entry.index('"', i)
        val, i = _read_cstr_concat(entry, q)
        fields.append(val)
    rest_code = entry[i:].split("//")[0]
    supported = "true" in rest_code
    return Item(fields[0], fields[1], fields[2], supported)


def parse_header(text: str):
    """Split dotref.hpp into (prefix, existing_items, suffix) around the row region."""
    a = text.index(ANCHOR) + len(ANCHOR)          # just after the opening '{'
    r = text.index(RETURN, a)                       # 'return k;'
    end = text.rindex("};", a, r)                   # the '};' closing the initializer
    rows_blob = text[a:end]
    prefix = text[:a]
    suffix = text[end:]
    items = [_parse_entry(e) for e in _iter_entries(rows_blob)]
    return prefix, items, suffix


# --------------------------------------------------------------------------- #
# Metadata readers
# --------------------------------------------------------------------------- #
def read_syscmd(path: Path) -> dict[str, bool]:
    """CAN_NAME (upper) -> supported (ACTIVE=='T')."""
    out: dict[str, bool] = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = (row.get("CAN_NAME") or "").strip()
            if not name:
                continue
            out[name.upper()] = (row.get("ACTIVE") or "").strip().upper() == "T"
    return out


def read_sysargs(path: Path) -> dict[str, str]:
    """OWNER_NAM (upper) -> syntax string built from distinct `usage=` clauses."""
    usages: dict[str, list[str]] = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            owner = (row.get("OWNER_NAM") or "").strip()
            notes = row.get("NOTES") or ""
            if not owner:
                continue
            key = owner.upper()
            bucket = usages.setdefault(key, [])
            for part in notes.split(";"):
                part = part.strip()
                if part.startswith("usage=") and not part.startswith("usage_access="):
                    u = part[len("usage="):].strip()
                    if u and u not in bucket:
                        bucket.append(u)
    return {k: " | ".join(v) for k, v in usages.items() if v}


# --------------------------------------------------------------------------- #
# Row assembly
# --------------------------------------------------------------------------- #
def build_items(existing, syscmd, syntax_by_cmd, mode: str):
    """Return (ordered items, stats). merge = safe/no-loss; pure = metadata-only."""
    by_name = {it.name.upper(): it for it in existing}
    stats = {"total": 0, "metadata": 0, "carried": 0, "new": 0, "args_syntax": 0}
    out: list[Item] = []

    if mode == "pure":
        for nm in sorted(syscmd):
            syn = syntax_by_cmd.get(nm)
            if syn:
                stats["args_syntax"] += 1
            else:
                syn = by_name[nm].syntax if nm in by_name else ""
            summary = by_name[nm].summary if nm in by_name else ""
            src = "metadata" if nm in by_name else "new from metadata"
            if nm not in by_name:
                stats["new"] += 1
            else:
                stats["metadata"] += 1
            out.append(Item(nm, syn, summary, syscmd[nm], src))
        stats["total"] = len(out)
        return out, stats

    # merge (default): preserve existing order, carry unseeded rows, append new metadata rows
    seen: set[str] = set()
    for it in existing:
        key = it.name.upper()
        seen.add(key)
        if key in syscmd:
            syn = syntax_by_cmd.get(key)
            if syn:
                stats["args_syntax"] += 1
            else:
                syn = it.syntax
            out.append(Item(it.name, syn, it.summary, syscmd[key],
                            "metadata" if syntax_by_cmd.get(key) else "metadata(name/active); syntax carried"))
            stats["metadata"] += 1
        else:
            out.append(Item(it.name, it.syntax, it.summary, it.supported, "carried (no SYSCMD row)"))
            stats["carried"] += 1
    for nm in sorted(k for k in syscmd if k not in seen):
        syn = syntax_by_cmd.get(nm, "")
        if syn:
            stats["args_syntax"] += 1
        out.append(Item(nm, syn, "", syscmd[nm], "new from metadata"))
        stats["new"] += 1
    stats["total"] = len(out)
    return out, stats


def _cstr(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def render(prefix: str, items, suffix: str, mode: str, stats, sources) -> str:
    prov = [
        "",
        "        // ===== GENERATED ROWS -- do not hand-edit below =====",
        "        // generator: dottalkpp/tools/help/generate_dotref_from_metadata_v1.py",
        f"        // mode: {mode}  sources: {', '.join(sources)}",
        f"        // {stats['total']} rows: {stats['metadata']} metadata-backed, "
        f"{stats['carried']} carried-forward, {stats['new']} new-from-metadata "
        f"({stats['args_syntax']} with SYSARGS-derived syntax)",
        "        // summary text is curated prose carried forward (no summary lane seeded yet)",
        "",
    ]
    rows = [
        f"        {{{_cstr(it.name)}, {_cstr(it.syntax)}, {_cstr(it.summary)}, "
        f"{'true' if it.supported else 'false'}}},"
        for it in items
    ]
    return prefix + "\n".join(prov) + "\n" + "\n".join(rows) + "\n" + suffix


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate include/dotref.hpp from SYSCMD + SYSARGS.")
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("--header", default=DEF_HEADER)
    ap.add_argument("--syscmd", default=DEF_SYSCMD)
    ap.add_argument("--sysargs", default=DEF_SYSARGS)
    ap.add_argument("--mode", choices=("merge", "pure"), default="merge")
    ap.add_argument("--out", default=None, help="candidate output path (default: <header>.generated)")
    ap.add_argument("--write", action="store_true", help="overwrite the header in place")
    ap.add_argument("--report", action="store_true", help="print coverage report only (no diff)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    header_path = root / args.header
    syscmd_path = root / args.syscmd
    sysargs_path = root / args.sysargs

    for p in (header_path, syscmd_path, sysargs_path):
        if not p.is_file():
            print(f"generate-dotref: missing input: {p}", file=sys.stderr)
            return 4

    original = header_path.read_text(encoding="utf-8")
    prefix, existing, suffix = parse_header(original)
    syscmd = read_syscmd(syscmd_path)
    syntax_by_cmd = read_sysargs(sysargs_path)

    items, stats = build_items(existing, syscmd, syntax_by_cmd, args.mode)
    sources = [Path(args.syscmd).name, Path(args.sysargs).name]
    generated = render(prefix, items, suffix, args.mode, stats, sources)

    print("=== generate-dotref coverage ===")
    print(f"  mode              : {args.mode}")
    print(f"  existing header   : {len(existing)} entries")
    print(f"  SYSCMD seeded     : {len(syscmd)} commands ({sum(1 for v in syscmd.values() if v)} active)")
    print(f"  SYSARGS w/ usage  : {len(syntax_by_cmd)} commands")
    print(f"  emitted           : {stats['total']} "
          f"({stats['metadata']} metadata-backed, {stats['carried']} carried, {stats['new']} new)")
    if existing:
        covered = sum(1 for it in existing if it.name.upper() in syscmd)
        pct = 100.0 * covered / len(existing)
        print(f"  metadata coverage : {covered}/{len(existing)} of current entries ({pct:.1f}%)")

    if args.report:
        return 0

    if args.write:
        header_path.write_text(generated, encoding="utf-8")
        print(f"\ngenerate-dotref: WROTE {header_path}")
        return 0

    # Default candidate goes to a temp dir, never into the repo working tree.
    out_path = Path(args.out) if args.out else Path(tempfile.gettempdir()) / "dotref.hpp.generated"
    out_path.write_text(generated, encoding="utf-8")
    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        generated.splitlines(keepends=True),
        fromfile=str(args.header),
        tofile=str(args.header) + " (generated)",
        n=2,
    ))
    print(f"\ngenerate-dotref: candidate written to {out_path}")
    print(f"generate-dotref: {len(diff)} diff lines vs current header "
          "(dry-run; re-run with --write to apply)\n")
    sys.stdout.writelines(diff[:400])
    if len(diff) > 400:
        print(f"\n... ({len(diff) - 400} more diff lines truncated)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
