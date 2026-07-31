#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, re, shutil
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZR", "docs/datadict/reports/DD096ZD2ZR-marker-local-patch-readiness-v0/dd096zd2zr_marker_local_patch_readiness_manifest.json", ["DD096ZD2ZR_MARKER_LOCAL_PATCH_READINESS_READY"]),
]

CONTRACT_BEGIN = "/*"
USAGE_SENTINEL = "@dottalk.usage v1"
CONTRACT_END_SENTINEL = "@dottalk.end"

INLINE_GENERATED_PATTERNS = [
    "DD096Z-D2ZN bridge helper notes",
    "The resolver bridge is intentionally available to DDICT call sites through:",
    "The actual call-site logic should use these helpers only at owner/table lookup boundaries.",
    "D2ZQ target:",
]

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")

def wt(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def wj(path: Path, obj):
    wt(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def wc(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def make_usage_contract() -> str:
    return """/*
@dottalk.usage v1
owner: DDICT
surface: DDICT
summary: Read-only Data Dictionary inspection command for active catalog metadata.
status: source_contract_review_candidate
profiles: ENGINE, PROFESSIONAL
read_mode: READ_ONLY
mutates: none

forms:
  DDICT STATUS
  DDICT TABLES
  DDICT FIELDS <table-or-alias>
  DDICT TAGS <table-or-alias>
  DDICT REL <object> [IN|OUT|BOTH]
  DDICT EVIDENCE <object>

alias_bridge:
  DDOBJECT -> DATA_DICTIONARY_OBJECTS
  DDATTR   -> DATA_DICTIONARY_OBJECT_ATTRIBUTES
  DDEDGE   -> DATA_DICTIONARY_RELATION_EDGES
  DDEVID   -> DATA_DICTIONARY_EVIDENCE_RECORDS
  DDGATE   -> DATA_DICTIONARY_GATE_RECORDS
  DDRUN    -> DATA_DICTIONARY_RUNS

active_roots:
  DBF  : dottalkpp/data/datadict
  CDX  : dottalkpp/data/indexes/datadict
  LMDB : dottalkpp/data/lmdb/datadict

contract_notes:
  - Preserve legacy DD* spellings as compatibility names.
  - Resolve DATA_DICTIONARY_* spellings as authoritative x64 catalog names.
  - FIELDS must keep DDICT FIELDS DDOBJECT working while bridging DATA_DICTIONARY_OBJECTS.
  - TAGS must distinguish catalog tag rows from physical CDX/LMDB artifacts.
  - If physical tag artifacts exist but catalog tag rows are absent, report an honest physical-artifact status instead of plain NO_CATALOG_TAGS_FOUND.

safety:
  - No DBF append, replace, delete, pack, zap, create, or load.
  - No active CDX/LMDB rebuild.
  - No HELP, CMDHELPCHK, manual publication, metadata catalog, or Data Dictionary catalog mutation.
  - Runtime surface remains read-only inspection.

evidence_lane:
  DD096Z-D2ZS reviewed source patch lane
@dottalk.end
*/
"""

def strip_existing_top_contract(text: str) -> str:
    stripped = text.lstrip("\ufeff")
    leading_bom = "\ufeff" if text.startswith("\ufeff") else ""
    if USAGE_SENTINEL in stripped[:3000] and stripped.startswith("/*"):
        end_idx = stripped.find("*/")
        if end_idx != -1:
            rest = stripped[end_idx + 2:]
            return leading_bom + rest.lstrip("\r\n")
    return text

def align_top_contract(text: str) -> tuple[str, str]:
    body = strip_existing_top_contract(text)
    contract = make_usage_contract().rstrip() + "\n\n"
    return contract + body.lstrip("\r\n"), "top_usage_contract_inserted_or_replaced"

def strip_generated_inline_comments(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    out = []
    removed = 0
    skip_next_blank = False
    for line in lines:
        if any(p in line for p in INLINE_GENERATED_PATTERNS):
            removed += 1
            skip_next_blank = False
            continue
        # Remove purely generated bridge helper ref lines, but preserve D2ZP marker lines themselves.
        if "dottalk::datadict::ddict_bridge_" in line and line.strip().startswith("//"):
            removed += 1
            continue
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), removed

def validate_contract(text: str):
    top = text[:2500]
    checks = []
    def add(name, observed, required, passed):
        checks.append({"check": name, "observed": observed, "required": required, "pass": int(passed)})
    add("starts_with_block_comment", int(text.lstrip("\ufeff").startswith("/*")), 1, text.lstrip("\ufeff").startswith("/*"))
    add("usage_sentinel_near_top", int(USAGE_SENTINEL in top), 1, USAGE_SENTINEL in top)
    add("contract_end_near_top", int(CONTRACT_END_SENTINEL in top), 1, CONTRACT_END_SENTINEL in top)
    add("has_forms", int("forms:" in top), 1, "forms:" in top)
    add("has_ddict_fields_form", int("DDICT FIELDS <table-or-alias>" in top), 1, "DDICT FIELDS <table-or-alias>" in top)
    add("has_ddict_tags_form", int("DDICT TAGS <table-or-alias>" in top), 1, "DDICT TAGS <table-or-alias>" in top)
    add("has_alias_bridge", int("alias_bridge:" in top), 1, "alias_bridge:" in top)
    add("has_read_only_safety", int("read_mode: READ_ONLY" in top and "mutates: none" in top), 1, "read_mode: READ_ONLY" in top and "mutates: none" in top)
    add("has_active_roots", int("active_roots:" in top), 1, "active_roots:" in top)
    return checks

def default_target(repo: Path):
    review = repo / "docs/datadict/reviews/DD096ZD2ZS/cmd_ddict.cpp.review_candidate"
    if review.exists():
        return review
    return repo / "src/cli/cmd_ddict.cpp"

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZT top usage contract alignment")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZT-top-usage-contract-alignment-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--target-file", default="")
    ap.add_argument("--apply-contract", action="store_true")
    ap.add_argument("--strip-generated-inline-comments", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_top_usage_contract_alignment"
    gen.mkdir(parents=True, exist_ok=True)

    blockers = 0
    pre_rows = []
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        observed = read_json(p).get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zt_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    target = Path(args.target_file) if args.target_file else default_target(repo)
    if not target.is_absolute():
        target = repo / target

    original = read_text(target)
    aligned, align_status = align_top_contract(original)
    inline_removed = 0
    if args.strip_generated_inline_comments:
        aligned, inline_removed = strip_generated_inline_comments(aligned)

    wt(gen / "cmd_ddict_contract_aligned_preview.cpp", aligned)
    wt(gen / "DD096ZD2ZT_TOP_USAGE_CONTRACT_BLOCK.txt", make_usage_contract())
    validation_rows = validate_contract(aligned)
    wc(gen / "dd096zd2zt_usage_contract_validation.csv", validation_rows, ["check","observed","required","pass"])

    required_missing = int(not target.exists())
    validation_failures = sum(1 for r in validation_rows if int(r["pass"]) != 1)
    source_files_written = 0
    backups_written = 0

    if args.apply_contract:
        if blockers or required_missing:
            raise SystemExit("Precondition or target-file blockers present; refusing --apply-contract.")
        if validation_failures:
            raise SystemExit("Contract validation failed; refusing --apply-contract.")
        backup_root = repo / f"docs/datadict/backups/DD096ZD2ZT-contract-backup-{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup = backup_root / target.relative_to(repo)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        backups_written = 1
        wt(target, aligned)
        source_files_written = 1

    failures = blockers + required_missing + validation_failures
    if failures:
        status = "DD096ZD2ZT_TOP_USAGE_CONTRACT_ALIGNMENT_REVIEW"
    elif args.apply_contract:
        status = "DD096ZD2ZT_TOP_USAGE_CONTRACT_ALIGNED"
    else:
        status = "DD096ZD2ZT_TOP_USAGE_CONTRACT_ALIGNMENT_READY"

    boundary = [
        {"boundary": "top_usage_contract_alignment", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "target_file_written", "observed": source_files_written, "required": 1 if args.apply_contract else 0, "pass": int(source_files_written == (1 if args.apply_contract else 0))},
        {"boundary": "runtime_logic_rewritten", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zt_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZT Top Usage Contract Alignment

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZT fixes the comment/contract issue before the reviewed source patch.

The source-level comment section belongs at the top of the file and must be a SelfDoc-compatible `@dottalk.usage v1` contract. Runtime logic is not changed.

## Summary

- Target file: `{target}`
- Precondition blockers: **{blockers}**
- Target missing: **{required_missing}**
- Alignment status: **{align_status}**
- Validation failures: **{validation_failures}**
- Generated inline comments removed: **{inline_removed}**
- Target file written: **{source_files_written}**
- Runtime logic rewritten: **0**

## Next

After this is green, continue the D2ZS reviewed patch candidate from the contract-aligned file.
"""
    wt(out / "DD096ZD2ZT_TOP_USAGE_CONTRACT_ALIGNMENT_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zt_top_usage_contract_alignment_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "target_file": str(target),
        "precondition_blockers": blockers,
        "target_missing": required_missing,
        "align_status": align_status,
        "validation_failures": validation_failures,
        "generated_inline_comments_removed": inline_removed,
        "apply_contract": int(args.apply_contract),
        "target_file_written": source_files_written,
        "backups_written": backups_written,
        "runtime_logic_rewritten": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Continue D2ZS reviewed source patch candidate from the contract-aligned file.",
    }
    wj(out / "dd096zd2zt_top_usage_contract_alignment_manifest.json", manifest)

    print(f"DD096Z-D2ZT top usage contract alignment manifest: {out / 'dd096zd2zt_top_usage_contract_alignment_manifest.json'}")
    print(f"status: {status}; target_file_written: {source_files_written}; validation_failures: {validation_failures}; runtime_logic_rewritten: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
