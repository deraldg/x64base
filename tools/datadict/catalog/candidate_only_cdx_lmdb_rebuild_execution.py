#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List

REQUIRED = {
    "DD096ZGQ": (
        "docs/datadict/reports/DD096ZGQ-candidate-raw-smoke-closure-v0/dd096zgq_candidate_raw_smoke_closure_manifest.json",
        ["DD096ZGQ_CANDIDATE_RAW_SMOKE_CLOSURE_GREEN"],
    ),
    "DD096ZD": (
        "docs/datadict/reports/DD096ZD-candidate-cdx-lmdb-rebuild-planning-v0/dd096zd_candidate_cdx_lmdb_rebuild_planning_manifest.json",
        ["DD096ZD_CANDIDATE_CDX_LMDB_REBUILD_PLAN_READY"],
    ),
}

TABLE_TAGS = [
    ("DATA_DICTIONARY_OBJECTS", "CATALOG_OBJECT_ID", "CATALOG_OBJECT_ID", "Primary object id lookup"),
    ("DATA_DICTIONARY_OBJECTS", "CATALOG_OBJECT_NAME", "CATALOG_OBJECT_NAME", "Object name/surface lookup"),
    ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", "CATALOG_OBJECT_ID", "CATALOG_OBJECT_ID", "Attribute owner lookup"),
    ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", "CATALOG_ATTRIBUTE_NAME", "CATALOG_ATTRIBUTE_NAME", "Attribute-name lookup"),
    ("DATA_DICTIONARY_RELATION_EDGES", "RELATION_FROM_OBJECT_ID", "RELATION_FROM_OBJECT_ID", "Outbound relation lookup"),
    ("DATA_DICTIONARY_RELATION_EDGES", "RELATION_TO_OBJECT_ID", "RELATION_TO_OBJECT_ID", "Inbound relation lookup"),
    ("DATA_DICTIONARY_EVIDENCE_RECORDS", "CATALOG_OBJECT_ID", "CATALOG_OBJECT_ID", "Evidence by catalog object"),
    ("DATA_DICTIONARY_GATE_RECORDS", "GATE_RECORD_ID", "GATE_RECORD_ID", "Gate id lookup"),
    ("DATA_DICTIONARY_RUNS", "RUN_RECORD_ID", "RUN_RECORD_ID", "Run id lookup"),
]

