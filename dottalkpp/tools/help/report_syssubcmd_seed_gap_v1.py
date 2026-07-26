#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: help
# layer: tool
# owns:
# project: project.x64base.runtime
# lane: help/reference authority (SYSSUBCMD harvest; sibling of the SYSCMD seed-gap)
# owner: member.derald
# status: candidate
"""
report_syssubcmd_seed_gap_v1.py -- harvest the subcommand surface into SYSSUBCMD candidates.

The SYSCMD seed-gap pass showed several dotref entries are `SET <option>` forms, not
top-level commands. This tool models the real subcommand surface for the parents that
have one, so those land in SYSSUBCMD instead of being mis-filed as commands.

Authoritative sources (source is implementation truth):
  1. cmd_SET option ladder  -- src/cli/cmd_set.cpp  `opt == "X"` (and nested `sub == "Y"`)
                               = the SET subcommands dispatched internally by cmd_SET
  2. registry compounds     -- src/cli/shell_commands.cpp space-separated tokens
                               ("SET RELATION", "BUILD VECTORS", "ERROR CLEAR", ...)
Crosswalk (documentation / alt-spelling evidence, not authority):
  3. dotref.hpp             -- first collection point; documents some as "SET X"
  4. registry concat tokens -- SETCASE / SETFILTER / SETORDER ... (same feature, one word)

The spelling fork this surfaces: e.g. FILTER is reachable as `SET FILTER` (cmd_SET ladder),
`SETFILTER` (registry token), and documented `SET FILTER` in dotref -- one feature, three
spellings. The report lists every such fork for the fullstack push to reconcile.

Output:
  - markdown report (stdout or --report-out): per-parent subcommand inventory + spelling forks
  - candidate SYSSUBCMD import CSV (--csv-out) in the backlog's canonical column order:
      SUBCMD_ID,PARENT_CMD,CAN_NAME,TOKEN,HANDLER,OWNER,ACTIVE,SRC_FILE,HELP_TOPIC,NOTES
    NOTE: SYSSUBCMD.dbf is x64-format and has no import CSV yet; confirm these field names
    against the table via a DDICT readback before importing.

Never touches source / SYSCMD / SYSSUBCMD / dotref. Owner: member.derald  authored_by: member.ai.claude.cowork.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

DEF_REGISTRY = "src/cli/shell_commands.cpp"
DEF_SETSRC = "src/cli/cmd_set.cpp"
DEF_HEADER = "include/dotref.hpp"

# SET options that are meta / not real subcommands.
SET_META = {"?", "HELP", "USAGE"}
# Ladder tokens that are alt-spellings of another sub -> fold to the canonical sub.
SET_FOLD = {"SETCASE": "CASE", "SETNEAR": "NEAR", "RELATIONS": "RELATION"}
OWNER = "member.derald"

_SET_OPT = re.compile(r'opt == "([A-Z_?]+)"')
_SET_SUB = re.compile(r'sub == "([A-Z_]+)"')


def load_registry(path: Path):
    """Reuse the seed-gap registry parser (token -> handler)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import report_syscmd_seed_gap_v1 as r  # noqa: E402
    return r.parse_registry(path), r


def set_ladder(path: Path) -> set[str]:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    opts = set(_SET_OPT.findall(txt)) | set(_SET_SUB.findall(txt))
    out = set()
    for o in opts:
        if o in SET_META:
            continue
        out.add(SET_FOLD.get(o, o))
    return out


def subcmd_id(parent: str, sub: str) -> str:
    return "SUB_" + re.sub(r"[^A-Za-z0-9]+", "_", f"{parent}_{sub}".upper()).strip("_")


