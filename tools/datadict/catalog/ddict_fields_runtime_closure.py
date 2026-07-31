#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD073_STATUS = "DDICT_FIELDS_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"
TABLES = ["DDOBJECT", "DDATTR", "DDEDGE"]
EXPECTED_COUNTS = {"DDOBJECT": 7, "DDATTR": 6, "DDEDGE": 5}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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


def classify_runtime(text: str) -> Dict[str, Any]:
    upper = text.upper()
    result: Dict[str, Any] = {}
    for table in TABLES:
        result[f"has_fields_{table.lower()}"] = int(f"DDICT FIELDS {table}" in upper)
        result[f"has_{table.lower()}_count"] = int(f"FIELD ROWS    : {EXPECTED_COUNTS[table]}" in upper or f"FIELD ROWS: {EXPECTED_COUNTS[table]}" in upper)
    result["has_read_only"] = int("READ-ONLY" in upper)
    result["has_active_catalog"] = int("ACTIVE CATALOG:" in upper and "DATADICT" in upper)
    result["has_ddobject_field_objid"] = int("OBJID" in upper and "OBJ_018C4A8AB6B109E2E0A0" in upper)
    result["has_ddattr_field_attrname"] = int("ATTRNAME" in upper)
    result["has_ddedge_field_fromobj"] = int("FROMOBJ" in upper)
    result["tags_pending_preserved"] = int("DDICT TAGS" in upper and "PENDING" in upper)
    result["has_unknown_command_for_ddict"] = int("UNKNOWN COMMAND" in upper and "DDICT" in upper)
    result["fields_surface_green"] = int(
        all(result[f"has_fields_{table.lower()}"] for table in TABLES)
        and all(result[f"has_{table.lower()}_count"] for table in TABLES)
        and result["has_read_only"]
        and result["has_active_catalog"]
        and result["tags_pending_preserved"]
        and not result["has_unknown_command_for_ddict"]
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-073 DDICT FIELDS runtime closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD073-fields-runtime-closure-v0")
    ap.add_argument("--dd073-dir", default="docs/datadict/reports/DD073-guarded-ddict-fields-implementation-apply-v0")
    ap.add_argument("--runtime-proof", required=True)
    ap.add_argument("--exe-path", default="build/src/Release/dottalkpp.exe")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-073_DDICT_FIELDS_RUNTIME_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd073_dir = (repo / args.dd073_dir).resolve()
    dd073_manifest = read_json(dd073_dir / "dd073_guarded_ddict_fields_impl_manifest.json")
    proof_path = (repo / args.runtime_proof).resolve()
    exe_path = (repo / args.exe_path).resolve()
    closure_path = (repo / args.closure_path).resolve()

    proof_text = read_text(proof_path)
    classified = classify_runtime(proof_text)
    exe_exists = int(exe_path.exists())
    exe_bytes = exe_path.stat().st_size if exe_path.exists() else 0
    proof_exists = int(proof_path.exists())
    dd073_ok = int(dd073_manifest.get("status") == EXPECTED_DD073_STATUS)

    gate_rows = [
        {"gate": "dd073_source_patch_applied", "expected": EXPECTED_DD073_STATUS, "observed": dd073_manifest.get("status", ""), "pass": dd073_ok},
        {"gate": "dottalkpp_exe_exists", "expected": 1, "observed": exe_exists, "pass": exe_exists},
        {"gate": "dottalkpp_exe_nonempty", "expected": 1, "observed": int(exe_bytes > 0), "pass": int(exe_bytes > 0)},
        {"gate": "runtime_proof_exists", "expected": 1, "observed": proof_exists, "pass": proof_exists},
        {"gate": "ddict_fields_ddobject_seen", "expected": 1, "observed": classified["has_fields_ddobject"], "pass": classified["has_fields_ddobject"]},
        {"gate": "ddobject_field_count_7_seen", "expected": 1, "observed": classified["has_ddobject_count"], "pass": classified["has_ddobject_count"]},
        {"gate": "ddict_fields_ddattr_seen", "expected": 1, "observed": classified["has_fields_ddattr"], "pass": classified["has_fields_ddattr"]},
        {"gate": "ddattr_field_count_6_seen", "expected": 1, "observed": classified["has_ddattr_count"], "pass": classified["has_ddattr_count"]},
        {"gate": "ddict_fields_ddedge_seen", "expected": 1, "observed": classified["has_fields_ddedge"], "pass": classified["has_fields_ddedge"]},
        {"gate": "ddedge_field_count_5_seen", "expected": 1, "observed": classified["has_ddedge_count"], "pass": classified["has_ddedge_count"]},
        {"gate": "active_catalog_seen", "expected": 1, "observed": classified["has_active_catalog"], "pass": classified["has_active_catalog"]},
        {"gate": "read_only_seen", "expected": 1, "observed": classified["has_read_only"], "pass": classified["has_read_only"]},
        {"gate": "sample_field_objid_seen", "expected": 1, "observed": classified["has_ddobject_field_objid"], "pass": classified["has_ddobject_field_objid"]},
        {"gate": "sample_field_attrname_seen", "expected": 1, "observed": classified["has_ddattr_field_attrname"], "pass": classified["has_ddattr_field_attrname"]},
        {"gate": "sample_field_fromobj_seen", "expected": 1, "observed": classified["has_ddedge_field_fromobj"], "pass": classified["has_ddedge_field_fromobj"]},
        {"gate": "tags_pending_preserved", "expected": 1, "observed": classified["tags_pending_preserved"], "pass": classified["tags_pending_preserved"]},
        {"gate": "no_unknown_command_for_ddict", "expected": 0, "observed": classified["has_unknown_command_for_ddict"], "pass": int(classified["has_unknown_command_for_ddict"] == 0)},
    ]

    boundary_rows = [
        {"boundary": "runtime_closure_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]

    table_rows = [
        {"table": "DDOBJECT", "expected_fields": 7, "seen_command": classified["has_fields_ddobject"], "seen_count": classified["has_ddobject_count"]},
        {"table": "DDATTR", "expected_fields": 6, "seen_command": classified["has_fields_ddattr"], "seen_count": classified["has_ddattr_count"]},
        {"table": "DDEDGE", "expected_fields": 5, "seen_command": classified["has_fields_ddedge"], "seen_count": classified["has_ddedge_count"]},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_FIELDS_RUNTIME_CLOSURE_GREEN" if failures == 0 else "DDICT_FIELDS_RUNTIME_CLOSURE_REVIEW"

    write_csv(out / "dd073_fields_runtime_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd073_fields_table_runtime_ledger.csv", table_rows, ["table", "expected_fields", "seen_command", "seen_count"])
    write_csv(out / "dd073_fields_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-073 DDICT FIELDS Runtime Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-073 closes the guarded `DDICT FIELDS <table>` runtime milestone.

## Evidence

- DD-073 apply status: `{dd073_manifest.get('status', '')}`
- Runtime proof: `{rel(repo, proof_path)}`
- Executable: `{rel(repo, exe_path)}`
- Executable exists: **{exe_exists}**
- Executable bytes: **{exe_bytes}**

## Runtime classification

- DDICT FIELDS DDOBJECT seen: **{classified['has_fields_ddobject']}**
- DDOBJECT field rows 7 seen: **{classified['has_ddobject_count']}**
- DDICT FIELDS DDATTR seen: **{classified['has_fields_ddattr']}**
- DDATTR field rows 6 seen: **{classified['has_ddattr_count']}**
- DDICT FIELDS DDEDGE seen: **{classified['has_fields_ddedge']}**
- DDEDGE field rows 5 seen: **{classified['has_ddedge_count']}**
- READ-ONLY seen: **{classified['has_read_only']}**
- TAGS pending preserved: **{classified['tags_pending_preserved']}**

## Boundary

DD-073 closure is readback only. It does not edit C++ source, edit registry/build files,
mutate active catalog data, append/replace/delete/pack/zap DBFs, rebuild CDX/LMDB,
or mutate HELP/META/CMDHELPCHK.
"""
    (out / "DD073_DDICT_FIELDS_RUNTIME_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    closure_written = 0
    if args.write_closure:
        closure_path.parent.mkdir(parents=True, exist_ok=True)
        closure_path.write_text(report, encoding="utf-8")
        closure_written = 1

    manifest = {
        "contract": "dd073_fields_runtime_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd073_status": dd073_manifest.get("status", ""),
        "runtime_proof": rel(repo, proof_path),
        "exe_exists": exe_exists,
        "exe_bytes": exe_bytes,
        "fields_surface_green": classified["fields_surface_green"],
        "closure_written": closure_written,
        "closure_path": str(closure_path) if closure_written else "",
        "failures": failures,
        "cxx_source_edits": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "DD-074 plan/implementation for guarded DDICT TAGS read surface.",
    }
    write_json(out / "dd073_fields_runtime_closure_manifest.json", manifest)

    print(f"DD-073 FIELDS runtime closure manifest: {out / 'dd073_fields_runtime_closure_manifest.json'}")
    print(f"status: {status}; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
