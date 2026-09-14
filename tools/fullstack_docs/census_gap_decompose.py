#!/usr/bin/env python3
"""Decompose the source_census / contract_inventory file-count gap.

Applies each tool's OWN inclusion rule, then names every file that one
counts and the other does not. Read-only.

  python tmp/census_gap_decompose.py --repo-root D:\\code\\ccode
"""
import argparse, re, subprocess, sys
from pathlib import Path

# source_census.py:37-40
CENSUS_DIRS = ("src", "include", "bindings")
CENSUS_EXTS = {".cpp", ".hpp", ".h", ".cc", ".cxx", ".hxx", ".c", ".inl", ".ipp"}
CENSUS_RE = re.compile(r"@dottalk\.usage\b")

# contract_inventory.py:67,76,89
INV_EXTS = {".cpp", ".hpp", ".h", ".cc", ".cxx"}
INV_MARKER = "@dottalk.usage v1"
VOLUNTARY = "@dottalk.usage.voluntary"


def read(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    a = ap.parse_args()
    root = a.repo_root.resolve()

    tracked = subprocess.run(
        ["git", "ls-files"], cwd=root, text=True, capture_output=True, check=True
    ).stdout.splitlines()

    census, inventory, voluntary = set(), set(), set()

    # census: filesystem walk under its three dirs
    for d in CENSUS_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix in CENSUS_EXTS:
                if CENSUS_RE.search(read(p)):
                    census.add(p.relative_to(root).as_posix())

    # inventory: git ls-files, five extensions, literal marker
    for rel in tracked:
        if Path(rel).suffix.lower() not in INV_EXTS:
            continue
        t = read(root / rel)
        if VOLUNTARY in t:
            voluntary.add(rel)
        if INV_MARKER in t:
            inventory.add(rel)

    only_c = sorted(census - inventory)
    only_i = sorted(inventory - census)

    print(f"source_census      files : {len(census)}")
    print(f"contract_inventory files : {len(inventory)}")
    print(f"voluntary (separate)     : {len(voluntary)}")
    print(f"gap                      : {len(census) - len(inventory)}")
    print()
    print(f"CENSUS ONLY ({len(only_c)}) -- counted by census, not a mined contract")
    for rel in only_c:
        t = read(root / rel)
        why = []
        if Path(rel).suffix.lower() not in INV_EXTS:
            why.append(f"ext {Path(rel).suffix}")
        if rel not in tracked:
            why.append("UNTRACKED")
        if VOLUNTARY in t and INV_MARKER not in t:
            why.append("voluntary")
        if INV_MARKER not in t and VOLUNTARY not in t:
            why.append("marker is not 'usage v1'")
        print(f"    {rel:<62} {'; '.join(why) or 'UNEXPLAINED'}")
    print()
    print(f"INVENTORY ONLY ({len(only_i)}) -- mined, but outside census scope")
    for rel in only_i:
        why = "outside src/include/bindings" if rel.split("/", 1)[0] not in CENSUS_DIRS else "UNEXPLAINED"
        print(f"    {rel:<62} {why}")
    print()
    unexplained = [r for r in only_c
                   if Path(r).suffix.lower() in INV_EXTS
                   and r in tracked
                   and INV_MARKER not in read(root / r)
                   and VOLUNTARY not in read(root / r)]
    print(f"UNEXPLAINED census-only files: {len(unexplained)}")
    for rel in unexplained:
        print(f"    {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
