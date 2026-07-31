#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_APPLIED = "LOCALE_PHASE23P_MSGMGR_SCHEMA_STATUS_SOURCE_PATCH_APPLIED_BUILD_HELD"
STATUS_BLOCKED = "LOCALE_PHASE23P_MSGMGR_SCHEMA_STATUS_SOURCE_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_MSGMGR_SCHEMA_STATUS_SMOKE_THEN_VALIDATE"
REPORT_DIR = Path("docs/locale/reports")
BACKUP_ROOT = Path("docs/locale/backups")

CMD_MSGMGR = Path("src/cli/cmd_msgmgr.cpp")
SMOKE = Path("docs/locale/scripts/LOCALE_PHASE23P_MSGMGR_SCHEMA_STATUS_SMOKE.dts")
ACTIVE_LOCALE_SCHEMA = Path("dottalkpp/data/schemas/locale/locale_spine.dtschema")

SCHEMA_INSERT_AFTER = '        << "  locale spine         : scaffold present; runtime status wiring held\\n"'
SCHEMA_LINES = '        << "  schema root          : dottalkpp/data/schemas\\n"\n        << "  locale schema        : dottalkpp/data/schemas/locale/locale_spine.dtschema\\n"\n        << "  messaging schema     : held; field/tag reconciliation pending\\n"'
SMOKE_TEXT = '* LOCALE_PHASE23P_MSGMGR_SCHEMA_STATUS_SMOKE.dts\n* MSGMGR schema-status reporting smoke.\n* Boundary: read-only command status; no DBF/CDX/LMDB mutation.\n\nMSGMGR STATUS\nMSGMGR CHECK\n\n'

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

def backup_file(path: Path, backup_root: Path, repo: Path, rows: list[dict[str, Any]]) -> None:
    if not path.exists():
        return
    dest = backup_root / rel(path, repo)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    rows.append({
        "SOURCE_PATH": rel(path, repo),
        "BACKUP_PATH": rel(dest, repo),
        "BYTES": dest.stat().st_size,
        "SHA256": sha256_file(dest),
        "ACTION": "BACKUP_EXISTING_FILE",
    })

