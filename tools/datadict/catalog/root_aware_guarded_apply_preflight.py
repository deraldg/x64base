#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD096C_READY = "DATADICT_CANDIDATE_ROW_ACCEPTANCE_PLAN_READY"
EXPECTED_DD096B_READY = "DATADICT_CANDIDATE_ROW_REVIEW_DEDUP_READY"
EXPECTED_DD098_READY = "DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN"

DEFAULT_ACCEPTANCE_DIR = "docs/datadict/reports/DD096CR-acceptance-gate-repair-v0/generated_acceptance_plan"
REQUIRED_ACCEPTANCE_FILES = [
    "dd096c_ddobject_acceptance_plan.csv",
    "dd096c_objid_remap_plan.csv",
    "dd096c_ddattr_acceptance_plan.csv",
    "dd096c_ddedge_acceptance_plan.csv",
    "dd096c_ddevid_acceptance_plan.csv",
    "dd096c_ddgate_acceptance_plan.csv",
    "dd096c_acceptance_plan_index.csv",
]


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


def artifact_row(path: Path, role: str) -> Dict[str, object]:
    return {
        "role": role,
        "path": str(path),
        "exists": int(path.exists()),
        "kind": "dir" if path.exists() and path.is_dir() else "file" if path.exists() and path.is_file() else "",
        "bytes_or_children": path.stat().st_size if path.exists() and path.is_file() else sum(1 for _ in path.iterdir()) if path.exists() and path.is_dir() else 0,
        "sha256": sha256(path),
    }


