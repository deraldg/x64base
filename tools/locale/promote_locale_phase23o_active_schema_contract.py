#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_PROMOTED = "LOCALE_PHASE23O_ACTIVE_LOCALE_SCHEMA_CONTRACT_PROMOTED_VALIDATE_HELD"
STATUS_BLOCKED = "LOCALE_PHASE23O_ACTIVE_LOCALE_SCHEMA_CONTRACT_PROMOTION_BLOCKED"
NEXT_GATE = "VALIDATE_PHASE23O_ACTIVE_SCHEMA_CONTRACT_THEN_SAVEPOINT"
REPORT_DIR = Path("docs/locale/reports")
BACKUP_ROOT = Path("docs/locale/backups")

CANDIDATE = Path("docs/locale/schemas/candidates/phase23n_schema_location_contract/locale_spine.dtschema")
TARGET = Path("dottalkpp/data/schemas/locale/locale_spine.dtschema")
MESSAGING_TARGET = Path("dottalkpp/data/schemas/messaging/message_catalog.dtschema")

def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
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

def backup_file(path: Path, backup_root: Path, repo: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    dest = backup_root / rel(path, repo)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return {
        "SOURCE_PATH": rel(path, repo),
        "BACKUP_PATH": rel(dest, repo),
        "BYTES": dest.stat().st_size,
        "SHA256": sha256_file(dest),
        "ACTION": "BACKUP_EXISTING_ACTIVE_SCHEMA",
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-active-schema-promotion", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23n = first_row(reports / "locale_phase23n_schema_location_status_summary_v1.csv")
    candidate = repo / CANDIDATE
    target = repo / TARGET
    messaging_target = repo / MESSAGING_TARGET

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_ALLOWED_ACTIVE_SCHEMA_PROMOTION",
         args.allow_active_schema_promotion,
         "requires --allow-active-schema-promotion")
    gate("PHASE23N_SCHEMA_LOCATION_GREEN",
         phase23n.get("STATUS") == "LOCALE_PHASE23N_SCHEMA_LOCATION_CONTRACT_GREEN_REPORT_ONLY",
         phase23n.get("STATUS", ""))
    gate("PHASE23N_VALIDATION_ZERO",
         phase23n.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23n.get('VALIDATION_ISSUES', '')}")
    gate("PHASE23N_ACTIVE_SCHEMA_HELD",
         phase23n.get("ACTIVE_SCHEMA_FILES_CREATED", "") == "0",
         f"active_schema_files_created={phase23n.get('ACTIVE_SCHEMA_FILES_CREATED', '')}")
    gate("LOCALE_SCHEMA_CANDIDATE_PRESENT",
         candidate.exists(),
         rel(candidate, repo))
    gate("MESSAGING_SCHEMA_TARGET_HELD",
         not messaging_target.exists(),
         "message_catalog.dtschema promotion intentionally held for field reconciliation")

    mutation_rows: list[dict[str, Any]] = []
    backup_rows: list[dict[str, Any]] = []
    status = STATUS_BLOCKED

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = repo / BACKUP_ROOT / f"LOC-023O_ACTIVE_SCHEMA_BACKUP_{timestamp}"

    if failures == 0:
        existing_backup = backup_file(target, backup_root, repo)
        if existing_backup:
            backup_rows.append(existing_backup)

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate, target)

        mutation_rows.append({
            "TARGET_PATH": rel(target, repo),
            "SOURCE_PATH": rel(candidate, repo),
            "ACTION": "PROMOTE_ACTIVE_LOCALE_SCHEMA_CONTRACT",
            "BYTES": target.stat().st_size,
            "SHA256": sha256_file(target),
            "SOURCE_SHA256": sha256_file(candidate),
        })
        status = STATUS_PROMOTED

    validation_issues = "0" if status == STATUS_PROMOTED else str(failures)

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_SCHEMA_CONTRACTS", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized active locale schema contract promotion only."},
        {"PROTECTED_SYSTEM": "MESSAGING_SCHEMA_CONTRACT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "message_catalog.dtschema held for field reconciliation."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "BUILD_RUNTIME", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No build or runtime execution."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    write_csv(reports / "locale_phase23o_promotion_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "ACTIVE_SCHEMA_PROMOTION_AUTHORIZED": 1 if args.allow_active_schema_promotion else 0,
        "ACTIVE_SCHEMA_FILES_CREATED_OR_REPLACED": len(mutation_rows),
        "ACTIVE_SCHEMA_BACKUP_ROWS": len(backup_rows),
        "LOCALE_SCHEMA_TARGET": rel(target, repo),
        "MESSAGING_SCHEMA_PROMOTED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "ACTIVE_SCHEMA_PROMOTION_AUTHORIZED",
         "ACTIVE_SCHEMA_FILES_CREATED_OR_REPLACED", "ACTIVE_SCHEMA_BACKUP_ROWS",
         "LOCALE_SCHEMA_TARGET", "MESSAGING_SCHEMA_PROMOTED", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23o_promotion_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23o_active_schema_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "SOURCE_PATH", "ACTION", "BYTES", "SHA256", "SOURCE_SHA256"])
    write_csv(reports / "locale_phase23o_active_schema_backup_inventory_v1.csv", backup_rows,
              ["SOURCE_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ACTION"])
    write_csv(reports / "locale_phase23o_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    package_doc = repo / "docs/locale/LOCALE_PHASE23O_ACTIVE_SCHEMA_CONTRACT_PROMOTION.md"
    package_doc.parent.mkdir(parents=True, exist_ok=True)
    package_doc.write_text(f"""# Locale Phase 23O — Active Schema Contract Promotion

Status: `{status}`

Promoted active schema contract:

```text
{rel(target, repo)}
```

Source candidate:

```text
{rel(candidate, repo)}
```

Messaging schema contract remains held:

```text
{rel(messaging_target, repo)}
```

Boundary: active schema contract promotion only. No DBF/CDX/LMDB, source,
runtime, HELP, CMDHELPCHK, manualgen, Data Dictionary, or SelfDoc mutation.

Next gate:

```text
{NEXT_GATE}
```
""", encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  active schema promotion authorized: {1 if args.allow_active_schema_promotion else 0}")
    print(f"  active schema files created/replaced: {len(mutation_rows)}")
    print(f"  active schema backup rows: {len(backup_rows)}")
    print(f"  locale schema target: {rel(target, repo)}")
    print("  messaging schema promoted: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_PROMOTED else 2

if __name__ == "__main__":
    raise SystemExit(main())
