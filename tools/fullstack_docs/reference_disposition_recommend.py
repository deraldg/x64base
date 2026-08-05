#!/usr/bin/env python3
"""reference_disposition_recommend.py -- Phase 1 Gate-1 disposition recommender.

The reference pipeline (build_reference_identity_inventory -> build_reference_
authority_crosswalk -> validate_reference_identity_authority) deliberately STOPS
at review rows: per REFERENCE_IDENTITY_AUTHORITY_CONTRACT_V1, "disagreement
produces a review row carrying both values and their evidence; no downstream layer
may silently replace a stronger authority." So a human dispositions every review
row by hand, each run.

This step does NOT resolve or apply anything. It reads the crosswalk + duplicate
inventory the tools already produced and attaches a RECOMMENDED disposition +
evidence to each review row -- a candidate the reviewer accepts or overrides --
shrinking the manual review to rows that are genuinely undecided.

It DEFERS to the crosswalk's own entity typing (a COMMAND-shaped review row whose
name is also a FUNCTION identity is function-owned, not a command decision) and
honours the contract's compact-form rule (SETNEAR is an entry variant of SET NEAR).

Recommended dispositions (Gate-1 vocabulary):
  FUNCTION_AUTHORITY        crosswalk emits a FN: identity for this name (SYSFUNC owns it)
  EDUCATION_TOPIC           edref topic
  EDUCATION_SURFACE         edu_ handler, or a reference summary marking demo/student/teaching
  DELIBERATE_SUBFORM        @dottalk.subusage ladder arm (incl. compact form, e.g. SETNEAR = SET NEAR)
  DELIBERATE_ALIAS          reference summary declares "alias of X", or shares a handler with an owner
  DELIBERATE_DUAL_HOME      present in dotref AND foxref (native + FoxPro wording overlay)
  FOXPRO_COMPAT_REFERENCE   foxref-only compatibility entry (not registered, not a function)
  CONTRACT_FORMAT_NORMALIZE has a /* @dottalk.usage surface: */ block the harvester can't read (DDICT)
  CLI_EDU_VARIANT           same command name contracted in both src/cli and src/edu
  CURATED_REFERENCE_GAP     registered, in no reference, not an alias -- a genuine gap
  NEEDS_HUMAN_DISPOSITION   none matched -- decide by hand

Report-only. Owner: member.derald . lane: AIF-067 . status: candidate
"""
from __future__ import annotations
import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

EDU_WORDS = ("student", "demo", "teaching", "educational", "placeholder")
ITEM_RE = re.compile(r'\{\s*"((?:\\.|[^"\\])+)"\s*,\s*"(?:\\.|[^"\\])*"\s*,\s*"((?:\\.|[^"\\])*)"\s*,')


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().upper()).replace("_", " ")


def compact(s: str) -> str:
    return norm(s).replace(" ", "")


def registry_handlers(root: Path) -> dict[str, tuple[str, str]]:
    text = (root / "src/cli/shell_commands.cpp").read_text(encoding="utf-8", errors="replace")
    out: dict[str, tuple[str, str]] = {}
    for key, body in re.findall(r'registry\(\)\.add\(\s*"([^"]+)"\s*,\s*\[\][^{]*\{([^{}]*)\}', text):
        m = re.search(r"\b([a-z]+)_([A-Za-z0-9_]+)\s*\(", body)
        if m:
            out[norm(key)] = (m.group(1), m.group(2))
    return out


def ref_names(root: Path, header: str) -> set[str]:
    t = (root / "include" / header).read_text(encoding="utf-8", errors="replace")
    return {norm(n) for n in re.findall(r'\{\s*"([^"]+)"', t)}


def ref_summaries(root: Path, header: str) -> dict[str, str]:
    t = (root / "include" / header).read_text(encoding="utf-8", errors="replace")
    return {norm(m.group(1)): m.group(2).lower() for m in ITEM_RE.finditer(t)}


def subusage_forms(root: Path) -> tuple[set[str], set[str]]:
    spaced: set[str] = set()
    for p in (root / "src/cli").rglob("*.cpp"):
        t = p.read_text(encoding="utf-8-sig", errors="replace").replace("\r", "")
        for b in re.finditer(r"(?ms)^\s*// @dottalk\.subusage.*?(?=^\s*// @dottalk\.subusage|^\s*(?!\s*//)\S|\Z)", t):
            par = re.search(r"(?m)^\s*// parent:\s*(.+?)\s*$", b.group(0))
            sub = re.search(r"(?m)^\s*// sub:\s*(.+?)\s*$", b.group(0))
            if par and sub:
                spaced.add(norm(f"{par.group(1)} {sub.group(1)}"))
    return spaced, {s.replace(" ", "") for s in spaced}


