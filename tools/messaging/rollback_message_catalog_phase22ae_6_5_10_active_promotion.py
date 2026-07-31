#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPORT_DIR = Path("docs/messaging/reports")
STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10_ACTIVE_CATALOG_ROLLBACK_EXECUTED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10_ACTIVE_CATALOG_ROLLBACK_BLOCKED"

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path):
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path: Path, repo: Path):
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def restore_one(repo: Path, original: Path, backup: Path, kind: str):
    if kind == "missing":
        # If original now exists but did not at backup, remove it.
        if original.is_dir():
            shutil.rmtree(original)
            return "removed_dir"
        if original.is_file():
            original.unlink()
            return "removed_file"
        return "still_missing"
    if kind == "dir":
        if original.exists():
            if original.is_dir():
                shutil.rmtree(original)
            else:
                original.unlink()
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(backup, original)
        return "restored_dir"
    if kind == "file":
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, original)
        return "restored_file"
    return "skipped_unknown_kind"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--backup-root", default="")
    ap.add_argument("--allow-active-catalog-rollback", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    prep = first_row(reports / "message_catalog_phase22ae_6_5_10_prepare_status_summary_v1.csv")
    backup_root = Path(args.backup_root) if args.backup_root else repo / prep.get("BACKUP_ROOT", "")
    if not backup_root.is_absolute():
        backup_root = repo / backup_root

    rows = read_csv(reports / "message_catalog_phase22ae_6_5_10_backup_manifest_v1.csv")
    restore_rows = []
    failures = 0
    if not args.allow_active_catalog_rollback:
        failures += 1
    if not backup_root.exists():
        failures += 1

    if failures == 0:
        for row in rows:
            original = repo / row.get("ORIGINAL_PATH", "")
            backup = repo / row.get("BACKUP_PATH", "")
            kind = row.get("KIND", "")
            if not backup.is_absolute():
                backup = repo / backup
            try:
                action = restore_one(repo, original, backup, kind)
                ok = 1
                detail = ""
            except Exception as exc:
                action = "failed"
                ok = 0
                detail = str(exc)
                failures += 1
            restore_rows.append({
                "ROLE": row.get("ROLE",""),
                "ORIGINAL_PATH": rel(original, repo),
                "BACKUP_PATH": rel(backup, repo),
                "KIND": kind,
                "ACTION": action,
                "OK": ok,
                "DETAIL": detail,
            })

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    write_csv(reports / "message_catalog_phase22ae_6_5_10_rollback_restore_rows_v1.csv", restore_rows, ["ROLE","ORIGINAL_PATH","BACKUP_PATH","KIND","ACTION","OK","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10_rollback_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": failures,
        "ALLOW_ACTIVE_CATALOG_ROLLBACK": 1 if args.allow_active_catalog_rollback else 0,
        "BACKUP_ROOT": rel(backup_root, repo),
        "RESTORE_ROWS": len(restore_rows),
        "NEXT_GATE": "RERUN_PHASE22AE_6_5_10_PREPARE_OR_HOLD_FOR_REVIEW",
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","ALLOW_ACTIVE_CATALOG_ROLLBACK","BACKUP_ROOT","RESTORE_ROWS","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {failures}")
    print(f"  backup root: {rel(backup_root, repo)}")
    print(f"  restore rows: {len(restore_rows)}")
    print("  active catalog rollback observed: 1" if status == STATUS_GREEN else "  active catalog rollback observed: 0")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
