#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD076_STATUS = "DDICT_TAGS_RUNTIME_CLOSURE_GREEN"
TARGET_TABLES = ["DDOBJECT", "DDEDGE", "DDATTR"]
SAMPLE_OBJECTS = ["DDOBJECT", "DDATTR", "DDEDGE", "DDRUN", "DDBASE"]


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


def schema_rows(repo: Path, active_dir: Path) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, str]]], Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    table_rows: Dict[str, List[Dict[str, str]]] = {}
    meta: Dict[str, Any] = {}
    for table in TARGET_TABLES:
        path = active_dir / f"{table}.dbf"
        fields, records, info = read_dbf(path)
        table_rows[table] = records
        meta[table] = info
        for i, f in enumerate(fields, start=1):
            rows.append({
                "table": table,
                "ordinal": i,
                "field": f["name"],
                "type": f["type"],
                "width": f["width"],
                "dbf": rel(repo, path),
            })
    return rows, table_rows, meta


def build_object_maps(objects: List[Dict[str, str]]) -> Tuple[Dict[str, Dict[str, str]], Dict[str, List[Dict[str, str]]]]:
    by_id: Dict[str, Dict[str, str]] = {}
    by_name_owner: Dict[str, List[Dict[str, str]]] = {}
    for row in objects:
        objid = trim(row.get("OBJID", ""))
        name = up(row.get("NAME", ""))
        owner = up(row.get("OWNER", ""))
        if objid:
            by_id[objid] = row
        for key in {name, owner, f"{owner}.{name}", f"{name}.{owner}"}:
            key = key.strip(".")
            if key:
                by_name_owner.setdefault(key, []).append(row)
    return by_id, by_name_owner


