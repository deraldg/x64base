#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD070_STATUS = "DDICT_STATUS_TABLES_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"
TABLES = [
    "DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE",
    "DDEVID", "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE",
]


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
    table_hits = {name: int(name in upper) for name in TABLES}
    return {
        "has_ddict_status": int("DDICT STATUS" in upper),
        "has_active_catalog_path": int("ACTIVE CATALOG:" in upper and "METADATA" in upper and "DATADICT" in upper),
        "has_read_only": int("READ-ONLY" in upper),
        "has_dbf_11_of_11": int("DBF TABLES" in upper and "11 / 11" in upper),
        "has_active_catalog_present": int("ACTIVE_CATALOG_PRESENT" in upper),
        "has_ddict_tables": int("DDICT TABLES" in upper),
        "table_hit_count": sum(table_hits.values()),
        "all_tables_listed": int(all(table_hits.values())),
        "has_fields_pending": int("DDICT FIELDS" in upper and "PENDING" in upper),
        "has_unknown_command_for_ddict": int("UNKNOWN COMMAND" in upper and "DDICT" in upper),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-071 DDICT STATUS/TABLES runtime closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD071-ddict-status-tables-runtime-closure-v0")
    ap.add_argument("--dd070-dir", default="docs/datadict/reports/DD070-guarded-ddict-status-tables-implementation-apply-v0")
    ap.add_argument("--runtime-proof", required=True)
    ap.add_argument("--exe-path", default="build/src/Release/dottalkpp.exe")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-071_DDICT_STATUS_TABLES_RUNTIME_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd070_dir = (repo / args.dd070_dir).resolve()
    dd070_manifest = read_json(dd070_dir / "dd070_guarded_ddict_status_tables_impl_manifest.json")
    proof_path = (repo / args.runtime_proof).resolve()
    exe_path = (repo / args.exe_path).resolve()
    closure_path = (repo / args.closure_path).resolve()

    proof_text = read_text(proof_path)
    classified = classify_runtime(proof_text)

    exe_exists = int(exe_path.exists())
    exe_bytes = exe_path.stat().st_size if exe_path.exists() else 0
    proof_exists = int(proof_path.exists())
    dd070_ok = int(dd070_manifest.get("status") == EXPECTED_DD070_STATUS)

    gate_rows = [
        {"gate": "dd070_source_patch_applied", "expected": EXPECTED_DD070_STATUS, "observed": dd070_manifest.get("status", ""), "pass": dd070_ok},
        {"gate": "dottalkpp_exe_exists", "expected": 1, "observed": exe_exists, "pass": exe_exists},
        {"gate": "dottalkpp_exe_nonempty", "expected": 1, "observed": int(exe_bytes > 0), "pass": int(exe_bytes > 0)},
        {"gate": "runtime_proof_exists", "expected": 1, "observed": proof_exists, "pass": proof_exists},
        {"gate": "ddict_status_seen", "expected": 1, "observed": classified["has_ddict_status"], "pass": classified["has_ddict_status"]},
        {"gate": "active_catalog_path_seen", "expected": 1, "observed": classified["has_active_catalog_path"], "pass": classified["has_active_catalog_path"]},
        {"gate": "read_only_seen", "expected": 1, "observed": classified["has_read_only"], "pass": classified["has_read_only"]},
        {"gate": "dbf_11_of_11_seen", "expected": 1, "observed": classified["has_dbf_11_of_11"], "pass": classified["has_dbf_11_of_11"]},
        {"gate": "active_catalog_present_seen", "expected": 1, "observed": classified["has_active_catalog_present"], "pass": classified["has_active_catalog_present"]},
        {"gate": "ddict_tables_seen", "expected": 1, "observed": classified["has_ddict_tables"], "pass": classified["has_ddict_tables"]},
        {"gate": "all_11_tables_listed", "expected": 1, "observed": classified["all_tables_listed"], "pass": classified["all_tables_listed"]},
        {"gate": "fields_pending_preserved", "expected": 1, "observed": classified["has_fields_pending"], "pass": classified["has_fields_pending"]},
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

    table_rows = [{"table": name, "seen_in_runtime_proof": int(name in proof_text.upper())} for name in TABLES]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_STATUS_TABLES_RUNTIME_CLOSURE_GREEN" if failures == 0 else "DDICT_STATUS_TABLES_RUNTIME_CLOSURE_REVIEW"

    write_csv(out / "dd071_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd071_table_runtime_ledger.csv", table_rows, ["table", "seen_in_runtime_proof"])
    write_csv(out / "dd071_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-071 DDICT STATUS/TABLES Runtime Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-071 closes the first real `DDICT` read-surface milestone:

```text
DDICT STATUS
DDICT TABLES
```

## Evidence

- DD-070 status: `{dd070_manifest.get('status', '')}`
- Runtime proof: `{rel(repo, proof_path)}`
- Executable: `{rel(repo, exe_path)}`
- Executable exists: **{exe_exists}**
- Executable bytes: **{exe_bytes}**

## Runtime classification

- DDICT STATUS seen: **{classified['has_ddict_status']}**
- Active catalog path seen: **{classified['has_active_catalog_path']}**
- READ-ONLY seen: **{classified['has_read_only']}**
- DBF tables 11 / 11 seen: **{classified['has_dbf_11_of_11']}**
- ACTIVE_CATALOG_PRESENT seen: **{classified['has_active_catalog_present']}**
- DDICT TABLES seen: **{classified['has_ddict_tables']}**
- Canonical DD* tables listed: **{classified['table_hit_count']} / {len(TABLES)}**
- FIELDS pending preserved: **{classified['has_fields_pending']}**

## Boundary

DD-071 is closure/readback only. It does not edit C++ source, edit registry/build files,
mutate active catalog data, append/replace/delete/pack/zap DBFs, rebuild CDX/LMDB,
or mutate HELP/META/CMDHELPCHK.
"""
    (out / "DD071_DDICT_STATUS_TABLES_RUNTIME_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    closure_written = 0
    if args.write_closure:
        closure_path.parent.mkdir(parents=True, exist_ok=True)
        closure_path.write_text(report, encoding="utf-8")
        closure_written = 1

    manifest = {
        "contract": "dd071_ddict_status_tables_runtime_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd070_status": dd070_manifest.get("status", ""),
        "runtime_proof": rel(repo, proof_path),
        "exe_exists": exe_exists,
        "exe_bytes": exe_bytes,
        "table_hit_count": classified["table_hit_count"],
        "closure_written": closure_written,
        "closure_path": str(closure_path) if closure_written else "",
        "failures": failures,
        "cxx_source_edits": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "DD-072 plan for guarded DDICT FIELDS/TAGS implementation.",
    }
    write_json(out / "dd071_ddict_status_tables_runtime_closure_manifest.json", manifest)

    print(f"DD-071 DDICT STATUS/TABLES runtime closure manifest: {out / 'dd071_ddict_status_tables_runtime_closure_manifest.json'}")
    print(f"status: {status}; table_hits: {classified['table_hit_count']}; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
