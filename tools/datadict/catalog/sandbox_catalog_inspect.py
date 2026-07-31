#!/usr/bin/env python3
"""
DD-042 Sandbox Catalog DBF Inspection / x64base Readback Plan.

Read-only inspection of DD-041 sandbox catalog DBFs plus generation of runtime
readback probe artifacts. This tool does not write DBFs, create CDX files, write
LMDB data, launch DotTalk++, mutate HELP/META/CMDHELPCHK, or promote a catalog.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import struct
from pathlib import Path
from typing import Any, Dict, List


CATALOG_TABLES = [
    "DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE",
    "DDEVID", "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE"
]


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
        raise SystemExit(f"Refusing sandbox inspection outside allowed sandbox path: {rel}")


def read_dbf_header(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        data = f.read(8192)
    if len(data) < 32:
        raise ValueError(f"Too small for DBF header: {path}")
    version = data[0]
    y, m, d = data[1], data[2], data[3]
    records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    field_count = (header_len - 33) // 32
    fields = []
    offset = 32
    for _ in range(field_count):
        desc = data[offset:offset + 32]
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
        "date": f"{1900+y:04d}-{m:02d}-{d:02d}",
        "records": records,
        "header_len": header_len,
        "record_len": record_len,
        "field_count": field_count,
        "fields": fields,
    }


def decode_field(raw: bytes, f: Dict[str, Any]) -> str:
    return raw.decode("cp1252", errors="replace").rstrip().strip()


def sample_dbf_rows(path: Path, limit: int = 3) -> List[Dict[str, str]]:
    header = read_dbf_header(path)
    rows: List[Dict[str, str]] = []
    if header["records"] == 0 or limit <= 0:
        return rows
    with path.open("rb") as f:
        f.seek(header["header_len"])
        for recno in range(1, min(header["records"], limit) + 1):
            rec = f.read(header["record_len"])
            if len(rec) < header["record_len"]:
                break
            deleted = rec[:1] == b"*"
            pos = 1
            out: Dict[str, str] = {"RECNO": str(recno), "DELETED": "1" if deleted else "0"}
            for fld in header["fields"]:
                width = int(fld["width"])
                raw = rec[pos:pos+width]
                pos += width
                out[fld["name"]] = decode_field(raw, fld)
            rows.append(out)
    return rows


def emit_pydottalk_probe(path: Path) -> None:
    text = """#!/usr/bin/env python3
\"\"\"
DD-042 generated pydottalk sandbox catalog readback probe.

Read-only diagnostic. It imports pydottalk, prints version/introspection details,
and lists sandbox DBFs. It deliberately avoids guessing write APIs.
\"\"\"
from pathlib import Path

repo = Path(r"D:\\code\\ccode")
sandbox = repo / "dottalkpp" / "data" / "metadata" / "datadict_sandbox"

print("DD-042 pydottalk readback probe")
print("repo:", repo)
print("sandbox:", sandbox)
print("sandbox exists:", sandbox.exists())
print("dbf files:")
for p in sorted(sandbox.glob("*.dbf")):
    print(" -", p.name)

try:
    import pydottalk
except Exception as exc:
    print("PYDOTTALK_IMPORT_ERROR:", exc)
    raise SystemExit(2)

print("pydottalk imported:", pydottalk)
print("pydottalk version:", getattr(pydottalk, "__version__", "<no __version__>"))
print("available names:")
for name in sorted(n for n in dir(pydottalk) if not n.startswith("__")):
    print(" -", name)

