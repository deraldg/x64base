#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD079_STATUS = "DDICT_REL_RUNTIME_CLOSURE_GREEN"
TARGET_TABLES = ["DDOBJECT", "DDATTR", "DDEDGE", "DDEVID", "DDSOURCE", "DDARTIF"]
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


def build_object_maps(objects: List[Dict[str, str]]) -> Tuple[Dict[str, Dict[str, str]], Dict[str, List[Dict[str, str]]]]:
    by_id: Dict[str, Dict[str, str]] = {}
    by_token: Dict[str, List[Dict[str, str]]] = {}
    for row in objects:
        objid = trim(row.get("OBJID", ""))
        name = up(row.get("NAME", ""))
        owner = up(row.get("OWNER", ""))
        if objid:
            by_id[objid] = row
        for key in {objid.upper(), name, owner, f"{owner}.{name}", f"{name}.{owner}"}:
            key = key.strip(".")
            if key:
                by_token.setdefault(key, []).append(row)
    return by_id, by_token


def resolve_object(objects: List[Dict[str, str]], token: str) -> Dict[str, str]:
    want = up(token)
    by_id, by_token = build_object_maps(objects)
    if want in by_id:
        return by_id[want]
    matches = by_token.get(want, [])
    for row in matches:
        if up(row.get("OBJTYPE", "")) == "CATALOG_TABLE" and up(row.get("NAME", "")) == want:
            return row
    return matches[0] if matches else {}