def usage_files(root: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for p in list((root / "src").rglob("*.cpp")) + list((root / "src").rglob("*.hpp")):
        t = p.read_text(encoding="utf-8-sig", errors="replace").replace("\r", "")
        for b in re.finditer(r"(?ms)^// @dottalk\.usage.*?(?=^// @dottalk\.usage|^\s*(?!//)\S|\Z)", t):
            m = re.search(r"(?m)^// command:\s*(.+?)\s*$", b.group(0))
            if m:
                for n in m.group(1).split("/"):
                    out[norm(n)].append(p.relative_to(root).as_posix())
    return out


def block_usage_names(root: Path) -> set[str]:
    out: set[str] = set()
    for p in (root / "src").rglob("*.cpp"):
        t = p.read_text(encoding="utf-8-sig", errors="replace")
        for b in re.finditer(r"/\*(?:(?!\*/).)*?@dottalk\.usage(?:(?!\*/).)*?\*/", t, re.S):
            for m in re.finditer(r"(?m)^\s*surface:\s*(.+?)\s*$", b.group(0)):
                out.add(norm(m.group(1)))
    return out


def crosswalk_functions(path: Path) -> set[str]:
    return {norm(r["canonical_name"]) for r in csv.DictReader(path.open(encoding="utf-8"))
            if r.get("entity_type") == "FUNCTION" and r.get("canonical_name")}


class Ctx:
    def __init__(self, root, crosswalk):
        self.dot = ref_names(root, "dotref.hpp")
        self.fox = ref_names(root, "foxref.hpp")
        self.ed = ref_names(root, "edref.hpp")
        self.reg = registry_handlers(root)
        self.subs, self.subs_c = subusage_forms(root)
        self.ufiles = usage_files(root)
        self.block = block_usage_names(root)
        self.fn = crosswalk_functions(crosswalk)
        self.sums = {**ref_summaries(root, "foxref.hpp"), **ref_summaries(root, "dotref.hpp")}


def recommend(name: str, c: Ctx):
    n = norm(name)
    summ = c.sums.get(n, "")
    if n in c.fn:
        return "FUNCTION_AUTHORITY", "crosswalk emits FN: identity; SYSFUNC owns it"
    if n in c.ed:
        return "EDUCATION_TOPIC", "edref"
    files = c.ufiles.get(n, [])
    if any(f.startswith("src/cli") for f in files) and any(f.startswith("src/edu") for f in files):
        return "CLI_EDU_VARIANT", " | ".join(files)
    if n in c.subs or compact(n) in c.subs_c:
        return "DELIBERATE_SUBFORM", "@dottalk.subusage ladder arm"
    if "alias of" in summ or "alias for" in summ:
        return "DELIBERATE_ALIAS", "reference summary declares an alias"
    if n in c.dot and n in c.fox:
        return "DELIBERATE_DUAL_HOME", "dotref + foxref (native + FoxPro wording)"
    if n in c.reg:
        pfx, base = c.reg[n]
        if pfx == "edu":
            return "EDUCATION_SURFACE", f"edu_ handler ({pfx}_{base})"
        for k2, (_p2, b2) in c.reg.items():
            if k2 != n and b2 == base and (k2 in c.dot or c.ufiles.get(k2)):
                return "DELIBERATE_ALIAS", f"alias of {k2} via cmd_{base}"
        if n in c.block:
            return "CONTRACT_FORMAT_NORMALIZE", "/* @dottalk.usage surface: */ block; normalize to // form"
        if any(w in summ for w in EDU_WORDS):
            return "EDUCATION_SURFACE", "reference summary marks demo/student/teaching surface"
        if n not in c.dot and n not in c.fox:
            return "CURATED_REFERENCE_GAP", f"registered ({pfx}_{base}), no reference entry, no alias"
    if any(w in summ for w in EDU_WORDS):
        return "EDUCATION_SURFACE", "reference summary marks demo/student/teaching surface"
    if n in c.fox and n not in c.dot and n not in c.reg:
        return "FOXPRO_COMPAT_REFERENCE", "foxref compatibility entry (not registered, not a function)"
    return "NEEDS_HUMAN_DISPOSITION", "no rule matched"


DECIDE = ("CLI_EDU_VARIANT", "CONTRACT_FORMAT_NORMALIZE", "CURATED_REFERENCE_GAP", "NEEDS_HUMAN_DISPOSITION")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--crosswalk", type=Path, required=True)
    ap.add_argument("--duplicates", type=Path)
    a = ap.parse_args(argv)
    root = a.repo_root.resolve()
    c = Ctx(root, a.crosswalk)

    review = [r["canonical_name"] for r in csv.DictReader(a.crosswalk.open(encoding="utf-8"))
              if r.get("entity_type") == "COMMAND" and r.get("validation_state") == "REVIEW"]
    dups = []
    if a.duplicates and a.duplicates.is_file():
        dups = [(r["identity"], r["layer"], r["evidence"]) for r in csv.DictReader(a.duplicates.open(encoding="utf-8"))]

    counts: dict[str, int] = defaultdict(int)
    print("== reference disposition recommender (Phase 1 Gate-1, report-only) ==\n")
    print(f"crosswalk REVIEW command rows: {len(review)}   duplicate rows: {len(dups)}\n")
    print("-- rows still needing a human decision (everything else auto-recommended deliberate) --")
    for name in sorted(review):
        disp, ev = recommend(name, c)
        counts[disp] += 1
        if disp in DECIDE:
            print(f"   {name:16} -> {disp}   ({ev})")
    for ident, layer, ev in dups:
        disp, why = recommend(ident, c)
        counts[f"dup:{disp}"] += 1
        if disp in DECIDE:
            print(f"   [{layer}] {ident:14} -> {disp}   ({ev})")
    print("\n== recommendation counts ==")
    for k in sorted(counts):
        print(f"   {k}: {counts[k]}")
    genuine = sum(v for k, v in counts.items() if any(d in k for d in DECIDE))
    print(f"\nrows still needing a human decision: {genuine}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
