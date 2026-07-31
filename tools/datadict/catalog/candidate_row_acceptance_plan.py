#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD096A_STATUS = "DATADICT_CANDIDATE_CATALOG_ROW_DESIGN_READY"
EXPECTED_DD096B_STATUS = "DATADICT_CANDIDATE_ROW_REVIEW_DEDUP_READY"
EXPECTED_DD098_STATUS = "DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN"

DEFAULT_CANDIDATE_DIR = "docs/datadict/reports/DD096A-candidate-catalog-row-design-v0/generated_candidate_catalog_rows"
DEFAULT_REVIEW_DIR = "docs/datadict/reports/DD096B-candidate-catalog-row-review-dedup-v0/generated_candidate_review"

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


def norm(s: object) -> str:
    return str(s or "").strip().upper()


def parse_active_objid_list(value: str) -> str:
    parts = [p.strip() for p in str(value or "").split(";") if p.strip()]
    return parts[0] if parts else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096C candidate row acceptance/remap plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096C-candidate-row-acceptance-plan-v0")
    ap.add_argument("--dd096a-dir", default="docs/datadict/reports/DD096A-candidate-catalog-row-design-v0")
    ap.add_argument("--dd096b-dir", default="docs/datadict/reports/DD096B-candidate-catalog-row-review-dedup-v0")
    ap.add_argument("--dd098-dir", default="docs/datadict/reports/DD098-datadict-baseline-closeout-v0")
    ap.add_argument("--candidate-dir", default=DEFAULT_CANDIDATE_DIR)
    ap.add_argument("--review-dir", default=DEFAULT_REVIEW_DIR)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd096a_manifest_path = repo / args.dd096a_dir / "dd096a_candidate_catalog_row_design_manifest.json"
    dd096b_manifest_path = repo / args.dd096b_dir / "dd096b_candidate_catalog_row_review_dedup_manifest.json"
    dd098_manifest_path = repo / args.dd098_dir / "dd098_datadict_baseline_closeout_manifest.json"
    dd096a = read_json(dd096a_manifest_path)
    dd096b = read_json(dd096b_manifest_path)
    dd098 = read_json(dd098_manifest_path)

    cdir = repo / args.candidate_dir
    rdir = repo / args.review_dir

    ddobject = read_csv(cdir / "dd096a_candidate_ddobject_rows.csv")
    ddattr = read_csv(cdir / "dd096a_candidate_ddattr_rows.csv")
    ddedge = read_csv(cdir / "dd096a_candidate_ddedge_rows.csv")
    ddevid = read_csv(cdir / "dd096a_candidate_ddevid_rows.csv")
    ddgate = read_csv(cdir / "dd096a_candidate_ddgate_rows.csv")
    review_all = read_csv(rdir / "dd096b_candidate_review_all.csv")

    review_by_candidate = {r.get("candidate_row_id", ""): r for r in review_all}

    # Build candidate object remap from duplicate DDOBJECT rows.
    object_acceptance: List[Dict[str, object]] = []
    remap_rows: List[Dict[str, object]] = []
    remap_by_candidate_objid: Dict[str, str] = {}
    duplicate_objects = 0
    new_objects = 0

    for row in ddobject:
        rid = row.get("candidate_row_id", "")
        review = review_by_candidate.get(rid, {})
        status = review.get("review_status", "")
        active_objid = parse_active_objid_list(review.get("active_objids", ""))
        candidate_objid = row.get("candidate_objid", "")
        if status == "DUPLICATE_REVIEW" and active_objid:
            decision = "ACCEPT_EXISTING_REUSE_ACTIVE_OBJID"
            duplicate_objects += 1
            remap_by_candidate_objid[candidate_objid] = active_objid
            remap_rows.append({
                "candidate_objid": candidate_objid,
                "active_objid": active_objid,
                "object_name": row.get("name", ""),
                "object_type": row.get("objtype", ""),
                "decision": decision,
                "apply_now": 0,
            })
        else:
            decision = "ACCEPT_NEW_CANDIDATE_PENDING_APPLY_DESIGN"
            new_objects += 1
        object_acceptance.append({
            "candidate_row_id": rid,
            "target_table": "DDOBJECT",
            "candidate_objid": candidate_objid,
            "object_type": row.get("objtype", ""),
            "owner": row.get("owner", ""),
            "name": row.get("name", ""),
            "review_status": status or "NEW_CANDIDATE_REVIEW",
            "active_objid": active_objid,
            "acceptance_decision": decision,
            "apply_now": 0,
        })

    attr_acceptance: List[Dict[str, object]] = []
    rebase_attr_count = 0
    new_attr_count = 0
    for row in ddattr:
        old_objid = row.get("objid", "")
        rebased_objid = remap_by_candidate_objid.get(old_objid, old_objid)
        needs_rebase = int(rebased_objid != old_objid)
        rebase_attr_count += needs_rebase
        new_attr_count += 1
        attr_acceptance.append({
            "candidate_row_id": row.get("candidate_row_id", ""),
            "target_table": "DDATTR",
            "candidate_attrid": row.get("candidate_attrid", ""),
            "candidate_objid": old_objid,
            "planned_objid": rebased_objid,
            "attrname": row.get("attrname", ""),
            "attrval": row.get("attrval", ""),
            "acceptance_decision": "REBASE_TO_ACTIVE_OBJID_THEN_REVIEW_ATTR" if needs_rebase else "ACCEPT_NEW_ATTR_CANDIDATE_PENDING_APPLY_DESIGN",
            "apply_now": 0,
        })

    edge_acceptance: List[Dict[str, object]] = []
    rebase_edge_count = 0
    for row in ddedge:
        old_from = row.get("from_objid", "")
        old_to = row.get("to_objid", "")
        new_from = remap_by_candidate_objid.get(old_from, old_from)
        new_to = remap_by_candidate_objid.get(old_to, old_to)
        needs_rebase = int(new_from != old_from or new_to != old_to)
        rebase_edge_count += needs_rebase
        edge_acceptance.append({
            "candidate_row_id": row.get("candidate_row_id", ""),
            "target_table": "DDEDGE",
            "candidate_edgeid": row.get("candidate_edgeid", ""),
            "from_name": row.get("from_name", ""),
            "to_name": row.get("to_name", ""),
            "candidate_from_objid": old_from,
            "planned_from_objid": new_from,
            "candidate_to_objid": old_to,
            "planned_to_objid": new_to,
            "edge_type": row.get("edge_type", ""),
            "key": row.get("key", ""),
            "acceptance_decision": "REBASE_EDGE_ENDPOINTS_THEN_REVIEW" if needs_rebase else "ACCEPT_NEW_EDGE_CANDIDATE_PENDING_APPLY_DESIGN",
            "apply_now": 0,
        })

    evidence_acceptance = []
    for row in ddevid:
        evidence_acceptance.append({
            "candidate_row_id": row.get("candidate_row_id", ""),
            "target_table": "DDEVID",
            "candidate_evid": row.get("candidate_evid", ""),
            "kind": row.get("kind", ""),
            "source": row.get("source", ""),
            "acceptance_decision": "ACCEPT_NEW_EVIDENCE_CANDIDATE_PENDING_APPLY_DESIGN",
            "apply_now": 0,
        })

    gate_acceptance = []
    for row in ddgate:
        gate_acceptance.append({
            "candidate_row_id": row.get("candidate_row_id", ""),
            "target_table": "DDGATE",
            "gate_id": row.get("gate_id", ""),
            "gate_type": row.get("gate_type", ""),
            "acceptance_decision": "ACCEPT_NEW_GATE_CANDIDATE_PENDING_APPLY_DESIGN",
            "apply_now": 0,
        })

    generated = out / "generated_acceptance_plan"
    generated.mkdir(parents=True, exist_ok=True)

    write_csv(generated / "dd096c_ddobject_acceptance_plan.csv", object_acceptance, [
        "candidate_row_id", "target_table", "candidate_objid", "object_type", "owner", "name",
        "review_status", "active_objid", "acceptance_decision", "apply_now"
    ])
    write_csv(generated / "dd096c_objid_remap_plan.csv", remap_rows, [
        "candidate_objid", "active_objid", "object_name", "object_type", "decision", "apply_now"
    ])
    write_csv(generated / "dd096c_ddattr_acceptance_plan.csv", attr_acceptance, [
        "candidate_row_id", "target_table", "candidate_attrid", "candidate_objid", "planned_objid",
        "attrname", "attrval", "acceptance_decision", "apply_now"
    ])
    write_csv(generated / "dd096c_ddedge_acceptance_plan.csv", edge_acceptance, [
        "candidate_row_id", "target_table", "candidate_edgeid", "from_name", "to_name",
        "candidate_from_objid", "planned_from_objid", "candidate_to_objid", "planned_to_objid",
        "edge_type", "key", "acceptance_decision", "apply_now"
    ])
    write_csv(generated / "dd096c_ddevid_acceptance_plan.csv", evidence_acceptance, [
        "candidate_row_id", "target_table", "candidate_evid", "kind", "source",
        "acceptance_decision", "apply_now"
    ])
    write_csv(generated / "dd096c_ddgate_acceptance_plan.csv", gate_acceptance, [
        "candidate_row_id", "target_table", "gate_id", "gate_type",
        "acceptance_decision", "apply_now"
    ])

    all_acceptance = []
    for family, rows in [
        ("DDOBJECT", object_acceptance),
        ("DDATTR", attr_acceptance),
        ("DDEDGE", edge_acceptance),
        ("DDEVID", evidence_acceptance),
        ("DDGATE", gate_acceptance),
    ]:
        for r in rows:
            all_acceptance.append({
                "family": family,
                "candidate_row_id": r.get("candidate_row_id", ""),
                "acceptance_decision": r.get("acceptance_decision", ""),
                "apply_now": r.get("apply_now", 0),
            })
    write_csv(generated / "dd096c_acceptance_plan_index.csv", all_acceptance, [
        "family", "candidate_row_id", "acceptance_decision", "apply_now"
    ])

    counts = {
        "total_acceptance_rows": len(all_acceptance),
        "duplicate_objects_reuse_active": duplicate_objects,
        "new_objects": new_objects,
        "objid_remaps": len(remap_rows),
        "attrs_requiring_rebase": rebase_attr_count,
        "edges_requiring_rebase": rebase_edge_count,
        "evidence_candidates": len(evidence_acceptance),
        "gate_candidates": len(gate_acceptance),
        "apply_now_total": sum(int(r.get("apply_now", 0)) for r in all_acceptance),
    }

    write_json(generated / "dd096c_acceptance_plan_summary.json", {
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "counts": counts,
        "candidate_only": True,
        "apply_now_total": counts["apply_now_total"],
    })

    plan_doc = f"""# DD096C Candidate Row Acceptance / Remap Plan

Run id: `{args.run_id}`
Created UTC: `{utc_now()}`

## Purpose

DD096C turns the DD096B review result into an acceptance/remap plan.

The core finding is that the 11 catalog-table DDOBJECT rows already exist in the active catalog.
Future apply design must reuse those active OBJIDs instead of inserting duplicate DDOBJECT rows.

## Acceptance summary

- Total acceptance rows: **{counts['total_acceptance_rows']}**
- Existing DDOBJECT table rows to reuse: **{counts['duplicate_objects_reuse_active']}**
- New DDOBJECT rows: **{counts['new_objects']}**
- OBJID remaps required: **{counts['objid_remaps']}**
- DDATTR rows requiring parent OBJID rebase: **{counts['attrs_requiring_rebase']}**
- DDEDGE rows requiring endpoint rebase: **{counts['edges_requiring_rebase']}**
- DDEVID candidates: **{counts['evidence_candidates']}**
- DDGATE candidates: **{counts['gate_candidates']}**
- apply_now total: **{counts['apply_now_total']}**

## Rule

Do not insert duplicate catalog-table DDOBJECT rows. Reuse active OBJIDs for the 11 existing tables, then rebase dependent DDATTR and DDEDGE candidates before any future apply design.

## Boundary

DD096C is an acceptance/remap plan only. It does not write DBFs, update indexes, rebuild LMDB, mutate HELP/CMDHELPCHK, edit source, or apply schema promotion.
"""
    write_text(generated / "DD096C_CANDIDATE_ROW_ACCEPTANCE_PLAN.md", plan_doc)

    artifact_rows = [
        artifact_row(repo, str(dd096a_manifest_path.relative_to(repo)), "dd096a_manifest"),
        artifact_row(repo, str(dd096b_manifest_path.relative_to(repo)), "dd096b_manifest"),
        artifact_row(repo, str(dd098_manifest_path.relative_to(repo)), "dd098_manifest"),
        artifact_row(repo, args.candidate_dir, "candidate_dir"),
        artifact_row(repo, args.review_dir, "review_dir"),
    ]
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))
    for f in sorted(generated.iterdir()):
        if f.is_file():
            artifact_rows.append({
                "role": "generated_acceptance_plan",
                "path": str(f),
                "exists": 1,
                "kind": "file",
                "bytes_or_children": f.stat().st_size,
                "sha256": sha256(f),
            })

    boundary_rows = [
        {"boundary": "candidate_acceptance_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "apply_now_total", "observed": counts["apply_now_total"], "required": 0, "pass": int(counts["apply_now_total"] == 0)},
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

    gates = [
        {"gate": "dd096a_ready", "expected": EXPECTED_DD096A_STATUS, "observed": dd096a.get("status", ""), "pass": int(dd096a.get("status") == EXPECTED_DD096A_STATUS)},
        {"gate": "dd096b_ready", "expected": EXPECTED_DD096B_STATUS, "observed": dd096b.get("status", ""), "pass": int(dd096b.get("status") == EXPECTED_DD096B_STATUS)},
        {"gate": "dd098_closed", "expected": EXPECTED_DD098_STATUS, "observed": dd098.get("status", ""), "pass": int(dd098.get("status") == EXPECTED_DD098_STATUS)},
        {"gate": "duplicate_objects_11", "expected": 11, "observed": duplicate_objects, "pass": int(duplicate_objects == 11)},
        {"gate": "new_objects_8", "expected": 8, "observed": new_objects, "pass": int(new_objects == 8)},
        {"gate": "objid_remaps_11", "expected": 11, "observed": len(remap_rows), "pass": int(len(remap_rows) == 11)},
        {"gate": "acceptance_rows_match_candidates", "expected": dd096a.get("candidate_counts", {}).get("all", ""), "observed": len(all_acceptance), "pass": int(str(dd096a.get("candidate_counts", {}).get("all", "")) == str(len(all_acceptance)))},
        {"gate": "apply_now_zero", "expected": 0, "observed": counts["apply_now_total"], "pass": int(counts["apply_now_total"] == 0)},
    ]

    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DATADICT_CANDIDATE_ROW_ACCEPTANCE_PLAN_READY" if failures == 0 else "DATADICT_CANDIDATE_ROW_ACCEPTANCE_PLAN_REVIEW"

    next_rows = [
        {"next_id": "DD096D", "title": "guarded apply design preflight", "allowed_scope": "design/preflight only; no DBF writes"},
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply planning", "allowed_scope": "only after explicit authorization"},
        {"next_id": "DD099", "title": "baseline-to-manual integration report", "allowed_scope": "documentation/explanation only"},
    ]

    write_csv(out / "dd096c_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096c_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd096c_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd096c_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD096C Candidate Row Acceptance / Remap Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096C creates a candidate-only acceptance/remap plan from DD096A candidates and DD096B read-only deduplication.

## Summary

- Total acceptance rows: **{counts['total_acceptance_rows']}**
- Existing DDOBJECT table rows to reuse: **{counts['duplicate_objects_reuse_active']}**
- New DDOBJECT rows: **{counts['new_objects']}**
- OBJID remaps required: **{counts['objid_remaps']}**
- DDATTR rows requiring parent OBJID rebase: **{counts['attrs_requiring_rebase']}**
- DDEDGE rows requiring endpoint rebase: **{counts['edges_requiring_rebase']}**
- apply_now total: **{counts['apply_now_total']}**

## Key rule

The 11 existing catalog-table `DDOBJECT` rows must be reused. Future apply design must not insert duplicates for DDARTIF, DDATTR, DDBASE, DDEDGE, DDEVID, DDGATE, DDOBJECT, DDPROFILE, DDREVIEW, DDRUN, or DDSOURCE.

## Boundary

DD096C is candidate-acceptance-planning/report-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    write_text(out / "DD096C_CANDIDATE_ROW_ACCEPTANCE_PLAN_REPORT.md", report)

    manifest = {
        "contract": "dd096c_candidate_row_acceptance_plan_v0",
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
        "next_recommended_action": "DD096D guarded apply design preflight, still no DBF writes.",
    }
    write_json(out / "dd096c_candidate_row_acceptance_plan_manifest.json", manifest)

    print(f"DD096C candidate row acceptance/remap plan manifest: {out / 'dd096c_candidate_row_acceptance_plan_manifest.json'}")
    print(f"status: {status}; acceptance_rows: {counts['total_acceptance_rows']}; reuse_existing_objects: {duplicate_objects}; new_objects: {new_objects}; remaps: {len(remap_rows)}; attr_rebase: {rebase_attr_count}; edge_rebase: {rebase_edge_count}; apply_now: {counts['apply_now_total']}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
