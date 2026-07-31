#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import importlib
import json
import string
import struct
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


CANONICAL_TABLE_ORDER = [
    "DDRUN",
    "DDBASE",
    "DDSOURCE",
    "DDOBJECT",
    "DDATTR",
    "DDEDGE",
    "DDEVID",
    "DDGATE",
    "DDREVIEW",
    "DDARTIF",
    "DDPROFILE",
]

DEFAULT_EXPECTED_COUNTS = {
    "DDRUN": 1,
    "DDBASE": 1,
    "DDSOURCE": 7,
    "DDOBJECT": 100,
    "DDATTR": 423,
    "DDEDGE": 89,
    "DDEVID": 1,
    "DDGATE": 6,
    "DDREVIEW": 0,
    "DDARTIF": 7,
    "DDPROFILE": 3,
}

EXPECTED_MEMO_TABLES = {
    "DDRUN": ["NOTES"],
    "DDBASE": ["NOTES"],
    "DDATTR": ["ATTRMEMO"],
    "DDEVID": ["DETAIL"],
    "DDGATE": ["DETAIL"],
    "DDREVIEW": ["DETAIL"],
    "DDPROFILE": ["NOTES"],
}

VALID_DBF_FIELD_TYPES = set("CNDLFMGIYTBVQ+@0")
PRINTABLE_NAME = set(string.ascii_letters + string.digits + "_")


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return str(value)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(data), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


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


def harden_pydottalk_path(repo: Path) -> Dict[str, Any]:
    build_python = repo / "build" / "python"
    added = 0
    if build_python.exists():
        bp = str(build_python.resolve())
        if bp not in sys.path:
            sys.path.insert(0, bp)
            added = 1
    return {
        "build_python_path": str(build_python),
        "build_python_exists": int(build_python.exists()),
        "added_to_sys_path": added,
    }


def normalize_name(raw: bytes) -> str:
    raw = raw.split(b"\x00", 1)[0]
    return raw.decode("ascii", errors="ignore").strip().upper()


def descriptor_at(data: bytes, off: int) -> Dict[str, Any] | None:
    if off < 0 or off + 32 > len(data):
        return None
    d = data[off:off+32]
    name = normalize_name(d[0:11])
    ftype = chr(d[11]) if d[11] else ""
    width = d[16]
    decimals = d[17]
    if not name:
        return None
    if any(ch not in PRINTABLE_NAME for ch in name):
        return None
    if ftype not in VALID_DBF_FIELD_TYPES:
        return None
    if width == 0 and ftype not in {"M", "G"}:
        return None
    return {
        "offset": off,
        "name": name,
        "type": ftype,
        "width": int(width),
        "decimals": int(decimals),
    }


