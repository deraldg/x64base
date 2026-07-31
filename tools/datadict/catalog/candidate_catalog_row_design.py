#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD096_STATUS = "DATADICT_SCHEMA_PROMOTION_CATALOG_POLICY_READY"
EXPECTED_DD098_STATUS = "DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN"

CATALOG_TABLES = [
    ("DDARTIF", "Catalog artifact/report references", "ARTID"),
    ("DDATTR", "Catalog object attributes", "ATTRNAME"),
    ("DDBASE", "Catalog/base-level metadata", "BASEID"),
    ("DDEDGE", "Catalog object relationship edges", "EDGEID"),
    ("DDEVID", "Evidence links for catalog objects and artifacts", "EVID"),
    ("DDGATE", "Gate/checkpoint records", "GATEID"),
    ("DDOBJECT", "Catalog objects such as tables, fields, tags, commands, and surfaces", "OBJID"),
    ("DDPROFILE", "Profile definitions", "PROFID"),
    ("DDREVIEW", "Review records", "REVID"),
    ("DDRUN", "Run records", "RUNID"),
    ("DDSOURCE", "Source/provenance roots", "SRCID"),
]

RELATIONS = [
    ("DDOBJECT", "DDATTR", "OBJID", "WORKSPACE_RELATION", "object_has_attributes"),
    ("DDOBJECT", "DDEVID", "OBJID", "WORKSPACE_RELATION", "object_has_evidence"),
    ("DDSOURCE", "DDEVID", "SRCID", "WORKSPACE_RELATION", "source_has_evidence"),
    ("DDRUN", "DDARTIF", "RUNID", "WORKSPACE_RELATION", "run_has_artifacts"),
    ("DDRUN", "DDBASE", "RUNID", "WORKSPACE_RELATION", "run_has_base_records"),
    ("DDRUN", "DDGATE", "RUNID", "WORKSPACE_RELATION", "run_has_gates"),
    ("DDRUN", "DDREVIEW", "RUNID", "WORKSPACE_RELATION", "run_has_reviews"),
]

LAYOUT_EVIDENCE = [
    ("DD093C", "runtime_closure", "DDICT full path remap runtime closure green"),
    ("DD094", "workspace_savepoint", "11 areas, 7 relations, DBF/CDX/LMDB artifact presence green"),
    ("DD095", "layout_policy", "Data Dictionary layout and anti-collision policy green"),
    ("DD096", "schema_promotion_policy", "schema promotion/catalog policy ready"),
    ("DD097", "regression_smoke", "layout regression smoke green"),
    ("DD098", "baseline_closeout", "baseline closed and regression proven"),
]

