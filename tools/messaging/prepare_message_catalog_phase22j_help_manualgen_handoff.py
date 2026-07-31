#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22J_HELP_MANUALGEN_LANGUAGE_HANDOFF_GREEN_REPORT_ONLY"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22J_HELP_MANUALGEN_LANGUAGE_HANDOFF_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23_LOCALE_SPINE_OR_PHASE22K_HELP_MANUALGEN_CONSUMER_PLAN"
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

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def has_savepoint(repo: Path, savepoint_id: str) -> bool:
    idx = repo / "docs/messaging/reports/message_savepoint_thread_index_v1.csv"
    if not idx.exists():
        return False
    try:
        return any(row.get("savepoint_id") == savepoint_id for row in read_csv(idx))
    except Exception:
        return False

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-report-only-handoff", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22i = first_row(reports / "message_catalog_phase22i_runtime_status_summary_v1.csv")
    messages = p22i.get("MESSAGES", "12")
    text_rows = p22i.get("TEXT_ROWS", "60")
    locales = p22i.get("LOCALES", "de;en-US;es;fr;it")

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("OPERATOR_ACCEPTED_REPORT_ONLY_HANDOFF", args.accept_report_only_handoff,
         "requires --accept-report-only-handoff")
    gate("PHASE22I_ARGUMENT_SUBSTITUTION_GREEN",
         p22i.get("STATUS") == "MESSAGE_CATALOG_PHASE22I_ARGUMENT_SUBSTITUTION_SMOKE_GREEN",
         p22i.get("STATUS", ""))
    gate("PHASE22I_VALIDATION_ZERO", p22i.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={p22i.get('VALIDATION_ISSUES', '')}")
    review("MSG_022I_SAVEPOINT_OBSERVED", has_savepoint(repo, "MSG-022I"),
           "recommended before handoff, but report can still be generated from green validation evidence")

    runtime_capabilities = [
        {"CAPABILITY_ID": "LANG-001", "CAPABILITY": "ACTIVE_DBF_PROVIDER", "STATUS": "PROVEN", "EVIDENCE": "MSG-022F active DBF row-load provider; active catalog loaded yes"},
        {"CAPABILITY_ID": "LANG-002", "CAPABILITY": "RUNTIME_LOOKUP", "STATUS": "PROVEN", "EVIDENCE": "MSG-022G SET MESSAGE CATALOG GET; six lookup blocks"},
        {"CAPABILITY_ID": "LANG-003", "CAPABILITY": "LOCALE_FALLBACK", "STATUS": "PROVEN", "EVIDENCE": "MSG-022G xx-XX fallback to en-US"},
        {"CAPABILITY_ID": "LANG-004", "CAPABILITY": "SET_LANGUAGE_EMISSION", "STATUS": "PROVEN", "EVIDENCE": "MSG-022H SET LANGUAGE CHECK active provider-backed emission"},
        {"CAPABILITY_ID": "LANG-005", "CAPABILITY": "ARGUMENT_SUBSTITUTION", "STATUS": "PROVEN", "EVIDENCE": "MSG-022I command=USE substitution in en-US, es, and xx-XX fallback"},
        {"CAPABILITY_ID": "LANG-006", "CAPABILITY": "SUPPORTED_LOCALES_CURRENT", "STATUS": "PROVEN", "EVIDENCE": "de;en-US;es;fr;it"},
        {"CAPABILITY_ID": "LANG-007", "CAPABILITY": "FORMAL_LOCALE_SPINE", "STATUS": "DEFERRED", "EVIDENCE": "Phase 23 candidate: SYSTEM_LOCALES and SYSTEM_LOCALE_FALLBACK"},
        {"CAPABILITY_ID": "LANG-008", "CAPABILITY": "FORMAL_ARGUMENT_SCHEMA", "STATUS": "DEFERRED", "EVIDENCE": "Phase 24 candidate: SYSTEM_MESSAGE_ARGS / placeholder contracts"},
    ]

    data_contract = [
        {"CONTRACT_ID": "MSG-TABLE-001", "TABLE_OR_CONTRACT": "SYSTEM_MESSAGES", "FIELDS": "MSGID;SYMBOL;ENUMNAME;FACILITY;OWNER;CATEGORY;SEVERITY;STATUS;SRC", "ROLE": "message symbol identity and ownership"},
        {"CONTRACT_ID": "MSG-TABLE-002", "TABLE_OR_CONTRACT": "SYSTEM_MESSAGE_TEXT", "FIELDS": "MSGID;SYMBOL;ENUMNAME;LOCALE;MSGLOCALE;SYMBOLLOC;TEXT;TXTHASH;STATUS;SRC", "ROLE": "localized runtime text rows"},
        {"CONTRACT_ID": "MSG-RUNTIME-001", "TABLE_OR_CONTRACT": "Runtime provider status", "FIELDS": "provider_mode;current_locale;fallback_locale;active_catalog_present;active_catalog_loaded;message_count;text_row_count", "ROLE": "runtime provenance for emitted messages"},
        {"CONTRACT_ID": "MSG-RUNTIME-002", "TABLE_OR_CONTRACT": "Runtime lookup request", "FIELDS": "symbol;locale;arguments;fallback_locale", "ROLE": "provider lookup input contract"},
        {"CONTRACT_ID": "MSG-RUNTIME-003", "TABLE_OR_CONTRACT": "Runtime lookup result", "FIELDS": "text;source=active_dbf_or_compiled_fallback;substitution_status", "ROLE": "provider lookup output contract"},
    ]

    help_requirements = [
        {"REQ_ID": "HELP-LANG-001", "SYSTEM": "HELP", "REQUIREMENT": "Document SET LANGUAGE CHECK active Messaging provider behavior", "STATUS": "READY_FOR_DOC", "BOUNDARY": "documentation only; no HELP DATA mutation in Phase 22J"},
        {"REQ_ID": "HELP-LANG-002", "SYSTEM": "HELP", "REQUIREMENT": "Document SET MESSAGE CATALOG CHECK and GET commands", "STATUS": "READY_FOR_DOC", "BOUNDARY": "documentation only; command surface already runtime-proven"},
        {"REQ_ID": "HELP-LANG-003", "SYSTEM": "HELP", "REQUIREMENT": "Allow HELP topics to reference message SYMBOL values without owning localized text", "STATUS": "RECOMMENDED", "BOUNDARY": "HELP references Messaging; Messaging remains runtime language source"},
        {"REQ_ID": "HELP-LANG-004", "SYSTEM": "HELP", "REQUIREMENT": "Add future HELP audit that documented symbols exist in SYSTEM_MESSAGES", "STATUS": "CANDIDATE_CONSUMER", "BOUNDARY": "report-only audit first; no CMDHELPCHK mutation yet"},
        {"REQ_ID": "HELP-LANG-005", "SYSTEM": "CMDHELPCHK", "REQUIREMENT": "Future validation may check SET LANGUAGE / SET MESSAGE CATALOG documented examples", "STATUS": "DEFERRED", "BOUNDARY": "CMDHELPCHK mutation requires separate authorization"},
        {"REQ_ID": "HELP-LANG-006", "SYSTEM": "HELP", "REQUIREMENT": "Do not translate HELP/manual text as part of runtime message catalog work", "STATUS": "ACCEPTED_BOUNDARY", "BOUNDARY": "manual/help translation is separate content program"},
    ]

    manualgen_requirements = [
        {"REQ_ID": "MANLANG-001", "SYSTEM": "MANUALGEN", "REQUIREMENT": "Add Messaging/language chapter or section describing active DBF provider, fallback, and substitution proofs", "STATUS": "READY_FOR_DOC", "BOUNDARY": "no manual publication mutation in Phase 22J"},
        {"REQ_ID": "MANLANG-002", "SYSTEM": "MANUALGEN", "REQUIREMENT": "Consume language handoff reports as downstream evidence, not source of truth", "STATUS": "ACCEPTED", "BOUNDARY": "manualgen remains explanatory downstream artifact"},
        {"REQ_ID": "MANLANG-003", "SYSTEM": "MANUALGEN", "REQUIREMENT": "Expose message symbol inventory for command documentation cross-reference", "STATUS": "CANDIDATE_CONSUMER", "BOUNDARY": "report-only consumer first"},
        {"REQ_ID": "MANLANG-004", "SYSTEM": "MANUALGEN", "REQUIREMENT": "Record current supported locales and proof status", "STATUS": "READY_FOR_DOC", "BOUNDARY": "de;en-US;es;fr;it are proven for current catalog only"},
        {"REQ_ID": "MANLANG-005", "SYSTEM": "MANUALGEN", "REQUIREMENT": "Defer full manual localization until locale spine and manual content strategy are authorized", "STATUS": "DEFERRED", "BOUNDARY": "do not make manualgen depend on Messaging runtime"},
        {"REQ_ID": "MANLANG-006", "SYSTEM": "MANUALGEN", "REQUIREMENT": "Record placeholder/substitution requirement as proven runtime behavior and future formal schema need", "STATUS": "READY_FOR_DOC", "BOUNDARY": "formal SYSTEM_MESSAGE_ARGS deferred"},
    ]

    selfdoc_datadict_requirements = [
        {"REQ_ID": "SELF-LANG-001", "SYSTEM": "SELFDOC", "REQUIREMENT": "Track Messaging language lane savepoints MSG-022F through MSG-022I as provenance", "STATUS": "READY_FOR_AUDIT", "BOUNDARY": "no production SelfDoc metadata mutation"},
        {"REQ_ID": "DD-LANG-001", "SYSTEM": "DATA_DICTIONARY", "REQUIREMENT": "Future Data Dictionary scan should discover Messaging tables and message text fields", "STATUS": "CANDIDATE", "BOUNDARY": "Data Dictionary derives from repo/source/help/metadata evidence, not manuals"},
        {"REQ_ID": "DD-LANG-002", "SYSTEM": "DATA_DICTIONARY", "REQUIREMENT": "Future object model should recognize message symbol, localized text, fallback locale, and placeholder contracts", "STATUS": "DEFERRED", "BOUNDARY": "no Data Dictionary mutation in Phase 22J"},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation; handoff requirements only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; future consumer/audit only."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen publication/catalog mutation; report-only handoff."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary or production SelfDoc mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22j_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "REPORT_ONLY_HANDOFF_ACCEPTED": 1 if args.accept_report_only_handoff else 0,
        "HELP_REQUIREMENT_ROWS": len(help_requirements),
        "MANUALGEN_REQUIREMENT_ROWS": len(manualgen_requirements),
        "DATADICT_SELFDOC_REQUIREMENT_ROWS": len(selfdoc_datadict_requirements),
        "PROTECTED_MUTATIONS": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "REPORT_ONLY_HANDOFF_ACCEPTED", "HELP_REQUIREMENT_ROWS",
         "MANUALGEN_REQUIREMENT_ROWS", "DATADICT_SELFDOC_REQUIREMENT_ROWS",
         "PROTECTED_MUTATIONS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22j_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22j_runtime_capability_inventory_v1.csv", runtime_capabilities,
              ["CAPABILITY_ID", "CAPABILITY", "STATUS", "EVIDENCE"])
    write_csv(reports / "message_catalog_phase22j_language_data_contract_v1.csv", data_contract,
              ["CONTRACT_ID", "TABLE_OR_CONTRACT", "FIELDS", "ROLE"])
    write_csv(reports / "message_catalog_phase22j_help_requirements_v1.csv", help_requirements,
              ["REQ_ID", "SYSTEM", "REQUIREMENT", "STATUS", "BOUNDARY"])
    write_csv(reports / "message_catalog_phase22j_manualgen_requirements_v1.csv", manualgen_requirements,
              ["REQ_ID", "SYSTEM", "REQUIREMENT", "STATUS", "BOUNDARY"])
    write_csv(reports / "message_catalog_phase22j_selfdoc_datadict_requirements_v1.csv", selfdoc_datadict_requirements,
              ["REQ_ID", "SYSTEM", "REQUIREMENT", "STATUS", "BOUNDARY"])
    write_csv(reports / "message_catalog_phase22j_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    handoff_md = (
        f"# Message Locale Phase 22J — HELP / Manualgen Language Handoff\n\n"
        f"Status: `{status}`\n\n"
        "Phase 22J is a report-only handoff. It gives HELP, CMDHELPCHK, manualgen,\n"
        "SelfDoc, and Data Dictionary enough requirements data to support the runtime\n"
        "language work without taking ownership of localized runtime text.\n\n"
        "## Proven runtime language substrate\n\n"
        "- Active Messaging DBF provider loads runtime rows.\n"
        f"- Current message rows: {messages}\n"
        f"- Current localized text rows: {text_rows}\n"
        f"- Current locales: {locales}\n"
        "- SET MESSAGE CATALOG GET resolves active catalog text.\n"
        "- SET LANGUAGE CHECK emits provider-backed message text.\n"
        "- Argument substitution is proven for `{command}` via `command=USE`.\n"
        "- Missing locale fallback to `en-US` is proven.\n"
        "- Runtime use is read-only: no DBF/CDX/LMDB mutation or runtime writeback.\n\n"
        "## Source-of-truth rule\n\n"
        "Messaging is the source of truth for runtime messages and localized runtime\n"
        "message text.\n\n"
        "HELP and manuals may describe, reference, audit, and explain Messaging symbols,\n"
        "but they should not own or rewrite runtime-localized text.\n\n"
        "## HELP requirements\n\n"
        "See:\n\n"
        "```text\n"
        "docs/messaging/reports/message_catalog_phase22j_help_requirements_v1.csv\n"
        "```\n\n"
        "## Manualgen requirements\n\n"
        "See:\n\n"
        "```text\n"
        "docs/messaging/reports/message_catalog_phase22j_manualgen_requirements_v1.csv\n"
        "```\n\n"
        "## SelfDoc / Data Dictionary requirements\n\n"
        "See:\n\n"
        "```text\n"
        "docs/messaging/reports/message_catalog_phase22j_selfdoc_datadict_requirements_v1.csv\n"
        "```\n\n"
        "## Boundary\n\n"
        "Phase 22J performs no HELP DATA mutation, no CMDHELPCHK mutation, no manualgen\n"
        "publication/catalog mutation, no Data Dictionary/SelfDoc mutation, no source\n"
        "mutation, and no active Messaging catalog mutation.\n"
    )

    handoff_path = repo / "docs/messaging/MESSAGE_LOCALE_PHASE22J_HELP_MANUALGEN_LANGUAGE_HANDOFF.md"
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(handoff_md, encoding="utf-8")

    manifest_rows = []
    for path in [
        reports / "message_catalog_phase22j_status_summary_v1.csv",
        reports / "message_catalog_phase22j_gate_check_v1.csv",
        reports / "message_catalog_phase22j_runtime_capability_inventory_v1.csv",
        reports / "message_catalog_phase22j_language_data_contract_v1.csv",
        reports / "message_catalog_phase22j_help_requirements_v1.csv",
        reports / "message_catalog_phase22j_manualgen_requirements_v1.csv",
        reports / "message_catalog_phase22j_selfdoc_datadict_requirements_v1.csv",
        reports / "message_catalog_phase22j_boundary_ledger_v1.csv",
        handoff_path,
    ]:
        if path.exists():
            rel_path = path.relative_to(repo).as_posix()
            text_content = path.read_text(encoding="utf-8", errors="replace")
            manifest_rows.append({
                "ARTIFACT": rel_path,
                "BYTES": path.stat().st_size,
                "SHA256": sha256_text(text_content),
                "ROLE": "phase22j_handoff_artifact",
            })
    write_csv(reports / "message_catalog_phase22j_artifact_manifest_v1.csv", manifest_rows,
              ["ARTIFACT", "BYTES", "SHA256", "ROLE"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  help requirement rows: {len(help_requirements)}")
    print(f"  manualgen requirement rows: {len(manualgen_requirements)}")
    print(f"  datadict/selfdoc requirement rows: {len(selfdoc_datadict_requirements)}")
    print("  protected mutations: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
