#!/usr/bin/env python3
"""
DD-045 Active Catalog Promotion Execution.

Authorized mutation scope:
  promote sandbox Data Dictionary catalog DBF/DBT files to active catalog path:
    dottalkpp/data/metadata/datadict/

Required:
  --execute-promotion

Execution behavior:
  1. Validate DD-044 promotion plan is READY.
  2. Validate sandbox inventory and hashes.
  3. Create backup directory under dottalkpp/data/metadata/datadict_backups/<run-id>.
  4. Back up existing active catalog if present.
  5. Replace active catalog directory with sandbox DBF/DBT files.
  6. Validate active file hashes against DD-044 sandbox inventory.
  7. Validate active DBF header row/field counts.
  8. Emit rollback script.

Not allowed:
  CDX creation
  LMDB writes/builds
  HELP/META/CMDHELPCHK mutation
  source edits
  runtime write operations
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import shutil
import struct
from pathlib import Path
from typing import Any, Dict, List


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


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def ps_path(repo_rel: str) -> str:
    return repo_rel.replace("/", "\\")


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


def read_dbf_header(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        data = f.read(8192)
    if len(data) < 32:
        raise ValueError(f"Too small for DBF header: {path}")
    version = data[0]
    records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    field_count = (header_len - 33) // 32
    return {
        "version": version,
        "records": records,
        "header_len": header_len,
        "record_len": record_len,
        "field_count": field_count,
    }


def list_active_files(active: Path) -> List[Path]:
    if not active.exists():
        return []
    return [p for p in active.iterdir() if p.is_file()]


def copy_tree_files(src_dir: Path, dst_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted(src_dir.iterdir(), key=lambda p: p.name.lower()):
        if not src.is_file():
            continue
        dst = dst_dir / src.name
        shutil.copy2(src, dst)
        rows.append({
            "file": src.name,
            "source": str(src),
            "target": str(dst),
            "bytes": dst.stat().st_size,
            "sha256": sha256_file(dst),
        })
    return rows


def emit_rollback_script(path: Path, repo: Path, active: Path, backup_dir: Path, backup_had_files: bool) -> None:
    backup_rel = ps_path(safe_rel(repo, backup_dir))
    if backup_had_files:
        body = f"""# DD-045 rollback script
# Restores active Data Dictionary catalog from backup.
# Review before execution.

$RepoRoot = "D:\\code\\ccode"
$Active = Join-Path $RepoRoot "dottalkpp\\data\\metadata\\datadict"
$Backup = Join-Path $RepoRoot "{backup_rel}"

if (-not (Test-Path $Backup)) {{
  throw "Backup path does not exist: $Backup"
}}

if (Test-Path $Active) {{
  Remove-Item $Active -Recurse -Force
}}
New-Item -ItemType Directory -Force $Active | Out-Null
Copy-Item (Join-Path $Backup "*") $Active -Recurse -Force
Write-Host "[DD-045 rollback] restored active catalog from $Backup"
"""
    else:
        body = """# DD-045 rollback script
# Removes active Data Dictionary catalog created when no previous active files existed.
# Review before execution.

$RepoRoot = "D:\\code\\ccode"
$Active = Join-Path $RepoRoot "dottalkpp\\data\\metadata\\datadict"

