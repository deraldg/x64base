#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

REQUIRED = {
    "DD096ZD2S": (
        "docs/datadict/reports/DD096ZD2S-single-table-cdx-lmdb-proof-closure-v0/dd096zd2s_single_table_cdx_lmdb_proof_closure_manifest.json",
        ["DD096ZD2S_SINGLE_TABLE_CDX_LMDB_PROOF_GREEN"],
    ),
    "DD096ZGQ": (
        "docs/datadict/reports/DD096ZGQ-candidate-raw-smoke-closure-v0/dd096zgq_candidate_raw_smoke_closure_manifest.json",
        ["DD096ZGQ_CANDIDATE_RAW_SMOKE_CLOSURE_GREEN"],
    ),
}

# Actual intended STRUCT field names from the accepted DD096Z-D tag plan.
TABLES: List[Tuple[str, int, List[Tuple[str, str]]]] = [
    ("DATA_DICTIONARY_OBJECTS", 10, [
        ("CATALOG_OBJECT_ID", "CATALOG_OBJECT_ID"),
        ("CATALOG_OBJECT_NAME", "CATALOG_OBJECT_NAME"),
    ]),
    ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", 127, [
        ("CATALOG_OBJECT_ID", "CATALOG_OBJECT_ID"),
        ("CATALOG_ATTRIBUTE_NAME", "CATALOG_ATTRIBUTE_NAME"),
    ]),
    ("DATA_DICTIONARY_RELATION_EDGES", 16, [
        ("RELATION_FROM_OBJECT_ID", "RELATION_FROM_OBJECT_ID"),
        ("RELATION_TO_OBJECT_ID", "RELATION_TO_OBJECT_ID"),
    ]),
    ("DATA_DICTIONARY_EVIDENCE_RECORDS", 7, [
        ("CATALOG_OBJECT_ID", "CATALOG_OBJECT_ID"),
    ]),
    ("DATA_DICTIONARY_GATE_RECORDS", 3, [
        ("GATE_RECORD_ID", "GATE_RECORD_ID"),
    ]),
    ("DATA_DICTIONARY_RUNS", 2, [
        ("RUN_RECORD_ID", "RUN_RECORD_ID"),
    ]),
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