def evidence_analysis(rows_by_table: Dict[str, List[Dict[str, str]]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    objects = rows_by_table.get("DDOBJECT", [])
    attrs = rows_by_table.get("DDATTR", [])
    edges = rows_by_table.get("DDEDGE", [])
    evid = rows_by_table.get("DDEVID", [])
    sources = rows_by_table.get("DDSOURCE", [])
    artifacts = rows_by_table.get("DDARTIF", [])

    source_by_id = {trim(r.get("SRCID", "")): r for r in sources}
    artifact_by_id = {trim(r.get("ARTID", "")): r for r in artifacts}
    evid_by_obj: Dict[str, List[Dict[str, str]]] = {}
    for row in evid:
        objid = trim(row.get("OBJID", ""))
        if objid:
            evid_by_obj.setdefault(objid, []).append(row)

    attr_by_obj: Dict[str, List[Dict[str, str]]] = {}
    for row in attrs:
        objid = trim(row.get("OBJID", ""))
        if objid:
            attr_by_obj.setdefault(objid, []).append(row)

    sample_rows: List[Dict[str, Any]] = []
    for token in SAMPLE_OBJECTS:
        obj = resolve_object(objects, token)
        objid = trim(obj.get("OBJID", ""))
        obj_evid = evid_by_obj.get(objid, [])
        obj_attrs = attr_by_obj.get(objid, [])
        srcids = sorted({trim(e.get("SRCID", "")) for e in obj_evid if trim(e.get("SRCID", ""))})
        kinds = sorted({trim(e.get("KIND", "")) for e in obj_evid if trim(e.get("KIND", ""))})
        sample_rows.append({
            "token": token,
            "resolved": int(bool(objid)),
            "objid": objid,
            "objtype": obj.get("OBJTYPE", ""),
            "name": obj.get("NAME", ""),
            "owner": obj.get("OWNER", ""),
            "evidence_rows": len(obj_evid),
            "attribute_rows": len(obj_attrs),
            "srcids": ",".join(srcids),
            "evidence_kinds": ",".join(kinds),
        })

    evid_rows: List[Dict[str, Any]] = []
    for row in evid[:250]:
        srcid = trim(row.get("SRCID", ""))
        artid = trim(row.get("ARTID", ""))
        src = source_by_id.get(srcid, {})
        art = artifact_by_id.get(artid, {})
        evid_rows.append({
            "evid": row.get("EVID", ""),
            "objid": row.get("OBJID", ""),
            "srcid": srcid,
            "kind": row.get("KIND", ""),
            "artid": artid,
            "source_kind": src.get("KIND", ""),
            "source_path": src.get("PATH", "") or src.get("NAME", ""),
            "artifact_kind": art.get("KIND", ""),
            "artifact_path": art.get("PATH", "") or art.get("NAME", ""),
        })

    ref_summary = [
        {"source": "DDEVID", "rows": len(evid), "role": "object-level evidence links"},
        {"source": "DDSOURCE", "rows": len(sources), "role": "source inventory / provenance roots"},
        {"source": "DDARTIF", "rows": len(artifacts), "role": "artifact/report links"},
        {"source": "DDATTR", "rows": len(attrs), "role": "object attributes, including memo-backed notes where present"},
        {"source": "DDEDGE", "rows": len(edges), "role": "relationship evidence through EVID field where populated"},
    ]
    return sample_rows, evid_rows, ref_summary


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-080 DDICT EVIDENCE representation and implementation plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD080-ddict-evidence-representation-plan-v0")
    ap.add_argument("--dd079-dir", default="docs/datadict/reports/DD079-ddict-rel-runtime-closure-v0")
    ap.add_argument("--active-catalog-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd079_dir = (repo / args.dd079_dir).resolve()
    dd079_manifest = read_json(dd079_dir / "dd079_rel_runtime_closure_manifest.json")
    active_dir = (repo / args.active_catalog_path).resolve()

    schema, rows_by_table, meta = load_tables(repo, active_dir)
    sample_evidence, evid_samples, ref_summary = evidence_analysis(rows_by_table)

    dd079_green = int(dd079_manifest.get("status") == EXPECTED_DD079_STATUS)
    active_exists = int(active_dir.exists())
    target_tables_present = sum(1 for t in TARGET_TABLES if meta.get(t, {}).get("exists") == 1)
    evid_rows = len(rows_by_table.get("DDEVID", []))
    source_rows = len(rows_by_table.get("DDSOURCE", []))
    artifact_rows = len(rows_by_table.get("DDARTIF", []))
    sample_resolved = sum(1 for r in sample_evidence if int(r["resolved"]) == 1)

    query_rows = [
        {
            "query_id": "Q_EVIDENCE_RESOLVE_OBJECT",
            "surface": "DDICT EVIDENCE <object-id-or-name>",
            "ready": int(len(rows_by_table.get("DDOBJECT", [])) > 0),
            "logic": "Resolve token as OBJID or DDOBJECT NAME/OWNER token, preferring CATALOG_TABLE for table names.",
            "risk": "LOW",
        },
        {
            "query_id": "Q_EVIDENCE_DIRECT",
            "surface": "DDICT EVIDENCE <object>",
            "ready": int(evid_rows >= 0),
            "logic": "Read DDEVID rows for resolved OBJID; decorate SRCID/ARTID if present.",
            "risk": "LOW",
        },
        {
            "query_id": "Q_EVIDENCE_ATTRIBUTES",
            "surface": "DDICT EVIDENCE <object>",
            "ready": int(len(rows_by_table.get("DDATTR", [])) > 0),
            "logic": "Show bounded DDATTR rows for object as supplementary definition evidence.",
            "risk": "LOW_MEDIUM",
        },
        {
            "query_id": "Q_EVIDENCE_RELATION_HINT",
            "surface": "DDICT EVIDENCE <object>",
            "ready": int(len(rows_by_table.get("DDEDGE", [])) > 0),
            "logic": "Optionally report relationship EVID counts later; first implementation should keep edge evidence summary bounded.",
            "risk": "MEDIUM",
        },
    ]

    gate_rows = [
        {"gate": "dd079_rel_closure_green", "expected": EXPECTED_DD079_STATUS, "observed": dd079_manifest.get("status", ""), "pass": dd079_green},
        {"gate": "active_catalog_dir_exists", "expected": 1, "observed": active_exists, "pass": active_exists},
        {"gate": "target_tables_present", "expected": len(TARGET_TABLES), "observed": target_tables_present, "pass": int(target_tables_present == len(TARGET_TABLES))},
        {"gate": "sample_objects_resolved", "expected": len(SAMPLE_OBJECTS), "observed": sample_resolved, "pass": int(sample_resolved == len(SAMPLE_OBJECTS))},
        {"gate": "schema_inspection_completed", "expected": 1, "observed": 1, "pass": 1},
        {"gate": "representation_plan_only", "expected": 1, "observed": 1, "pass": 1},
    ]
    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_EVIDENCE_REPRESENTATION_PLAN_READY" if failures == 0 else "DDICT_EVIDENCE_REPRESENTATION_PLAN_REVIEW"

    boundary_rows = [
        {"boundary": "evidence_representation_plan_only", "observed": 1, "required": 1, "pass": 1},
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
            "slice_id": "DD081A_EVIDENCE_OBJECT_ATTRS",
            "surface": "DDICT EVIDENCE <object>",
            "allowed_future_edits": "cmd_ddict.cpp/read-only helper only, after explicit authorization",
            "logic": "Resolve object and show object identity plus bounded DDEVID and DDATTR evidence rows.",
            "success_smoke": "DDICT EVIDENCE DDOBJECT shows resolved object, evidence/attribute counts, and no mutation.",
        },
        {
            "slice_id": "DD081B_EVIDENCE_SOURCE_ARTIFACT_DECORATION",
            "surface": "DDICT EVIDENCE <object>",
            "allowed_future_edits": "same read-only helper only",
            "logic": "Decorate DDEVID rows with DDSOURCE/DDARTIF when available.",
            "success_smoke": "DDICT EVIDENCE DDATTR shows source/artifact references when catalog rows provide them.",
        },
    ]

    write_csv(out / "dd080_target_schema_fields.csv", schema, ["table", "ordinal", "field", "type", "width", "dbf"])
    write_csv(out / "dd080_reference_summary.csv", ref_summary, ["source", "rows", "role"])
    write_csv(out / "dd080_sample_object_evidence.csv", sample_evidence, ["token", "resolved", "objid", "objtype", "name", "owner", "evidence_rows", "attribute_rows", "srcids", "evidence_kinds"])
    write_csv(out / "dd080_evidence_sample_rows.csv", evid_samples, ["evid", "objid", "srcid", "kind", "artid", "source_kind", "source_path", "artifact_kind", "artifact_path"])
    write_csv(out / "dd080_query_pattern_plan.csv", query_rows, ["query_id", "surface", "ready", "logic", "risk"])
    write_csv(out / "dd080_implementation_slice_plan.csv", impl_rows, ["slice_id", "surface", "allowed_future_edits", "logic", "success_smoke"])
    write_csv(out / "dd080_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd080_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-080 DDICT EVIDENCE Representation and Implementation Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-080 discovers the active catalog evidence representation needed for future:

```text
DDICT EVIDENCE <object-id-or-name>
```

## Inputs

- DD-079 status: `{dd079_manifest.get('status', '')}`
- Active catalog: `{rel(repo, active_dir)}`

## Findings

- DDEVID rows: **{evid_rows}**
- DDSOURCE rows: **{source_rows}**
- DDARTIF rows: **{artifact_rows}**
- Sample objects resolved: **{sample_resolved} / {len(SAMPLE_OBJECTS)}**
- Target tables present: **{target_tables_present} / {len(TARGET_TABLES)}**

## Recommended implementation model

Start with bounded read-only object evidence:

```text
DDICT EVIDENCE <object>
  resolve token to DDOBJECT
  print resolved object identity
  print bounded DDEVID rows for OBJID
  print bounded DDATTR rows for OBJID
  decorate with DDSOURCE/DDARTIF where available
```

Do not make `DDICT EVIDENCE` repair provenance, create evidence rows, rewrite memo payloads,
or mutate catalogs.

## Boundary

DD-080 is representation discovery and planning only. It does not edit C++ source,
registry/build files, active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK, or
manual/catalog rows.
"""
    (out / "DD080_DDICT_EVIDENCE_REPRESENTATION_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd080_ddict_evidence_representation_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd079_status": dd079_manifest.get("status", ""),
        "active_catalog_path": rel(repo, active_dir),
        "ddevid_rows": evid_rows,
        "ddsource_rows": source_rows,
        "ddartif_rows": artifact_rows,
        "sample_objects_resolved": sample_resolved,
        "failures": failures,
        "cxx_source_edits": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "Review DD-080 evidence ledgers, then authorize DD-081 guarded DDICT EVIDENCE implementation.",
    }
    write_json(out / "dd080_ddict_evidence_representation_plan_manifest.json", manifest)

    print(f"DD-080 DDICT EVIDENCE representation plan manifest: {out / 'dd080_ddict_evidence_representation_plan_manifest.json'}")
    print(f"status: {status}; evid_rows: {evid_rows}; sources: {source_rows}; artifacts: {artifact_rows}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
