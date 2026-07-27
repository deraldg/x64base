#!/usr/bin/env python3
"""
Per-entity lifecycle stage report (AIF-067).

WHY THIS EXISTS
    Every fact needed to say how far an entity has progressed already exists --
    the file contract, the usage contract, the catalog row, the HELP topic, the
    proof registry -- and until now none of it was ever ASSEMBLED PER ENTITY.
    The information was present and unreadable, which is this project's
    signature failure in a different coat.

    docs/ai-friendly/ENTITY_LIFECYCLE_AND_THE_BRIDGE_V1.md is the doctrine this
    implements. Short version: an entity is real from the moment it is declared,
    documentation is the tracker, and an entity may never CLAIM a stage later
    than the one it occupies.

THE VOCABULARY IS NOT INVENTED HERE
    States come from labtalk/registries/proofs.yaml, which declares ten of them.
    An earlier draft of the doctrine document invented a parallel chain before
    checking; that was the exact defect the doctrine warns about. This tool
    reads the registry so the vocabulary has ONE home.

    States are a SET, not a ladder. An entity can be source_defined and
    help_documented without being runtime_observed. The report shows what is
    held and what is missing, never a single collapsed label.

WHAT IS OBSERVABLE HERE, AND WHAT IS NOT
    Observable from the tree and the tables:
        idea             a tracked file exists and declares no command
        source_defined   carries a usage or subusage contract
        help_documented  its command has a live HELP_TOPIC row
        (catalogued)     its command has a SYSCMD / SYSSUBCMD row
    NOT observable here, and deliberately not guessed:
        runtime_observed / validated / case_registered /
        runtime_lab_candidate / student_ready / simulated
    Those are claims about events, and events are recorded in proofs.yaml or in
    lane documents. This tool reports them ONLY where the registry cites the
    entity. A file is never promoted because it looks finished.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dbfread  # noqa: E402

SRC_DIRS = ("src", "include", "bindings")
EXTS = {".cpp", ".hpp", ".h", ".c", ".inl", ".ipp"}

FILE_RE = re.compile(r"@dottalk\.file\b")
USAGE_RE = re.compile(r"//\s*@dottalk\.usage v1\n(?://[^\n]*\n)+")
SUBUSAGE_RE = re.compile(r"//\s*@dottalk\.subusage v1\n(?:\s*//[^\n]*\n)+")
CMD_RE = re.compile(r"(?m)^\s*(?://)?\s*command:\s*(.+?)\s*$")


def tracked(root: Path) -> list[str]:
    out = subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(root), "ls-files", *SRC_DIRS],
        text=True)
    return [p for p in out.split("\n") if p and Path(p).suffix.lower() in EXTS]


def load_states(root: Path) -> dict[str, str]:
    try:
        import yaml
        d = yaml.safe_load((root / "labtalk/registries/proofs.yaml").read_text(
            encoding="utf-8"))
        return {s["id"]: s.get("meaning", "") for s in d.get("proof_states", [])}
    except Exception:                                        # noqa: BLE001
        return {}


def table_names(path: Path, col: str) -> set[str]:
    try:
        return {r[col].upper() for r in dbfread.read(path).rows if r.get(col)}
    except Exception:                                        # noqa: BLE001
        return set()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--stage", help="list entities holding this state")
    ap.add_argument("--gaps", action="store_true",
                    help="only entities that declare a command but are not catalogued")
    ap.add_argument("--limit", type=int, default=25)
    a = ap.parse_args()
    root = Path(a.root).resolve()

    states = load_states(root)
    data = root / "dottalkpp" / "data"
    syscmd = table_names(data / "metadata" / "SYSCMD.dbf", "CAN_NAME")
    syssub = table_names(data / "metadata" / "SYSSUBCMD.dbf", "QUAL_NAME")
    # JOIN ON `TOPIC`, NOT `TOPICKEY`.
    #
    # TOPICKEY is the QUALIFIED form `CATALOG|TOPIC` -- 'DOT|ABOUT'. Joining
    # command names against it matched nothing and reported help_documented = 0
    # for all 223 contracted entities, against 714 live HELP_TOPIC rows. That is
    # not a finding, it is a join key error, and it would have been a confident
    # false claim that the entire command surface is undocumented.
    #
    # Worth noting the qualified form is the SAME shape as the `owner:` field in
    # a usage contract (`owner: DOT|SET CASE`), so the contracts already speak
    # this vocabulary. Matching owner -> TOPICKEY directly is the more precise
    # join and is the natural next refinement.
    helptopics = table_names(data / "help" / "HELP_TOPIC.dbf", "TOPIC")
    catalog = syscmd | syssub

    entities = []
    for rel in tracked(root):
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        cmds: set[str] = set()
        for blk in USAGE_RE.findall(text):
            m = CMD_RE.search(blk)
            if m:
                cmds.add(re.sub(r"\s+", " ", m.group(1)).strip().upper())
        for blk in SUBUSAGE_RE.findall(text):
            p = re.search(r"//\s*parent:\s*(\S+)", blk)
            s = re.search(r"//\s*sub:\s*(\S+)", blk)
            if p and s:
                cmds.add(f"{p.group(1)} {s.group(1)}".upper())
        cmds.discard("NONE")

        held = set()
        if FILE_RE.search(text):
            held.add("described")
        if cmds:
            held.add("source_defined")
        else:
            held.add("idea")
        if cmds and cmds & catalog:
            held.add("catalogued")
        if cmds and cmds & helptopics:
            held.add("help_documented")
        entities.append({"file": rel, "commands": sorted(cmds), "held": held})

    total = len(entities)
    def count(s): return sum(1 for e in entities if s in e["held"])

    print(f"entities (tracked source files): {total}")
    print(f"  idea            {count('idea'):5}   declares no command -- a reserved slot")
    print(f"  described       {count('described'):5}   carries @dottalk.file")
    print(f"  source_defined  {count('source_defined'):5}   carries a usage/subusage contract")
    print(f"  catalogued      {count('catalogued'):5}   command has a SYSCMD/SYSSUBCMD row")
    print(f"  help_documented {count('help_documented'):5}   command has a HELP_TOPIC row")
    print()
    print("NOT DERIVABLE FROM THE TREE -- reported only where proofs.yaml cites the")
    print("entity, never inferred from a file looking finished:")
    for s in ("runtime_observed", "validated", "case_registered",
              "runtime_lab_candidate", "student_ready", "simulated"):
        if s in states:
            print(f"  {s:22} {states[s]}")

    if a.gaps:
        gap = [e for e in entities
               if "source_defined" in e["held"] and "catalogued" not in e["held"]]
        print(f"\nCONTRACTED BUT NOT CATALOGUED: {len(gap)}")
        print("(an entity claiming a stage its catalog does not confirm)")
        for e in gap[: a.limit]:
            print(f"  {e['file']:52} {', '.join(e['commands'])}")
    elif a.stage:
        sel = [e for e in entities if a.stage in e["held"]]
        print(f"\n{a.stage}: {len(sel)}")
        for e in sel[: a.limit]:
            print(f"  {e['file']:52} {', '.join(e['commands']) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