print()
print("No write APIs invoked. Use this output to choose the exact x64base readback surface for DD-043.")
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def emit_dotscript_probe(path: Path) -> None:
    text = """* DD-042 generated DotTalk++ sandbox catalog readback probe template
* Review before execution. Intended read-only.
*
* Terminology:
*   WORKSPACE is live/open area/session behavior.
*   DDL defines table structure.
*
* Suggested manual/runtime sequence:
*
SETPATH DBF dottalkpp/data/metadata/datadict_sandbox
*
* Then inspect a few catalog DBFs:
*
USE DDRUN
* COUNT
* TUP
* LIST STRUCTURE
*
USE DDBASE
* COUNT
* TUP
*
USE DDOBJECT
* COUNT
* TUP
*
USE DDATTR
* COUNT
* TUP
*
USE DDEDGE
* COUNT
* TUP
*
* No REPLACE, APPEND, DELETE, BUILDLMDB, or promotion commands are part of DD-042.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-042 read-only sandbox catalog DBF inspection and x64base readback plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--sandbox-path", default="dottalkpp/data/metadata/datadict_sandbox")
    ap.add_argument("--dd041-dir", default="docs/datadict/reports/DD041-sandbox-catalog-dbf-smoke-v0")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD042-sandbox-catalog-inspection-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--sample-limit", type=int, default=3)
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    sandbox = (repo / args.sandbox_path).resolve()
    dd041_dir = (repo / args.dd041_dir).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    assert_sandbox_path(repo, sandbox)

    ledger_path = dd041_dir / "dd041_table_readback_ledger.csv"
    ledger = read_csv_dict(ledger_path)
    expected_by_table: Dict[str, Dict[str, str]] = {r.get("table", "").upper(): r for r in ledger}

    table_rows: List[Dict[str, Any]] = []
    sample_rows: List[Dict[str, Any]] = []
    failures = 0

    for table in CATALOG_TABLES:
        dbf_path = sandbox / f"{table}.dbf"
        dbt_path = sandbox / f"{table}.dbt"
        expected = expected_by_table.get(table, {})
        expected_rows = int(float(expected.get("projected_rows") or 0)) if expected else ""
        expected_fields = int(float(expected.get("field_count") or 0)) if expected else ""
        has_memo = str(expected.get("has_memo", "0"))

        row = {
            "table": table,
            "dbf_exists": int(dbf_path.exists()),
            "dbt_exists": int(dbt_path.exists()),
            "expected_rows": expected_rows,
            "readback_rows": "",
            "expected_fields": expected_fields,
            "readback_fields": "",
            "has_memo": has_memo,
            "status": "PENDING",
            "pass": 0,
        }

        if not dbf_path.exists():
            row["status"] = "FAIL_MISSING_DBF"
            failures += 1
            table_rows.append(row)
            continue

        try:
            hdr = read_dbf_header(dbf_path)
            row["readback_rows"] = hdr["records"]
            row["readback_fields"] = hdr["field_count"]
            memo_ok = True
            if has_memo in {"1", "True", "true"}:
                memo_ok = dbt_path.exists()
            pass_row = (expected_rows == "" or hdr["records"] == expected_rows) and (expected_fields == "" or hdr["field_count"] == expected_fields) and memo_ok
            row["status"] = "PASS" if pass_row else "FAIL_INSPECTION_MISMATCH"
            row["pass"] = int(pass_row)
            if not pass_row:
                failures += 1

            for sample in sample_dbf_rows(dbf_path, args.sample_limit):
                sample_out = {"table": table}
                sample_out.update(sample)
                sample_rows.append(sample_out)
        except Exception as exc:
            row["status"] = f"FAIL_READ_ERROR: {exc}"
            failures += 1

        table_rows.append(row)

    boundary_rows = [
        {"boundary": "sandbox_read_only_inspection", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "dbf_rows_written_by_dd042", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_created", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_written", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "meta_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_promotion", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "runtime_launch_by_dd042", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "protected_system_mutations", "observed": 0, "required": 0, "pass": 1},
    ]

    emit_pydottalk_probe(out / "dd042_pydottalk_readback_probe.py")
    emit_dotscript_probe(out / "dd042_dottalk_readback_probe_template.dts")

    status = "SANDBOX_CATALOG_INSPECTION_READY" if failures == 0 else "SANDBOX_CATALOG_INSPECTION_REVIEW"

    write_csv(out / "dd042_sandbox_catalog_inspection_ledger.csv", table_rows,
              ["table", "dbf_exists", "dbt_exists", "expected_rows", "readback_rows", "expected_fields",
               "readback_fields", "has_memo", "status", "pass"])

    sample_fields = sorted({k for r in sample_rows for k in r.keys()})
    write_csv(out / "dd042_sample_rows.csv", sample_rows, sample_fields or ["table", "RECNO", "DELETED"])
    write_csv(out / "dd042_no_mutation_boundary_ledger.csv", boundary_rows,
              ["boundary", "observed", "required", "pass"])

    manifest = {
        "contract": "dd042_sandbox_catalog_dbf_inspection_x64base_readback_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "sandbox_path": str(sandbox),
        "dd041_dir": str(dd041_dir),
        "profiles": args.profile,
        "tables_inspected": len(table_rows),
        "inspection_failures": failures,
        "dbf_rows_written": 0,
        "cdx_created": 0,
        "lmdb_written": 0,
        "runtime_launch": 0,
        "active_catalog_promotion": 0,
        "protected_system_mutations": 0,
        "generated_probe_artifacts": [
            "dd042_pydottalk_readback_probe.py",
            "dd042_dottalk_readback_probe_template.dts",
        ],
        "next_recommended_package": "DD-043 pydottalk/DotTalk++ runtime readback execution, only after explicit runtime-read authorization",
    }
    write_json(out / "dd042_sandbox_catalog_inspection_manifest.json", manifest)

    report = f"""# DD-042 Sandbox Catalog DBF Inspection / x64base Readback Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Sandbox path

```text
{safe_rel(repo, sandbox)}
```

## Inspection

- Tables inspected: {len(table_rows)}
- Inspection failures: {failures}
- DBF rows written by DD-042: 0
- Runtime launched by DD-042: 0

## Generated readback probe artifacts

```text
dd042_pydottalk_readback_probe.py
dd042_dottalk_readback_probe_template.dts
```

These are generated for review and later execution. DD-042 itself does not launch DotTalk++ or pydottalk runtime readback.

## Boundary

DD-042 is read-only. It does not write DBFs, create CDX files, write LMDB data,
launch DotTalk++, mutate HELP/META/CMDHELPCHK, edit source, or promote the catalog.

## Next

DD-043 may execute pydottalk/DotTalk++ runtime readback only after explicit runtime-read authorization.
"""
    (out / "DD042_SANDBOX_CATALOG_INSPECTION_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-042 sandbox catalog inspection manifest: {out / 'dd042_sandbox_catalog_inspection_manifest.json'}")
    print(f"status: {status}; tables_inspected: {len(table_rows)}; inspection_failures: {failures}; runtime_launch: 0")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
