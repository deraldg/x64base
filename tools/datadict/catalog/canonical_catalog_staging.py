#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple


MEMO_NAME_HINTS = ("memo", "text", "body", "detail", "description", "message", "report", "json", "payload", "content", "notes")
MAX_C_WIDTH = 240


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def find_manifest(run_dir: Path, name: str) -> Path:
    exact = run_dir / name
    if exact.exists():
        return exact
    matches = [p for p in run_dir.rglob(name) if p.is_file()] if run_dir.exists() else []
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else exact


def sanitize_field_name(raw: str, used: set[str]) -> str:
    s = (raw or "").strip()
    s = re.sub(r"[^A-Za-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        s = "FIELD"
    if s[0].isdigit():
        s = "F_" + s
    s = s.upper()
    base = s
    n = 2
    while s in used:
        s = f"{base}_{n}"
        n += 1
    used.add(s)
    return s


def infer_field_type(name: str, values: List[str]) -> Tuple[str, int]:
    max_len = max([len(v or "") for v in values] + [1])
    lname = name.lower()
    if max_len > MAX_C_WIDTH or any(h in lname for h in MEMO_NAME_HINTS):
        return "M", 0
    return "C", max(1, min(MAX_C_WIDTH, max(max_len, len(name), 8)))


def load_table_plan(dd051_dir: Path) -> List[Dict[str, str]]:
    path = dd051_dir / "dd051_canonical_table_build_plan.csv"
    rows = read_csv_dict(path)
    if not rows:
        raise SystemExit(f"DD-051 table build plan not found or empty: {path}")
    return rows


def analyze_projection_candidate(table: str, candidate: str, expected_rows: int) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "table": table,
        "candidate": candidate,
        "candidate_exists": 0,
        "headers": [],
        "data_rows": 0,
        "expected_rows": expected_rows,
        "row_count_match": 0,
        "looks_like_ledger": 0,
        "status": "PENDING",
        "error": "",
    }

    if not candidate:
        result["status"] = "MISSING_CANDIDATE"
        result["error"] = "projection_csv_candidate is blank"
        return result

    path = Path(candidate)
    if not path.exists():
        result["status"] = "MISSING_CANDIDATE"
        result["error"] = f"candidate does not exist: {candidate}"
        return result

    result["candidate_exists"] = 1
    try:
        with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                headers = []
            rows = list(reader)
    except Exception as exc:
        result["status"] = "READ_ERROR"
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    headers_norm = [h.strip() for h in headers]
    result["headers"] = headers_norm
    result["data_rows"] = len(rows)
    result["row_count_match"] = int(len(rows) == expected_rows)

    ledger_headers = {"table", "rows", "gate", "expected", "observed", "pass", "boundary", "status"}
    header_set = {h.lower() for h in headers_norm}
    if len(header_set & ledger_headers) >= 2 and table.upper() not in header_set:
        result["looks_like_ledger"] = 1

    if not headers_norm:
        result["status"] = "NO_HEADERS"
    elif result["looks_like_ledger"]:
        result["status"] = "REVIEW_LEDGER_LIKE_CSV"
    elif not result["row_count_match"]:
        result["status"] = "ROW_COUNT_MISMATCH"
    else:
        result["status"] = "PASS"
    return result


