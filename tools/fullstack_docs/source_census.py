#!/usr/bin/env python3
"""
Source census + coverage gate for the universal @dottalk.file contract (AIF-050 M2/M3).

Computes the set algebra over the source tree:
  census      = files carrying @dottalk.file        (the harvestable node set)
  commands    = files carrying @dottalk.usage
  non_command = census \\ commands
  uncovered   = tracked source files NOT in census  (the advisory coverage gate)

Advisory by default (reports, exit 0). --strict makes `uncovered` a failure (exit 1) -- the
promotion to a hard drift gate once the backfill is complete.

--sample <path> prints the first-pass @dottalk.file block a generator would emit from derivable
fields, demonstrating the cheap backfill without mutating the tree.

--write  inserts a @dottalk.file block at the top of every uncovered file (idempotent).
--upgrade rewrites existing blocks from the OLD schema (had path:/provenance:) to the
          current schema (lane:/owner:), preserving manually-set layer: and owns: values.
--only <prefixes>  restricts --write or --upgrade to files under those comma-separated prefixes.

Owner: member.derald  . steward: member.ai.claude.cowork  . lane: AIF-050  . status: candidate
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

# Match the full @dottalk.file block: header line + consecutive // lines (stops at blank/non-//)
BLOCK_RE = re.compile(r"// @dottalk\.file v1\n(?://[^\n]*\n)+")

# Lane assignments: subsystem directory -> AIF lane (files created/primarily owned in that lane)
SUBSYSTEM_LANE: dict[str, str] = {
    "bbs":      "AIF-052",   # AI-BBS agent-server
    "security": "AIF-053",   # NET egress + Argon2id crypto
    "identity": "AIF-045",   # identity RBAC + AI token auth
    "selfdoc":  "AIF-050",   # source traceability / contract family
}

# Per-stem overrides for files whose lane differs from their directory subsystem
STEM_LANE: dict[str, str] = {
    "cmd_bbs":   "AIF-052",
    "cmd_net":   "AIF-053",
    "bbsd_main": "AIF-054",
}


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
            return fh.read(n)
    except Exception:
        return ""


def derive_lane(rel: str) -> str:
    """Best-effort lane from subsystem directory + per-stem overrides."""
    stem = Path(rel).stem
    if stem in STEM_LANE:
        return STEM_LANE[stem]
    parts = rel.split("/")
    subsystem = parts[1] if len(parts) > 2 else parts[0]
    return SUBSYSTEM_LANE.get(subsystem, "")


def derive_block(rel: str, text: str,
                 override_layer: str = "", override_owns: str = "") -> str:
    """
    Build a @dottalk.file v1 block for rel.
    override_layer / override_owns: preserved values from an existing block (upgrade path).
    """
    parts = rel.split("/")
    subsystem = parts[1] if len(parts) > 2 else parts[0]
    stem = Path(rel).stem
    suffix = Path(rel).suffix

    is_cmd = bool(USAGE_RE.search(text))

    if override_layer:
        layer = override_layer
    elif is_cmd:
        layer = "command"
    elif "/tests/" in rel or rel.startswith("tests/") or "test" in stem:
        layer = "test"
    elif suffix in {".hpp", ".h", ".hxx"}:
        layer = "header"
    else:
        layer = "helper"

    if override_owns:
        owns = override_owns
    elif is_cmd:
        # try to extract from @dottalk.usage owns: line in the file body
        m = re.search(r"//[ \t]*owns:[ \t]*(\S[^\n]*)", text)
        owns = m.group(1).strip() if m else ""
    else:
        owns = ""

    lane = derive_lane(rel)

    return (
        "// @dottalk.file v1\n"
        f"// subsystem: {subsystem}\n"
        f"// layer: {layer}\n"
        f"// owns: {owns}\n"
        f"// project: project.x64base.runtime\n"
        f"// lane: {lane}\n"
        f"// owner: member.derald\n"
        f"// status: supported\n"
    )


def _extract_field(block: str, field: str) -> str:
    """Pull the value of a // field: ... line from an existing block.
    Uses [ \\t]* (horizontal whitespace only) so a blank owns: line never
    bleeds into the next // line."""
    m = re.search(rf"//[ \t]*{re.escape(field)}:[ \t]*(.*)", block)
    return m.group(1).strip() if m else ""


