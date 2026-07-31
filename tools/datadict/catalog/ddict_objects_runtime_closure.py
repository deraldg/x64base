#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD085_STATUS = "DDICT_OBJECTS_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"


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


def has(upper: str, needle: str) -> int:
    return int(needle.upper() in upper)


def classify_runtime(text: str) -> Dict[str, Any]:
    upper = text.upper()
    return {
        "has_ddict_objects": has(upper, "DDICT OBJECTS\n") or has(upper, ". DDICT OBJECTS\n"),
        "has_ddict_objects_type_catalog_table": has(upper, "DDICT OBJECTS TYPE CATALOG_TABLE"),
        "has_ddict_objects_profile_engine": has(upper, "DDICT OBJECTS PROFILE ENGINE"),
        "has_active_catalog": int("ACTIVE CATALOG:" in upper and "DATADICT" in upper),
        "has_read_only": has(upper, "READ-ONLY"),
        "has_object_rows_100": int("OBJECT ROWS   : 100" in upper or "OBJECT ROWS: 100" in upper),
        "has_object_rows_11": int("OBJECT ROWS   : 11" in upper or "OBJECT ROWS: 11" in upper),
        "has_type_filter_none": has(upper, "TYPE FILTER   : (NONE)"),
        "has_type_filter_catalog_table": has(upper, "TYPE FILTER   : CATALOG_TABLE"),
        "has_profile_filter_none": has(upper, "PROFILE FILTER: (NONE)"),
        "has_profile_filter_engine": has(upper, "PROFILE FILTER: ENGINE"),
        "has_header": int("OBJTYPE" in upper and "OWNER" in upper and "PROFILE" in upper and "ATTRS" in upper),
        "has_catalog_table_ddrun": int("CATALOG_TABLE" in upper and "DDRUN" in upper and "DATADICT_CATALOG" in upper),
        "has_catalog_table_ddprofile": int("CATALOG_TABLE" in upper and "DDPROFILE" in upper),
        "has_catalog_field_runid": int("CATALOG_FIELD" in upper and "RUNID" in upper),
        "has_catalog_tag_runid": int("CATALOG_TAG" in upper and "RUNID" in upper),
        "has_attrs_counts": int("ENGINE        2" in upper and "ENGINE        5" in upper and "ENGINE        3" in upper),
        "has_evidence_ddobject": has(upper, "DDICT EVIDENCE DDOBJECT"),
        "has_evidence_read_only": int("DDICT EVIDENCE DDOBJECT" in upper and "ATTRIBUTE EVIDENCE ROWS: 2" in upper),
        "has_unknown_command_for_ddict": int("UNKNOWN COMMAND" in upper and "DDICT" in upper),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-086 DDICT OBJECTS runtime closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD086-ddict-objects-runtime-closure-v0")
    ap.add_argument("--dd085-dir", default="docs/datadict/reports/DD085-guarded-ddict-objects-implementation-apply-v0")
    ap.add_argument("--runtime-proof", required=True)
    ap.add_argument("--exe-path", default="build/src/Release/dottalkpp.exe")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-086_DDICT_OBJECTS_RUNTIME_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd085_dir = (repo / args.dd085_dir).resolve()
    dd085_manifest = read_json(dd085_dir / "dd085_guarded_ddict_objects_impl_manifest.json")
    proof_path = (repo / args.runtime_proof).resolve()
    exe_path = (repo / args.exe_path).resolve()
    closure_path = (repo / args.closure_path).resolve()

    proof_text = read_text(proof_path)
    classified = classify_runtime(proof_text)
    exe_exists = int(exe_path.exists())
    exe_bytes = exe_path.stat().st_size if exe_path.exists() else 0
    proof_exists = int(proof_path.exists())
    dd085_ok = int(dd085_manifest.get("status") == EXPECTED_DD085_STATUS)

    gate_rows = [
        {"gate": "dd085_source_patch_applied", "expected": EXPECTED_DD085_STATUS, "observed": dd085_manifest.get("status", ""), "pass": dd085_ok},
        {"gate": "dottalkpp_exe_exists", "expected": 1, "observed": exe_exists, "pass": exe_exists},
        {"gate": "dottalkpp_exe_nonempty", "expected": 1, "observed": int(exe_bytes > 0), "pass": int(exe_bytes > 0)},
        {"gate": "runtime_proof_exists", "expected": 1, "observed": proof_exists, "pass": proof_exists},
        {"gate": "ddict_objects_seen", "expected": 1, "observed": classified["has_ddict_objects"], "pass": classified["has_ddict_objects"]},
        {"gate": "ddict_objects_type_catalog_table_seen", "expected": 1, "observed": classified["has_ddict_objects_type_catalog_table"], "pass": classified["has_ddict_objects_type_catalog_table"]},
        {"gate": "ddict_objects_profile_engine_seen", "expected": 1, "observed": classified["has_ddict_objects_profile_engine"], "pass": classified["has_ddict_objects_profile_engine"]},
        {"gate": "active_catalog_seen", "expected": 1, "observed": classified["has_active_catalog"], "pass": classified["has_active_catalog"]},
        {"gate": "read_only_seen", "expected": 1, "observed": classified["has_read_only"], "pass": classified["has_read_only"]},
        {"gate": "object_rows_100_seen", "expected": 1, "observed": classified["has_object_rows_100"], "pass": classified["has_object_rows_100"]},
        {"gate": "object_rows_11_seen", "expected": 1, "observed": classified["has_object_rows_11"], "pass": classified["has_object_rows_11"]},
        {"gate": "type_filter_none_seen", "expected": 1, "observed": classified["has_type_filter_none"], "pass": classified["has_type_filter_none"]},
        {"gate": "type_filter_catalog_table_seen", "expected": 1, "observed": classified["has_type_filter_catalog_table"], "pass": classified["has_type_filter_catalog_table"]},
        {"gate": "profile_filter_none_seen", "expected": 1, "observed": classified["has_profile_filter_none"], "pass": classified["has_profile_filter_none"]},
        {"gate": "profile_filter_engine_seen", "expected": 1, "observed": classified["has_profile_filter_engine"], "pass": classified["has_profile_filter_engine"]},
        {"gate": "objects_header_seen", "expected": 1, "observed": classified["has_header"], "pass": classified["has_header"]},
        {"gate": "catalog_table_ddrun_seen", "expected": 1, "observed": classified["has_catalog_table_ddrun"], "pass": classified["has_catalog_table_ddrun"]},
        {"gate": "catalog_table_ddprofile_seen", "expected": 1, "observed": classified["has_catalog_table_ddprofile"], "pass": classified["has_catalog_table_ddprofile"]},
        {"gate": "catalog_field_runid_seen", "expected": 1, "observed": classified["has_catalog_field_runid"], "pass": classified["has_catalog_field_runid"]},
        {"gate": "catalog_tag_runid_seen", "expected": 1, "observed": classified["has_catalog_tag_runid"], "pass": classified["has_catalog_tag_runid"]},
        {"gate": "attr_counts_seen", "expected": 1, "observed": classified["has_attrs_counts"], "pass": classified["has_attrs_counts"]},
        {"gate": "evidence_ddobject_preserved", "expected": 1, "observed": classified["has_evidence_ddobject"], "pass": classified["has_evidence_ddobject"]},
        {"gate": "evidence_read_only_preserved", "expected": 1, "observed": classified["has_evidence_read_only"], "pass": classified["has_evidence_read_only"]},
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
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    command_rows = [
        {"command": "DDICT OBJECTS", "seen": classified["has_ddict_objects"], "expected_rows": 100, "row_count_seen": classified["has_object_rows_100"], "filter_seen": classified["has_type_filter_none"]},
        {"command": "DDICT OBJECTS TYPE CATALOG_TABLE", "seen": classified["has_ddict_objects_type_catalog_table"], "expected_rows": 11, "row_count_seen": classified["has_object_rows_11"], "filter_seen": classified["has_type_filter_catalog_table"]},
        {"command": "DDICT OBJECTS PROFILE ENGINE", "seen": classified["has_ddict_objects_profile_engine"], "expected_rows": 100, "row_count_seen": classified["has_object_rows_100"], "filter_seen": classified["has_profile_filter_engine"]},
        {"command": "DDICT EVIDENCE DDOBJECT", "seen": classified["has_evidence_ddobject"], "expected_rows": 0, "row_count_seen": classified["has_evidence_read_only"], "filter_seen": 1},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_OBJECTS_RUNTIME_CLOSURE_GREEN" if failures == 0 else "DDICT_OBJECTS_RUNTIME_CLOSURE_REVIEW"

    write_csv(out / "dd086_objects_runtime_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd086_objects_command_runtime_ledger.csv", command_rows, ["command", "seen", "expected_rows", "row_count_seen", "filter_seen"])
    write_csv(out / "dd086_objects_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-086 DDICT OBJECTS Runtime Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-086 closes the guarded `DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]`
runtime milestone.

## Evidence

- DD-085 apply status: `{dd085_manifest.get('status', '')}`
- Runtime proof: `{rel(repo, proof_path)}`
- Executable: `{rel(repo, exe_path)}`
- Executable exists: **{exe_exists}**
- Executable bytes: **{exe_bytes}**

## Runtime classification

- DDICT OBJECTS seen: **{classified['has_ddict_objects']}**
- DDICT OBJECTS TYPE CATALOG_TABLE seen: **{classified['has_ddict_objects_type_catalog_table']}**
- DDICT OBJECTS PROFILE ENGINE seen: **{classified['has_ddict_objects_profile_engine']}**
- Object rows 100 seen: **{classified['has_object_rows_100']}**
- Object rows 11 seen: **{classified['has_object_rows_11']}**
- READ-ONLY seen: **{classified['has_read_only']}**
- EVIDENCE DDOBJECT preserved: **{classified['has_evidence_ddobject']}**

## Boundary

DD-086 closure is readback only. It does not edit C++ source, edit registry/build files,
mutate active catalog data, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB,
mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    (out / "DD086_DDICT_OBJECTS_RUNTIME_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    closure_written = 0
    if args.write_closure:
        closure_path.parent.mkdir(parents=True, exist_ok=True)
        closure_path.write_text(report, encoding="utf-8")
        closure_written = 1

    manifest = {
        "contract": "dd086_ddict_objects_runtime_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd085_status": dd085_manifest.get("status", ""),
        "runtime_proof": rel(repo, proof_path),
        "exe_exists": exe_exists,
        "exe_bytes": exe_bytes,
        "closure_written": closure_written,
        "closure_path": str(closure_path) if closure_written else "",
        "failures": failures,
        "cxx_source_edits": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-087 DDICT accepted command contract final closure / HELP integration planning lane.",
    }
    write_json(out / "dd086_objects_runtime_closure_manifest.json", manifest)

    print(f"DD-086 OBJECTS runtime closure manifest: {out / 'dd086_objects_runtime_closure_manifest.json'}")
    print(f"status: {status}; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
