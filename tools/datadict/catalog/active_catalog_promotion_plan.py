#!/usr/bin/env python3
"""
DD-044 Active Catalog Promotion Plan.

Report-only authority gate for promoting the sandbox Data Dictionary catalog.

This tool verifies that the sandbox catalog proof chain is present and green,
then emits a promotion plan. It does NOT copy files, replace the active catalog,
write DBFs, create CDX, write LMDB, mutate HELP/META/CMDHELPCHK, or edit source.

Promotion execution must be a separate explicit package after this plan is green.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


CATALOG_TABLES = [
    "DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE",
    "DDEVID", "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE"
]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


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


def assert_inside(repo: Path, path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(repo.resolve())
    except Exception:
        raise SystemExit(f"{label} must be inside repo root: {path}")


def assert_expected_paths(repo: Path, sandbox: Path, active: Path, backup_root: Path) -> None:
    assert_inside(repo, sandbox, "sandbox path")
    assert_inside(repo, active, "active catalog path")
    assert_inside(repo, backup_root, "backup root")
    srel = sandbox.resolve().relative_to(repo.resolve()).as_posix().lower()
    arel = active.resolve().relative_to(repo.resolve()).as_posix().lower()
    brel = backup_root.resolve().relative_to(repo.resolve()).as_posix().lower()
    if srel != "dottalkpp/data/metadata/datadict_sandbox":
        raise SystemExit(f"Unexpected sandbox path: {srel}")
    if arel != "dottalkpp/data/metadata/datadict":
        raise SystemExit(f"Unexpected active catalog path: {arel}")
    if brel != "dottalkpp/data/metadata/datadict_backups":
        raise SystemExit(f"Unexpected backup root: {brel}")


def check_manifest(name: str, path: Path, expected_status: str, rows: List[Dict[str, Any]]) -> bool:
    data = read_json(path)
    status = data.get("status", "")
    ok = path.exists() and status == expected_status
    rows.append({
        "gate": name,
        "path": str(path),
        "expected": expected_status,
        "observed": status,
        "exists": int(path.exists()),
        "pass": int(ok),
    })
    return ok


def inventory_sandbox(repo: Path, sandbox: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for table in CATALOG_TABLES:
        for ext in [".dbf", ".dbt"]:
            path = sandbox / f"{table}{ext}"
            if path.exists():
                rows.append({
                    "table": table,
                    "kind": ext.upper().lstrip("."),
                    "path": safe_rel(repo, path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                })
    return rows


def build_execution_plan(run_id: str, repo: Path, sandbox: Path, active: Path, backup_dir: Path) -> str:
    return f"""# DD-044 generated promotion execution plan
