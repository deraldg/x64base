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
    "DD096ZD2X": (
        "docs/datadict/reports/DD096ZD2X-candidate-area-identity-guard-v0/dd096zd2x_candidate_area_identity_guard_manifest.json",
        [
            "DD096ZD2X_CANDIDATE_AREA_IDENTITY_GUARD_READY",
            "DD096ZD2X_CANDIDATE_AREA_IDENTITY_GUARD_GREEN",
            "DD096ZD2X_CANDIDATE_AREA_IDENTITY_GUARD_REVIEW",
        ],
    ),
}

TABLES: List[Tuple[str, int, List[str]]] = [
    ("DATA_DICTIONARY_OBJECTS", 10, ["CATALOG_OBJECT_ID", "CATALOG_OBJECT_NAME"]),
    ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", 127, ["CATALOG_OBJECT_ID", "CATALOG_ATTRIBUTE_NAME"]),
    ("DATA_DICTIONARY_RELATION_EDGES", 16, ["RELATION_FROM_OBJECT_ID", "RELATION_TO_OBJECT_ID"]),
    ("DATA_DICTIONARY_EVIDENCE_RECORDS", 7, ["CATALOG_OBJECT_ID"]),
    ("DATA_DICTIONARY_GATE_RECORDS", 3, ["GATE_RECORD_ID"]),
    ("DATA_DICTIONARY_RUNS", 2, ["RUN_RECORD_ID"]),
]

LEGACY_ACTIVE_NAMES = ["DDBASE", "DDOBJECT", "DDATTR", "DDEDGE", "DDEVID", "DDGATE", "DDARTIF", "DDSRC"]

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

