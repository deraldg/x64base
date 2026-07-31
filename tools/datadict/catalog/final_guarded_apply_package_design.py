#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD096F_STATUS = "DATADICT_STAGED_ROW_SIMULATED_APPLY_VALIDATION_READY"
EXPECTED_DD096E_STATUS = "DATADICT_EXTERNAL_APPLY_ROW_STAGING_READY"
EXPECTED_DD096D_STATUS = "DATADICT_GUARDED_APPLY_DESIGN_PREFLIGHT_READY"
EXPECTED_DD098_STATUS = "DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN"

DEFAULT_STAGED_DIR = "docs/datadict/reports/DD096E-R-root-aware-external-apply-staging-v0/generated_staged_apply_rows"
DEFAULT_SIM_DIR = "docs/datadict/reports/DD096F-R-root-aware-staged-row-simulated-apply-v0/generated_simulated_apply_validation"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except Exception as exc:
        return {"_read_error": str(exc)}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Dict[str, object]) -> None:
    write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: List[Dict[str, object]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_row(repo: Path, rel_path: str, role: str) -> Dict[str, object]:
    p = repo / rel_path
    return {
        "role": role,
        "path": rel_path,
        "exists": int(p.exists()),
        "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
        "bytes_or_children": p.stat().st_size if p.exists() and p.is_file() else sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else 0,
        "sha256": sha256(p),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096G final guarded apply package design")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096G-final-guarded-apply-package-design-v0")
    ap.add_argument("--dd096f-dir", default="docs/datadict/reports/DD096F-R-root-aware-staged-row-simulated-apply-v0")
    ap.add_argument("--dd096e-dir", default="docs/datadict/reports/DD096E-R-root-aware-external-apply-staging-v0")
    ap.add_argument("--dd096d-dir", default="docs/datadict/reports/DD096D-R-root-aware-guarded-apply-preflight-v0")
    ap.add_argument("--dd098-dir", default="docs/datadict/reports/DD098-datadict-baseline-closeout-v0")
    ap.add_argument("--staged-dir", default=DEFAULT_STAGED_DIR)
    ap.add_argument("--sim-dir", default=DEFAULT_SIM_DIR)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    f_manifest_path = repo / args.dd096f_dir / "dd096f_staged_row_review_simulated_apply_manifest.json"
    e_manifest_path = repo / args.dd096e_dir / "dd096e_external_apply_row_staging_manifest.json"
    d_manifest_path = repo / args.dd096d_dir / "dd096d_guarded_apply_design_preflight_manifest.json"
    z_manifest_path = repo / args.dd098_dir / "dd098_datadict_baseline_closeout_manifest.json"

    f_manifest = read_json(f_manifest_path)
    e_manifest = read_json(e_manifest_path)
    d_manifest = read_json(d_manifest_path)
    z_manifest = read_json(z_manifest_path)

    staged_dir = repo / args.staged_dir
    sim_dir = repo / args.sim_dir

    target_counts = read_csv(sim_dir / "dd096f_target_row_counts.csv")
    validation_ledger = read_csv(sim_dir / "dd096f_validation_ledger.csv")
    duplicate_risk = read_csv(sim_dir / "dd096f_ddobject_duplicate_risk.csv")
    ref_validation = read_csv(sim_dir / "dd096f_reference_validation.csv")

    staged_index = read_csv(staged_dir / "dd096e_staged_apply_row_index.csv")
    suppressed_objects = read_csv(staged_dir / "dd096e_suppressed_existing_ddobject_rows.csv")

    validation_failures = sum(1 for r in validation_ledger if str(r.get("pass", "")).strip() != "1")
    duplicate_blockers = sum(1 for r in duplicate_risk if str(r.get("active_duplicate_seen", "")).strip() == "1")
    reference_failures = sum(1 for r in ref_validation if str(r.get("reference_ok", "")).strip() != "1")
    staged_total = len(staged_index)
    suppressed_total = len(suppressed_objects)

    generated = out / "generated_guarded_apply_design"
    generated.mkdir(parents=True, exist_ok=True)

    apply_sequence = [
        {
            "step": 1,
            "phase": "freeze_inputs",
            "description": "Pin DD096E-R staged row hashes and DD096F-R validation outputs before any future apply run.",
            "write_action": 0,
            "requires_explicit_authorization": 1,
        },
        {
            "step": 2,
            "phase": "backup",
            "description": "Create timestamped backups of active target DBFs, CDXs, and LMDB environments before any future write.",
            "write_action": 0,
            "requires_explicit_authorization": 1,
        },
        {
            "step": 3,
            "phase": "open_exclusive_or_abort",
            "description": "Future apply must open target DBFs in a guarded/exclusive mutation mode or abort.",
            "write_action": 0,
            "requires_explicit_authorization": 1,
        },
        {
            "step": 4,
            "phase": "verify_suppression",
            "description": "Confirm the 11 existing catalog-table DDOBJECT rows remain suppressed from insertion.",
            "write_action": 0,
            "requires_explicit_authorization": 1,
        },
        {
            "step": 5,
            "phase": "append_staged_rows",
            "description": "Future authorized apply would append only staged rows after all prechecks pass.",
            "write_action": 0,
            "requires_explicit_authorization": 1,
        },
        {
            "step": 6,
            "phase": "rebuild_verify_indexes",
            "description": "Future authorized apply would rebuild/verify CDX and LMDB for affected tables after DBF writes.",
            "write_action": 0,
            "requires_explicit_authorization": 1,
        },
        {
            "step": 7,
            "phase": "runtime_smoke",
            "description": "Future authorized apply must run DDICT STATUS/TABLES/TAGS/REL/EVIDENCE smoke and compare expected counts.",
            "write_action": 0,
            "requires_explicit_authorization": 1,
        },
        {
            "step": 8,
            "phase": "closeout_or_rollback",
            "description": "Close out only if runtime smoke is green; otherwise restore backups and document rollback.",
            "write_action": 0,
            "requires_explicit_authorization": 1,
        },
    ]
    write_csv(generated / "dd096g_guarded_apply_sequence_design.csv", apply_sequence, [
        "step", "phase", "description", "write_action", "requires_explicit_authorization"
    ])

    go_no_go = [
        {"gate": "DD096F_R_GREEN", "question": "Is DD096F-R simulated apply validation READY?", "required": EXPECTED_DD096F_STATUS, "observed": f_manifest.get("status", ""), "pass": int(f_manifest.get("status") == EXPECTED_DD096F_STATUS), "go_required": 1},
        {"gate": "DD096E_R_GREEN", "question": "Is DD096E-R external staging READY?", "required": EXPECTED_DD096E_STATUS, "observed": e_manifest.get("status", ""), "pass": int(e_manifest.get("status") == EXPECTED_DD096E_STATUS), "go_required": 1},
        {"gate": "DD096D_R_GREEN", "question": "Is DD096D-R preflight READY?", "required": EXPECTED_DD096D_STATUS, "observed": d_manifest.get("status", ""), "pass": int(d_manifest.get("status") == EXPECTED_DD096D_STATUS), "go_required": 1},
        {"gate": "DD098_CLOSED", "question": "Is the baseline closeout still green?", "required": EXPECTED_DD098_STATUS, "observed": z_manifest.get("status", ""), "pass": int(z_manifest.get("status") == EXPECTED_DD098_STATUS), "go_required": 1},
        {"gate": "VALIDATION_FAILURES_ZERO", "question": "Are DD096F-R validation failures zero?", "required": 0, "observed": validation_failures, "pass": int(validation_failures == 0), "go_required": 1},
        {"gate": "DUPLICATE_BLOCKERS_ZERO", "question": "Are staged DDOBJECT duplicate blockers zero?", "required": 0, "observed": duplicate_blockers, "pass": int(duplicate_blockers == 0), "go_required": 1},
        {"gate": "REFERENCE_FAILURES_ZERO", "question": "Are staged DDATTR/DDEDGE reference failures zero?", "required": 0, "observed": reference_failures, "pass": int(reference_failures == 0), "go_required": 1},
        {"gate": "STAGED_ROWS_158", "question": "Are 158 external staged rows present?", "required": 158, "observed": staged_total, "pass": int(staged_total == 158), "go_required": 1},
        {"gate": "SUPPRESSED_OBJECTS_11", "question": "Are 11 existing DDOBJECT table rows suppressed from insertion?", "required": 11, "observed": suppressed_total, "pass": int(suppressed_total == 11), "go_required": 1},
        {"gate": "AUTHORIZATION_NOT_PRESENT", "question": "Has active DBF apply been explicitly authorized?", "required": "NOT_AUTHORIZED", "observed": "NOT_AUTHORIZED", "pass": 1, "go_required": 0},
    ]
    write_csv(generated / "dd096g_go_no_go_checklist.csv", go_no_go, ["gate", "question", "required", "observed", "pass", "go_required"])

    authorization_template = [
        {"field": "authorization_status", "value": "NOT_AUTHORIZED"},
        {"field": "authorized_by", "value": ""},
        {"field": "authorized_utc", "value": ""},
        {"field": "authorized_scope", "value": "none"},
        {"field": "permitted_target_tables", "value": ""},
        {"field": "rollback_required", "value": "yes"},
        {"field": "notes", "value": "DD096G is design-only. Do not treat this as apply authorization."},
    ]
    write_csv(generated / "dd096g_apply_authorization_template.csv", authorization_template, ["field", "value"])

    write_guard_policy = [
        {"policy_id": "WRITE001", "rule": "No active DBF write may occur in DD096G.", "required": 1, "observed": 1, "pass": 1},
        {"policy_id": "WRITE002", "rule": "Future apply requires explicit authorization after DD096G.", "required": 1, "observed": 1, "pass": 1},
        {"policy_id": "WRITE003", "rule": "Future apply must suppress 11 existing DDOBJECT table-object rows.", "required": 11, "observed": suppressed_total, "pass": int(suppressed_total == 11)},
        {"policy_id": "WRITE004", "rule": "Future apply must preserve HELP/CMDHELPCHK decoupling.", "required": "decoupled", "observed": "decoupled", "pass": 1},
        {"policy_id": "WRITE005", "rule": "Future apply must backup before write and validate after write.", "required": 1, "observed": 1, "pass": 1},
    ]
    write_csv(generated / "dd096g_write_guard_policy.csv", write_guard_policy, ["policy_id", "rule", "required", "observed", "pass"])

    rollback_design = [
        {"step": 1, "rollback_action": "Restore pre-apply DBF backups for DDOBJECT, DDATTR, DDEDGE, DDEVID, and DDGATE.", "required": 1},
        {"step": 2, "rollback_action": "Restore or rebuild associated CDX artifacts from backup/source state.", "required": 1},
        {"step": 3, "rollback_action": "Restore or rebuild associated LMDB environments from backup/source state.", "required": 1},
        {"step": 4, "rollback_action": "Rerun DDICT STATUS/TABLES/TAGS/REL/EVIDENCE baseline smoke.", "required": 1},
        {"step": 5, "rollback_action": "Write rollback incident report and do not continue apply chain.", "required": 1},
    ]
    write_csv(generated / "dd096g_rollback_design.csv", rollback_design, ["step", "rollback_action", "required"])

    write_csv(generated / "dd096g_target_row_counts_from_simulation.csv", target_counts, [
        "target_table", "staged_rows", "suppressed_existing_rows", "simulated_insert_rows", "apply_now"
    ])

    authorization_present = False
    go_required_failures = sum(1 for r in go_no_go if int(r["go_required"]) == 1 and int(r["pass"]) != 1)
    policy_failures = sum(1 for r in write_guard_policy if int(r["pass"]) != 1)
    sequence_write_actions = sum(1 for r in apply_sequence if int(r["write_action"]) != 0)

    boundary_rows = [
        {"boundary": "final_apply_package_design_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "authorization_present", "observed": int(authorization_present), "required": 0, "pass": 1},
        {"boundary": "sequence_write_actions", "observed": sequence_write_actions, "required": 0, "pass": int(sequence_write_actions == 0)},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    gates = [
        {"gate": "all_go_required_pass", "expected": 0, "observed": go_required_failures, "pass": int(go_required_failures == 0)},
        {"gate": "write_guard_policy_pass", "expected": 0, "observed": policy_failures, "pass": int(policy_failures == 0)},
        {"gate": "no_write_actions_in_design", "expected": 0, "observed": sequence_write_actions, "pass": int(sequence_write_actions == 0)},
        {"gate": "authorization_not_present", "expected": 0, "observed": int(authorization_present), "pass": 1},
        {"gate": "staged_rows_158", "expected": 158, "observed": staged_total, "pass": int(staged_total == 158)},
        {"gate": "suppressed_objects_11", "expected": 11, "observed": suppressed_total, "pass": int(suppressed_total == 11)},
    ]
    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DATADICT_FINAL_GUARDED_APPLY_PACKAGE_DESIGN_READY" if failures == 0 else "DATADICT_FINAL_GUARDED_APPLY_PACKAGE_DESIGN_REVIEW"

    write_csv(out / "dd096g_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096g_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd096g_artifact_ledger.csv", [
        artifact_row(repo, str(f_manifest_path.relative_to(repo)), "dd096f_manifest"),
        artifact_row(repo, str(e_manifest_path.relative_to(repo)), "dd096e_manifest"),
        artifact_row(repo, str(d_manifest_path.relative_to(repo)), "dd096d_manifest"),
        artifact_row(repo, str(z_manifest_path.relative_to(repo)), "dd098_manifest"),
        artifact_row(repo, args.staged_dir, "staged_dir"),
        artifact_row(repo, args.sim_dir, "simulation_dir"),
        artifact_row(repo, str(generated.relative_to(repo)) if str(generated).startswith(str(repo)) else str(generated), "generated_design_dir"),
    ], ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])

    write_csv(out / "dd096g_next_lane_recommendations.csv", [
        {"next_id": "DD096H", "title": "apply authorization record / go-no-go checkpoint", "allowed_scope": "authorization record only; no DBF writes"},
        {"next_id": "DD096I", "title": "guarded DBF apply", "allowed_scope": "only if explicitly authorized"},
        {"next_id": "DD099", "title": "baseline-to-manual integration report", "allowed_scope": "documentation/explanation only"},
    ], ["next_id", "title", "allowed_scope"])

    report = f"""# DD096G Final Guarded Apply Package Design

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096G designs the final guarded apply package shape for the Data Dictionary schema-promotion lane.

It is **not** an authorization and **not** an apply lane. It writes no active DBFs.

## Design summary

- Staged rows available: **{staged_total}**
- Suppressed existing DDOBJECT rows: **{suppressed_total}**
- Validation failures: **{validation_failures}**
- Duplicate blockers: **{duplicate_blockers}**
- Reference failures: **{reference_failures}**
- Go-required failures: **{go_required_failures}**
- Write policy failures: **{policy_failures}**
- Authorization status: **NOT_AUTHORIZED**

## Important boundary

DD096G intentionally emits no write-capable apply script. A future DD096H authorization record must be explicit before a DD096I guarded DBF apply package may exist.

## Boundary

DD096G is final-apply-package-design/report-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    write_text(out / "DD096G_FINAL_GUARDED_APPLY_PACKAGE_DESIGN_REPORT.md", report)

    manifest = {
        "contract": "dd096g_final_guarded_apply_package_design_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "staged_rows": staged_total,
        "suppressed_existing_objects": suppressed_total,
        "validation_failures": validation_failures,
        "duplicate_blockers": duplicate_blockers,
        "reference_failures": reference_failures,
        "go_required_failures": go_required_failures,
        "policy_failures": policy_failures,
        "authorization_status": "NOT_AUTHORIZED",
        "failures": failures,
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD096H apply authorization record / go-no-go checkpoint. Do not create DD096I apply package without explicit authorization.",
    }
    write_json(out / "dd096g_final_guarded_apply_package_design_manifest.json", manifest)

    print(f"DD096G final guarded apply package design manifest: {out / 'dd096g_final_guarded_apply_package_design_manifest.json'}")
    print(f"status: {status}; staged_rows: {staged_total}; suppressed_objects: {suppressed_total}; validation_failures: {validation_failures}; duplicate_blockers: {duplicate_blockers}; ref_failures: {reference_failures}; authorization: NOT_AUTHORIZED; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