def patch_cmd_msgmgr(text: str) -> tuple[str, str]:
    if "schema root          : dottalkpp/data/schemas" in text:
        return text, "already_present"
    if SCHEMA_INSERT_AFTER not in text:
        return text, "anchor_missing"
    return text.replace(SCHEMA_INSERT_AFTER, SCHEMA_INSERT_AFTER + "\n" + SCHEMA_LINES, 1), "inserted_after_locale_spine_status"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23o = first_row(reports / "locale_phase23o_validation_status_summary_v1.csv")
    phase23l = first_row(reports / "locale_phase23l_msgmgr_status_summary_v1.csv")

    cmd = repo / CMD_MSGMGR
    smoke = repo / SMOKE
    active_schema = repo / ACTIVE_LOCALE_SCHEMA

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_ALLOWED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE23O_ACTIVE_SCHEMA_VALIDATED_GREEN", phase23o.get("STATUS") == "LOCALE_PHASE23O_ACTIVE_LOCALE_SCHEMA_CONTRACT_VALIDATED_GREEN", phase23o.get("STATUS", ""))
    gate("PHASE23O_VALIDATION_ZERO", phase23o.get("VALIDATION_ISSUES", "") == "0", f"validation_issues={phase23o.get('VALIDATION_ISSUES', '')}")
    gate("ACTIVE_LOCALE_SCHEMA_PRESENT", active_schema.exists(), rel(active_schema, repo))
    gate("PHASE23L_MSGMGR_BUILD_SMOKE_GREEN", phase23l.get("STATUS") == "LOCALE_PHASE23L_MSGMGR_HOUSE_COMMAND_BUILD_SMOKE_GREEN", phase23l.get("STATUS", ""))
    gate("CMD_MSGMGR_PRESENT", cmd.exists(), rel(cmd, repo))

    mutation_rows: list[dict[str, Any]] = []
    backup_rows: list[dict[str, Any]] = []
    patch_status = "not_attempted"
    status = STATUS_BLOCKED

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = repo / BACKUP_ROOT / f"LOC-023P_MSGMGR_SCHEMA_STATUS_BACKUP_{timestamp}"

    if failures == 0:
        backup_file(cmd, backup_root, repo, backup_rows)
        backup_file(smoke, backup_root, repo, backup_rows)

        original = cmd.read_text(encoding="utf-8", errors="replace")
        patched, patch_status = patch_cmd_msgmgr(original)
        if patch_status == "anchor_missing":
            failures += 1
        else:
            if patched != original:
                cmd.write_text(patched, encoding="utf-8", newline="\n")
                mutation_rows.append({
                    "TARGET_PATH": rel(cmd, repo),
                    "ACTION": f"UPDATE_MSGMGR_STATUS_{patch_status}",
                    "BYTES": cmd.stat().st_size,
                    "SHA256": sha256_file(cmd),
                })

            smoke.parent.mkdir(parents=True, exist_ok=True)
            smoke.write_text(SMOKE_TEXT, encoding="utf-8", newline="\n")
            mutation_rows.append({
                "TARGET_PATH": rel(smoke, repo),
                "ACTION": "CREATE_OR_REPLACE_SCHEMA_STATUS_SMOKE",
                "BYTES": smoke.stat().st_size,
                "SHA256": sha256_file(smoke),
            })

            status = STATUS_APPLIED

    validation_issues = "0" if status == STATUS_APPLIED else str(failures)

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("src/")]), "DETAIL": "Authorized narrow MSGMGR STATUS text wiring only."},
        {"PROTECTED_SYSTEM": "DOCS_LOCALE_SCRIPT", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("docs/")]), "DETAIL": "Runtime smoke script staged."},
        {"PROTECTED_SYSTEM": "ACTIVE_SCHEMA_CONTRACTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active schema mutation; report existing promoted locale schema path only."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "BUILD_RUNTIME", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No build/runtime execution by apply package."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    write_csv(reports / "locale_phase23p_msgmgr_schema_status_apply_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("src/")]),
        "DOCS_LOCALE_FILES_MUTATED": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("docs/")]),
        "BACKUP_ROWS": len(backup_rows),
        "PATCH_STATUS": patch_status,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "DOCS_LOCALE_FILES_MUTATED", "BACKUP_ROWS", "PATCH_STATUS", "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23p_msgmgr_schema_status_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23p_msgmgr_schema_status_mutation_inventory_v1.csv", mutation_rows, ["TARGET_PATH", "ACTION", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23p_msgmgr_schema_status_backup_inventory_v1.csv", backup_rows, ["SOURCE_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ACTION"])
    write_csv(reports / "locale_phase23p_msgmgr_schema_status_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    doc = repo / "docs/locale/LOCALE_PHASE23P_MSGMGR_SCHEMA_STATUS.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(f"""# Locale Phase 23P — MSGMGR Schema Status Reporting

Status: `{status}`

This phase wires `MSGMGR STATUS` text to report the promoted active locale
schema contract path:

```text
dottalkpp/data/schemas/locale/locale_spine.dtschema
```

Messaging schema remains held:

```text
dottalkpp/data/schemas/messaging/message_catalog.dtschema
```

Boundary: source text/status wiring only. No active schema, DBF, CDX, LMDB,
HELP, CMDHELPCHK, manualgen, Data Dictionary, or SelfDoc mutation.

Next gate:

```text
{NEXT_GATE}
```
""", encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len([r for r in mutation_rows if r['TARGET_PATH'].startswith('src/')])}")
    print(f"  docs locale files mutated: {len([r for r in mutation_rows if r['TARGET_PATH'].startswith('docs/')])}")
    print(f"  backup rows: {len(backup_rows)}")
    print(f"  patch status: {patch_status}")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_APPLIED else 2

if __name__ == "__main__":
    raise SystemExit(main())
