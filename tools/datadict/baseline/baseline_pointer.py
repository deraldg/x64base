#!/usr/bin/env python3
"""
DD-038 report-only current baseline pointer inspector.

This tool reads docs/datadict/baselines/current_baseline.json, verifies that the
referenced accepted baseline manifest exists, and writes a report packet. It does
not run scans, accept baselines, mutate HELP/META/CMDHELPCHK, write DBFs, or move
files.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def rel_or_abs(root: Path, value: str) -> Path:
    p = Path(value)
    if p.is_absolute():
        return p
    return root / p


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-038 report-only current baseline pointer inspector")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--pointer", default="docs/datadict/baselines/current_baseline.json")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--emit-command", action="store_true", help="Emit a daily command reference script into the report packet")
    ap.add_argument("--fail-on-missing", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or "DD038-current-baseline-pointer"

    pointer_path = rel_or_abs(repo, args.pointer)
    checks: List[Dict[str, Any]] = []

    pointer_exists = pointer_path.exists()
    pointer: Dict[str, Any] = {}
    if pointer_exists:
        pointer = read_json(pointer_path)

    baseline_id = pointer.get("baseline_id", "")
    baseline_path = rel_or_abs(repo, pointer.get("baseline_path", "")) if pointer else Path("")
    baseline_manifest = rel_or_abs(repo, pointer.get("baseline_manifest", "")) if pointer else Path("")
    baseline_exists = bool(pointer and baseline_path.exists())
    manifest_exists = bool(pointer and baseline_manifest.exists())

    manifest_status = ""
    fingerprint = ""
    if manifest_exists:
        try:
            m = read_json(baseline_manifest)
            manifest_status = str(m.get("status", ""))
            fingerprint = str(m.get("fingerprint") or m.get("aggregate_fingerprint") or "")
        except Exception as exc:
            manifest_status = f"READ_ERROR: {exc}"

    checks.extend([
        {"check": "pointer_exists", "observed": int(pointer_exists), "required": 1, "pass": int(pointer_exists)},
        {"check": "baseline_path_exists", "observed": int(baseline_exists), "required": 1, "pass": int(baseline_exists)},
        {"check": "baseline_manifest_exists", "observed": int(manifest_exists), "required": 1, "pass": int(manifest_exists)},
        {"check": "baseline_manifest_status", "observed": manifest_status, "required": "ACCEPTED_BASELINE", "pass": int(manifest_status == "ACCEPTED_BASELINE")},
        {"check": "fingerprint_present", "observed": int(bool(fingerprint)), "required": 1, "pass": int(bool(fingerprint))},
    ])
    failures = sum(1 for r in checks if str(r["pass"]) != "1")
    status = "CURRENT_BASELINE_POINTER_READY" if failures == 0 else "CURRENT_BASELINE_POINTER_REVIEW"

    manifest = {
        "schema": "dd038_current_baseline_pointer_manifest_v0",
        "run_id": run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "pointer_path": str(pointer_path),
        "baseline_id": baseline_id,
        "baseline_path": str(baseline_path) if pointer else "",
        "baseline_manifest": str(baseline_manifest) if pointer else "",
        "baseline_manifest_status": manifest_status,
        "fingerprint": fingerprint,
        "profiles": args.profile,
        "gate_failures": failures,
        "boundary": {
            "source_edits": 0,
            "build": 0,
            "runtime_launch": 0,
            "help_meta_cmdhelpchk_mutation": 0,
            "dbf_cdx_lmdb_catalog_mutation": 0,
            "baseline_replacement": 0
        },
        "daily_command": ".\\tools\\datadict\\dd-status.ps1",
        "daily_command_with_closure": ".\\tools\\datadict\\dd-status.ps1 -AcceptBaselineArtifacts"
    }
    write_json(out / "dd038_current_baseline_pointer_manifest.json", manifest)
    write_csv(out / "dd038_pointer_check_ledger.csv", checks, ["check", "observed", "required", "pass"])

    report = f"""# DD-038 Current Baseline Pointer Report

Run id: `{run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Current baseline

- Pointer: `{pointer_path}`
- Baseline id: `{baseline_id}`
- Baseline path: `{baseline_path}`
- Baseline manifest: `{baseline_manifest}`
- Manifest status: `{manifest_status}`
- Fingerprint: `{fingerprint}`

## Daily commands

```powershell
.\\tools\\datadict\\dd-status.ps1
```

If the daily check reports accepted baseline/proof artifacts that need closure:

```powershell
.\\tools\\datadict\\dd-status.ps1 -AcceptBaselineArtifacts
```

## Boundary

DD-038 is report-only. It does not edit source, run builds, launch DotTalk++,
mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, move/delete files,
or replace baselines.
"""
    (out / "DD038_CURRENT_BASELINE_POINTER_REPORT.md").write_text(report, encoding="utf-8")

    if args.emit_command:
        cmd = """# DD-038 daily command reference
cd D:\\code\\ccode
.\\tools\\datadict\\dd-status.ps1
"""
        (out / "dd038_daily_command_reference.ps1").write_text(cmd, encoding="utf-8")

    print(f"DD-038 current baseline pointer manifest: {out / 'dd038_current_baseline_pointer_manifest.json'}")
    print(f"status: {status}; baseline: {baseline_id}; gate_failures: {failures}; fingerprint: {fingerprint}")
    if args.fail_on_missing and failures:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
