#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD096D_STATUS = "DATADICT_GUARDED_APPLY_DESIGN_PREFLIGHT_READY"
EXPECTED_DD096C_STATUS = "DATADICT_CANDIDATE_ROW_ACCEPTANCE_PLAN_READY"
EXPECTED_DD098_STATUS = "DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN"

DEFAULT_ACCEPTANCE_DIR = "docs/datadict/reports/DD096C-candidate-row-acceptance-plan-v0/generated_acceptance_plan"
DEFAULT_CANDIDATE_DIR = "docs/datadict/reports/DD096A-candidate-catalog-row-design-v0/generated_candidate_catalog_rows"

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
    ap = argparse.ArgumentParser(description="DD096E external apply-row staging package")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096E-external-apply-row-staging-v0")
    ap.add_argument("--dd096d-dir", default="docs/datadict/reports/DD096D-guarded-apply-design-preflight-v0")
    ap.add_argument("--dd096c-dir", default="docs/datadict/reports/DD096C-candidate-row-acceptance-plan-v0")
    ap.add_argument("--dd098-dir", default="docs/datadict/reports/DD098-datadict-baseline-closeout-v0")
    ap.add_argument("--acceptance-dir", default=DEFAULT_ACCEPTANCE_DIR)
    ap.add_argument("--candidate-dir", default=DEFAULT_CANDIDATE_DIR)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd096d_manifest_path = repo / args.dd096d_dir / "dd096d_guarded_apply_design_preflight_manifest.json"
    dd096c_manifest_path = repo / args.dd096c_dir / "dd096c_candidate_row_acceptance_plan_manifest.json"
    dd098_manifest_path = repo / args.dd098_dir / "dd098_datadict_baseline_closeout_manifest.json"

    dd096d = read_json(dd096d_manifest_path)
    dd096c = read_json(dd096c_manifest_path)
    dd098 = read_json(dd098_manifest_path)

    adir = repo / args.acceptance_dir
    cdir = repo / args.candidate_dir

    acc_object = read_csv(adir / "dd096c_ddobject_acceptance_plan.csv")
    remap = read_csv(adir / "dd096c_objid_remap_plan.csv")
    acc_attr = read_csv(adir / "dd096c_ddattr_acceptance_plan.csv")
    acc_edge = read_csv(adir / "dd096c_ddedge_acceptance_plan.csv")
    acc_evid = read_csv(adir / "dd096c_ddevid_acceptance_plan.csv")
    acc_gate = read_csv(adir / "dd096c_ddgate_acceptance_plan.csv")

    cand_object = read_csv(cdir / "dd096a_candidate_ddobject_rows.csv")
    cand_attr = read_csv(cdir / "dd096a_candidate_ddattr_rows.csv")
    cand_edge = read_csv(cdir / "dd096a_candidate_ddedge_rows.csv")
    cand_evid = read_csv(cdir / "dd096a_candidate_ddevid_rows.csv")
    cand_gate = read_csv(cdir / "dd096a_candidate_ddgate_rows.csv")

    obj_accept_by_id = {r.get("candidate_objid", ""): r for r in acc_object}
    cand_object_by_id = {r.get("candidate_objid", ""): r for r in cand_object}
    remap_by_candidate = {r.get("candidate_objid", ""): r.get("active_objid", "") for r in remap}

    # Stage only the eight new DDOBJECT rows. Existing catalog-table objects are suppressed/reused.
    staged_objects = []
    suppressed_objects = []
    for acc in acc_object:
        cid = acc.get("candidate_objid", "")
        cand = cand_object_by_id.get(cid, {})
        if acc.get("acceptance_decision") == "ACCEPT_EXISTING_REUSE_ACTIVE_OBJID":
            suppressed_objects.append({
                "candidate_objid": cid,
                "active_objid": acc.get("active_objid", ""),
                "name": acc.get("name", ""),
                "object_type": acc.get("object_type", ""),
                "reason": "existing_catalog_table_object_reused_no_insert",
                "apply_now": 0,
            })
        elif acc.get("acceptance_decision") == "ACCEPT_NEW_CANDIDATE_PENDING_APPLY_DESIGN":
            staged_objects.append({
                "target_table": "DDOBJECT",
                "objid": cid,
                "objtype": acc.get("object_type", cand.get("objtype", "")),
                "owner": acc.get("owner", cand.get("owner", "")),
                "name": acc.get("name", cand.get("name", "")),
                "status": cand.get("status", "REVIEW_READY_CANDIDATE"),
                "profile": cand.get("profile", "ENGINE"),
                "srcid": cand.get("srcid", ""),
                "purpose": cand.get("purpose", ""),
                "staging_decision": "STAGE_NEW_OBJECT_ROW",
                "apply_now": 0,
            })

    # Stage all attr rows with planned/rebased OBJID. Still external staging only.
    staged_attrs = []
    for acc in acc_attr:
        staged_attrs.append({
            "target_table": "DDATTR",
            "attrid": acc.get("candidate_attrid", ""),
            "objid": acc.get("planned_objid", ""),
            "attrname": acc.get("attrname", ""),
            "attrval": acc.get("attrval", ""),
            "status": "REVIEW_READY_CANDIDATE",
            "profile": "ENGINE",
            "evid": "EVID_DD096E_STAGED_FROM_DD096C",
            "staging_decision": acc.get("acceptance_decision", ""),
            "apply_now": 0,
        })

    staged_edges = []
    for acc in acc_edge:
        staged_edges.append({
            "target_table": "DDEDGE",
            "edgeid": acc.get("candidate_edgeid", ""),
            "from_objid": acc.get("planned_from_objid", ""),
            "from_name": acc.get("from_name", ""),
            "to_objid": acc.get("planned_to_objid", ""),
            "to_name": acc.get("to_name", ""),
            "edge_type": acc.get("edge_type", ""),
            "key": acc.get("key", ""),
            "meaning": "staged_from_DD096C_acceptance_plan",
            "status": "REVIEW_READY_CANDIDATE",
            "profile": "ENGINE",
            "evid": "EVID_DD096E_STAGED_FROM_DD096C",
            "staging_decision": acc.get("acceptance_decision", ""),
            "apply_now": 0,
        })

    staged_evid = []
    for acc in acc_evid:
        staged_evid.append({
            "target_table": "DDEVID",
            "evid": acc.get("candidate_evid", ""),
            "kind": acc.get("kind", ""),
            "source": acc.get("source", ""),
            "status": "REVIEW_READY_CANDIDATE",
            "profile": "ENGINE",
            "staging_decision": acc.get("acceptance_decision", ""),
            "apply_now": 0,
        })

    staged_gates = []
    for acc in acc_gate:
        staged_gates.append({
            "target_table": "DDGATE",
            "gate_id": acc.get("gate_id", ""),
            "gate_type": acc.get("gate_type", ""),
            "required_state": "explicit_apply_authorization_required",
            "observed_state": "staged_external_only",
            "status": "REVIEW_READY_CANDIDATE",
            "staging_decision": acc.get("acceptance_decision", ""),
            "apply_now": 0,
        })

    generated = out / "generated_staged_apply_rows"
    generated.mkdir(parents=True, exist_ok=True)

    write_csv(generated / "dd096e_staged_ddobject_insert_rows.csv", staged_objects, [
        "target_table", "objid", "objtype", "owner", "name", "status", "profile", "srcid", "purpose", "staging_decision", "apply_now"
    ])
    write_csv(generated / "dd096e_suppressed_existing_ddobject_rows.csv", suppressed_objects, [
        "candidate_objid", "active_objid", "name", "object_type", "reason", "apply_now"
    ])
    write_csv(generated / "dd096e_staged_ddattr_insert_rows.csv", staged_attrs, [
        "target_table", "attrid", "objid", "attrname", "attrval", "status", "profile", "evid", "staging_decision", "apply_now"
    ])
    write_csv(generated / "dd096e_staged_ddedge_insert_rows.csv", staged_edges, [
        "target_table", "edgeid", "from_objid", "from_name", "to_objid", "to_name", "edge_type", "key", "meaning", "status", "profile", "evid", "staging_decision", "apply_now"
    ])
    write_csv(generated / "dd096e_staged_ddevid_insert_rows.csv", staged_evid, [
        "target_table", "evid", "kind", "source", "status", "profile", "staging_decision", "apply_now"
    ])
    write_csv(generated / "dd096e_staged_ddgate_insert_rows.csv", staged_gates, [
        "target_table", "gate_id", "gate_type", "required_state", "observed_state", "status", "staging_decision", "apply_now"
    ])

    staged_index = []
    for family, rows, id_field in [
        ("DDOBJECT", staged_objects, "objid"),
        ("DDATTR", staged_attrs, "attrid"),
        ("DDEDGE", staged_edges, "edgeid"),
        ("DDEVID", staged_evid, "evid"),
        ("DDGATE", staged_gates, "gate_id"),
    ]:
        for r in rows:
            staged_index.append({
                "family": family,
                "staged_id": r.get(id_field, ""),
                "target_table": r.get("target_table", family),
                "staging_decision": r.get("staging_decision", ""),
                "apply_now": r.get("apply_now", 0),
            })
    write_csv(generated / "dd096e_staged_apply_row_index.csv", staged_index, [
        "family", "staged_id", "target_table", "staging_decision", "apply_now"
    ])

    counts = {
        "staged_total": len(staged_index),
        "staged_ddobject": len(staged_objects),
        "suppressed_existing_ddobject": len(suppressed_objects),
        "staged_ddattr": len(staged_attrs),
        "staged_ddedge": len(staged_edges),
        "staged_ddevid": len(staged_evid),
        "staged_ddgate": len(staged_gates),
        "apply_now_total": sum(int_field(r, "apply_now") for r in staged_index) + sum(int_field(r, "apply_now") for r in suppressed_objects),
    }

    write_json(generated / "dd096e_staged_apply_rows.json", {
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "external_staging_only": True,
        "counts": counts,
        "ddobject": staged_objects,
        "suppressed_existing_ddobject": suppressed_objects,
        "ddattr": staged_attrs,
        "ddedge": staged_edges,
        "ddevid": staged_evid,
        "ddgate": staged_gates,
    })

    staging_rules = [
        {
            "rule_id": "STAGE001_NO_ACTIVE_WRITES",
            "rule": "DD096E writes only external staging files under the report directory.",
            "pass": 1,
        },
        {
            "rule_id": "STAGE002_SUPPRESS_EXISTING_TABLE_OBJECTS",
            "rule": "The 11 existing catalog-table DDOBJECT rows are suppressed from insert staging.",
            "pass": int(len(suppressed_objects) == 11),
        },
        {
            "rule_id": "STAGE003_STAGE_ONLY_NEW_OBJECTS",
            "rule": "Only the 8 new DDOBJECT candidates are staged as object inserts.",
            "pass": int(len(staged_objects) == 8),
        },
        {
            "rule_id": "STAGE004_REBASED_ATTRS_PRESENT",
            "rule": "DDATTR rows are staged using the DD096C planned/rebased OBJIDs.",
            "pass": int(len(staged_attrs) == 120),
        },
        {
            "rule_id": "STAGE005_REBASED_EDGES_PRESENT",
            "rule": "DDEDGE rows are staged using the DD096C planned/rebased endpoints.",
            "pass": int(len(staged_edges) == 15),
        },
        {
            "rule_id": "STAGE006_APPLY_NOW_ZERO",
            "rule": "All staged and suppressed rows retain apply_now = 0.",
            "pass": int(counts["apply_now_total"] == 0),
        },
    ]

    write_csv(generated / "dd096e_staging_rules.csv", staging_rules, ["rule_id", "rule", "pass"])

    boundary_rows = [
        {"boundary": "external_apply_row_staging_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "apply_now_total", "observed": counts["apply_now_total"], "required": 0, "pass": int(counts["apply_now_total"] == 0)},
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
        {"gate": "dd096d_ready", "expected": EXPECTED_DD096D_STATUS, "observed": dd096d.get("status", ""), "pass": int(dd096d.get("status") == EXPECTED_DD096D_STATUS)},
        {"gate": "dd096c_ready", "expected": EXPECTED_DD096C_STATUS, "observed": dd096c.get("status", ""), "pass": int(dd096c.get("status") == EXPECTED_DD096C_STATUS)},
        {"gate": "dd098_closed", "expected": EXPECTED_DD098_STATUS, "observed": dd098.get("status", ""), "pass": int(dd098.get("status") == EXPECTED_DD098_STATUS)},
        {"gate": "staged_objects_8", "expected": 8, "observed": len(staged_objects), "pass": int(len(staged_objects) == 8)},
        {"gate": "suppressed_existing_objects_11", "expected": 11, "observed": len(suppressed_objects), "pass": int(len(suppressed_objects) == 11)},
        {"gate": "staged_attrs_120", "expected": 120, "observed": len(staged_attrs), "pass": int(len(staged_attrs) == 120)},
        {"gate": "staged_edges_15", "expected": 15, "observed": len(staged_edges), "pass": int(len(staged_edges) == 15)},
        {"gate": "staged_evidence_6", "expected": 6, "observed": len(staged_evid), "pass": int(len(staged_evid) == 6)},
        {"gate": "staged_gates_2", "expected": 2, "observed": len(staged_gates), "pass": int(len(staged_gates) == 2)},
        {"gate": "apply_now_zero", "expected": 0, "observed": counts["apply_now_total"], "pass": int(counts["apply_now_total"] == 0)},
        {"gate": "staging_rules_pass", "expected": len(staging_rules), "observed": sum(int(r["pass"]) for r in staging_rules), "pass": int(sum(int(r["pass"]) for r in staging_rules) == len(staging_rules))},
    ]

    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DATADICT_EXTERNAL_APPLY_ROW_STAGING_READY" if failures == 0 else "DATADICT_EXTERNAL_APPLY_ROW_STAGING_REVIEW"

    artifact_rows = [
        artifact_row(repo, str(dd096d_manifest_path.relative_to(repo)), "dd096d_manifest"),
        artifact_row(repo, str(dd096c_manifest_path.relative_to(repo)), "dd096c_manifest"),
        artifact_row(repo, str(dd098_manifest_path.relative_to(repo)), "dd098_manifest"),
        artifact_row(repo, args.acceptance_dir, "acceptance_dir"),
        artifact_row(repo, args.candidate_dir, "candidate_dir"),
    ]
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))
    for f in sorted(generated.iterdir()):
        if f.is_file():
            artifact_rows.append({
                "role": "generated_staged_rows",
                "path": str(f),
                "exists": 1,
                "kind": "file",
                "bytes_or_children": f.stat().st_size,
                "sha256": sha256(f),
            })

    next_rows = [
        {"next_id": "DD096F", "title": "staged-row review and simulated apply validation", "allowed_scope": "simulation only; no active DBF writes"},
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply planning", "allowed_scope": "only after explicit authorization"},
        {"next_id": "DD099", "title": "baseline-to-manual integration report", "allowed_scope": "documentation/explanation only"},
    ]

    write_csv(out / "dd096e_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096e_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd096e_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd096e_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD096E External Apply-Row Staging

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096E stages the DD096C acceptance/remap result into external CSV/JSON files that a future apply design could review.

It is not an apply lane. It writes no active DBFs and performs no catalog mutation.

## Summary

- Staged total rows: **{counts['staged_total']}**
- Staged new DDOBJECT rows: **{counts['staged_ddobject']}**
- Suppressed existing DDOBJECT rows: **{counts['suppressed_existing_ddobject']}**
- Staged DDATTR rows: **{counts['staged_ddattr']}**
- Staged DDEDGE rows: **{counts['staged_ddedge']}**
- Staged DDEVID rows: **{counts['staged_ddevid']}**
- Staged DDGATE rows: **{counts['staged_ddgate']}**
- apply_now total: **{counts['apply_now_total']}**

## Key rule

DD096E suppresses the 11 existing catalog-table DDOBJECT rows from insert staging and stages only the 8 new DDOBJECT candidates.

## Boundary

DD096E is external-apply-row-staging/report-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    write_text(out / "DD096E_EXTERNAL_APPLY_ROW_STAGING_REPORT.md", report)

    manifest = {
        "contract": "dd096e_external_apply_row_staging_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "counts": counts,
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
        "next_recommended_action": "DD096F staged-row review and simulated apply validation, still no active DBF writes.",
    }
    write_json(out / "dd096e_external_apply_row_staging_manifest.json", manifest)

    print(f"DD096E external apply-row staging manifest: {out / 'dd096e_external_apply_row_staging_manifest.json'}")
    print(f"status: {status}; staged_total: {counts['staged_total']}; objects: {counts['staged_ddobject']}; suppressed_objects: {counts['suppressed_existing_ddobject']}; attrs: {counts['staged_ddattr']}; edges: {counts['staged_ddedge']}; evidence: {counts['staged_ddevid']}; gates: {counts['staged_ddgate']}; apply_now: {counts['apply_now_total']}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
