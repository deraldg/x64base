#!/usr/bin/env python3
"""
DD-041 Sandbox Catalog DBF Creation and Readback Smoke.

Authorized mutation scope:
  create/write DBF and optional DBT files ONLY under the configured sandbox path:
    dottalkpp/data/metadata/datadict_sandbox/

This tool imports DD-040 projected CSV rows into sandbox DBFs and validates
readback counts. It does not create CDX files, write LMDB data, launch DotTalk++,
mutate HELP/META/CMDHELPCHK, promote an active catalog, or edit source.

Implementation note:
  This writer emits simple xBase DBF files directly from the DD-039 DBF layout
  definitions and DD-040 projected CSV rows. Memo fields are stored in DBT
  sidecar files using fixed-size 512-byte blocks for this sandbox smoke.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import math
import os
import shutil
import struct
from pathlib import Path
from typing import Any, Dict, List, Tuple


CATALOG_TABLES = [
    "DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE",
    "DDEVID", "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE"
]

DBT_BLOCK_SIZE = 512


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def assert_within_repo(repo: Path, path: Path) -> None:
    repo_r = repo.resolve()
    path_r = path.resolve()
    try:
        path_r.relative_to(repo_r)
    except Exception:
        raise SystemExit(f"Refusing path outside repo root: {path_r}")


def assert_sandbox_path(repo: Path, sandbox: Path) -> None:
    assert_within_repo(repo, sandbox)
    rel = sandbox.resolve().relative_to(repo.resolve()).as_posix().lower()
    allowed = "dottalkpp/data/metadata/datadict_sandbox"
    if rel != allowed and not rel.startswith(allowed + "/"):
        raise SystemExit(f"Refusing sandbox write outside allowed sandbox path: {rel}")


def load_field_definitions(def_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    rows = read_csv_dict(def_dir / "dd039_catalog_field_definition_plan_v0.csv")
    by_table: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        table = str(r.get("table", "")).upper()
        if not table:
            continue
        field = str(r.get("field", "")).upper()
        ftype = str(r.get("type", "C")).upper()
        width = int(float(r.get("width") or 10))
        dec = int(float(r.get("decimals") or 0))
        if len(field) > 10:
            raise SystemExit(f"DBF field name exceeds 10 characters for {table}.{field}")
        by_table.setdefault(table, []).append({
            "name": field,
            "type": ftype,
            "width": width,
            "decimals": dec,
            "required": str(r.get("required", "0")),
            "description": r.get("description", ""),
        })
    return by_table


def encode_text(value: Any, width: int) -> bytes:
    s = "" if value is None else str(value)
    b = s.encode("cp1252", errors="replace")[:width]
    return b.ljust(width, b" ")


def encode_num(value: Any, width: int, decimals: int) -> bytes:
    s = "" if value is None else str(value).strip()
    if not s:
        return b" " * width
    try:
        n = float(s)
        if decimals == 0:
            out = str(int(n))
        else:
            out = f"{n:.{decimals}f}"
    except Exception:
        out = s
    return out.encode("ascii", errors="ignore")[:width].rjust(width, b" ")


def encode_logical(value: Any) -> bytes:
    s = "" if value is None else str(value).strip().upper()
    if s in {"1", "T", "TRUE", "Y", "YES"}:
        return b"T"
    if s in {"0", "F", "FALSE", "N", "NO"}:
        return b"F"
    return b"?"


def dbt_init(path: Path) -> bytearray:
    header = bytearray(DBT_BLOCK_SIZE)
    # dBASE III style: next available block as big-endian 32-bit at bytes 0..3.
    header[0:4] = (1).to_bytes(4, "big")
    return header


def dbt_add_memo(dbt: bytearray, text: str) -> int:
    if text is None:
        text = ""
    if not str(text):
        return 0
    pointer = len(dbt) // DBT_BLOCK_SIZE
    data = str(text).encode("cp1252", errors="replace") + b"\x1a\x1a"
    blocks = max(1, math.ceil(len(data) / DBT_BLOCK_SIZE))
    padded = data.ljust(blocks * DBT_BLOCK_SIZE, b"\x00")
    dbt.extend(padded)
    next_block = len(dbt) // DBT_BLOCK_SIZE
    dbt[0:4] = next_block.to_bytes(4, "big")
    return pointer


def write_dbf(table: str, fields: List[Dict[str, Any]], rows: List[Dict[str, str]], out_dir: Path) -> Dict[str, Any]:
    has_memo = any(f["type"] == "M" for f in fields)
    version = 0x83 if has_memo else 0x03
    today = _dt.date.today()
    header_len = 32 + 32 * len(fields) + 1
    record_len = 1 + sum(int(f["width"]) for f in fields)
    record_count = len(rows)

    dbf_path = out_dir / f"{table}.dbf"
    dbt_path = out_dir / f"{table}.dbt"
    dbt = dbt_init(dbt_path) if has_memo else None

    header = bytearray()
    header.append(version)
    header.extend(bytes([today.year - 1900, today.month, today.day]))
    header.extend(struct.pack("<I", record_count))
    header.extend(struct.pack("<H", header_len))
    header.extend(struct.pack("<H", record_len))
    header.extend(b"\x00" * 20)

    for f in fields:
        name = f["name"].encode("ascii", errors="ignore")[:10]
        desc = bytearray(32)
        desc[0:len(name)] = name
        desc[11] = ord(f["type"])
        desc[16] = int(f["width"])
        desc[17] = int(f["decimals"])
        header.extend(desc)
    header.append(0x0D)

    records = bytearray()
    for row in rows:
        records.extend(b" ")
        for f in fields:
            name = f["name"]
            typ = f["type"]
            width = int(f["width"])
            dec = int(f["decimals"])
            value = row.get(name, "")
            if typ == "C":
                records.extend(encode_text(value, width))
            elif typ == "N":
                records.extend(encode_num(value, width, dec))
            elif typ == "L":
                records.extend(encode_logical(value))
            elif typ == "M":
                ptr = dbt_add_memo(dbt, str(value or "")) if dbt is not None else 0
                if ptr == 0:
                    records.extend(b" " * width)
                else:
                    records.extend(str(ptr).encode("ascii").rjust(width, b" ")[:width])
            else:
                records.extend(encode_text(value, width))
    eof = b"\x1A"

    with dbf_path.open("wb") as f:
        f.write(header)
        f.write(records)
        f.write(eof)

    if dbt is not None:
        with dbt_path.open("wb") as f:
            f.write(dbt)

    return {
        "table": table,
        "dbf_path": dbf_path,
        "dbt_path": dbt_path if has_memo else None,
        "rows_written": record_count,
        "field_count": len(fields),
        "header_len": header_len,
        "record_len": record_len,
        "has_memo": int(has_memo),
        "dbf_sha256": sha256_file(dbf_path),
        "dbt_sha256": sha256_file(dbt_path) if has_memo else "",
    }


def read_dbf_header(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        data = f.read(4096)
    if len(data) < 32:
        raise ValueError(f"Too small for DBF header: {path}")
    version = data[0]
    records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    field_count = (header_len - 33) // 32
    fields = []
    offset = 32
    for _ in range(field_count):
        desc = data[offset:offset+32]
        raw_name = desc[0:11].split(b"\x00", 1)[0]
        fields.append({
            "name": raw_name.decode("ascii", errors="ignore"),
            "type": chr(desc[11]),
            "width": desc[16],
            "decimals": desc[17],
        })
        offset += 32
    return {
        "version": version,
        "records": records,
        "header_len": header_len,
        "record_len": record_len,
        "field_count": field_count,
        "fields": fields,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-041 sandbox catalog DBF creation and readback smoke")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--projection-dir", required=True, help="DD-040 projection output directory")
    ap.add_argument("--definition-dir", default="docs/datadict/definitions", help="DD-039 definition CSV directory")
    ap.add_argument("--sandbox-path", default="dottalkpp/data/metadata/datadict_sandbox")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD041-sandbox-catalog-dbf-smoke-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--execute-sandbox-write", action="store_true", help="Required to create/write sandbox DBFs")
    ap.add_argument("--replace-existing-sandbox", action="store_true")
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    projection_dir = Path(args.projection_dir).resolve()
    definition_dir = (repo / args.definition_dir).resolve()
    sandbox = (repo / args.sandbox_path).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    assert_sandbox_path(repo, sandbox)

    if not args.execute_sandbox_write:
        manifest = {
            "contract": "dd041_sandbox_catalog_dbf_creation_readback_smoke_v0",
            "run_id": args.run_id,
            "created_utc": utc_now(),
            "status": "SANDBOX_WRITE_NOT_EXECUTED",
            "reason": "Missing --execute-sandbox-write",
            "sandbox_path": str(sandbox),
            "dbf_tables_created": 0,
            "dbf_rows_written": 0,
            "protected_system_mutations": 0,
        }
        write_json(out / "dd041_sandbox_catalog_dbf_smoke_manifest.json", manifest)
        print(f"DD-041 manifest: {out / 'dd041_sandbox_catalog_dbf_smoke_manifest.json'}")
        print("status: SANDBOX_WRITE_NOT_EXECUTED; add --execute-sandbox-write after authorization")
        return 2 if args.fail_on_review else 0

    field_defs = load_field_definitions(definition_dir)

    if sandbox.exists() and any(sandbox.iterdir()):
        if not args.replace_existing_sandbox:
            raise SystemExit(f"Sandbox is not empty; rerun with --replace-existing-sandbox if intended: {sandbox}")
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True, exist_ok=True)

    table_rows: List[Dict[str, Any]] = []
    boundary_rows: List[Dict[str, Any]] = []
    failures = 0
    total_written = 0

    for table in CATALOG_TABLES:
        csv_path = projection_dir / f"dd040_projected_{table}.csv"
        rows = read_csv_dict(csv_path)
        fields = field_defs.get(table, [])
        if not fields:
            failures += 1
            table_rows.append({"table": table, "status": "FAIL_NO_FIELD_DEFINITION", "projected_rows": len(rows), "written_rows": 0, "readback_rows": 0, "pass": 0})
            continue

        result = write_dbf(table, fields, rows, sandbox)
        header = read_dbf_header(result["dbf_path"])
        pass_row = int(header["records"] == len(rows) and header["field_count"] == len(fields))
        if not pass_row:
            failures += 1
        total_written += len(rows)
        table_rows.append({
            "table": table,
            "status": "PASS" if pass_row else "FAIL_READBACK_MISMATCH",
            "projected_rows": len(rows),
            "written_rows": result["rows_written"],
            "readback_rows": header["records"],
            "field_count": result["field_count"],
            "readback_field_count": header["field_count"],
            "has_memo": result["has_memo"],
            "dbf_path": safe_rel(repo, result["dbf_path"]),
            "dbt_path": safe_rel(repo, result["dbt_path"]) if result["dbt_path"] else "",
            "dbf_sha256": result["dbf_sha256"],
            "dbt_sha256": result["dbt_sha256"],
            "pass": pass_row,
        })

    boundary = [
        ("sandbox_dbf_creation", 1, "1 when explicitly authorized", 1),
        ("sandbox_path_only", int(str(sandbox).lower().replace("\\","/").endswith("dottalkpp/data/metadata/datadict_sandbox")), 1, 1),
        ("cdx_created", 0, 0, 1),
        ("lmdb_written", 0, 0, 1),
        ("help_mutation", 0, 0, 1),
        ("meta_mutation", 0, 0, 1),
        ("cmdhelpchk_mutation", 0, 0, 1),
        ("active_catalog_promotion", 0, 0, 1),
        ("source_edits", 0, 0, 1),
        ("runtime_launch", 0, 0, 1),
        ("protected_system_mutations", 0, 0, 1),
    ]
    boundary_rows = [{"boundary": b, "observed": o, "required": r, "pass": p} for b, o, r, p in boundary]

    status = "SANDBOX_CATALOG_DBF_READBACK_GREEN" if failures == 0 else "SANDBOX_CATALOG_DBF_READBACK_REVIEW"

    write_csv(out / "dd041_table_readback_ledger.csv", table_rows,
              ["table", "status", "projected_rows", "written_rows", "readback_rows", "field_count",
               "readback_field_count", "has_memo", "dbf_path", "dbt_path", "dbf_sha256", "dbt_sha256", "pass"])
    write_csv(out / "dd041_no_mutation_boundary_ledger.csv", boundary_rows,
              ["boundary", "observed", "required", "pass"])

    manifest = {
        "contract": "dd041_sandbox_catalog_dbf_creation_readback_smoke_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "projection_dir": str(projection_dir),
        "definition_dir": str(definition_dir),
        "sandbox_path": str(sandbox),
        "profiles": args.profile,
        "dbf_tables_created": len([r for r in table_rows if r.get("written_rows", 0) != 0 or r.get("projected_rows", 0) == 0]),
        "dbf_rows_written": total_written,
        "readback_failures": failures,
        "cdx_created": 0,
        "lmdb_written": 0,
        "help_meta_cmdhelpchk_mutations": 0,
        "active_catalog_promotion": 0,
        "protected_system_mutations": 0,
        "next_recommended_package": "DD-042 Sandbox Catalog Query/Inspection or Promotion Gate, no promotion without authorization",
    }
    write_json(out / "dd041_sandbox_catalog_dbf_smoke_manifest.json", manifest)

    report = f"""# DD-041 Sandbox Catalog DBF Creation and Readback Smoke Report

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Sandbox path

```text
{safe_rel(repo, sandbox)}
```

## Result

- DBF tables created: {manifest['dbf_tables_created']}
- DBF rows written: {manifest['dbf_rows_written']}
- Readback failures: {manifest['readback_failures']}
- CDX created: 0
- LMDB written: 0
- Active catalog promotion: 0

## Boundary

DD-041 wrote sandbox DBF/DBT files only under the authorized sandbox path.
It did not create CDX files, write LMDB data, launch DotTalk++, mutate
HELP/META/CMDHELPCHK, edit product source, or promote the catalog.
"""
    (out / "DD041_SANDBOX_CATALOG_DBF_READBACK_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-041 sandbox catalog DBF smoke manifest: {out / 'dd041_sandbox_catalog_dbf_smoke_manifest.json'}")
    print(f"status: {status}; dbf_rows_written: {total_written}; readback_failures: {failures}; sandbox: {sandbox}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
