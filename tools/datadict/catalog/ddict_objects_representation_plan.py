#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD083_STATUS = "DDICT_COMMAND_SURFACE_CYCLE_CLOSED_GREEN"
TARGET_TABLES = ["DDOBJECT", "DDPROFILE", "DDATTR"]
SAMPLE_LIMIT = 80


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


def trim(s: str) -> str:
    return (s or "").replace("\x00", "").strip()


def up(s: str) -> str:
    return trim(s).upper()


def le16(data: bytes, off: int) -> int:
    if off + 2 > len(data):
        return 0
    return data[off] | (data[off + 1] << 8)


def le32(data: bytes, off: int) -> int:
    if off + 4 > len(data):
        return 0
    return data[off] | (data[off + 1] << 8) | (data[off + 2] << 16) | (data[off + 3] << 24)


def plausible_name(data: bytes, off: int) -> bool:
    if off + 11 > len(data):
        return False
    first = data[off]
    if not (chr(first).isalpha() or first == ord("_")):
        return False
    for i in range(off, min(off + 11, len(data))):
        b = data[i]
        if b == 0:
            return True
        ch = chr(b)
        if not (ch.isalnum() or ch == "_"):
            return False
    return True


def plausible_desc(data: bytes, off: int) -> bool:
    if off + 32 > len(data):
        return False
    if data[off] in (0x0D, 0x1A, 0x00):
        return False
    if not plausible_name(data, off):
        return False
    return chr(data[off + 11]) in set("CDNLFIMBYT@GOVQ")


def descriptor_start(data: bytes) -> int:
    for start in (96, 32):
        if plausible_desc(data, start):
            return start
    limit = min(len(data) - 64, 512)
    for start in range(max(0, limit)):
        if plausible_desc(data, start) and plausible_desc(data, start + 32):
            return start
    return -1


def desc_name(data: bytes, off: int) -> str:
    raw = data[off:off+11].split(b"\x00", 1)[0]
    return raw.decode("ascii", errors="replace").strip().upper()


def parse_schema(data: bytes) -> List[Dict[str, Any]]:
    start = descriptor_start(data)
    fields: List[Dict[str, Any]] = []
    if start < 0:
        return fields
    off = start
    while off + 32 <= len(data):
        if data[off] == 0x0D or not plausible_desc(data, off):
            break
        width = data[off + 16]
        width16 = le16(data, off + 16)
        if width == 0 and 0 < width16 < 4096:
            width = width16
        fields.append({"name": desc_name(data, off), "type": chr(data[off+11]), "width": width})
        off += 32
        if len(fields) > 512:
            break
    return fields


def read_dbf(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]], Dict[str, Any]]:
    if not path.exists():
        return [], [], {"exists": 0, "records": 0, "header_len": 0, "record_len": 0, "descriptor_start": -1, "file_bytes": 0}
    data = path.read_bytes()
    records = le32(data, 4) if len(data) >= 8 else 0
    header_len = le16(data, 8) if len(data) >= 10 else 0
    record_len = le16(data, 10) if len(data) >= 12 else 0
    fields = parse_schema(data)
    rows: List[Dict[str, str]] = []
    if header_len and record_len and fields:
        for rec in range(records):
            base = header_len + rec * record_len
            if base + record_len > len(data):
                break
            if data[base] == ord("*"):
                continue
            pos = base + 1
            row: Dict[str, str] = {}
            for f in fields:
                width = int(f.get("width", 0))
                if width <= 0 or pos + width > len(data):
                    break
                raw = data[pos:pos+width].decode("utf-8", errors="replace")
                row[f["name"]] = trim(raw)
                pos += width
            rows.append(row)
    return fields, rows, {
        "exists": 1,
        "records": records,
        "header_len": header_len,
        "record_len": record_len,
        "descriptor_start": descriptor_start(data),
        "file_bytes": path.stat().st_size,
    }


def load_tables(repo: Path, active_dir: Path) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, str]]], Dict[str, Any]]:
    schema_rows: List[Dict[str, Any]] = []
    rows_by_table: Dict[str, List[Dict[str, str]]] = {}
    meta: Dict[str, Any] = {}
    for table in TARGET_TABLES:
        path = active_dir / f"{table}.dbf"
        fields, rows, info = read_dbf(path)
        rows_by_table[table] = rows
        meta[table] = info
        for i, f in enumerate(fields, start=1):
            schema_rows.append({
                "table": table,
                "ordinal": i,
                "field": f["name"],
                "type": f["type"],
                "width": f["width"],
                "dbf": rel(repo, path),
            })
    return schema_rows, rows_by_table, meta


def count_rows(rows: List[Dict[str, str]], key: str) -> List[Dict[str, Any]]:
    c = Counter(up(r.get(key, "")) or "(blank)" for r in rows)
    return [{"value": k, "count": v} for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))]


