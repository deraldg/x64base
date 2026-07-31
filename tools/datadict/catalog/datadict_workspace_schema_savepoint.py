#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD092C_STATUS = "DDICT_CMDHELPCHK_CANDIDATE_RULES_GENERATED_REVIEW_READY"
EXPECTED_DD093C_STATUS = "DDICT_FULL_PATH_REMAP_RUNTIME_CLOSURE_GREEN"

EXPECTED_AREAS = [
    {"area": 0, "alias": "DDARTIF", "dbf": "DDARTIF.dbf", "index": "ddartif.cdx", "tag": "ARTID"},
    {"area": 1, "alias": "DDATTR", "dbf": "DDATTR.dbf", "index": "ddattr.cdx", "tag": "ATTRNAME"},
    {"area": 2, "alias": "DDBASE", "dbf": "DDBASE.dbf", "index": "ddbase.cdx", "tag": "BASEID"},
    {"area": 3, "alias": "DDEDGE", "dbf": "DDEDGE.dbf", "index": "ddedge.cdx", "tag": "EDGEID"},
    {"area": 4, "alias": "DDEVID", "dbf": "DDEVID.dbf", "index": "ddevid.cdx", "tag": "EVID"},
    {"area": 5, "alias": "DDGATE", "dbf": "DDGATE.dbf", "index": "ddgate.cdx", "tag": "GATEID"},
    {"area": 6, "alias": "DDOBJECT", "dbf": "DDOBJECT.dbf", "index": "ddobject.cdx", "tag": "OBJID"},
    {"area": 7, "alias": "DDPROFILE", "dbf": "DDPROFILE.dbf", "index": "ddprofile.cdx", "tag": "PROFID"},
    {"area": 8, "alias": "DDREVIEW", "dbf": "DDREVIEW.dbf", "index": "ddreview.cdx", "tag": "REVID"},
    {"area": 9, "alias": "DDRUN", "dbf": "DDRUN.dbf", "index": "ddrun.cdx", "tag": "RUNID"},
    {"area": 10, "alias": "DDSOURCE", "dbf": "DDSOURCE.dbf", "index": "ddsource.cdx", "tag": "SRCID"},
]

EXPECTED_RELATIONS = [
    "RELATION DDOBJECT DDATTR ON OBJID",
    "RELATION DDOBJECT DDEVID ON OBJID",
    "RELATION DDSOURCE DDEVID ON SRCID",
    "RELATION DDRUN DDARTIF ON RUNID",
    "RELATION DDRUN DDBASE ON RUNID",
    "RELATION DDRUN DDGATE ON RUNID",
    "RELATION DDRUN DDREVIEW ON RUNID",
]

PROTECTED_ARTIFACTS = [
    "dottalkpp/data/workspaces/ddbase.dtschema",
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
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


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().upper())


def parse_area_line(line: str) -> Dict[str, Any]:
    # AREA 0 | dbf=DDARTIF.dbf | index=ddartif.cdx | indextype=CDX | tag=ARTID | alias=DDARTIF
    m = re.match(r"\s*AREA\s+(\d+)\s*\|\s*(.*)$", line, re.I)
    if not m:
        return {}
    result: Dict[str, Any] = {"area": int(m.group(1))}
    rest = m.group(2)
    for part in rest.split("|"):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        result[k.strip().lower()] = v.strip()
    return result


