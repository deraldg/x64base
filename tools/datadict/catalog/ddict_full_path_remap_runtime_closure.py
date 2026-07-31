#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD093B_STATUS = "DDICT_INDEX_LMDB_SUBROOT_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"

REQUIRED_RUNTIME_NEEDLES = [
    ("active_catalog_new_root", "Active catalog: D:\\code\\ccode\\dottalkpp\\data\\datadict"),
    ("dbf_tables_11", "DBF tables    : 11 / 11"),
    ("catalog_present", "Catalog state : ACTIVE_CATALOG_PRESENT"),
    ("ddict_tables", "DDICT TABLES"),
    ("ddict_tags_ddattr", "DDICT TAGS DDATTR"),
    ("ddattr_cdx_subroot", "data\\indexes\\datadict\\ddattr.cdx"),
    ("ddattr_lmdb_subroot", "data\\lmdb\\datadict\\DDATTR.cdx.d"),
    ("ddict_tags_ddobject", "DDICT TAGS DDOBJECT"),
    ("ddobject_cdx_subroot", "data\\indexes\\datadict\\ddobject.cdx"),
    ("ddobject_lmdb_subroot", "data\\lmdb\\datadict\\DDOBJECT.cdx.d"),
]

WORKSPACE_TABLES = [
    "DDARTIF", "DDATTR", "DDBASE", "DDEDGE", "DDEVID", "DDGATE",
    "DDOBJECT", "DDPROFILE", "DDREVIEW", "DDRUN", "DDSOURCE",
]

WORKSPACE_RELATIONS = [
    "RELATION DDOBJECT DDATTR ON OBJID",
    "RELATION DDOBJECT DDEVID ON OBJID",
    "RELATION DDSOURCE DDEVID ON SRCID",
    "RELATION DDRUN DDARTIF ON RUNID",
    "RELATION DDRUN DDBASE ON RUNID",
    "RELATION DDRUN DDGATE ON RUNID",
    "RELATION DDRUN DDREVIEW ON RUNID",
]