def sample_object_rows(rows_by_table: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, Any]]:
    objects = rows_by_table.get("DDOBJECT", [])
    attrs = rows_by_table.get("DDATTR", [])
    attr_counts = Counter(trim(a.get("OBJID", "")) for a in attrs if trim(a.get("OBJID", "")))

    priority_types = ["CATALOG_TABLE", "CATALOG_FIELD", "CATALOG_TAG", "CATALOG_COMMAND", "CATALOG_SOURCE", "CATALOG_ARTIFACT"]
    selected: List[Dict[str, str]] = []
    seen_ids = set()

    for typ in priority_types:
        for row in objects:
            if up(row.get("OBJTYPE", "")) == typ and trim(row.get("OBJID", "")) not in seen_ids:
                selected.append(row)
                seen_ids.add(trim(row.get("OBJID", "")))
                if len([r for r in selected if up(r.get("OBJTYPE", "")) == typ]) >= 8:
                    break

    for row in objects:
        if len(selected) >= SAMPLE_LIMIT:
            break
        objid = trim(row.get("OBJID", ""))
        if objid not in seen_ids:
            selected.append(row)
            seen_ids.add(objid)

    sample = []
    for row in selected[:SAMPLE_LIMIT]:
        objid = trim(row.get("OBJID", ""))
        sample.append({
            "objid": objid,
            "objtype": row.get("OBJTYPE", ""),
            "name": row.get("NAME", ""),
            "owner": row.get("OWNER", ""),
            "status": row.get("STATUS", ""),
            "profile": row.get("PROFILE", ""),
            "srcid": row.get("SRCID", ""),
            "attr_count": attr_counts.get(objid, 0),
        })
    return sample


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-084 DDICT OBJECTS representation and implementation plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD084-ddict-objects-representation-plan-v0")
    ap.add_argument("--dd083-dir", default="docs/datadict/reports/DD083-ddict-command-surface-cycle-closure-v0")
    ap.add_argument("--active-catalog-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd083_dir = (repo / args.dd083_dir).resolve()
    dd083_manifest = read_json(dd083_dir / "dd083_ddict_command_surface_cycle_closure_manifest.json")
    active_dir = (repo / args.active_catalog_path).resolve()

    schema, rows_by_table, meta = load_tables(repo, active_dir)
    objects = rows_by_table.get("DDOBJECT", [])
    profiles = rows_by_table.get("DDPROFILE", [])
    attrs = rows_by_table.get("DDATTR", [])

    type_counts = count_rows(objects, "OBJTYPE")
    status_counts = count_rows(objects, "STATUS")
    profile_counts = count_rows(objects, "PROFILE")
    owner_counts = count_rows(objects, "OWNER")
    samples = sample_object_rows(rows_by_table)

    dd083_green = int(dd083_manifest.get("status") == EXPECTED_DD083_STATUS)
    active_exists = int(active_dir.exists())
    target_tables_present = sum(1 for t in TARGET_TABLES if meta.get(t, {}).get("exists") == 1)
    object_rows = len(objects)
    profile_rows = len(profiles)
    attr_rows = len(attrs)

    query_rows = [
        {
            "query_id": "Q_OBJECTS_LIST_ALL",
            "surface": "DDICT OBJECTS",
            "ready": int(object_rows > 0),
            "logic": "List bounded DDOBJECT rows with OBJTYPE, NAME, OWNER, STATUS, PROFILE, and attr count.",
            "risk": "LOW",
        },
        {
            "query_id": "Q_OBJECTS_TYPE_FILTER",
            "surface": "DDICT OBJECTS TYPE <type>",
            "ready": int(len(type_counts) > 0),
            "logic": "Filter by OBJTYPE case-insensitively, preserving bounded display.",
            "risk": "LOW",
        },
        {
            "query_id": "Q_OBJECTS_PROFILE_FILTER",
            "surface": "DDICT OBJECTS PROFILE <profile>",
            "ready": int(profile_rows >= 0),
            "logic": "Filter by DDOBJECT.PROFILE; optionally decorate/validate against DDPROFILE in later slice.",
            "risk": "LOW",
        },
        {
            "query_id": "Q_OBJECTS_COMBINED_FILTER",
            "surface": "DDICT OBJECTS TYPE <type> PROFILE <profile>",
            "ready": int(object_rows > 0),
            "logic": "Allow simple combined filters without introducing query language complexity.",
            "risk": "LOW_MEDIUM",
        },
    ]

    impl_rows = [
        {
            "slice_id": "DD085A_OBJECTS_LIST_AND_TYPE",
            "surface": "DDICT OBJECTS [TYPE <type>]",
            "allowed_future_edits": "cmd_ddict.cpp/read-only helper only, after explicit authorization",
            "logic": "Add bounded object list and TYPE filter.",
            "success_smoke": "DDICT OBJECTS and DDICT OBJECTS TYPE CATALOG_TABLE list object rows without mutation.",
        },
        {
            "slice_id": "DD085B_OBJECTS_PROFILE_FILTER",
            "surface": "DDICT OBJECTS [PROFILE <profile>]",
            "allowed_future_edits": "same read-only helper only",
            "logic": "Add PROFILE filter after basic list is green.",
            "success_smoke": "DDICT OBJECTS PROFILE ENGINE lists ENGINE-profile rows.",
        },
    ]

    gate_rows = [
        {"gate": "dd083_cycle_closure_green", "expected": EXPECTED_DD083_STATUS, "observed": dd083_manifest.get("status", ""), "pass": dd083_green},
        {"gate": "active_catalog_dir_exists", "expected": 1, "observed": active_exists, "pass": active_exists},
        {"gate": "target_tables_present", "expected": len(TARGET_TABLES), "observed": target_tables_present, "pass": int(target_tables_present == len(TARGET_TABLES))},
        {"gate": "ddobject_rows_present", "expected": ">0", "observed": object_rows, "pass": int(object_rows > 0)},
        {"gate": "object_types_present", "expected": ">0", "observed": len(type_counts), "pass": int(len(type_counts) > 0)},
        {"gate": "object_samples_created", "expected": ">0", "observed": len(samples), "pass": int(len(samples) > 0)},
        {"gate": "representation_plan_only", "expected": 1, "observed": 1, "pass": 1},
    ]
    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_OBJECTS_REPRESENTATION_PLAN_READY" if failures == 0 else "DDICT_OBJECTS_REPRESENTATION_PLAN_REVIEW"

    boundary_rows = [
        {"boundary": "objects_representation_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd084_target_schema_fields.csv", schema, ["table", "ordinal", "field", "type", "width", "dbf"])
    write_csv(out / "dd084_object_type_counts.csv", type_counts, ["value", "count"])
    write_csv(out / "dd084_object_status_counts.csv", status_counts, ["value", "count"])
    write_csv(out / "dd084_object_profile_counts.csv", profile_counts, ["value", "count"])
    write_csv(out / "dd084_object_owner_counts.csv", owner_counts, ["value", "count"])
    write_csv(out / "dd084_sample_object_rows.csv", samples, ["objid", "objtype", "name", "owner", "status", "profile", "srcid", "attr_count"])
    write_csv(out / "dd084_query_pattern_plan.csv", query_rows, ["query_id", "surface", "ready", "logic", "risk"])
    write_csv(out / "dd084_implementation_slice_plan.csv", impl_rows, ["slice_id", "surface", "allowed_future_edits", "logic", "success_smoke"])
    write_csv(out / "dd084_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd084_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-084 DDICT OBJECTS Representation and Implementation Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-084 plans the last accepted `DDICT` command surface not included in the first green read cycle:

```text
DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]
```

## Inputs

- DD-083 status: `{dd083_manifest.get('status', '')}`
- Active catalog: `{rel(repo, active_dir)}`

## Findings

- DDOBJECT rows: **{object_rows}**
- DDPROFILE rows: **{profile_rows}**
- DDATTR rows: **{attr_rows}**
- Object type count: **{len(type_counts)}**
- Target tables present: **{target_tables_present} / {len(TARGET_TABLES)}**

## Recommended implementation model

Start with bounded read-only object browsing:

```text
DDICT OBJECTS
  list bounded DDOBJECT rows
  show OBJTYPE, NAME, OWNER, STATUS, PROFILE, ATTRS

DDICT OBJECTS TYPE <type>
  filter by OBJTYPE

DDICT OBJECTS PROFILE <profile>
  filter by PROFILE
```

Keep it simple. Do not introduce general query language, mutation, repair, or catalog regeneration.

## Boundary

DD-084 is representation discovery and planning only. It does not edit C++ source,
registry/build files, active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK, generated catalog content, or manual rows.
"""
    (out / "DD084_DDICT_OBJECTS_REPRESENTATION_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd084_ddict_objects_representation_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd083_status": dd083_manifest.get("status", ""),
        "active_catalog_path": rel(repo, active_dir),
        "ddobject_rows": object_rows,
        "ddprofile_rows": profile_rows,
        "ddattr_rows": attr_rows,
        "object_type_count": len(type_counts),
        "failures": failures,
        "cxx_source_edits": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Review DD-084 object ledgers, then authorize DD-085 guarded DDICT OBJECTS implementation.",
    }
    write_json(out / "dd084_ddict_objects_representation_plan_manifest.json", manifest)

    print(f"DD-084 DDICT OBJECTS representation plan manifest: {out / 'dd084_ddict_objects_representation_plan_manifest.json'}")
    print(f"status: {status}; objects: {object_rows}; types: {len(type_counts)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
