#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD093C_STATUS = "DDICT_FULL_PATH_REMAP_RUNTIME_CLOSURE_GREEN"
EXPECTED_DD094_STATUS = "DATADICT_WORKSPACE_SCHEMA_SAVEPOINT_GREEN"
EXPECTED_DD092C_STATUS = "DDICT_CMDHELPCHK_CANDIDATE_RULES_GENERATED_REVIEW_READY"

LAYOUT_ROWS = [
    {
        "lane": "DATADICT_DBF_ROOT",
        "canonical_path": "dottalkpp/data/datadict",
        "purpose": "First-class Data Dictionary catalog DBFs.",
        "must_not_live_under": "dottalkpp/data/metadata/datadict",
        "policy": "Data Dictionary catalog tables are not feature metadata tables and must not collide with feature metadata roots.",
    },
    {
        "lane": "DATADICT_INDEX_ROOT",
        "canonical_path": "dottalkpp/data/indexes/datadict",
        "purpose": "CDX artifacts for Data Dictionary catalog tables.",
        "must_not_live_under": "dottalkpp/data/indexes",
        "policy": "Data Dictionary CDX files must live under the datadict index subroot, not the flat global index root.",
    },
    {
        "lane": "DATADICT_LMDB_ROOT",
        "canonical_path": "dottalkpp/data/lmdb/datadict",
        "purpose": "LMDB mirrors for Data Dictionary CDX artifacts.",
        "must_not_live_under": "dottalkpp/data/lmdb",
        "policy": "Data Dictionary LMDB mirrors must live under the datadict LMDB subroot, not the flat global LMDB root.",
    },
    {
        "lane": "DATADICT_WORKSPACE_SCHEMA",
        "canonical_path": "dottalkpp/data/workspaces/ddbase.dtschema",
        "purpose": "Workspace schema that restores 11 Data Dictionary areas and 7 core relations.",
        "must_not_live_under": "",
        "policy": "The ddbase workspace schema is the current controlled workspace entry point for the Data Dictionary catalog.",
    },
]

EXPECTED_TABLES = [
    "DDARTIF", "DDATTR", "DDBASE", "DDEDGE", "DDEVID", "DDGATE",
    "DDOBJECT", "DDPROFILE", "DDREVIEW", "DDRUN", "DDSOURCE",
]

EXPECTED_RELATIONS = [
    "DDOBJECT -> DDATTR ON OBJID",
    "DDOBJECT -> DDEVID ON OBJID",
    "DDSOURCE -> DDEVID ON SRCID",
    "DDRUN -> DDARTIF ON RUNID",
    "DDRUN -> DDBASE ON RUNID",
    "DDRUN -> DDGATE ON RUNID",
    "DDRUN -> DDREVIEW ON RUNID",
]

