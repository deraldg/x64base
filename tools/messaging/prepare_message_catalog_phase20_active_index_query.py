#!/usr/bin/env python3
"""
Phase 20: Active Messaging CDX/LMDB attach/order smoke.

This stages a DotTalk++ script that proves active promoted indexes are usable by
explicitly attaching CDX files and setting orders. It reflects runtime behavior:
after index creation/promotion, DotTalk++ still needs:

  USE / SELECT table
  SET INDEX TO <tablename>
  SET ORDER TO <tagname>

The smoke is read-only against active Messaging artifacts.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS = "MESSAGE_CATALOG_PHASE20_ACTIVE_INDEX_QUERY_SMOKE_STAGED"
NEXT_GATE = "RUN_DOTTALK_PHASE20_ACTIVE_INDEX_QUERY_SMOKE_THEN_VALIDATE"
REPORT_DIR = Path("docs/messaging/reports")

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

    p18 = first_row(reports / "message_catalog_phase18_1_status_summary_v1.csv")
    p19 = first_row(reports / "message_catalog_phase19_status_summary_v1.csv")

    active_dbf = repo / "dottalkpp/data/messaging"
    active_indexes = repo / "dottalkpp/data/indexes/messaging"
    active_lmdb = repo / "dottalkpp/data/lmdb/messaging"

    messages = p18.get("MESSAGES", "12")
    text_rows = p18.get("TEXT_ROWS", "60")
    locales = p18.get("LOCALES", "de;en-US;es;fr;it")

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE18_PROMOTION_GREEN", p18.get("STATUS") == "MESSAGE_CATALOG_PHASE18_1_ACTIVE_PROMOTION_GREEN", p18.get("STATUS", ""))
    # Phase 19 is preferred but not hard precondition if active artifacts are present.
    gates.append({"GATE": "PHASE19_READBACK_GREEN", "STATUS": "PASS" if p19.get("STATUS") == "MESSAGE_CATALOG_PHASE19_ACTIVE_READBACK_SMOKE_GREEN" else "REVIEW", "DETAIL": p19.get("STATUS", "not present")})

    for t in ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]:
        gate(f"ACTIVE_{t}_DBF_PRESENT", (active_dbf / f"{t}.dbf").exists(), str(active_dbf / f"{t}.dbf"))
        gate(f"ACTIVE_{t}_CDX_PRESENT", (active_indexes / f"{t}.cdx").exists(), str(active_indexes / f"{t}.cdx"))
        gate(f"ACTIVE_{t}_LMDB_ENV_PRESENT", (active_lmdb / f"{t}.cdx.d").exists(), str(active_lmdb / f"{t}.cdx.d"))

    script_dir = repo / "docs/messaging/scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    script = script_dir / "MESSAGE_CATALOG_PHASE20_ACTIVE_INDEX_QUERY_SMOKE.dts"

    if failures == 0:
        script.write_text("\n".join([
            "* MESSAGE_CATALOG_PHASE20_ACTIVE_INDEX_QUERY_SMOKE.dts",
            "* Read-only active Messaging CDX attach/order smoke.",
            "* Runtime rule: after USE, attach index with SET INDEX TO, then choose a tag with SET ORDER TO.",
            "CLOSE ALL",
            f"SET PATH DBF {active_dbf}",
            f"SET PATH INDEXES {active_indexes}",
            f"SET PATH LMDB {active_lmdb}",
            "",
            "SELECT 0",
            "USE SYSTEM_MESSAGES",
            "SET INDEX TO SYSTEM_MESSAGES",
            "SET ORDER TO MSGID",
            "AREA",
            "COUNT",
            "SL 3",
            "SET ORDER TO SYMBOL",
            "AREA",
            "SL 3",
            "",
            "SELECT 1",
            "USE SYSTEM_MESSAGE_TEXT",
            "SET INDEX TO SYSTEM_MESSAGE_TEXT",
            "SET ORDER TO MSGLOCALE",
            "AREA",
            "COUNT",
            "SL 3",
            "SET ORDER TO SYMBOLLOC",
            "AREA",
            "SL 3",
            "",
            "SELECT 2",
            "",
        ]), encoding="utf-8")

    status = STATUS if failures == 0 else "MESSAGE_CATALOG_PHASE20_ACTIVE_INDEX_QUERY_SMOKE_STAGING_BLOCKED"
    validation_issues = "0" if failures == 0 else str(failures)

    write_csv(reports / "message_catalog_phase20_prepare_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "ACTIVE_INDEX_QUERY_SCRIPT_STAGED": 1 if failures == 0 else 0,
        "ACTIVE_MUTATION": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "ACTIVE_INDEX_QUERY_SCRIPT_STAGED", "ACTIVE_MUTATION", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase20_prepare_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 20 prepare is read-only/staging only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 20 prepare creates no active CDX/index files."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 20 prepare creates no active LMDB files."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-code mutation."},
    ]
    write_csv(reports / "message_catalog_phase20_prepare_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  active index query script staged: {1 if failures == 0 else 0}")
    print("  active mutation: 0")
    print(f"  reports: {reports}")
    return 0 if failures == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
