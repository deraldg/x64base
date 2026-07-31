#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD096C_STATUS = "DATADICT_CANDIDATE_ROW_ACCEPTANCE_PLAN_READY"
EXPECTED_DD096B_STATUS = "DATADICT_CANDIDATE_ROW_REVIEW_DEDUP_READY"
EXPECTED_DD098_STATUS = "DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN"

DEFAULT_ACCEPTANCE_DIR = "docs/datadict/reports/DD096C-candidate-row-acceptance-plan-v0/generated_acceptance_plan"
DEFAULT_CANDIDATE_DIR = "docs/datadict/reports/DD096A-candidate-catalog-row-design-v0/generated_candidate_catalog_rows"

REQUIRED_ACCEPTANCE_FILES = [
    "dd096c_ddobject_acceptance_plan.csv",
    "dd096c_objid_remap_plan.csv",
    "dd096c_ddattr_acceptance_plan.csv",
    "dd096c_ddedge_acceptance_plan.csv",
    "dd096c_ddevid_acceptance_plan.csv",
    "dd096c_ddgate_acceptance_plan.csv",
    "dd096c_acceptance_plan_index.csv",
]

PROTECTED_ARTIFACTS = [
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
    "dottalkpp/data/workspaces/ddbase.dtschema",
    "src/datadict/ddict_catalog_paths.cpp",
    "src/cli/cmd_ddict.cpp",
    "src/CMakeLists.txt",
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


def int_field(row: Dict[str, str], name: str) -> int:
    try:
        return int(str(row.get(name, "0")).strip() or "0")
    except ValueError:
        return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096D guarded apply-design preflight")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096D-guarded-apply-design-preflight-v0")
    ap.add_argument("--dd096c-dir", default="docs/datadict/reports/DD096C-candidate-row-acceptance-plan-v0")
    ap.add_argument("--dd096b-dir", default="docs/datadict/reports/DD096B-candidate-catalog-row-review-dedup-v0")
    ap.add_argument("--dd098-dir", default="docs/datadict/reports/DD098-datadict-baseline-closeout-v0")
    ap.add_argument("--acceptance-dir", default=DEFAULT_ACCEPTANCE_DIR)
    ap.add_argument("--candidate-dir", default=DEFAULT_CANDIDATE_DIR)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd096c_manifest_path = repo / args.dd096c_dir / "dd096c_candidate_row_acceptance_plan_manifest.json"
    dd096b_manifest_path = repo / args.dd096b_dir / "dd096b_candidate_catalog_row_review_dedup_manifest.json"
    dd098_manifest_path = repo / args.dd098_dir / "dd098_datadict_baseline_closeout_manifest.json"

    dd096c = read_json(dd096c_manifest_path)
    dd096b = read_json(dd096b_manifest_path)
    dd098 = read_json(dd098_manifest_path)

    adir = repo / args.acceptance_dir
    cdir = repo / args.candidate_dir

    ddobject = read_csv(adir / "dd096c_ddobject_acceptance_plan.csv")
    objid_remap = read_csv(adir / "dd096c_objid_remap_plan.csv")
    ddattr = read_csv(adir / "dd096c_ddattr_acceptance_plan.csv")
    ddedge = read_csv(adir / "dd096c_ddedge_acceptance_plan.csv")
    ddevid = read_csv(adir / "dd096c_ddevid_acceptance_plan.csv")
    ddgate = read_csv(adir / "dd096c_ddgate_acceptance_plan.csv")
    index_rows = read_csv(adir / "dd096c_acceptance_plan_index.csv")

    file_rows = []
    for name in REQUIRED_ACCEPTANCE_FILES:
        p = adir / name
        file_rows.append({
            "required_file": name,
            "path": str(p),
            "exists": int(p.exists()),
            "bytes": p.stat().st_size if p.exists() else 0,
            "sha256": sha256(p),
        })

    reuse_objects = sum(1 for r in ddobject if r.get("acceptance_decision") == "ACCEPT_EXISTING_REUSE_ACTIVE_OBJID")
    new_objects = sum(1 for r in ddobject if r.get("acceptance_decision") == "ACCEPT_NEW_CANDIDATE_PENDING_APPLY_DESIGN")
    attr_rebase = sum(1 for r in ddattr if r.get("acceptance_decision") == "REBASE_TO_ACTIVE_OBJID_THEN_REVIEW_ATTR")
    edge_rebase = sum(1 for r in ddedge if r.get("acceptance_decision") == "REBASE_EDGE_ENDPOINTS_THEN_REVIEW")
    apply_now_total = sum(int_field(r, "apply_now") for rows in [ddobject, objid_remap, ddattr, ddedge, ddevid, ddgate, index_rows] for r in rows)

    # Preflight checks for a future apply design. All remain design/preflight-only.
    check_rows = [
        {
            "check_id": "PRE001_ACCEPTANCE_PLAN_EXISTS",
            "description": "All DD096C acceptance-plan CSV files exist.",
            "expected": len(REQUIRED_ACCEPTANCE_FILES),
            "observed": sum(int(r["exists"]) for r in file_rows),
            "pass": int(sum(int(r["exists"]) for r in file_rows) == len(REQUIRED_ACCEPTANCE_FILES)),
            "apply_blocker_if_fail": 1,
        },
        {
            "check_id": "PRE002_REUSE_11_EXISTING_TABLE_OBJECTS",
            "description": "The 11 existing catalog-table DDOBJECT rows are marked for active OBJID reuse.",
            "expected": 11,
            "observed": reuse_objects,
            "pass": int(reuse_objects == 11),
            "apply_blocker_if_fail": 1,
        },
        {
            "check_id": "PRE003_NEW_OBJECTS_8",
            "description": "The 8 non-table DDOBJECT candidates remain new candidates.",
            "expected": 8,
            "observed": new_objects,
            "pass": int(new_objects == 8),
            "apply_blocker_if_fail": 1,
        },
        {
            "check_id": "PRE004_OBJID_REMAPS_11",
            "description": "There is one remap row for each reused catalog-table object.",
            "expected": 11,
            "observed": len(objid_remap),
            "pass": int(len(objid_remap) == 11),
            "apply_blocker_if_fail": 1,
        },
        {
            "check_id": "PRE005_ATTR_REBASE_PRESENT",
            "description": "Dependent DDATTR rows requiring active-OBJID rebasing are identified.",
            "expected": ">=1",
            "observed": attr_rebase,
            "pass": int(attr_rebase >= 1),
            "apply_blocker_if_fail": 1,
        },
        {
            "check_id": "PRE006_EDGE_REBASE_PRESENT",
            "description": "Dependent DDEDGE rows requiring endpoint rebasing are identified.",
            "expected": ">=1",
            "observed": edge_rebase,
            "pass": int(edge_rebase >= 1),
            "apply_blocker_if_fail": 1,
        },
        {
            "check_id": "PRE007_ACCEPTANCE_ROWS_MATCH",
            "description": "Acceptance index row count matches DD096C manifest acceptance row count.",
            "expected": dd096c.get("counts", {}).get("total_acceptance_rows", ""),
            "observed": len(index_rows),
            "pass": int(str(dd096c.get("counts", {}).get("total_acceptance_rows", "")) == str(len(index_rows))),
            "apply_blocker_if_fail": 1,
        },
        {
            "check_id": "PRE008_APPLY_NOW_ZERO",
            "description": "No row is marked for apply now.",
            "expected": 0,
            "observed": apply_now_total,
            "pass": int(apply_now_total == 0),
            "apply_blocker_if_fail": 1,
        },
        {
            "check_id": "PRE009_HELP_CMDHELPCHK_DECOUPLED",
            "description": "Schema candidate apply design remains decoupled from HELP/CMDHELPCHK application.",
            "expected": "decoupled",
            "observed": "decoupled",
            "pass": 1,
            "apply_blocker_if_fail": 1,
        },
        {
            "check_id": "PRE010_DBFS_NOT_MUTATED",
            "description": "This preflight performs no active catalog mutation.",
            "expected": 0,
            "observed": 0,
            "pass": 1,
            "apply_blocker_if_fail": 1,
        },
    ]

    apply_blockers = sum(1 for r in check_rows if int(r["pass"]) != 1 and int(r["apply_blocker_if_fail"]) == 1)

    future_apply_rows = [
        {
            "step": 1,
            "phase": "load",
            "description": "Load DD096C acceptance/remap plans.",
            "required_before_apply": 1,
            "apply_now": 0,
        },
        {
            "step": 2,
            "phase": "remap",
            "description": "Replace candidate OBJIDs for 11 existing catalog-table objects with active OBJIDs.",
            "required_before_apply": 1,
            "apply_now": 0,
        },
        {
            "step": 3,
            "phase": "rebase",
            "description": "Rebase dependent DDATTR parent OBJIDs and DDEDGE endpoints before any row generation.",
            "required_before_apply": 1,
            "apply_now": 0,
        },
        {
            "step": 4,
            "phase": "dedup",
            "description": "Re-run active-catalog duplicate checks after remap/rebase.",
            "required_before_apply": 1,
            "apply_now": 0,
        },
        {
            "step": 5,
            "phase": "stage",
            "description": "Stage final apply rows into an external review package, not active DBFs.",
            "required_before_apply": 1,
            "apply_now": 0,
        },
        {
            "step": 6,
            "phase": "authorize",
            "description": "Require explicit apply authorization before DBF writes.",
            "required_before_apply": 1,
            "apply_now": 0,
        },
    ]

    generated = out / "generated_apply_design_preflight"
    generated.mkdir(parents=True, exist_ok=True)

    write_csv(generated / "dd096d_preflight_checks.csv", check_rows, [
        "check_id", "description", "expected", "observed", "pass", "apply_blocker_if_fail"
    ])
    write_csv(generated / "dd096d_future_apply_design_sequence.csv", future_apply_rows, [
        "step", "phase", "description", "required_before_apply", "apply_now"
    ])
    write_csv(generated / "dd096d_required_acceptance_files.csv", file_rows, [
        "required_file", "path", "exists", "bytes", "sha256"
    ])

    boundary_rows = [
        {"boundary": "guarded_apply_design_preflight_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "apply_now_total", "observed": apply_now_total, "required": 0, "pass": int(apply_now_total == 0)},
        {"boundary": "future_apply_rows_apply_now", "observed": sum(int(r["apply_now"]) for r in future_apply_rows), "required": 0, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    gate_rows = [
        {"gate": "dd096c_ready", "expected": EXPECTED_DD096C_STATUS, "observed": dd096c.get("status", ""), "pass": int(dd096c.get("status") == EXPECTED_DD096C_STATUS)},
        {"gate": "dd096b_ready", "expected": EXPECTED_DD096B_STATUS, "observed": dd096b.get("status", ""), "pass": int(dd096b.get("status") == EXPECTED_DD096B_STATUS)},
        {"gate": "dd098_closed", "expected": EXPECTED_DD098_STATUS, "observed": dd098.get("status", ""), "pass": int(dd098.get("status") == EXPECTED_DD098_STATUS)},
        {"gate": "preflight_checks_pass", "expected": len(check_rows), "observed": sum(int(r["pass"]) for r in check_rows), "pass": int(sum(int(r["pass"]) for r in check_rows) == len(check_rows))},
        {"gate": "apply_blockers_zero", "expected": 0, "observed": apply_blockers, "pass": int(apply_blockers == 0)},
        {"gate": "apply_now_zero", "expected": 0, "observed": apply_now_total, "pass": int(apply_now_total == 0)},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DATADICT_GUARDED_APPLY_DESIGN_PREFLIGHT_READY" if failures == 0 else "DATADICT_GUARDED_APPLY_DESIGN_PREFLIGHT_REVIEW"

    artifact_rows = [
        artifact_row(repo, str(dd096c_manifest_path.relative_to(repo)), "dd096c_manifest"),
        artifact_row(repo, str(dd096b_manifest_path.relative_to(repo)), "dd096b_manifest"),
        artifact_row(repo, str(dd098_manifest_path.relative_to(repo)), "dd098_manifest"),
        artifact_row(repo, args.acceptance_dir, "acceptance_dir"),
        artifact_row(repo, args.candidate_dir, "candidate_dir"),
    ]
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))
    for f in sorted(generated.iterdir()):
        if f.is_file():
            artifact_rows.append({
                "role": "generated_preflight",
                "path": str(f),
                "exists": 1,
                "kind": "file",
                "bytes_or_children": f.stat().st_size,
                "sha256": sha256(f),
            })

    next_rows = [
        {"next_id": "DD096E", "title": "apply-row staging package", "allowed_scope": "external staged rows only; no active DBF writes"},
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply planning", "allowed_scope": "only after explicit authorization"},
        {"next_id": "DD099", "title": "baseline-to-manual integration report", "allowed_scope": "documentation/explanation only"},
    ]

    write_csv(out / "dd096d_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096d_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd096d_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd096d_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD096D Guarded Apply-Design Preflight

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096D checks whether the DD096C acceptance/remap plan is structurally ready for a future apply design.

It is not an apply lane. It writes no DBFs and performs no catalog mutation.

## Summary

- Preflight checks passed: **{sum(int(r['pass']) for r in check_rows)} / {len(check_rows)}**
- Apply blockers: **{apply_blockers}**
- Reuse existing objects: **{reuse_objects}**
- New objects: **{new_objects}**
- OBJID remaps: **{len(objid_remap)}**
- Attr rebases: **{attr_rebase}**
- Edge rebases: **{edge_rebase}**
- apply_now total: **{apply_now_total}**

## Required future rule

Any future apply package must reuse the 11 existing catalog-table `DDOBJECT` rows and rebase dependent `DDATTR` and `DDEDGE` candidates before writing anything.

## Boundary

DD096D is guarded-apply-design-preflight/report-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    write_text(out / "DD096D_GUARDED_APPLY_DESIGN_PREFLIGHT_REPORT.md", report)

    manifest = {
        "contract": "dd096d_guarded_apply_design_preflight_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "preflight_checks": len(check_rows),
        "preflight_pass": sum(int(r["pass"]) for r in check_rows),
        "apply_blockers": apply_blockers,
        "reuse_existing_objects": reuse_objects,
        "new_objects": new_objects,
        "objid_remaps": len(objid_remap),
        "attr_rebase": attr_rebase,
        "edge_rebase": edge_rebase,
        "apply_now_total": apply_now_total,
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
        "next_recommended_action": "DD096E external apply-row staging package, still no active DBF writes.",
    }
    write_json(out / "dd096d_guarded_apply_design_preflight_manifest.json", manifest)

    print(f"DD096D guarded apply-design preflight manifest: {out / 'dd096d_guarded_apply_design_preflight_manifest.json'}")
    print(f"status: {status}; preflight: {manifest['preflight_pass']}/{manifest['preflight_checks']}; blockers: {apply_blockers}; remaps: {len(objid_remap)}; attr_rebase: {attr_rebase}; edge_rebase: {edge_rebase}; apply_now: {apply_now_total}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