TABLES = [
    "DATA_DICTIONARY_OBJECTS",
    "DATA_DICTIONARY_OBJECT_ATTRIBUTES",
    "DATA_DICTIONARY_RELATION_EDGES",
    "DATA_DICTIONARY_EVIDENCE_RECORDS",
    "DATA_DICTIONARY_GATE_RECORDS",
    "DATA_DICTIONARY_RUNS",
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

def make_candidate_rebuild_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2 candidate-only CDX/LMDB rebuild execution script")
    lines.append("* Candidate paths only. Does not target active dottalkpp/data/datadict roots.")
    lines.append("* Review command syntax in current runtime before treating CDX commands as final.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("CLOSE ALL")
    lines.append("")
    for table in TABLES:
        lines.append(f"* ---------- candidate table: {table} ----------")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("STRUCT")
        table_tags = [r for r in TABLE_TAGS if r[0] == table]
        for _, tag_name, expr, purpose in table_tags:
            # Keep CDX commands as review comments because exact current syntax has varied.
            lines.append(f"* CDX ADDTAG candidate: {tag_name} ON {expr}  && {purpose}")
            lines.append(f"* INDEX ON {expr} TAG {tag_name}")
        lines.append("BUILDLMDB CLEAN YES")
        lines.append("AREA")
        lines.append("CLOSE ALL")
        lines.append("")
    lines.append("* DD096Z-D2 candidate-only rebuild script complete.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def make_verification_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2 candidate-only CDX/LMDB rebuild verification script")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("CLOSE ALL")
    lines.append("")
    for table in TABLES:
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("LIST")
        lines.append("CLOSE ALL")
        lines.append("")
    return "\n".join(lines) + "\n\n"

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2 candidate-only CDX/LMDB rebuild execution package")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2-candidate-only-cdx-lmdb-rebuild-execution-v0")
    ap.add_argument("--write-runtime-scripts", action="store_true")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_candidate_only_cdx_lmdb_rebuild_execution"
    gen.mkdir(parents=True, exist_ok=True)

    pre = []
    blockers = 0
    manifests = {}
    for lane, (rel, expected) in REQUIRED.items():
        path = repo / rel
        data = read_json(path)
        manifests[lane] = data
        observed = data.get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre.append({
            "lane": lane,
            "manifest_path": str(path),
            "observed_status": observed,
            "expected_status": "|".join(expected),
            "pass": passed,
        })
    wc(gen / "dd096zd2_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    # Candidate root comes from DD096ZGQ if present, otherwise from DD096ZB manifest.
    zb = read_json(repo / "docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json")
    candidate_root = Path(zb.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(zb.get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    target_rows = [
        {"root": "candidate_dbf", "path": str(candidate_dbf), "exists": int(candidate_dbf.exists()), "candidate_only": 1},
        {"root": "candidate_indexes", "path": str(candidate_index), "exists": int(candidate_index.exists()), "candidate_only": 1},
        {"root": "candidate_lmdb", "path": str(candidate_lmdb), "exists": int(candidate_lmdb.exists()), "candidate_only": 1},
        {"root": "active_datadict", "path": str(repo / "dottalkpp/data/datadict"), "exists": int((repo / "dottalkpp/data/datadict").exists()), "candidate_only": 0},
        {"root": "active_indexes", "path": str(repo / "dottalkpp/data/indexes/datadict"), "exists": int((repo / "dottalkpp/data/indexes/datadict").exists()), "candidate_only": 0},
        {"root": "active_lmdb", "path": str(repo / "dottalkpp/data/lmdb/datadict"), "exists": int((repo / "dottalkpp/data/lmdb/datadict").exists()), "candidate_only": 0},
    ]
    wc(gen / "dd096zd2_target_root_ledger.csv", target_rows, ["root","path","exists","candidate_only"])

    table_rows = []
    missing_tables = 0
    for table in TABLES:
        path = candidate_dbf / f"{table}.dbf"
        exists = int(path.exists())
        missing_tables += 0 if exists else 1
        table_rows.append({
            "table": table,
            "candidate_dbf": str(path),
            "exists": exists,
            "buildlmdb_planned": 1,
            "cdx_tag_count_planned": sum(1 for t in TABLE_TAGS if t[0] == table),
        })
    wc(gen / "dd096zd2_candidate_table_execution_plan.csv", table_rows, ["table","candidate_dbf","exists","buildlmdb_planned","cdx_tag_count_planned"])

    wc(gen / "dd096zd2_candidate_tag_execution_plan.csv",
       [{"table": a, "tag_name": b, "expression": c, "purpose": d, "cdx_command_review_required": 1} for a,b,c,d in TABLE_TAGS],
       ["table","tag_name","expression","purpose","cdx_command_review_required"])

    rebuild_dts = make_candidate_rebuild_dts(candidate_dbf, candidate_index, candidate_lmdb)
    verify_dts = make_verification_dts(candidate_dbf, candidate_index, candidate_lmdb)
    wt(gen / "DD096ZD2_CANDIDATE_ONLY_CDX_LMDB_REBUILD.dts", rebuild_dts)
    wt(gen / "DD096ZD2_CANDIDATE_ONLY_REBUILD_VERIFY.dts", verify_dts)

    runtime_scripts_written = 0
    if args.write_runtime_scripts:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2_CANDIDATE_ONLY_CDX_LMDB_REBUILD.dts", rebuild_dts)
        wt(repo / "dottalkpp/data/scripts/DD096ZD2_CANDIDATE_ONLY_REBUILD_VERIFY.dts", verify_dts)
        runtime_scripts_written = 1

    proof_supplied = 0
    proof_text = ""
    if args.runtime_proof:
        p = Path(args.runtime_proof)
        if not p.is_absolute():
            p = repo / p
        proof_text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        proof_supplied = int(bool(proof_text))

    proof_rows = []
    if proof_supplied:
        up = proof_text.upper()
        for table in TABLES:
            proof_rows.append({
                "table": table,
                "table_seen": int(table in up),
                "buildlmdb_seen": int("BUILDLMDB" in up),
                "candidate_path_seen": int("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up),
                "active_datadict_seen": int("DOTTALKPP\\DATA\\DATADICT" in up or "DOTTALKPP/DATA/DATADICT" in up),
            })
    else:
        for table in TABLES:
            proof_rows.append({
                "table": table,
                "table_seen": 0,
                "buildlmdb_seen": 0,
                "candidate_path_seen": 0,
                "active_datadict_seen": 0,
            })
    wc(gen / "dd096zd2_runtime_proof_scan.csv", proof_rows, ["table","table_seen","buildlmdb_seen","candidate_path_seen","active_datadict_seen"])

    proof_failures = 0
    if proof_supplied:
        proof_failures += sum(1 for r in proof_rows if int(r["table_seen"]) != 1)
        proof_failures += sum(1 for r in proof_rows if int(r["candidate_path_seen"]) != 1)
        proof_failures += sum(1 for r in proof_rows if int(r["active_datadict_seen"]) != 0)

    boundary = [
        ("candidate_only_cdx_lmdb_rebuild_execution_package", 1, 1, 1),
        ("runtime_scripts_written", runtime_scripts_written, int(args.write_runtime_scripts), int(runtime_scripts_written == int(args.write_runtime_scripts))),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("source_edits", 0, 0, 1),
        ("build_file_edits", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zd2_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    gates = [
        {"gate": "preconditions_green", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "candidate_tables_present", "expected": 0, "observed": missing_tables, "pass": int(missing_tables == 0)},
        {"gate": "runtime_scripts_written_if_requested", "expected": int(args.write_runtime_scripts), "observed": runtime_scripts_written, "pass": int(runtime_scripts_written == int(args.write_runtime_scripts))},
        {"gate": "runtime_proof_failures_if_supplied", "expected": 0, "observed": proof_failures, "pass": int((not proof_supplied) or proof_failures == 0)},
        {"gate": "active_rebuild_performed_by_generator", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for g in gates if int(g["pass"]) != 1)
    wc(out / "dd096zd2_gate_ledger.csv", gates, ["gate","expected","observed","pass"])

    if failures:
        status = "DD096ZD2_CANDIDATE_ONLY_CDX_LMDB_REBUILD_EXECUTION_REVIEW"
    elif proof_supplied:
        status = "DD096ZD2_CANDIDATE_ONLY_CDX_LMDB_REBUILD_EXECUTION_GREEN"
    else:
        status = "DD096ZD2_CANDIDATE_ONLY_CDX_LMDB_REBUILD_EXECUTION_READY"

    report = f"""# DD096Z-D2 Candidate-Only CDX/LMDB Rebuild Execution Package

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2 prepares candidate-only CDX/LMDB rebuild runtime scripts for the inactive x64 Data Dictionary candidate.

The generator itself does not rebuild indexes or LMDB. It writes runtime scripts that target candidate paths only.

## Summary

- Candidate DBF root: `{candidate_dbf}`
- Candidate INDEXES root: `{candidate_index}`
- Candidate LMDB root: `{candidate_lmdb}`
- Preconditions blockers: **{blockers}**
- Missing candidate tables: **{missing_tables}**
- Runtime scripts written: **{runtime_scripts_written}**
- Runtime proof supplied: **{proof_supplied}**
- Runtime proof failures: **{proof_failures}**
- Active catalog replacement: **0**
- Active CDX/LMDB rebuild: **0**

## Runtime scripts

- `DD096ZD2_CANDIDATE_ONLY_CDX_LMDB_REBUILD`
- `DD096ZD2_CANDIDATE_ONLY_REBUILD_VERIFY`

The CDX tag commands are emitted as review comments because current CDX command syntax should be confirmed before execution. `BUILDLMDB CLEAN YES` is active in the generated runtime script and is candidate-path scoped.

## Next lane

After candidate-only rebuild runtime proof is green, close it with DD096Z-D2Q and then proceed to DDICT resolver source apply planning only if explicitly authorized.
"""
    wt(out / "DD096ZD2_CANDIDATE_ONLY_CDX_LMDB_REBUILD_EXECUTION_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2_candidate_only_cdx_lmdb_rebuild_execution_v0",
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
        "runtime_scripts_written": runtime_scripts_written,
        "runtime_proof_supplied": proof_supplied,
        "runtime_proof_failures": proof_failures,
        "active_catalog_replacement": 0,
        "active_cdx_lmdb_rebuild": 0,
        "source_edits": 0,
        "failures": failures,
        "next_recommended_action": "Run candidate-only rebuild script, then DD096Z-D2Q closure; no active replacement.",
    }
    wj(out / "dd096zd2_candidate_only_cdx_lmdb_rebuild_execution_manifest.json", manifest)

    print(f"DD096Z-D2 candidate-only CDX/LMDB rebuild execution manifest: {out / 'dd096zd2_candidate_only_cdx_lmdb_rebuild_execution_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; missing_candidate_tables: {missing_tables}; runtime_scripts_written: {runtime_scripts_written}; proof_supplied: {proof_supplied}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