DDICT_SURFACES = [
    ("DDICT HELP", "runtime_help_surface"),
    ("DDICT STATUS", "runtime_status_surface"),
    ("DDICT TABLES", "runtime_tables_surface"),
    ("DDICT OBJECTS", "runtime_objects_surface"),
    ("DDICT FIELDS <table>", "runtime_fields_surface"),
    ("DDICT TAGS <table>", "runtime_tags_surface"),
    ("DDICT REL <object> [IN|OUT|BOTH]", "runtime_rel_surface"),
    ("DDICT EVIDENCE <object>", "runtime_evidence_surface"),
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


def stable_id(prefix: str, *parts: str, length: int = 20) -> str:
    raw = "|".join(parts).encode("utf-8")
    return prefix + "_" + hashlib.sha1(raw).hexdigest().upper()[:length]


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


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_row(repo: Path, rel_path: str, role: str) -> Dict[str, Any]:
    p = repo / rel_path
    return {
        "role": role,
        "path": rel_path,
        "exists": int(p.exists()),
        "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
        "bytes_or_children": p.stat().st_size if p.exists() and p.is_file() else sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else 0,
        "sha256": sha256(p),
    }


def make_object_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for table, purpose, primary_tag in CATALOG_TABLES:
        rows.append({
            "candidate_row_id": stable_id("CANDOBJ", "DD096A", "CATALOG_TABLE", table),
            "target_table": "DDOBJECT",
            "candidate_objid": stable_id("OBJ", "DD096A", "CATALOG_TABLE", table),
            "objtype": "CATALOG_TABLE",
            "owner": "DATADICT_CATALOG",
            "name": table,
            "status": "ACCEPTED_BASELINE_CANDIDATE",
            "profile": "ENGINE",
            "srcid": "SRC_DD098_BASELINE_CLOSEOUT",
            "purpose": purpose,
            "primary_tag": primary_tag,
            "candidate_action": "UPSERT_CANDIDATE",
            "apply_now": 0,
        })
    for surface, purpose in DDICT_SURFACES:
        rows.append({
            "candidate_row_id": stable_id("CANDOBJ", "DD096A", "COMMAND_SURFACE", surface),
            "target_table": "DDOBJECT",
            "candidate_objid": stable_id("OBJ", "DD096A", "COMMAND_SURFACE", surface),
            "objtype": "COMMAND_SURFACE",
            "owner": "DDICT",
            "name": surface,
            "status": "REVIEW_READY_CANDIDATE",
            "profile": "ENGINE",
            "srcid": "SRC_DD092C_CMDHELPCHK_CANDIDATES",
            "purpose": purpose,
            "primary_tag": "",
            "candidate_action": "UPSERT_CANDIDATE",
            "apply_now": 0,
        })
    return rows


def make_attribute_rows(object_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for obj in object_rows:
        attrs = [
            ("source_stage", "DD096A candidate catalog-row design"),
            ("promotion_policy", "candidate_only_no_dbf_write"),
            ("baseline_status", "DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN"),
            ("purpose", obj.get("purpose", "")),
        ]
        if obj["objtype"] == "CATALOG_TABLE":
            attrs.extend([
                ("canonical_dbf_root", "dottalkpp/data/datadict"),
                ("canonical_index_root", "dottalkpp/data/indexes/datadict"),
                ("canonical_lmdb_root", "dottalkpp/data/lmdb/datadict"),
                ("primary_tag", obj.get("primary_tag", "")),
            ])
        for attr_name, attr_val in attrs:
            rows.append({
                "candidate_row_id": stable_id("CANDATTR", obj["candidate_objid"], attr_name),
                "target_table": "DDATTR",
                "candidate_attrid": stable_id("ATTR", obj["candidate_objid"], attr_name),
                "objid": obj["candidate_objid"],
                "attrname": attr_name,
                "attrval": attr_val,
                "status": "REVIEW_READY_CANDIDATE",
                "profile": "ENGINE",
                "evid": "EVID_DD096A_POLICY",
                "candidate_action": "UPSERT_CANDIDATE",
                "apply_now": 0,
            })
    return rows


def make_edge_rows(object_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    obj_by_name = {r["name"]: r for r in object_rows if r["objtype"] == "CATALOG_TABLE"}
    for from_name, to_name, key, edge_type, meaning in RELATIONS:
        rows.append({
            "candidate_row_id": stable_id("CANDEDGE", "DD096A", from_name, to_name, key),
            "target_table": "DDEDGE",
            "candidate_edgeid": stable_id("EDGE", "DD096A", from_name, to_name, key),
            "from_objid": obj_by_name[from_name]["candidate_objid"],
            "from_name": from_name,
            "to_objid": obj_by_name[to_name]["candidate_objid"],
            "to_name": to_name,
            "edge_type": edge_type,
            "key": key,
            "meaning": meaning,
            "status": "REVIEW_READY_CANDIDATE",
            "profile": "ENGINE",
            "evid": "EVID_DD094_WORKSPACE_SCHEMA",
            "candidate_action": "UPSERT_CANDIDATE",
            "apply_now": 0,
        })
    # DDICT command surface ownership edges.
    ddict_root = {
        "candidate_objid": stable_id("OBJ", "DD096A", "COMMAND", "DDICT"),
        "name": "DDICT",
    }
    for surface, _purpose in DDICT_SURFACES:
        surface_obj = next(r for r in object_rows if r["name"] == surface and r["objtype"] == "COMMAND_SURFACE")
        rows.append({
            "candidate_row_id": stable_id("CANDEDGE", "DD096A", "DDICT", surface),
            "target_table": "DDEDGE",
            "candidate_edgeid": stable_id("EDGE", "DD096A", "DDICT", surface),
            "from_objid": ddict_root["candidate_objid"],
            "from_name": "DDICT",
            "to_objid": surface_obj["candidate_objid"],
            "to_name": surface,
            "edge_type": "HAS_SURFACE",
            "key": "COMMAND",
            "meaning": "DDICT command has runtime surface",
            "status": "REVIEW_READY_CANDIDATE",
            "profile": "ENGINE",
            "evid": "EVID_DD092C_CMDHELPCHK_CANDIDATES",
            "candidate_action": "UPSERT_CANDIDATE",
            "apply_now": 0,
        })
    return rows


def make_evidence_rows() -> List[Dict[str, Any]]:
    rows = []
    for ddid, kind, meaning in LAYOUT_EVIDENCE:
        rows.append({
            "candidate_row_id": stable_id("CANDEVID", "DD096A", ddid),
            "target_table": "DDEVID",
            "candidate_evid": stable_id("EVID", "DD096A", ddid),
            "kind": kind,
            "srcid": f"SRC_{ddid}",
            "source": ddid,
            "artifact": f"docs/datadict/reports/{ddid}",
            "meaning": meaning,
            "status": "REVIEW_READY_CANDIDATE",
            "profile": "ENGINE",
            "candidate_action": "UPSERT_CANDIDATE",
            "apply_now": 0,
        })
    return rows


def make_gate_rows_candidate() -> List[Dict[str, Any]]:
    return [
        {
            "candidate_row_id": stable_id("CANDGATE", "DD096A", "NO_DBf_WRITES"),
            "target_table": "DDGATE",
            "gate_id": "DD096A_NO_DBF_WRITES",
            "gate_type": "SAFETY_BOUNDARY",
            "required_state": "candidate_only",
            "observed_state": "candidate_only",
            "status": "PASS",
            "candidate_action": "REVIEW_ONLY",
            "apply_now": 0,
        },
        {
            "candidate_row_id": stable_id("CANDGATE", "DD096A", "REQUIRES_EXPLICIT_APPLY"),
            "target_table": "DDGATE",
            "gate_id": "DD096A_REQUIRES_EXPLICIT_APPLY",
            "gate_type": "AUTHORIZATION_BOUNDARY",
            "required_state": "explicit_apply_authorization_required",
            "observed_state": "not_authorized",
            "status": "PASS",
            "candidate_action": "REVIEW_ONLY",
            "apply_now": 0,
        },
    ]


def make_design_doc(run_id: str, created_utc: str, counts: Dict[str, int]) -> str:
    return f"""# DD096A Candidate Catalog-Row Design for Data Dictionary Schema Promotion

Run id: `{run_id}`
Created UTC: `{created_utc}`

## Purpose

DD096A designs candidate catalog rows for representing the closed Data Dictionary baseline inside the Data Dictionary itself.

This is a candidate design only. It does not write DBF rows, update indexes, rebuild LMDB, mutate HELP/CMDHELPCHK, edit source, or regenerate catalog content.

## Candidate row families

- DDOBJECT candidates: **{counts['objects']}**
- DDATTR candidates: **{counts['attrs']}**
- DDEDGE candidates: **{counts['edges']}**
- DDEVID candidates: **{counts['evidence']}**
- DDGATE candidates: **{counts['gates']}**

## Design doctrine

1. Candidate rows are generated from the closed baseline, not from manuals.
2. Runtime artifacts and green manifests remain the source of truth.
3. All rows carry `apply_now = 0`.
4. A later apply lane must be separately authorized before any DBF writes.
5. HELP/CMDHELPCHK candidates remain separate and unapplied.

## Target interpretation

The closed Data Dictionary baseline can eventually be represented as:

```text
DDOBJECT  catalog table objects and DDICT command surfaces
DDATTR    purpose/path/policy attributes
DDEDGE    workspace relations and command-surface edges
DDEVID    evidence links back to DD093C-DD098
DDGATE    safety and authorization gates
```

## Boundary

DD096A is candidate-catalog-row-design/report-only. It does not mutate active catalog DBFs, append/replace/delete/pack/zap, create/rebuild CDX/LMDB, edit source, edit build files, edit command registration, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096A candidate catalog-row design for Data Dictionary schema promotion")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096A-candidate-catalog-row-design-v0")
    ap.add_argument("--dd096-dir", default="docs/datadict/reports/DD096-datadict-schema-promotion-catalog-policy-v0")
    ap.add_argument("--dd098-dir", default="docs/datadict/reports/DD098-datadict-baseline-closeout-v0")
    ap.add_argument("--write-candidate-pack", action="store_true")
    ap.add_argument("--candidate-pack-path", default="docs/datadict/candidates/DD096A_CANDIDATE_CATALOG_ROWS")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd096_manifest_path = repo / args.dd096_dir / "dd096_datadict_schema_promotion_catalog_policy_manifest.json"
    dd098_manifest_path = repo / args.dd098_dir / "dd098_datadict_baseline_closeout_manifest.json"
    dd096 = read_json(dd096_manifest_path)
    dd098 = read_json(dd098_manifest_path)

    object_rows = make_object_rows()
    attr_rows = make_attribute_rows(object_rows)
    edge_rows = make_edge_rows(object_rows)
    evidence_rows = make_evidence_rows()
    gate_candidate_rows = make_gate_rows_candidate()

    all_candidates = []
    for family, rows in [
        ("DDOBJECT", object_rows),
        ("DDATTR", attr_rows),
        ("DDEDGE", edge_rows),
        ("DDEVID", evidence_rows),
        ("DDGATE", gate_candidate_rows),
    ]:
        for r in rows:
            all_candidates.append({
                "family": family,
                "candidate_row_id": r["candidate_row_id"],
                "target_table": r["target_table"],
                "candidate_action": r.get("candidate_action", ""),
                "status": r.get("status", ""),
                "apply_now": r.get("apply_now", 0),
            })

    generated = out / "generated_candidate_catalog_rows"
    generated.mkdir(parents=True, exist_ok=True)
    write_csv(generated / "dd096a_candidate_ddobject_rows.csv", object_rows, ["candidate_row_id", "target_table", "candidate_objid", "objtype", "owner", "name", "status", "profile", "srcid", "purpose", "primary_tag", "candidate_action", "apply_now"])
    write_csv(generated / "dd096a_candidate_ddattr_rows.csv", attr_rows, ["candidate_row_id", "target_table", "candidate_attrid", "objid", "attrname", "attrval", "status", "profile", "evid", "candidate_action", "apply_now"])
    write_csv(generated / "dd096a_candidate_ddedge_rows.csv", edge_rows, ["candidate_row_id", "target_table", "candidate_edgeid", "from_objid", "from_name", "to_objid", "to_name", "edge_type", "key", "meaning", "status", "profile", "evid", "candidate_action", "apply_now"])
    write_csv(generated / "dd096a_candidate_ddevid_rows.csv", evidence_rows, ["candidate_row_id", "target_table", "candidate_evid", "kind", "srcid", "source", "artifact", "meaning", "status", "profile", "candidate_action", "apply_now"])
    write_csv(generated / "dd096a_candidate_ddgate_rows.csv", gate_candidate_rows, ["candidate_row_id", "target_table", "gate_id", "gate_type", "required_state", "observed_state", "status", "candidate_action", "apply_now"])
    write_csv(generated / "dd096a_candidate_catalog_row_index.csv", all_candidates, ["family", "candidate_row_id", "target_table", "candidate_action", "status", "apply_now"])
    write_json(generated / "dd096a_candidate_catalog_rows.json", {
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "candidate_only": True,
        "apply_now_total": sum(int(r["apply_now"]) for r in all_candidates),
        "ddobject": object_rows,
        "ddattr": attr_rows,
        "ddedge": edge_rows,
        "ddevid": evidence_rows,
        "ddgate": gate_candidate_rows,
    })

    counts = {
        "objects": len(object_rows),
        "attrs": len(attr_rows),
        "edges": len(edge_rows),
        "evidence": len(evidence_rows),
        "gates": len(gate_candidate_rows),
        "all": len(all_candidates),
    }
    design_doc = make_design_doc(args.run_id, utc_now(), counts)
    write_text(generated / "DD096A_CANDIDATE_CATALOG_ROW_DESIGN.md", design_doc)

    candidate_pack_written = 0
    candidate_pack_path = repo / args.candidate_pack_path
    if args.write_candidate_pack:
        candidate_pack_path.mkdir(parents=True, exist_ok=True)
        for f in generated.iterdir():
            if f.is_file():
                (candidate_pack_path / f.name).write_bytes(f.read_bytes())
        candidate_pack_written = 1

    artifact_rows = [
        artifact_row(repo, str(dd096_manifest_path.relative_to(repo)), "dd096_manifest"),
        artifact_row(repo, str(dd098_manifest_path.relative_to(repo)), "dd098_manifest"),
    ]
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))
    for f in sorted(generated.iterdir()):
        if f.is_file():
            artifact_rows.append({
                "role": "generated_candidate",
                "path": str(f),
                "exists": 1,
                "kind": "file",
                "bytes_or_children": f.stat().st_size,
                "sha256": sha256(f),
            })

    apply_now_total = sum(int(r["apply_now"]) for r in all_candidates)
    boundary_rows = [
        {"boundary": "candidate_catalog_row_design_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "apply_now_total", "observed": apply_now_total, "required": 0, "pass": int(apply_now_total == 0)},
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
        {"gate": "dd096_ready", "expected": EXPECTED_DD096_STATUS, "observed": dd096.get("status", ""), "pass": int(dd096.get("status") == EXPECTED_DD096_STATUS)},
        {"gate": "dd098_closed", "expected": EXPECTED_DD098_STATUS, "observed": dd098.get("status", ""), "pass": int(dd098.get("status") == EXPECTED_DD098_STATUS)},
        {"gate": "ddobject_candidate_rows", "expected": 19, "observed": len(object_rows), "pass": int(len(object_rows) == 19)},
        {"gate": "ddattr_candidate_rows", "expected": ">=76", "observed": len(attr_rows), "pass": int(len(attr_rows) >= 76)},
        {"gate": "ddedge_candidate_rows", "expected": 15, "observed": len(edge_rows), "pass": int(len(edge_rows) == 15)},
        {"gate": "ddevid_candidate_rows", "expected": 6, "observed": len(evidence_rows), "pass": int(len(evidence_rows) == 6)},
        {"gate": "ddgate_candidate_rows", "expected": 2, "observed": len(gate_candidate_rows), "pass": int(len(gate_candidate_rows) == 2)},
        {"gate": "apply_now_zero", "expected": 0, "observed": apply_now_total, "pass": int(apply_now_total == 0)},
        {"gate": "candidate_index_written", "expected": 1, "observed": int((generated / "dd096a_candidate_catalog_row_index.csv").exists()), "pass": int((generated / "dd096a_candidate_catalog_row_index.csv").exists())},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DATADICT_CANDIDATE_CATALOG_ROW_DESIGN_READY" if failures == 0 else "DATADICT_CANDIDATE_CATALOG_ROW_DESIGN_REVIEW"

    next_rows = [
        {"next_id": "DD096B", "title": "candidate row review and deduplication against active catalog", "allowed_scope": "read-only comparison; no DBF writes"},
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply planning", "allowed_scope": "only after explicit authorization"},
        {"next_id": "DD099", "title": "baseline-to-manual integration report", "allowed_scope": "documentation/explanation only"},
    ]

    write_csv(out / "dd096a_candidate_catalog_row_summary.csv", all_candidates, ["family", "candidate_row_id", "target_table", "candidate_action", "status", "apply_now"])
    write_csv(out / "dd096a_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096a_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd096a_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd096a_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD096A Candidate Catalog-Row Design

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096A designs candidate catalog rows for promoting the closed Data Dictionary baseline into catalog policy/evidence.

It is candidate-only. It does not write active catalog rows.

## Inputs

- DD096 status: `{dd096.get('status', '')}`
- DD098 status: `{dd098.get('status', '')}`

## Candidate counts

- DDOBJECT candidates: **{counts['objects']}**
- DDATTR candidates: **{counts['attrs']}**
- DDEDGE candidates: **{counts['edges']}**
- DDEVID candidates: **{counts['evidence']}**
- DDGATE candidates: **{counts['gates']}**
- Total candidate index rows: **{counts['all']}**
- apply_now total: **{apply_now_total}**

## Generated candidate directory

`{generated}`

## Boundary

DD096A is candidate-catalog-row-design/report-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    write_text(out / "DD096A_CANDIDATE_CATALOG_ROW_DESIGN_REPORT.md", report)

    manifest = {
        "contract": "dd096a_candidate_catalog_row_design_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd096_status": dd096.get("status", ""),
        "dd098_status": dd098.get("status", ""),
        "candidate_counts": counts,
        "apply_now_total": apply_now_total,
        "generated_candidate_dir": str(generated),
        "candidate_pack_written": candidate_pack_written,
        "candidate_pack_path": str(candidate_pack_path) if candidate_pack_written else "",
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
        "next_recommended_action": "DD096B read-only candidate row review/deduplication against active catalog.",
    }
    write_json(out / "dd096a_candidate_catalog_row_design_manifest.json", manifest)

    print(f"DD096A candidate catalog-row design manifest: {out / 'dd096a_candidate_catalog_row_design_manifest.json'}")
    print(f"status: {status}; candidates: {counts['all']}; objects: {counts['objects']}; attrs: {counts['attrs']}; edges: {counts['edges']}; evidence: {counts['evidence']}; gates: {counts['gates']}; apply_now: {apply_now_total}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
