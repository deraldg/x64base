#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD094_STATUS = "DATADICT_WORKSPACE_SCHEMA_SAVEPOINT_GREEN"
EXPECTED_DD095_STATUS = "DATADICT_LAYOUT_POLICY_DOCUMENTED_GREEN"
EXPECTED_DD092C_STATUS = "DDICT_CMDHELPCHK_CANDIDATE_RULES_GENERATED_REVIEW_READY"

CATALOG_TABLES = [
    ("DDARTIF", "Catalog artifact/report references"),
    ("DDATTR", "Catalog object attributes"),
    ("DDBASE", "Catalog/base-level metadata"),
    ("DDEDGE", "Catalog object relationship edges"),
    ("DDEVID", "Evidence links for catalog objects and artifacts"),
    ("DDGATE", "Gate/checkpoint records"),
    ("DDOBJECT", "Catalog objects such as tables, fields, tags, commands, and surfaces"),
    ("DDPROFILE", "Profile definitions"),
    ("DDREVIEW", "Review records"),
    ("DDRUN", "Run records"),
    ("DDSOURCE", "Source/provenance roots"),
]

RELATIONS = [
    ("DDOBJECT", "DDATTR", "OBJID", "object_has_attributes"),
    ("DDOBJECT", "DDEVID", "OBJID", "object_has_evidence"),
    ("DDSOURCE", "DDEVID", "SRCID", "source_has_evidence"),
    ("DDRUN", "DDARTIF", "RUNID", "run_has_artifacts"),
    ("DDRUN", "DDBASE", "RUNID", "run_has_base_records"),
    ("DDRUN", "DDGATE", "RUNID", "run_has_gates"),
    ("DDRUN", "DDREVIEW", "RUNID", "run_has_reviews"),
]

POLICY_LANES = [
    {
        "lane": "SCHEMA_BASELINE",
        "source_of_truth": "ddbase.dtschema + Data Dictionary catalog artifacts",
        "promotion_target": "catalog policy evidence",
        "rule": "The active Data Dictionary schema baseline is the 11-table, 7-relation workspace proven by DD094.",
    },
    {
        "lane": "RUNTIME_READ_SURFACE",
        "source_of_truth": "DDICT runtime proofs",
        "promotion_target": "runtime-inspection policy",
        "rule": "DDICT is a read-only inspection surface, not a catalog repair or mutation command.",
    },
    {
        "lane": "LAYOUT_POLICY",
        "source_of_truth": "DD095 layout policy",
        "promotion_target": "path/root doctrine",
        "rule": "Data Dictionary lives under data/datadict, data/indexes/datadict, and data/lmdb/datadict, not metadata/datadict.",
    },
    {
        "lane": "HELP_CMDHELPCHK_CANDIDATES",
        "source_of_truth": "DD092A/B/C candidate outputs",
        "promotion_target": "review-ready HELP/CMDHELPCHK candidates",
        "rule": "Candidates are not applied until a later explicit guarded apply lane.",
    },
    {
        "lane": "MANUAL_DOWNSTREAM",
        "source_of_truth": "reports and runtime proof",
        "promotion_target": "manual/explanatory docs",
        "rule": "Manuals explain the Data Dictionary; they do not serve as its source of truth.",
    },
]

SOURCE_OF_TRUTH_ROWS = [
    {
        "rank": 1,
        "source": "runtime artifacts",
        "examples": "DBF/CDX/LMDB files, workspace schema, DDICT runtime output",
        "trust_level": "highest",
        "notes": "Runtime proves actual availability and pathing.",
    },
    {
        "rank": 2,
        "source": "green report manifests",
        "examples": "DD093C, DD094, DD095, DD092C manifests",
        "trust_level": "high",
        "notes": "Report manifests summarize validated proof and boundaries.",
    },
    {
        "rank": 3,
        "source": "candidate policy files",
        "examples": "DD095 policy document, DD096 generated policy",
        "trust_level": "policy",
        "notes": "Policy records accepted doctrine and next-step boundaries.",
    },
    {
        "rank": 4,
        "source": "manuals and explanatory documents",
        "examples": "developer manual, student/user manuals",
        "trust_level": "downstream",
        "notes": "Manuals explain; they must not drive active catalog truth.",
    },
]

