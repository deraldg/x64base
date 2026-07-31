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
}

# Observed candidate area mapping from D2T failure transcript.
TABLES: List[Tuple[int, str, int, List[str]]] = [
    (3, "DATA_DICTIONARY_OBJECTS", 10, ["CATALOG_OBJECT_ID", "CATALOG_OBJECT_NAME"]),
    (2, "DATA_DICTIONARY_OBJECT_ATTRIBUTES", 127, ["CATALOG_OBJECT_ID", "CATALOG_ATTRIBUTE_NAME"]),
    (4, "DATA_DICTIONARY_RELATION_EDGES", 16, ["RELATION_FROM_OBJECT_ID", "RELATION_TO_OBJECT_ID"]),
    (0, "DATA_DICTIONARY_EVIDENCE_RECORDS", 7, ["CATALOG_OBJECT_ID"]),
    (1, "DATA_DICTIONARY_GATE_RECORDS", 3, ["GATE_RECORD_ID"]),
    (5, "DATA_DICTIONARY_RUNS", 2, ["RUN_RECORD_ID"]),
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

def make_select_smartlist_rebuild(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2W SELECT-area candidate CDX/LMDB rebuild with SMARTLIST verification")
    lines.append("* Repair policy: if table is already open, SELECT its area instead of USE.")
    lines.append("* Listing policy: use SMARTLIST/SL for generated scripts; LIST is dev/manual cursor tooling.")
    lines.append("* Candidate paths only. No active Data Dictionary root.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("")
    lines.append("* Expected open-area mapping from D2T:")
    for area, table, expected, tags in TABLES:
        lines.append(f"*   Area {area}: {table} ({expected} records)")
    lines.append("")
    for area, table, expected, tags in TABLES:
        lines.append(f"* ---------- SELECT AREA {area}: {table}; expected records {expected} ----------")
        lines.append(f"SELECT {area}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("* If AREA does not show the expected DATA_DICTIONARY_* table, stop and report.")
        lines.append("CDX CREATE")
        for tag in tags:
            lines.append(f"CDX ADDTAG {tag}")
        lines.append("CDX INFO")
        lines.append("BUILDLMDB CLEAN YES")
        for tag in tags:
            lines.append(f"SET ORDER TO TAG {tag}")
            lines.append("TOP")
            lines.append("SL")
        lines.append("")
    lines.append("* DD096Z-D2W SELECT-area SMARTLIST rebuild complete.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def make_select_smartlist_verify(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2W SELECT-area candidate rebuild verification with SMARTLIST")
    lines.append("* Candidate paths only. Uses already-open areas rather than USE.")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("")
    for area, table, expected, tags in TABLES:
        lines.append(f"* ---------- VERIFY AREA {area}: {table}; expected records {expected} ----------")
        lines.append(f"SELECT {area}")
        lines.append("AREA")
        lines.append("CDX INFO")
        for tag in tags:
            lines.append(f"SET ORDER TO TAG {tag}")
            lines.append("TOP")
            lines.append("SL")
        lines.append("")
    lines.append("* DD096Z-D2W SELECT-area SMARTLIST verify complete.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def scan_runtime(text: str) -> Dict[str, int]:
    up = text.upper()
    metrics: Dict[str, int] = {}
    metrics["proof_supplied"] = int(bool(text))
    metrics["candidate_path_seen"] = int("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up)
    metrics["active_datadict_seen"] = int("DOTTALKPP\\DATA\\DATADICT" in up or "DOTTALKPP/DATA/DATADICT" in up)
    metrics["already_open_failures"] = len(re.findall(r"IS ALREADY OPEN IN AREA", up))
    metrics["no_table_open_failures"] = len(re.findall(r"NO TABLE OPEN", up))
    metrics["table_cdx_fallback_seen"] = int("\\INDEXES\\TABLE.CDX" in up or "/INDEXES/TABLE.CDX" in up)
    metrics["buildlmdb_failed_count"] = len(re.findall(r"BUILDLMDB:\s*FAILED", up))
    metrics["buildlmdb_ok_count"] = len(re.findall(r"BUILDLMDB:\s*DONE\s+OK=\d+\s+TAGS REBUILT", up))
    metrics["smartlist_seen_count"] = len(re.findall(r"RECORD\(S\) LISTED \(LIMIT", up))
    metrics["sl_usage_seen_count"] = len(re.findall(r"USAGE:\s*\n\s*SMARTLIST", up))
    metrics["list_command_mode_seen"] = int("CDX(LMDB) INDEXED RECORD(S)" in up)
    metrics["cdx_addtag_added_count"] = len(re.findall(r"CDX ADDTAG:\s*ADDED", up))
    metrics["cdx_addtag_already_exists_count"] = len(re.findall(r"CDX ADDTAG:\s*TAG ALREADY EXISTS", up))
    for area, table, expected, tags in TABLES:
        key = table.lower()
        metrics[f"{key}_seen"] = int(table in up)
        metrics[f"{key}_area_seen"] = int(table in up and (f"RECS: {expected}" in up or f"RECORD COUNT {expected}" in up))
        metrics[f"{key}_cdx_file_seen"] = int(f"{table}.CDX" in up)
        for tag in tags:
            tkey = f"{key}_{tag.lower()}"
            metrics[f"{tkey}_order_seen"] = int(f"SET ORDER: CDX TAG '{tag}'" in up or f"TAG '{tag}'" in up)
    return metrics

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2W SELECT-area SMARTLIST candidate rebuild generator and optional closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2W-select-area-smartlist-candidate-rebuild-v0")
    ap.add_argument("--write-runtime-scripts", action="store_true")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_select_area_smartlist_candidate_rebuild"
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
    wc(gen / "dd096zd2w_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    zb = read_json(repo / "docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json")
    candidate_root = Path(zb.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(zb.get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    table_rows = []
    missing = 0
    for area, table, expected, tags in TABLES:
        p = candidate_dbf / f"{table}.dbf"
        exists = int(p.exists())
        missing += 0 if exists else 1
        table_rows.append({
            "area": area,
            "table": table,
            "expected_records": expected,
            "candidate_dbf": str(p),
            "exists": exists,
            "tags": ";".join(tags),
            "access_strategy": f"SELECT {area}",
            "listing_command": "SL",
        })
    wc(gen / "dd096zd2w_select_area_smartlist_table_plan.csv", table_rows, ["area","table","expected_records","candidate_dbf","exists","tags","access_strategy","listing_command"])

    policy_rows = [
        {"policy": "listing_command_for_generated_scripts", "value": "SMARTLIST / SL", "rationale": "standard script listing, not manual cursor tooling"},
        {"policy": "list_command", "value": "developer/manual only", "rationale": "manual cursor-controlled behavior"},
        {"policy": "cursor_proof_commands", "value": "TUP/TOP/BOTTOM/RECNO only when explicitly proving cursor/order", "rationale": "avoid accidental cursor-coupled smoke proofs"},
        {"policy": "open_table_strategy", "value": "SELECT existing area when table already open", "rationale": "avoid USE already-open failure and table.cdx fallback"},
    ]
    wc(gen / "dd096zd2w_scripting_policy_corrections.csv", policy_rows, ["policy","value","rationale"])

    rebuild = make_select_smartlist_rebuild(candidate_dbf, candidate_index, candidate_lmdb)
    verify = make_select_smartlist_verify(candidate_dbf, candidate_index, candidate_lmdb)
    wt(gen / "DD096ZD2W_SELECT_AREA_SMARTLIST_CANDIDATE_CDX_LMDB_REBUILD.dts", rebuild)
    wt(gen / "DD096ZD2W_SELECT_AREA_SMARTLIST_CANDIDATE_CDX_LMDB_VERIFY.dts", verify)

    scripts_written = 0
    if args.write_runtime_scripts:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2W_SELECT_AREA_SMARTLIST_CANDIDATE_CDX_LMDB_REBUILD.dts", rebuild)
        wt(repo / "dottalkpp/data/scripts/DD096ZD2W_SELECT_AREA_SMARTLIST_CANDIDATE_CDX_LMDB_VERIFY.dts", verify)
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

    wc(gen / "dd096zd2w_runtime_proof_scan.csv",
       [{"metric": k, "value": v} for k, v in sorted(metrics.items())],
       ["metric","value"])

    expected_tables = len(TABLES)
    expected_tags = sum(len(tags) for _, _, _, tags in TABLES)
    proof_failures = 0
    if proof_supplied:
        checks = [
            ("candidate_path_seen", 1),
            ("active_datadict_seen", 0),
            ("already_open_failures", 0),
            ("no_table_open_failures", 0),
            ("table_cdx_fallback_seen", 0),
            ("buildlmdb_failed_count", 0),
        ]
        for k, expected in checks:
            if int(metrics.get(k, 0)) != expected:
                proof_failures += 1
        if int(metrics.get("buildlmdb_ok_count", 0)) < expected_tables:
            proof_failures += 1
        if int(metrics.get("smartlist_seen_count", 0)) < expected_tags:
            proof_failures += 1

    boundary = [
        ("select_area_smartlist_candidate_rebuild_script_package", 1, 1, 1),
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
    wc(out / "dd096zd2w_no_mutation_boundary_ledger.csv",
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
    wc(out / "dd096zd2w_gate_ledger.csv", gates, ["gate","expected","observed","pass"])

    if failures:
        status = "DD096ZD2W_SELECT_AREA_SMARTLIST_CANDIDATE_REBUILD_REVIEW"
    elif proof_supplied:
        status = "DD096ZD2W_SELECT_AREA_SMARTLIST_CANDIDATE_REBUILD_GREEN"
    else:
        status = "DD096ZD2W_SELECT_AREA_SMARTLIST_CANDIDATE_REBUILD_READY"

    report = f"""# DD096Z-D2W SELECT-Area SMARTLIST Candidate Rebuild

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2W supersedes DD096Z-D2V's listing style.

It keeps the correct SELECT-area repair, but changes generated verification output from `LIST` to `SMARTLIST` / `SL`.

## Summary

- Candidate DBF root: `{candidate_dbf}`
- Candidate INDEXES root: `{candidate_index}`
- Candidate LMDB root: `{candidate_lmdb}`
- Precondition blockers: **{blockers}**
- Missing candidate tables: **{missing}**
- Runtime scripts written: **{scripts_written}**
- Runtime proof supplied: **{proof_supplied}**
- Runtime proof failures: **{proof_failures}**
- Active catalog replacement: **0**
- Active CDX/LMDB rebuild: **0**

## Policy correction

Generated scripts should use:

```text
SL
SMARTLIST
```

not `LIST`, except when a developer/manual cursor proof explicitly requires `LIST`.

## Runtime scripts

- `DD096ZD2W_SELECT_AREA_SMARTLIST_CANDIDATE_CDX_LMDB_REBUILD`
- `DD096ZD2W_SELECT_AREA_SMARTLIST_CANDIDATE_CDX_LMDB_VERIFY`

Each table starts with `SELECT <area>`, then `AREA` and `STRUCT` before CDX commands.
"""
    wt(out / "DD096ZD2W_SELECT_AREA_SMARTLIST_CANDIDATE_REBUILD_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2w_select_area_smartlist_candidate_rebuild_v0",
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
        "runtime_proof_failures": proof_failures,
        "listing_policy": "SMARTLIST/SL for generated scripts; LIST dev/manual only",
        "active_catalog_replacement": 0,
        "active_cdx_lmdb_rebuild": 0,
        "source_edits": 0,
        "failures": failures,
        "next_recommended_action": "Run SELECT-area SMARTLIST candidate rebuild and verify; save transcript and rerun with --runtime-proof.",
    }
    wj(out / "dd096zd2w_select_area_smartlist_candidate_rebuild_manifest.json", manifest)

    print(f"DD096Z-D2W SELECT-area SMARTLIST candidate rebuild manifest: {out / 'dd096zd2w_select_area_smartlist_candidate_rebuild_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; missing_candidate_tables: {missing}; runtime_scripts_written: {scripts_written}; proof_supplied: {proof_supplied}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
