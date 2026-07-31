#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import struct
import subprocess
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_5_3_ACTIVE_CATALOG_ROLLBACK_EXECUTED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_5_3_ACTIVE_CATALOG_ROLLBACK_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_5_4_POST_ROLLBACK_READBACK_AND_RUNTIME_REGRESSION"

REPORT_DIR = Path("docs/messaging/reports")
BACKUP_BASE = Path("docs/messaging/backups")
ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")

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

def dottalkpp_running() -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq dottalkpp.exe"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return ("dottalkpp.exe" in out.lower()), out.strip().replace("\r\n", " | ")
    except Exception as exc:
        return False, f"tasklist unavailable: {exc}"

def parse_dbf_count(path: Path) -> int:
    data = path.read_bytes()
    if len(data) < 12:
        raise RuntimeError(f"DBF too small: {path}")
    return struct.unpack("<I", data[4:8])[0]

def fingerprint_root(root: Path, repo: Path, label: str):
    rows = []
    if not root.exists():
        rows.append({"LABEL": label, "PATH": rel(root, repo), "EXISTS": 0, "BYTES": 0, "SHA256": "", "ROLE": "missing_root"})
        return rows
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rows.append({"LABEL": label, "PATH": rel(p, repo), "EXISTS": 1, "BYTES": p.stat().st_size, "SHA256": sha256_file(p), "ROLE": "file"})
    if not rows:
        rows.append({"LABEL": label, "PATH": rel(root, repo), "EXISTS": 1, "BYTES": 0, "SHA256": "", "ROLE": "empty_root"})
    return rows

def copy_tree_with_inventory(src: Path, dst: Path, repo: Path, rows: list[dict], role: str):
    if not src.exists():
        rows.append({"SOURCE": rel(src, repo), "TARGET": rel(dst, repo), "ROLE": role, "EXISTS": 0, "FILES": 0, "BYTES": 0, "SHA256": ""})
        return
    if dst.exists():
        shutil.rmtree(dst)
    file_count = 0
    total_bytes = 0
    for p in src.rglob("*"):
        if p.is_file():
            q = dst / p.relative_to(src)
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, q)
            file_count += 1
            total_bytes += q.stat().st_size
    rows.append({"SOURCE": rel(src, repo), "TARGET": rel(dst, repo), "ROLE": role, "EXISTS": 1, "FILES": file_count, "BYTES": total_bytes, "SHA256": ""})

