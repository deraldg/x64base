#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: help
# layer: tool
# owns:
# project: project.x64base.runtime
# lane: help/reference authority (SYSCMD seed-gap; feeds Phase 3B dotref generator)
# owner: member.derald
# status: candidate
"""
report_syscmd_seed_gap_v1.py -- turn the SYSCMD seed gap into a checklist.

dotref.hpp is the first collection point of the fullstack document harvest, and
the Phase 3B generator proved SYSCMD only reproduces ~15% of it today. This tool
reconciles three surfaces to say exactly what still needs a SYSCMD row:

  1. command registry   -- src/cli/shell_commands.cpp  registry().add("TOKEN", []{ handler(A,S); })
                           (authoritative implemented-command set + handler names)
  2. dotref.hpp         -- the documented command surface (first collection point)
  3. SYSCMD seed        -- dottalkpp/data/scripts/metadata/SYSCMD_IMPORT_v1.csv (already seeded)
  plus SYSARGS          -- which commands already have usage/syntax rows

Output:
  - a markdown checklist report (stdout, or --report-out PATH)
  - a review-ready candidate SYSCMD import CSV for the gap (--csv-out PATH),
    columns matching SYSCMD_IMPORT_v1.csv exactly: CMD_ID,CAN_NAME,TYPE,VIS,HANDLER,ACTIVE

Each gap row is classified:
  - registry-backed : handler resolved from the registry -> safe to seed
  - documented-only : in dotref but not in the registry -> review (alias? retired? subcommand?)
  - syntax-ready    : SYSARGS already has usage rows -> dotref syntax can be generated too

Nothing is written into the repo unless you pass --csv-out / --report-out. It never
touches source, SYSCMD, or dotref. Owner: member.derald  authored_by: member.ai.claude.cowork.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

DEF_REGISTRY = "src/cli/shell_commands.cpp"
DEF_HEADER = "include/dotref.hpp"
DEF_SYSCMD = "dottalkpp/data/scripts/metadata/SYSCMD_IMPORT_v1.csv"
DEF_SYSARGS = "dottalkpp/data/scripts/metadata/SYSARGS_IMPORT_v1.csv"

_ADD = re.compile(r'registry\(\)\.add\(\s*"([^"]+)"\s*,')
_HANDLER_CALL = re.compile(r'\b([A-Za-z_]\w*)\s*\(\s*A\s*,\s*S\s*\)')
_CONTROL = {"if", "for", "while", "switch", "return", "else", "do"}


def _match_brace(s: str, open_idx: int) -> int:
    """Given s[open_idx]=='{', return index of the matching '}' (string-aware)."""
    depth, i, in_str, in_chr = 0, open_idx, False, False
    while i < len(s):
        c = s[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif in_chr:
            if c == "\\":
                i += 2
                continue
            if c == "'":
                in_chr = False
        else:
            if c == '"':
                in_str = True
            elif c == "'":
                in_chr = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1


def parse_registry(path: Path) -> dict[str, str]:
    """TOKEN (upper) -> primary handler name. Brace-matches each add() lambda body."""
    txt = path.read_text(encoding="utf-8", errors="ignore")
    out: dict[str, str] = {}
    for m in _ADD.finditer(txt):
        token = m.group(1).strip().upper()
        brace = txt.find("{", m.end())
        if brace < 0:
            continue
        close = _match_brace(txt, brace)
        if close < 0:
            continue
        body = txt[brace + 1:close]
        handler = ""
        for hm in _HANDLER_CALL.finditer(body):
            name = hm.group(1)
            if name not in _CONTROL:
                handler = name
                break
        out.setdefault(token, handler)
    return out


def read_syscmd(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return {(r.get("CAN_NAME") or "").strip().upper()
                for r in csv.DictReader(f) if (r.get("CAN_NAME") or "").strip()}


def read_sysargs_owners(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return {(r.get("OWNER_NAM") or "").strip().upper()
                for r in csv.DictReader(f) if (r.get("OWNER_NAM") or "").strip()}


def load_dotref(header: Path):
    """Reuse the generator's C++ parser. Returns {name_upper: supported_bool}."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import generate_dotref_from_metadata_v1 as g  # noqa: E402
    _, items, _ = g.parse_header(header.read_text(encoding="utf-8"))
    return {it.name.upper(): it.supported for it in items}


def cmd_id(name: str) -> str:
    return "CMD_" + re.sub(r"[^A-Za-z0-9]+", "_", name.strip().upper()).strip("_")


