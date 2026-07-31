#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_2_EXECUTION_SCRIPT_TARGET_CONSTANT_REPAIR_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_2_EXECUTION_SCRIPT_TARGET_CONSTANT_REPAIR_BLOCKED"
NEXT_GATE = "RERUN_PHASE22AE_WITH_ALLOW_ALREADY_PROMOTED_NOOP_THEN_APPEND_IF_GREEN"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_BASE = Path("docs/messaging/backups")
TARGET = Path("tools/messaging/execute_message_catalog_phase22ae_active_catalog_replacement.py")

ANCHOR = 'REQUIRED_LOCALES = ["en-US", "es", "fr", "de", "it"]'

REQUIRED_CONSTANTS = {
    "CURRENT_MESSAGES": "12",
    "CURRENT_TEXT_ROWS": "60",
    "TARGET_MESSAGES": "14",
    "TARGET_TEXT_ROWS": "70",
}

def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def constant_line(name: str, value: str) -> str:
    return f"{name} = {value}"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-tool-repair", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    target = repo / TARGET
    failures = 0
    errors: list[str] = []
    backup_rows: list[dict] = []
    mutation_rows: list[dict] = []
    action_rows: list[dict] = []

    if not args.allow_tool_repair:
        failures += 1
        errors.append("missing --allow-tool-repair")
    if not target.exists():
        failures += 1
        errors.append(f"target script missing: {rel(target, repo)}")

    status = STATUS_BLOCKED

    if failures == 0:
        try:
            text = target.read_text(encoding="utf-8")

            backup_root = repo / BACKUP_BASE / f"MSG-022AE_2_SCRIPT_TARGET_CONSTANT_REPAIR_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            backup_path = backup_root / TARGET
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup_path)
            backup_rows.append({
                "TARGET_PATH": rel(target, repo),
                "BACKUP_PATH": rel(backup_path, repo),
                "BYTES": backup_path.stat().st_size,
                "SHA256": sha256_file(backup_path),
                "ROLE": "pre_repair_tool_backup",
            })

            missing = []
            for name, value in REQUIRED_CONSTANTS.items():
                if constant_line(name, value) not in text:
                    missing.append((name, value))

            if not missing:
                action_rows.append({
                    "TARGET_PATH": rel(target, repo),
                    "ACTION": "NOOP_ALREADY_REPAIRED",
                    "DETAIL": "all CURRENT/TARGET constants already present",
                })
                status = STATUS_GREEN
            else:
                if ANCHOR not in text:
                    raise RuntimeError(f"anchor not found: {ANCHOR}")

                # Insert only the missing constants immediately after REQUIRED_LOCALES.
                insert_block = "\n" + "\n".join(constant_line(name, value) for name, value in missing) + "\n"
                text2 = text.replace(ANCHOR, ANCHOR + insert_block, 1)

                # Safety: do not duplicate constants that already exist elsewhere.
                for name, value in REQUIRED_CONSTANTS.items():
                    count = text2.count(constant_line(name, value))
                    if count != 1:
                        raise RuntimeError(f"constant {name} appears {count} times after repair; refusing")

                target.write_text(text2, encoding="utf-8")
                mutation_rows.append({
                    "TARGET_PATH": rel(target, repo),
                    "ACTION": "INSERT_MISSING_CONSTANTS",
                    "BYTES": target.stat().st_size,
                    "SHA256": sha256_file(target),
                    "DETAIL": "inserted missing constants: " + ";".join(name for name, _ in missing),
                })
                for name, value in missing:
                    action_rows.append({
                        "TARGET_PATH": rel(target, repo),
                        "ACTION": "INSERT_CONSTANT",
                        "DETAIL": f"{name} = {value}",
                    })
                status = STATUS_GREEN
        except Exception as exc:
            failures += 1
            errors.append(str(exc))
            status = STATUS_BLOCKED

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_2_script_repair_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])
    write_csv(reports / "message_catalog_phase22ae_2_script_repair_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_2_script_repair_actions_v1.csv", action_rows,
              ["TARGET_PATH", "ACTION", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "TOOLS_MESSAGING_SCRIPT", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Repair is limited to missing constants in the Phase 22AE execution script."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No src/include source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation during 22AE.2 script repair."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation during 22AE.2 script repair."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation during 22AE.2 script repair."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_2_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_2_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "TOOL_REPAIR_AUTHORIZED": 1 if args.allow_tool_repair else 0,
        "TOOL_FILES_MUTATED": len(mutation_rows),
        "TOOL_BACKUP_ROWS": len(backup_rows),
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "TOOL_REPAIR_AUTHORIZED", "TOOL_FILES_MUTATED",
         "TOOL_BACKUP_ROWS", "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  tool repair authorized: {1 if args.allow_tool_repair else 0}")
    print(f"  tool files mutated: {len(mutation_rows)}")
    print(f"  tool backup rows: {len(backup_rows)}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