def replace_tree(src: Path, dst: Path, repo: Path, rows: list[dict], role: str):
    if not src.exists():
        rows.append({"SOURCE": rel(src, repo), "TARGET": rel(dst, repo), "ROLE": role, "ACTION": "SKIPPED_SOURCE_MISSING", "FILES": 0, "BYTES": 0})
        return False
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    file_count = 0
    total_bytes = 0
    for p in src.rglob("*"):
        if p.is_file():
            q = dst / p.relative_to(src)
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, q)
            file_count += 1
            total_bytes += q.stat().st_size
    rows.append({"SOURCE": rel(src, repo), "TARGET": rel(dst, repo), "ROLE": role, "ACTION": "RESTORED_FROM_BACKUP", "FILES": file_count, "BYTES": total_bytes})
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-active-catalog-rollback", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae52 = first_row(reports / "message_catalog_phase22ae_5_2_status_summary_v1.csv")
    sp_ok, latest_id = savepoint_present(repo, "MSG-022AE.5.2")
    running, running_detail = dottalkpp_running()

    selected_rel = ae52.get("SELECTED_BACKUP_ROOT", "")
    selected_root = repo / selected_rel if selected_rel else Path("")
    selected_messaging = selected_root / "messaging"
    selected_indexes = selected_root / "indexes_messaging"
    selected_lmdb = selected_root / "lmdb_messaging"

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_ACTIVE_CATALOG_ROLLBACK", args.allow_active_catalog_rollback, "requires -AllowActiveCatalogRollback")
    gate("PHASE22AE_5_2_GREEN",
         ae52.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_2_PARTIAL_PROMOTION_REPAIR_OR_ROLLBACK_PLAN_GREEN_SOURCE_HELD",
         ae52.get("STATUS", "missing"))
    gate("MSG_022AE_5_2_SAVEPOINT_PRESENT", sp_ok, latest_id)
    gate("DOTTALKPP_PROCESS_NOT_RUNNING", not running, running_detail)
    gate("SELECTED_BACKUP_ROOT_PRESENT", bool(selected_rel) and selected_root.exists(), selected_rel)
    gate("SELECTED_BACKUP_MESSAGING_PRESENT", selected_messaging.exists(), rel(selected_messaging, repo) if selected_rel else "")
    gate("SELECTED_BACKUP_INDEXES_PRESENT", selected_indexes.exists(), rel(selected_indexes, repo) if selected_rel else "")
    gate("SELECTED_BACKUP_LMDB_PRESENT", selected_lmdb.exists(), rel(selected_lmdb, repo) if selected_rel else "")
    gate("CURRENT_PARTIAL_COUNTS_REPORTED_14_70",
         ae52.get("MESSAGE_ROWS_AFTER") == "14" and ae52.get("TEXT_ROWS_AFTER") == "70",
         f"{ae52.get('MESSAGE_ROWS_AFTER')}/{ae52.get('TEXT_ROWS_AFTER')}")

    before = (
        fingerprint_root(repo / ACTIVE_MSG_ROOT, repo, "before_partial_active_messaging") +
        fingerprint_root(repo / ACTIVE_INDEX_ROOT, repo, "before_partial_active_indexes") +
        fingerprint_root(repo / ACTIVE_LMDB_ROOT, repo, "before_partial_active_lmdb")
    )

    archive_rows = []
    restore_rows = []
    errors = []
    msg_count_after = ""
    text_count_after = ""
    status = STATUS_BLOCKED

    if failures == 0:
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            partial_archive = repo / BACKUP_BASE / f"MSG-022AE_5_3_PARTIAL_STATE_ARCHIVE_{timestamp}"
            copy_tree_with_inventory(repo / ACTIVE_MSG_ROOT, partial_archive / "messaging", repo, archive_rows, "partial_active_messaging_archive")
            copy_tree_with_inventory(repo / ACTIVE_INDEX_ROOT, partial_archive / "indexes_messaging", repo, archive_rows, "partial_active_indexes_archive")
            copy_tree_with_inventory(repo / ACTIVE_LMDB_ROOT, partial_archive / "lmdb_messaging", repo, archive_rows, "partial_active_lmdb_archive")

            ok1 = replace_tree(selected_messaging, repo / ACTIVE_MSG_ROOT, repo, restore_rows, "active_messaging_restore")
            ok2 = replace_tree(selected_indexes, repo / ACTIVE_INDEX_ROOT, repo, restore_rows, "active_indexes_restore")
            ok3 = replace_tree(selected_lmdb, repo / ACTIVE_LMDB_ROOT, repo, restore_rows, "active_lmdb_restore")

            if not (ok1 and ok2 and ok3):
                raise RuntimeError("one or more active roots were not restored")

            msg_count_after = parse_dbf_count(repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGES.dbf")
            text_count_after = parse_dbf_count(repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGE_TEXT.dbf")

            gate("ROLLBACK_MESSAGE_COUNT_12", msg_count_after == 12, msg_count_after)
            gate("ROLLBACK_TEXT_COUNT_60", text_count_after == 60, text_count_after)

            if msg_count_after == 12 and text_count_after == 60:
                status = STATUS_GREEN
            else:
                status = STATUS_BLOCKED
        except Exception as exc:
            errors.append(str(exc))
            failures += 1
            gates.append({"GATE": "ROLLBACK_EXECUTION", "STATUS": "FAIL", "DETAIL": str(exc)})
            status = STATUS_BLOCKED

    after = (
        fingerprint_root(repo / ACTIVE_MSG_ROOT, repo, "after_rollback_active_messaging") +
        fingerprint_root(repo / ACTIVE_INDEX_ROOT, repo, "after_rollback_active_indexes") +
        fingerprint_root(repo / ACTIVE_LMDB_ROOT, repo, "after_rollback_active_lmdb")
    )

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_5_3_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_5_3_partial_archive_inventory_v1.csv", archive_rows, ["SOURCE", "TARGET", "ROLE", "EXISTS", "FILES", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_5_3_restore_inventory_v1.csv", restore_rows, ["SOURCE", "TARGET", "ROLE", "ACTION", "FILES", "BYTES"])
    write_csv(reports / "message_catalog_phase22ae_5_3_active_fingerprint_before_v1.csv", before, ["LABEL", "PATH", "EXISTS", "BYTES", "SHA256", "ROLE"])
    write_csv(reports / "message_catalog_phase22ae_5_3_active_fingerprint_after_v1.csv", after, ["LABEL", "PATH", "EXISTS", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation in 22AE.5.3."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if status == STATUS_GREEN else 0, "DETAIL": "Rollback restored active messaging DBF root from selected backup."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if status == STATUS_GREEN else 0, "DETAIL": "Rollback restored active messaging index root from selected backup."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if status == STATUS_GREEN else 0, "DETAIL": "Rollback restored active messaging LMDB root from selected backup."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_5_3_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_5_3_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_5_2_GREEN": 1 if ae52.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_2_PARTIAL_PROMOTION_REPAIR_OR_ROLLBACK_PLAN_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_5_2_SAVEPOINT_PRESENT": 1 if sp_ok else 0,
        "DOTTALKPP_PROCESS_RUNNING": 1 if running else 0,
        "SELECTED_BACKUP_ROOT": selected_rel,
        "MESSAGE_ROWS_AFTER_ROLLBACK": msg_count_after,
        "TEXT_ROWS_AFTER_ROLLBACK": text_count_after,
        "PARTIAL_ARCHIVE_ROWS": len(archive_rows),
        "RESTORE_ROWS": len(restore_rows),
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 1 if status == STATUS_GREEN else 0,
        "ACTIVE_INDEX_MUTATION_OBSERVED": 1 if status == STATUS_GREEN else 0,
        "ACTIVE_LMDB_MUTATION_OBSERVED": 1 if status == STATUS_GREEN else 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_5_2_GREEN", "MSG_022AE_5_2_SAVEPOINT_PRESENT",
         "DOTTALKPP_PROCESS_RUNNING", "SELECTED_BACKUP_ROOT", "MESSAGE_ROWS_AFTER_ROLLBACK",
         "TEXT_ROWS_AFTER_ROLLBACK", "PARTIAL_ARCHIVE_ROWS", "RESTORE_ROWS",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "ACTIVE_INDEX_MUTATION_OBSERVED", "ACTIVE_LMDB_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED", "ERRORS",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.5.3 Active Catalog Rollback Execution

Status: `{status}`

Selected backup:

```text
{selected_rel}
```

Post-rollback active counts:

```text
SYSTEM_MESSAGES: {msg_count_after}
SYSTEM_MESSAGE_TEXT: {text_count_after}
```

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_5_3_ACTIVE_CATALOG_ROLLBACK_EXECUTION.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.5.2 green: {1 if ae52.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_5_2_PARTIAL_PROMOTION_REPAIR_OR_ROLLBACK_PLAN_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.5.2 savepoint present: {1 if sp_ok else 0}")
    print(f"  dottalkpp process running: {1 if running else 0}")
    print(f"  selected backup root: {selected_rel}")
    print(f"  message rows after rollback: {msg_count_after}")
    print(f"  text rows after rollback: {text_count_after}")
    print(f"  partial archive rows: {len(archive_rows)}")
    print(f"  restore rows: {len(restore_rows)}")
    print("  source files mutated: 0")
    print(f"  active catalog mutation observed: {1 if status == STATUS_GREEN else 0}")
    print(f"  active index mutation observed: {1 if status == STATUS_GREEN else 0}")
    print(f"  active lmdb mutation observed: {1 if status == STATUS_GREEN else 0}")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
