#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List

REQUIRED = {
    "DD096ZB": (
        "docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json",
        ["DD096ZB_BACKUP_CANDIDATE_STAGING_EXECUTED"],
    ),
    "DD096ZC": (
        "docs/datadict/reports/DD096ZC-candidate-root-readback-validation-v0/dd096zc_candidate_root_readback_validation_manifest.json",
        ["DD096ZC_CANDIDATE_ROOT_READBACK_READY", "DD096ZC_CANDIDATE_ROOT_READBACK_GREEN"],
    ),
    "DD096ZD": (
        "docs/datadict/reports/DD096ZD-candidate-cdx-lmdb-rebuild-planning-v0/dd096zd_candidate_cdx_lmdb_rebuild_planning_manifest.json",
        ["DD096ZD_CANDIDATE_CDX_LMDB_REBUILD_PLAN_READY"],
    ),
    "DD096ZE": (
        "docs/datadict/reports/DD096ZE-ddict-resolver-alias-bridge-planning-v0/dd096ze_ddict_resolver_alias_bridge_planning_manifest.json",
        ["DD096ZE_DDICT_RESOLVER_ALIAS_BRIDGE_PLAN_READY"],
    ),
    "DD096ZF2": (
        "docs/datadict/reports/DD096ZF2-guarded-resolver-source-patch-proposal-v0/dd096zf2_guarded_resolver_source_patch_proposal_manifest.json",
        ["DD096ZF2_GUARDED_RESOLVER_SOURCE_PATCH_PROPOSAL_READY"],
    ),
}

TABLES = [
    ("DATA_DICTIONARY_OBJECTS", 10, "CATALOG_OBJECT_ID"),
    ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", 127, "CATALOG_ATTRIBUTE_ID"),
    ("DATA_DICTIONARY_RELATION_EDGES", 16, "RELATION_EDGE_ID"),
    ("DATA_DICTIONARY_EVIDENCE_RECORDS", 7, "EVIDENCE_RECORD_ID"),
    ("DATA_DICTIONARY_GATE_RECORDS", 3, "GATE_RECORD_ID"),
    ("DATA_DICTIONARY_RUNS", 2, "RUN_RECORD_ID"),
]