def make_open_close_rebuild(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2Y open/close candidate CDX/LMDB rebuild")
    lines.append("* Corrected after D2W: do not SELECT hardcoded active areas.")
    lines.append("* Pattern: SETPATH candidate roots, USE one DATA_DICTIONARY_* table, rebuild, verify with SL, CLOSE, next table.")
    lines.append("* LIST is dev/manual tooling; generated proof uses SL/SMARTLIST.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("REL")
    lines.append("CLOSE ALL")
    lines.append("")
    for table, expected, tags in TABLES:
        lines.append(f"* ---------- OPEN/CLOSE REBUILD {table}; expected records {expected} ----------")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("* Guard: Path above must be docs\\datadict\\candidates\\...\\dbf and File must be this DATA_DICTIONARY_* table.")
        lines.append("CDX CREATE")
        for tag in tags:
            lines.append(f"CDX ADDTAG {tag}")
        lines.append("CDX INFO")
        lines.append("BUILDLMDB CLEAN YES")
        lines.append(f"SET INDEX TO {table}")
        lines.append("CDX INFO")
        for tag in tags:
            lines.append(f"SET ORDER TO TAG {tag}")
            lines.append("TOP")
            lines.append("SL")
        lines.append("CLOSE")
        lines.append("")
    lines.append("* DD096Z-D2Y open/close candidate rebuild complete.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def make_open_close_verify(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2Y open/close candidate CDX/LMDB verify")
    lines.append("* Opens candidate tables by name from candidate DBF root; verifies tags with SL.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("REL")
    lines.append("CLOSE ALL")
    lines.append("")
    for table, expected, tags in TABLES:
        lines.append(f"* ---------- OPEN/CLOSE VERIFY {table}; expected records {expected} ----------")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append(f"SET INDEX TO {table}")
        lines.append("CDX INFO")
        for tag in tags:
            lines.append(f"SET ORDER TO TAG {tag}")
            lines.append("TOP")
            lines.append("SL")
        lines.append("CLOSE")
        lines.append("")
    lines.append("* DD096Z-D2Y open/close candidate verify complete.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def scan_runtime(text: str) -> Dict[str, int]:
    up = text.upper()
    metrics: Dict[str, int] = {}
    metrics["proof_supplied"] = int(bool(text))
    metrics["candidate_path_seen"] = int("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up)
    metrics["active_datadict_path_seen"] = int("DOTTALKPP\\DATA\\DATADICT" in up or "DOTTALKPP/DATA/DATADICT" in up)
    metrics["legacy_active_table_seen_count"] = sum(1 for name in LEGACY_ACTIVE_NAMES if f"FILE: {name}" in up)
    metrics["mixed_root_build_seen"] = int(("DOTTALKPP\\DATA\\INDEXES\\DATADICT" in up or "DOTTALKPP/DATA/INDEXES/DATADICT" in up) and ("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up))
    metrics["table_cdx_fallback_seen"] = int("\\INDEXES\\TABLE.CDX" in up or "/INDEXES/TABLE.CDX" in up)
    metrics["already_open_failures"] = len(re.findall(r"IS ALREADY OPEN IN AREA", up))
    metrics["no_table_open_failures"] = len(re.findall(r"NO TABLE OPEN", up))
    metrics["buildlmdb_failed_count"] = len(re.findall(r"BUILDLMDB:\s*FAILED", up))
    metrics["buildlmdb_ok_count"] = len(re.findall(r"BUILDLMDB:\s*DONE\s+OK=\d+\s+TAGS REBUILT", up))
    metrics["cdx_created_count"] = len(re.findall(r"CDX CREATED:", up))
    metrics["cdx_file_exists_count"] = len(re.findall(r"CDX CREATE:\s*FILE ALREADY EXISTS", up))
    metrics["cdx_addtag_added_count"] = len(re.findall(r"CDX ADDTAG:\s*ADDED", up))
    metrics["cdx_addtag_exists_count"] = len(re.findall(r"CDX ADDTAG:\s*TAG ALREADY EXISTS", up))
    metrics["smartlist_output_count"] = len(re.findall(r"RECORD\(S\) LISTED \(LIMIT", up))
    metrics["set_index_count"] = len(re.findall(r"SET INDEX", up))
    metrics["set_order_success_count"] = len(re.findall(r"SET ORDER:\s*CDX TAG", up))
    for table, expected, tags in TABLES:
        key = table.lower()
        metrics[f"{key}_opened_v64"] = int(bool(re.search(r"OPENED\s+" + re.escape(table) + r"\s+\(V64\)\s*:\s*RECORD COUNT\s+" + str(expected), up)))
        metrics[f"{key}_candidate_path_seen"] = int(table in up and ("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up))
        metrics[f"{key}_cdx_seen"] = int(f"{table}.CDX" in up)
        for tag in tags:
            tkey = f"{key}_{tag.lower()}"
            metrics[f"{tkey}_tag_seen"] = int(tag in up)
            metrics[f"{tkey}_order_success_seen"] = int(f"SET ORDER: CDX TAG '{tag}'" in up or f"TAG '{tag}'  MODE LMDB" in up)
    return metrics

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2Y open/close candidate CDX/LMDB rebuild generator and optional closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2Y-open-close-candidate-rebuild-v0")
    ap.add_argument("--write-runtime-scripts", action="store_true")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_open_close_candidate_rebuild"
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
    wc(gen / "dd096zd2y_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    zb = read_json(repo / "docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json")
    candidate_root = Path(zb.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(zb.get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    table_rows = []
    missing = 0
    for table, expected, tags in TABLES:
        p = candidate_dbf / f"{table}.dbf"
        exists = int(p.exists())
        missing += 0 if exists else 1
        table_rows.append({
            "table": table,
            "expected_records": expected,
            "candidate_dbf": str(p),
            "exists": exists,
            "tags": ";".join(tags),
            "access_strategy": "USE from candidate DBF root, then CLOSE",
            "listing_command": "SL",
        })
    wc(gen / "dd096zd2y_open_close_table_plan.csv", table_rows, ["table","expected_records","candidate_dbf","exists","tags","access_strategy","listing_command"])

    policy_rows = [
        {"rule": "Do not hardcode SELECT areas unless a prior identity inventory proves that area currently contains the candidate DATA_DICTIONARY_* table.", "reason": "D2W selected active legacy DD* tables."},
        {"rule": "In fresh or uncertain sessions, open each candidate table by USE after SETPATH DBF points to the candidate DBF root.", "reason": "D2X open probe proved this works and lands in area 10."},
        {"rule": "After each candidate table rebuild/verify, CLOSE before moving to the next table.", "reason": "Prevents already-open area conflicts."},
        {"rule": "Use SET INDEX TO <table> after BUILDLMDB and before SET ORDER TO TAG <tag>.", "reason": "Keeps CDX/LMDB attachment explicit."},
        {"rule": "Use SL/SMARTLIST for generated proof listings.", "reason": "LIST is developer/manual cursor-controlled tooling."},
    ]
    wc(gen / "dd096zd2y_rebuild_policy.csv", policy_rows, ["rule","reason"])

    rebuild = make_open_close_rebuild(candidate_dbf, candidate_index, candidate_lmdb)
    verify = make_open_close_verify(candidate_dbf, candidate_index, candidate_lmdb)
    wt(gen / "DD096ZD2Y_OPEN_CLOSE_CANDIDATE_CDX_LMDB_REBUILD.dts", rebuild)
    wt(gen / "DD096ZD2Y_OPEN_CLOSE_CANDIDATE_CDX_LMDB_VERIFY.dts", verify)

    scripts_written = 0
    if args.write_runtime_scripts:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2Y_OPEN_CLOSE_CANDIDATE_CDX_LMDB_REBUILD.dts", rebuild)
        wt(repo / "dottalkpp/data/scripts/DD096ZD2Y_OPEN_CLOSE_CANDIDATE_CDX_LMDB_VERIFY.dts", verify)
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

    wc(gen / "dd096zd2y_runtime_proof_scan.csv",
       [{"metric": k, "value": v} for k, v in sorted(metrics.items())],
       ["metric","value"])

    expected_tables = len(TABLES)
    expected_tags = sum(len(tags) for _, _, tags in TABLES)
    proof_failures = 0
    if proof_supplied:
        checks = [
            ("candidate_path_seen", 1),
            ("active_datadict_path_seen", 0),
            ("legacy_active_table_seen_count", 0),
            ("mixed_root_build_seen", 0),
            ("table_cdx_fallback_seen", 0),
            ("already_open_failures", 0),
            ("no_table_open_failures", 0),
            ("buildlmdb_failed_count", 0),
        ]
        for k, expected in checks:
            if int(metrics.get(k, 0)) != expected:
                proof_failures += 1
        if int(metrics.get("buildlmdb_ok_count", 0)) < expected_tables:
            proof_failures += 1
        if int(metrics.get("smartlist_output_count", 0)) < expected_tags:
            proof_failures += 1

    boundary = [
        ("open_close_candidate_rebuild_script_package", 1, 1, 1),
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
    wc(out / "dd096zd2y_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    gates = [
        {"gate": "preconditions_green_or_accepted", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "candidate_tables_present", "expected": 0, "observed": missing, "pass": int(missing == 0)},
        {"gate": "runtime_scripts_written_if_requested", "expected": int(args.write_runtime_scripts), "observed": scripts_written, "pass": int(scripts_written == int(args.write_runtime_scripts))},
        {"gate": "runtime_proof_failures_if_supplied", "expected": 0, "observed": proof_failures, "pass": int((not proof_supplied) or proof_failures == 0)},
        {"gate": "active_replacement_performed_by_generator", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    wc(out / "dd096zd2y_gate_ledger.csv", gates, ["gate","expected","observed","pass"])

    if failures:
        status = "DD096ZD2Y_OPEN_CLOSE_CANDIDATE_REBUILD_REVIEW"
    elif proof_supplied:
        status = "DD096ZD2Y_OPEN_CLOSE_CANDIDATE_REBUILD_GREEN"
    else:
        status = "DD096ZD2Y_OPEN_CLOSE_CANDIDATE_REBUILD_READY"

    report = f"""# DD096Z-D2Y Open/Close Candidate Rebuild

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2Y corrects the D2W mixed-root failure.

D2X proved that in a fresh session no candidate tables are open, and the safe identity path is to `USE` one candidate `DATA_DICTIONARY_*` table from the candidate DBF root, verify it, then `CLOSE`.

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

## Runtime scripts

- `DD096ZD2Y_OPEN_CLOSE_CANDIDATE_CDX_LMDB_REBUILD`
- `DD096ZD2Y_OPEN_CLOSE_CANDIDATE_CDX_LMDB_VERIFY`

## Working pattern

```text
SETPATH DBF <candidate dbf root>
USE DATA_DICTIONARY_*
AREA / STRUCT
CDX CREATE
CDX ADDTAG <actual STRUCT field>
BUILDLMDB CLEAN YES
SET INDEX TO <table>
SET ORDER TO TAG <tag>
TOP
SL
CLOSE
```

No hardcoded SELECT area mapping is used.
"""
    wt(out / "DD096ZD2Y_OPEN_CLOSE_CANDIDATE_REBUILD_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2y_open_close_candidate_rebuild_v0",
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
        "next_recommended_action": "Run open/close candidate rebuild and verify; save transcript and rerun with --runtime-proof.",
    }
    wj(out / "dd096zd2y_open_close_candidate_rebuild_manifest.json", manifest)

    print(f"DD096Z-D2Y open/close candidate rebuild manifest: {out / 'dd096zd2y_open_close_candidate_rebuild_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; missing_candidate_tables: {missing}; runtime_scripts_written: {scripts_written}; proof_supplied: {proof_supplied}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