def wc(path: Path, rows: List[Dict], fields: List[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def make_rebuild_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2T full six-table candidate-only CDX/LMDB rebuild")
    lines.append("* Uses the D2S-proven pattern: CDX CREATE, CDX ADDTAG <actual field>, BUILDLMDB CLEAN YES.")
    lines.append("* Candidate paths only. No active Data Dictionary root.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("CLOSE ALL")
    lines.append("")
    for table, expected, tags in TABLES:
        lines.append(f"* ---------- {table}; expected records {expected} ----------")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("CDX CREATE")
        for tag_name, expr in tags:
            lines.append(f"CDX ADDTAG {tag_name}")
        lines.append("CDX INFO")
        lines.append("BUILDLMDB CLEAN YES")
        # Verify one order per table, and second tag when present.
        for tag_name, expr in tags:
            lines.append(f"SET ORDER TO {tag_name}")
            lines.append("LIST")
        lines.append("CLOSE ALL")
        lines.append("")
    lines.append("* DD096Z-D2T full candidate rebuild complete.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def make_verify_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2T full candidate rebuild verification")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("CLOSE ALL")
    lines.append("")
    for table, expected, tags in TABLES:
        lines.append(f"* ---------- verify {table}; expected records {expected} ----------")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("CDX INFO")
        for tag_name, expr in tags:
            lines.append(f"SET ORDER TO {tag_name}")
            lines.append("LIST")
        lines.append("CLOSE ALL")
        lines.append("")
    lines.append("* DD096Z-D2T verification complete.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def scan_runtime(text: str) -> Dict[str, int]:
    up = text.upper()
    metrics: Dict[str, int] = {}
    metrics["proof_supplied"] = int(bool(text))
    metrics["candidate_path_seen"] = int("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up)
    metrics["active_datadict_seen"] = int("DOTTALKPP\\DATA\\DATADICT" in up or "DOTTALKPP/DATA/DATADICT" in up)
    metrics["buildlmdb_ok_count"] = len(re.findall(r"BUILDLMDB:\s*DONE\s+OK=1\s+TAGS REBUILT", up))
    metrics["buildlmdb_failed_count"] = len(re.findall(r"BUILDLMDB:\s*FAILED", up))
    metrics["lmdb_mode_count"] = len(re.findall(r"MODE LMDB", up))
    metrics["cdx_create_count"] = len(re.findall(r"CDX CREATED:", up))
    metrics["cdx_addtag_count"] = len(re.findall(r"CDX ADDTAG:\s*ADDED", up))
    for table, expected, tags in TABLES:
        key = table.lower()
        metrics[f"{key}_seen"] = int(table in up)
        metrics[f"{key}_expected_count_seen"] = int(bool(re.search(re.escape(table) + r".{0,80}(RECORD COUNT|RECS:)\s*" + str(expected), up, flags=re.DOTALL)))
        metrics[f"{key}_buildlmdb_ok_seen"] = int(table in up and "BUILDLMDB: DONE OK=1" in up)
        for tag_name, expr in tags:
            tkey = f"{key}_{tag_name.lower()}"
            metrics[f"{tkey}_addtag_seen"] = int(f"CDX ADDTAG: ADDED '{tag_name}'" in up)
            metrics[f"{tkey}_order_seen"] = int(f"SET ORDER: CDX TAG '{tag_name}'" in up or f"TAG '{tag_name}'  MODE LMDB" in up)
    return metrics

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2T full candidate-only CDX/LMDB rebuild script generator and optional closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2T-full-candidate-cdx-lmdb-rebuild-v0")
    ap.add_argument("--write-runtime-scripts", action="store_true")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_full_candidate_cdx_lmdb_rebuild"
    gen.mkdir(parents=True, exist_ok=True)

    pre = []
    blockers = 0
    for lane, (rel, expected_list) in REQUIRED.items():
        path = repo / rel
        data = read_json(path)
        observed = data.get("status", "MISSING")
        passed = int(observed in expected_list)
        blockers += 0 if passed else 1
        pre.append({"lane": lane, "manifest_path": str(path), "observed_status": observed, "expected_status": "|".join(expected_list), "pass": passed})
    wc(gen / "dd096zd2t_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    zb = read_json(repo / "docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json")
    candidate_root = Path(zb.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(zb.get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    table_rows = []
    missing_tables = 0
    for table, expected, tags in TABLES:
        p = candidate_dbf / f"{table}.dbf"
        exists = int(p.exists())
        missing_tables += 0 if exists else 1
        table_rows.append({
            "table": table,
            "expected_records": expected,
            "candidate_dbf": str(p),
            "exists": exists,
            "tag_count": len(tags),
            "tags": ";".join(t for t, _ in tags),
        })
    wc(gen / "dd096zd2t_table_rebuild_plan.csv", table_rows, ["table","expected_records","candidate_dbf","exists","tag_count","tags"])

    tag_rows = []
    for table, expected, tags in TABLES:
        for tag_name, expr in tags:
            tag_rows.append({
                "table": table,
                "expected_records": expected,
                "tag_name": tag_name,
                "expression": expr,
                "command": f"CDX ADDTAG {tag_name}",
                "actual_struct_field_required": 1,
            })
    wc(gen / "dd096zd2t_tag_command_plan.csv", tag_rows, ["table","expected_records","tag_name","expression","command","actual_struct_field_required"])

    rebuild_dts = make_rebuild_dts(candidate_dbf, candidate_index, candidate_lmdb)
    verify_dts = make_verify_dts(candidate_dbf, candidate_index, candidate_lmdb)
    wt(gen / "DD096ZD2T_FULL_CANDIDATE_CDX_LMDB_REBUILD.dts", rebuild_dts)
    wt(gen / "DD096ZD2T_FULL_CANDIDATE_CDX_LMDB_VERIFY.dts", verify_dts)

    scripts_written = 0
    if args.write_runtime_scripts:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2T_FULL_CANDIDATE_CDX_LMDB_REBUILD.dts", rebuild_dts)
        wt(repo / "dottalkpp/data/scripts/DD096ZD2T_FULL_CANDIDATE_CDX_LMDB_VERIFY.dts", verify_dts)
        scripts_written = 1

    metrics: Dict[str, int] = {}
    proof_supplied = 0
    if args.runtime_proof:
        p = Path(args.runtime_proof)
        if not p.is_absolute():
            p = repo / p
        text = read_text(p)
        metrics = scan_runtime(text)
        proof_supplied = metrics.get("proof_supplied", 0)
    else:
        metrics = scan_runtime("")

    wc(gen / "dd096zd2t_runtime_proof_scan.csv",
       [{"metric": k, "value": v} for k, v in sorted(metrics.items())],
       ["metric","value"])

    expected_tags = sum(len(tags) for _, _, tags in TABLES)
    expected_builds = len(TABLES)
    expected_lmdb_order_lists = expected_tags

    proof_failures = 0
    if proof_supplied:
        checks = [
            ("candidate_path_seen", 1),
            ("active_datadict_seen", 0),
            ("buildlmdb_failed_count", 0),
        ]
        for k, expect in checks:
            if int(metrics.get(k, 0)) != expect:
                proof_failures += 1
        if int(metrics.get("buildlmdb_ok_count", 0)) < expected_builds:
            proof_failures += 1
        if int(metrics.get("cdx_create_count", 0)) < expected_builds:
            proof_failures += 1
        if int(metrics.get("cdx_addtag_count", 0)) < expected_tags:
            proof_failures += 1
        if int(metrics.get("lmdb_mode_count", 0)) < expected_lmdb_order_lists:
            proof_failures += 1

    boundary = [
        ("full_candidate_cdx_lmdb_rebuild_script_package", 1, 1, 1),
        ("runtime_scripts_written", scripts_written, int(args.write_runtime_scripts), int(scripts_written == int(args.write_runtime_scripts))),
        ("source_edits", 0, 0, 1),
        ("build_file_edits", 0, 0, 1),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zd2t_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    gate_rows = [
        {"gate": "preconditions_green", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "candidate_tables_present", "expected": 0, "observed": missing_tables, "pass": int(missing_tables == 0)},
        {"gate": "runtime_scripts_written_if_requested", "expected": int(args.write_runtime_scripts), "observed": scripts_written, "pass": int(scripts_written == int(args.write_runtime_scripts))},
        {"gate": "runtime_proof_failures_if_supplied", "expected": 0, "observed": proof_failures, "pass": int((not proof_supplied) or proof_failures == 0)},
        {"gate": "active_replacement_performed_by_generator", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for row in gate_rows if int(row["pass"]) != 1)
    wc(out / "dd096zd2t_gate_ledger.csv", gate_rows, ["gate","expected","observed","pass"])

    if failures:
        status = "DD096ZD2T_FULL_CANDIDATE_CDX_LMDB_REBUILD_REVIEW"
    elif proof_supplied:
        status = "DD096ZD2T_FULL_CANDIDATE_CDX_LMDB_REBUILD_GREEN"
    else:
        status = "DD096ZD2T_FULL_CANDIDATE_CDX_LMDB_REBUILD_READY"

    report = f"""# DD096Z-D2T Full Candidate CDX/LMDB Rebuild

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2T generates the full six-table candidate-only CDX/LMDB rebuild scripts using the D2S-proven pattern.

It targets only the inactive candidate root.

## Summary

- Candidate DBF root: `{candidate_dbf}`
- Candidate INDEXES root: `{candidate_index}`
- Candidate LMDB root: `{candidate_lmdb}`
- Precondition blockers: **{blockers}**
- Missing candidate tables: **{missing_tables}**
- Runtime scripts written: **{scripts_written}**
- Runtime proof supplied: **{proof_supplied}**
- Runtime proof failures: **{proof_failures}**
- Expected candidate CDX CREATE count: **{expected_builds}**
- Expected CDX ADDTAG count: **{expected_tags}**
- Active catalog replacement: **0**
- Active CDX/LMDB rebuild: **0**

## Generated runtime scripts

- `DD096ZD2T_FULL_CANDIDATE_CDX_LMDB_REBUILD`
- `DD096ZD2T_FULL_CANDIDATE_CDX_LMDB_VERIFY`

## Caution

This script uses actual intended STRUCT field names. If any field name is not found at runtime, stop and report; do not substitute aliases.

## Next lane

After runtime proof is green, run DD096Z-D2TQ closure or use this same tool with `--runtime-proof` to mark D2T green.
"""
    wt(out / "DD096ZD2T_FULL_CANDIDATE_CDX_LMDB_REBUILD_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2t_full_candidate_cdx_lmdb_rebuild_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "candidate_dbf_root": str(candidate_dbf),
        "candidate_index_root": str(candidate_index),
        "candidate_lmdb_root": str(candidate_lmdb),
        "precondition_blockers": blockers,
        "missing_candidate_tables": missing_tables,
        "runtime_scripts_written": scripts_written,
        "runtime_proof_supplied": proof_supplied,
        "runtime_proof_failures": proof_failures,
        "expected_buildlmdb_ok_count": expected_builds,
        "expected_cdx_addtag_count": expected_tags,
        "active_catalog_replacement": 0,
        "active_cdx_lmdb_rebuild": 0,
        "source_edits": 0,
        "failures": failures,
        "next_recommended_action": "Run full candidate-only rebuild and verify scripts; save transcript and rerun with --runtime-proof.",
    }
    wj(out / "dd096zd2t_full_candidate_cdx_lmdb_rebuild_manifest.json", manifest)

    print(f"DD096Z-D2T full candidate CDX/LMDB rebuild manifest: {out / 'dd096zd2t_full_candidate_cdx_lmdb_rebuild_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; missing_candidate_tables: {missing_tables}; runtime_scripts_written: {scripts_written}; proof_supplied: {proof_supplied}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
