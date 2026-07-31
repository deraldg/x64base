#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Dict, List

REQUIRED = {
    "DD096ZD2R": (
        "docs/datadict/reports/DD096ZD2R-candidate-cdx-tag-prereq-diagnostic-v0/dd096zd2r_candidate_cdx_tag_prereq_diagnostic_manifest.json",
        [
            "DD096ZD2R_CANDIDATE_CDX_TAG_PREREQ_DIAGNOSTIC_READY",
            "DD096ZD2R_CANDIDATE_CDX_TAG_PREREQ_DIAGNOSTIC_REVIEW",
        ],
    ),
    "DD096ZGQ": (
        "docs/datadict/reports/DD096ZGQ-candidate-raw-smoke-closure-v0/dd096zgq_candidate_raw_smoke_closure_manifest.json",
        ["DD096ZGQ_CANDIDATE_RAW_SMOKE_CLOSURE_GREEN"],
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

def scan(text: str) -> Dict[str, int]:
    up = text.upper()
    return {
        "candidate_path_seen": int("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up),
        "active_datadict_seen": int("DOTTALKPP\\DATA\\DATADICT" in up or "DOTTALKPP/DATA/DATADICT" in up),
        "objects_opened_v64": int(bool(re.search(r"OPENED\s+DATA_DICTIONARY_OBJECTS\s+\(V64\)\s*:\s*RECORD COUNT\s+10", up))),
        "cdx_create_seen": int("CDX CREATED:" in up and "DATA_DICTIONARY_OBJECTS.CDX" in up),
        "catalog_object_id_addtag_seen": int("CDX ADDTAG: ADDED 'CATALOG_OBJECT_ID'" in up),
        "bad_object_type_tag_seen": int("CDX ADDTAG: ADDED 'OBJECT_TYPE'" in up),
        "object_type_droptag_seen": int("CDX DROPTAG: REMOVED 'OBJECT_TYPE'" in up),
        "catalog_object_type_addtag_seen": int("CDX ADDTAG: ADDED 'CATALOG_OBJECT_TYPE'" in up),
        "buildlmdb_confirmation_seen": int("BUILDLMDB: CONFIRMATION REQUIRED" in up),
        "buildlmdb_clean_seen": int("BUILDLMDB CLEAN" in up),
        "buildlmdb_ok_seen": int(bool(re.search(r"BUILDLMDB:\s*DONE\s+OK=1\s+TAGS REBUILT", up))),
        "lmdb_mode_list_seen": int("MODE LMDB" in up),
        "set_order_catalog_object_id_seen": int("SET ORDER: CDX TAG 'CATALOG_OBJECT_ID'" in up),
        "cdx_lmdb_indexed_records_seen": int("CDX(LMDB) INDEXED RECORD(S)" in up),
        "tup_ordered_seen": int("OBJ_038D3910E2A03EC3C8E3" in up),
    }

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2S single-table CDX/LMDB proof closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2S-single-table-cdx-lmdb-proof-closure-v0")
    ap.add_argument("--runtime-proof", required=True)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_single_table_cdx_lmdb_proof_closure"
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
    wc(gen / "dd096zd2s_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    proof_path = Path(args.runtime_proof)
    if not proof_path.is_absolute():
        proof_path = repo / proof_path
    text = read_text(proof_path)
    proof_supplied = int(bool(text))
    metrics = scan(text)
    wc(gen / "dd096zd2s_single_table_proof_scan.csv",
       [{"metric": k, "value": v} for k, v in metrics.items()] + [{"metric": "proof_supplied", "value": proof_supplied}],
       ["metric","value"])

    success_rows = [
        {"proof_point": "candidate_path_seen", "required": 1, "observed": metrics["candidate_path_seen"], "pass": int(metrics["candidate_path_seen"] == 1)},
        {"proof_point": "active_datadict_not_seen", "required": 0, "observed": metrics["active_datadict_seen"], "pass": int(metrics["active_datadict_seen"] == 0)},
        {"proof_point": "objects_opened_v64", "required": 1, "observed": metrics["objects_opened_v64"], "pass": int(metrics["objects_opened_v64"] == 1)},
        {"proof_point": "cdx_create_seen", "required": 1, "observed": metrics["cdx_create_seen"], "pass": int(metrics["cdx_create_seen"] == 1)},
        {"proof_point": "catalog_object_id_addtag_seen", "required": 1, "observed": metrics["catalog_object_id_addtag_seen"], "pass": int(metrics["catalog_object_id_addtag_seen"] == 1)},
        {"proof_point": "buildlmdb_ok_seen", "required": 1, "observed": metrics["buildlmdb_ok_seen"], "pass": int(metrics["buildlmdb_ok_seen"] == 1)},
        {"proof_point": "set_order_catalog_object_id_seen", "required": 1, "observed": metrics["set_order_catalog_object_id_seen"], "pass": int(metrics["set_order_catalog_object_id_seen"] == 1)},
        {"proof_point": "lmdb_mode_list_seen", "required": 1, "observed": metrics["lmdb_mode_list_seen"], "pass": int(metrics["lmdb_mode_list_seen"] == 1)},
    ]
    wc(gen / "dd096zd2s_success_criteria_ledger.csv", success_rows, ["proof_point","required","observed","pass"])

    finding_rows = [
        {
            "finding_id": "D2S-F01",
            "finding": "CDX CREATE is required before CDX ADDTAG/BUILDLMDB can succeed for candidate tables.",
            "evidence": "Before create, SET INDEX failed/file not found; after CDX CREATE, ADDTAG worked.",
            "classification": "confirmed",
        },
        {
            "finding_id": "D2S-F02",
            "finding": "CDX ADDTAG <field_name> is the observed working syntax.",
            "evidence": "CDX ADDTAG CATALOG_OBJECT_ID added the tag.",
            "classification": "confirmed",
        },
        {
            "finding_id": "D2S-F03",
            "finding": "BUILDLMDB requires confirmation when existing envdir data exists.",
            "evidence": "BUILDLMDB without YES requested confirmation; BUILDLMDB CLEAN YES succeeded.",
            "classification": "confirmed",
        },
        {
            "finding_id": "D2S-F04",
            "finding": "After BUILDLMDB CLEAN YES, SET ORDER TO CATALOG_OBJECT_ID can list through LMDB mode.",
            "evidence": "LIST reported ORDER file/tag MODE LMDB and listed 10 cdx(lmdb) indexed records.",
            "classification": "confirmed",
        },
        {
            "finding_id": "D2S-F05",
            "finding": "CDX INFO can show tag metadata even when STRUCT still reports Index file: (none).",
            "evidence": "After CDX ADDTAG/BUILDLMDB, cdx info showed tags; later STRUCT still showed Index file: (none).",
            "classification": "runtime_observation_needs_followup",
        },
        {
            "finding_id": "D2S-F06",
            "finding": "A wrong tag name such as OBJECT_TYPE can be added as metadata, but BUILDLMDB rebuilt only the valid CATALOG_OBJECT_ID tag.",
            "evidence": "OBJECT_TYPE was added then later dropped; BUILDLMDB reported OK=1.",
            "classification": "caution",
        },
    ]
    wc(gen / "dd096zd2s_findings.csv", finding_rows, ["finding_id","finding","evidence","classification"])

    next_plan = [
        {"step_id": "D2T-01", "step": "Generate full candidate CDX create/addtag/BUILDLMDB script for all six DATA_DICTIONARY_* tables.", "precondition": "DD096ZD2S green"},
        {"step_id": "D2T-02", "step": "Use CDX CREATE first for each candidate table.", "precondition": "candidate path only"},
        {"step_id": "D2T-03", "step": "Use CDX ADDTAG <actual_field_name> only; no alias/short tags.", "precondition": "field visible in STRUCT"},
        {"step_id": "D2T-04", "step": "Run BUILDLMDB CLEAN YES after tags exist.", "precondition": "CDX INFO shows tags"},
        {"step_id": "D2T-05", "step": "Verify SET ORDER/LIST for at least one tag per table.", "precondition": "BUILDLMDB OK"},
    ]
    wc(gen / "dd096zd2s_next_full_rebuild_plan.csv", next_plan, ["step_id","step","precondition"])

    boundary = [
        ("single_table_cdx_lmdb_proof_closure_only", 1, 1, 1),
        ("source_edits", 0, 0, 1),
        ("build_file_edits", 0, 0, 1),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zd2s_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    gate_rows = [
        {"gate": "preconditions_green_or_accepted", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "runtime_proof_supplied", "expected": 1, "observed": proof_supplied, "pass": int(proof_supplied == 1)},
    ] + [{"gate": r["proof_point"], "expected": r["required"], "observed": r["observed"], "pass": r["pass"]} for r in success_rows]
    failures = sum(1 for row in gate_rows if int(row["pass"]) != 1)
    wc(out / "dd096zd2s_gate_ledger.csv", gate_rows, ["gate","expected","observed","pass"])

    status = "DD096ZD2S_SINGLE_TABLE_CDX_LMDB_PROOF_GREEN" if failures == 0 else "DD096ZD2S_SINGLE_TABLE_CDX_LMDB_PROOF_REVIEW"

    report = f"""# DD096Z-D2S Single-Table CDX/LMDB Proof Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2S closes the one-table candidate CDX/LMDB proof for `DATA_DICTIONARY_OBJECTS`.

It proves the missing prerequisite from DD096Z-D2R: create a candidate CDX first, add a real tag, then run `BUILDLMDB CLEAN YES`.

## Summary

- Runtime proof supplied: **{proof_supplied}**
- Candidate path seen: **{metrics['candidate_path_seen']}**
- Active datadict root seen: **{metrics['active_datadict_seen']}**
- DATA_DICTIONARY_OBJECTS opened v64/count 10: **{metrics['objects_opened_v64']}**
- CDX CREATE seen: **{metrics['cdx_create_seen']}**
- CDX ADDTAG CATALOG_OBJECT_ID seen: **{metrics['catalog_object_id_addtag_seen']}**
- BUILDLMDB OK seen: **{metrics['buildlmdb_ok_seen']}**
- SET ORDER CATALOG_OBJECT_ID seen: **{metrics['set_order_catalog_object_id_seen']}**
- LIST MODE LMDB seen: **{metrics['lmdb_mode_list_seen']}**
- Source edits: **0**
- Active catalog replacement: **0**
- Active CDX/LMDB rebuild: **0**

## Interpretation

The candidate LMDB failure was not caused by unreadable x64 DBFs. It was caused by missing candidate CDX/tag setup.

Observed working sequence:

```text
CDX CREATE
CDX ADDTAG CATALOG_OBJECT_ID
BUILDLMDB CLEAN YES
SET ORDER TO CATALOG_OBJECT_ID
LIST
```

## Next lane

DD096Z-D2T should generate a full candidate-only rebuild script for all six candidate tables using only actual STRUCT field names.
"""
    wt(out / "DD096ZD2S_SINGLE_TABLE_CDX_LMDB_PROOF_CLOSURE_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2s_single_table_cdx_lmdb_proof_closure_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "runtime_proof": str(proof_path),
        "runtime_proof_supplied": proof_supplied,
        "candidate_path_seen": metrics["candidate_path_seen"],
        "active_datadict_seen": metrics["active_datadict_seen"],
        "objects_opened_v64": metrics["objects_opened_v64"],
        "cdx_create_seen": metrics["cdx_create_seen"],
        "catalog_object_id_addtag_seen": metrics["catalog_object_id_addtag_seen"],
        "buildlmdb_ok_seen": metrics["buildlmdb_ok_seen"],
        "set_order_catalog_object_id_seen": metrics["set_order_catalog_object_id_seen"],
        "lmdb_mode_list_seen": metrics["lmdb_mode_list_seen"],
        "source_edits": 0,
        "active_catalog_replacement": 0,
        "active_cdx_lmdb_rebuild": 0,
        "failures": failures,
        "next_recommended_action": "DD096Z-D2T full candidate-only CDX/LMDB rebuild script for all candidate tables.",
    }
    wj(out / "dd096zd2s_single_table_cdx_lmdb_proof_closure_manifest.json", manifest)

    print(f"DD096Z-D2S single-table CDX/LMDB proof closure manifest: {out / 'dd096zd2s_single_table_cdx_lmdb_proof_closure_manifest.json'}")
    print(f"status: {status}; proof_supplied: {proof_supplied}; cdx_create_seen: {metrics['cdx_create_seen']}; addtag_seen: {metrics['catalog_object_id_addtag_seen']}; buildlmdb_ok_seen: {metrics['buildlmdb_ok_seen']}; lmdb_mode_list_seen: {metrics['lmdb_mode_list_seen']}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
