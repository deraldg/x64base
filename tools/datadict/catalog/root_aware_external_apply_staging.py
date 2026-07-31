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

DEFAULT_ACCEPTANCE_DIR = "docs/datadict/reports/DD096CR-acceptance-gate-repair-v0/generated_acceptance_plan"
DEFAULT_CANDIDATE_DIR = "docs/datadict/reports/DD096AR-ddict-root-command-candidate-repair-v0/generated_repaired_candidate_catalog_rows"


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
    ap = argparse.ArgumentParser(description="DD096E-R root-aware external apply-row staging")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096E-R-root-aware-external-apply-staging-v0")
    ap.add_argument("--dd096d-dir", default="docs/datadict/reports/DD096D-R-root-aware-guarded-apply-preflight-v0")
    ap.add_argument("--dd096c-dir", default="docs/datadict/reports/DD096CR-acceptance-gate-repair-v0")
    ap.add_argument("--dd098-dir", default="docs/datadict/reports/DD098-datadict-baseline-closeout-v0")
    ap.add_argument("--acceptance-dir", default=DEFAULT_ACCEPTANCE_DIR)
    ap.add_argument("--candidate-dir", default=DEFAULT_CANDIDATE_DIR)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    d_manifest_path = repo / args.dd096d_dir / "dd096d_guarded_apply_design_preflight_manifest.json"
    c_manifest_path = repo / args.dd096c_dir / "dd096c_candidate_row_acceptance_plan_manifest.json"
    z_manifest_path = repo / args.dd098_dir / "dd098_datadict_baseline_closeout_manifest.json"
    d_manifest = read_json(d_manifest_path)
    c_manifest = read_json(c_manifest_path)
    z_manifest = read_json(z_manifest_path)

    adir = repo / args.acceptance_dir
    cdir = repo / args.candidate_dir

    acc_object = read_csv(adir / "dd096c_ddobject_acceptance_plan.csv")
    acc_attr = read_csv(adir / "dd096c_ddattr_acceptance_plan.csv")
    acc_edge = read_csv(adir / "dd096c_ddedge_acceptance_plan.csv")
    acc_evid = read_csv(adir / "dd096c_ddevid_acceptance_plan.csv")
    acc_gate = read_csv(adir / "dd096c_ddgate_acceptance_plan.csv")

    cand_object = read_csv(cdir / "dd096a_candidate_ddobject_rows.csv")
    cand_object_by_id = {r.get("candidate_objid", ""): r for r in cand_object}

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
                "staging_decision": "STAGE_NEW_OBJECT_ROW_ROOT_AWARE",
                "apply_now": 0,
            })

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
            "evid": "EVID_DD096ER_STAGED_FROM_ROOT_AWARE_ACCEPTANCE",
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
            "meaning": "staged_from_DD096CR_root_aware_acceptance_plan",
            "status": "REVIEW_READY_CANDIDATE",
            "profile": "ENGINE",
            "evid": "EVID_DD096ER_STAGED_FROM_ROOT_AWARE_ACCEPTANCE",
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
            "observed_state": "staged_external_only_root_aware",
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
        "root_aware": True,
        "counts": counts,
        "ddobject": staged_objects,
        "suppressed_existing_ddobject": suppressed_objects,
        "ddattr": staged_attrs,
        "ddedge": staged_edges,
        "ddevid": staged_evid,
        "ddgate": staged_gates,
    })

    rules = [
        {"rule_id": "STAGE001_NO_ACTIVE_WRITES", "rule": "External staging only.", "pass": 1},
        {"rule_id": "STAGE002_SUPPRESS_EXISTING_TABLE_OBJECTS", "rule": "Suppress 11 existing table-object rows.", "pass": int(len(suppressed_objects) == 11)},
        {"rule_id": "STAGE003_STAGE_ROOT_AWARE_NEW_OBJECTS", "rule": "Stage 9 new DDOBJECT candidates: root DDICT plus 8 surfaces.", "pass": int(len(staged_objects) == 9)},
        {"rule_id": "STAGE004_ROOT_AWARE_ATTRS", "rule": "Stage 126 DDATTR rows including root DDICT support attrs.", "pass": int(len(staged_attrs) == 126)},
        {"rule_id": "STAGE005_EDGES_15", "rule": "Stage 15 DDEDGE rows.", "pass": int(len(staged_edges) == 15)},
        {"rule_id": "STAGE006_APPLY_NOW_ZERO", "rule": "All rows retain apply_now = 0.", "pass": int(counts["apply_now_total"] == 0)},
    ]
    write_csv(generated / "dd096e_staging_rules.csv", rules, ["rule_id", "rule", "pass"])

    gates = [
        {"gate": "dd096d_ready", "expected": EXPECTED_DD096D_STATUS, "observed": d_manifest.get("status", ""), "pass": int(d_manifest.get("status", "") == EXPECTED_DD096D_STATUS)},
        {"gate": "dd096c_ready", "expected": EXPECTED_DD096C_STATUS, "observed": c_manifest.get("status", ""), "pass": int(c_manifest.get("status", "") == EXPECTED_DD096C_STATUS)},
        {"gate": "dd098_closed", "expected": EXPECTED_DD098_STATUS, "observed": z_manifest.get("status", ""), "pass": int(z_manifest.get("status", "") == EXPECTED_DD098_STATUS)},
        {"gate": "staged_objects_root_aware_9", "expected": 9, "observed": len(staged_objects), "pass": int(len(staged_objects) == 9)},
        {"gate": "suppressed_existing_objects_11", "expected": 11, "observed": len(suppressed_objects), "pass": int(len(suppressed_objects) == 11)},
        {"gate": "staged_attrs_root_aware_126", "expected": 126, "observed": len(staged_attrs), "pass": int(len(staged_attrs) == 126)},
        {"gate": "staged_edges_15", "expected": 15, "observed": len(staged_edges), "pass": int(len(staged_edges) == 15)},
        {"gate": "staged_evidence_6", "expected": 6, "observed": len(staged_evid), "pass": int(len(staged_evid) == 6)},
        {"gate": "staged_gates_2", "expected": 2, "observed": len(staged_gates), "pass": int(len(staged_gates) == 2)},
        {"gate": "apply_now_zero", "expected": 0, "observed": counts["apply_now_total"], "pass": int(counts["apply_now_total"] == 0)},
        {"gate": "staging_rules_pass", "expected": len(rules), "observed": sum(int(r["pass"]) for r in rules), "pass": int(sum(int(r["pass"]) for r in rules) == len(rules))},
    ]
    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DATADICT_EXTERNAL_APPLY_ROW_STAGING_READY" if failures == 0 else "DATADICT_EXTERNAL_APPLY_ROW_STAGING_REVIEW"

    boundary = [
        {"boundary": "root_aware_external_staging_only", "observed": 1, "required": 1, "pass": 1},
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
    write_csv(out / "dd096e_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096e_no_mutation_boundary_ledger.csv", boundary, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd096e_artifact_ledger.csv", [
        artifact_row(d_manifest_path, "dd096d_manifest"),
        artifact_row(c_manifest_path, "dd096c_manifest"),
        artifact_row(z_manifest_path, "dd098_manifest"),
        artifact_row(adir, "acceptance_dir"),
        artifact_row(cdir, "candidate_dir"),
        artifact_row(generated, "generated_staged_rows"),
    ], ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])

    report = f"""# DD096E-R Root-Aware External Apply-Row Staging

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Summary

- Staged total rows: **{counts['staged_total']}**
- Staged new DDOBJECT rows: **{counts['staged_ddobject']}**
- Suppressed existing DDOBJECT rows: **{counts['suppressed_existing_ddobject']}**
- Staged DDATTR rows: **{counts['staged_ddattr']}**
- Staged DDEDGE rows: **{counts['staged_ddedge']}**
- Staged DDEVID rows: **{counts['staged_ddevid']}**
- Staged DDGATE rows: **{counts['staged_ddgate']}**
- apply_now total: **{counts['apply_now_total']}**

## Boundary

DD096E-R is external staging only. It performs no active catalog mutation.
"""
    write_text(out / "DD096E_ROOT_AWARE_EXTERNAL_APPLY_STAGING_REPORT.md", report)

    manifest = {
        "contract": "dd096er_root_aware_external_apply_staging_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "profiles": args.profile,
        "counts": counts,
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
    write_json(out / "dd096e_external_apply_row_staging_manifest.json", manifest)
    write_json(out / "dd096er_root_aware_external_apply_staging_manifest.json", manifest)

    print(f"DD096E-R root-aware external apply staging manifest: {out / 'dd096er_root_aware_external_apply_staging_manifest.json'}")
    print(f"status: {status}; staged_total: {counts['staged_total']}; objects: {counts['staged_ddobject']}; suppressed_objects: {counts['suppressed_existing_ddobject']}; attrs: {counts['staged_ddattr']}; edges: {counts['staged_ddedge']}; evidence: {counts['staged_ddevid']}; gates: {counts['staged_ddgate']}; apply_now: {counts['apply_now_total']}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