if (Test-Path $Active) {
  Remove-Item $Active -Recurse -Force
  Write-Host "[DD-045 rollback] removed active catalog $Active"
} else {
  Write-Host "[DD-045 rollback] active catalog already absent"
}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-045 active catalog promotion execution")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD045-active-catalog-promotion-execution-v0")
    ap.add_argument("--sandbox-path", default="dottalkpp/data/metadata/datadict_sandbox")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--backup-root", default="dottalkpp/data/metadata/datadict_backups")
    ap.add_argument("--dd044-dir", default="docs/datadict/reports/DD044-active-catalog-promotion-plan-v0")
    ap.add_argument("--dd041-dir", default="docs/datadict/reports/DD041-sandbox-catalog-dbf-smoke-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--execute-promotion", action="store_true", help="Required to replace active catalog")
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    sandbox = (repo / args.sandbox_path).resolve()
    active = (repo / args.active_path).resolve()
    backup_root = (repo / args.backup_root).resolve()
    backup_dir = backup_root / args.run_id
    dd044_dir = (repo / args.dd044_dir).resolve()
    dd041_dir = (repo / args.dd041_dir).resolve()

    out.mkdir(parents=True, exist_ok=True)
    assert_expected_paths(repo, sandbox, active, backup_root)

    plan_manifest = read_json(dd044_dir / "dd044_active_catalog_promotion_plan_manifest.json")
    inventory = read_csv_dict(dd044_dir / "dd044_sandbox_inventory.csv")
    dd041_rows = read_csv_dict(dd041_dir / "dd041_table_readback_ledger.csv")

    guard_rows: List[Dict[str, Any]] = []
    plan_ready = plan_manifest.get("status") == "ACTIVE_CATALOG_PROMOTION_PLAN_READY"
    guard_rows.append({
        "gate": "DD044_PROMOTION_PLAN_READY",
        "expected": "ACTIVE_CATALOG_PROMOTION_PLAN_READY",
        "observed": plan_manifest.get("status", ""),
        "pass": int(plan_ready),
    })

    sandbox_dbf_count = len([r for r in inventory if str(r.get("kind", "")).upper() == "DBF"])
    inv_ok = sandbox_dbf_count == len(CATALOG_TABLES)
    guard_rows.append({
        "gate": "DD044_SANDBOX_INVENTORY_COMPLETE",
        "expected": len(CATALOG_TABLES),
        "observed": sandbox_dbf_count,
        "pass": int(inv_ok),
    })

    execute_ok = int(args.execute_promotion)
    guard_rows.append({
        "gate": "PROMOTION_EXECUTION_FLAG_PRESENT",
        "expected": 1,
        "observed": execute_ok,
        "pass": execute_ok,
    })

    inventory_rows: List[Dict[str, Any]] = []
    inv_failures = 0
    for row in inventory:
        rel = row.get("path", "")
        p = repo / rel
        expected_sha = row.get("sha256", "")
        exists = p.exists()
        actual_sha = sha256_file(p) if exists else ""
        ok = exists and expected_sha == actual_sha
        if not ok:
            inv_failures += 1
        inventory_rows.append({
            "path": rel,
            "kind": row.get("kind", ""),
            "expected_sha256": expected_sha,
            "actual_sha256": actual_sha,
            "exists": int(exists),
            "pass": int(ok),
        })
    guard_rows.append({
        "gate": "SANDBOX_HASHES_MATCH_DD044_INVENTORY",
        "expected": 0,
        "observed": inv_failures,
        "pass": int(inv_failures == 0),
    })

    guard_failures = sum(1 for r in guard_rows if str(r.get("pass")) != "1")

    if not args.execute_promotion:
        write_csv(out / "dd045_execution_gate_ledger.csv", guard_rows, ["gate", "expected", "observed", "pass"])
        write_csv(out / "dd045_sandbox_inventory_recheck.csv", inventory_rows,
                  ["path", "kind", "expected_sha256", "actual_sha256", "exists", "pass"])
        manifest = {
            "contract": "dd045_active_catalog_promotion_execution_v0",
            "run_id": args.run_id,
            "created_utc": utc_now(),
            "status": "PROMOTION_EXECUTION_NOT_RUN",
            "reason": "Missing --execute-promotion",
            "gate_failures": guard_failures,
            "promotion_executed": 0,
            "active_catalog_replaced": 0,
            "backup_created": 0,
            "dbf_files_promoted": 0,
            "dbt_files_promoted": 0,
            "cdx_created": 0,
            "lmdb_written": 0,
            "protected_system_mutations": 0,
        }
        write_json(out / "dd045_active_catalog_promotion_execution_manifest.json", manifest)
        print(f"DD-045 promotion manifest: {out / 'dd045_active_catalog_promotion_execution_manifest.json'}")
        print("status: PROMOTION_EXECUTION_NOT_RUN; add --execute-promotion after authorization")
        return 2 if args.fail_on_review else 0

    if guard_failures:
        write_csv(out / "dd045_execution_gate_ledger.csv", guard_rows, ["gate", "expected", "observed", "pass"])
        manifest = {
            "contract": "dd045_active_catalog_promotion_execution_v0",
            "run_id": args.run_id,
            "created_utc": utc_now(),
            "status": "PROMOTION_EXECUTION_BLOCKED",
            "gate_failures": guard_failures,
            "promotion_executed": 0,
            "active_catalog_replaced": 0,
            "backup_created": 0,
            "protected_system_mutations": 0,
        }
        write_json(out / "dd045_active_catalog_promotion_execution_manifest.json", manifest)
        print(f"DD-045 promotion manifest: {out / 'dd045_active_catalog_promotion_execution_manifest.json'}")
        print(f"status: PROMOTION_EXECUTION_BLOCKED; gate_failures: {guard_failures}")
        return 2 if args.fail_on_review else 0

    backup_root.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    active_files_before = list_active_files(active)
    backup_had_files = bool(active_files_before)
    backup_rows: List[Dict[str, Any]] = []
    if backup_had_files:
        backup_rows = copy_tree_files(active, backup_dir)

    if active.exists():
        shutil.rmtree(active)
    active.mkdir(parents=True, exist_ok=True)

    promoted_rows: List[Dict[str, Any]] = []
    for row in inventory:
        rel = row.get("path", "")
        kind = row.get("kind", "")
        if str(kind).upper() not in {"DBF", "DBT"}:
            continue
        src = repo / rel
        dst = active / src.name
        shutil.copy2(src, dst)
        actual = sha256_file(dst)
        expected = row.get("sha256", "")
        promoted_rows.append({
            "table": row.get("table", ""),
            "kind": kind,
            "source": safe_rel(repo, src),
            "target": safe_rel(repo, dst),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "bytes": dst.stat().st_size,
            "pass": int(expected == actual),
        })

    promoted_failures = sum(1 for r in promoted_rows if str(r.get("pass")) != "1")

    expected_counts = {r.get("table", "").upper(): r for r in dd041_rows}
    readback_rows: List[Dict[str, Any]] = []
    readback_failures = 0
    for table in CATALOG_TABLES:
        dbf = active / f"{table}.dbf"
        expected = expected_counts.get(table, {})
        expected_rows = int(float(expected.get("projected_rows") or 0)) if expected else ""
        expected_fields = int(float(expected.get("field_count") or 0)) if expected else ""
        row = {
            "table": table,
            "dbf_exists": int(dbf.exists()),
            "expected_rows": expected_rows,
            "active_rows": "",
            "expected_fields": expected_fields,
            "active_fields": "",
            "status": "PENDING",
            "pass": 0,
        }
        if not dbf.exists():
            row["status"] = "FAIL_MISSING_DBF"
            readback_failures += 1
        else:
            try:
                hdr = read_dbf_header(dbf)
                row["active_rows"] = hdr["records"]
                row["active_fields"] = hdr["field_count"]
                ok = (expected_rows == "" or hdr["records"] == expected_rows) and (expected_fields == "" or hdr["field_count"] == expected_fields)
                row["status"] = "PASS" if ok else "FAIL_ACTIVE_READBACK_MISMATCH"
                row["pass"] = int(ok)
                if not ok:
                    readback_failures += 1
            except Exception as exc:
                row["status"] = f"FAIL_READ_ERROR: {type(exc).__name__}: {exc}"
                readback_failures += 1
        readback_rows.append(row)

    rollback_script = out / "dd045_rollback_active_catalog.ps1"
    emit_rollback_script(rollback_script, repo, active, backup_dir, backup_had_files)

    boundary_rows = [
        {"boundary": "promotion_execution_authorized", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_replacement_by_dd045", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "backup_created_by_dd045", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "hash_validation_failures", "observed": promoted_failures, "required": 0, "pass": int(promoted_failures == 0)},
        {"boundary": "active_readback_failures", "observed": readback_failures, "required": 0, "pass": int(readback_failures == 0)},
        {"boundary": "cdx_created", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_written", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "meta_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "protected_system_mutations", "observed": 0, "required": 0, "pass": 1},
    ]

    final_failures = promoted_failures + readback_failures
    status = "ACTIVE_CATALOG_PROMOTION_EXECUTION_GREEN" if final_failures == 0 else "ACTIVE_CATALOG_PROMOTION_EXECUTION_REVIEW"

    write_csv(out / "dd045_execution_gate_ledger.csv", guard_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd045_sandbox_inventory_recheck.csv", inventory_rows,
              ["path", "kind", "expected_sha256", "actual_sha256", "exists", "pass"])
    write_csv(out / "dd045_backup_ledger.csv", backup_rows,
              ["file", "source", "target", "bytes", "sha256"])
    write_csv(out / "dd045_promoted_file_hash_ledger.csv", promoted_rows,
              ["table", "kind", "source", "target", "expected_sha256", "actual_sha256", "bytes", "pass"])
    write_csv(out / "dd045_active_catalog_readback_ledger.csv", readback_rows,
              ["table", "dbf_exists", "expected_rows", "active_rows", "expected_fields", "active_fields", "status", "pass"])
    write_csv(out / "dd045_no_mutation_boundary_ledger.csv", boundary_rows,
              ["boundary", "observed", "required", "pass"])

    dbf_files = len([r for r in promoted_rows if str(r.get("kind", "")).upper() == "DBF"])
    dbt_files = len([r for r in promoted_rows if str(r.get("kind", "")).upper() == "DBT"])

    manifest = {
        "contract": "dd045_active_catalog_promotion_execution_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "source_sandbox": str(sandbox),
        "target_active_catalog": str(active),
        "backup_dir": str(backup_dir),
        "backup_had_files": int(backup_had_files),
        "backup_files_copied": len(backup_rows),
        "profiles": args.profile,
        "gate_failures": guard_failures,
        "promotion_executed": 1,
        "active_catalog_replaced": 1,
        "backup_created": 1,
        "dbf_files_promoted": dbf_files,
        "dbt_files_promoted": dbt_files,
        "hash_validation_failures": promoted_failures,
        "active_readback_failures": readback_failures,
        "cdx_created": 0,
        "lmdb_written": 0,
        "help_meta_cmdhelpchk_mutations": 0,
        "source_edits": 0,
        "protected_system_mutations": 0,
        "rollback_script": str(rollback_script),
        "next_recommended_package": "DD-046 active catalog post-promotion runtime readback / status closure",
    }
    write_json(out / "dd045_active_catalog_promotion_execution_manifest.json", manifest)

    report = f"""# DD-045 Active Catalog Promotion Execution Report

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Source and target

Source sandbox:

```text
{safe_rel(repo, sandbox)}
```

Active catalog:

```text
{safe_rel(repo, active)}
```

Backup directory:

```text
{safe_rel(repo, backup_dir)}
```

## Result

- Promotion executed: 1
- Active catalog replaced: 1
- Backup created: 1
- Backup files copied: {len(backup_rows)}
- DBF files promoted: {dbf_files}
- DBT files promoted: {dbt_files}
- Hash validation failures: {promoted_failures}
- Active readback failures: {readback_failures}
- CDX created: 0
- LMDB written: 0
- HELP/META/CMDHELPCHK mutations: 0

## Rollback

Rollback script:

```text
{safe_rel(repo, rollback_script)}
```

## Boundary

DD-045 promotes only DBF/DBT catalog files from sandbox to active catalog.
It does not create CDX files, write LMDB data, mutate HELP/META/CMDHELPCHK,
edit source, or build indexes.
"""
    (out / "DD045_ACTIVE_CATALOG_PROMOTION_EXECUTION_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-045 active catalog promotion execution manifest: {out / 'dd045_active_catalog_promotion_execution_manifest.json'}")
    print(f"status: {status}; dbf_files_promoted: {dbf_files}; dbt_files_promoted: {dbt_files}; hash_failures: {promoted_failures}; readback_failures: {readback_failures}")
    return 2 if (args.fail_on_review and final_failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
