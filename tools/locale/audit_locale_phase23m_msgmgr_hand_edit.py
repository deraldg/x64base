#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23M_MSGMGR_HAND_EDIT_AND_SAVEPOINT_AUDIT_GREEN_REPORT_ONLY"
STATUS_BLOCKED = "LOCALE_PHASE23M_MSGMGR_HAND_EDIT_AND_SAVEPOINT_AUDIT_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_MSGMGR_RUNTIME_STATUS_WIRING"

REPORT_DIR = Path("docs/locale/reports")
SAVEPOINT_INDEX = REPORT_DIR / "locale_savepoint_thread_index_v1.csv"
SAVEPOINT_LATEST = REPORT_DIR / "locale_savepoint_latest_v1.json"
SHELL_COMMANDS = Path("src/cli/shell_commands.cpp")
CMD_MSGMGR = Path("src/cli/cmd_msgmgr.cpp")

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

def extract_evidence_lines(path: Path, terms: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines, start=1):
        upper = line.upper()
        for term in terms:
            if term.upper() in upper:
                rows.append({
                    "SOURCE_PATH": str(path),
                    "LINE_NO": i,
                    "MATCH_TERM": term,
                    "LINE_TEXT": line.strip()[:240],
                })
                break
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-report-only-audit", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23l = first_row(reports / "locale_phase23l_msgmgr_status_summary_v1.csv")
    apply23l = first_row(reports / "locale_phase23l_msgmgr_apply_status_summary_v1.csv")
    savepoint_rows = read_csv(repo / SAVEPOINT_INDEX)
    latest = {}
    if (repo / SAVEPOINT_LATEST).exists():
        try:
            latest = json.loads((repo / SAVEPOINT_LATEST).read_text(encoding="utf-8"))
        except Exception:
            latest = {}

    shell_path = repo / SHELL_COMMANDS
    cmd_path = repo / CMD_MSGMGR
    shell_text = shell_path.read_text(encoding="utf-8", errors="replace") if shell_path.exists() else ""
    cmd_text = cmd_path.read_text(encoding="utf-8", errors="replace") if cmd_path.exists() else ""

    msgmgr_index_rows = [r for r in savepoint_rows if r.get("savepoint_id") == "LOC-023L-MSGMGR"]
    duplicate_count = max(0, len(msgmgr_index_rows) - 1)

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("OPERATOR_ACCEPTED_REPORT_ONLY_AUDIT",
         args.accept_report_only_audit,
         "requires --accept-report-only-audit")
    gate("PHASE23L_MSGMGR_VALIDATION_GREEN",
         phase23l.get("STATUS") == "LOCALE_PHASE23L_MSGMGR_HOUSE_COMMAND_BUILD_SMOKE_GREEN",
         phase23l.get("STATUS", ""))
    gate("PHASE23L_MSGMGR_VALIDATION_ZERO",
         phase23l.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23l.get('VALIDATION_ISSUES', '')}")
    gate("CMD_MSGMGR_SOURCE_PRESENT",
         cmd_path.exists(),
         rel(cmd_path, repo))
    gate("CMD_MSGMGR_USAGE_CONTRACT_PRESENT",
         "@dottalk.usage v1" in cmd_text and "command: MSGMGR" in cmd_text,
         "cmd_msgmgr.cpp should retain usage contract")
    gate("SHELL_COMMANDS_PRESENT",
         shell_path.exists(),
         rel(shell_path, repo))
    gate("SHELL_MSGMGR_IDENTIFIER_PRESENT",
         "cmd_MSGMGR" in shell_text,
         "manual identifier/prototype/registration visibility for cmd_MSGMGR")
    gate("SHELL_MSGMGR_COMMAND_STRING_PRESENT",
         "MSGMGR" in shell_text,
         "MSGMGR command string should be present in shell registration")
    gate("LOC_023L_MSGMGR_SAVEPOINT_PRESENT",
         len(msgmgr_index_rows) >= 1,
         f"LOC-023L-MSGMGR rows={len(msgmgr_index_rows)}")
    review("LOC_023L_MSGMGR_DUPLICATE_ACCOUNTING",
           len(msgmgr_index_rows) <= 1,
           f"duplicate rows={duplicate_count}; nonblocking duplicate-savepoint accounting item")
    review("LATEST_SAVEPOINT_IS_LOC_023L_MSGMGR_OR_LATER",
           latest.get("savepoint_id") in ("LOC-023L-MSGMGR", "LOC-023M-MSGMGR-AUDIT"),
           f"latest_savepoint={latest.get('savepoint_id', '')}")

    shell_evidence = extract_evidence_lines(shell_path, ["cmd_MSGMGR", "MSGMGR"])
    cmd_evidence = extract_evidence_lines(cmd_path, ["@dottalk.usage v1", "command: MSGMGR", "cmd_MSGMGR", "MSGMGR STATUS"])

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    duplicate_rows = []
    for row in msgmgr_index_rows:
        duplicate_rows.append({
            "timestamp_utc": row.get("timestamp_utc", ""),
            "savepoint_id": row.get("savepoint_id", ""),
            "lane": row.get("lane", ""),
            "status": row.get("status", ""),
            "DUPLICATE_GROUP": "LOC-023L-MSGMGR",
            "ACCOUNTING_STATUS": "KEEP_NONBLOCKING_DUPLICATE" if duplicate_count else "UNIQUE",
        })

    hand_edit_acceptance = [
        {
            "ITEM": "shell_commands.cpp hand identifier/registration repair",
            "STATUS": "ACCEPTED_AS_BUILD_REQUIRED",
            "DETAIL": "Initial generated patch registered MSGMGR lambda but missed visible cmd_MSGMGR identifier/prototype path; user hand edit repaired central shell registration and build passed.",
        },
        {
            "ITEM": "cmd_msgmgr.cpp usage contract",
            "STATUS": "ACCEPTED",
            "DETAIL": "Command file includes @dottalk.usage v1 contract and read-only MSGMGR house behavior.",
        },
        {
            "ITEM": "duplicate LOC-023L-MSGMGR savepoint rows",
            "STATUS": "NONBLOCKING_ACCOUNTING_DUPLICATE",
            "DETAIL": "Two green rows exist in locale_savepoint_thread_index_v1.csv; do not hand-edit journal; future append scripts should be duplicate-aware.",
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "23M audit only; no source mutation."},
        {"PROTECTED_SYSTEM": "BUILD", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No build execution."},
        {"PROTECTED_SYSTEM": "RUNTIME", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No runtime execution."},
        {"PROTECTED_SYSTEM": "LOCALE_SAVEPOINT_JOURNAL", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Audit does not edit prior duplicate journal/index rows."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active locale DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    summary = [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "REPORT_ONLY_AUDIT": 1,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SHELL_MSGMGR_IDENTIFIER_PRESENT": 1 if "cmd_MSGMGR" in shell_text else 0,
        "SHELL_MSGMGR_COMMAND_STRING_PRESENT": 1 if "MSGMGR" in shell_text else 0,
        "CMD_MSGMGR_USAGE_CONTRACT_PRESENT": 1 if "@dottalk.usage v1" in cmd_text and "command: MSGMGR" in cmd_text else 0,
        "LOC_023L_MSGMGR_SAVEPOINT_ROWS": len(msgmgr_index_rows),
        "LOC_023L_MSGMGR_DUPLICATE_ROWS": duplicate_count,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }]

    write_csv(reports / "locale_phase23m_msgmgr_audit_status_summary_v1.csv", summary,
              ["STATUS", "VALIDATION_ISSUES", "REPORT_ONLY_AUDIT", "SOURCE_MUTATION_AUTHORIZED",
               "SHELL_MSGMGR_IDENTIFIER_PRESENT", "SHELL_MSGMGR_COMMAND_STRING_PRESENT",
               "CMD_MSGMGR_USAGE_CONTRACT_PRESENT", "LOC_023L_MSGMGR_SAVEPOINT_ROWS",
               "LOC_023L_MSGMGR_DUPLICATE_ROWS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])
    write_csv(reports / "locale_phase23m_msgmgr_audit_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23m_msgmgr_shell_evidence_v1.csv", shell_evidence,
              ["SOURCE_PATH", "LINE_NO", "MATCH_TERM", "LINE_TEXT"])
    write_csv(reports / "locale_phase23m_msgmgr_cmd_evidence_v1.csv", cmd_evidence,
              ["SOURCE_PATH", "LINE_NO", "MATCH_TERM", "LINE_TEXT"])
    write_csv(reports / "locale_phase23m_msgmgr_hand_edit_acceptance_v1.csv", hand_edit_acceptance,
              ["ITEM", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23m_msgmgr_duplicate_savepoint_review_v1.csv", duplicate_rows,
              ["timestamp_utc", "savepoint_id", "lane", "status", "DUPLICATE_GROUP", "ACCOUNTING_STATUS"])
    write_csv(reports / "locale_phase23m_msgmgr_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    plan_path = repo / "docs/locale/LOCALE_PHASE23M_MSGMGR_HAND_EDIT_AND_SAVEPOINT_AUDIT.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(f"""# Locale Phase 23M — MSGMGR Hand Edit and Savepoint Audit

Status: `{status}`

This report-only audit accepts the user hand edit in `src/cli/shell_commands.cpp`
as the required central-shell identifier/registration repair for `cmd_MSGMGR`.

It also records the duplicate `LOC-023L-MSGMGR` savepoint rows as a nonblocking
accounting issue. The journal is not edited by this audit.

## Next gate

```text
{NEXT_GATE}
```
""", encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print("  report-only audit: 1")
    print("  source mutation authorized: 0")
    print(f"  shell cmd_MSGMGR identifier present: {1 if 'cmd_MSGMGR' in shell_text else 0}")
    print(f"  shell MSGMGR command string present: {1 if 'MSGMGR' in shell_text else 0}")
    print(f"  cmd_msgmgr usage contract present: {1 if '@dottalk.usage v1' in cmd_text and 'command: MSGMGR' in cmd_text else 0}")
    print(f"  LOC-023L-MSGMGR savepoint rows: {len(msgmgr_index_rows)}")
    print(f"  LOC-023L-MSGMGR duplicate rows: {duplicate_count}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