PROTECTED_ARTIFACTS = [
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
    "dottalkpp/data/workspaces/ddbase.dtschema",
    "dottalkpp/data/metadata",
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


def build_policy_doc(run_id: str, created_utc: str) -> str:
    table_lines = "\n".join(f"- `{t}`" for t in EXPECTED_TABLES)
    rel_lines = "\n".join(f"- `{r}`" for r in EXPECTED_RELATIONS)
    layout_lines = "\n".join(
        f"- **{r['lane']}**: `{r['canonical_path']}` — {r['purpose']}"
        for r in LAYOUT_ROWS
    )
    anti_lines = "\n".join(
        f"- `{r['canonical_path']}` must not be collapsed into `{r['must_not_live_under']}`."
        for r in LAYOUT_ROWS if r["must_not_live_under"]
    )
    return f"""# DD095 Data Dictionary Layout Policy

Run id: `{run_id}`
Created UTC: `{created_utc}`

## Purpose

DD095 records the accepted Data Dictionary layout policy after the DD093C full path-remap closure and DD094 workspace schema savepoint.

The Data Dictionary is a first-class catalog lane. It must not be stored under the feature-metadata catalog root.

## Accepted layout

{layout_lines}

## Anti-collision rule

The Data Dictionary catalog is not the feature metadata catalog.

{anti_lines}

The legacy path `dottalkpp/data/metadata/datadict` may remain a historical or migration reference, but it must not be the active Data Dictionary catalog root when `dottalkpp/data/datadict` is present.

## Current catalog table set

{table_lines}

## Current workspace relation set

{rel_lines}

## Runtime doctrine

- `DDICT` reads the Data Dictionary catalog in read-only mode.
- `DDICT STATUS`, `DDICT TABLES`, `DDICT TAGS`, `DDICT REL`, and `DDICT EVIDENCE` should resolve against `dottalkpp/data/datadict`.
- CDX artifacts should resolve under `dottalkpp/data/indexes/datadict`.
- LMDB mirrors should resolve under `dottalkpp/data/lmdb/datadict`.
- `ddbase.dtschema` is the current controlled workspace schema for restoring the Data Dictionary work areas and relations.

## Boundary

This policy document is explanatory and report-only. It does not mutate source files, build files, registry files, active catalog DBFs, CDX/LMDB artifacts, HELP/META/CMDHELPCHK data, generated catalog content, or manual rows.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD095 Data Dictionary layout policy documentation")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD095-datadict-layout-policy-documentation-v0")
    ap.add_argument("--dd093c-dir", default="docs/datadict/reports/DD093C-ddict-full-path-remap-runtime-closure-v0")
    ap.add_argument("--dd094-dir", default="docs/datadict/reports/DD094-datadict-workspace-schema-savepoint-v0")
    ap.add_argument("--dd092c-dir", default="docs/datadict/reports/DD092C-cmdhelpchk-candidate-rule-generation-v0")
    ap.add_argument("--write-policy", action="store_true")
    ap.add_argument("--policy-path", default="docs/datadict/policy/DD095_DATADICT_LAYOUT_POLICY.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd093c_manifest_path = repo / args.dd093c_dir / "dd093c_ddict_full_path_remap_runtime_closure_manifest.json"
    dd094_manifest_path = repo / args.dd094_dir / "dd094_datadict_workspace_schema_savepoint_manifest.json"
    dd092c_manifest_path = repo / args.dd092c_dir / "dd092c_cmdhelpchk_candidate_rule_generation_manifest.json"

    dd093c = read_json(dd093c_manifest_path)
    dd094 = read_json(dd094_manifest_path)
    dd092c = read_json(dd092c_manifest_path)

    created_utc = utc_now()
    policy_doc = build_policy_doc(args.run_id, created_utc)
    generated_dir = out / "generated_policy"
    generated_dir.mkdir(parents=True, exist_ok=True)
    generated_policy_path = generated_dir / "DD095_DATADICT_LAYOUT_POLICY.md"
    write_text(generated_policy_path, policy_doc)

    layout_rows = []
    for r in LAYOUT_ROWS:
        p = repo / r["canonical_path"]
        row = dict(r)
        row.update({
            "exists": int(p.exists()),
            "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
            "bytes_or_children": p.stat().st_size if p.exists() and p.is_file() else sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else 0,
        })
        layout_rows.append(row)

    table_rows = []
    for table in EXPECTED_TABLES:
        lower = table.lower()
        dbf = repo / "dottalkpp/data/datadict" / f"{table}.dbf"
        cdx = repo / "dottalkpp/data/indexes/datadict" / f"{lower}.cdx"
        lmdb_upper = repo / "dottalkpp/data/lmdb/datadict" / f"{table}.cdx.d"
        lmdb_lower = repo / "dottalkpp/data/lmdb/datadict" / f"{lower}.cdx.d"
        table_rows.append({
            "table": table,
            "dbf_exists": int(dbf.exists()),
            "cdx_exists": int(cdx.exists()),
            "lmdb_exists_any_case": int(lmdb_upper.exists() or lmdb_lower.exists()),
            "dbf_path": f"dottalkpp/data/datadict/{table}.dbf",
            "cdx_path": f"dottalkpp/data/indexes/datadict/{lower}.cdx",
            "lmdb_path_upper": f"dottalkpp/data/lmdb/datadict/{table}.cdx.d",
            "lmdb_path_lower": f"dottalkpp/data/lmdb/datadict/{lower}.cdx.d",
        })

    relation_rows = [{"relation": r, "policy_status": "accepted_dd094_workspace_relation"} for r in EXPECTED_RELATIONS]

    artifact_rows = [
        artifact_row(repo, str(Path(args.dd093c_dir) / "dd093c_ddict_full_path_remap_runtime_closure_manifest.json"), "dd093c_manifest"),
        artifact_row(repo, str(Path(args.dd094_dir) / "dd094_datadict_workspace_schema_savepoint_manifest.json"), "dd094_manifest"),
        artifact_row(repo, str(Path(args.dd092c_dir) / "dd092c_cmdhelpchk_candidate_rule_generation_manifest.json"), "dd092c_manifest"),
    ]
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))

    boundary_rows = [
        {"boundary": "layout_policy_documentation_only", "observed": 1, "required": 1, "pass": 1},
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

    dbf_count = sum(int(r["dbf_exists"]) for r in table_rows)
    cdx_count = sum(int(r["cdx_exists"]) for r in table_rows)
    lmdb_count = sum(int(r["lmdb_exists_any_case"]) for r in table_rows)
    layout_count = sum(int(r["exists"]) for r in layout_rows)

    gates = [
        {"gate": "dd093c_green", "expected": EXPECTED_DD093C_STATUS, "observed": dd093c.get("status", ""), "pass": int(dd093c.get("status") == EXPECTED_DD093C_STATUS)},
        {"gate": "dd094_green", "expected": EXPECTED_DD094_STATUS, "observed": dd094.get("status", ""), "pass": int(dd094.get("status") == EXPECTED_DD094_STATUS)},
        {"gate": "dd092c_review_ready", "expected": EXPECTED_DD092C_STATUS, "observed": dd092c.get("status", ""), "pass": int(dd092c.get("status") == EXPECTED_DD092C_STATUS)},
        {"gate": "layout_roots_present", "expected": len(LAYOUT_ROWS), "observed": layout_count, "pass": int(layout_count == len(LAYOUT_ROWS))},
        {"gate": "table_dbfs_present", "expected": 11, "observed": dbf_count, "pass": int(dbf_count == 11)},
        {"gate": "table_cdxs_present", "expected": 11, "observed": cdx_count, "pass": int(cdx_count == 11)},
        {"gate": "table_lmdbs_present", "expected": 11, "observed": lmdb_count, "pass": int(lmdb_count == 11)},
        {"gate": "policy_generated", "expected": 1, "observed": int(generated_policy_path.exists()), "pass": int(generated_policy_path.exists())},
    ]

    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DATADICT_LAYOUT_POLICY_DOCUMENTED_GREEN" if failures == 0 else "DATADICT_LAYOUT_POLICY_DOCUMENTED_REVIEW"

    policy_written = 0
    policy_path = repo / args.policy_path
    if args.write_policy:
        write_text(policy_path, policy_doc)
        policy_written = 1

    next_rows = [
        {"next_id": "DD096", "title": "Data Dictionary schema promotion/catalog policy", "allowed_scope": "report-only policy and schema planning"},
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply planning", "allowed_scope": "only after explicit authorization and candidate review"},
        {"next_id": "DD097", "title": "Data Dictionary layout regression smoke package", "allowed_scope": "runtime smoke/proof generation only"},
    ]

    write_csv(out / "dd095_layout_policy_ledger.csv", layout_rows, ["lane", "canonical_path", "purpose", "must_not_live_under", "policy", "exists", "kind", "bytes_or_children"])
    write_csv(out / "dd095_catalog_table_artifact_policy.csv", table_rows, ["table", "dbf_exists", "cdx_exists", "lmdb_exists_any_case", "dbf_path", "cdx_path", "lmdb_path_upper", "lmdb_path_lower"])
    write_csv(out / "dd095_workspace_relation_policy.csv", relation_rows, ["relation", "policy_status"])
    write_csv(out / "dd095_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd095_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd095_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd095_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD095 Data Dictionary Layout Policy Documentation

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{created_utc}`

## Purpose

DD095 documents the accepted Data Dictionary layout and anti-collision rule after DD093C and DD094.

## Inputs

- DD093C status: `{dd093c.get('status', '')}`
- DD094 status: `{dd094.get('status', '')}`
- DD092C status: `{dd092c.get('status', '')}`

## Summary

- Layout roots present: **{layout_count} / {len(LAYOUT_ROWS)}**
- DBF artifacts present: **{dbf_count} / 11**
- CDX artifacts present: **{cdx_count} / 11**
- LMDB artifacts present: **{lmdb_count} / 11**
- Generated policy: `{generated_policy_path}`
- Policy written to repo: **{policy_written}**

## Policy

The Data Dictionary is a first-class catalog lane:

```text
DBF     dottalkpp/data/datadict
INDEXES dottalkpp/data/indexes/datadict
LMDB    dottalkpp/data/lmdb/datadict
```

It must not live under `dottalkpp/data/metadata/datadict`, because that collides conceptually and operationally with feature metadata.

## Boundary

DD095 is layout-policy-documentation/report-only unless `--write-policy` is explicitly supplied. Even with `--write-policy`,
it writes only the policy document path and does not edit C++ source, build files, command registration,
active catalog DBFs, CDX/LMDB artifacts, HELP/META/CMDHELPCHK, generated catalog content, or manual rows.
"""
    write_text(out / "DD095_DATADICT_LAYOUT_POLICY_DOCUMENTATION_REPORT.md", report)

    manifest = {
        "contract": "dd095_datadict_layout_policy_documentation_v0",
        "run_id": args.run_id,
        "created_utc": created_utc,
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd093c_status": dd093c.get("status", ""),
        "dd094_status": dd094.get("status", ""),
        "dd092c_status": dd092c.get("status", ""),
        "layout_roots_present": layout_count,
        "dbf_artifacts_present": dbf_count,
        "cdx_artifacts_present": cdx_count,
        "lmdb_artifacts_present": lmdb_count,
        "generated_policy_path": str(generated_policy_path),
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
        "next_recommended_action": "DD096 schema promotion/catalog policy or DD092D guarded HELP/CMDHELPCHK apply planning after explicit authorization.",
    }
    write_json(out / "dd095_datadict_layout_policy_documentation_manifest.json", manifest)

    print(f"DD095 Data Dictionary layout policy documentation manifest: {out / 'dd095_datadict_layout_policy_documentation_manifest.json'}")
    print(f"status: {status}; layout_roots: {layout_count}/{len(LAYOUT_ROWS)}; dbf: {dbf_count}/11; cdx: {cdx_count}/11; lmdb: {lmdb_count}/11; failures: {failures}; policy_written: {policy_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
