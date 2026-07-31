#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Dict, List

CANDIDATE_TABLES = [
    ("DATA_DICTIONARY_OBJECTS", 10, ["CATALOG_OBJECT_ID", "CATALOG_OBJECT_NAME"]),
    ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", 127, ["CATALOG_OBJECT_ID", "CATALOG_ATTRIBUTE_NAME"]),
    ("DATA_DICTIONARY_RELATION_EDGES", 16, ["RELATION_FROM_OBJECT_ID", "RELATION_TO_OBJECT_ID"]),
    ("DATA_DICTIONARY_EVIDENCE_RECORDS", 7, ["CATALOG_OBJECT_ID"]),
    ("DATA_DICTIONARY_GATE_RECORDS", 3, ["GATE_RECORD_ID"]),
    ("DATA_DICTIONARY_RUNS", 2, ["RUN_RECORD_ID"]),
]

LEGACY_ACTIVE_NAMES = ["DDBASE", "DDOBJECT", "DDATTR", "DDEDGE", "DDEVID", "DDGATE", "DDARTIF", "DDSRC"]

REQUIRED = {
    "DD096ZD2S": (
        "docs/datadict/reports/DD096ZD2S-single-table-cdx-lmdb-proof-closure-v0/dd096zd2s_single_table_cdx_lmdb_proof_closure_manifest.json",
        ["DD096ZD2S_SINGLE_TABLE_CDX_LMDB_PROOF_GREEN"],
    ),
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

def make_area_inventory_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2X candidate area identity guard inventory")
    lines.append("* Inventory only. No CDX CREATE, no CDX ADDTAG, no BUILDLMDB.")
    lines.append("* Goal: prove which areas actually contain candidate DATA_DICTIONARY_* tables before using SELECT.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("")
    for area in range(0, 11):
        lines.append(f"SELECT {area}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("")
    lines.append("* End D2X inventory. If areas show active legacy DD* tables, do not use SELECT mapping for candidate rebuild.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def make_candidate_open_probe_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2X candidate open probe")
    lines.append("* Opens candidate tables by name after candidate paths are set.")
    lines.append("* No CDX/LMDB rebuild here; this proves open identity only.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("")
    for table, expected, tags in CANDIDATE_TABLES:
        lines.append(f"* ---- candidate open probe: {table}; expected records {expected} ----")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("SL")
        lines.append("CLOSE")
        lines.append("")
    lines.append("* End D2X candidate open probe.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def scan_runtime(text: str) -> Dict[str, int]:
    up = text.upper()
    metrics: Dict[str, int] = {}
    metrics["proof_supplied"] = int(bool(text))
    metrics["candidate_path_seen"] = int("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up)
    metrics["active_datadict_path_seen"] = int("DOTTALKPP\\DATA\\DATADICT" in up or "DOTTALKPP/DATA/DATADICT" in up)
    metrics["active_legacy_table_seen_count"] = sum(1 for name in LEGACY_ACTIVE_NAMES if f"FILE: {name}" in up or f"FILE: {name} " in up)
    metrics["candidate_table_seen_count"] = sum(1 for table, _, _ in CANDIDATE_TABLES if f"FILE: {table}" in up or table in up)
    metrics["cdx_create_seen"] = int("CDX CREATED:" in up)
    metrics["buildlmdb_seen"] = int("BUILDLMDB" in up)
    metrics["table_cdx_fallback_seen"] = int("\\INDEXES\\TABLE.CDX" in up or "/INDEXES/TABLE.CDX" in up)
    for table, expected, tags in CANDIDATE_TABLES:
        key = table.lower()
        metrics[f"{key}_file_seen"] = int(f"FILE: {table}" in up)
        metrics[f"{key}_candidate_path_seen"] = int(table in up and ("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up))
        metrics[f"{key}_expected_recs_seen"] = int(f"RECS: {expected}" in up or f"RECORD COUNT {expected}" in up)
    for name in LEGACY_ACTIVE_NAMES:
        metrics[f"legacy_{name.lower()}_seen"] = int(f"FILE: {name}" in up)
    return metrics

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2X candidate area identity guard")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2X-candidate-area-identity-guard-v0")
    ap.add_argument("--write-runtime-scripts", action="store_true")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_candidate_area_identity_guard"
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
    wc(gen / "dd096zd2x_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    zb = read_json(repo / "docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json")
    candidate_root = Path(zb.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(zb.get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    table_rows = []
    missing = 0
    for table, expected, tags in CANDIDATE_TABLES:
        p = candidate_dbf / f"{table}.dbf"
        exists = int(p.exists())
        missing += 0 if exists else 1
        table_rows.append({"table": table, "expected_records": expected, "candidate_dbf": str(p), "exists": exists, "tags": ";".join(tags)})
    wc(gen / "dd096zd2x_candidate_table_identity_plan.csv", table_rows, ["table","expected_records","candidate_dbf","exists","tags"])

    policy_rows = [
        {"rule": "Do not SELECT by hardcoded area unless AREA shows the expected DATA_DICTIONARY_* table and candidate path.", "reason": "D2W selected active legacy DD* tables and mixed them with candidate index paths."},
        {"rule": "If table is already open, SELECT the proven area.", "reason": "Correct xBase pattern, but only after identity proof."},
        {"rule": "If table is not already open, USE it from candidate DBF path.", "reason": "Avoid operating on active legacy areas."},
        {"rule": "Never run CDX CREATE/ADDTAG/BUILDLMDB after AREA shows the wrong table.", "reason": "Prevents table.cdx fallback and mixed active/candidate root rebuilds."},
        {"rule": "Use SMARTLIST/SL for generated listing.", "reason": "LIST is developer/manual cursor tooling."},
    ]
    wc(gen / "dd096zd2x_area_identity_policy.csv", policy_rows, ["rule","reason"])

    inventory_dts = make_area_inventory_dts(candidate_dbf, candidate_index, candidate_lmdb)
    open_probe_dts = make_candidate_open_probe_dts(candidate_dbf, candidate_index, candidate_lmdb)
    wt(gen / "DD096ZD2X_CANDIDATE_AREA_IDENTITY_INVENTORY.dts", inventory_dts)
    wt(gen / "DD096ZD2X_CANDIDATE_OPEN_PROBE.dts", open_probe_dts)

    scripts_written = 0
    if args.write_runtime_scripts:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2X_CANDIDATE_AREA_IDENTITY_INVENTORY.dts", inventory_dts)
        wt(repo / "dottalkpp/data/scripts/DD096ZD2X_CANDIDATE_OPEN_PROBE.dts", open_probe_dts)
        scripts_written = 1

    proof_supplied = 0
    metrics = scan_runtime("")
    if args.runtime_proof:
        p = Path(args.runtime_proof)
        if not p.is_absolute():
            p = repo / p
        text = read_text(p)
        metrics = scan_runtime(text)
        proof_supplied = metrics.get("proof_supplied", 0)

    wc(gen / "dd096zd2x_runtime_identity_scan.csv",
       [{"metric": k, "value": v} for k, v in sorted(metrics.items())],
       ["metric","value"])

    proof_failures = 0
    if proof_supplied:
        # This is an identity guard: active legacy tables may be seen, but that means SELECT mapping is unsafe, not tool failure.
        if int(metrics.get("candidate_path_seen", 0)) != 1:
            proof_failures += 1
        if int(metrics.get("cdx_create_seen", 0)) != 0:
            proof_failures += 1
        if int(metrics.get("buildlmdb_seen", 0)) != 0:
            proof_failures += 1
        if int(metrics.get("table_cdx_fallback_seen", 0)) != 0:
            proof_failures += 1

    boundary = [
        ("candidate_area_identity_guard_only", 1, 1, 1),
        ("runtime_scripts_written", scripts_written, int(args.write_runtime_scripts), int(scripts_written == int(args.write_runtime_scripts))),
        ("cdx_create", 0, 0, 1),
        ("buildlmdb", 0, 0, 1),
        ("source_edits", 0, 0, 1),
        ("build_file_edits", 0, 0, 1),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zd2x_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    gates = [
        {"gate": "preconditions_green", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "candidate_tables_present", "expected": 0, "observed": missing, "pass": int(missing == 0)},
        {"gate": "runtime_scripts_written_if_requested", "expected": int(args.write_runtime_scripts), "observed": scripts_written, "pass": int(scripts_written == int(args.write_runtime_scripts))},
        {"gate": "runtime_proof_failures_if_supplied", "expected": 0, "observed": proof_failures, "pass": int((not proof_supplied) or proof_failures == 0)},
        {"gate": "active_replacement_performed_by_generator", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    wc(out / "dd096zd2x_gate_ledger.csv", gates, ["gate","expected","observed","pass"])

    if failures:
        status = "DD096ZD2X_CANDIDATE_AREA_IDENTITY_GUARD_REVIEW"
    elif proof_supplied:
        status = "DD096ZD2X_CANDIDATE_AREA_IDENTITY_GUARD_GREEN"
    else:
        status = "DD096ZD2X_CANDIDATE_AREA_IDENTITY_GUARD_READY"

    report = f"""# DD096Z-D2X Candidate Area Identity Guard

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2X corrects the DD096Z-D2W failure mode.

D2W correctly used `SELECT`, but it selected hardcoded areas that actually contained active legacy `DD*` tables, not inactive candidate `DATA_DICTIONARY_*` tables.

## Summary

- Candidate DBF root: `{candidate_dbf}`
- Candidate INDEXES root: `{candidate_index}`
- Candidate LMDB root: `{candidate_lmdb}`
- Precondition blockers: **{blockers}**
- Missing candidate tables: **{missing}**
- Runtime scripts written: **{scripts_written}**
- Runtime proof supplied: **{proof_supplied}**
- Active legacy table names seen in proof: **{metrics.get('active_legacy_table_seen_count', 0)}**
- Candidate table names seen in proof: **{metrics.get('candidate_table_seen_count', 0)}**
- CDX CREATE run by this package: **0**
- BUILDLMDB run by this package: **0**
- Active catalog replacement: **0**

## Rule

```text
If table is already open:
  SELECT the proven area.

But first:
  AREA must show the expected DATA_DICTIONARY_* table
  and the path must be under docs/datadict/candidates/...
```

## Runtime scripts

- `DD096ZD2X_CANDIDATE_AREA_IDENTITY_INVENTORY`
- `DD096ZD2X_CANDIDATE_OPEN_PROBE`

Both are identity-only scripts. They do not run CDX or LMDB commands.
"""
    wt(out / "DD096ZD2X_CANDIDATE_AREA_IDENTITY_GUARD_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2x_candidate_area_identity_guard_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "candidate_dbf_root": str(candidate_dbf),
        "candidate_index_root": str(candidate_index),
        "candidate_lmdb_root": str(candidate_lmdb),
        "precondition_blockers": blockers,
        "missing_candidate_tables": missing,
        "runtime_scripts_written": scripts_written,
        "runtime_proof_supplied": proof_supplied,
        "active_legacy_table_seen_count": metrics.get("active_legacy_table_seen_count", 0),
        "candidate_table_seen_count": metrics.get("candidate_table_seen_count", 0),
        "cdx_create": 0,
        "buildlmdb": 0,
        "active_catalog_replacement": 0,
        "source_edits": 0,
        "failures": failures,
        "next_recommended_action": "Run candidate area identity inventory and open probe; then generate rebuild only from proven candidate areas or candidate USE opens.",
    }
    wj(out / "dd096zd2x_candidate_area_identity_guard_manifest.json", manifest)

    print(f"DD096Z-D2X candidate area identity guard manifest: {out / 'dd096zd2x_candidate_area_identity_guard_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; missing_candidate_tables: {missing}; runtime_scripts_written: {scripts_written}; proof_supplied: {proof_supplied}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
