#!/usr/bin/env python3
"""
Phase 17: Messaging promotion-readiness and schema-scope review.

This phase does not promote active catalogs. It reviews the x64 candidate DBF/CDX
and LMDB proof, records the current two-table candidate as technically proven,
and holds promotion pending a locale-spine decision.

Why hold:
  The current candidate has localized text rows, but the broader Messaging +
  HELP + manualgen language-support architecture needs explicit locale identity
  and fallback catalogs before active promotion if we want this to scale cleanly.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE17_PROMOTION_READINESS_REVIEW_GREEN_PROMOTION_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE17_PROMOTION_READINESS_REVIEW_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE18_LOCALE_SPINE_CANDIDATE_EXTENSION"
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

def savepoint_present(index_path: Path, savepoint_id: str) -> bool:
    if not index_path.exists():
        return False
    try:
        return any(r.get("savepoint_id") == savepoint_id for r in read_csv(index_path))
    except Exception:
        return False

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p15x_path = reports / "message_catalog_phase15x_status_summary_v1.csv"
    p16x_path = reports / "message_catalog_phase16x_status_summary_v1.csv"
    p15x_gate = reports / "message_catalog_phase15x_gate_check_v1.csv"
    p16x_gate = reports / "message_catalog_phase16x_gate_check_v1.csv"
    p16x_lmdb = reports / "message_catalog_phase16x_lmdb_artifact_inventory_v1.csv"
    savepoint_index = reports / "message_savepoint_thread_index_v1.csv"

    p15x = first_row(p15x_path)
    p16x = first_row(p16x_path)

    messages = p16x.get("MESSAGES", p15x.get("MESSAGES", "12"))
    text_rows = p16x.get("TEXT_ROWS", p15x.get("TEXT_ROWS", "60"))
    locales = p16x.get("LOCALES", p15x.get("LOCALES", "de;en-US;es;fr;it"))
    validation_issues = "0"

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE15X_STATUS_PRESENT", p15x_path.exists(), str(p15x_path))
    gate("PHASE16X_STATUS_PRESENT", p16x_path.exists(), str(p16x_path))
    gate("PHASE15X_X64_REBUILD_GREEN", p15x.get("STATUS") == "MESSAGE_CATALOG_PHASE15X_X64_CANDIDATE_REBUILD_GREEN", p15x.get("STATUS", ""))
    gate("PHASE16X_X64_LMDB_GREEN", p16x.get("STATUS") == "MESSAGE_CATALOG_PHASE16X_X64_CANDIDATE_LMDB_BUILD_GREEN", p16x.get("STATUS", ""))
    gate("PHASE16X_VALIDATION_ZERO", p16x.get("VALIDATION_ISSUES", "") == "0", f"validation_issues={p16x.get('VALIDATION_ISSUES','')}")
    gate("PHASE16X_LMDB_ARTIFACT_INVENTORY_PRESENT", p16x_lmdb.exists(), str(p16x_lmdb))

    review("MSG_015X_SAVEPOINT_PRESENT", savepoint_present(savepoint_index, "MSG-015X"),
           "Recommended for audit continuity, but not a technical blocker if Phase 15X reports and runlog are present.")
    review("MSG_016X_SAVEPOINT_PRESENT", savepoint_present(savepoint_index, "MSG-016X"),
           "Expected after Phase 16X green.")
    review("LOCALE_SPINE_PRESENT", False,
           "SYSTEM_LOCALES and SYSTEM_LOCALE_FALLBACK are not yet part of the candidate; promotion should hold until Phase 18 or explicit override.")
    review("MESSAGE_ARGS_PRESENT", False,
           "SYSTEM_MESSAGE_ARGS is deferred; not required for current 12 messages, but should be planned before placeholder-heavy diagnostics expand.")
    review("PLURAL_RULES_PRESENT", False,
           "Plural rules are deferred; not required for current proof, but must be handled before serious multilingual diagnostics/manual output.")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    if failures:
        validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase17_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "X64_CANDIDATE_DBF_CDX_GREEN": 1 if p15x.get("STATUS") == "MESSAGE_CATALOG_PHASE15X_X64_CANDIDATE_REBUILD_GREEN" else 0,
        "X64_CANDIDATE_LMDB_GREEN": 1 if p16x.get("STATUS") == "MESSAGE_CATALOG_PHASE16X_X64_CANDIDATE_LMDB_BUILD_GREEN" else 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "PROMOTION_HELD": 1,
        "PROMOTION_HOLD_REASON": "locale spine not yet modeled as candidate catalog tables",
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "X64_CANDIDATE_DBF_CDX_GREEN", "X64_CANDIDATE_LMDB_GREEN",
         "ACTIVE_PROMOTION_AUTHORIZED", "PROMOTION_HELD", "PROMOTION_HOLD_REASON",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    scope_rows = [
        {"ITEM": "CURRENT_PROVEN_TABLES", "DECISION": "ACCEPT_AS_TECHNICAL_PROOF", "DETAIL": "SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT are proven as x64 candidate DBF/CDX/LMDB artifacts."},
        {"ITEM": "ACTIVE_PROMOTION", "DECISION": "HOLD", "DETAIL": "Do not promote active catalogs until locale spine decision is resolved or explicitly overridden."},
        {"ITEM": "LOCALE_SPINE", "DECISION": "ADD_BEFORE_PROMOTION_RECOMMENDED", "DETAIL": "Add SYSTEM_LOCALES and SYSTEM_LOCALE_FALLBACK as x64 candidate tables before active promotion."},
        {"ITEM": "LOCALE_FIELD_NAME", "DECISION": "NORMALIZE_TO_LOCALE_ID_RECOMMENDED", "DETAIL": "Rename/normalize SYSTEM_MESSAGE_TEXT.LOCALE to LOCALE_ID in the next candidate extension, preserving current locale values."},
        {"ITEM": "COMPOUND_KEYS", "DECISION": "PRECOMPUTED_FIELDS", "DETAIL": "Continue using MSGLOCALE, SYMBOLLOC, FALLKEY style fields because compound CDX expressions are not supported yet."},
        {"ITEM": "MESSAGE_ARGUMENTS", "DECISION": "DEFER_BUT_PLAN", "DETAIL": "SYSTEM_MESSAGE_ARGS should be designed soon for placeholder contracts, but is not required to validate the current 12-message proof."},
        {"ITEM": "PLURALS", "DECISION": "DEFER", "DETAIL": "SYSTEM_MESSAGE_PLURALS / plural category support should wait until diagnostics and manual text need plural-sensitive rendering."},
        {"ITEM": "MANUALGEN", "DECISION": "CONSUMER_NOT_OWNER", "DETAIL": "Manualgen/manuals should reference the Messaging locale spine later; Messaging should not depend on manualgen."},
    ]
    write_csv(reports / "message_catalog_phase17_scope_decisions_v1.csv", scope_rows,
              ["ITEM", "DECISION", "DETAIL"])

    table_plan = [
        {"TABLE_NAME": "SYSTEM_LOCALES", "PHASE": "18", "ACTION": "ADD_CANDIDATE_X64", "PURPOSE": "Canonical locale identity, language tag, direction, status, source/provenance notes."},
        {"TABLE_NAME": "SYSTEM_LOCALE_FALLBACK", "PHASE": "18", "ACTION": "ADD_CANDIDATE_X64", "PURPOSE": "Explicit fallback chain, e.g. es-MX -> es -> en-US."},
        {"TABLE_NAME": "SYSTEM_MESSAGES", "PHASE": "18", "ACTION": "PRESERVE_CURRENT_X64_CANDIDATE", "PURPOSE": "Message identity/metadata table remains valid."},
        {"TABLE_NAME": "SYSTEM_MESSAGE_TEXT", "PHASE": "18", "ACTION": "EXTEND_OR_REBUILD_CANDIDATE", "PURPOSE": "Normalize LOCALE to LOCALE_ID and connect to SYSTEM_LOCALES."},
        {"TABLE_NAME": "SYSTEM_MESSAGE_ARGS", "PHASE": "LATER", "ACTION": "PLAN_ONLY", "PURPOSE": "Placeholder/format argument contracts."},
        {"TABLE_NAME": "SYSTEM_MESSAGE_PLURALS", "PHASE": "LATER", "ACTION": "PLAN_ONLY", "PURPOSE": "Plural/variant rows for languages requiring CLDR-style categories."},
    ]
    write_csv(reports / "message_catalog_phase17_candidate_table_scope_v1.csv", table_plan,
              ["TABLE_NAME", "PHASE", "ACTION", "PURPOSE"])

    phase18_plan = [
        {"STEP": 1, "ACTION": "CREATE_X64_SYSTEM_LOCALES", "DETAIL": "Seed en-US, es, it, fr, de with BCP47-shaped IDs, text direction ltr, status active."},
        {"STEP": 2, "ACTION": "CREATE_X64_SYSTEM_LOCALE_FALLBACK", "DETAIL": "Seed fallback rows for es/fr/de/it -> en-US; keep room for es-MX -> es -> en-US later."},
        {"STEP": 3, "ACTION": "REBUILD_OR_EXTEND_SYSTEM_MESSAGE_TEXT", "DETAIL": "Use LOCALE_ID and precomputed MSGLOCALE/SYMBOLLOC fields; retain TEXT M and hashes."},
        {"STEP": 4, "ACTION": "RECREATE_CDX_ON_ALL_CANDIDATE_TABLES", "DETAIL": "Simple single-field tags only; use FALLKEY for fallback lookup."},
        {"STEP": 5, "ACTION": "BUILDLMDB_CANDIDATE", "DETAIL": "Candidate-only BUILDLMDB after x64/CDX proof."},
        {"STEP": 6, "ACTION": "READINESS_REVIEW", "DETAIL": "Hold again before active promotion."},
    ]
    write_csv(reports / "message_catalog_phase17_phase18_locale_spine_plan_v1.csv", phase18_plan,
              ["STEP", "ACTION", "DETAIL"])

    write_csv(reports / "message_catalog_phase17_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_X64_CANDIDATE_DBF", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 17 review only; no candidate DBF writes."},
        {"PROTECTED_SYSTEM": "INACTIVE_X64_CANDIDATE_CDX", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 17 review only; no candidate CDX/index writes."},
        {"PROTECTED_SYSTEM": "INACTIVE_X64_CANDIDATE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 17 review only; no candidate LMDB writes."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/catalog mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-code mutation."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion."},
    ]
    write_csv(reports / "message_catalog_phase17_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    review_md = f"""# Message Catalog Phase 17 Promotion-Readiness Review

