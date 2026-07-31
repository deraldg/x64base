#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD073_STATUS = "DDICT_FIELDS_RUNTIME_CLOSURE_GREEN"

CATALOG_TABLES = ["DDOBJECT", "DDATTR", "DDEDGE", "DDARTIF", "DDRUN", "DDBASE"]
TAG_TERMS = ["TAG", "INDEX", "CDX", "ORDER", "KEY", "LMDB"]


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


def upper(s: str) -> str:
    return (s or "").upper()


def trim(s: str) -> str:
    return (s or "").replace("\x00", "").strip()


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
    try:
        ftype = chr(data[off + 11])
    except Exception:
        return False
    return ftype in set("CDNLFIMBYT@GOVQ")


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
        fields.append({"name": desc_name(data, off), "type": chr(data[off+11]), "width": width, "offset": off})
        off += 32
        if len(fields) > 512:
            break
    return fields


def read_dbf(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]], Dict[str, Any]]:
    if not path.exists():
        return [], [], {"exists": 0, "records": 0, "header_len": 0, "record_len": 0, "descriptor_start": -1}
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
    meta = {
        "exists": 1,
        "records": records,
        "header_len": header_len,
        "record_len": record_len,
        "descriptor_start": descriptor_start(data),
        "file_bytes": path.stat().st_size,
    }
    return fields, rows, meta


