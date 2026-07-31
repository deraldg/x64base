#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD071_STATUS = "DDICT_STATUS_TABLES_RUNTIME_CLOSURE_GREEN"
TARGET_TABLES = ["DDOBJECT", "DDATTR", "DDEDGE"]
ALL_TABLES = [
    "DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE",
    "DDEVID", "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def is_name_bytes(bs: bytes) -> bool:
    if not bs:
        return False
    s = bs.split(b"\x00", 1)[0]
    if not s:
        return False
    try:
        txt = s.decode("ascii")
    except Exception:
        return False
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]{0,30}$", txt.strip()))


def plausible_desc(data: bytes, off: int) -> bool:
    if off + 32 > len(data):
        return False
    if data[off] in (0x0D, 0x1A, 0x00):
        return False
    if not is_name_bytes(data[off:off+11]):
        return False
    ftype = chr(data[off+11]) if 32 <= data[off+11] <= 126 else ""
    return ftype in set("CDNLFIMBYT@GOVQ")


def parse_descriptor(data: bytes, off: int) -> Dict[str, Any]:
    name = data[off:off+11].split(b"\x00", 1)[0].decode("ascii", errors="replace").strip()
    ftype = chr(data[off+11])
    # Classic DBF stores length at 16, decimal at 17. Some x64 widened variants may also keep these useful.
    width = data[off+16] if off + 17 <= len(data) else 0
    decimals = data[off+17] if off + 18 <= len(data) else 0
    # Capture little-endian offset/width guesses for diagnostics.
    offset32 = int.from_bytes(data[off+12:off+16], "little", signed=False) if off + 16 <= len(data) else 0
    width16 = int.from_bytes(data[off+16:off+18], "little", signed=False) if off + 18 <= len(data) else 0
    return {
        "name": name,
        "type": ftype,
        "width": width,
        "decimals": decimals,
        "offset32": offset32,
        "width16": width16,
        "descriptor_offset": off,
    }


def find_descriptor_start(data: bytes) -> int:
    # Prefer known x64 prefix, then classic DBF.
    for start in (96, 32):
        if plausible_desc(data, start):
            return start
    # Scan first 512 bytes for a run of at least two plausible descriptors spaced by 32.
    max_scan = min(len(data) - 64, 512)
    for start in range(0, max_scan):
        if plausible_desc(data, start) and plausible_desc(data, start + 32):
            return start
    # Fall back to first plausible descriptor.
    for start in range(0, max_scan):
        if plausible_desc(data, start):
            return start
    return -1