PROTECTED_ARTIFACTS = [
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
    "dottalkpp/data/workspaces/ddbase.dtschema",
    "docs/datadict/policy/DD095_DATADICT_LAYOUT_POLICY.md",
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


def schema_object_rows(repo: Path) -> List[Dict[str, Any]]:
    rows = []
    for table, purpose in CATALOG_TABLES:
        lower = table.lower()
        dbf = repo / "dottalkpp/data/datadict" / f"{table}.dbf"
        cdx = repo / "dottalkpp/data/indexes/datadict" / f"{lower}.cdx"
        lmdb_upper = repo / "dottalkpp/data/lmdb/datadict" / f"{table}.cdx.d"
        lmdb_lower = repo / "dottalkpp/data/lmdb/datadict" / f"{lower}.cdx.d"
        rows.append({
            "object_name": table,
            "candidate_objtype": "CATALOG_TABLE",
            "policy_status": "ACCEPTED_BASELINE_CANDIDATE",
            "purpose": purpose,
            "dbf_path": f"dottalkpp/data/datadict/{table}.dbf",
            "dbf_exists": int(dbf.exists()),
            "cdx_path": f"dottalkpp/data/indexes/datadict/{lower}.cdx",
            "cdx_exists": int(cdx.exists()),
            "lmdb_path_upper": f"dottalkpp/data/lmdb/datadict/{table}.cdx.d",
            "lmdb_path_lower": f"dottalkpp/data/lmdb/datadict/{lower}.cdx.d",
            "lmdb_exists_any_case": int(lmdb_upper.exists() or lmdb_lower.exists()),
            "promotion_now": 0,
        })
    return rows


def relation_policy_rows() -> List[Dict[str, Any]]:
    rows = []
    for parent, child, key, meaning in RELATIONS:
        rows.append({
            "from_object": parent,
            "to_object": child,
            "key": key,
            "relation_meaning": meaning,
            "candidate_edge_type": "WORKSPACE_RELATION",
            "policy_status": "ACCEPTED_BASELINE_CANDIDATE",
            "promotion_now": 0,
        })
    return rows


def build_policy_doc(run_id: str, created_utc: str) -> str:
    table_lines = "\n".join(f"- `{name}` — {purpose}" for name, purpose in CATALOG_TABLES)
    relation_lines = "\n".join(f"- `{a} -> {b} ON {key}` — {meaning}" for a, b, key, meaning in RELATIONS)
    lane_lines = "\n".join(f"- **{r['lane']}**: {r['rule']}" for r in POLICY_LANES)
    source_lines = "\n".join(f"{r['rank']}. **{r['source']}** — {r['notes']}" for r in SOURCE_OF_TRUTH_ROWS)
    return f"""# DD096 Data Dictionary Schema Promotion / Catalog Policy

Run id: `{run_id}`
Created UTC: `{created_utc}`

## Purpose

DD096 defines how the active Data Dictionary schema baseline should be represented as catalog policy and evidence.

This is a report-only policy stage. It does not write Data Dictionary rows, promote schema records, edit HELP/CMDHELPCHK, edit source, rebuild indexes, or mutate runtime data.

## Baseline schema

The accepted baseline is the 11-table Data Dictionary catalog proven by DD094:

{table_lines}

## Baseline workspace relations

The accepted workspace relation set is:

{relation_lines}

## Promotion doctrine

{lane_lines}

## Source-of-truth order

{source_lines}

## Promotion rules

1. Runtime artifacts and green runtime proofs are the primary source of truth.
2. The Data Dictionary should eventually describe itself using `DDOBJECT`, `DDATTR`, `DDEDGE`, `DDEVID`, `DDSOURCE`, `DDARTIF`, `DDRUN`, `DDGATE`, and `DDREVIEW`.
3. Schema-promotion candidate rows must remain candidate-only until an explicit apply package is authorized.
4. Manuals and narrative reports explain the schema, but they do not define or overwrite active catalog truth.
5. HELP/CMDHELPCHK integration remains candidate-only until reviewed and explicitly authorized.
6. The Data Dictionary must remain separate from the feature metadata root.

## Current accepted layout

```text
DBF     dottalkpp/data/datadict
INDEXES dottalkpp/data/indexes/datadict
LMDB    dottalkpp/data/lmdb/datadict
```

## Boundary

DD096 is policy/report-only. It does not edit C++ source, build files, command registry files, active catalog DBFs, CDX/LMDB artifacts, HELP/META/CMDHELPCHK data, generated catalog content, or manual rows.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096 Data Dictionary schema promotion / catalog policy")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096-datadict-schema-promotion-catalog-policy-v0")
    ap.add_argument("--dd094-dir", default="docs/datadict/reports/DD094-datadict-workspace-schema-savepoint-v0")
    ap.add_argument("--dd095-dir", default="docs/datadict/reports/DD095-datadict-layout-policy-documentation-v0")
    ap.add_argument("--dd092c-dir", default="docs/datadict/reports/DD092C-cmdhelpchk-candidate-rule-generation-v0")
    ap.add_argument("--write-policy", action="store_true")
    ap.add_argument("--policy-path", default="docs/datadict/policy/DD096_DATADICT_SCHEMA_PROMOTION_POLICY.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd094_manifest_path = repo / args.dd094_dir / "dd094_datadict_workspace_schema_savepoint_manifest.json"
    dd095_manifest_path = repo / args.dd095_dir / "dd095_datadict_layout_policy_documentation_manifest.json"
    dd092c_manifest_path = repo / args.dd092c_dir / "dd092c_cmdhelpchk_candidate_rule_generation_manifest.json"

    dd094 = read_json(dd094_manifest_path)
    dd095 = read_json(dd095_manifest_path)
    dd092c = read_json(dd092c_manifest_path)

    created_utc = utc_now()
    policy_doc = build_policy_doc(args.run_id, created_utc)
    generated_dir = out / "generated_policy"
    generated_dir.mkdir(parents=True, exist_ok=True)
    generated_policy_path = generated_dir / "DD096_DATADICT_SCHEMA_PROMOTION_POLICY.md"
    write_text(generated_policy_path, policy_doc)

    object_rows = schema_object_rows(repo)
    relation_rows = relation_policy_rows()
    lane_rows = [dict(r, promotion_now=0) for r in POLICY_LANES]
    truth_rows = [dict(r, promotion_now=0) for r in SOURCE_OF_TRUTH_ROWS]

    evidence_rows = [
        {
            "evidence_id": "DD093C_PATH_REMAP",
            "evidence_kind": "runtime_closure",
            "source": "DD093C",
            "meaning": "DDICT resolves DBF/CDX/LMDB under datadict roots.",
            "candidate_catalog_use": "DDEVID/DDARTIF/DDRUN provenance evidence",
            "promotion_now": 0,
        },
        {
            "evidence_id": "DD094_WORKSPACE_SCHEMA",
            "evidence_kind": "workspace_savepoint",
            "source": "DD094",
            "meaning": "ddbase.dtschema restores 11 areas and 7 relations; artifacts are present.",
            "candidate_catalog_use": "DDBASE/DDEDGE/DDARTIF/DDRUN policy evidence",
            "promotion_now": 0,
        },
        {
            "evidence_id": "DD095_LAYOUT_POLICY",
            "evidence_kind": "layout_policy",
            "source": "DD095",
            "meaning": "Data Dictionary layout and anti-collision rule documented.",
            "candidate_catalog_use": "DDSOURCE/DDARTIF/DDREVIEW policy evidence",
            "promotion_now": 0,
        },
        {
            "evidence_id": "DD092C_CMDHELPCHK_CANDIDATES",
            "evidence_kind": "candidate_help_cmdhelpchk",
            "source": "DD092C",
            "meaning": "DDICT HELP/CMDHELPCHK candidates generated but not applied.",
            "candidate_catalog_use": "DDREVIEW/DDGATE candidate review evidence",
            "promotion_now": 0,
        },
    ]

    artifact_rows = [
        artifact_row(repo, str(Path(args.dd094_dir) / "dd094_datadict_workspace_schema_savepoint_manifest.json"), "dd094_manifest"),
        artifact_row(repo, str(Path(args.dd095_dir) / "dd095_datadict_layout_policy_documentation_manifest.json"), "dd095_manifest"),
        artifact_row(repo, str(Path(args.dd092c_dir) / "dd092c_cmdhelpchk_candidate_rule_generation_manifest.json"), "dd092c_manifest"),
    ]
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))

    object_ready = sum(1 for r in object_rows if int(r["dbf_exists"]) and int(r["cdx_exists"]) and int(r["lmdb_exists_any_case"]))
    relation_ready = len(relation_rows)
    promotion_now_total = (
        sum(int(r["promotion_now"]) for r in object_rows)
        + sum(int(r["promotion_now"]) for r in relation_rows)
        + sum(int(r["promotion_now"]) for r in lane_rows)
        + sum(int(r["promotion_now"]) for r in truth_rows)
        + sum(int(r["promotion_now"]) for r in evidence_rows)
    )

    boundary_rows = [
        {"boundary": "schema_promotion_policy_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "promotion_now", "observed": promotion_now_total, "required": 0, "pass": int(promotion_now_total == 0)},
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
        {"gate": "dd094_green", "expected": EXPECTED_DD094_STATUS, "observed": dd094.get("status", ""), "pass": int(dd094.get("status") == EXPECTED_DD094_STATUS)},
        {"gate": "dd095_green", "expected": EXPECTED_DD095_STATUS, "observed": dd095.get("status", ""), "pass": int(dd095.get("status") == EXPECTED_DD095_STATUS)},
        {"gate": "dd092c_review_ready", "expected": EXPECTED_DD092C_STATUS, "observed": dd092c.get("status", ""), "pass": int(dd092c.get("status") == EXPECTED_DD092C_STATUS)},
        {"gate": "schema_objects_ready", "expected": 11, "observed": object_ready, "pass": int(object_ready == 11)},
        {"gate": "relations_policy_rows", "expected": 7, "observed": relation_ready, "pass": int(relation_ready == 7)},
        {"gate": "policy_lanes", "expected": len(POLICY_LANES), "observed": len(lane_rows), "pass": int(len(lane_rows) == len(POLICY_LANES))},
        {"gate": "source_of_truth_rows", "expected": len(SOURCE_OF_TRUTH_ROWS), "observed": len(truth_rows), "pass": int(len(truth_rows) == len(SOURCE_OF_TRUTH_ROWS))},
        {"gate": "promotion_now_zero", "expected": 0, "observed": promotion_now_total, "pass": int(promotion_now_total == 0)},
        {"gate": "policy_generated", "expected": 1, "observed": int(generated_policy_path.exists()), "pass": int(generated_policy_path.exists())},
    ]

    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DATADICT_SCHEMA_PROMOTION_CATALOG_POLICY_READY" if failures == 0 else "DATADICT_SCHEMA_PROMOTION_CATALOG_POLICY_REVIEW"

    policy_written = 0
    policy_path = repo / args.policy_path
    if args.write_policy:
        write_text(policy_path, policy_doc)
        policy_written = 1

    next_rows = [
        {"next_id": "DD097", "title": "Data Dictionary layout regression smoke package", "allowed_scope": "runtime smoke/proof only"},
        {"next_id": "DD096A", "title": "candidate catalog-row design for schema promotion", "allowed_scope": "candidate rows only; no DBF writes"},
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply planning", "allowed_scope": "only after explicit authorization and candidate review"},
    ]

    write_csv(out / "dd096_schema_object_policy.csv", object_rows, ["object_name", "candidate_objtype", "policy_status", "purpose", "dbf_path", "dbf_exists", "cdx_path", "cdx_exists", "lmdb_path_upper", "lmdb_path_lower", "lmdb_exists_any_case", "promotion_now"])
    write_csv(out / "dd096_relation_policy.csv", relation_rows, ["from_object", "to_object", "key", "relation_meaning", "candidate_edge_type", "policy_status", "promotion_now"])
    write_csv(out / "dd096_promotion_policy_lanes.csv", lane_rows, ["lane", "source_of_truth", "promotion_target", "rule", "promotion_now"])
    write_csv(out / "dd096_source_of_truth_policy.csv", truth_rows, ["rank", "source", "examples", "trust_level", "notes", "promotion_now"])
    write_csv(out / "dd096_evidence_policy.csv", evidence_rows, ["evidence_id", "evidence_kind", "source", "meaning", "candidate_catalog_use", "promotion_now"])
    write_csv(out / "dd096_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd096_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd096_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD096 Data Dictionary Schema Promotion / Catalog Policy

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{created_utc}`

## Purpose

DD096 defines how the active Data Dictionary schema baseline should be represented as catalog policy and evidence.

It is report-only. It does not write catalog rows, mutate DBFs, change HELP/CMDHELPCHK, edit source, rebuild indexes, or repair manuals.

## Inputs

- DD094 status: `{dd094.get('status', '')}`
- DD095 status: `{dd095.get('status', '')}`
- DD092C status: `{dd092c.get('status', '')}`

## Summary

- Schema object candidates ready: **{object_ready} / 11**
- Relation policy rows: **{relation_ready} / 7**
- Policy lanes: **{len(lane_rows)}**
- Source-of-truth rows: **{len(truth_rows)}**
- Promotion-now rows: **{promotion_now_total}**
- Generated policy: `{generated_policy_path}`
- Policy written to repo: **{policy_written}**

## Key decision

The Data Dictionary schema may be represented as catalog policy evidence, but not applied to active catalog rows until a later explicit guarded apply package.

## Boundary

DD096 is schema-promotion-policy/report-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    write_text(out / "DD096_DATADICT_SCHEMA_PROMOTION_CATALOG_POLICY_REPORT.md", report)

    manifest = {
        "contract": "dd096_datadict_schema_promotion_catalog_policy_v0",
        "run_id": args.run_id,
        "created_utc": created_utc,
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd094_status": dd094.get("status", ""),
        "dd095_status": dd095.get("status", ""),
        "dd092c_status": dd092c.get("status", ""),
        "schema_objects_ready": object_ready,
        "relation_policy_rows": relation_ready,
        "policy_lanes": len(lane_rows),
        "source_of_truth_rows": len(truth_rows),
        "promotion_now_total": promotion_now_total,
        "policy_written": policy_written,
        "policy_path": str(policy_path) if policy_written else "",
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
        "next_recommended_action": "DD097 layout regression smoke package, or DD096A candidate catalog-row design with no DBF writes.",
    }
    write_json(out / "dd096_datadict_schema_promotion_catalog_policy_manifest.json", manifest)

    print(f"DD096 Data Dictionary schema promotion/catalog policy manifest: {out / 'dd096_datadict_schema_promotion_catalog_policy_manifest.json'}")
    print(f"status: {status}; schema_objects: {object_ready}/11; relations: {relation_ready}/7; promotion_now: {promotion_now_total}; failures: {failures}; policy_written: {policy_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