PROTECTED_ARTIFACTS = [
    "src/datadict/ddict_catalog_paths.cpp",
    "src/cli/cmd_ddict.cpp",
    "src/CMakeLists.txt",
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
    "dottalkpp/data/workspaces/ddbase.dtschema",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    if not path.exists():
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
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


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


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-093C DDICT full path-remap runtime closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD093C-ddict-full-path-remap-runtime-closure-v0")
    ap.add_argument("--dd093b-dir", default="docs/datadict/reports/DD093B-ddict-index-lmdb-subroot-repair-apply-v1")
    ap.add_argument("--runtime-proof", required=True)
    ap.add_argument("--workspace-schema", default="dottalkpp/data/workspaces/ddbase.dtschema")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-093C_DDICT_FULL_PATH_REMAP_RUNTIME_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd093b_manifest_path = repo / args.dd093b_dir / "dd093b_ddict_index_lmdb_subroot_repair_manifest.json"
    dd093b = read_json(dd093b_manifest_path)

    runtime_path = repo / args.runtime_proof
    schema_path = repo / args.workspace_schema

    runtime_text = read_text(runtime_path)
    runtime_lower = runtime_text.lower()
    schema_text = read_text(schema_path)
    schema_upper = schema_text.upper()

    runtime_rows = []
    for key, needle in REQUIRED_RUNTIME_NEEDLES:
        runtime_rows.append({
            "proof_key": key,
            "needle": needle,
            "seen": int(needle.lower() in runtime_lower),
        })

    workspace_rows = []
    for table in WORKSPACE_TABLES:
        workspace_rows.append({
            "kind": "area",
            "name": table,
            "seen": int(f"DBF={table}.DBF" in schema_upper or f"ALIAS={table}" in schema_upper),
        })
    for relation in WORKSPACE_RELATIONS:
        workspace_rows.append({
            "kind": "relation",
            "name": relation,
            "seen": int(relation in schema_upper),
        })

    artifact_rows = []
    for role, path in [
        ("dd093b_manifest", str(Path(args.dd093b_dir) / "dd093b_ddict_index_lmdb_subroot_repair_manifest.json")),
        ("runtime_proof", args.runtime_proof),
        ("workspace_schema", args.workspace_schema),
    ]:
        artifact_rows.append(artifact_row(repo, path, role))
    for path in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, path, "protected_observed"))

    gate_rows = [
        {
            "gate": "dd093b_applied",
            "expected": EXPECTED_DD093B_STATUS,
            "observed": dd093b.get("status", ""),
            "pass": int(dd093b.get("status") == EXPECTED_DD093B_STATUS),
        },
        {
            "gate": "dd093b_failures_zero",
            "expected": 0,
            "observed": dd093b.get("failures", ""),
            "pass": int(dd093b.get("failures") == 0),
        },
        {
            "gate": "runtime_proof_exists",
            "expected": 1,
            "observed": int(runtime_path.exists()),
            "pass": int(runtime_path.exists()),
        },
        {
            "gate": "runtime_needles_all_seen",
            "expected": len(runtime_rows),
            "observed": sum(int(r["seen"]) for r in runtime_rows),
            "pass": int(sum(int(r["seen"]) for r in runtime_rows) == len(runtime_rows)),
        },
        {
            "gate": "workspace_schema_exists",
            "expected": 1,
            "observed": int(schema_path.exists()),
            "pass": int(schema_path.exists()),
        },
        {
            "gate": "workspace_areas_11_seen",
            "expected": 11,
            "observed": sum(1 for r in workspace_rows if r["kind"] == "area" and int(r["seen"]) == 1),
            "pass": int(sum(1 for r in workspace_rows if r["kind"] == "area" and int(r["seen"]) == 1) == 11),
        },
        {
            "gate": "workspace_relations_7_seen",
            "expected": 7,
            "observed": sum(1 for r in workspace_rows if r["kind"] == "relation" and int(r["seen"]) == 1),
            "pass": int(sum(1 for r in workspace_rows if r["kind"] == "relation" and int(r["seen"]) == 1) == 7),
        },
        {
            "gate": "closure_report_only",
            "expected": 1,
            "observed": 1,
            "pass": 1,
        },
    ]

    boundary_rows = [
        {"boundary": "runtime_closure_report_only", "observed": 1, "required": 1, "pass": 1},
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

    next_rows = [
        {"next_id": "DD092B", "title": "CMDHELPCHK expectation mapping", "allowed_scope": "report-only mapping from DDICT surfaces to validation expectations"},
        {"next_id": "DD094", "title": "Data Dictionary workspace schema savepoint", "allowed_scope": "capture ddbase.dtschema and workspace-load proof"},
        {"next_id": "DD095", "title": "Data Dictionary catalog artifact placement policy", "allowed_scope": "document DATADICT/INDEXES/DATADICT/LMDB/DATADICT layout"},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_FULL_PATH_REMAP_RUNTIME_CLOSURE_GREEN" if failures == 0 else "DDICT_FULL_PATH_REMAP_RUNTIME_CLOSURE_REVIEW"

    write_csv(out / "dd093c_runtime_proof_ledger.csv", runtime_rows, ["proof_key", "needle", "seen"])
    write_csv(out / "dd093c_workspace_schema_ledger.csv", workspace_rows, ["kind", "name", "seen"])
    write_csv(out / "dd093c_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd093c_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd093c_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd093c_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-093C DDICT Full Path-Remap Runtime Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-093C closes the Data Dictionary runtime path remap after DD093R and DD093B.

The intended layout is now:

```text
DBF     dottalkpp/data/datadict
INDEXES dottalkpp/data/indexes/datadict
LMDB    dottalkpp/data/lmdb/datadict
```

## Inputs

- DD093B manifest: `{dd093b_manifest_path}`
- DD093B status: `{dd093b.get('status', '')}`
- Runtime proof: `{runtime_path}`
- Workspace schema: `{schema_path}`

## Runtime proof summary

- Runtime needles seen: **{sum(int(r['seen']) for r in runtime_rows)} / {len(runtime_rows)}**
- Workspace areas seen in schema: **{sum(1 for r in workspace_rows if r['kind'] == 'area' and int(r['seen']) == 1)} / 11**
- Workspace relations seen in schema: **{sum(1 for r in workspace_rows if r['kind'] == 'relation' and int(r['seen']) == 1)} / 7**

## Closed behavior

DDICT now resolves:

- active catalog under `data/datadict`
- CDX artifacts under `data/indexes/datadict`
- LMDB mirrors under `data/lmdb/datadict`

The `ddbase.dtschema` workspace schema preserves the 11 Data Dictionary areas and the 7 core relations.

## Boundary

DD-093C is runtime-closure/report-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""

    write_text(out / "DD093C_DDICT_FULL_PATH_REMAP_RUNTIME_CLOSURE_REPORT.md", report)

    closure_written = 0
    closure_path = repo / args.closure_path
    if args.write_closure:
        write_text(closure_path, report)
        closure_written = 1

    manifest = {
        "contract": "dd093c_ddict_full_path_remap_runtime_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd093b_status": dd093b.get("status", ""),
        "runtime_needles_seen": sum(int(r["seen"]) for r in runtime_rows),
        "runtime_needles_total": len(runtime_rows),
        "workspace_areas_seen": sum(1 for r in workspace_rows if r["kind"] == "area" and int(r["seen"]) == 1),
        "workspace_relations_seen": sum(1 for r in workspace_rows if r["kind"] == "relation" and int(r["seen"]) == 1),
        "failures": failures,
        "closure_written": closure_written,
        "closure_path": str(closure_path) if closure_written else "",
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Resume DD092B CMDHELPCHK expectation mapping, or capture DD094 workspace schema savepoint.",
    }
    write_json(out / "dd093c_ddict_full_path_remap_runtime_closure_manifest.json", manifest)

    print(f"DD-093C DDICT full path-remap runtime closure manifest: {out / 'dd093c_ddict_full_path_remap_runtime_closure_manifest.json'}")
    print(f"status: {status}; runtime_needles: {manifest['runtime_needles_seen']}/{manifest['runtime_needles_total']}; workspace_areas: {manifest['workspace_areas_seen']}/11; workspace_relations: {manifest['workspace_relations_seen']}/7; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