def parse_dbf_schema(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": 0, "path": str(path), "fields": [], "records": 0, "header_len": 0, "record_len": 0, "descriptor_start": -1, "file_bytes": 0}
    data = path.read_bytes()
    records = int.from_bytes(data[4:8], "little", signed=False) if len(data) >= 8 else 0
    header_len = int.from_bytes(data[8:10], "little", signed=False) if len(data) >= 10 else 0
    record_len = int.from_bytes(data[10:12], "little", signed=False) if len(data) >= 12 else 0
    start = find_descriptor_start(data)
    fields: List[Dict[str, Any]] = []
    if start >= 0:
        off = start
        while off + 32 <= len(data):
            if data[off] == 0x0D:
                break
            if not plausible_desc(data, off):
                break
            fields.append(parse_descriptor(data, off))
            off += 32
            if len(fields) > 512:
                break
    return {
        "exists": 1,
        "path": str(path),
        "fields": fields,
        "records": records,
        "header_len": header_len,
        "record_len": record_len,
        "descriptor_start": start,
        "file_bytes": path.stat().st_size,
    }


def field_role(name: str) -> str:
    u = name.upper()
    if u in {"OBJID", "OBJECTID", "OBJECT_ID"}:
        return "OBJECT_ID"
    if u in {"OBJNAME", "NAME", "OBJECTNAME", "LOGNAME", "LOG_NAME"}:
        return "OBJECT_NAME"
    if u in {"OBJTYPE", "TYPE", "OBJECTTYPE", "KIND"}:
        return "OBJECT_TYPE"
    if u in {"FROMOBJ", "FROMID", "FROM_OBJ", "PARENTOBJ", "OWNEROBJ", "TABLEOBJ"}:
        return "EDGE_FROM_OBJECT"
    if u in {"TOOBJ", "TOID", "TO_OBJ", "CHILDOBJ", "FIELDOBJ"}:
        return "EDGE_TO_OBJECT"
    if u in {"EDGETYPE", "RELTYPE", "KIND"}:
        return "EDGE_TYPE"
    if u in {"ATTRNAME", "ATTR", "NAME", "KEY"}:
        return "ATTRIBUTE_NAME"
    if u in {"ATTRVAL", "VALUE", "VAL", "TEXT", "MEMO"}:
        return "ATTRIBUTE_VALUE"
    if u in {"TAG", "TAGNAME", "INDEXTAG", "ORDER"}:
        return "TAG_NAME"
    if u in {"FIELD", "FIELDNAME", "FLDNAME", "COLNAME", "COLUMN"}:
        return "FIELD_NAME"
    return ""


def schema_rows(repo: Path, active_dir: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    schemas: Dict[str, Dict[str, Any]] = {}
    for table in TARGET_TABLES:
        path = active_dir / f"{table}.dbf"
        parsed = parse_dbf_schema(path)
        schemas[table] = parsed
        for ordinal, f in enumerate(parsed.get("fields", []), start=1):
            rows.append({
                "table": table,
                "dbf": rel(repo, path),
                "table_exists": parsed["exists"],
                "records": parsed["records"],
                "descriptor_start": parsed["descriptor_start"],
                "ordinal": ordinal,
                "field": f["name"],
                "type": f["type"],
                "width": f["width"],
                "decimals": f["decimals"],
                "role_guess": field_role(f["name"]),
            })
    return rows, schemas


def candidate_query_rows(schemas: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    def fields_for(table: str) -> List[str]:
        return [f["name"].upper() for f in schemas.get(table, {}).get("fields", [])]

    obj_fields = fields_for("DDOBJECT")
    attr_fields = fields_for("DDATTR")
    edge_fields = fields_for("DDEDGE")

    has_objid = "OBJID" in obj_fields
    has_objtype = any(x in obj_fields for x in ["OBJTYPE", "TYPE", "KIND"])
    has_objname = any(x in obj_fields for x in ["OBJNAME", "NAME", "LOGNAME", "LOG_NAME"])
    has_edge_from = any(x in edge_fields for x in ["FROMOBJ", "FROMID", "FROM_OBJ"])
    has_edge_to = any(x in edge_fields for x in ["TOOBJ", "TOID", "TO_OBJ"])
    has_edge_type = any(x in edge_fields for x in ["EDGETYPE", "RELTYPE", "KIND"])
    has_attr_obj = any(x in attr_fields for x in ["OBJID", "OBJECTID", "OBJECT_ID"])
    has_attr_name = any(x in attr_fields for x in ["ATTRNAME", "ATTR", "NAME", "KEY"])

    return [
        {
            "query_id": "Q_FIELDS_RESOLVE_TABLE_OBJECT",
            "surface": "DDICT FIELDS <table>",
            "tables": "DDOBJECT",
            "needed_columns_present": int(has_objid and has_objname),
            "logic": "Resolve requested table token to a DDOBJECT row, preferably by object name/logical name and object type TABLE.",
            "status": "READY_OR_REVIEW_BY_COLUMN_LEDGER",
        },
        {
            "query_id": "Q_FIELDS_EDGE_TRAVERSE",
            "surface": "DDICT FIELDS <table>",
            "tables": "DDEDGE,DDOBJECT,DDATTR",
            "needed_columns_present": int(has_edge_from and has_edge_to and has_edge_type),
            "logic": "Traverse field/member edges from table object to field objects; decorate fields with DDATTR rows.",
            "status": "READY_OR_REVIEW_BY_COLUMN_LEDGER",
        },
        {
            "query_id": "Q_TAGS_RESOLVE_TAGS",
            "surface": "DDICT TAGS <table>",
            "tables": "DDEDGE,DDOBJECT,DDATTR",
            "needed_columns_present": int(has_edge_from and has_edge_to and has_attr_name),
            "logic": "Resolve indexed/tag rows or attributes associated with the table and field objects.",
            "status": "READY_OR_REVIEW_BY_COLUMN_LEDGER",
        },
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-072 DDICT FIELDS/TAGS schema inspection and implementation plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD072-ddict-fields-tags-schema-plan-v0")
    ap.add_argument("--dd071-dir", default="docs/datadict/reports/DD071-ddict-status-tables-runtime-closure-v0")
    ap.add_argument("--active-catalog-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd071_dir = (repo / args.dd071_dir).resolve()
    dd071_manifest = read_json(dd071_dir / "dd071_ddict_status_tables_runtime_closure_manifest.json")
    active_dir = (repo / args.active_catalog_path).resolve()

    rows, schemas = schema_rows(repo, active_dir)
    query_rows = candidate_query_rows(schemas)

    table_summary = []
    for table in TARGET_TABLES:
        parsed = schemas[table]
        fields = parsed.get("fields", [])
        table_summary.append({
            "table": table,
            "dbf_exists": parsed["exists"],
            "records": parsed["records"],
            "field_count": len(fields),
            "descriptor_start": parsed["descriptor_start"],
            "file_bytes": parsed["file_bytes"],
            "fields": ",".join(f["name"] for f in fields),
        })

    dd071_green = int(dd071_manifest.get("status") == EXPECTED_DD071_STATUS)
    active_dir_exists = int(active_dir.exists())
    target_tables_present = sum(1 for t in TARGET_TABLES if schemas[t]["exists"] == 1)
    all_have_fields = int(all(len(schemas[t].get("fields", [])) > 0 for t in TARGET_TABLES))

    gate_rows = [
        {"gate": "dd071_status_tables_closure_green", "expected": EXPECTED_DD071_STATUS, "observed": dd071_manifest.get("status", ""), "pass": dd071_green},
        {"gate": "active_catalog_dir_exists", "expected": 1, "observed": active_dir_exists, "pass": active_dir_exists},
        {"gate": "target_tables_present", "expected": len(TARGET_TABLES), "observed": target_tables_present, "pass": int(target_tables_present == len(TARGET_TABLES))},
        {"gate": "target_table_schemas_parsed", "expected": 1, "observed": all_have_fields, "pass": all_have_fields},
        {"gate": "plan_only", "expected": 1, "observed": 1, "pass": 1},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    ready_queries = sum(1 for r in query_rows if int(r["needed_columns_present"]) == 1)
    status = "DDICT_FIELDS_TAGS_SCHEMA_PLAN_READY" if failures == 0 else "DDICT_FIELDS_TAGS_SCHEMA_PLAN_REVIEW"

    boundary_rows = [
        {"boundary": "schema_inspection_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]

    impl_rows = [
        {
            "slice_id": "DD073A_FIELDS_ONLY",
            "surface": "DDICT FIELDS <table>",
            "allowed_future_edits": "cmd_ddict.cpp or read-only helper only, after explicit authorization",
            "requires": "DD072 schema plan ready and column ledger accepted",
            "success_smoke": "DDICT FIELDS DDOBJECT lists fields or reports a precise schema-query review reason",
        },
        {
            "slice_id": "DD073B_TAGS_ONLY",
            "surface": "DDICT TAGS <table>",
            "allowed_future_edits": "read-only helper only, after FIELDS traversal is proven",
            "requires": "FIELDS traversal green and tag/index metadata mapping accepted",
            "success_smoke": "DDICT TAGS DDATTR lists known tags/index metadata or precise review reason",
        },
    ]

    write_csv(out / "dd072_target_table_summary.csv", table_summary, ["table", "dbf_exists", "records", "field_count", "descriptor_start", "file_bytes", "fields"])
    write_csv(out / "dd072_target_schema_fields.csv", rows, ["table", "dbf", "table_exists", "records", "descriptor_start", "ordinal", "field", "type", "width", "decimals", "role_guess"])
    write_csv(out / "dd072_query_pattern_plan.csv", query_rows, ["query_id", "surface", "tables", "needed_columns_present", "logic", "status"])
    write_csv(out / "dd072_implementation_slice_plan.csv", impl_rows, ["slice_id", "surface", "allowed_future_edits", "requires", "success_smoke"])
    write_csv(out / "dd072_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd072_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-072 DDICT FIELDS/TAGS Schema Inspection and Implementation Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-072 inspects the actual active catalog schema needed for future read-only
`DDICT FIELDS <table>` and `DDICT TAGS <table>` surfaces.

## Inputs

- DD-071 status: `{dd071_manifest.get('status', '')}`
- Active catalog: `{rel(repo, active_dir)}`

## Target table schema summary

- Target tables: `{', '.join(TARGET_TABLES)}`
- Target tables present: **{target_tables_present} / {len(TARGET_TABLES)}**
- Target table schemas parsed: **{all_have_fields}**
- Query patterns with all needed columns detected: **{ready_queries} / {len(query_rows)}**

## Recommended next step

Do not patch `DDICT FIELDS` or `DDICT TAGS` until the schema field ledger is reviewed.

Next package after review:

```text
DD-073
  Guarded DDICT FIELDS implementation
```

Then:

```text
DD-074
  Guarded DDICT TAGS implementation
```

## Boundary

DD-072 is schema-inspection and planning only. It does not edit C++ source,
registry/build files, active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK, or
manual/catalog rows.
"""
    (out / "DD072_DDICT_FIELDS_TAGS_SCHEMA_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd072_ddict_fields_tags_schema_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd071_status": dd071_manifest.get("status", ""),
        "active_catalog_path": rel(repo, active_dir),
        "target_tables_present": target_tables_present,
        "target_schemas_parsed": all_have_fields,
        "query_patterns_ready": ready_queries,
        "failures": failures,
        "cxx_source_edits": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "Review dd072_target_schema_fields.csv, then authorize DD-073 guarded DDICT FIELDS implementation.",
    }
    write_json(out / "dd072_ddict_fields_tags_schema_plan_manifest.json", manifest)

    print(f"DD-072 DDICT FIELDS/TAGS schema plan manifest: {out / 'dd072_ddict_fields_tags_schema_plan_manifest.json'}")
    print(f"status: {status}; target_tables_present: {target_tables_present}; query_patterns_ready: {ready_queries}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