def relation_rows(table_rows: Dict[str, List[Dict[str, str]]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    objects = table_rows.get("DDOBJECT", [])
    edges = table_rows.get("DDEDGE", [])
    attrs = table_rows.get("DDATTR", [])
    by_id, by_name = build_object_maps(objects)

    edge_type_counts: Dict[str, int] = {}
    for edge in edges:
        edge_type = up(edge.get("EDGETYPE", ""))
        edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1

    edge_type_rows = [{"edgetype": k, "count": v} for k, v in sorted(edge_type_counts.items())]

    object_summary_rows: List[Dict[str, Any]] = []
    for token in SAMPLE_OBJECTS:
        matches = by_name.get(token, [])
        # Prefer CATALOG_TABLE if present.
        chosen = None
        for m in matches:
            if up(m.get("OBJTYPE", "")) == "CATALOG_TABLE" and up(m.get("NAME", "")) == token:
                chosen = m
                break
        if chosen is None and matches:
            chosen = matches[0]
        if chosen is None:
            object_summary_rows.append({
                "token": token,
                "resolved": 0,
                "objid": "",
                "objtype": "",
                "name": "",
                "owner": "",
                "incoming_edges": 0,
                "outgoing_edges": 0,
                "field_edges": 0,
                "tag_edges": 0,
            })
            continue
        objid = trim(chosen.get("OBJID", ""))
        incoming = [e for e in edges if trim(e.get("TOOBJ", "")) == objid]
        outgoing = [e for e in edges if trim(e.get("FROMOBJ", "")) == objid]
        field_edges = [e for e in outgoing if "FIELD" in up(e.get("EDGETYPE", ""))]
        tag_edges = [e for e in outgoing if "TAG" in up(e.get("EDGETYPE", ""))]
        object_summary_rows.append({
            "token": token,
            "resolved": 1,
            "objid": objid,
            "objtype": chosen.get("OBJTYPE", ""),
            "name": chosen.get("NAME", ""),
            "owner": chosen.get("OWNER", ""),
            "incoming_edges": len(incoming),
            "outgoing_edges": len(outgoing),
            "field_edges": len(field_edges),
            "tag_edges": len(tag_edges),
        })

    sample_edge_rows: List[Dict[str, Any]] = []
    for edge in edges[:250]:
        from_id = trim(edge.get("FROMOBJ", ""))
        to_id = trim(edge.get("TOOBJ", ""))
        fr = by_id.get(from_id, {})
        to = by_id.get(to_id, {})
        sample_edge_rows.append({
            "edgeid": edge.get("EDGEID", ""),
            "edgetype": edge.get("EDGETYPE", ""),
            "fromobj": from_id,
            "from_type": fr.get("OBJTYPE", ""),
            "from_name": fr.get("NAME", ""),
            "from_owner": fr.get("OWNER", ""),
            "toobj": to_id,
            "to_type": to.get("OBJTYPE", ""),
            "to_name": to.get("NAME", ""),
            "to_owner": to.get("OWNER", ""),
            "evid": edge.get("EVID", ""),
        })

    return edge_type_rows, object_summary_rows, sample_edge_rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-077 DDICT REL representation and implementation plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD077-ddict-rel-representation-plan-v0")
    ap.add_argument("--dd076-dir", default="docs/datadict/reports/DD076-ddict-tags-runtime-closure-v0")
    ap.add_argument("--active-catalog-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd076_dir = (repo / args.dd076_dir).resolve()
    dd076_manifest = read_json(dd076_dir / "dd076_tags_runtime_closure_manifest.json")
    active_dir = (repo / args.active_catalog_path).resolve()

    schema, rows_by_table, meta = schema_rows(repo, active_dir)
    edge_types, object_summary, sample_edges = relation_rows(rows_by_table)

    dd076_green = int(dd076_manifest.get("status") == EXPECTED_DD076_STATUS)
    active_exists = int(active_dir.exists())
    target_tables_present = sum(1 for t in TARGET_TABLES if meta.get(t, {}).get("exists") == 1)
    edge_count = len(rows_by_table.get("DDEDGE", []))
    object_count = len(rows_by_table.get("DDOBJECT", []))
    edge_type_count = len(edge_types)
    sample_resolved = sum(1 for r in object_summary if int(r["resolved"]) == 1)

    query_rows = [
        {
            "query_id": "Q_REL_RESOLVE_OBJECT",
            "surface": "DDICT REL <object-id-or-name>",
            "ready": int(object_count > 0),
            "logic": "Resolve token as OBJID or DDOBJECT NAME/OWNER token, preferring CATALOG_TABLE for table names.",
            "risk": "LOW",
        },
        {
            "query_id": "Q_REL_OUTGOING",
            "surface": "DDICT REL <object> OUT",
            "ready": int(edge_count > 0),
            "logic": "Find DDEDGE rows where FROMOBJ equals resolved OBJID; decorate TOOBJ through DDOBJECT.",
            "risk": "LOW",
        },
        {
            "query_id": "Q_REL_INCOMING",
            "surface": "DDICT REL <object> IN",
            "ready": int(edge_count > 0),
            "logic": "Find DDEDGE rows where TOOBJ equals resolved OBJID; decorate FROMOBJ through DDOBJECT.",
            "risk": "LOW",
        },
        {
            "query_id": "Q_REL_BOTH",
            "surface": "DDICT REL <object> BOTH",
            "ready": int(edge_count > 0),
            "logic": "Display incoming and outgoing relationship groups with bounded row counts.",
            "risk": "LOW_MEDIUM",
        },
    ]

    gate_rows = [
        {"gate": "dd076_tags_closure_green", "expected": EXPECTED_DD076_STATUS, "observed": dd076_manifest.get("status", ""), "pass": dd076_green},
        {"gate": "active_catalog_dir_exists", "expected": 1, "observed": active_exists, "pass": active_exists},
        {"gate": "target_tables_present", "expected": len(TARGET_TABLES), "observed": target_tables_present, "pass": int(target_tables_present == len(TARGET_TABLES))},
        {"gate": "ddobject_rows_present", "expected": ">0", "observed": object_count, "pass": int(object_count > 0)},
        {"gate": "ddedge_rows_present", "expected": ">0", "observed": edge_count, "pass": int(edge_count > 0)},
        {"gate": "edge_types_present", "expected": ">0", "observed": edge_type_count, "pass": int(edge_type_count > 0)},
        {"gate": "sample_objects_resolved", "expected": len(SAMPLE_OBJECTS), "observed": sample_resolved, "pass": int(sample_resolved == len(SAMPLE_OBJECTS))},
        {"gate": "representation_plan_only", "expected": 1, "observed": 1, "pass": 1},
    ]
    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_REL_REPRESENTATION_PLAN_READY" if failures == 0 else "DDICT_REL_REPRESENTATION_PLAN_REVIEW"

    boundary_rows = [
        {"boundary": "rel_representation_plan_only", "observed": 1, "required": 1, "pass": 1},
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
            "slice_id": "DD078A_REL_BOTH_ONLY",
            "surface": "DDICT REL <object> [BOTH]",
            "allowed_future_edits": "cmd_ddict.cpp/read-only helper only, after explicit authorization",
            "logic": "Resolve object and print incoming/outgoing edge summaries; default BOTH.",
            "success_smoke": "DDICT REL DDOBJECT BOTH shows resolved object and relationship rows without mutation.",
        },
        {
            "slice_id": "DD078B_REL_DIRECTION_FILTERS",
            "surface": "DDICT REL <object> IN|OUT|BOTH",
            "allowed_future_edits": "same read-only helper only",
            "logic": "Add direction filter parsing and bounded row display.",
            "success_smoke": "DDICT REL DDATTR IN and OUT produce distinct groups.",
        },
    ]

    write_csv(out / "dd077_target_schema_fields.csv", schema, ["table", "ordinal", "field", "type", "width", "dbf"])
    write_csv(out / "dd077_edge_type_counts.csv", edge_types, ["edgetype", "count"])
    write_csv(out / "dd077_sample_object_resolution.csv", object_summary, ["token", "resolved", "objid", "objtype", "name", "owner", "incoming_edges", "outgoing_edges", "field_edges", "tag_edges"])
    write_csv(out / "dd077_sample_edge_rows.csv", sample_edges, ["edgeid", "edgetype", "fromobj", "from_type", "from_name", "from_owner", "toobj", "to_type", "to_name", "to_owner", "evid"])
    write_csv(out / "dd077_query_pattern_plan.csv", query_rows, ["query_id", "surface", "ready", "logic", "risk"])
    write_csv(out / "dd077_implementation_slice_plan.csv", impl_rows, ["slice_id", "surface", "allowed_future_edits", "logic", "success_smoke"])
    write_csv(out / "dd077_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd077_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-077 DDICT REL Representation and Implementation Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-077 discovers the active catalog relationship representation needed for future
`DDICT REL <object-id-or-name> [IN|OUT|BOTH]`.

## Inputs

- DD-076 status: `{dd076_manifest.get('status', '')}`
- Active catalog: `{rel(repo, active_dir)}`

## Findings

- DDOBJECT rows: **{object_count}**
- DDEDGE rows: **{edge_count}**
- Edge type count: **{edge_type_count}**
- Sample objects resolved: **{sample_resolved} / {len(SAMPLE_OBJECTS)}**

## Recommended implementation model

Start with a bounded read-only relationship view:

```text
DDICT REL <object> [BOTH]
  resolve token to DDOBJECT
  print resolved object identity
  print outgoing DDEDGE rows decorated with TOOBJ object info
  print incoming DDEDGE rows decorated with FROMOBJ object info
```

Then add direction filters:

```text
DDICT REL <object> IN
DDICT REL <object> OUT
DDICT REL <object> BOTH
```

Do not make `DDICT REL` repair relationships, create edges, rebuild indexes, or mutate catalogs.

## Boundary

DD-077 is representation discovery and planning only. It does not edit C++ source,
registry/build files, active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK, or
manual/catalog rows.
"""
    (out / "DD077_DDICT_REL_REPRESENTATION_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd077_ddict_rel_representation_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd076_status": dd076_manifest.get("status", ""),
        "active_catalog_path": rel(repo, active_dir),
        "object_rows": object_count,
        "edge_rows": edge_count,
        "edge_type_count": edge_type_count,
        "sample_objects_resolved": sample_resolved,
        "failures": failures,
        "cxx_source_edits": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "Review DD-077 relationship ledgers, then authorize DD-078 guarded DDICT REL implementation.",
    }
    write_json(out / "dd077_ddict_rel_representation_plan_manifest.json", manifest)

    print(f"DD-077 DDICT REL representation plan manifest: {out / 'dd077_ddict_rel_representation_plan_manifest.json'}")
    print(f"status: {status}; objects: {object_count}; edges: {edge_count}; edge_types: {edge_type_count}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