def stage_table_csv(table: str, source_csv: Path, dest_csv: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    with source_csv.open("r", newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        original_headers = list(reader.fieldnames or [])
        raw_rows = list(reader)

    used: set[str] = set()
    mapping: List[Dict[str, Any]] = []
    sanitized_headers: List[str] = []
    for h in original_headers:
        sh = sanitize_field_name(h, used)
        sanitized_headers.append(sh)
        mapping.append({
            "table": table,
            "original_header": h,
            "staged_header": sh,
        })

    staged_rows: List[Dict[str, Any]] = []
    for raw in raw_rows:
        row: Dict[str, Any] = {}
        for old, new in zip(original_headers, sanitized_headers):
            row[new] = raw.get(old, "")
        staged_rows.append(row)

    write_csv(dest_csv, staged_rows, sanitized_headers)

    field_defs: List[Dict[str, Any]] = []
    for h in sanitized_headers:
        values = [str(row.get(h, "")) for row in staged_rows]
        ftype, width = infer_field_type(h, values)
        field_defs.append({
            "table": table,
            "field": h,
            "type": ftype,
            "width": width,
            "create_fragment": f"{h} {ftype}" if ftype == "M" else f"{h} C({width})",
        })

    return mapping, field_defs, sanitized_headers


def build_create_command(table: str, field_defs: List[Dict[str, Any]]) -> str:
    fragments = [str(f["create_fragment"]) for f in field_defs]
    return f"create x64 {table.lower()} (" + ", ".join(fragments) + ")"


def ensure_safe_target(repo: Path, target_path: Path, active_path: Path) -> None:
    target_resolved = target_path.resolve()
    active_resolved = active_path.resolve()
    try:
        target_rel = target_resolved.relative_to(repo.resolve()).as_posix().lower()
    except Exception:
        raise SystemExit(f"Target path must be inside repo: {target_path}")

    if target_resolved == active_resolved:
        raise SystemExit("Refusing to use active catalog path as DD-052 staging target")

    if "datadict_canonical_rebuild_v0" not in target_rel:
        raise SystemExit(f"Refusing target path without datadict_canonical_rebuild_v0 safety marker: {target_rel}")


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-052 guarded canonical catalog CREATE X64 / IMPORT staging")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD052-canonical-catalog-create-import-staging-v0")
    ap.add_argument("--dd051-dir", default="docs/datadict/reports/DD051-canonical-catalog-rebuild-plan-v0")
    ap.add_argument("--target-slot", default="metadata\\datadict_canonical_rebuild_v0")
    ap.add_argument("--target-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--prepare-staging", action="store_true", help="Create staging import CSVs and DotTalk++ command script")
    ap.add_argument("--replace-target", action="store_true", help="Delete existing DD-052 target staging path before preparing")
    ap.add_argument("--verify-after-runtime", action="store_true", help="Verify target DBFs after manual/runtime CREATE+IMPORT execution")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd051_dir = (repo / args.dd051_dir).resolve()
    target_path = (repo / args.target_path).resolve()
    active_path = (repo / args.active_path).resolve()
    imports_dir = target_path / "_dd052_imports"
    out.mkdir(parents=True, exist_ok=True)

    ensure_safe_target(repo, target_path, active_path)

    dd051_manifest = read_json(find_manifest(dd051_dir, "dd051_canonical_catalog_rebuild_plan_manifest.json"))
    table_plan = load_table_plan(dd051_dir)

    candidate_rows: List[Dict[str, Any]] = []
    failures = 0
    for row in table_plan:
        table = (row.get("table") or "").strip().upper()
        expected_rows = int(float(row.get("projected_rows") or 0))
        candidate = row.get("projection_csv_candidate") or ""
        analysis = analyze_projection_candidate(table, candidate, expected_rows)
        candidate_rows.append(analysis)
        if analysis.get("status") != "PASS":
            failures += 1

    preflight_green = failures == 0 and dd051_manifest.get("status") == "CANONICAL_CATALOG_REBUILD_PLAN_READY"

    staged_mapping_rows: List[Dict[str, Any]] = []
    staged_field_rows: List[Dict[str, Any]] = []
    staged_table_rows: List[Dict[str, Any]] = []
    dts_lines: List[str] = []

    if args.prepare_staging and preflight_green:
        if target_path.exists() and args.replace_target:
            shutil.rmtree(target_path)
        target_path.mkdir(parents=True, exist_ok=True)
        imports_dir.mkdir(parents=True, exist_ok=True)

        dts_lines.extend([
            "* DD-052 canonical catalog CREATE X64 / IMPORT staging script",
            "* Generated by guarded DD-052 package.",
            "* Target is staging only; do not promote active catalog from this script.",
            f"setpath dbf {args.target_slot}",
            "",
        ])

        for row in table_plan:
            table = (row.get("table") or "").strip().upper()
            src = Path(row.get("projection_csv_candidate") or "")
            staged_csv = imports_dir / f"{table.lower()}_import.csv"
            mapping, field_defs, headers = stage_table_csv(table, src, staged_csv)
            staged_mapping_rows.extend(mapping)
            staged_field_rows.extend(field_defs)
            create_cmd = build_create_command(table, field_defs)

            dts_lines.append(f"* ---- {table} ----")
            dts_lines.append(create_cmd)
            dts_lines.append(f"import {staged_csv}")
            dts_lines.append("count")
            dts_lines.append("")

            staged_table_rows.append({
                "table": table,
                "staged_csv": str(staged_csv),
                "expected_rows": row.get("projected_rows") or "0",
                "field_count": len(headers),
                "create_command": create_cmd,
            })

        (target_path / "dd052_create_import_catalog.dts").write_text("\n".join(dts_lines) + "\n", encoding="utf-8")

    elif args.prepare_staging and not preflight_green:
        # Do not write target staging when inputs are suspect.
        pass

    if args.verify_after_runtime:
        # Minimal verification for now: expected DBF files exist. DD-053 can do full pydottalk row checks.
        for row in table_plan:
            table = (row.get("table") or "").strip().upper()
            dbf = target_path / f"{table.lower()}.dbf"
            staged_table_rows.append({
                "table": table,
                "expected_rows": row.get("projected_rows") or "0",
                "dbf_exists": int(dbf.exists()),
                "dbf_path": str(dbf),
            })
            if not dbf.exists():
                failures += 1

    write_csv(out / "dd052_projection_candidate_preflight.csv", candidate_rows, [
        "table", "candidate", "candidate_exists", "headers", "data_rows", "expected_rows",
        "row_count_match", "looks_like_ledger", "status", "error",
    ])
    write_csv(out / "dd052_staged_table_plan.csv", staged_table_rows, [
        "table", "staged_csv", "expected_rows", "field_count", "create_command", "dbf_exists", "dbf_path",
    ])
    write_csv(out / "dd052_staged_field_definitions.csv", staged_field_rows, [
        "table", "field", "type", "width", "create_fragment",
    ])
    write_csv(out / "dd052_header_mapping.csv", staged_mapping_rows, [
        "table", "original_header", "staged_header",
    ])

    boundary_rows = [
        {"boundary": "target_path_safety_marker", "observed": int("datadict_canonical_rebuild_v0" in str(target_path).lower()), "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_build", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_index_created_by_python", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "promotion_executed", "observed": 0, "required": 0, "pass": 1},
    ]
    write_csv(out / "dd052_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    if args.verify_after_runtime:
        status = "CANONICAL_CATALOG_STAGING_RUNTIME_VERIFY_GREEN" if failures == 0 else "CANONICAL_CATALOG_STAGING_RUNTIME_VERIFY_REVIEW"
    elif args.prepare_staging:
        status = "CANONICAL_CATALOG_STAGING_PREPARED" if preflight_green else "CANONICAL_CATALOG_STAGING_PREFLIGHT_REVIEW"
    else:
        status = "CANONICAL_CATALOG_STAGING_PREFLIGHT_GREEN" if preflight_green else "CANONICAL_CATALOG_STAGING_PREFLIGHT_REVIEW"

    manifest = {
        "contract": "dd052_canonical_catalog_create_import_staging_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd051_status": dd051_manifest.get("status", ""),
        "table_count": len(table_plan),
        "candidate_failures": sum(1 for r in candidate_rows if r.get("status") != "PASS"),
        "failures": failures,
        "prepare_staging": int(args.prepare_staging),
        "replace_target": int(args.replace_target),
        "verify_after_runtime": int(args.verify_after_runtime),
        "target_slot": args.target_slot,
        "target_path": str(target_path),
        "imports_dir": str(imports_dir),
        "dottalk_script": str(target_path / "dd052_create_import_catalog.dts"),
        "active_catalog_mutation": 0,
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "lmdb_build": 0,
        "promotion_executed": 0,
        "next_recommended_action": "Run generated DotTalk++ script manually, then DD-052 --verify-after-runtime, then DD-053 pydottalk/readback verification.",
    }
    write_json(out / "dd052_canonical_catalog_staging_manifest.json", manifest)

    report = f"""# DD-052 Canonical Catalog CREATE X64 / IMPORT Staging

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-052 is the first guarded staging package for the real Data Dictionary catalog
build. It stages import-ready CSVs and a DotTalk++ CREATE X64 / IMPORT script
under a rebuild-only target path.

## Target

```text
DBF slot: {args.target_slot}
Path: {safe_rel(repo, target_path)}
Script: {safe_rel(repo, target_path / 'dd052_create_import_catalog.dts')}
```

## Preflight

- DD-051 status: `{dd051_manifest.get('status', '')}`
- Tables: `{len(table_plan)}`
- Candidate failures: `{manifest['candidate_failures']}`

## Boundary

DD-052 does not promote the active catalog, does not build LMDB, does not mutate
HELP/META/CMDHELPCHK, and does not edit source.

## Manual runtime step after staging

Run DotTalk++ and execute the generated script or paste its commands:

```text
do {target_path / 'dd052_create_import_catalog.dts'}
```

If `DO` path handling is awkward, open the `.dts` file and paste commands manually.
"""
    (out / "DD052_CANONICAL_CATALOG_CREATE_IMPORT_STAGING_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-052 canonical catalog staging manifest: {out / 'dd052_canonical_catalog_staging_manifest.json'}")
    print(f"status: {status}; tables: {len(table_plan)}; candidate_failures: {manifest['candidate_failures']}; prepare_staging: {int(args.prepare_staging)}")
    return 2 if (args.fail_on_review and ("REVIEW" in status or failures)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