def upgrade_one(path: Path, rel: str) -> bool:
    """
    Rewrite an existing @dottalk.file block to the current schema.
    Preserves layer: and owns: from the old block.
    Returns True if the file was modified.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="surrogateescape")
    except Exception as e:
        print(f"  SKIP (read) {rel}: {e}", file=sys.stderr)
        return False

    m = BLOCK_RE.search(text)
    if not m:
        return False  # no existing block

    old_block = m.group(0)

    # Already on new schema (no path: field) -- skip
    if "// path:" not in old_block and "// provenance:" not in old_block:
        return False

    old_layer = _extract_field(old_block, "layer")
    old_owns  = _extract_field(old_block, "owns")

    new_block = derive_block(rel, text,
                             override_layer=old_layer,
                             override_owns=old_owns)
    new_text = text.replace(old_block, new_block, 1)
    if new_text == text:
        return False

    try:
        path.write_text(new_text, encoding="utf-8", errors="surrogateescape")
        return True
    except Exception as e:
        print(f"  SKIP (write) {rel}: {e}", file=sys.stderr)
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("--strict", action="store_true",
                    help="uncovered files fail (exit 1)")
    ap.add_argument("--list-uncovered", action="store_true",
                    help="print uncovered files")
    ap.add_argument("--sample", metavar="PATH",
                    help="print the derived @dottalk.file block for PATH")
    ap.add_argument("--write", action="store_true",
                    help="INSERT the derived block at the top of each uncovered file "
                         "(idempotent: files already carrying a block are skipped)")
    ap.add_argument("--upgrade", action="store_true",
                    help="REWRITE existing blocks from old schema (path:/provenance:) "
                         "to current schema (lane:/owner:), preserving layer: and owns:")
    ap.add_argument("--only", metavar="PREFIXES",
                    help="restrict --write/--upgrade to files whose path starts with one "
                         "of these comma-separated prefixes (e.g. src/bbs,include/bbs)")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    if args.sample:
        p = root / args.sample
        print(derive_block(args.sample, head(p)))
        return 0

    files = source_files(root)
    prefixes = (tuple(s.strip() for s in args.only.split(","))
                if args.only else None)

    if args.upgrade:
        upgraded = 0
        skipped  = 0
        for rel, p in files:
            if prefixes and not rel.startswith(prefixes):
                continue
            t = head(p)
            if not FILE_RE.search(t):
                continue   # no existing block; --write handles these
            if upgrade_one(p, rel):
                print(f"  upgraded {rel}")
                upgraded += 1
            else:
                skipped += 1
        scope = f" under {args.only}" if args.only else " (whole tree)"
        print(f"upgrade: {upgraded} block(s) rewritten, {skipped} already current{scope}")
        return 0

    census, commands, uncovered = [], [], []
    for rel, p in files:
        t = head(p)
        in_file  = bool(FILE_RE.search(t))
        in_usage = bool(USAGE_RE.search(t))
        if in_file:
            census.append(rel)
        else:
            uncovered.append(rel)
        if in_usage:
            commands.append(rel)

    if args.write:
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
                continue   # already has a block; idempotent
            block = derive_block(rel, original[:4096])
            try:
                p.write_text(block + "\n" + original,
                             encoding="utf-8", errors="surrogateescape")
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
        print(f"\nSTRICT: {len(uncovered)} file(s) missing @dottalk.file -> FAIL",
              file=sys.stderr)
        return 1
    if uncovered:
        print(f"\nadvisory: {len(uncovered)} file(s) missing @dottalk.file (not a failure yet)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
