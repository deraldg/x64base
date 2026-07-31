#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List

EXPECTED_TABLES = [
    "DATA_DICTIONARY_OBJECTS",
    "DATA_DICTIONARY_OBJECT_ATTRIBUTES",
    "DATA_DICTIONARY_RELATION_EDGES",
    "DATA_DICTIONARY_EVIDENCE_RECORDS",
    "DATA_DICTIONARY_GATE_RECORDS",
    "DATA_DICTIONARY_RUNS",
]

REQUIRED_STATUS = {
    "DD096ZB": ("docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json", "DD096ZB_BACKUP_CANDIDATE_STAGING_EXECUTED"),
    "DD096ZC": ("docs/datadict/reports/DD096ZC-candidate-root-readback-validation-v0/dd096zc_candidate_root_readback_validation_manifest.json", ["DD096ZC_CANDIDATE_ROOT_READBACK_READY", "DD096ZC_CANDIDATE_ROOT_READBACK_GREEN"]),
}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

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

def make_rebuild_plan_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D candidate CDX/LMDB rebuild planning script")
    lines.append("* REVIEW SCRIPT ONLY: do not run until candidate-root readback is accepted.")
    lines.append("* This targets the inactive candidate root, not the active Data Dictionary catalog.")
    lines.append("* It uses candidate paths only.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("CLOSE ALL")
    lines.append("")
    for table in EXPECTED_TABLES:
        lines.append(f"* -------- candidate index/mirror review for {table} --------")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("* BUILDLMDB CLEAN YES")
        lines.append("* CDX/tag rebuild policy is still pending explicit tag manifest.")
        lines.append("CLOSE ALL")
        lines.append("")
    lines.append("* DD096Z-D review script done.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D candidate CDX/LMDB rebuild planning")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD-candidate-cdx-lmdb-rebuild-planning-v0")
    ap.add_argument("--write-review-script", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_candidate_cdx_lmdb_rebuild_plan"
    gen.mkdir(parents=True, exist_ok=True)

    pre = []
    blockers = 0
    zb_manifest_data = {}
    zc_manifest_data = {}
    for lane, pair in REQUIRED_STATUS.items():
        rel, expected = pair
        path = repo / rel
        data = read_json(path)
        if lane == "DD096ZB":
            zb_manifest_data = data
        if lane == "DD096ZC":
            zc_manifest_data = data
        observed = data.get("status", "MISSING")
        if isinstance(expected, list):
            passed = int(observed in expected)
            expected_text = "|".join(expected)
        else:
            passed = int(observed == expected)
            expected_text = expected
        blockers += 0 if passed else 1
        pre.append({
            "lane": lane,
            "manifest_path": str(path),
            "observed_status": observed,
            "expected_status": expected_text,
            "pass": passed,
        })
    wc(gen / "dd096zd_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    candidate_root = Path(zb_manifest_data.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(zb_manifest_data.get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    target_rows = [
        {"root_family": "candidate_root", "path": str(candidate_root), "exists": int(candidate_root.exists()), "write_allowed_in_this_package": 0},
        {"root_family": "candidate_dbf", "path": str(candidate_dbf), "exists": int(candidate_dbf.exists()), "write_allowed_in_this_package": 0},
        {"root_family": "candidate_indexes", "path": str(candidate_index), "exists": int(candidate_index.exists()), "write_allowed_in_this_package": 0},
        {"root_family": "candidate_lmdb", "path": str(candidate_lmdb), "exists": int(candidate_lmdb.exists()), "write_allowed_in_this_package": 0},
        {"root_family": "active_indexes", "path": str(repo / "dottalkpp/data/indexes/datadict"), "exists": int((repo / "dottalkpp/data/indexes/datadict").exists()), "write_allowed_in_this_package": 0},
        {"root_family": "active_lmdb", "path": str(repo / "dottalkpp/data/lmdb/datadict"), "exists": int((repo / "dottalkpp/data/lmdb/datadict").exists()), "write_allowed_in_this_package": 0},
    ]
    wc(gen / "dd096zd_target_root_ledger.csv", target_rows, ["root_family","path","exists","write_allowed_in_this_package"])

    table_rows = []
    missing_dbf = 0
    for table in EXPECTED_TABLES:
        dbf_path = candidate_dbf / f"{table}.dbf"
        exists = int(dbf_path.exists())
        missing_dbf += 0 if exists else 1
        table_rows.append({
            "table": table,
            "candidate_dbf_path": str(dbf_path),
            "candidate_dbf_exists": exists,
            "candidate_cdx_path": str(candidate_index / f"{table.lower()}.cdx"),
            "candidate_lmdb_hint": str(candidate_lmdb / f"{table}.cdx.d"),
            "rebuild_execution_in_this_package": 0,
            "notes": "Plan only. Actual CDX/LMDB rebuild requires DD096Z-D execution package or explicit operator command.",
        })
    wc(gen / "dd096zd_table_rebuild_plan.csv", table_rows, ["table","candidate_dbf_path","candidate_dbf_exists","candidate_cdx_path","candidate_lmdb_hint","rebuild_execution_in_this_package","notes"])

    tag_manifest = [
        ("DATA_DICTIONARY_OBJECTS", "CATALOG_OBJECT_ID", "Primary object id lookup", "required_candidate_tag"),
        ("DATA_DICTIONARY_OBJECTS", "CATALOG_OBJECT_NAME", "Object name/surface lookup", "required_candidate_tag"),
        ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", "CATALOG_OBJECT_ID", "Attribute owner lookup", "required_candidate_tag"),
        ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", "CATALOG_ATTRIBUTE_NAME", "Attribute-name lookup", "required_candidate_tag"),
        ("DATA_DICTIONARY_RELATION_EDGES", "RELATION_FROM_OBJECT_ID", "Outbound relation lookup", "required_candidate_tag"),
        ("DATA_DICTIONARY_RELATION_EDGES", "RELATION_TO_OBJECT_ID", "Inbound relation lookup", "required_candidate_tag"),
        ("DATA_DICTIONARY_EVIDENCE_RECORDS", "CATALOG_OBJECT_ID", "Evidence by catalog object", "required_candidate_tag"),
        ("DATA_DICTIONARY_GATE_RECORDS", "GATE_RECORD_ID", "Gate id lookup", "candidate_tag"),
        ("DATA_DICTIONARY_RUNS", "RUN_RECORD_ID", "Run id lookup", "candidate_tag"),
    ]
    wc(gen / "dd096zd_candidate_tag_manifest_plan.csv",
       [{"table": a, "tag_expression_or_field": b, "purpose": c, "priority": d} for a,b,c,d in tag_manifest],
       ["table","tag_expression_or_field","purpose","priority"])

    dts_text = make_rebuild_plan_dts(candidate_dbf, candidate_index, candidate_lmdb)
    preview = gen / "DD096ZD_CANDIDATE_CDX_LMDB_REBUILD_REVIEW.dts"
    wt(preview, dts_text)

    review_script_written = 0
    runtime_path = repo / "dottalkpp/data/scripts/DD096ZD_CANDIDATE_CDX_LMDB_REBUILD_REVIEW.dts"
    if args.write_review_script:
        wt(runtime_path, dts_text)
        review_script_written = 1

    risk_rows = [
        {"risk_id": "ZD-RISK-001", "risk": "DDICT may not yet resolve long DATA_DICTIONARY_* table names from candidate root.", "mitigation": "Keep DDICT resolver/alias bridge as a separate gate before active switch."},
        {"risk_id": "ZD-RISK-002", "risk": "Rebuilding CDX/LMDB before tag policy is reviewed may create misleading readiness.", "mitigation": "Use candidate tag manifest plan before execution."},
        {"risk_id": "ZD-RISK-003", "risk": "Active indexes/LMDB could be accidentally rebuilt if paths are wrong.", "mitigation": "Candidate paths are explicit; active writes are boundary-failed in this package."},
        {"risk_id": "ZD-RISK-004", "risk": "BUILDLMDB/CDX command syntax may need runtime-specific adjustment.", "mitigation": "Review script comments commands; execution is later after syntax confirmation."},
    ]
    wc(gen / "dd096zd_risk_register.csv", risk_rows, ["risk_id","risk","mitigation"])

    boundary = [
        ("candidate_cdx_lmdb_rebuild_planning_only", 1, 1, 1),
        ("candidate_cdx_lmdb_rebuild_executed", 0, 0, 1),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("source_edits", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zd_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    gate_rows = [
        {"gate": "preconditions_accepted", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "candidate_dbfs_present", "expected": 0, "observed": missing_dbf, "pass": int(missing_dbf == 0)},
        {"gate": "review_script_written_if_requested", "expected": int(args.write_review_script), "observed": review_script_written, "pass": int(review_script_written == int(args.write_review_script))},
        {"gate": "active_rebuild_performed", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for g in gate_rows if int(g["pass"]) != 1)
    wc(out / "dd096zd_gate_ledger.csv", gate_rows, ["gate","expected","observed","pass"])

    status = "DD096ZD_CANDIDATE_CDX_LMDB_REBUILD_PLAN_READY" if failures == 0 else "DD096ZD_CANDIDATE_CDX_LMDB_REBUILD_PLAN_REVIEW"

    report = f"""# DD096Z-D Candidate CDX/LMDB Rebuild Planning

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D plans candidate-root CDX/LMDB rebuild for the inactive x64 Data Dictionary candidate.

It does not execute the rebuild and does not touch the active catalog.

## Summary

- Candidate root: `{candidate_root}`
- Candidate DBF root: `{candidate_dbf}`
- Candidate index root: `{candidate_index}`
- Candidate LMDB root: `{candidate_lmdb}`
- Precondition blockers: **{blockers}**
- Missing candidate DBFs: **{missing_dbf}**
- Review script written: **{review_script_written}**
- Candidate CDX/LMDB rebuild executed: **0**
- Active CDX/LMDB rebuild: **0**
- Active catalog replacement: **0**

## Next lane

DD096Z-D2 or DD096Z-E should either execute candidate-only rebuild after syntax confirmation, or first build the DDICT resolver/alias bridge plan.
"""
    wt(out / "DD096ZD_CANDIDATE_CDX_LMDB_REBUILD_PLANNING_REPORT.md", report)

    manifest = {
        "contract": "dd096zd_candidate_cdx_lmdb_rebuild_planning_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "candidate_root": str(candidate_root),
        "candidate_dbf_root": str(candidate_dbf),
        "candidate_index_root": str(candidate_index),
        "candidate_lmdb_root": str(candidate_lmdb),
        "precondition_blockers": blockers,
        "missing_candidate_dbfs": missing_dbf,
        "review_script_written": review_script_written,
        "candidate_cdx_lmdb_rebuild_executed": 0,
        "active_cdx_lmdb_rebuild": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "DD096Z-D2 candidate-only CDX/LMDB rebuild execution after tag/syntax review, or DD096Z-E DDICT resolver bridge planning.",
    }
    wj(out / "dd096zd_candidate_cdx_lmdb_rebuild_planning_manifest.json", manifest)

    print(f"DD096Z-D candidate CDX/LMDB rebuild plan manifest: {out / 'dd096zd_candidate_cdx_lmdb_rebuild_planning_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; missing_candidate_dbfs: {missing_dbf}; review_script_written: {review_script_written}; candidate_rebuild_executed: 0; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