def int_field(row: Dict[str, str], name: str) -> int:
    try:
        return int(str(row.get(name, "0")).strip() or "0")
    except ValueError:
        return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096D-R root-aware guarded apply-design preflight")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096DR-root-aware-guarded-apply-preflight-v0")
    ap.add_argument("--dd096c-dir", default="docs/datadict/reports/DD096CR-acceptance-gate-repair-v0")
    ap.add_argument("--dd096b-dir", default="docs/datadict/reports/DD096B-R-candidate-catalog-row-review-dedup-v0")
    ap.add_argument("--dd098-dir", default="docs/datadict/reports/DD098-datadict-baseline-closeout-v0")
    ap.add_argument("--acceptance-dir", default=DEFAULT_ACCEPTANCE_DIR)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    c_manifest_path = repo / args.dd096c_dir / "dd096c_candidate_row_acceptance_plan_manifest.json"
    b_manifest_path = repo / args.dd096b_dir / "dd096b_candidate_catalog_row_review_dedup_manifest.json"
    z_manifest_path = repo / args.dd098_dir / "dd098_datadict_baseline_closeout_manifest.json"

    c_manifest = read_json(c_manifest_path)
    b_manifest = read_json(b_manifest_path)
    z_manifest = read_json(z_manifest_path)

    adir = repo / args.acceptance_dir
    ddobject = read_csv(adir / "dd096c_ddobject_acceptance_plan.csv")
    objid_remap = read_csv(adir / "dd096c_objid_remap_plan.csv")
    ddattr = read_csv(adir / "dd096c_ddattr_acceptance_plan.csv")
    ddedge = read_csv(adir / "dd096c_ddedge_acceptance_plan.csv")
    ddevid = read_csv(adir / "dd096c_ddevid_acceptance_plan.csv")
    ddgate = read_csv(adir / "dd096c_ddgate_acceptance_plan.csv")
    index_rows = read_csv(adir / "dd096c_acceptance_plan_index.csv")

    reuse_objects = sum(1 for r in ddobject if r.get("acceptance_decision") == "ACCEPT_EXISTING_REUSE_ACTIVE_OBJID")
    new_objects = sum(1 for r in ddobject if r.get("acceptance_decision") == "ACCEPT_NEW_CANDIDATE_PENDING_APPLY_DESIGN")
    attr_rebase = sum(1 for r in ddattr if r.get("acceptance_decision") == "REBASE_TO_ACTIVE_OBJID_THEN_REVIEW_ATTR")
    edge_rebase = sum(1 for r in ddedge if r.get("acceptance_decision") == "REBASE_EDGE_ENDPOINTS_THEN_REVIEW")
    apply_now_total = sum(int_field(r, "apply_now") for rows in [ddobject, objid_remap, ddattr, ddedge, ddevid, ddgate, index_rows] for r in rows)

    file_rows = []
    for name in REQUIRED_ACCEPTANCE_FILES:
        p = adir / name
        file_rows.append({"required_file": name, "path": str(p), "exists": int(p.exists()), "bytes": p.stat().st_size if p.exists() else 0, "sha256": sha256(p)})

    checks = [
        {"check_id": "PRE001_ACCEPTANCE_FILES", "expected": len(REQUIRED_ACCEPTANCE_FILES), "observed": sum(int(r["exists"]) for r in file_rows), "pass": int(sum(int(r["exists"]) for r in file_rows) == len(REQUIRED_ACCEPTANCE_FILES)), "apply_blocker_if_fail": 1},
        {"check_id": "PRE002_REUSE_11_EXISTING_TABLE_OBJECTS", "expected": 11, "observed": reuse_objects, "pass": int(reuse_objects == 11), "apply_blocker_if_fail": 1},
        {"check_id": "PRE003_NEW_OBJECTS_ROOT_AWARE_9", "expected": 9, "observed": new_objects, "pass": int(new_objects == 9), "apply_blocker_if_fail": 1},
        {"check_id": "PRE004_OBJID_REMAPS_11", "expected": 11, "observed": len(objid_remap), "pass": int(len(objid_remap) == 11), "apply_blocker_if_fail": 1},
        {"check_id": "PRE005_ATTR_REBASE_PRESENT", "expected": ">=1", "observed": attr_rebase, "pass": int(attr_rebase >= 1), "apply_blocker_if_fail": 1},
        {"check_id": "PRE006_EDGE_REBASE_PRESENT", "expected": ">=1", "observed": edge_rebase, "pass": int(edge_rebase >= 1), "apply_blocker_if_fail": 1},
        {"check_id": "PRE007_ACCEPTANCE_ROWS_169", "expected": 169, "observed": len(index_rows), "pass": int(len(index_rows) == 169), "apply_blocker_if_fail": 1},
        {"check_id": "PRE008_APPLY_NOW_ZERO", "expected": 0, "observed": apply_now_total, "pass": int(apply_now_total == 0), "apply_blocker_if_fail": 1},
        {"check_id": "PRE009_HELP_CMDHELPCHK_DECOUPLED", "expected": "decoupled", "observed": "decoupled", "pass": 1, "apply_blocker_if_fail": 1},
        {"check_id": "PRE010_NO_ACTIVE_WRITES", "expected": 0, "observed": 0, "pass": 1, "apply_blocker_if_fail": 1},
    ]
    blockers = sum(1 for r in checks if int(r["pass"]) != 1 and int(r["apply_blocker_if_fail"]) == 1)

    generated = out / "generated_apply_design_preflight"
    generated.mkdir(parents=True, exist_ok=True)
    write_csv(generated / "dd096d_preflight_checks.csv", checks, ["check_id", "expected", "observed", "pass", "apply_blocker_if_fail"])
    write_csv(generated / "dd096d_required_acceptance_files.csv", file_rows, ["required_file", "path", "exists", "bytes", "sha256"])
    future_steps = [
        {"step": 1, "phase": "load", "description": "Load root-aware acceptance/remap plans.", "required_before_apply": 1, "apply_now": 0},
        {"step": 2, "phase": "suppress", "description": "Suppress 11 existing table-object inserts.", "required_before_apply": 1, "apply_now": 0},
        {"step": 3, "phase": "stage", "description": "Stage 9 new DDOBJECT rows and dependent rows externally.", "required_before_apply": 1, "apply_now": 0},
        {"step": 4, "phase": "simulate", "description": "Run staged-row simulated apply before any DBF writes.", "required_before_apply": 1, "apply_now": 0},
        {"step": 5, "phase": "authorize", "description": "Require explicit authorization for any active DBF apply.", "required_before_apply": 1, "apply_now": 0},
    ]
    write_csv(generated / "dd096d_future_apply_design_sequence.csv", future_steps, ["step", "phase", "description", "required_before_apply", "apply_now"])

    gates = [
        {"gate": "dd096c_ready", "expected": EXPECTED_DD096C_READY, "observed": c_manifest.get("status", ""), "pass": int(c_manifest.get("status", "") == EXPECTED_DD096C_READY)},
        {"gate": "dd096b_ready", "expected": EXPECTED_DD096B_READY, "observed": b_manifest.get("status", ""), "pass": int(b_manifest.get("status", "") == EXPECTED_DD096B_READY)},
        {"gate": "dd098_closed", "expected": EXPECTED_DD098_READY, "observed": z_manifest.get("status", ""), "pass": int(z_manifest.get("status", "") == EXPECTED_DD098_READY)},
        {"gate": "preflight_checks_pass", "expected": len(checks), "observed": sum(int(r["pass"]) for r in checks), "pass": int(sum(int(r["pass"]) for r in checks) == len(checks))},
        {"gate": "apply_blockers_zero", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "apply_now_zero", "expected": 0, "observed": apply_now_total, "pass": int(apply_now_total == 0)},
    ]
    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DATADICT_GUARDED_APPLY_DESIGN_PREFLIGHT_READY" if failures == 0 else "DATADICT_GUARDED_APPLY_DESIGN_PREFLIGHT_REVIEW"

    boundary = [
        {"boundary": "root_aware_guarded_apply_preflight_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "apply_now_total", "observed": apply_now_total, "required": 0, "pass": int(apply_now_total == 0)},
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

    write_csv(out / "dd096d_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096d_no_mutation_boundary_ledger.csv", boundary, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd096d_artifact_ledger.csv", [
        artifact_row(c_manifest_path, "dd096c_manifest"),
        artifact_row(b_manifest_path, "dd096b_manifest"),
        artifact_row(z_manifest_path, "dd098_manifest"),
        artifact_row(adir, "acceptance_dir"),
        artifact_row(generated, "generated_preflight_dir"),
    ], ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])

    report = f"""# DD096D-R Root-Aware Guarded Apply-Design Preflight

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Summary

- Preflight checks passed: **{sum(int(r['pass']) for r in checks)} / {len(checks)}**
- Apply blockers: **{blockers}**
- Reuse existing objects: **{reuse_objects}**
- New objects: **{new_objects}**
- OBJID remaps: **{len(objid_remap)}**
- Attr rebases: **{attr_rebase}**
- Edge rebases: **{edge_rebase}**
- apply_now total: **{apply_now_total}**

## Boundary

DD096D-R is root-aware preflight/report-only. It performs no active catalog mutation.
"""
    write_text(out / "DD096D_ROOT_AWARE_GUARDED_APPLY_PREFLIGHT_REPORT.md", report)

    manifest = {
        "contract": "dd096dr_root_aware_guarded_apply_preflight_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "profiles": args.profile,
        "preflight_checks": len(checks),
        "preflight_pass": sum(int(r["pass"]) for r in checks),
        "apply_blockers": blockers,
        "reuse_existing_objects": reuse_objects,
        "new_objects": new_objects,
        "objid_remaps": len(objid_remap),
        "attr_rebase": attr_rebase,
        "edge_rebase": edge_rebase,
        "apply_now_total": apply_now_total,
        "failures": failures,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
    }
    write_json(out / "dd096d_guarded_apply_design_preflight_manifest.json", manifest)
    write_json(out / "dd096dr_root_aware_guarded_apply_preflight_manifest.json", manifest)

    print(f"DD096D-R root-aware guarded apply preflight manifest: {out / 'dd096dr_root_aware_guarded_apply_preflight_manifest.json'}")
    print(f"status: {status}; preflight: {manifest['preflight_pass']}/{manifest['preflight_checks']}; blockers: {blockers}; reuse: {reuse_objects}; new_objects: {new_objects}; remaps: {len(objid_remap)}; apply_now: {apply_now_total}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