def main() -> int:
    ap = argparse.ArgumentParser(description="SYSCMD seed-gap report + candidate CSV.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--registry", default=DEF_REGISTRY)
    ap.add_argument("--header", default=DEF_HEADER)
    ap.add_argument("--syscmd", default=DEF_SYSCMD)
    ap.add_argument("--sysargs", default=DEF_SYSARGS)
    ap.add_argument("--csv-out", default=None, help="write candidate SYSCMD import CSV here")
    ap.add_argument("--report-out", default=None, help="write markdown report here (else stdout)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    registry = parse_registry(root / args.registry)
    dotref = load_dotref(root / args.header)
    seeded = read_syscmd(root / args.syscmd)
    sysargs = read_sysargs_owners(root / args.sysargs)

    universe = (set(registry) | set(dotref)) - seeded
    # Symbol-only aliases (e.g. "!") are not command identities -- skip, report separately.
    symbol_aliases = sorted(nm for nm in universe if not re.sub(r"[^A-Za-z0-9]", "", nm))
    universe -= set(symbol_aliases)
    rows = []
    for nm in sorted(universe):
        in_reg = nm in registry
        in_doc = nm in dotref
        handler = registry.get(nm, "")
        if in_reg and not handler:
            klass = "registry-backed (handler needs review)"
        elif in_reg:
            klass = "registry-backed"
        else:
            klass = "documented-only"
        active = "T" if (in_reg or dotref.get(nm, False)) else "F"
        rows.append({
            "CMD_ID": cmd_id(nm), "CAN_NAME": nm, "TYPE": "command", "VIS": "public",
            "HANDLER": handler or "TODO", "ACTIVE": active,
            "_class": klass, "_reg": in_reg, "_doc": in_doc, "_args": nm in sysargs,
        })

    reg_backed = [r for r in rows if r["_reg"]]
    doc_only = [r for r in rows if not r["_reg"]]
    syntax_ready = [r for r in rows if r["_args"]]
    handler_todo = [r for r in rows if r["_reg"] and r["HANDLER"] == "TODO"]

    lines = []
    lines.append("# SYSCMD seed-gap report v1\n")
    lines.append("Feeds the Phase 3B dotref generator. dotref.hpp is the first collection point of\n"
                 "the fullstack document harvest; this lists commands still missing a SYSCMD row.\n")
    lines.append("## Surface sizes\n")
    lines.append(f"- registry (implemented commands): {len(registry)}")
    lines.append(f"- dotref.hpp (documented surface): {len(dotref)}")
    lines.append(f"- SYSCMD (already seeded): {len(seeded)}")
    lines.append(f"- SYSARGS (commands with usage rows): {len(sysargs)}")
    lines.append(f"- **gap to seed (registry union dotref, minus seeded): {len(rows)}**\n")
    lines.append("## Gap breakdown\n")
    lines.append(f"- registry-backed (handler resolved, safe to seed): {len(reg_backed) - len(handler_todo)}")
    lines.append(f"- registry-backed but handler needs review: {len(handler_todo)}")
    lines.append(f"- documented-only (in dotref, not in registry -- review): {len(doc_only)}")
    lines.append(f"- syntax-ready (SYSARGS usage already present): {len(syntax_ready)}")
    if symbol_aliases:
        lines.append(f"- symbol-only aliases skipped (not command identities): "
                     f"{len(symbol_aliases)} ({', '.join(symbol_aliases)})")
    lines.append("")
    lines.append("## Checklist (candidate rows)\n")
    lines.append("| CAN_NAME | HANDLER | ACTIVE | reg | doc | args | class |")
    lines.append("|---|---|:--:|:--:|:--:|:--:|---|")
    for r in rows:
        lines.append(f"| {r['CAN_NAME']} | {r['HANDLER']} | {r['ACTIVE']} | "
                     f"{'Y' if r['_reg'] else '-'} | {'Y' if r['_doc'] else '-'} | "
                     f"{'Y' if r['_args'] else '-'} | {r['_class']} |")
    report = "\n".join(lines) + "\n"

    if args.report_out:
        Path(args.report_out).write_text(report, encoding="utf-8")
        print(f"seed-gap: report -> {args.report_out}")
    else:
        sys.stdout.write(report)

    if args.csv_out:
        with open(args.csv_out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["CMD_ID", "CAN_NAME", "TYPE", "VIS", "HANDLER", "ACTIVE"])
            for r in rows:
                w.writerow([r["CMD_ID"], r["CAN_NAME"], r["TYPE"], r["VIS"], r["HANDLER"], r["ACTIVE"]])
        print(f"seed-gap: candidate CSV ({len(rows)} rows) -> {args.csv_out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
