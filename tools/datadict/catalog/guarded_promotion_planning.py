#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_DD096X_DIR = "docs/datadict/reports/DD096X-guarded-x64-datadict-schema-proof-v0"
DEFAULT_DD096Y_DIR = "docs/datadict/reports/DD096Y-stage-candidate-rows-into-x64-schema-v0"
DEFAULT_DD096YQ_DIR = "docs/datadict/reports/DD096YQ-post-import-validation-readback-v0"

REQUIRED_STATUSES = {
    "DD096X": ["DD096X_GUARDED_X64_SCHEMA_PROOF_READY"],
    "DD096Y": ["DD096Y_X64_STAGED_IMPORT_READY"],
    "DD096YQ": ["DD096YQ_POST_IMPORT_VALIDATION_GREEN"],
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def find_manifest(report_dir: Path, pattern: str) -> Path:
    if report_dir.exists():
        matches = sorted(report_dir.glob(pattern))
        if matches:
            return matches[0]
    return report_dir / pattern.replace("*", "")


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096Z guarded promotion planning for x64 Data Dictionary proof schema")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096Z-guarded-promotion-planning-v0")
    ap.add_argument("--dd096x-dir", default=DEFAULT_DD096X_DIR)
    ap.add_argument("--dd096y-dir", default=DEFAULT_DD096Y_DIR)
    ap.add_argument("--dd096yq-dir", default=DEFAULT_DD096YQ_DIR)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    generated = out / "generated_promotion_plan"
    generated.mkdir(parents=True, exist_ok=True)

    manifest_paths = {
        "DD096X": find_manifest(repo / args.dd096x_dir, "dd096x_guarded_x64_datadict_schema_proof_manifest.json"),
        "DD096Y": find_manifest(repo / args.dd096y_dir, "dd096y_stage_candidate_rows_into_x64_schema_manifest.json"),
        "DD096YQ": find_manifest(repo / args.dd096yq_dir, "dd096yq_post_import_validation_readback_manifest.json"),
    }

    precondition_rows: List[Dict[str, Any]] = []
    precondition_blockers = 0
    for lane, path in manifest_paths.items():
        data = read_json(path)
        observed = data.get("status", "MISSING")
        required = "|".join(REQUIRED_STATUSES[lane])
        present = int(bool(data))
        pass_status = int(present and observed in REQUIRED_STATUSES[lane])
        # DD096Z is allowed to be ready as planning even when DD096YQ is not green yet.
        if lane != "DD096YQ" and not pass_status:
            precondition_blockers += 1
        precondition_rows.append({
            "lane": lane,
            "manifest_path": str(path),
            "manifest_present": present,
            "observed_status": observed,
            "required_for_apply": required,
            "pass_for_apply": pass_status,
            "notes": "DD096YQ may be pending during planning; must be green before any promotion apply package.",
        })
    write_csv(generated / "dd096z_precondition_ledger.csv", precondition_rows, [
        "lane", "manifest_path", "manifest_present", "observed_status", "required_for_apply", "pass_for_apply", "notes"
    ])

    phases = [
        ("Z1_FREEZE", "Freeze active Data Dictionary catalog and proof inputs", "No DBF writes; capture active and proof roots; require explicit operator authorization.", "planning_only"),
        ("Z2_BACKUP", "Create rollback backup plan", "Back up dottalkpp/data/datadict, indexes/datadict, lmdb/datadict, workspace schema, and relevant run reports.", "planning_only"),
        ("Z3_VALIDATE_PROOF", "Require DD096YQ green readback", "Expected counts: objects 10, attrs 127, edges 16, evidence 7, gates 3, runs 2; v64 readback required.", "planning_only"),
        ("Z4_SELECT_COPY_POLICY", "Choose copy/import policy", "Do not promote SANDBOX files by blind copy unless paths, sidecars, memo files, CDX/LMDB, and workspace policy are verified.", "planning_only"),
        ("Z5_STAGE_ACTIVE_REPLACEMENT", "Plan inactive staging root", "Create an inactive candidate root before active datadict switch; validate DDICT against candidate root if pathing supports it.", "planning_only"),
        ("Z6_CDX_LMDB_REBUILD", "Plan CDX/LMDB rebuild", "Rebuild indexes/mirrors only after DBF/memo/table identity proof is accepted; capture logs.", "planning_only"),
        ("Z7_WORKSPACE_SCHEMA", "Plan workspace schema update", "Update ddbase/dictionary workspace only after table roots, fields, relations, and indexes are stable.", "planning_only"),
        ("Z8_DDICT_SMOKE", "Plan runtime DDICT smoke", "DDICT STATUS/TABLES/FIELDS/TAGS/REL/EVIDENCE must pass against candidate/active catalog.", "planning_only"),
        ("Z9_HELP_BOUNDARY", "Keep HELP/CMDHELPCHK separate", "Do not apply HELP/CMDHELPCHK changes during catalog promotion unless separately authorized.", "planning_only"),
        ("Z10_ROLLBACK", "Plan rollback verification", "Restore old DBF/CDX/LMDB/workspace roots and rerun DDICT status/table smoke.", "planning_only"),
        ("Z11_CLOSEOUT", "Promotion closeout criteria", "Only after apply package and runtime green: capture manifest, proof transcript, boundary ledger, and MDO/SelfDoc handoff.", "planning_only"),
    ]
    phase_rows = [
        {"phase_id": pid, "phase": phase, "required_action": action, "status": status}
        for pid, phase, action, status in phases
    ]
    write_csv(generated / "dd096z_promotion_phase_plan.csv", phase_rows, [
        "phase_id", "phase", "required_action", "status"
    ])

    copy_policy_rows = [
        {"policy_id": "COPY-001", "policy": "Do not overwrite active datadict DBFs directly from SANDBOX proof tables without a staged candidate root.", "status": "required"},
        {"policy_id": "COPY-002", "policy": "Memo sidecars and x64 metadata sidecars must move with DBFs; treat DBF alone as incomplete when memo fields exist.", "status": "required"},
        {"policy_id": "COPY-003", "policy": "CDX and LMDB are regenerated for the promoted/candidate root, not blindly copied from an unrelated path.", "status": "required"},
        {"policy_id": "COPY-004", "policy": "Path roots must remain dottalkpp/data/datadict, dottalkpp/data/indexes/datadict, and dottalkpp/data/lmdb/datadict after active promotion.", "status": "required"},
        {"policy_id": "COPY-005", "policy": "DDICT path resolver must be rerun or smoked after promotion to confirm it sees DBF/CDX/LMDB artifacts.", "status": "required"},
        {"policy_id": "COPY-006", "policy": "Old active catalog backup must be restorable without schema conversion.", "status": "required"},
    ]
    write_csv(generated / "dd096z_active_catalog_copy_policy.csv", copy_policy_rows, [
        "policy_id", "policy", "status"
    ])

    validation_rows = [
        {"surface": "DDICT STATUS", "expected": "ACTIVE_CATALOG_PRESENT with expected table count and paths", "apply_gate": "required"},
        {"surface": "DDICT TABLES", "expected": "new x64 catalog tables visible and readable", "apply_gate": "required"},
        {"surface": "DDICT FIELDS DATA_DICTIONARY_OBJECTS", "expected": "long x64 identity fields visible", "apply_gate": "required"},
        {"surface": "DDICT FIELDS DATA_DICTIONARY_OBJECT_ATTRIBUTES", "expected": "CATALOG_ATTRIBUTE_VALUE C(254) and CATALOG_ATTRIBUTE_DETAIL M visible", "apply_gate": "required"},
        {"surface": "DDICT REL DDICT BOTH", "expected": "DDICT root command relates to DDICT sub-surfaces", "apply_gate": "required"},
        {"surface": "DDICT EVIDENCE DDICT", "expected": "evidence rows visible for runtime/catalog provenance", "apply_gate": "required"},
        {"surface": "WORKSPACE LOAD ddbase", "expected": "workspace restore compatible or intentionally versioned", "apply_gate": "required"},
        {"surface": "BUILDLMDB / CDX rebuild", "expected": "only after schema/copy policy accepted", "apply_gate": "separate_authorization"},
    ]
    write_csv(generated / "dd096z_runtime_validation_plan.csv", validation_rows, [
        "surface", "expected", "apply_gate"
    ])

    risk_rows = [
        {"risk_id": "RISK-001", "risk": "Promoting SANDBOX proof tables by blind copy may miss sidecars or path-specific metadata.", "mitigation": "Use staged candidate root and explicit copy ledger."},
        {"risk_id": "RISK-002", "risk": "DDICT currently expects older DD* table names/paths.", "mitigation": "Plan DDICT compatibility bridge, aliases, or path/schema resolver before active cutover."},
        {"risk_id": "RISK-003", "risk": "Workspace schema may still reference old table names.", "mitigation": "Version ddbase workspace schema and test both old and x64 names."},
        {"risk_id": "RISK-004", "risk": "CDX/LMDB rebuild could obscure DBF success with index failures.", "mitigation": "Promote DBF/memo proof first; rebuild index/mirror as a separate gated phase."},
        {"risk_id": "RISK-005", "risk": "HELP/CMDHELPCHK changes could be conflated with catalog promotion.", "mitigation": "Keep HELP/CMDHELPCHK candidate apply in separate DD092D lane."},
        {"risk_id": "RISK-006", "risk": "DotScript multiline CREATE continuation remains red.", "mitigation": "Use generated single-line CREATE or fix continuation in a separate script-engine lane."},
    ]
    write_csv(generated / "dd096z_risk_register.csv", risk_rows, [
        "risk_id", "risk", "mitigation"
    ])

    boundary_rows = [
        {"boundary": "promotion_planning_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_dbf_write", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "workspace_schema_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    write_csv(out / "dd096z_no_mutation_boundary_ledger.csv", boundary_rows, [
        "boundary", "observed", "required", "pass"
    ])

    dd096yq_pass = next((r for r in precondition_rows if r["lane"] == "DD096YQ"), {}).get("pass_for_apply", 0)
    status = "DD096Z_PROMOTION_PLAN_READY_PENDING_DD096YQ" if not dd096yq_pass else "DD096Z_PROMOTION_PLAN_READY"
    failures = 0 if precondition_blockers == 0 else precondition_blockers

    gates = [
        {"gate": "dd096x_generator_ready", "expected": "DD096X_GUARDED_X64_SCHEMA_PROOF_READY", "observed": next((r["observed_status"] for r in precondition_rows if r["lane"] == "DD096X"), ""), "pass": next((r["pass_for_apply"] for r in precondition_rows if r["lane"] == "DD096X"), 0)},
        {"gate": "dd096y_stage_ready", "expected": "DD096Y_X64_STAGED_IMPORT_READY", "observed": next((r["observed_status"] for r in precondition_rows if r["lane"] == "DD096Y"), ""), "pass": next((r["pass_for_apply"] for r in precondition_rows if r["lane"] == "DD096Y"), 0)},
        {"gate": "dd096yq_green_before_apply", "expected": "DD096YQ_POST_IMPORT_VALIDATION_GREEN", "observed": next((r["observed_status"] for r in precondition_rows if r["lane"] == "DD096YQ"), ""), "pass": next((r["pass_for_apply"] for r in precondition_rows if r["lane"] == "DD096YQ"), 0)},
        {"gate": "active_replacement_authorized", "expected": 0, "observed": 0, "pass": 1},
        {"gate": "promotion_plan_written", "expected": 1, "observed": 1, "pass": 1},
    ]
    write_csv(out / "dd096z_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])

    report = f"""# DD096Z Guarded Promotion Planning

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096Z plans a future guarded promotion from the SANDBOX x64 Data Dictionary proof schema toward the active Data Dictionary catalog.

It is planning only. It does not replace, overwrite, copy, rebuild, or mutate the active catalog.

## Current position

DD096X and DD096Y may be green, but active promotion must wait for DD096YQ post-import validation/readback to be green.

## Promotion principle

Do not blindly copy SANDBOX proof DBFs into the active Data Dictionary root.

A safe promotion must handle:

- DBF files
- memo sidecars
- x64 metadata sidecars
- CDX rebuild
- LMDB rebuild
- DDICT pathing
- workspace schema versioning
- rollback
- HELP/CMDHELPCHK boundary separation

## Status summary

- Precondition blockers excluding DD096YQ: **{precondition_blockers}**
- DD096YQ apply gate pass: **{dd096yq_pass}**
- Active catalog replacement authorized: **0**
- Active DBF writes performed: **0**
- CDX/LMDB rebuild performed: **0**

## Next safe action

Run DD096YQ runtime validation/readback and, if green, rerun this planner or proceed to a separately authorized DD096Z-A apply-package design.
"""
    write_text(out / "DD096Z_GUARDED_PROMOTION_PLANNING_REPORT.md", report)

    manifest = {
        "contract": "dd096z_guarded_promotion_planning_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers_excluding_dd096yq": precondition_blockers,
        "dd096yq_apply_gate_pass": int(dd096yq_pass),
        "active_catalog_replacement": 0,
        "active_catalog_dbf_write": 0,
        "cdx_lmdb_rebuild": 0,
        "failures": failures,
        "next_recommended_action": "Run DD096YQ validation; then design a separate apply package only if explicitly authorized.",
    }
    write_json(out / "dd096z_guarded_promotion_planning_manifest.json", manifest)

    print(f"DD096Z guarded promotion planning manifest: {out / 'dd096z_guarded_promotion_planning_manifest.json'}")
    print(f"status: {status}; precondition_blockers_excluding_dd096yq: {precondition_blockers}; dd096yq_apply_gate_pass: {int(dd096yq_pass)}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
