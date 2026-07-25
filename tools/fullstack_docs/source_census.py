#!/usr/bin/env python3
"""
Source census + coverage gate for the universal @dottalk.file contract (AIF-050 M2/M3).

Computes the set algebra over the source tree:
  census      = files carrying @dottalk.file        (the harvestable node set)
  commands    = files carrying @dottalk.usage
  non_command = census \\ commands
  uncovered   = tracked source files NOT in census  (the advisory coverage gate)

Advisory by default (reports, exit 0). --strict makes `uncovered` a failure (exit 1) — the
promotion to a hard drift gate once the backfill is complete.

--sample <path> prints the first-pass @dottalk.file block a generator would emit from derivable
fields, demonstrating the cheap backfill without mutating the tree.

Owner: member.derald  ·  steward: member.ai.claude.cowork  ·  lane: AIF-050  ·  status: candidate
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

SRC_DIRS = ("src", "include")
EXTS = {".cpp", ".hpp", ".h", ".cc", ".cxx", ".hxx"}
FILE_RE = re.compile(r"@dottalk\.file\b")
USAGE_RE = re.compile(r"@dottalk\.usage\b")
OWNER_RE = re.compile(r"//\s*owner:\s*(\S+)")


def source_files(root: Path):
    """Tracked source under src/ + include/. Prefer git ls-files; fall back to walk."""
    rels = []
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "src", "include"], text=True
        )
        rels = out.splitlines()
    except Exception:
        for d in SRC_DIRS:
            base = root / d
            if base.is_dir():
                for p in base.rglob("*"):
                    if p.is_file():
                        rels.append(str(p.relative_to(root)).replace(os.sep, "/"))
    files = []
    for r in rels:
        p = root / r
        if p.suffix in EXTS and r.split("/", 1)[0] in SRC_DIRS:
            files.append((r, p))
    return sorted(set(files))


def head(path: Path, n: int = 4096) -> str:
    try:
        with open(path, "r", errors="ignore") as fh:
            return fh.read(n)  # contract blocks live at the top of the file
    except Exception:
        return ""


def derive_block(rel: str, text: str) -> str:
    parts = rel.split("/")
    subsystem = parts[1] if len(parts) > 2 else parts[0]
    is_cmd = bool(USAGE_RE.search(text))
    if is_cmd:
        layer = "command"
    elif "/tests/" in rel or rel.startswith("tests/") or "test" in Path(rel).stem:
        layer = "test"
    elif Path(rel).suffix in {".hpp", ".h", ".hxx"}:
        layer = "header"
    else:
        layer = "helper"
    m = OWNER_RE.search(text)
    owns = m.group(1) if (m and is_cmd) else ""
    return (
        "// @dottalk.file v1\n"
        f"// path: {rel}\n"
        f"// subsystem: {subsystem}\n"
        f"// layer: {layer}\n"
        f"// owns: {owns}\n"
        "// project: project.x64base.runtime\n"
        "// status: supported\n"
        f"// provenance: prov://{rel}\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("--strict", action="store_true", help="uncovered files fail (exit 1)")
    ap.add_argument("--list-uncovered", action="store_true", help="print uncovered files")
    ap.add_argument("--sample", metavar="PATH", help="print the derived @dottalk.file block")
    ap.add_argument("--write", action="store_true",
                    help="INSERT the derived @dottalk.file block at the top of each uncovered file (M2 backfill). Idempotent: files already carrying a block are skipped.")
    ap.add_argument("--only", metavar="PREFIXES",
                    help="restrict --write to files whose path starts with one of these comma-separated prefixes (e.g. src/bbs,include/bbs)")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    if args.sample:
        p = root / args.sample
        print(derive_block(args.sample, head(p)))
        return 0

    files = source_files(root)
    census, commands, uncovered = [], [], []
    for rel, p in files:
        t = head(p)
        in_file = bool(FILE_RE.search(t))
        in_usage = bool(USAGE_RE.search(t))
        if in_file:
            census.append(rel)
        else:
            uncovered.append(rel)
        if in_usage:
            commands.append(rel)

    if args.write:
        prefixes = tuple(s.strip() for s in args.only.split(",")) if args.only else None
        wrote = 0
        for rel in uncovered:
            if prefixes and not rel.startswith(prefixes):
                continue
            p = root / rel
            try:
                original = p.read_text(encoding="utf-8", errors="surrogateescape")
            except Exception as e:
                print(f"  SKIP (read) {rel}: {e}", file=sys.stderr)
                continue
            if FILE_RE.search(original[:4096]):
                continue                       # already carries a block; idempotent
            block = derive_block(rel, original[:4096])
            try:
                p.write_text(block + "\n" + original, encoding="utf-8", errors="surrogateescape")
                wrote += 1
            except Exception as e:
                print(f"  SKIP (write) {rel}: {e}", file=sys.stderr)
        scope = f" under {args.only}" if args.only else " (whole tree)"
        print(f"backfill: inserted @dottalk.file into {wrote} file(s){scope}")
        return 0

    total = len(files)
    non_command = sorted(set(census) - set(commands))
    print("=== @dottalk.file source census (AIF-050 M2/M3) ===")
    print(f"root:             {root}")
    print(f"total source:     {total}")
    print(f"census (@file):   {len(census)}")
    print(f"commands (@usage):{len(commands)}")
    print(f"non_command:      {len(non_command)}   # census \\ usage")
    print(f"uncovered:        {len(uncovered)}   # tracked source NOT in census (advisory gate)")
    cov = (len(census) / total * 100) if total else 0.0
    print(f"coverage:         {cov:.1f}%")
    if args.list_uncovered:
        for r in uncovered:
            print(f"  UNCOVERED {r}")
    if args.strict and uncovered:
        print(f"\nSTRICT: {len(uncovered)} file(s) missing @dottalk.file -> FAIL", file=sys.stderr)
        return 1
    if uncovered:
        print(f"\nadvisory: {len(uncovered)} file(s) missing @dottalk.file (not a failure yet)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