def scan_tag_signals(repo: Path, active_dir: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    schema_rows: List[Dict[str, Any]] = []
    signal_rows: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {}
    for table in CATALOG_TABLES:
        path = active_dir / f"{table}.dbf"
        fields, rows, meta = read_dbf(path)
        summary[table] = {"fields": len(fields), "rows": len(rows), **meta}
        for idx, f in enumerate(fields, start=1):
            schema_rows.append({
                "table": table,
                "ordinal": idx,
                "field": f["name"],
                "type": f["type"],
                "width": f["width"],
                "dbf": rel(repo, path),
            })
        for rowno, row in enumerate(rows, start=1):
            joined = " | ".join(f"{k}={v}" for k, v in row.items())
            u = joined.upper()
            terms = [term for term in TAG_TERMS if term in u]
            if terms:
                signal_rows.append({
                    "table": table,
                    "rowno": rowno,
                    "terms": ",".join(terms),
                    "objid": row.get("OBJID", ""),
                    "objtype": row.get("OBJTYPE", ""),
                    "name": row.get("NAME", ""),
                    "owner": row.get("OWNER", ""),
                    "attrname": row.get("ATTRNAME", ""),
                    "attrval": row.get("ATTRVAL", "")[:160],
                    "edgetype": row.get("EDGETYPE", ""),
                    "fromobj": row.get("FROMOBJ", ""),
                    "toobj": row.get("TOOBJ", ""),
                    "snippet": joined[:260],
                })
    return schema_rows, signal_rows, summary


def inventory_artifacts(repo: Path, active_dir: Path, staging_dir: Path) -> List[Dict[str, Any]]:
    roots = [
        active_dir,
        staging_dir,
        repo / "dottalkpp" / "indexes",
        repo / "dottalkpp" / "data" / "indexes",
        repo / "dottalkpp" / "lmdb",
        repo / "dottalkpp" / "data" / "lmdb",
        repo / "indexes",
        repo / "lmdb",
    ]
    rows: List[Dict[str, Any]] = []
    seen = set()
    for root in roots:
        if not root.exists():
            rows.append({
                "root": rel(repo, root),
                "path": "",
                "kind": "ROOT_MISSING",
                "table_guess": "",
                "exists": 0,
                "bytes": 0,
            })
            continue
        for path in root.rglob("*"):
            if not path.is_file() and not path.is_dir():
                continue
            suffix = path.suffix.lower()
            name = path.name.lower()
            kind = ""
            if path.is_file() and suffix == ".cdx":
                kind = "CDX"
            elif path.is_file() and suffix in {".idx", ".ntx"}:
                kind = "OTHER_INDEX_FILE"
            elif path.is_file() and suffix in {".mdb", ".mdbx", ".dat", ".lock"} and "lmdb" in str(path).lower():
                kind = "LMDB_FILE"
            elif path.is_dir() and ("lmdb" in str(path).lower() or name in {t.lower() for t in CATALOG_TABLES}):
                kind = "DIR_REVIEW"
            if not kind:
                continue
            key = str(path.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            stem = path.stem.upper()
            table_guess = stem if stem in {t.upper() for t in CATALOG_TABLES + ["DDPROFILE", "DDEVID", "DDGATE", "DDREVIEW"]} else ""
            rows.append({
                "root": rel(repo, root),
                "path": rel(repo, path),
                "kind": kind,
                "table_guess": table_guess,
                "exists": 1,
                "bytes": path.stat().st_size if path.is_file() else 0,
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-074 DDICT TAGS representation discovery and plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD074-ddict-tags-representation-plan-v0")
    ap.add_argument("--dd073-dir", default="docs/datadict/reports/DD073-fields-runtime-closure-v0")
    ap.add_argument("--active-catalog-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--staging-catalog-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd073_dir = (repo / args.dd073_dir).resolve()
    dd073_manifest = read_json(dd073_dir / "dd073_fields_runtime_closure_manifest.json")
    active_dir = (repo / args.active_catalog_path).resolve()
    staging_dir = (repo / args.staging_catalog_path).resolve()

    schema_rows, signal_rows, summary = scan_tag_signals(repo, active_dir)
    artifact_rows = inventory_artifacts(repo, active_dir, staging_dir)

    dd073_green = int(dd073_manifest.get("status") == EXPECTED_DD073_STATUS)
    active_exists = int(active_dir.exists())
    cdx_count = sum(1 for r in artifact_rows if r["kind"] == "CDX")
    lmdb_count = sum(1 for r in artifact_rows if r["kind"] == "LMDB_FILE")
    signal_count = len(signal_rows)
    schema_target_ok = int(all(summary.get(t, {}).get("fields", 0) > 0 for t in ["DDOBJECT", "DDATTR", "DDEDGE"]))

    query_rows = [
        {
            "query_id": "Q_TAGS_CDX_ARTIFACTS",
            "source": "CDX artifact inventory",
            "ready": int(cdx_count > 0),
            "logic": "If canonical CDX files are present, DDICT TAGS can report table-level tag availability from artifacts first.",
            "risk": "LOW",
        },
        {
            "query_id": "Q_TAGS_CATALOG_SIGNALS",
            "source": "DDOBJECT/DDATTR/DDEDGE tag/index signal rows",
            "ready": int(signal_count > 0),
            "logic": "If catalog rows contain TAG/INDEX/CDX/ORDER signals, DDICT TAGS can decorate artifact tags with catalog provenance.",
            "risk": "MEDIUM",
        },
        {
            "query_id": "Q_TAGS_LMDB_MIRRORS",
            "source": "LMDB artifact inventory",
            "ready": int(lmdb_count > 0),
            "logic": "LMDB mirrors may support future confirmation only; do not make DDICT TAGS depend on LMDB mutation or rebuild.",
            "risk": "MEDIUM",
        },
    ]

    gate_rows = [
        {"gate": "dd073_fields_closure_green", "expected": EXPECTED_DD073_STATUS, "observed": dd073_manifest.get("status", ""), "pass": dd073_green},
        {"gate": "active_catalog_dir_exists", "expected": 1, "observed": active_exists, "pass": active_exists},
        {"gate": "target_schema_available", "expected": 1, "observed": schema_target_ok, "pass": schema_target_ok},
        {"gate": "artifact_inventory_completed", "expected": 1, "observed": 1, "pass": 1},
        {"gate": "tag_signal_scan_completed", "expected": 1, "observed": 1, "pass": 1},
        {"gate": "representation_plan_only", "expected": 1, "observed": 1, "pass": 1},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_TAGS_REPRESENTATION_PLAN_READY" if failures == 0 else "DDICT_TAGS_REPRESENTATION_PLAN_REVIEW"

    boundary_rows = [
        {"boundary": "tags_representation_plan_only", "observed": 1, "required": 1, "pass": 1},
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
            "slice_id": "DD075A_TAGS_ARTIFACT_ONLY",
            "surface": "DDICT TAGS <table>",
            "allowed_future_edits": "cmd_ddict.cpp/read-only helper only, after explicit authorization",
            "logic": "Report table CDX presence and known tag names from artifact/catalog signals without changing indexes.",
            "success_smoke": "DDICT TAGS DDATTR reports read-only tag/index status and does not rebuild CDX/LMDB.",
        },
        {
            "slice_id": "DD075B_TAGS_CATALOG_DECORATED",
            "surface": "DDICT TAGS <table>",
            "allowed_future_edits": "read-only helper only",
            "logic": "Add catalog provenance decoration once artifact-only tags are proven.",
            "success_smoke": "DDICT TAGS DDATTR shows tag sources and related catalog object/attribute evidence.",
        },
    ]

    write_csv(out / "dd074_index_artifact_inventory.csv", artifact_rows, ["root", "path", "kind", "table_guess", "exists", "bytes"])
    write_csv(out / "dd074_catalog_schema_fields.csv", schema_rows, ["table", "ordinal", "field", "type", "width", "dbf"])
    write_csv(out / "dd074_catalog_tag_signal_rows.csv", signal_rows, ["table", "rowno", "terms", "objid", "objtype", "name", "owner", "attrname", "attrval", "edgetype", "fromobj", "toobj", "snippet"])
    write_csv(out / "dd074_query_pattern_plan.csv", query_rows, ["query_id", "source", "ready", "logic", "risk"])
    write_csv(out / "dd074_implementation_slice_plan.csv", impl_rows, ["slice_id", "surface", "allowed_future_edits", "logic", "success_smoke"])
    write_csv(out / "dd074_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd074_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-074 DDICT TAGS Representation Discovery and Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-074 discovers how the active Data Dictionary should support future
`DDICT TAGS <table>` output without assuming that tags live in only one place.

## Inputs

- DD-073 status: `{dd073_manifest.get('status', '')}`
- Active catalog: `{rel(repo, active_dir)}`
- Staging catalog: `{rel(repo, staging_dir)}`

## Findings

- CDX artifacts discovered: **{cdx_count}**
- LMDB artifacts discovered: **{lmdb_count}**
- Catalog tag/index signal rows: **{signal_count}**
- Target schema available: **{schema_target_ok}**

## Recommended implementation model

Start with an artifact/read-only view:

```text
DDICT TAGS <table>
  active catalog path
  table DBF presence
  CDX artifact presence
  tag/index signal rows, if present
  LMDB mirror presence, if present
```

Do not make `DDICT TAGS` create, rebuild, repair, or promote indexes.

## Boundary

DD-074 is representation discovery and planning only. It does not edit C++ source,
registry/build files, active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK, or
manual/catalog rows.
"""
    (out / "DD074_DDICT_TAGS_REPRESENTATION_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd074_ddict_tags_representation_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd073_status": dd073_manifest.get("status", ""),
        "active_catalog_path": rel(repo, active_dir),
        "staging_catalog_path": rel(repo, staging_dir),
        "cdx_artifact_count": cdx_count,
        "lmdb_artifact_count": lmdb_count,
        "catalog_tag_signal_rows": signal_count,
        "failures": failures,
        "cxx_source_edits": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "Review DD-074 inventories, then authorize DD-075 guarded DDICT TAGS artifact-only implementation.",
    }
    write_json(out / "dd074_ddict_tags_representation_plan_manifest.json", manifest)

    print(f"DD-074 DDICT TAGS representation plan manifest: {out / 'dd074_ddict_tags_representation_plan_manifest.json'}")
    print(f"status: {status}; cdx: {cdx_count}; lmdb: {lmdb_count}; catalog_signals: {signal_count}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