# REPORT-ONLY. Do not execute as promotion authority.
#
# Intended later package: DD-045 Active Catalog Promotion Execution
#
# Source sandbox:
#   {sandbox}
#
# Target active catalog:
#   {active}
#
# Backup target:
#   {backup_dir}
#
# Required execution sequence for DD-045:
#   1. Revalidate DD-041, DD-042, DD-043 v1.1, and DotTalk++ runtime proof.
#   2. Verify sandbox inventory and hashes match this DD-044 plan.
#   3. Create backup directory.
#   4. If active catalog exists, copy active catalog to backup before replacement.
#   5. Copy sandbox DBF/DBT files to active catalog.
#   6. Validate copied active catalog hashes against sandbox inventory.
#   7. Run readback on active catalog.
#   8. Emit rollback script.
#
# No command below is executed by DD-044.
#
# Suggested later DD-045 outline:
# New-Item -ItemType Directory -Force "{backup_dir}" | Out-Null
# Copy-Item "{active}\\*" "{backup_dir}\\" -Recurse -Force
# New-Item -ItemType Directory -Force "{active}" | Out-Null
# Copy-Item "{sandbox}\\*.dbf" "{active}\\" -Force
# Copy-Item "{sandbox}\\*.dbt" "{active}\\" -Force
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-044 report-only active catalog promotion plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD044-active-catalog-promotion-plan-v0")
    ap.add_argument("--sandbox-path", default="dottalkpp/data/metadata/datadict_sandbox")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--backup-root", default="dottalkpp/data/metadata/datadict_backups")
    ap.add_argument("--dd041", default="docs/datadict/reports/DD041-sandbox-catalog-dbf-smoke-v0/dd041_sandbox_catalog_dbf_smoke_manifest.json")
    ap.add_argument("--dd042", default="docs/datadict/reports/DD042-sandbox-catalog-inspection-v0/dd042_sandbox_catalog_inspection_manifest.json")
    ap.add_argument("--dd043", default="docs/datadict/reports/DD043-pydottalk-runtime-readback-v1_1/dd043_pydottalk_runtime_readback_manifest.json")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--acknowledge-dot-runtime-proof", action="store_true",
                    help="Acknowledge the local DotTalk++ USE/COUNT/TUP runtime proof recorded in runlog")
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    sandbox = (repo / args.sandbox_path).resolve()
    active = (repo / args.active_path).resolve()
    backup_root = (repo / args.backup_root).resolve()
    backup_dir = backup_root / args.run_id

    out.mkdir(parents=True, exist_ok=True)
    assert_expected_paths(repo, sandbox, active, backup_root)

    gate_rows: List[Dict[str, Any]] = []
    ok041 = check_manifest("DD041_SANDBOX_DBF_READBACK_GREEN", repo / args.dd041,
                           "SANDBOX_CATALOG_DBF_READBACK_GREEN", gate_rows)
    ok042 = check_manifest("DD042_SANDBOX_INSPECTION_READY", repo / args.dd042,
                           "SANDBOX_CATALOG_INSPECTION_READY", gate_rows)
    ok043 = check_manifest("DD043_V1_1_PYDOTTALK_RUNTIME_GREEN", repo / args.dd043,
                           "PYDOTTALK_RUNTIME_READBACK_GREEN", gate_rows)

    dot_runtime_path = repo / "docs/datadict/runlog/DD-043_LOCAL_DOTTALK_RUNTIME_SANDBOX_CATALOG_READBACK_PROOF.md"
    dot_runtime_ok = dot_runtime_path.exists() and args.acknowledge_dot_runtime_proof
    gate_rows.append({
        "gate": "DOTTALK_RUNTIME_USE_COUNT_TUP_PROOF_ACKNOWLEDGED",
        "path": str(dot_runtime_path),
        "expected": "exists and --acknowledge-dot-runtime-proof",
        "observed": f"exists={int(dot_runtime_path.exists())}; acknowledged={int(args.acknowledge_dot_runtime_proof)}",
        "exists": int(dot_runtime_path.exists()),
        "pass": int(dot_runtime_ok),
    })

    sandbox_inventory = inventory_sandbox(repo, sandbox)
    expected_files_ok = len([r for r in sandbox_inventory if r["kind"] == "DBF"]) == len(CATALOG_TABLES)
    gate_rows.append({
        "gate": "SANDBOX_DBF_INVENTORY_COMPLETE",
        "path": str(sandbox),
        "expected": f"{len(CATALOG_TABLES)} DBF files",
        "observed": len([r for r in sandbox_inventory if r["kind"] == "DBF"]),
        "exists": int(sandbox.exists()),
        "pass": int(expected_files_ok),
    })

    active_exists = active.exists()
    backup_root_parent_exists = backup_root.parent.exists()
    gate_rows.append({
        "gate": "BACKUP_ROOT_PARENT_EXISTS",
        "path": str(backup_root.parent),
        "expected": "exists",
        "observed": int(backup_root_parent_exists),
        "exists": int(backup_root.parent.exists()),
        "pass": int(backup_root_parent_exists),
    })

    promotion_authorized = 0
    gate_rows.append({
        "gate": "PROMOTION_EXECUTION_AUTHORIZED",
        "path": "",
        "expected": "0 in DD-044 plan",
        "observed": promotion_authorized,
        "exists": "",
        "pass": 1,
    })

    failures = sum(1 for r in gate_rows if str(r.get("pass")) != "1")
    status = "ACTIVE_CATALOG_PROMOTION_PLAN_READY" if failures == 0 else "ACTIVE_CATALOG_PROMOTION_PLAN_REVIEW"

    boundary_rows = [
        {"boundary": "promotion_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_replacement_by_dd044", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "backup_created_by_dd044", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_rows_written_by_dd044", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_created", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_written", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "meta_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "protected_system_mutations", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd044_promotion_gate_ledger.csv", gate_rows,
              ["gate", "path", "expected", "observed", "exists", "pass"])
    write_csv(out / "dd044_sandbox_inventory.csv", sandbox_inventory,
              ["table", "kind", "path", "bytes", "sha256"])
    write_csv(out / "dd044_no_mutation_boundary_ledger.csv", boundary_rows,
              ["boundary", "observed", "required", "pass"])

    plan_text = build_execution_plan(args.run_id, repo, sandbox, active, backup_dir)
    (out / "dd044_generated_promotion_execution_plan_NOT_AUTHORIZED.ps1").write_text(plan_text, encoding="utf-8")

    manifest = {
        "contract": "dd044_active_catalog_promotion_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "source_sandbox": str(sandbox),
        "target_active_catalog": str(active),
        "backup_target_for_future_execution": str(backup_dir),
        "profiles": args.profile,
        "gate_failures": failures,
        "active_catalog_exists_now": int(active_exists),
        "sandbox_inventory_files": len(sandbox_inventory),
        "sandbox_dbf_files": len([r for r in sandbox_inventory if r["kind"] == "DBF"]),
        "promotion_execution_authorized": 0,
        "active_catalog_replaced": 0,
        "backup_created": 0,
        "dbf_rows_written": 0,
        "cdx_created": 0,
        "lmdb_written": 0,
        "protected_system_mutations": 0,
        "next_recommended_package": "DD-045 Active Catalog Promotion Execution, only after explicit promotion execution authorization",
    }
    write_json(out / "dd044_active_catalog_promotion_plan_manifest.json", manifest)

    report = f"""# DD-044 Active Catalog Promotion Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-044 is a report-only authority gate for promoting the sandbox Data Dictionary catalog.

It does not promote the catalog.

## Source and target

Source sandbox:

```text
{safe_rel(repo, sandbox)}
```

Target active catalog for a future execution package:

```text
{safe_rel(repo, active)}
```

Future backup target:

```text
{safe_rel(repo, backup_dir)}
```

## Preconditions

- DD-041 sandbox DBF creation/readback green: {int(ok041)}
- DD-042 sandbox inspection green: {int(ok042)}
- DD-043 v1.1 pydottalk runtime readback green: {int(ok043)}
- DotTalk++ direct runtime proof acknowledged: {int(dot_runtime_ok)}
- Sandbox DBF inventory complete: {int(expected_files_ok)}

## Boundary

DD-044 is plan-only. It does not copy DBFs, replace the active catalog, create a
backup, create CDX files, write LMDB data, mutate HELP/META/CMDHELPCHK, edit
source, or promote dictionary facts.

## Next

DD-045 may execute active catalog promotion only after explicit promotion execution
authorization. DD-045 must back up any existing active catalog before replacement,
copy sandbox DBF/DBT files, validate hashes, and provide rollback instructions.
"""
    (out / "DD044_ACTIVE_CATALOG_PROMOTION_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-044 active catalog promotion plan manifest: {out / 'dd044_active_catalog_promotion_plan_manifest.json'}")
    print(f"status: {status}; gate_failures: {failures}; promotion_execution_authorized: 0; sandbox_dbf_files: {manifest['sandbox_dbf_files']}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