FUTURE_DDICT_SMOKES = [
    ("DDICT STATUS", "Reports current resolver mode/root and read-only status"),
    ("DDICT TABLES", "Shows legacy DD* and/or DATA_DICTIONARY_* tables based on resolver mode"),
    ("DDICT FIELDS DDOBJECT", "Legacy alias resolves to objects family"),
    ("DDICT FIELDS DATA_DICTIONARY_OBJECTS", "x64 name resolves to objects family"),
    ("DDICT TAGS DATA_DICTIONARY_OBJECTS", "Reports candidate tag policy and physical availability honestly"),
    ("DDICT REL DDICT BOTH", "Relations resolve through relation family bridge"),
    ("DDICT EVIDENCE DDICT", "Evidence resolves through evidence family bridge"),
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

def make_candidate_raw_readback_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-G candidate raw readback smoke harness")
    lines.append("* This targets the inactive candidate root, not the active Data Dictionary catalog.")
    lines.append("* No active catalog replacement. No source edits. No index/LMDB rebuild.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("CLOSE ALL")
    lines.append("")
    for table, expected, key in TABLES:
        lines.append(f"* ---- {table}; expected records {expected}; key {key} ----")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("TOP")
        lines.append("LIST")
        lines.append("CLOSE ALL")
        lines.append("")
    lines.append("* DD096Z-G raw candidate smoke complete.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def make_future_ddict_smoke_dts() -> str:
    lines = []
    lines.append("* DD096Z-G future DDICT resolver bridge smoke contract")
    lines.append("* REVIEW ONLY. These commands require resolver mode support before they are expected to pass.")
    lines.append("* Desired future mode setup examples:")
    lines.append("*   DDICT MODE LEGACY_ACTIVE")
    lines.append("*   DDICT MODE X64_CANDIDATE")
    lines.append("*   DDICT MODE DUAL_BRIDGE")
    lines.append("")
    for smoke, expect in FUTURE_DDICT_SMOKES:
        lines.append(f"* expected: {expect}")
        lines.append(f"* {smoke}")
        lines.append("")
    return "\n".join(lines) + "\n\n"

def main():
    ap = argparse.ArgumentParser(description="DD096Z-G candidate smoke harness design")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZG-candidate-smoke-harness-design-v0")
    ap.add_argument("--write-smoke-drafts", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_candidate_smoke_harness_design"
    gen.mkdir(parents=True, exist_ok=True)

    manifests = {}
    pre = []
    blockers = 0
    for lane, (rel, expected_list) in REQUIRED.items():
        path = repo / rel
        data = read_json(path)
        manifests[lane] = data
        observed = data.get("status", "MISSING")
        passed = int(observed in expected_list)
        blockers += 0 if passed else 1
        pre.append({
            "lane": lane,
            "manifest_path": str(path),
            "observed_status": observed,
            "expected_status": "|".join(expected_list),
            "pass": passed,
        })
    wc(gen / "dd096zg_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    zb = manifests.get("DD096ZB", {})
    candidate_root = Path(zb.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(zb.get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    table_rows = []
    missing_tables = 0
    for table, expected, key in TABLES:
        dbf = candidate_dbf / f"{table}.dbf"
        exists = int(dbf.exists())
        missing_tables += 0 if exists else 1
        table_rows.append({
            "table": table,
            "candidate_dbf": str(dbf),
            "exists": exists,
            "expected_records": expected,
            "primary_key": key,
            "raw_readback_smoke": "USE/AREA/STRUCT/TOP/LIST",
            "ddict_bridge_smoke": "future resolver mode required",
        })
    wc(gen / "dd096zg_candidate_raw_smoke_matrix.csv", table_rows,
       ["table","candidate_dbf","exists","expected_records","primary_key","raw_readback_smoke","ddict_bridge_smoke"])

    ddict_rows = [
        {"surface": surf, "expected_behavior": expect, "requires_source_patch": 1, "implemented_in_this_package": 0}
        for surf, expect in FUTURE_DDICT_SMOKES
    ]
    wc(gen / "dd096zg_future_ddict_bridge_smoke_matrix.csv", ddict_rows,
       ["surface","expected_behavior","requires_source_patch","implemented_in_this_package"])

    harness_plan = [
        ("ZG-01", "Raw candidate root readback smoke", "available_now", "Confirms candidate DBFs can be opened from candidate paths."),
        ("ZG-02", "Candidate header/count parser check", "already_covered_by_DD096ZC", "Header counts already green before runtime proof."),
        ("ZG-03", "Candidate index/LMDB smoke", "deferred_to_DD096ZD2", "Requires candidate-only rebuild execution."),
        ("ZG-04", "DDICT legacy_active smoke", "future_after_resolver_patch", "Must preserve current active behavior."),
        ("ZG-05", "DDICT x64_candidate smoke", "future_after_resolver_patch", "Must read candidate root without active replacement."),
        ("ZG-06", "DDICT dual_bridge smoke", "future_after_resolver_patch", "Must resolve DDOBJECT and DATA_DICTIONARY_OBJECTS as aliases."),
        ("ZG-07", "Post-smoke closeout", "future", "Manifest and transcript capture."),
    ]
    wc(gen / "dd096zg_harness_phase_plan.csv",
       [{"phase_id": a, "phase": b, "status": c, "purpose": d} for a,b,c,d in harness_plan],
       ["phase_id","phase","status","purpose"])

    raw_dts = make_candidate_raw_readback_dts(candidate_dbf, candidate_index, candidate_lmdb)
    future_dts = make_future_ddict_smoke_dts()
    wt(gen / "DD096ZG_CANDIDATE_RAW_READBACK_SMOKE.dts", raw_dts)
    wt(gen / "DD096ZG_FUTURE_DDICT_BRIDGE_SMOKE_CONTRACT.dts", future_dts)

    smoke_written = 0
    if args.write_smoke_drafts:
        wt(repo / "dottalkpp/data/scripts/DD096ZG_CANDIDATE_RAW_READBACK_SMOKE.dts", raw_dts)
        wt(repo / "dottalkpp/data/scripts/DD096ZG_FUTURE_DDICT_BRIDGE_SMOKE_CONTRACT.dts", future_dts)
        smoke_written = 1

    boundary = [
        ("candidate_smoke_harness_design_only", 1, 1, 1),
        ("source_edits", 0, 0, 1),
        ("build_file_edits", 0, 0, 1),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("candidate_cdx_lmdb_rebuild", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zg_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    gates = [
        {"gate": "preconditions_green", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "candidate_tables_present", "expected": 0, "observed": missing_tables, "pass": int(missing_tables == 0)},
        {"gate": "smoke_drafts_written_if_requested", "expected": int(args.write_smoke_drafts), "observed": smoke_written, "pass": int(smoke_written == int(args.write_smoke_drafts))},
        {"gate": "source_edits_performed", "expected": 0, "observed": 0, "pass": 1},
        {"gate": "active_replacement_performed", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for row in gates if int(row["pass"]) != 1)
    wc(out / "dd096zg_gate_ledger.csv", gates, ["gate","expected","observed","pass"])

    status = "DD096ZG_CANDIDATE_SMOKE_HARNESS_DESIGN_READY" if failures == 0 else "DD096ZG_CANDIDATE_SMOKE_HARNESS_DESIGN_REVIEW"

    report = f"""# DD096Z-G Candidate Smoke Harness Design

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-G designs the smoke harness for the inactive x64 Data Dictionary candidate root.

It does not edit source, rebuild CDX/LMDB, or replace the active catalog.

## Summary

- Precondition blockers: **{blockers}**
- Missing candidate DBFs: **{missing_tables}**
- Smoke drafts written: **{smoke_written}**
- Source edits: **0**
- Candidate CDX/LMDB rebuild: **0**
- Active catalog replacement: **0**

## What can run now

The raw candidate readback smoke can run now because it only uses candidate paths and opens the candidate DATA_DICTIONARY_* tables.

## What cannot be expected yet

The DDICT resolver bridge smoke is a contract draft. It should not be expected to pass until resolver mode/source support is implemented.

## Next lane

Run the raw candidate smoke if desired. Then choose either DD096Z-D2 candidate-only CDX/LMDB rebuild execution or DD096Z-F3 guarded resolver source apply, with explicit authorization.
"""
    wt(out / "DD096ZG_CANDIDATE_SMOKE_HARNESS_DESIGN_REPORT.md", report)

    manifest = {
        "contract": "dd096zg_candidate_smoke_harness_design_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "candidate_root": str(candidate_root),
        "candidate_dbf_root": str(candidate_dbf),
        "precondition_blockers": blockers,
        "missing_candidate_dbfs": missing_tables,
        "smoke_drafts_written": smoke_written,
        "source_edits": 0,
        "candidate_cdx_lmdb_rebuild": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Run raw candidate smoke, then decide between DD096Z-D2 candidate rebuild or DD096Z-F3 guarded resolver source apply.",
    }
    wj(out / "dd096zg_candidate_smoke_harness_design_manifest.json", manifest)

    print(f"DD096Z-G candidate smoke harness design manifest: {out / 'dd096zg_candidate_smoke_harness_design_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; missing_candidate_dbfs: {missing_tables}; smoke_drafts_written: {smoke_written}; source_edits: 0; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