Status: `{status}`

Phase 17 confirms the x64 candidate DBF/CDX/LMDB proof is technically green,
but holds active promotion pending a locale-spine candidate extension.

## Current technical proof

- Messages: {messages}
- Text rows: {text_rows}
- Locales: {locales}
- Phase 15X x64 DBF/CDX proof: {p15x.get('STATUS', '')}
- Phase 16X x64 LMDB proof: {p16x.get('STATUS', '')}

## Promotion decision

Active promotion is **not authorized**.

Reason: the current two-table candidate does not yet include explicit locale
identity/fallback tables. Messaging should own the locale spine so HELP, manuals,
lessons, and runtime messages can share stable locale behavior without making
manualgen the source of truth.

## Recommended next gate

`{NEXT_GATE}`
"""
    (reports / "MESSAGE_CATALOG_PHASE17_PROMOTION_READINESS_REVIEW.md").write_text(review_md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print("  x64 candidate dbf/cdx green:", 1 if p15x.get("STATUS") == "MESSAGE_CATALOG_PHASE15X_X64_CANDIDATE_REBUILD_GREEN" else 0)
    print("  x64 candidate lmdb green:", 1 if p16x.get("STATUS") == "MESSAGE_CATALOG_PHASE16X_X64_CANDIDATE_LMDB_BUILD_GREEN" else 0)
    print("  active promotion authorized: 0")
    print("  promotion held: 1")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
