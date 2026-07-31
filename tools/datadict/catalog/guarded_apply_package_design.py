#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
from pathlib import Path

READY = {
    "DD096YQ": ("docs/datadict/reports/DD096YQ-post-import-validation-readback-v0/dd096yq_post_import_validation_readback_manifest.json", "DD096YQ_POST_IMPORT_VALIDATION_GREEN"),
    "DD096Z": ("docs/datadict/reports/DD096Z-guarded-promotion-planning-v0/dd096z_guarded_promotion_planning_manifest.json", "DD096Z_PROMOTION_PLAN_READY"),
}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def read_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

def wt(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def wj(path, obj):
    wt(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def wc(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def main():
    parser = argparse.ArgumentParser(description="DD096Z-A guarded apply-package design")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--run-id", default="DD096ZA-guarded-apply-package-design-v0")
    parser.add_argument("--profile", action="append", default=[])
    parser.add_argument("--fail-on-review", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_apply_package_design"
    gen.mkdir(parents=True, exist_ok=True)

    preconditions = []
    blockers = 0
    for lane, pair in READY.items():
        rel, expected = pair
        path = repo / rel
        data = read_json(path)
        observed = data.get("status", "MISSING")
        passed = int(bool(data) and observed == expected)
        blockers += 0 if passed else 1
        preconditions.append({
            "lane": lane,
            "manifest_path": str(path),
            "observed_status": observed,
            "expected_status": expected,
            "pass": passed,
        })
    wc(gen / "dd096za_precondition_ledger.csv", preconditions, ["lane", "manifest_path", "observed_status", "expected_status", "pass"])

    apply_steps = [
        ("A0", "Refuse active replacement by default", "implemented_in_skeleton"),
        ("A1", "Capture active DBF/CDX/LMDB/workspace roots", "future_apply_required"),
        ("A2", "Create timestamped rollback backup with hash ledger", "future_apply_required"),
        ("A3", "Create inactive candidate Data Dictionary root", "future_apply_required"),
        ("A4", "Copy x64 proof DBFs plus memo/x64 sidecars into candidate root only", "future_apply_required"),
        ("A5", "Validate candidate DBF readback as v64", "future_apply_required"),
        ("A6", "Rebuild candidate CDX and LMDB mirrors", "future_apply_required"),
        ("A7", "Run DDICT smoke against candidate/resolver bridge", "future_apply_required"),
        ("A8", "Switch or replace active root only after explicit later authorization", "not_implemented_in_v0"),
        ("A9", "Run post-switch DDICT smoke", "future_apply_required"),
        ("A10", "Prove rollback path", "future_apply_required"),
        ("A11", "Closeout manifest and SelfDoc/MDO handoff", "future_apply_required"),
    ]
    wc(gen / "dd096za_guarded_apply_design_steps.csv",
       [{"step_id": a, "step": b, "status": c} for a, b, c in apply_steps],
       ["step_id", "step", "status"])

    file_plan = [
        ("active_dbf_root", "dottalkpp/data/datadict", 1, 1, 0),
        ("active_index_root", "dottalkpp/data/indexes/datadict", 1, 1, 0),
        ("active_lmdb_root", "dottalkpp/data/lmdb/datadict", 1, 1, 0),
        ("workspace_schema", "dottalkpp/data/workspaces/ddbase.dtschema", 1, 1, 0),
        ("sandbox_proof_dbf_root", "dottalkpp/data/dbf/sandbox", 0, 0, 0),
        ("sandbox_proof_index_root", "dottalkpp/data/indexes/sandbox", 0, 0, 0),
        ("sandbox_proof_lmdb_root", "dottalkpp/data/lmdb/sandbox", 0, 0, 0),
    ]
    wc(gen / "dd096za_file_family_plan.csv",
       [{"family": a, "path": b, "backup_required": c, "candidate_required": d, "active_replace_in_v0": e} for a, b, c, d, e in file_plan],
       ["family", "path", "backup_required", "candidate_required", "active_replace_in_v0"])

    table_map = [
        ("DDRUN", "DATA_DICTIONARY_RUNS", "compatibility bridge needed"),
        ("DDOBJECT", "DATA_DICTIONARY_OBJECTS", "DDICT resolver/alias needed"),
        ("DDATTR", "DATA_DICTIONARY_OBJECT_ATTRIBUTES", "long fields and widened values"),
        ("DDEDGE", "DATA_DICTIONARY_RELATION_EDGES", "relation reader update needed"),
        ("DDEVID", "DATA_DICTIONARY_EVIDENCE_RECORDS", "evidence reader update needed"),
        ("DDGATE", "DATA_DICTIONARY_GATE_RECORDS", "gate reader update needed"),
    ]
    wc(gen / "dd096za_old_to_x64_table_map.csv",
       [{"old_table": a, "new_x64_table": b, "policy": c} for a, b, c in table_map],
       ["old_table", "new_x64_table", "policy"])

    decisions = [
        ("COMPAT-001", "Do not switch DDICT directly to long table names until resolver/alias layer is proven."),
        ("COMPAT-002", "Preserve or bridge old DD* surfaces during transition."),
        ("COMPAT-003", "Regenerate CDX/LMDB in candidate/active roots; do not blindly copy from SANDBOX."),
        ("COMPAT-004", "Keep HELP/CMDHELPCHK apply separate in DD092D."),
        ("COMPAT-005", "DD096Z-A v0 is design only and performs no active replacement."),
    ]
    wc(gen / "dd096za_compatibility_decision_register.csv",
       [{"decision_id": a, "recommended_decision": b} for a, b in decisions],
       ["decision_id", "recommended_decision"])

    future_gates = [
        ("DD096YQ green", 1),
        ("DD096Z promotion plan ready", 1),
        ("Backup manifest green", 0),
        ("Candidate root readback green", 0),
        ("Candidate CDX/LMDB rebuild green", 0),
        ("Candidate DDICT smoke green", 0),
        ("Rollback proof green", 0),
        ("Explicit active replacement authorization", 0),
    ]
    wc(gen / "dd096za_future_apply_gates.csv",
       [{"gate": a, "checked_in_v0": b} for a, b in future_gates],
       ["gate", "checked_in_v0"])

    apply_skeleton = (
        "# DD096Z-A guarded apply skeleton v0\n"
        "# Design only. Refuses active catalog replacement.\n"
        "param([string]$RepoRoot = \"D:\\code\\ccode\", [string]$PromotionToken = \"\")\n"
        "Write-Host \"DD096Z-A guarded apply skeleton v0\"\n"
        "Write-Host \"REFUSING ACTIVE REPLACEMENT: DD096Z-A is design-only.\"\n"
        "Write-Host \"No DBFs, CDX, LMDB, workspace schemas, source, HELP, or manuals were changed.\"\n"
        "if ($PromotionToken -ne \"\") { throw \"Active replacement is not implemented in DD096Z-A v0.\" }\n"
        "exit 0\n"
    )
    rollback_skeleton = (
        "# DD096Z-A rollback skeleton v0\n"
        "Write-Host \"Design only; no rollback action performed.\"\n"
        "exit 0\n"
    )
    wt(gen / "skeletons/invoke_dd096za_guarded_apply_skeleton.ps1", apply_skeleton)
    wt(gen / "skeletons/invoke_dd096za_rollback_skeleton.ps1", rollback_skeleton)

    boundaries = [
        ("apply_package_design_only", 1, 1, 1),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("source_edits", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096za_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a, b, c, d in boundaries],
       ["boundary", "observed", "required", "pass"])

    status = "DD096ZA_GUARDED_APPLY_PACKAGE_DESIGN_READY" if blockers == 0 else "DD096ZA_GUARDED_APPLY_PACKAGE_DESIGN_REVIEW"
    wc(out / "dd096za_gate_ledger.csv", [
        {"gate": "preconditions_ready", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "active_replacement_implemented", "expected": 0, "observed": 0, "pass": 1},
        {"gate": "design_artifacts_written", "expected": 1, "observed": 1, "pass": 1},
    ], ["gate", "expected", "observed", "pass"])

    report = f"""# DD096Z-A Guarded Apply-Package Design

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-A converts the green DD096YQ + DD096Z proof chain into a guarded apply-package design.

It does not replace the active Data Dictionary catalog.

## Current status

- Precondition blockers: **{blockers}**
- Active catalog replacement: **0**
- Active DBF copy/write: **0**
- Active CDX/LMDB rebuild: **0**
- Workspace schema mutation: **0**

## Next lane

DD096Z-B should be backup plus inactive candidate-root staging. It should still avoid active replacement until candidate readback, CDX/LMDB, DDICT smoke, and rollback are proven.
"""
    wt(out / "DD096ZA_GUARDED_APPLY_PACKAGE_DESIGN_REPORT.md", report)

    manifest = {
        "contract": "dd096za_guarded_apply_package_design_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "active_catalog_replacement": 0,
        "active_catalog_dbf_copy_or_write": 0,
        "active_cdx_lmdb_rebuild": 0,
        "workspace_schema_mutation": 0,
        "failures": blockers,
        "next_recommended_action": "DD096Z-B backup and inactive candidate-root staging; no active replacement yet.",
    }
    wj(out / "dd096za_guarded_apply_package_design_manifest.json", manifest)

    print(f"DD096Z-A guarded apply-package design manifest: {out / 'dd096za_guarded_apply_package_design_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; active_catalog_replacement: 0; active_dbf_writes: 0; failures: {blockers}")
    return 2 if (args.fail_on_review and blockers) else 0

if __name__ == "__main__":
    raise SystemExit(main())