def schema_area_rows(schema_text: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    parsed = [parse_area_line(line) for line in schema_text.splitlines() if line.strip().upper().startswith("AREA ")]
    parsed_by_area = {p.get("area"): p for p in parsed if p}

    for exp in EXPECTED_AREAS:
        p = parsed_by_area.get(exp["area"], {})
        rows.append({
            "area": exp["area"],
            "expected_alias": exp["alias"],
            "observed_alias": p.get("alias", ""),
            "expected_dbf": exp["dbf"],
            "observed_dbf": p.get("dbf", ""),
            "expected_index": exp["index"],
            "observed_index": p.get("index", ""),
            "expected_tag": exp["tag"],
            "observed_tag": p.get("tag", ""),
            "observed_indextype": p.get("indextype", ""),
            "alias_pass": int(p.get("alias", "").upper() == exp["alias"]),
            "dbf_pass": int(p.get("dbf", "").upper() == exp["dbf"].upper()),
            "index_pass": int(p.get("index", "").upper() == exp["index"].upper()),
            "tag_pass": int(p.get("tag", "").upper() == exp["tag"]),
            "indextype_pass": int(p.get("indextype", "").upper() == "CDX"),
        })
    return rows


def schema_relation_rows(schema_text: str) -> List[Dict[str, Any]]:
    norm_schema_lines = {normalize(line) for line in schema_text.splitlines() if line.strip()}
    rows = []
    for rel in EXPECTED_RELATIONS:
        rows.append({
            "relation": rel,
            "seen": int(normalize(rel) in norm_schema_lines),
        })
    return rows


def artifact_presence_rows(repo: Path) -> List[Dict[str, Any]]:
    rows = []
    for exp in EXPECTED_AREAS:
        table = exp["alias"].lower()
        paths = [
            ("dbf", f"dottalkpp/data/datadict/{exp['alias']}.dbf"),
            ("cdx", f"dottalkpp/data/indexes/datadict/{table}.cdx"),
            ("lmdb", f"dottalkpp/data/lmdb/datadict/{exp['alias']}.cdx.d"),
            ("lmdb_lower", f"dottalkpp/data/lmdb/datadict/{table}.cdx.d"),
        ]
        for kind, rel_path in paths:
            p = repo / rel_path
            rows.append({
                "alias": exp["alias"],
                "kind": kind,
                "path": rel_path,
                "exists": int(p.exists()),
                "type": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
                "bytes_or_children": p.stat().st_size if p.exists() and p.is_file() else sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else 0,
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD094 Data Dictionary workspace schema savepoint")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD094-datadict-workspace-schema-savepoint-v0")
    ap.add_argument("--workspace-schema", default="dottalkpp/data/workspaces/ddbase.dtschema")
    ap.add_argument("--dd092c-dir", default="docs/datadict/reports/DD092C-cmdhelpchk-candidate-rule-generation-v0")
    ap.add_argument("--dd093c-dir", default="docs/datadict/reports/DD093C-ddict-full-path-remap-runtime-closure-v0")
    ap.add_argument("--workspace-proof", default="")
    ap.add_argument("--write-savepoint", action="store_true")
    ap.add_argument("--savepoint-path", default="docs/datadict/runlog/DD-094_DATADICT_WORKSPACE_SCHEMA_SAVEPOINT.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    schema_path = repo / args.workspace_schema
    schema_text = read_text(schema_path)

    dd092c_manifest_path = repo / args.dd092c_dir / "dd092c_cmdhelpchk_candidate_rule_generation_manifest.json"
    dd093c_manifest_path = repo / args.dd093c_dir / "dd093c_ddict_full_path_remap_runtime_closure_manifest.json"
    dd092c = read_json(dd092c_manifest_path)
    dd093c = read_json(dd093c_manifest_path)

    area_rows = schema_area_rows(schema_text)
    relation_rows = schema_relation_rows(schema_text)
    presence_rows = artifact_presence_rows(repo)

    proof_rows = []
    if args.workspace_proof:
        proof_path = repo / args.workspace_proof
        proof_text = read_text(proof_path)
        proof_lower = proof_text.lower()
        proof_needles = [
            ("workspace_11_areas_open", "WORKSPACE: 11 area(s) open."),
            ("workspace_load_11_7", "WORKSPACE LOAD: restored 11 area(s) and 7 relation(s)."),
            ("ddattr_lmdb_mode", "MODE LMDB"),
            ("ddobject_index_path", "data\\indexes\\datadict\\ddobject.cdx"),
            ("ddattr_index_path", "data\\indexes\\datadict\\ddattr.cdx"),
        ]
        for key, needle in proof_needles:
            proof_rows.append({"proof_key": key, "needle": needle, "seen": int(needle.lower() in proof_lower)})
    else:
        proof_rows.append({"proof_key": "workspace_proof_optional", "needle": "not supplied", "seen": ""})

    snapshot_dir = out / "schema_snapshot"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / "ddbase.dtschema"
    if schema_path.exists():
        shutil.copy2(schema_path, snapshot_path)

    artifact_rows = [
        artifact_row(repo, args.workspace_schema, "workspace_schema"),
        artifact_row(repo, str(Path(args.dd092c_dir) / "dd092c_cmdhelpchk_candidate_rule_generation_manifest.json"), "dd092c_manifest"),
        artifact_row(repo, str(Path(args.dd093c_dir) / "dd093c_ddict_full_path_remap_runtime_closure_manifest.json"), "dd093c_manifest"),
    ]
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))

    area_pass_count = sum(1 for r in area_rows if all(int(r[k]) == 1 for k in ["alias_pass", "dbf_pass", "index_pass", "tag_pass", "indextype_pass"]))
    relation_pass_count = sum(int(r["seen"]) for r in relation_rows)
    dbf_present = sum(1 for r in presence_rows if r["kind"] == "dbf" and int(r["exists"]) == 1)
    cdx_present = sum(1 for r in presence_rows if r["kind"] == "cdx" and int(r["exists"]) == 1)
    lmdb_present_any_case = 0
    for exp in EXPECTED_AREAS:
        aliases = [r for r in presence_rows if r["alias"] == exp["alias"] and r["kind"] in {"lmdb", "lmdb_lower"} and int(r["exists"]) == 1]
        if aliases:
            lmdb_present_any_case += 1

    boundary_rows = [
        {"boundary": "workspace_schema_savepoint_only", "observed": 1, "required": 1, "pass": 1},
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
        {"gate": "dd092c_review_ready", "expected": EXPECTED_DD092C_STATUS, "observed": dd092c.get("status", ""), "pass": int(dd092c.get("status") == EXPECTED_DD092C_STATUS)},
        {"gate": "dd093c_path_remap_green", "expected": EXPECTED_DD093C_STATUS, "observed": dd093c.get("status", ""), "pass": int(dd093c.get("status") == EXPECTED_DD093C_STATUS)},
        {"gate": "workspace_schema_exists", "expected": 1, "observed": int(schema_path.exists()), "pass": int(schema_path.exists())},
        {"gate": "workspace_schema_header", "expected": "DTSHEMA 2", "observed": schema_text.splitlines()[0] if schema_text.splitlines() else "", "pass": int(bool(schema_text.splitlines()) and schema_text.splitlines()[0].strip().upper() == "DTSHEMA 2")},
        {"gate": "area_rows_full_cdx", "expected": 11, "observed": area_pass_count, "pass": int(area_pass_count == 11)},
        {"gate": "relations_seen", "expected": 7, "observed": relation_pass_count, "pass": int(relation_pass_count == 7)},
        {"gate": "dbf_artifacts_present", "expected": 11, "observed": dbf_present, "pass": int(dbf_present == 11)},
        {"gate": "cdx_artifacts_present", "expected": 11, "observed": cdx_present, "pass": int(cdx_present == 11)},
        {"gate": "lmdb_artifacts_present", "expected": 11, "observed": lmdb_present_any_case, "pass": int(lmdb_present_any_case == 11)},
        {"gate": "snapshot_written", "expected": 1, "observed": int(snapshot_path.exists()), "pass": int(snapshot_path.exists())},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DATADICT_WORKSPACE_SCHEMA_SAVEPOINT_GREEN" if failures == 0 else "DATADICT_WORKSPACE_SCHEMA_SAVEPOINT_REVIEW"

    next_rows = [
        {"next_id": "DD095", "title": "Data Dictionary layout policy documentation", "allowed_scope": "document DBF/INDEXES/LMDB datadict layout and no metadata collision policy"},
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply planning", "allowed_scope": "only after explicit authorization and candidate review"},
        {"next_id": "DD096", "title": "Data Dictionary schema promotion / catalog policy", "allowed_scope": "report-only planning; no catalog mutation"},
    ]

    write_csv(out / "dd094_workspace_area_ledger.csv", area_rows, ["area", "expected_alias", "observed_alias", "expected_dbf", "observed_dbf", "expected_index", "observed_index", "expected_tag", "observed_tag", "observed_indextype", "alias_pass", "dbf_pass", "index_pass", "tag_pass", "indextype_pass"])
    write_csv(out / "dd094_workspace_relation_ledger.csv", relation_rows, ["relation", "seen"])
    write_csv(out / "dd094_catalog_artifact_presence.csv", presence_rows, ["alias", "kind", "path", "exists", "type", "bytes_or_children"])
    write_csv(out / "dd094_workspace_proof_ledger.csv", proof_rows, ["proof_key", "needle", "seen"])
    write_csv(out / "dd094_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd094_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd094_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd094_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD094 Data Dictionary Workspace Schema Savepoint

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD094 captures a report-only savepoint for the Data Dictionary workspace schema.

It validates and snapshots:

- `ddbase.dtschema`
- 11 Data Dictionary work areas
- CDX attachment declarations for all 11 areas
- 7 core workspace relations
- DBF/CDX/LMDB artifact presence under the remapped Data Dictionary layout

## Inputs

- Workspace schema: `{schema_path}`
- DD092C status: `{dd092c.get('status', '')}`
- DD093C status: `{dd093c.get('status', '')}`

## Summary

- Fully matched area rows: **{area_pass_count} / 11**
- Relations seen: **{relation_pass_count} / 7**
- DBF artifacts present: **{dbf_present} / 11**
- CDX artifacts present: **{cdx_present} / 11**
- LMDB artifacts present: **{lmdb_present_any_case} / 11**
- Schema snapshot: `{snapshot_path}`

## Accepted layout

```text
DBF     dottalkpp/data/datadict
INDEXES dottalkpp/data/indexes/datadict
LMDB    dottalkpp/data/lmdb/datadict
```

## Boundary

DD094 is workspace-schema-savepoint/report-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    write_text(out / "DD094_DATADICT_WORKSPACE_SCHEMA_SAVEPOINT_REPORT.md", report)

    savepoint_written = 0
    savepoint_path = repo / args.savepoint_path
    if args.write_savepoint:
        write_text(savepoint_path, report)
        savepoint_written = 1

    manifest = {
        "contract": "dd094_datadict_workspace_schema_savepoint_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "workspace_schema": str(schema_path),
        "schema_snapshot": str(snapshot_path),
        "area_pass_count": area_pass_count,
        "relation_pass_count": relation_pass_count,
        "dbf_artifacts_present": dbf_present,
        "cdx_artifacts_present": cdx_present,
        "lmdb_artifacts_present": lmdb_present_any_case,
        "failures": failures,
        "savepoint_written": savepoint_written,
        "savepoint_path": str(savepoint_path) if savepoint_written else "",
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD095 Data Dictionary layout policy documentation, or DD092D guarded HELP/CMDHELPCHK apply planning after explicit authorization.",
    }
    write_json(out / "dd094_datadict_workspace_schema_savepoint_manifest.json", manifest)

    print(f"DD094 Data Dictionary workspace schema savepoint manifest: {out / 'dd094_datadict_workspace_schema_savepoint_manifest.json'}")
    print(f"status: {status}; areas: {area_pass_count}/11; relations: {relation_pass_count}/7; dbf: {dbf_present}/11; cdx: {cdx_present}/11; lmdb: {lmdb_present_any_case}/11; failures: {failures}; savepoint_written: {savepoint_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
