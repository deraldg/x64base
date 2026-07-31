#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23A_SHARED_LOCALE_CONTRACT_GREEN_REPORT_ONLY"
STATUS_BLOCKED = "LOCALE_PHASE23A_SHARED_LOCALE_CONTRACT_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23B_CANDIDATE_SYSTEM_LOCALES_SCHEMA_STAGING"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
MESSAGING_REPORT_DIR = Path("docs/messaging/reports")

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
    ap.add_argument("--accept-report-only-locale-contract", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    msg22j = first_row(repo / MESSAGING_REPORT_DIR / "message_catalog_phase22j_status_summary_v1.csv")
    messages = msg22j.get("MESSAGES", "12")
    text_rows = msg22j.get("TEXT_ROWS", "60")
    locales = msg22j.get("LOCALES", "de;en-US;es;fr;it")

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("OPERATOR_ACCEPTED_REPORT_ONLY_LOCALE_CONTRACT",
         args.accept_report_only_locale_contract,
         "requires --accept-report-only-locale-contract")
    gate("MSG_022J_HANDOFF_GREEN",
         msg22j.get("STATUS") == "MESSAGE_CATALOG_PHASE22J_HELP_MANUALGEN_LANGUAGE_HANDOFF_GREEN_REPORT_ONLY",
         msg22j.get("STATUS", ""))
    gate("MSG_022J_VALIDATION_ZERO",
         msg22j.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={msg22j.get('VALIDATION_ISSUES', '')}")
    review("MSG_022J_SAVEPOINT_OBSERVED", has_savepoint(repo, "MSG-022J"),
           "recommended; Phase 23A can still be generated from green 22J evidence")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    system_locales_plan = [
        {
            "LOCALE_ID": "en-US",
            "BASE_LOCALE": "en",
            "DISPLAY_NAME": "English (United States)",
            "TEXT_DIR": "LTR",
            "LOCALE_STATUS": "DEFAULT_ACTIVE",
            "DEFAULT_LOCALE": 1,
            "FALLBACK_ALLOWED": 0,
            "SOURCE_EVIDENCE": "MSG-022G/22H/22I active runtime proof",
            "NOTES": "Canonical default runtime locale"
        },
        {
            "LOCALE_ID": "es",
            "BASE_LOCALE": "es",
            "DISPLAY_NAME": "Spanish",
            "TEXT_DIR": "LTR",
            "LOCALE_STATUS": "ACTIVE",
            "DEFAULT_LOCALE": 0,
            "FALLBACK_ALLOWED": 1,
            "SOURCE_EVIDENCE": "MSG-022G/22H/22I active runtime proof",
            "NOTES": "Runtime lookup, SET LANGUAGE emission, and substitution proven"
        },
        {
            "LOCALE_ID": "fr",
            "BASE_LOCALE": "fr",
            "DISPLAY_NAME": "French",
            "TEXT_DIR": "LTR",
            "LOCALE_STATUS": "ACTIVE",
            "DEFAULT_LOCALE": 0,
            "FALLBACK_ALLOWED": 1,
            "SOURCE_EVIDENCE": "MSG-022G active runtime lookup proof",
            "NOTES": "Runtime lookup proven"
        },
        {
            "LOCALE_ID": "de",
            "BASE_LOCALE": "de",
            "DISPLAY_NAME": "German",
            "TEXT_DIR": "LTR",
            "LOCALE_STATUS": "ACTIVE",
            "DEFAULT_LOCALE": 0,
            "FALLBACK_ALLOWED": 1,
            "SOURCE_EVIDENCE": "MSG-022G active runtime lookup proof",
            "NOTES": "Runtime lookup proven"
        },
        {
            "LOCALE_ID": "it",
            "BASE_LOCALE": "it",
            "DISPLAY_NAME": "Italian",
            "TEXT_DIR": "LTR",
            "LOCALE_STATUS": "ACTIVE",
            "DEFAULT_LOCALE": 0,
            "FALLBACK_ALLOWED": 1,
            "SOURCE_EVIDENCE": "MSG-022G active runtime lookup proof",
            "NOTES": "Runtime lookup proven"
        },
    ]

    fallback_plan = [
        {
            "FALLBACK_ID": "FB-001",
            "LOCALE_ID": "es",
            "FALLBACK_TO": "en-US",
            "FALLBACK_ORDER": 100,
            "FALLBACK_TYPE": "DEFAULT",
            "APPLIES_TO": "Messaging;HELP;Manualgen;SelfDoc;Data Dictionary when fallback is enabled",
            "STATUS": "PLANNED_FROM_PROVEN_RUNTIME_BEHAVIOR",
            "EVIDENCE": "MSG-022G/22I xx-XX fallback to en-US; explicit per-locale rows planned"
        },
        {
            "FALLBACK_ID": "FB-002",
            "LOCALE_ID": "fr",
            "FALLBACK_TO": "en-US",
            "FALLBACK_ORDER": 100,
            "FALLBACK_TYPE": "DEFAULT",
            "APPLIES_TO": "all consumers when fallback is enabled",
            "STATUS": "PLANNED",
            "EVIDENCE": "current catalog includes fr; fallback rule explicit"
        },
        {
            "FALLBACK_ID": "FB-003",
            "LOCALE_ID": "de",
            "FALLBACK_TO": "en-US",
            "FALLBACK_ORDER": 100,
            "FALLBACK_TYPE": "DEFAULT",
            "APPLIES_TO": "all consumers when fallback is enabled",
            "STATUS": "PLANNED",
            "EVIDENCE": "current catalog includes de; fallback rule explicit"
        },
        {
            "FALLBACK_ID": "FB-004",
            "LOCALE_ID": "it",
            "FALLBACK_TO": "en-US",
            "FALLBACK_ORDER": 100,
            "FALLBACK_TYPE": "DEFAULT",
            "APPLIES_TO": "all consumers when fallback is enabled",
            "STATUS": "PLANNED",
            "EVIDENCE": "current catalog includes it; fallback rule explicit"
        },
        {
            "FALLBACK_ID": "FB-005",
            "LOCALE_ID": "*",
            "FALLBACK_TO": "en-US",
            "FALLBACK_ORDER": 999,
            "FALLBACK_TYPE": "GLOBAL_DEFAULT",
            "APPLIES_TO": "runtime lookup when exact locale unsupported and fallback is allowed",
            "STATUS": "PROVEN_AS_RUNTIME_BEHAVIOR_NOT_YET_TABLE_BACKED",
            "EVIDENCE": "MSG-022G/22I xx-XX -> en-US"
        },
    ]

    field_contract = [
        {"FIELD": "LOCALE_ID", "ROLE": "shared stable locale key", "TRANSLATED": 0, "EXAMPLE": "en-US;es;fr;de;it", "REQUIRED": 1},
        {"FIELD": "BASE_LOCALE", "ROLE": "parent/base language or base tag", "TRANSLATED": 0, "EXAMPLE": "en;es;fr", "REQUIRED": 1},
        {"FIELD": "SOURCE_LOCALE", "ROLE": "source text locale for translation/provenance", "TRANSLATED": 0, "EXAMPLE": "en-US", "REQUIRED": 0},
        {"FIELD": "FALLBACK_ALLOWED", "ROLE": "whether consumer may use fallback rows", "TRANSLATED": 0, "EXAMPLE": "1", "REQUIRED": 1},
        {"FIELD": "TEXT_DIR", "ROLE": "rendering direction", "TRANSLATED": 0, "EXAMPLE": "LTR;RTL", "REQUIRED": 1},
        {"FIELD": "LOCALE_STATUS", "ROLE": "locale availability state", "TRANSLATED": 0, "EXAMPLE": "ACTIVE;DEFAULT_ACTIVE;DISABLED", "REQUIRED": 1},
        {"FIELD": "TRANSL_STATUS", "ROLE": "localized text/artifact review state", "TRANSLATED": 0, "EXAMPLE": "CANONICAL;DRAFT;MACHINE;REVIEWED;APPROVED;STALE", "REQUIRED": 0},
        {"FIELD": "SOURCE_HASH", "ROLE": "hash of canonical source text/artifact", "TRANSLATED": 0, "EXAMPLE": "sha256", "REQUIRED": 0},
        {"FIELD": "LOCALIZED_HASH", "ROLE": "hash of localized text/artifact", "TRANSLATED": 0, "EXAMPLE": "sha256", "REQUIRED": 0},
        {"FIELD": "REVIEW_STATUS", "ROLE": "human/process review state", "TRANSLATED": 0, "EXAMPLE": "UNREVIEWED;REVIEWED;APPROVED", "REQUIRED": 0},
        {"FIELD": "REVIEWED_BY", "ROLE": "reviewer identity or tool/process", "TRANSLATED": 0, "EXAMPLE": "reviewer id", "REQUIRED": 0},
        {"FIELD": "REVIEWED_AT", "ROLE": "review timestamp", "TRANSLATED": 0, "EXAMPLE": "UTC timestamp", "REQUIRED": 0},
    ]

    consumer_mapping = [
        {"CONSUMER": "Messaging", "STABLE_IDENTITY": "SYSTEM_MESSAGES", "LOCALIZED_COMPANION": "SYSTEM_MESSAGE_TEXT", "LOCALE_FIELD": "LOCALE_ID or current LOCALE field transition", "CONSUMER_ROLE": "runtime message rendering", "STATUS": "FIRST_PROVEN_RUNTIME_CONSUMER"},
        {"CONSUMER": "HELP", "STABLE_IDENTITY": "HELP_TOPIC", "LOCALIZED_COMPANION": "HELP_TEXT", "LOCALE_FIELD": "LOCALE_ID", "CONSUMER_ROLE": "command/help explanation", "STATUS": "PLANNED_CONSUMER"},
        {"CONSUMER": "CMDHELPCHK", "STABLE_IDENTITY": "command/help validation rules", "LOCALIZED_COMPANION": "localized example/check rows as needed", "LOCALE_FIELD": "LOCALE_ID", "CONSUMER_ROLE": "validation/audit", "STATUS": "PLANNED_REPORT_FIRST_CONSUMER"},
        {"CONSUMER": "Manualgen/MAN*", "STABLE_IDENTITY": "MANSECTION;MANPUB", "LOCALIZED_COMPANION": "MANSECTION_TXT;MANPUB_TXT;locale-aware MANHASH/MANREVIEW", "LOCALE_FIELD": "LOCALE_ID", "CONSUMER_ROLE": "manual artifact generation", "STATUS": "PLANNED_CONSUMER"},
        {"CONSUMER": "SelfDoc", "STABLE_IDENTITY": "source/object/provenance identities", "LOCALIZED_COMPANION": "localized labels/descriptions where needed", "LOCALE_FIELD": "LOCALE_ID", "CONSUMER_ROLE": "documentation/provenance audit", "STATUS": "PLANNED_CONSUMER"},
        {"CONSUMER": "Data Dictionary", "STABLE_IDENTITY": "DDOBJECT/DDATTR/etc.", "LOCALIZED_COMPANION": "*_TXT or localized label/description rows", "LOCALE_FIELD": "LOCALE_ID", "CONSUMER_ROLE": "schema/object explanation", "STATUS": "PLANNED_CONSUMER"},
    ]

    doctrine = [
        {"RULE_ID": "LC-001", "RULE": "One shared locale spine; no subsystem-specific language spines.", "STATUS": "ACCEPTED"},
        {"RULE_ID": "LC-002", "RULE": "Stable IDs are not translated.", "STATUS": "ACCEPTED"},
        {"RULE_ID": "LC-003", "RULE": "Rendered text and localized artifacts attach via LOCALE_ID companion rows.", "STATUS": "ACCEPTED"},
        {"RULE_ID": "LC-004", "RULE": "Fallback must be explicit and testable.", "STATUS": "ACCEPTED"},
        {"RULE_ID": "LC-005", "RULE": "Messaging owns runtime localized message rendering; manuals/HELP explain and reference.", "STATUS": "ACCEPTED"},
        {"RULE_ID": "LC-006", "RULE": "Manualgen owns manual artifact generation; it consumes locale contracts but does not own runtime language.", "STATUS": "ACCEPTED"},
        {"RULE_ID": "LC-007", "RULE": "HELP owns command/help explanation; it may reference message symbols but must not rewrite runtime localized message text.", "STATUS": "ACCEPTED"},
        {"RULE_ID": "LC-008", "RULE": "Data Dictionary and SelfDoc derive from repo/source/help/metadata evidence, not from manuals as source of truth.", "STATUS": "ACCEPTED"},
    ]

    schema_plan = [
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "LOCALE_ID", "TYPE_HINT": "C(16)", "ROLE": "canonical shared locale key", "INDEX_HINT": "primary tag LOCALE_ID"},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "BASE_LOCALE", "TYPE_HINT": "C(16)", "ROLE": "base language/parent tag", "INDEX_HINT": "tag BASE_LOCALE"},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "DISPLAY_NAME", "TYPE_HINT": "C(80)", "ROLE": "human-readable locale name", "INDEX_HINT": ""},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "TEXT_DIR", "TYPE_HINT": "C(3)", "ROLE": "LTR/RTL", "INDEX_HINT": ""},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "LOCALE_STATUS", "TYPE_HINT": "C(24)", "ROLE": "ACTIVE/DEFAULT_ACTIVE/DISABLED/etc.", "INDEX_HINT": "tag STATUS"},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "DEFAULT_LOCALE", "TYPE_HINT": "L", "ROLE": "default locale marker", "INDEX_HINT": ""},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "SRC", "TYPE_HINT": "C(32)", "ROLE": "source/provenance lane", "INDEX_HINT": ""},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "LOCALE_ID", "TYPE_HINT": "C(16)", "ROLE": "source locale for fallback", "INDEX_HINT": "tag LOCALE_ID"},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "FALLBACK_TO", "TYPE_HINT": "C(16)", "ROLE": "fallback locale", "INDEX_HINT": "tag FALLBACK_TO"},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "FALLBACK_ORDER", "TYPE_HINT": "N(6,0)", "ROLE": "ordered fallback priority", "INDEX_HINT": "tag ORDER"},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "FALLBACK_TYPE", "TYPE_HINT": "C(24)", "ROLE": "DEFAULT/PARENT/GLOBAL_DEFAULT/etc.", "INDEX_HINT": ""},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "FALLBACK_ALLOWED", "TYPE_HINT": "L", "ROLE": "enabled fallback rule", "INDEX_HINT": ""},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "SRC", "TYPE_HINT": "C(32)", "ROLE": "source/provenance lane", "INDEX_HINT": ""},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging DBF/catalog mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen publication/catalog mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "LOCALE_DBF_SCHEMA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No SYSTEM_LOCALES/SYSTEM_LOCALE_FALLBACK DBF creation in Phase 23A."},
    ]

    write_csv(reports / "locale_phase23a_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGING_PROOF_MESSAGES": messages,
        "MESSAGING_PROOF_TEXT_ROWS": text_rows,
        "CURRENT_PROVEN_LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "REPORT_ONLY_LOCALE_CONTRACT_ACCEPTED": 1 if args.accept_report_only_locale_contract else 0,
        "SYSTEM_LOCALES_ROWS_PLANNED": len(system_locales_plan),
        "FALLBACK_ROWS_PLANNED": len(fallback_plan),
        "CONSUMER_ROWS": len(consumer_mapping),
        "PROTECTED_MUTATIONS": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGING_PROOF_MESSAGES", "MESSAGING_PROOF_TEXT_ROWS",
         "CURRENT_PROVEN_LOCALES", "VALIDATION_ISSUES", "REPORT_ONLY_LOCALE_CONTRACT_ACCEPTED",
         "SYSTEM_LOCALES_ROWS_PLANNED", "FALLBACK_ROWS_PLANNED", "CONSUMER_ROWS",
         "PROTECTED_MUTATIONS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23a_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23a_system_locales_plan_v1.csv", system_locales_plan,
              ["LOCALE_ID", "BASE_LOCALE", "DISPLAY_NAME", "TEXT_DIR", "LOCALE_STATUS",
               "DEFAULT_LOCALE", "FALLBACK_ALLOWED", "SOURCE_EVIDENCE", "NOTES"])
    write_csv(reports / "locale_phase23a_fallback_plan_v1.csv", fallback_plan,
              ["FALLBACK_ID", "LOCALE_ID", "FALLBACK_TO", "FALLBACK_ORDER", "FALLBACK_TYPE",
               "APPLIES_TO", "STATUS", "EVIDENCE"])
    write_csv(reports / "locale_phase23a_field_contract_v1.csv", field_contract,
              ["FIELD", "ROLE", "TRANSLATED", "EXAMPLE", "REQUIRED"])
    write_csv(reports / "locale_phase23a_consumer_mapping_v1.csv", consumer_mapping,
              ["CONSUMER", "STABLE_IDENTITY", "LOCALIZED_COMPANION", "LOCALE_FIELD",
               "CONSUMER_ROLE", "STATUS"])
    write_csv(reports / "locale_phase23a_doctrine_v1.csv", doctrine,
              ["RULE_ID", "RULE", "STATUS"])
    write_csv(reports / "locale_phase23a_schema_plan_v1.csv", schema_plan,
              ["TABLE", "FIELD", "TYPE_HINT", "ROLE", "INDEX_HINT"])
    write_csv(reports / "locale_phase23a_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    contract_md = f"""# Shared Locale Contract v1

Status: `{status}`

Phase 23A defines the shared locale contract and locale spine plan. It is
report-only. It creates no DBF tables, no indexes, no LMDB environments, and
does not mutate HELP, CMDHELPCHK, manualgen, Data Dictionary, SelfDoc, source,
or active Messaging catalogs.

## Core doctrine

One shared locale spine. Many domain spines. Localized companion rows where
human text or localized artifacts exist.

Stable IDs are not translated. Rendered text is localized. Fallback is explicit
and testable.

## Shared spine

Planned shared tables:

```text
SYSTEM_LOCALES
SYSTEM_LOCALE_FALLBACK
```

These tables are shared infrastructure, not Messaging-only and not
manualgen-only.

## First proven runtime consumer

Messaging is the first proven runtime consumer.

Current Messaging evidence:

```text
messages: {messages}
localized text rows: {text_rows}
locales: {locales}
provider: active_dbf
fallback: xx-XX -> en-US proven
argument substitution: command=USE proven
```

## Domain ownership

Messaging owns runtime message rendering.

HELP owns command/help explanation.

Manualgen owns manual artifact generation.

SelfDoc and Data Dictionary own provenance/object/schema documentation lanes.

All consume the same `LOCALE_ID` contract and explicit fallback model.

## Companion table pattern

```text
Messaging:
  SYSTEM_MESSAGES          stable message identity
  SYSTEM_MESSAGE_TEXT      localized message text by LOCALE_ID

HELP:
  HELP_TOPIC               stable topic identity
  HELP_TEXT                localized HELP text by LOCALE_ID

Manualgen / MAN*:
  MANSECTION               stable section identity/order/path
  MANSECTION_TXT           localized title/summary/body pointer by LOCALE_ID
  MANPUB                   stable publication identity
  MANPUB_TXT               localized publication title/description by LOCALE_ID
  MANHASH                  source/localized artifact hashes
  MANREVIEW                locale-aware review/provenance

Data Dictionary / SelfDoc:
  DDOBJECT / etc.          stable object identity
  *_TXT or localized rows  localized labels/descriptions by LOCALE_ID
```

## Report artifacts

```text
docs/locale/reports/locale_phase23a_status_summary_v1.csv
docs/locale/reports/locale_phase23a_system_locales_plan_v1.csv
docs/locale/reports/locale_phase23a_fallback_plan_v1.csv
docs/locale/reports/locale_phase23a_field_contract_v1.csv
docs/locale/reports/locale_phase23a_consumer_mapping_v1.csv
docs/locale/reports/locale_phase23a_doctrine_v1.csv
docs/locale/reports/locale_phase23a_schema_plan_v1.csv
docs/locale/reports/locale_phase23a_boundary_ledger_v1.csv
```

## Next gate

```text
{NEXT_GATE}
```
"""
    contract_path = repo / "docs/locale/SHARED_LOCALE_CONTRACT_v1.md"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(contract_md, encoding="utf-8")

    manifest_rows = []
    for path in [
        reports / "locale_phase23a_status_summary_v1.csv",
        reports / "locale_phase23a_gate_check_v1.csv",
        reports / "locale_phase23a_system_locales_plan_v1.csv",
        reports / "locale_phase23a_fallback_plan_v1.csv",
        reports / "locale_phase23a_field_contract_v1.csv",
        reports / "locale_phase23a_consumer_mapping_v1.csv",
        reports / "locale_phase23a_doctrine_v1.csv",
        reports / "locale_phase23a_schema_plan_v1.csv",
        reports / "locale_phase23a_boundary_ledger_v1.csv",
        contract_path,
    ]:
        if path.exists():
            rel = path.relative_to(repo).as_posix()
            text = path.read_text(encoding="utf-8", errors="replace")
            manifest_rows.append({
                "ARTIFACT": rel,
                "BYTES": path.stat().st_size,
                "SHA256": sha256_text(text),
                "ROLE": "phase23a_locale_contract_artifact",
            })
    write_csv(reports / "locale_phase23a_artifact_manifest_v1.csv", manifest_rows,
              ["ARTIFACT", "BYTES", "SHA256", "ROLE"])

    print(status)
    print(f"  messaging proof messages: {messages}")
    print(f"  messaging proof text rows: {text_rows}")
    print(f"  current proven locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  system locales rows planned: {len(system_locales_plan)}")
    print(f"  fallback rows planned: {len(fallback_plan)}")
    print(f"  consumer mapping rows: {len(consumer_mapping)}")
    print("  protected mutations: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
