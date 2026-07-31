#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23F_CANDIDATE_LOCALE_SPINE_PROMOTION_PLAN_GREEN_REPORT_ONLY"
STATUS_BLOCKED = "LOCALE_PHASE23F_CANDIDATE_LOCALE_SPINE_PROMOTION_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23G_ACTIVE_LOCALE_SPINE_PROMOTION_EXECUTION"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
CANDIDATE_ROOT = Path("docs/locale/candidates/phase23b_shared_locale_spine_candidate")

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
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

def rel(path: Path, repo: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)

def file_row(repo: Path, src: Path, dst: Path, artifact_type: str, required: bool = True) -> dict[str, Any]:
    exists = src.exists()
    return {
        "ARTIFACT_TYPE": artifact_type,
        "SOURCE_PATH": rel(src, repo),
        "TARGET_PATH": rel(dst, repo),
        "SOURCE_EXISTS": 1 if exists else 0,
        "BYTES": src.stat().st_size if exists else 0,
        "SHA256": sha256_file(src) if exists else "",
        "REQUIRED": 1 if required else 0,
        "PROMOTION_ACTION": "COPY_WITH_BACKUP_IF_AUTHORIZED",
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-report-only-promotion-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23e = first_row(reports / "locale_phase23e_status_summary_v1.csv")
    latest = {}
    latest_path = reports / "locale_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            import json
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except Exception:
            latest = {}

    candidate = repo / CANDIDATE_ROOT
    dbf_dir = candidate / "dbf"
    index_dir = candidate / "indexes"
    lmdb_dir = candidate / "lmdb"

    # Proposed active roots: neutral shared-locale infrastructure, not Messaging-specific.
    active_dbf_dir = repo / "dottalkpp/data/locale"
    active_index_dir = repo / "dottalkpp/data/indexes/locale"
    active_lmdb_dir = repo / "dottalkpp/data/lmdb/locale"

    sources = [
        file_row(repo, dbf_dir / "SYSTEM_LOCALES.dbf", active_dbf_dir / "SYSTEM_LOCALES.dbf", "DBF"),
        file_row(repo, dbf_dir / "SYSTEM_LOCALES.dbt", active_dbf_dir / "SYSTEM_LOCALES.dbt", "DBT", required=False),
        file_row(repo, dbf_dir / "SYSTEM_LOCALE_FALLBACK.dbf", active_dbf_dir / "SYSTEM_LOCALE_FALLBACK.dbf", "DBF"),
        file_row(repo, dbf_dir / "SYSTEM_LOCALE_FALLBACK.dbt", active_dbf_dir / "SYSTEM_LOCALE_FALLBACK.dbt", "DBT", required=False),
        file_row(repo, index_dir / "SYSTEM_LOCALES.cdx", active_index_dir / "SYSTEM_LOCALES.cdx", "CDX"),
        file_row(repo, index_dir / "SYSTEM_LOCALE_FALLBACK.cdx", active_index_dir / "SYSTEM_LOCALE_FALLBACK.cdx", "CDX"),
        file_row(repo, lmdb_dir / "SYSTEM_LOCALES.cdx.d" / "data.mdb", active_lmdb_dir / "SYSTEM_LOCALES.cdx.d" / "data.mdb", "LMDB_DATA_MDB"),
        file_row(repo, lmdb_dir / "SYSTEM_LOCALES.cdx.d" / "lock.mdb", active_lmdb_dir / "SYSTEM_LOCALES.cdx.d" / "lock.mdb", "LMDB_LOCK_MDB"),
        file_row(repo, lmdb_dir / "SYSTEM_LOCALE_FALLBACK.cdx.d" / "data.mdb", active_lmdb_dir / "SYSTEM_LOCALE_FALLBACK.cdx.d" / "data.mdb", "LMDB_DATA_MDB"),
        file_row(repo, lmdb_dir / "SYSTEM_LOCALE_FALLBACK.cdx.d" / "lock.mdb", active_lmdb_dir / "SYSTEM_LOCALE_FALLBACK.cdx.d" / "lock.mdb", "LMDB_LOCK_MDB"),
    ]

    required_missing = [r for r in sources if r["REQUIRED"] and not r["SOURCE_EXISTS"]]

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("OPERATOR_ACCEPTED_REPORT_ONLY_PROMOTION_PLAN",
         args.accept_report_only_promotion_plan,
         "requires --accept-report-only-promotion-plan")
    gate("PHASE23E_CANDIDATE_LMDB_GREEN",
         phase23e.get("STATUS") == "LOCALE_PHASE23E_CANDIDATE_LMDB_BUILD_RUNTIME_EXECUTION_GREEN",
         phase23e.get("STATUS", ""))
    gate("PHASE23E_VALIDATION_ZERO",
         phase23e.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23e.get('VALIDATION_ISSUES', '')}")
    gate("PHASE23E_LMDB_ENV_DIRS_TWO",
         phase23e.get("LMDB_ENV_DIRS", "") == "2",
         f"lmdb_env_dirs={phase23e.get('LMDB_ENV_DIRS', '')}")
    gate("PHASE23E_ACTIVE_PROMOTION_NOT_AUTHORIZED",
         phase23e.get("ACTIVE_PROMOTION_AUTHORIZED", "") == "0",
         f"active_promotion_authorized={phase23e.get('ACTIVE_PROMOTION_AUTHORIZED', '')}")
    gate("REQUIRED_CANDIDATE_ARTIFACTS_PRESENT",
         len(required_missing) == 0,
         f"missing_required={len(required_missing)}")
    review("LOC_023E_SAVEPOINT_LATEST",
           latest.get("savepoint_id") == "LOC-023E",
           f"latest_savepoint={latest.get('savepoint_id', '')}; recommended before active promotion planning")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    active_policy = [
        {"POLICY_ID": "ACTLOC-001", "ITEM": "active DBF root", "VALUE": "dottalkpp/data/locale", "STATUS": "PROPOSED"},
        {"POLICY_ID": "ACTLOC-002", "ITEM": "active indexes root", "VALUE": "dottalkpp/data/indexes/locale", "STATUS": "PROPOSED"},
        {"POLICY_ID": "ACTLOC-003", "ITEM": "active LMDB root", "VALUE": "dottalkpp/data/lmdb/locale", "STATUS": "PROPOSED"},
        {"POLICY_ID": "ACTLOC-004", "ITEM": "active promotion method", "VALUE": "backup existing active artifacts then copy candidate artifacts", "STATUS": "PROPOSED"},
        {"POLICY_ID": "ACTLOC-005", "ITEM": "promotion execution gate", "VALUE": "separate explicit authorization required for Phase 23G", "STATUS": "REQUIRED"},
        {"POLICY_ID": "ACTLOC-006", "ITEM": "runtime integration", "VALUE": "no source/runtime consumer integration in Phase 23F/23G unless separately authorized", "STATUS": "BOUNDARY"},
    ]

    execution_steps = [
        {"STEP": 1, "ACTION": "VERIFY_PRECONDITIONS", "DETAIL": "Confirm LOC-023E candidate DBF/CDX/LMDB green and source hashes match plan."},
        {"STEP": 2, "ACTION": "CREATE_ACTIVE_DIRECTORIES", "DETAIL": "Create dottalkpp/data/locale, dottalkpp/data/indexes/locale, and dottalkpp/data/lmdb/locale if authorized."},
        {"STEP": 3, "ACTION": "BACKUP_EXISTING_ACTIVE_ARTIFACTS", "DETAIL": "Copy existing active locale artifacts to timestamped backup before replacement."},
        {"STEP": 4, "ACTION": "COPY_CANDIDATE_DBF", "DETAIL": "Copy SYSTEM_LOCALES.dbf and SYSTEM_LOCALE_FALLBACK.dbf to active DBF root."},
        {"STEP": 5, "ACTION": "COPY_CANDIDATE_CDX", "DETAIL": "Copy SYSTEM_LOCALES.cdx and SYSTEM_LOCALE_FALLBACK.cdx to active indexes root."},
        {"STEP": 6, "ACTION": "COPY_CANDIDATE_LMDB", "DETAIL": "Copy SYSTEM_LOCALES.cdx.d and SYSTEM_LOCALE_FALLBACK.cdx.d env dirs to active LMDB root."},
        {"STEP": 7, "ACTION": "POST_PROMOTION_READBACK", "DETAIL": "Open active tables, attach indexes, set order, prove v64 and row counts."},
        {"STEP": 8, "ACTION": "SAVEPOINT", "DETAIL": "Append LOC-023G only after active promotion/readback is green."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 23F is promotion plan only; no active locale artifacts copied."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_DBF", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Candidate artifacts read/inventoried only."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_CDX", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Candidate CDX artifacts read/inventoried only."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Candidate LMDB artifacts read/inventoried only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
    ]

    write_csv(reports / "locale_phase23f_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "CANDIDATE_ARTIFACT_ROWS": len(sources),
        "REQUIRED_CANDIDATE_ARTIFACTS_MISSING": len(required_missing),
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "ACTIVE_PROMOTION_EXECUTED": 0,
        "ACTIVE_LOCALE_DBF_FILES_COPIED": 0,
        "ACTIVE_LOCALE_CDX_FILES_COPIED": 0,
        "ACTIVE_LOCALE_LMDB_FILE_ROWS_COPIED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "CANDIDATE_ARTIFACT_ROWS",
         "REQUIRED_CANDIDATE_ARTIFACTS_MISSING", "ACTIVE_PROMOTION_AUTHORIZED",
         "ACTIVE_PROMOTION_EXECUTED", "ACTIVE_LOCALE_DBF_FILES_COPIED",
         "ACTIVE_LOCALE_CDX_FILES_COPIED", "ACTIVE_LOCALE_LMDB_FILE_ROWS_COPIED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23f_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23f_candidate_artifact_inventory_v1.csv", sources,
              ["ARTIFACT_TYPE", "SOURCE_PATH", "TARGET_PATH", "SOURCE_EXISTS", "BYTES", "SHA256", "REQUIRED", "PROMOTION_ACTION"])
    write_csv(reports / "locale_phase23f_active_path_policy_v1.csv", active_policy,
              ["POLICY_ID", "ITEM", "VALUE", "STATUS"])
    write_csv(reports / "locale_phase23f_promotion_execution_steps_v1.csv", execution_steps,
              ["STEP", "ACTION", "DETAIL"])
    write_csv(reports / "locale_phase23f_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    plan_md = f"""# Locale Phase 23F — Candidate Locale Spine Promotion Plan

Status: `{status}`

Phase 23F is report-only. It plans, but does not execute, promotion of the
candidate shared locale spine into active neutral locale paths.

## Candidate source

```text
docs/locale/candidates/phase23b_shared_locale_spine_candidate
```

## Proposed active roots

```text
dottalkpp/data/locale
dottalkpp/data/indexes/locale
dottalkpp/data/lmdb/locale
```

These are proposed neutral shared-locale roots, not Messaging-only paths.

## Candidate artifacts inventoried

```text
artifact rows: {len(sources)}
required missing: {len(required_missing)}
```

## Promotion boundary

Phase 23F does not copy any active artifacts.

Active promotion remains separately gated:

```text
{NEXT_GATE}
```

## Important doctrine

The shared locale spine is infrastructure:

```text
SYSTEM_LOCALES
SYSTEM_LOCALE_FALLBACK
```

Messaging, HELP, CMDHELPCHK, manualgen, SelfDoc, and Data Dictionary may consume
it later. Phase 23F does not integrate any consumer and does not mutate source.
"""
    plan_path = repo / "docs/locale/LOCALE_PHASE23F_CANDIDATE_LOCALE_SPINE_PROMOTION_PLAN.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(plan_md, encoding="utf-8")

    manifest = []
    for p, role in [
        (reports / "locale_phase23f_status_summary_v1.csv", "phase23f status summary"),
        (reports / "locale_phase23f_candidate_artifact_inventory_v1.csv", "candidate promotion artifact inventory"),
        (reports / "locale_phase23f_active_path_policy_v1.csv", "active path policy proposal"),
        (reports / "locale_phase23f_promotion_execution_steps_v1.csv", "promotion execution step plan"),
        (reports / "locale_phase23f_boundary_ledger_v1.csv", "phase23f boundary ledger"),
        (plan_path, "phase23f narrative plan"),
    ]:
        if p.exists():
            manifest.append({
                "ARTIFACT": rel(p, repo),
                "ROLE": role,
                "BYTES": p.stat().st_size,
                "SHA256": sha256_file(p),
            })
    write_csv(reports / "locale_phase23f_artifact_manifest_v1.csv", manifest,
              ["ARTIFACT", "ROLE", "BYTES", "SHA256"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  candidate artifact rows: {len(sources)}")
    print(f"  required candidate artifacts missing: {len(required_missing)}")
    print("  active promotion authorized: 0")
    print("  active promotion executed: 0")
    print("  active locale dbf files copied: 0")
    print("  active locale cdx files copied: 0")
    print("  active locale lmdb file rows copied: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