def main() -> int:
    ap = argparse.ArgumentParser(description="SYSSUBCMD subcommand harvest.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--registry", default=DEF_REGISTRY)
    ap.add_argument("--setsrc", default=DEF_SETSRC)
    ap.add_argument("--header", default=DEF_HEADER)
    ap.add_argument("--csv-out", default=None)
    ap.add_argument("--report-out", default=None)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    reg, rmod = load_registry(root / args.registry)
    ladder = set_ladder(root / args.setsrc)
    dotref = rmod.load_dotref(root / args.header)  # {name_upper: supported}
    doc_names = set(dotref)

    # registry space-compounds grouped by parent
    compounds: dict[str, dict[str, str]] = {}
    for token, handler in reg.items():
        if " " in token:
            parent, sub = token.split(" ", 1)
            compounds.setdefault(parent, {})[sub.strip()] = handler

    # concat SETX tokens (single-word registry tokens that start with a parent name)
    def concat_subs(parent: str) -> dict[str, str]:
        out = {}
        for token, handler in reg.items():
            if " " in token or token == parent:
                continue
            if token.startswith(parent) and len(token) > len(parent):
                sub = token[len(parent):].lstrip("_ -")   # SETFILTER->FILTER, ERROR_CLEAR->CLEAR
                if sub:
                    out[sub] = handler
        return out

    parents = sorted(set(compounds) | ({"SET"} if ladder else set()))
    rows = []
    forks = []
    for parent in parents:
        subs: dict[str, dict] = {}
        # ladder (SET only)
        if parent == "SET":
            for s in ladder:
                subs.setdefault(s, {})["ladder"] = True
        # registry compounds
        for s, h in compounds.get(parent, {}).items():
            subs.setdefault(s, {})["compound"] = h
        # concat tokens
        for s, h in concat_subs(parent).items():
            subs.setdefault(s, {})["concat"] = h
        # dotref documentation crosswalk
        for s in list(subs):
            if f"{parent} {s}" in doc_names or f"{parent}{s}" in doc_names:
                subs[s]["doc"] = True

        for sub in sorted(subs):
            ev = subs[sub]
            # handler precedence: explicit compound > concat token > internal dispatch
            if "compound" in ev and ev["compound"]:
                handler, src = ev["compound"], args.registry
            elif "concat" in ev and ev["concat"]:
                handler, src = ev["concat"], args.registry
            else:
                handler = f"cmd_{parent}" if parent != "SET" else "cmd_SET"
                src = args.setsrc if parent == "SET" else args.registry
            spellings = [k for k in ("ladder", "compound", "concat", "doc") if ev.get(k)]
            note = "evidence: " + ",".join(spellings)
            rows.append({
                "SUBCMD_ID": subcmd_id(parent, sub), "PARENT_CMD": parent,
                "CAN_NAME": sub, "TOKEN": f"{parent} {sub}", "HANDLER": handler,
                "OWNER": OWNER, "ACTIVE": "T", "SRC_FILE": src,
                "HELP_TOPIC": "", "NOTES": note,
                "_ev": spellings,
            })
            if len(spellings) >= 2 and ("concat" in spellings or ("compound" in spellings and "ladder" in spellings)):
                variants = [f"{parent} {sub}"]
                if ev.get("concat"):
                    variants.append(f"{parent}{sub}")
                forks.append((parent, sub, variants, spellings))

    # ---- report ----
    L = []
    L.append("# SYSSUBCMD seed harvest v1\n")
    L.append("Sibling of the SYSCMD seed-gap. Models the subcommand surface (SET/BUILD/ERROR) so\n"
             "`SET <option>` forms seed into SYSSUBCMD, not SYSCMD. dotref.hpp is the first\n"
             "collection point; source (cmd_set.cpp ladder + registry) is the authority.\n")
    L.append("## Sizes\n")
    L.append(f"- SET ladder options (cmd_set.cpp): {len(ladder)}")
    L.append(f"- registry compound parents: {sorted(compounds)}")
    L.append(f"- **subcommand candidates emitted: {len(rows)}** across parents {parents}")
    L.append(f"- spelling forks (same feature, multiple spellings): {len(forks)}\n")
    L.append("## Candidate subcommands\n")
    L.append("| PARENT | CAN_NAME | HANDLER | evidence |")
    L.append("|---|---|---|---|")
    for r in rows:
        L.append(f"| {r['PARENT_CMD']} | {r['CAN_NAME']} | {r['HANDLER']} | {','.join(r['_ev'])} |")
    L.append("\n## Spelling forks to reconcile (fullstack push)\n")
    if forks:
        L.append("| feature | spellings | evidence |")
        L.append("|---|---|---|")
        for parent, sub, variants, ev in forks:
            L.append(f"| {parent} {sub} | {' / '.join(variants)} | {','.join(ev)} |")
    else:
        L.append("(none)")
    L.append("")
    report = "\n".join(L) + "\n"

    if args.report_out:
        Path(args.report_out).write_text(report, encoding="utf-8")
        print(f"syssubcmd: report -> {args.report_out}")
    else:
        sys.stdout.write(report)

    if args.csv_out:
        cols = ["SUBCMD_ID", "PARENT_CMD", "CAN_NAME", "TOKEN", "HANDLER",
                "OWNER", "ACTIVE", "SRC_FILE", "HELP_TOPIC", "NOTES"]
        with open(args.csv_out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"syssubcmd: candidate CSV ({len(rows)} rows) -> {args.csv_out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
