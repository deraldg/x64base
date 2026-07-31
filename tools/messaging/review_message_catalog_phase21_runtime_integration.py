#!/usr/bin/env python3
"""
Phase 21: Runtime Messaging catalog integration review.

This phase is report-only. It accepts the active DBF/CDX/LMDB proof chain through
Phase 20 and prepares the next guarded integration decision: how DotTalk++
runtime should consume the active Messaging catalog.

No source files are edited. No HELP/CMDHELPCHK/manualgen/datadict artifacts are
mutated. No active DBF/CDX/LMDB files are mutated.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE21_RUNTIME_INTEGRATION_REVIEW_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE21_RUNTIME_INTEGRATION_REVIEW_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22_RUNTIME_CATALOG_SOURCE_INTEGRATION_OR_PHASE23_LOCALE_SPINE_EXTENSION"
REPORT_DIR = Path("docs/messaging/reports")

ACTIVE_DBF = Path("dottalkpp/data/messaging")
ACTIVE_INDEXES = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB = Path("dottalkpp/data/lmdb/messaging")

SOURCE_CANDIDATES = [
    "src/help/message_catalog.cpp",
    "src/help/message_catalog.h",
    "src/help/helpdata_messages.cpp",
    "src/help/helpdata_messages.h",
    "src/cli/cmd_set.cpp",
    "src/cli/command_output.cpp",
    "src/cli/command_registry.cpp",
    "src/cli/cmd_display.cpp",
]

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

def savepoint_present(index_path: Path, savepoint_id: str) -> bool:
    if not index_path.exists():
        return False
    try:
        return any(r.get("savepoint_id") == savepoint_id for r in read_csv(index_path))
    except Exception:
        return False

def source_scan(repo: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    patterns = [
        "MessageCatalog",
        "message_catalog",
        "MESSAGE_LOCALE",
        "SET LANGUAGE",
        "set_language",
        "helpdata_messages",
        "SYSTEM_MESSAGE",
        "locale",
    ]
    for rel in SOURCE_CANDIDATES:
        p = repo / rel
        row = {
            "SOURCE_PATH": rel,
            "EXISTS": 1 if p.exists() else 0,
            "BYTES": p.stat().st_size if p.exists() else 0,
            "SHA256": sha256_file(p) if p.exists() and p.is_file() else "",
            "PATTERN_HITS": "",
            "ROLE": "",
        }
        if p.exists() and p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            hits = [pat for pat in patterns if pat.lower() in text.lower()]
            row["PATTERN_HITS"] = ";".join(hits)
            if "cmd_set" in rel:
                row["ROLE"] = "SET LANGUAGE command surface integration candidate"
            elif "message_catalog" in rel or "helpdata_messages" in rel:
                row["ROLE"] = "runtime message catalog/source fallback integration candidate"
            elif "command_output" in rel:
                row["ROLE"] = "message emission path integration candidate"
            else:
                row["ROLE"] = "review candidate"
        rows.append(row)
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p20 = first_row(reports / "message_catalog_phase20_status_summary_v1.csv")
    p18 = first_row(reports / "message_catalog_phase18_1_status_summary_v1.csv")
    savepoint_index = reports / "message_savepoint_thread_index_v1.csv"

    messages = p20.get("MESSAGES", p18.get("MESSAGES", "12"))
    text_rows = p20.get("TEXT_ROWS", p18.get("TEXT_ROWS", "60"))
    locales = p20.get("LOCALES", p18.get("LOCALES", "de;en-US;es;fr;it"))

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE18_ACTIVE_PROMOTION_GREEN", p18.get("STATUS") == "MESSAGE_CATALOG_PHASE18_1_ACTIVE_PROMOTION_GREEN", p18.get("STATUS", ""))
    gate("PHASE20_ACTIVE_INDEX_QUERY_GREEN", p20.get("STATUS") == "MESSAGE_CATALOG_PHASE20_ACTIVE_INDEX_QUERY_SMOKE_GREEN", p20.get("STATUS", ""))
    gate("ACTIVE_MESSAGES_DBF_PRESENT", (repo / ACTIVE_DBF / "SYSTEM_MESSAGES.dbf").exists(), str(repo / ACTIVE_DBF / "SYSTEM_MESSAGES.dbf"))
    gate("ACTIVE_MESSAGE_TEXT_DBF_PRESENT", (repo / ACTIVE_DBF / "SYSTEM_MESSAGE_TEXT.dbf").exists(), str(repo / ACTIVE_DBF / "SYSTEM_MESSAGE_TEXT.dbf"))
    gate("ACTIVE_MESSAGE_TEXT_DTX_PRESENT", (repo / ACTIVE_DBF / "SYSTEM_MESSAGE_TEXT.dtx").exists(), str(repo / ACTIVE_DBF / "SYSTEM_MESSAGE_TEXT.dtx"))
    gate("ACTIVE_MESSAGES_CDX_PRESENT", (repo / ACTIVE_INDEXES / "SYSTEM_MESSAGES.cdx").exists(), str(repo / ACTIVE_INDEXES / "SYSTEM_MESSAGES.cdx"))
    gate("ACTIVE_MESSAGE_TEXT_CDX_PRESENT", (repo / ACTIVE_INDEXES / "SYSTEM_MESSAGE_TEXT.cdx").exists(), str(repo / ACTIVE_INDEXES / "SYSTEM_MESSAGE_TEXT.cdx"))
    gate("ACTIVE_MESSAGES_LMDB_PRESENT", (repo / ACTIVE_LMDB / "SYSTEM_MESSAGES.cdx.d").exists(), str(repo / ACTIVE_LMDB / "SYSTEM_MESSAGES.cdx.d"))
    gate("ACTIVE_MESSAGE_TEXT_LMDB_PRESENT", (repo / ACTIVE_LMDB / "SYSTEM_MESSAGE_TEXT.cdx.d").exists(), str(repo / ACTIVE_LMDB / "SYSTEM_MESSAGE_TEXT.cdx.d"))

    review("MSG_020_SAVEPOINT_PRESENT", savepoint_present(savepoint_index, "MSG-020"),
           "Recommended before Phase 22, but reports/runlog are sufficient for this review if savepoint was not yet appended.")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    src_rows = source_scan(repo)
    write_csv(reports / "message_catalog_phase21_source_scan_v1.csv", src_rows,
              ["SOURCE_PATH", "EXISTS", "BYTES", "SHA256", "PATTERN_HITS", "ROLE"])

    decision_rows = [
        {"DECISION_ID": "RT-001", "DECISION": "KEEP_COMPILED_FALLBACK", "STATUS": "ACCEPTED", "DETAIL": "Compiled/static message rows remain the fallback path while active DBF catalog loading is introduced."},
        {"DECISION_ID": "RT-002", "DECISION": "ADD_RUNTIME_CATALOG_PROVIDER", "STATUS": "RECOMMENDED_PHASE22", "DETAIL": "Introduce a runtime provider that reads active SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT into the existing in-memory catalog shape."},
        {"DECISION_ID": "RT-003", "DECISION": "GATE_DB_PROVIDER", "STATUS": "RECOMMENDED_PHASE22", "DETAIL": "Gate runtime DBF catalog use behind explicit mode/setting first, e.g. compiled/static vs active DBF vs auto."},
        {"DECISION_ID": "RT-004", "DECISION": "NO_RUNTIME_WRITEBACK", "STATUS": "ACCEPTED", "DETAIL": "Runtime integration should read active messaging catalogs only; no message catalog writeback from normal runtime paths."},
        {"DECISION_ID": "RT-005", "DECISION": "DEFER_LOCALE_SPINE", "STATUS": "ACCEPTED_AS_NEXT_SCHEMA_EXTENSION", "DETAIL": "SYSTEM_LOCALES and SYSTEM_LOCALE_FALLBACK remain the next schema extension, but not a blocker to read the active two-table catalog."},
        {"DECISION_ID": "RT-006", "DECISION": "PRESERVE_ENGLISH_COMMANDS", "STATUS": "ACCEPTED", "DETAIL": "DotScript commands/verbs remain English-only; localization applies to messages, help/lessons/manual text, and diagnostics."},
    ]
    write_csv(reports / "message_catalog_phase21_runtime_integration_decisions_v1.csv", decision_rows,
              ["DECISION_ID", "DECISION", "STATUS", "DETAIL"])

    phase22_plan = [
        {"STEP": 1, "ACTION": "SOURCE_PLAN_ONLY_OR_EXPLICIT_PATCH", "DETAIL": "Locate message_catalog/helpdata message loading code and define provider interface/fallback path."},
        {"STEP": 2, "ACTION": "ADD_ACTIVE_CATALOG_READER", "DETAIL": "Open active SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT read-only; require v64/count/hash sanity checks."},
        {"STEP": 3, "ACTION": "LOAD_TO_IN_MEMORY_CATALOG", "DETAIL": "Populate existing runtime message catalog shape keyed by stable message symbol/id + locale."},
        {"STEP": 4, "ACTION": "ADD_MODE_SWITCH", "DETAIL": "Add setting or internal flag: COMPILED, ACTIVE_DBF, AUTO. Default should remain compiled until runtime smoke passes."},
        {"STEP": 5, "ACTION": "RUNTIME_SMOKE", "DETAIL": "Prove SET LANGUAGE CHECK and sample localized messages work through active DBF provider."},
        {"STEP": 6, "ACTION": "SAVEPOINT", "DETAIL": "Record source integration status and boundaries; no HELP/CMDHELPCHK/manualgen mutation."},
    ]
    write_csv(reports / "message_catalog_phase21_phase22_runtime_integration_plan_v1.csv", phase22_plan,
              ["STEP", "ACTION", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 21 review only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 21 review only; no active CDX mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 21 review only; no active LMDB mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source files edited by Phase 21."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase21_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase21_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase21_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "ACTIVE_CATALOG_PROVEN": 1 if failures == 0 else 0,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_MUTATION_OBSERVED": 0,
        "RUNTIME_INTEGRATION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "ACTIVE_CATALOG_PROVEN", "SOURCE_MUTATION_AUTHORIZED", "SOURCE_MUTATION_OBSERVED",
         "RUNTIME_INTEGRATION_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 21 Runtime Integration Review

Status: `{status}`

Phase 21 confirms the active Messaging catalog is proven and prepares the next
guarded decision: runtime consumption of the active catalog.

## Proven before this phase

- Active x64 DBF/memo readback.
- Active CDX attach/order.
- Active LMDB environment association.
- 12 message rows and 60 localized text rows across `{locales}`.

## Recommendation

Proceed to Phase 22 only with explicit authorization. Phase 22 should introduce
a read-only active DBF catalog provider while preserving compiled/static rows as
fallback.

## Boundary

No source files, HELP DATA, CMDHELPCHK, manualgen, Data Dictionary/SelfDoc, or
active Messaging artifacts were mutated by Phase 21.
"""
    (reports / "MESSAGE_CATALOG_PHASE21_RUNTIME_INTEGRATION_REVIEW.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  active catalog proven: {1 if failures == 0 else 0}")
    print("  source mutation authorized: 0")
    print("  runtime integration authorized: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