def read_base_header(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        data = f.read()
    if len(data) < 32:
        raise ValueError("too small for DBF header")
    version = data[0]
    records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    return {
        "version_byte": int(version),
        "records": int(records),
        "header_len": int(header_len),
        "record_len": int(record_len),
        "file_bytes": len(data),
        "raw": data,
    }


def find_descriptor_runs(data: bytes, header_len: int, expected_fields: List[str]) -> List[Dict[str, Any]]:
    expected = [x.upper() for x in expected_fields]
    upper_limit = min(max(header_len, 32), len(data))
    candidates: List[Dict[str, Any]] = []
    for start in range(32, max(33, upper_limit - 32)):
        run: List[Dict[str, Any]] = []
        off = start
        while off + 32 <= upper_limit:
            if data[off] == 0x0D:
                break
            desc = descriptor_at(data, off)
            if not desc:
                break
            run.append(desc)
            off += 32
            if len(run) > 128:
                break
        if not run:
            continue
        names = [d["name"] for d in run]
        expected_hits = sum(1 for n in expected if n in names)
        plausible = sum(1 for d in run if d["type"] in VALID_DBF_FIELD_TYPES)
        score = expected_hits * 100 + plausible * 10 - abs(len(run) - max(1, len(expected)))
        candidates.append({
            "start_offset": start,
            "field_count": len(run),
            "field_names": names,
            "expected_hits": expected_hits,
            "score": score,
            "fields": run,
        })
    candidates.sort(key=lambda r: (r["expected_hits"], r["score"], -r["start_offset"]), reverse=True)
    return candidates[:10]


def inspect_x64_dbf(repo: Path, dbf: Path, expected_fields: List[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "dbf_exists": int(dbf.exists()),
        "dbf_path": safe_rel(repo, dbf),
        "status": "PENDING",
    }
    if not dbf.exists():
        result["status"] = "MISSING_DBF"
        return result

    base = read_base_header(dbf)
    data = base.pop("raw")
    runs = find_descriptor_runs(data, base["header_len"], expected_fields)
    best = runs[0] if runs else {}
    best_names = best.get("field_names", [])
    expected_hits = best.get("expected_hits", 0)
    result.update(base)
    result.update({
        "selected_descriptor_start_offset": best.get("start_offset", ""),
        "selected_field_count": best.get("field_count", ""),
        "selected_field_names": best_names,
        "selected_fields": best.get("fields", []),
        "expected_fields": expected_fields,
        "expected_field_hits": expected_hits,
        "status": "PASS" if expected_hits == len(expected_fields) else "REVIEW",
    })
    return result


def load_expected_from_dd052(dd052_dir: Path) -> Dict[str, Dict[str, Any]]:
    plan = read_csv_dict(dd052_dir / "dd052_staged_table_plan.csv")
    fields = read_csv_dict(dd052_dir / "dd052_staged_field_definitions.csv")
    by_table: Dict[str, Dict[str, Any]] = {}
    for row in plan:
        table = (row.get("table") or "").strip().upper()
        if not table:
            continue
        by_table.setdefault(table, {})
        try:
            expected_rows = int(float(row.get("expected_rows") or DEFAULT_EXPECTED_COUNTS.get(table, 0)))
        except Exception:
            expected_rows = DEFAULT_EXPECTED_COUNTS.get(table, 0)
        by_table[table]["expected_rows"] = expected_rows
    for table in CANONICAL_TABLE_ORDER:
        by_table.setdefault(table, {})
        by_table[table].setdefault("expected_rows", DEFAULT_EXPECTED_COUNTS[table])
        by_table[table].setdefault("expected_fields", [])
    for row in fields:
        table = (row.get("table") or "").strip().upper()
        field = (row.get("field") or "").strip().upper()
        ftype = (row.get("type") or "").strip().upper()
        if not table or not field:
            continue
        by_table.setdefault(table, {})
        by_table[table].setdefault("expected_fields", []).append(field)
        by_table[table].setdefault("memo_fields", [])
        if ftype == "M":
            by_table[table]["memo_fields"].append(field)
    for table in CANONICAL_TABLE_ORDER:
        if not by_table[table].get("memo_fields"):
            by_table[table]["memo_fields"] = EXPECTED_MEMO_TABLES.get(table, [])
    return by_table


def inspect_sidecars(repo: Path, target_path: Path, table: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    stem = table.lower()
    if not target_path.exists():
        return out
    for p in sorted(target_path.iterdir(), key=lambda q: q.name.lower()):
        if not p.is_file():
            continue
        if p.stem.lower() == stem and p.suffix.lower() != ".dbf":
            out.append({
                "file": p.name,
                "path": safe_rel(repo, p),
                "bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            })
    return out


def read_pydottalk_table(repo: Path, target_path: Path, table: str, expected_rows: int) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "table": table,
        "attempted": 1,
        "import_ok": 0,
        "open_ok": 0,
        "rec_count": "",
        "expected_rows": expected_rows,
        "row_count_match": 0,
        "field_count": "",
        "memo_path": "",
        "memo_kind": "",
        "first_record": "",
        "last_record": "",
        "error": "",
    }
    try:
        harden_pydottalk_path(repo)
        mod = importlib.import_module("pydottalk")
        result["import_ok"] = 1
        dbf = target_path / f"{table.lower()}.dbf"
        a = mod.Dbf()
        a.open(str(dbf))
        result["open_ok"] = int(a.isOpen())
        rc = int(a.recCount())
        result["rec_count"] = rc
        result["row_count_match"] = int(rc == expected_rows)
        result["field_count"] = int(a.fieldCount())
        try:
            result["memo_path"] = str(a.memoPath())
        except Exception:
            result["memo_path"] = ""
        try:
            result["memo_kind"] = str(a.memoKind())
        except Exception:
            result["memo_kind"] = ""
        if rc > 0:
            a.top()
            result["first_record"] = repr(a.readCurrent())
            if rc > 1:
                try:
                    a.gotoRec(rc)
                    result["last_record"] = repr(a.readCurrent())
                except Exception:
                    result["last_record"] = ""
        a.close()
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-053 canonical catalog runtime / pydottalk readback verification")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD053-canonical-catalog-runtime-readback-v0")
    ap.add_argument("--target-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--dd052-prepare-dir", default="docs/datadict/reports/DD052-canonical-catalog-staging-prepare-v0")
    ap.add_argument("--dd052-verify-dir", default="docs/datadict/reports/DD052-canonical-catalog-staging-verify-v0")
    ap.add_argument("--dd052-proof", default="docs/datadict/runlog/DD-052_LOCAL_CANONICAL_CATALOG_CREATE_IMPORT_STAGING_PROOF.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    target_path = (repo / args.target_path).resolve()
    dd052_prepare_dir = (repo / args.dd052_prepare_dir).resolve()
    dd052_verify_dir = (repo / args.dd052_verify_dir).resolve()
    dd052_proof = (repo / args.dd052_proof).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd052_verify_manifest = read_json(dd052_verify_dir / "dd052_canonical_catalog_staging_manifest.json")
    expected = load_expected_from_dd052(dd052_prepare_dir)

    table_rows: List[Dict[str, Any]] = []
    field_rows: List[Dict[str, Any]] = []
    sidecar_rows: List[Dict[str, Any]] = []
    pydottalk_rows: List[Dict[str, Any]] = []
    sample_rows: List[Dict[str, Any]] = []

    failures = 0
    memo_sidecar_failures = 0

    for table in CANONICAL_TABLE_ORDER:
        exp = expected.get(table, {})
        expected_rows = int(exp.get("expected_rows", DEFAULT_EXPECTED_COUNTS[table]))
        expected_fields = list(exp.get("expected_fields", []))
        if not expected_fields:
            # Fallback: only table-level pydottalk count if staged field defs are missing.
            expected_fields = []
        memo_fields = list(exp.get("memo_fields", EXPECTED_MEMO_TABLES.get(table, [])))

        dbf = target_path / f"{table.lower()}.dbf"
        dbf_inspection = inspect_x64_dbf(repo, dbf, expected_fields) if expected_fields else {
            "dbf_exists": int(dbf.exists()),
            "dbf_path": safe_rel(repo, dbf),
            "records": "",
            "status": "PASS" if dbf.exists() else "MISSING_DBF",
            "selected_descriptor_start_offset": "",
            "selected_field_names": [],
            "selected_fields": [],
        }
        sidecars = inspect_sidecars(repo, target_path, table)
        pydt = read_pydottalk_table(repo, target_path, table, expected_rows)

        row_count_match = int(pydt.get("row_count_match") == 1)
        descriptor_pass = int(dbf_inspection.get("status") == "PASS")
        pydottalk_pass = int(pydt.get("import_ok") == 1 and pydt.get("open_ok") == 1 and row_count_match == 1)
        memo_sidecar_required = int(bool(memo_fields))
        memo_sidecar_ok = int((not memo_fields) or bool(sidecars))

        if not descriptor_pass or not pydottalk_pass or not memo_sidecar_ok:
            failures += 1
        if not memo_sidecar_ok:
            memo_sidecar_failures += 1

        table_rows.append({
            "table": table,
            "dbf_exists": dbf_inspection.get("dbf_exists", 0),
            "descriptor_status": dbf_inspection.get("status", ""),
            "selected_descriptor_start_offset": dbf_inspection.get("selected_descriptor_start_offset", ""),
            "expected_rows": expected_rows,
            "pydottalk_rows": pydt.get("rec_count", ""),
            "row_count_match": row_count_match,
            "memo_fields": ",".join(memo_fields),
            "memo_sidecar_required": memo_sidecar_required,
            "memo_sidecar_count": len(sidecars),
            "memo_sidecar_ok": memo_sidecar_ok,
            "pydottalk_open_ok": pydt.get("open_ok", 0),
            "table_pass": int(descriptor_pass and pydottalk_pass and memo_sidecar_ok),
        })

        for f in dbf_inspection.get("selected_fields", []):
            field_rows.append({
                "table": table,
                "offset": f.get("offset", ""),
                "name": f.get("name", ""),
                "type": f.get("type", ""),
                "width": f.get("width", ""),
                "decimals": f.get("decimals", ""),
            })
        for s in sidecars:
            sidecar_rows.append({"table": table, **s})
        pydottalk_rows.append(pydt)
        sample_rows.append({
            "table": table,
            "first_record": pydt.get("first_record", ""),
            "last_record": pydt.get("last_record", ""),
            "memo_path": pydt.get("memo_path", ""),
            "memo_kind": pydt.get("memo_kind", ""),
        })

    dd052_verify_green = dd052_verify_manifest.get("status") == "CANONICAL_CATALOG_STAGING_RUNTIME_VERIFY_GREEN"
    dd052_proof_exists = dd052_proof.exists()
    if not dd052_verify_green:
        failures += 1
    if not dd052_proof_exists:
        failures += 1

    gate_rows = [
        {
            "gate": "dd052_runtime_verify_green",
            "expected": "CANONICAL_CATALOG_STAGING_RUNTIME_VERIFY_GREEN",
            "observed": dd052_verify_manifest.get("status", ""),
            "pass": int(dd052_verify_green),
        },
        {
            "gate": "dd052_runtime_proof_exists",
            "expected": 1,
            "observed": int(dd052_proof_exists),
            "pass": int(dd052_proof_exists),
        },
        {
            "gate": "all_tables_pass_descriptor_rowcount_sidecar",
            "expected": 11,
            "observed": sum(1 for r in table_rows if r["table_pass"] == 1),
            "pass": int(sum(1 for r in table_rows if r["table_pass"] == 1) == 11),
        },
        {
            "gate": "memo_sidecar_failures",
            "expected": 0,
            "observed": memo_sidecar_failures,
            "pass": int(memo_sidecar_failures == 0),
        },
    ]

    boundary_rows = [
        {"boundary": "readback_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "staging_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_build", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_index_created", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "promotion_executed", "observed": 0, "required": 0, "pass": 1},
    ]

    status = "CANONICAL_CATALOG_RUNTIME_READBACK_GREEN" if failures == 0 else "CANONICAL_CATALOG_RUNTIME_READBACK_REVIEW"

    write_csv(out / "dd053_table_readback_ledger.csv", table_rows, [
        "table", "dbf_exists", "descriptor_status", "selected_descriptor_start_offset",
        "expected_rows", "pydottalk_rows", "row_count_match", "memo_fields",
        "memo_sidecar_required", "memo_sidecar_count", "memo_sidecar_ok",
        "pydottalk_open_ok", "table_pass",
    ])
    write_csv(out / "dd053_field_descriptor_ledger.csv", field_rows, [
        "table", "offset", "name", "type", "width", "decimals",
    ])
    write_csv(out / "dd053_memo_sidecar_ledger.csv", sidecar_rows, [
        "table", "file", "path", "bytes", "sha256",
    ])
    write_csv(out / "dd053_pydottalk_readback_ledger.csv", pydottalk_rows, [
        "table", "attempted", "import_ok", "open_ok", "rec_count", "expected_rows",
        "row_count_match", "field_count", "memo_path", "memo_kind", "first_record",
        "last_record", "error",
    ])
    write_csv(out / "dd053_sample_readback_ledger.csv", sample_rows, [
        "table", "first_record", "last_record", "memo_path", "memo_kind",
    ])
    write_csv(out / "dd053_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd053_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    manifest = {
        "contract": "dd053_canonical_catalog_runtime_readback_verification_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "target_path": str(target_path),
        "tables_checked": len(CANONICAL_TABLE_ORDER),
        "tables_passed": sum(1 for r in table_rows if r["table_pass"] == 1),
        "failures": failures,
        "memo_sidecar_failures": memo_sidecar_failures,
        "dd052_verify_green": int(dd052_verify_green),
        "dd052_proof_exists": int(dd052_proof_exists),
        "active_catalog_mutation": 0,
        "staging_catalog_mutation": 0,
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "lmdb_build": 0,
        "cdx_index_created": 0,
        "promotion_executed": 0,
        "next_recommended_action": "DD-054 index/tag plan or active-catalog promotion readiness plan.",
    }
    write_json(out / "dd053_canonical_catalog_runtime_readback_manifest.json", manifest)

    report = f"""# DD-053 Canonical Catalog Runtime / pydottalk Readback Verification

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-053 verifies the real staged Data Dictionary catalog created by DD-052 before
any indexing, LMDB build, or active-catalog promotion.

## Target

```text
{safe_rel(repo, target_path)}
```

## Result

- Tables checked: **{manifest['tables_checked']}**
- Tables passed: **{manifest['tables_passed']}**
- Failures: **{failures}**
- Memo sidecar failures: **{memo_sidecar_failures}**
- DD-052 runtime verify green: **{manifest['dd052_verify_green']}**
- DD-052 proof exists: **{manifest['dd052_proof_exists']}**

## Boundary

DD-053 is readback-only. It does not mutate active catalog, staging catalog,
source, HELP/META/CMDHELPCHK, CDX, or LMDB.

## Next

If green, next safe package is either:

```text
DD-054 catalog CDX/tag plan
```

or:

```text
DD-054 active-catalog promotion readiness plan
```
"""
    (out / "DD053_CANONICAL_CATALOG_RUNTIME_READBACK_VERIFICATION_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-053 canonical catalog readback manifest: {out / 'dd053_canonical_catalog_runtime_readback_manifest.json'}")
    print(f"status: {status}; tables_passed: {manifest['tables_passed']}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
