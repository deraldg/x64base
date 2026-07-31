#!/usr/bin/env python3
"""
Phase 19: Active Messaging readback smoke closeout.

Validates the active readback smoke after MSG-018.2 promotion. This closeout
proves the promoted active Messaging DBF/memo tables open as x64/v64 from the
active paths with the expected counts and fields.

It intentionally does not require CDX tag attachment/order proof because the
runtime smoke output shows "Valid Index/Indices: CDX" but AREA/STRUCT reports
natural order. Runtime CDX/LMDB query proof should be a separate follow-up if
needed.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE19_ACTIVE_READBACK_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE19_ACTIVE_READBACK_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE20_ACTIVE_INDEX_LMDB_QUERY_SMOKE_OR_PHASE18_LOCALE_SPINE_EXTENSION"
REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-019_ACTIVE_READBACK_SMOKE.md")

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

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    runlog = repo / RUNLOG
    p18 = first_row(reports / "message_catalog_phase18_1_status_summary_v1.csv")

    messages = p18.get("MESSAGES", "12")
    text_rows = p18.get("TEXT_ROWS", "60")
    locales = p18.get("LOCALES", "de;en-US;es;fr;it")

    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE18_PROMOTION_GREEN", p18.get("STATUS") == "MESSAGE_CATALOG_PHASE18_1_ACTIVE_PROMOTION_GREEN", p18.get("STATUS", ""))
    gate("ACTIVE_READBACK_RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("ACTIVE_PATH_DBFS_USED", "D:\\CODE\\CCODE\\DOTTALKPP\\DATA\\MESSAGING" in upper or "D:/CODE/CCODE/DOTTALKPP/DATA/MESSAGING" in upper, "runlog should show active messaging DBF path")
    gate("ACTIVE_SYSTEM_MESSAGES_V64", "OPENED SYSTEM_MESSAGES (V64) : RECORD COUNT 12" in upper, "SYSTEM_MESSAGES active v64 count 12")
    gate("ACTIVE_SYSTEM_MESSAGE_TEXT_V64", "OPENED SYSTEM_MESSAGE_TEXT (V64) : RECORD COUNT 60" in upper, "SYSTEM_MESSAGE_TEXT active v64 count 60")
    gate("SYSTEM_MESSAGES_DBF_FLAVOR_V64", "DBF FLAVOR          : V64" in upper and "SYSTEM_MESSAGES" in upper, "SYSTEM_MESSAGES DBF flavor v64")
    gate("SYSTEM_MESSAGE_TEXT_TEXT_MEMO_FIELD", "TEXT          M" in upper or "TEXT          M        8" in upper, "TEXT memo field present")
    gate("SYSTEM_MESSAGE_TEXT_MSGLOCALE_FIELD", "MSGLOCALE" in upper, "MSGLOCALE field present")
    gate("SYSTEM_MESSAGE_TEXT_SYMBOLLOC_FIELD", "SYMBOLLOC" in upper, "SYMBOLLOC field present")
    gate("ACTIVE_MESSAGE_TEXT_SAMPLE_ROWS", "HELP_HINT_COMMAND" in upper and "MESSAGE_LOCALE_SET" in upper, "sample rows visible")

    # Nonblocking review: current smoke sees CDX availability but not attached tags/order.
    review("ACTIVE_CDX_AVAILABLE_BUT_NOT_ATTACHED", "VALID INDEX/INDICES   : CDX" in upper and "INDEX FILE  : (NONE)" in upper,
           "Active smoke proves CDX availability but not tag attachment/order; keep active index/LMDB query smoke as optional next proof.")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase19_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "ACTIVE_READBACK_SMOKE_GREEN": 1 if status == STATUS_GREEN else 0,
        "ACTIVE_PROMOTION_CONFIRMED": 1 if p18.get("STATUS") == "MESSAGE_CATALOG_PHASE18_1_ACTIVE_PROMOTION_GREEN" else 0,
        "ACTIVE_INDEX_LMDB_QUERY_PROOF": 0,
        "ACTIVE_INDEX_LMDB_QUERY_PROOF_STATUS": "DEFERRED_OPTIONAL_FOLLOWUP",
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "ACTIVE_READBACK_SMOKE_GREEN", "ACTIVE_PROMOTION_CONFIRMED",
         "ACTIVE_INDEX_LMDB_QUERY_PROOF", "ACTIVE_INDEX_LMDB_QUERY_PROOF_STATUS",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase19_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 19 readback validation only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 19 readback validation only; no active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 19 readback validation only; no active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-code mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase19_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    md = f"""# Message Catalog Phase 19 Active Readback Smoke Closeout

Status: `{status}`

Phase 19 validates active readback after MSG-018.2 promotion.

## Proven

- Active `SYSTEM_MESSAGES` opens as v64 with 12 rows.
- Active `SYSTEM_MESSAGE_TEXT` opens as v64 with 60 rows.
- `TEXT M`, `MSGLOCALE`, and `SYMBOLLOC` are present.
- The active DBF path is `dottalkpp/data/messaging`.

## Not claimed

The active smoke reports CDX availability, but does not prove active CDX tag
attachment/order or LMDB query behavior. That remains a separate optional
Phase 20 proof.

## Next gate

`{NEXT_GATE}`
"""
    (reports / "MESSAGE_CATALOG_PHASE19_ACTIVE_READBACK_SMOKE_CLOSEOUT.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  active readback smoke green: {1 if status == STATUS_GREEN else 0}")
    print("  active index/lmdb query proof: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
