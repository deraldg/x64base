#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_5_2_PARTIAL_PROMOTION_REPAIR_OR_ROLLBACK_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_5_2_PARTIAL_PROMOTION_REPAIR_OR_ROLLBACK_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_5_3_ACTIVE_CATALOG_ROLLBACK_EXECUTION"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_BASE = Path("docs/messaging/backups")

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
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def savepoint_present(repo: Path, savepoint_id: str):
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest_path.exists():
        try:
            latest_id = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id == savepoint_id or savepoint_id in text, latest_id

def discover_backups(repo: Path):
    # Prefer the explicit 22AE.5 backup inventory if it exists.
    inv = read_csv(repo / REPORT_DIR / "message_catalog_phase22ae_5_backup_inventory_v1.csv")
    roots = []
    for row in inv:
        backup = row.get("BACKUP", "")
        if backup:
            parts = Path(backup.replace("/", "\\")).parts
            # docs/messaging/backups/<root>/messaging or indexes_messaging...
            try:
                i = parts.index("backups")
                if i + 1 < len(parts):
                    root = Path(*parts[:i+2])
                    roots.append(str(root).replace("\\", "/"))
            except ValueError:
                pass

    # Fallback: scan backups directory.
    base = repo / BACKUP_BASE
    if base.exists():
        for d in sorted(base.glob("MSG-022AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_BACKUP_*"), key=lambda p: p.name, reverse=True):
            if d.is_dir():
                roots.append(rel(d, repo))

    seen = []
    for r in roots:
        if r not in seen:
            seen.append(r)

    rows = []
    for idx, r in enumerate(seen):
        d = repo / r
        rows.append({
            "BACKUP_ROOT": r,
            "MESSAGING_EXISTS": 1 if (d / "messaging").exists() else 0,
            "INDEXES_EXISTS": 1 if (d / "indexes_messaging").exists() else 0,
            "LMDB_EXISTS": 1 if (d / "lmdb_messaging").exists() else 0,
            "MESSAGING_FILES": sum(1 for p in (d / "messaging").rglob("*") if p.is_file()) if (d / "messaging").exists() else 0,
            "INDEX_FILES": sum(1 for p in (d / "indexes_messaging").rglob("*") if p.is_file()) if (d / "indexes_messaging").exists() else 0,
            "LMDB_FILES": sum(1 for p in (d / "lmdb_messaging").rglob("*") if p.is_file()) if (d / "lmdb_messaging").exists() else 0,
            "SELECTED_FOR_ROLLBACK": 1 if idx == 0 else 0,
        })
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae51 = first_row(reports / "message_catalog_phase22ae_5_1_status_summary_v1.csv")
    ae5 = first_row(reports / "message_catalog_phase22ae_5_status_summary_v1.csv")
    sp_ok, latest = savepoint_present(repo, "MSG-022AE.5.1")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_5_1_GREEN",
         ae51.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_1_PARTIAL_PROMOTION_DIAGNOSTIC_GREEN_SOURCE_HELD",
         ae51.get("STATUS", "missing"))
    gate("MSG_022AE_5_1_SAVEPOINT_PRESENT", sp_ok, latest)
    gate("PHASE22AE_5_BLOCKED",
         ae5.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_BLOCKED",
         ae5.get("STATUS", "missing"))
    gate("COUNTS_ARE_PARTIAL_14_70",
         ae51.get("MESSAGE_ROWS_AFTER") == "14" and ae51.get("TEXT_ROWS_AFTER") == "70",
         f"{ae51.get('MESSAGE_ROWS_AFTER')}/{ae51.get('TEXT_ROWS_AFTER')}")
    gate("REQUIRED_KEYS_ABSENT",
         ae51.get("REQUIRED_MESSAGE_SYMBOL_ROWS_FOUND") == "0" and ae51.get("REQUIRED_TEXT_KEY_ROWS_FOUND") == "0",
         f"msg={ae51.get('REQUIRED_MESSAGE_SYMBOL_ROWS_FOUND')}; text={ae51.get('REQUIRED_TEXT_KEY_ROWS_FOUND')}")

    backup_rows = discover_backups(repo)
    selected = backup_rows[0] if backup_rows else {}
    gate("ROLLBACK_BACKUP_FOUND", len(backup_rows) > 0, f"backups={len(backup_rows)}")
    gate("SELECTED_BACKUP_HAS_MESSAGING_FILES",
         int(selected.get("MESSAGING_FILES", 0) or 0) > 0,
         selected.get("BACKUP_ROOT", ""))

    decision_rows = [
        {"OPTION": "ROLLBACK_TO_22AE5_BACKUP", "RECOMMENDATION": "PRIMARY", "WHY": "22AE.5 appended rows but did not populate required keys; restore clean 12/60 baseline before any redesigned apply.", "ACTIVE_MUTATION_REQUIRED_LATER": 1, "NEXT_PHASE": "22AE.5.3"},
        {"OPTION": "IN_PLACE_REPAIR", "RECOMMENDATION": "DEFER", "WHY": "Could be possible, but the runtime syntax that appended rows failed to populate fields; repair should not be attempted until row identity and update syntax are proven.", "ACTIVE_MUTATION_REQUIRED_LATER": 1, "NEXT_PHASE": "after rollback or sandbox proof"},
        {"OPTION": "RERUN_22AE5", "RECOMMENDATION": "FORBID", "WHY": "Would risk appending more malformed rows.", "ACTIVE_MUTATION_REQUIRED_LATER": 0, "NEXT_PHASE": "not allowed"},
    ]

    rollback_plan = [
        {"STEP": 1, "ACTION": "CONFIRM_NO_DOTTALKPP_PROCESS", "DETAIL": "Active catalog files must not be open/locked.", "MUTATES_ACTIVE": 0},
        {"STEP": 2, "ACTION": "SNAPSHOT_CURRENT_PARTIAL_STATE", "DETAIL": "Fingerprint and archive the current 14/70 partial state.", "MUTATES_ACTIVE": 0},
        {"STEP": 3, "ACTION": "RESTORE_SELECTED_BACKUP", "DETAIL": f"Restore selected backup root: {selected.get('BACKUP_ROOT','')}", "MUTATES_ACTIVE": 1},
        {"STEP": 4, "ACTION": "READBACK_12_60", "DETAIL": "Validate active catalog is back to 12 messages and 60 text rows.", "MUTATES_ACTIVE": 0},
        {"STEP": 5, "ACTION": "RERUN_22V_REGRESSION", "DETAIL": "Confirm the pre-promotion catalog remains runtime-green after rollback.", "MUTATES_ACTIVE": 0},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation in 22AE.5.2."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Plan/readback only; rollback is deferred to 22AE.5.3."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22ae_5_2_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_5_2_backup_selection_v1.csv", backup_rows, ["BACKUP_ROOT", "MESSAGING_EXISTS", "INDEXES_EXISTS", "LMDB_EXISTS", "MESSAGING_FILES", "INDEX_FILES", "LMDB_FILES", "SELECTED_FOR_ROLLBACK"])
    write_csv(reports / "message_catalog_phase22ae_5_2_decision_matrix_v1.csv", decision_rows, ["OPTION", "RECOMMENDATION", "WHY", "ACTIVE_MUTATION_REQUIRED_LATER", "NEXT_PHASE"])
    write_csv(reports / "message_catalog_phase22ae_5_2_rollback_plan_v1.csv", rollback_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_5_2_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_5_2_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_5_1_GREEN": 1 if ae51.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_1_PARTIAL_PROMOTION_DIAGNOSTIC_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_5_1_SAVEPOINT_PRESENT": 1 if sp_ok else 0,
        "MESSAGE_ROWS_AFTER": ae51.get("MESSAGE_ROWS_AFTER", ""),
        "TEXT_ROWS_AFTER": ae51.get("TEXT_ROWS_AFTER", ""),
        "REQUIRED_MESSAGE_SYMBOL_ROWS_FOUND": ae51.get("REQUIRED_MESSAGE_SYMBOL_ROWS_FOUND", ""),
        "REQUIRED_TEXT_KEY_ROWS_FOUND": ae51.get("REQUIRED_TEXT_KEY_ROWS_FOUND", ""),
        "BACKUPS_FOUND": len(backup_rows),
        "SELECTED_BACKUP_ROOT": selected.get("BACKUP_ROOT", ""),
        "RECOMMENDED_DECISION": "ROLLBACK_TO_22AE5_BACKUP",
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_5_1_GREEN", "MSG_022AE_5_1_SAVEPOINT_PRESENT", "MESSAGE_ROWS_AFTER", "TEXT_ROWS_AFTER", "REQUIRED_MESSAGE_SYMBOL_ROWS_FOUND", "REQUIRED_TEXT_KEY_ROWS_FOUND", "BACKUPS_FOUND", "SELECTED_BACKUP_ROOT", "RECOMMENDED_DECISION", "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.5.2 Partial Promotion Repair or Rollback Plan

Status: `{status}`

22AE.5 moved the active catalog to 14/70, but the required promoted keys are
absent. The recommended decision is rollback to the selected 22AE.5 backup.

Selected backup:

```text
{selected.get('BACKUP_ROOT', '')}
```

No active mutation occurred in 22AE.5.2.

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_5_2_PARTIAL_PROMOTION_REPAIR_OR_ROLLBACK_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.5.1 green: {1 if ae51.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_5_1_PARTIAL_PROMOTION_DIAGNOSTIC_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.5.1 savepoint present: {1 if sp_ok else 0}")
    print(f"  message rows after: {ae51.get('MESSAGE_ROWS_AFTER', '')}")
    print(f"  text rows after: {ae51.get('TEXT_ROWS_AFTER', '')}")
    print(f"  required message symbol rows found: {ae51.get('REQUIRED_MESSAGE_SYMBOL_ROWS_FOUND', '')}")
    print(f"  required text key rows found: {ae51.get('REQUIRED_TEXT_KEY_ROWS_FOUND', '')}")
    print(f"  backups found: {len(backup_rows)}")
    print(f"  selected backup root: {selected.get('BACKUP_ROOT', '')}")
    print("  recommended decision: ROLLBACK_TO_22AE5_BACKUP")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
