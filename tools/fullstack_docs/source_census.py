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
import csv
import datetime
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

# Keep identical to stack_audit_v1.py and reharvest_source_comment_catalog.py.
# See the SRC_DIRS note in stack_audit_v1.py for why divergence here manufactures
# phantom drift findings. Settled 2026-07-26: git ls-files over these roots.
SRC_DIRS = ("src", "include", "bindings")
EXTS = {".cpp", ".hpp", ".h", ".cc", ".cxx", ".hxx", ".c", ".inl", ".ipp"}
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
    """Tracked source under SRC_DIRS. Prefer git ls-files; fall back to walk.

    The roots MUST come from SRC_DIRS on both paths. They did not: the git call
    hardcoded ("src", "include") while only the fallback walk read the constant,
    so widening SRC_DIRS to include bindings/ changed nothing in normal operation
    and the census silently kept reporting 1034/1034 = 100%.

    That is the same defect this repo documented the same evening in AIF-065
    (BUILDLMDB's size ladder is parsed and echoed, then overridden downstream):
    a value that looks authoritative because it is declared at the top of the
    file, and is not consulted by the path that actually runs.
    """
    rels = []
    try:
        out = subprocess.check_output(
            ["git", "--no-optional-locks", "-C", str(root), "ls-files", *SRC_DIRS],
            text=True,
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
        # utf-8-sig strips a leading BOM on read so a rewrite never strands it
        # mid-file (see the AIF-062 backfill BOM regression).
        text = path.read_text(encoding="utf-8-sig", errors="surrogateescape")
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


# --------------------------------------------------------------------------- #
# M1 harvest (read-only): SYSSRC + SYSCMDDOC emitters
# Design: dottalkpp/docs/authority/SOURCE_CONTRACT_COLLECTION_DESIGN_v1.md
#
# Pure function of the tree. Emits CSV only -- never writes a table, never
# mutates source. SRC_HASH is taken over the BANNER BLOCK ONLY so ordinary body
# edits do not register as contract drift; banner edits do.
# --------------------------------------------------------------------------- #

# Two observed contract dialects. Phase 1B doctrine: record drift, do not collapse.
#   slash : // @dottalk.usage v1   + `command:` / `usage:`      (226 files)
#   block : /* @dottalk.usage v1   + `surface:` / `forms:`      (cmd_ddict.cpp)
USAGE_BLOCK_RE = re.compile(r"// @dottalk\.usage v1\n(?://[^\n]*\n)+")
USAGE_BLOCK_ALT_RE = re.compile(r"/\*\s*\n?\s*@dottalk\.usage v1\n(.*?)\*/", re.DOTALL)

BANNER_FIELDS = ["subsystem", "layer", "owns", "project", "lane", "owner", "status"]

# Values derive_block() hardcodes. Used to classify authored vs derived (FLD_PROV).
DERIVED_CONSTANTS = {
    "project": "project.x64base.runtime",
    "owner": "member.derald",
    "status": "supported",
}

SYSSRC_COLS = [
    "FILE_ID", "PATH", "STEM", "EXT", "SUBSYSTEM", "LAYER", "PROJECT", "LANE",
    "OWNER", "STATUS", "IS_CMD", "CMD_COUNT", "BANNER_V", "SRC_HASH",
    "HARVEST_AT", "FLD_PROV",
]

SYSCMDDOC_COLS = [
    "CMD_ID", "CAN_NAME", "FILE_ID", "DIALECT", "CATEGORY", "EFFECT", "NOARGS",
    "MUTATES", "RELATED", "USAGE_ACC", "SUMMARY", "USAGE_TXT", "EXAMPLES",
    "RISK", "NOTES", "SRC_HASH", "HARVEST_AT",
]


def file_id(rel: str) -> str:
    """Stable key: src/cli/cmd_if.cpp -> SRC_CLI_CMD_IF_CPP"""
    return re.sub(r"[^A-Za-z0-9]+", "_", rel).strip("_").upper()


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", "surrogateescape")).hexdigest()


def parse_banner_fields(block: str) -> dict:
    """Single-line `// field: value` pairs from a @dottalk.file block."""
    out = {}
    for f in BANNER_FIELDS:
        m = re.search(rf"//[ \t]*{re.escape(f)}:[ \t]*(.*)", block)
        out[f] = m.group(1).strip() if m else ""
    return out


def parse_usage_fields(block: str) -> dict:
    """
    Parse a @dottalk.usage block, honoring multi-line continuations:

        // summary:
        //   Build or report the current HELP DATA catalogs.

    A line whose comment body matches `name:` starts a field; anything else is
    appended to the field in progress.
    """
    fields: dict[str, list[str]] = {}
    cur = None
    for raw in block.splitlines():
        body = raw[2:] if raw.startswith("//") else raw
        if body.strip() in ("", "@dottalk.usage v1"):
            continue
        m = re.match(r"\s*([a-z][a-z0-9-]*):\s*(.*)$", body)
        if m:
            cur = m.group(1)
            val = m.group(2).strip()
            fields.setdefault(cur, [])
            if val:
                fields[cur].append(val)
        elif cur is not None:
            fields[cur].append(body.strip())
    return {k: "\n".join(v).strip() for k, v in fields.items()}


def field_provenance(vals: dict, rel: str, text: str) -> str:
    """
    Compact per-field provenance: A=authored, D=derived, E=empty.

    A field is DERIVED when its current value is byte-identical to what
    derive_block() would regenerate for this file -- i.e. the backfill could
    have produced it and it carries no human judgement. Anything else is
    AUTHORED. This is what makes a real `status: candidate` distinguishable
    from the 1034 backfilled `status: supported` defaults.
    """
    derived = parse_banner_fields(derive_block(rel, text))
    marks = []
    for f in BANNER_FIELDS:
        v = vals.get(f, "")
        if not v:
            marks.append(f"{f}=E")
        elif v == derived.get(f, ""):
            marks.append(f"{f}=D")
        else:
            marks.append(f"{f}=A")
    return ";".join(marks)


def harvest(root: Path):
    """Return (syssrc_rows, syscmddoc_rows, anomalies). Read-only."""
    stamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    src_rows, doc_rows, anomalies = [], [], []

    for rel, p in source_files(root):
        try:
            text = p.read_text(encoding="utf-8-sig", errors="surrogateescape")
        except Exception as e:
            print(f"  SKIP (read) {rel}: {e}", file=sys.stderr)
            continue

        bm = BLOCK_RE.search(text)
        if not bm:
            continue  # uncovered; the census/--write path owns these
        banner = bm.group(0)
        vals = parse_banner_fields(banner)

        usage_blocks = [(b, "slash") for b in USAGE_BLOCK_RE.findall(text)]
        usage_blocks += [(b, "block") for b in USAGE_BLOCK_ALT_RE.findall(text)]

        # Mention-only: the marker appears (a code string, prose) but no parseable
        # contract. The census counts these as commands; they are false positives.
        if not usage_blocks and "@dottalk.usage" in text:
            anomalies.append((rel, "mention-only (no parseable contract block)"))

        cmd_names = []
        for ub, dialect in usage_blocks:
            uf = parse_usage_fields(ub)
            # dialect fallbacks: block form uses surface:/forms: instead of command:/usage:
            name = (uf.get("command") or uf.get("surface") or "").strip()
            if not name:
                anomalies.append((rel, f"{dialect} block with no command:/surface: field"))
                continue
            if dialect == "block":
                anomalies.append(
                    (rel, f"non-canonical block dialect (surface/forms) for {name}"))
            cmd_names.append(name)
            doc_rows.append({
                "CMD_ID": "CMD_" + re.sub(r"[^A-Za-z0-9]+", "_", name.upper()).strip("_"),
                "CAN_NAME": name.upper(),
                "FILE_ID": file_id(rel),
                "DIALECT": dialect,
                "CATEGORY": uf.get("category", ""),
                "EFFECT": uf.get("effect", ""),
                "NOARGS": uf.get("noargs", ""),
                "MUTATES": uf.get("mutates", ""),
                "RELATED": uf.get("related", ""),
                "USAGE_ACC": uf.get("usage-access", ""),
                "SUMMARY": uf.get("summary", ""),
                "USAGE_TXT": uf.get("usage") or uf.get("forms", ""),
                "EXAMPLES": uf.get("examples", ""),
                "RISK": uf.get("risk", ""),
                "NOTES": uf.get("notes", ""),
                "SRC_HASH": sha1(ub),
                "HARVEST_AT": stamp,
            })

        src_rows.append({
            "FILE_ID": file_id(rel),
            "PATH": rel,
            "STEM": Path(rel).stem,
            "EXT": Path(rel).suffix,
            "SUBSYSTEM": vals["subsystem"],
            "LAYER": vals["layer"],
            "PROJECT": vals["project"],
            "LANE": vals["lane"],
            "OWNER": vals["owner"],
            "STATUS": vals["status"],
            "IS_CMD": "T" if usage_blocks else "F",
            "CMD_COUNT": str(len(cmd_names)),
            "BANNER_V": "v1",
            "SRC_HASH": sha1(banner),
            "HARVEST_AT": stamp,
            "FLD_PROV": field_provenance(vals, rel, text),
        })

    return src_rows, doc_rows, anomalies


def write_csv(path: str, cols: list, rows: list, bom: bool = False) -> None:
    """
    CSV ENCODING POLICY (verified against the engine, 2026-07-26):

      canonical = UTF-8, NO BOM.

    Rationale -- the engine, not the spreadsheet, defines the lane:
      * every existing canonical import file is BOM-less
        (SYSCMD/SYSARGS/SYSFUNC/SYSMSG _IMPORT_v1.csv)
      * the engine WRITES BOM-less CSV (no BOM emitter anywhere in src/)
      * cmd_import.cpp READS a BOM tolerantly -- strip_import_utf8_bom() clears it
        from column 0 of the HEADER record only (split_import_csv_record(rec, true)
        at cmd_import.cpp:146; data rows pass false). Correct, since a BOM can only
        occur at file start.

    So a BOM would import fine, but it would diverge from every other file in the
    lane and from the engine's own output. BOM is therefore OPT-IN (--csv-bom) and
    intended only for Excel review copies, never for the committed artifact:
    Excel misreads BOM-less UTF-8 as the ANSI codepage.

    Line endings are csv module default (\\r\\n); the engine strips trailing CR
    (strip_import_trailing_cr), and the existing lane files are already mixed
    CRLF/LF, so either is safe.
    """
    enc = "utf-8-sig" if bom else "utf-8"
    with open(path, "w", newline="", encoding=enc) as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"harvest: {len(rows)} row(s) -> {path}"
          f"{'  [UTF-8 BOM: review copy, not canonical]' if bom else ''}")


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
    ap.add_argument("--emit-syssrc", metavar="CSV",
                    help="M1 harvest: write the file-grain SYSSRC candidate CSV "
                         "(read-only; one row per source file carrying a banner)")
    ap.add_argument("--emit-syscmddoc", metavar="CSV",
                    help="M1 harvest: write the command-grain SYSCMDDOC candidate CSV "
                         "(read-only; one row per @dottalk.usage block)")
    ap.add_argument("--csv-bom", action="store_true",
                    help="write CSVs as UTF-8 WITH BOM. Excel-review copies ONLY -- the "
                         "canonical lane is BOM-less (see write_csv policy note). "
                         "cmd_import.cpp tolerates a BOM, so these still import.")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    if args.emit_syssrc or args.emit_syscmddoc:
        src_rows, doc_rows, anomalies = harvest(root)
        if args.emit_syssrc:
            write_csv(args.emit_syssrc, SYSSRC_COLS, src_rows, bom=args.csv_bom)
        if args.emit_syscmddoc:
            write_csv(args.emit_syscmddoc, SYSCMDDOC_COLS, doc_rows, bom=args.csv_bom)
        # SYSCMDDOC is the FIRST lane file to use quoted multi-line cells.
        # csv::read_record() supports them (it keeps reading while a record is
        # mid-quote), but no existing metadata CSV exercises that path -- so it is
        # untested HERE. Flag it rather than assume it.
        multiline = sum(1 for r in doc_rows
                        for c in ("SUMMARY", "USAGE_TXT", "EXAMPLES", "RISK", "NOTES")
                        if "\n" in r.get(c, ""))
        if multiline:
            print(f"harvest: NOTE {multiline} quoted multi-line cell(s). "
                  f"csv::read_record supports these, but no existing metadata CSV "
                  f"uses them -- smoke-test IMPORT on a scratch table before M2.")
        cmd_files = sum(1 for r in src_rows if r["IS_CMD"] == "T")
        print(f"harvest: {len(src_rows)} file rows "
              f"({cmd_files} command-bearing, {len(src_rows) - cmd_files} non-command), "
              f"{len(doc_rows)} command doc rows")
        # Provenance summary: how much of the banner estate is real vs backfilled.
        authored = sum(1 for r in src_rows if "=A" in r["FLD_PROV"])
        print(f"harvest: {authored} file(s) carry at least one AUTHORED banner field "
              f"({len(src_rows) - authored} fully derived/empty)")
        if anomalies:
            print(f"\nharvest: {len(anomalies)} contract anomaly/anomalies "
                  f"(reported, not corrected):", file=sys.stderr)
            for rel, why in anomalies:
                print(f"  ? {rel}: {why}", file=sys.stderr)
        return 0

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
                # utf-8-sig strips a leading BOM so prepending the banner cannot
                # strand it at line ~10 (the AIF-062 backfill BOM regression).
                original = p.read_text(encoding="utf-8-sig", errors="surrogateescape")
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
