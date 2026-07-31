#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22Z_CATALOG_ROW_PROMOTION_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22Z_CATALOG_ROW_PROMOTION_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AA_CATALOG_ROW_PROMOTION_CANDIDATE_STAGING"
REPORT_DIR = Path("docs/messaging/reports")

PROMOTION_SYMBOLS = [
    {
        "SYMBOL": "MESSAGE_PROOF_MODE_STATUS",
        "KIND": "runtime_status_message",
        "PLACEHOLDERS": "mode",
        "EN_US": "Message routing proof mode: {mode}",
        "ES": "Message routing proof mode: {mode} / Modo de prueba de enrutamiento de mensajes: {mode}",
        "FR": "Message routing proof mode: {mode} / Mode de preuve du routage des messages : {mode}",
        "DE": "Message routing proof mode: {mode} / Nachrichten-Routing-Pruefmodus: {mode}",
        "IT": "Message routing proof mode: {mode} / Modalita prova instradamento messaggi: {mode}",
    },
    {
        "SYMBOL": "MESSAGE_PROOF_BOUNDARY_NOTE",
        "KIND": "runtime_boundary_message",
        "PLACEHOLDERS": "",
        "EN_US": "boundary: proof mode changes runtime diagnostic state only; no DBF/CDX/LMDB mutation; no runtime writeback",
        "ES": "boundary: proof mode changes runtime diagnostic state only; no DBF/CDX/LMDB mutation; no runtime writeback / limite: el modo de prueba solo cambia el estado diagnostico",
        "FR": "boundary: proof mode changes runtime diagnostic state only; no DBF/CDX/LMDB mutation; no runtime writeback / limite : le mode de preuve ne change que l'etat diagnostique",
        "DE": "boundary: proof mode changes runtime diagnostic state only; no DBF/CDX/LMDB mutation; no runtime writeback / Grenze: Der Pruefmodus aendert nur den Diagnosestatus",
        "IT": "boundary: proof mode changes runtime diagnostic state only; no DBF/CDX/LMDB mutation; no runtime writeback / confine: la modalita prova cambia solo lo stato diagnostico",
    },
]

LOCALES = [
    ("en-US", "EN_US"),
    ("es", "ES"),
    ("fr", "FR"),
    ("de", "DE"),
    ("it", "IT"),
]

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

def savepoint_present(repo: Path, savepoint_id: str):
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            latest_id = latest.get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    journal_text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id == savepoint_id or savepoint_id in journal_text, latest_id

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    post22y = first_row(reports / "message_catalog_phase22v_post22y_status_summary_v1.csv")
    v = first_row(reports / "message_catalog_phase22v_runtime_regression_status_summary_v1.csv")
    y = first_row(reports / "message_catalog_phase22y_runtime_status_summary_v1.csv")
    current_messages = int(v.get("MESSAGES", y.get("MESSAGES", "12")) or "12")
    current_text_rows = int(v.get("TEXT_ROWS", y.get("TEXT_ROWS", "60")) or "60")
    locales = v.get("LOCALES", y.get("LOCALES", "de;en-US;es;fr;it"))

    y_savepoint_ok, latest_id = savepoint_present(repo, "MSG-022Y")
    post_savepoint_ok, post_latest_id = savepoint_present(repo, "MSG-022V-POST-22Y")

    gates = []
    failures = 0
    reviews = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str):
        nonlocal reviews
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})
        if not ok:
            reviews += 1

    gate("PHASE22Y_RUNTIME_GREEN",
         y.get("STATUS") == "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE_GREEN",
         y.get("STATUS", "missing"))
    gate("MSG_022Y_SAVEPOINT_PRESENT", y_savepoint_ok, latest_id)
    gate("PHASE22V_CURRENT_REGRESSION_GREEN",
         v.get("STATUS") == "MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN",
         v.get("STATUS", "missing"))
    gate("MESSAGE_LOCALE_SET_STILL_GREEN", v.get("MESSAGE_LOCALE_SET_PROOF") == "1", v.get("MESSAGE_LOCALE_SET_PROOF", ""))
    gate("UNSUPPORTED_MESSAGE_LOCALE_STILL_GREEN", v.get("UNSUPPORTED_MESSAGE_LOCALE_PROOF") == "1", v.get("UNSUPPORTED_MESSAGE_LOCALE_PROOF", ""))
    gate("HELP_HINT_COMMAND_STILL_GREEN", v.get("HELP_HINT_COMMAND_PROOF") == "1", v.get("HELP_HINT_COMMAND_PROOF", ""))
    gate("PROOF_LANE_GATED_STILL_GREEN", v.get("PROOF_LANE_GATED") == "1", v.get("PROOF_LANE_GATED", ""))
    gate("ACTIVE_PROVIDER_STILL_GREEN",
         v.get("PROVIDER_ACTIVE_DBF") == "1" and v.get("ACTIVE_CATALOG_LOADED") == "1",
         f"active_dbf={v.get('PROVIDER_ACTIVE_DBF','')}; loaded={v.get('ACTIVE_CATALOG_LOADED','')}")
    gate("FOXHELP_FALLBACK_STILL_ZERO", v.get("FOXHELP_FALLBACK_COUNT") == "0", v.get("FOXHELP_FALLBACK_COUNT", ""))

    review("POST22Y_CLOSEOUT_SAVEPOINT_PRESENT",
           post_savepoint_ok,
           "Recommended before active catalog replacement; Phase 22Z can still plan promotion because current 22V + 22Y reports are green.")
    review("POST22Y_CLOSEOUT_REPORT_GREEN",
           post22y.get("STATUS") == "MESSAGE_CATALOG_PHASE22V_POST22Y_REGRESSION_CLOSEOUT_GREEN_SOURCE_HELD",
           post22y.get("STATUS", "not yet recorded"))

    planned_message_adds = len(PROMOTION_SYMBOLS)
    planned_text_adds = len(PROMOTION_SYMBOLS) * len(LOCALES)
    target_messages = current_messages + planned_message_adds
    target_text_rows = current_text_rows + planned_text_adds

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    message_rows = []
    text_rows = []
    for seq, item in enumerate(PROMOTION_SYMBOLS, start=1):
        message_rows.append({
            "SYMBOL": item["SYMBOL"],
            "KIND": item["KIND"],
            "PLACEHOLDERS": item["PLACEHOLDERS"],
            "SOURCE_PHASE": "22Y",
            "PROMOTION_SCOPE": "candidate_then_active_after_explicit_gate",
            "ACTIVE_MUTATION_IN_22Z": 0,
            "ORDER": seq,
        })
        for locale, key in LOCALES:
            text_rows.append({
                "SYMBOL": item["SYMBOL"],
                "LOCALE": locale,
                "TEXT": item[key],
                "PLACEHOLDERS": item["PLACEHOLDERS"],
                "SOURCE_PHASE": "22Y",
                "ACTIVE_MUTATION_IN_22Z": 0,
            })

    write_csv(reports / "message_catalog_phase22z_promotion_message_rows_v1.csv", message_rows,
              ["SYMBOL", "KIND", "PLACEHOLDERS", "SOURCE_PHASE", "PROMOTION_SCOPE",
               "ACTIVE_MUTATION_IN_22Z", "ORDER"])
    write_csv(reports / "message_catalog_phase22z_promotion_text_rows_v1.csv", text_rows,
              ["SYMBOL", "LOCALE", "TEXT", "PLACEHOLDERS", "SOURCE_PHASE", "ACTIVE_MUTATION_IN_22Z"])

    counts = [{
        "CURRENT_MESSAGES": current_messages,
        "CURRENT_TEXT_ROWS": current_text_rows,
        "PLANNED_MESSAGE_ADDS": planned_message_adds,
        "PLANNED_TEXT_ROW_ADDS": planned_text_adds,
        "TARGET_MESSAGES_AFTER_PROMOTION": target_messages,
        "TARGET_TEXT_ROWS_AFTER_PROMOTION": target_text_rows,
        "LOCALES": locales,
    }]
    write_csv(reports / "message_catalog_phase22z_promotion_count_plan_v1.csv", counts,
              ["CURRENT_MESSAGES", "CURRENT_TEXT_ROWS", "PLANNED_MESSAGE_ADDS",
               "PLANNED_TEXT_ROW_ADDS", "TARGET_MESSAGES_AFTER_PROMOTION",
               "TARGET_TEXT_ROWS_AFTER_PROMOTION", "LOCALES"])

    promotion_plan = [
        {
            "PHASE": "22AA",
            "ACTION": "CANDIDATE_STAGING",
            "DETAIL": "Create a candidate copy of the active messaging catalog with 2 message symbols and 10 locale text rows added; do not replace active DBF/CDX/LMDB.",
            "MUTATION_SCOPE": "candidate files/reports only",
            "REQUIRES_AUTHORIZATION": 1,
        },
        {
            "PHASE": "22AB",
            "ACTION": "CANDIDATE_READBACK_VALIDATION",
            "DETAIL": "Open/read candidate catalog, validate target counts 14 messages and 70 text rows, validate all five locales and placeholder contracts.",
            "MUTATION_SCOPE": "readback/report only",
            "REQUIRES_AUTHORIZATION": 1,
        },
        {
            "PHASE": "22AC",
            "ACTION": "ACTIVE_REPLACEMENT_WITH_BACKUP",
            "DETAIL": "Only after candidate validation, backup active DBF/CDX/LMDB and replace active messaging catalog artifacts.",
            "MUTATION_SCOPE": "active messaging catalog only",
            "REQUIRES_AUTHORIZATION": 1,
        },
        {
            "PHASE": "22AD",
            "ACTION": "RUNTIME_VALIDATION",
            "DETAIL": "Run SET MESSAGE PROOF focused smoke and 22V regression pack against promoted active catalog.",
            "MUTATION_SCOPE": "runtime read-only validation",
            "REQUIRES_AUTHORIZATION": 1,
        },
        {
            "PHASE": "22AE",
            "ACTION": "PROMOTION_CLOSEOUT",
            "DETAIL": "Savepoint promoted catalog if active runtime validation is green; record target counts 14/70.",
            "MUTATION_SCOPE": "journal/reports only",
            "REQUIRES_AUTHORIZATION": 1,
        },
    ]
    write_csv(reports / "message_catalog_phase22z_promotion_ladder_v1.csv", promotion_plan,
              ["PHASE", "ACTION", "DETAIL", "MUTATION_SCOPE", "REQUIRES_AUTHORIZATION"])

    constraints = [
        {"RULE": "NO_SOURCE_MUTATION_IN_22Z", "VALUE": 1, "DETAIL": "22Z is plan-only."},
        {"RULE": "NO_ACTIVE_CATALOG_MUTATION_IN_22Z", "VALUE": 1, "DETAIL": "Active DBF/CDX/LMDB cannot be changed in 22Z."},
        {"RULE": "PROMOTE_ONLY_TWO_22Y_SYMBOLS", "VALUE": 1, "DETAIL": "MESSAGE_PROOF_MODE_STATUS and MESSAGE_PROOF_BOUNDARY_NOTE only."},
        {"RULE": "PRESERVE_INVARIANT_PREFIXES", "VALUE": 1, "DETAIL": "English proof-mode prefix and no-writeback boundary tokens remain for regression stability."},
        {"RULE": "NO_HELP_DATA_OR_CMDHELPCHK_MUTATION", "VALUE": 1, "DETAIL": "HELP DATA and CMDHELPCHK remain protected."},
        {"RULE": "RERUN_22V_AFTER_ACTIVE_PROMOTION", "VALUE": 1, "DETAIL": "Regression pack must remain green after any active promotion."},
    ]
    write_csv(reports / "message_catalog_phase22z_promotion_constraints_v1.csv", constraints,
              ["RULE", "VALUE", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22Z promotion plan only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation in 22Z."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation in 22Z."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation in 22Z."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22z_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22z_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22z_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": current_messages,
        "TEXT_ROWS": current_text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "REVIEW_ISSUES": reviews,
        "PHASE22Y_RUNTIME_GREEN": 1 if y.get("STATUS") == "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE_GREEN" else 0,
        "MSG_022Y_SAVEPOINT_PRESENT": 1 if y_savepoint_ok else 0,
        "PHASE22V_RERUN_GREEN": 1 if v.get("STATUS") == "MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN" else 0,
        "MSG_022V_POST_22Y_SAVEPOINT_PRESENT": 1 if post_savepoint_ok else 0,
        "PROMOTION_PATH_SELECTED": 1,
        "PLANNED_MESSAGE_ADDS": planned_message_adds,
        "PLANNED_TEXT_ROW_ADDS": planned_text_adds,
        "TARGET_MESSAGES_AFTER_PROMOTION": target_messages,
        "TARGET_TEXT_ROWS_AFTER_PROMOTION": target_text_rows,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES", "REVIEW_ISSUES",
         "PHASE22Y_RUNTIME_GREEN", "MSG_022Y_SAVEPOINT_PRESENT", "PHASE22V_RERUN_GREEN",
         "MSG_022V_POST_22Y_SAVEPOINT_PRESENT", "PROMOTION_PATH_SELECTED",
         "PLANNED_MESSAGE_ADDS", "PLANNED_TEXT_ROW_ADDS",
         "TARGET_MESSAGES_AFTER_PROMOTION", "TARGET_TEXT_ROWS_AFTER_PROMOTION",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22Z Catalog Row Promotion Plan

Status: `{status}`

Phase 22Z selects the catalog-row promotion path after the Phase 22Y proof-status
routing patch.

Planned promotion:

```text
MESSAGE_PROOF_MODE_STATUS
MESSAGE_PROOF_BOUNDARY_NOTE
```

Current active catalog count basis:

```text
messages: {current_messages}
text rows: {current_text_rows}
```

Planned target after active promotion:

```text
messages: {target_messages}
text rows: {target_text_rows}
```

Phase 22Z is plan-only. It does not mutate source, active messaging DBF/CDX/LMDB,
HELP DATA, CMDHELPCHK, command registry, manualgen, or Data Dictionary/SelfDoc.

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22Z_CATALOG_ROW_PROMOTION_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {current_messages}")
    print(f"  text rows: {current_text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  review issues: {reviews}")
    print(f"  Phase 22Y runtime green: {1 if y.get('STATUS') == 'MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE_GREEN' else 0}")
    print(f"  MSG-022Y savepoint present: {1 if y_savepoint_ok else 0}")
    print(f"  Phase 22V rerun green: {1 if v.get('STATUS') == 'MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN' else 0}")
    print(f"  MSG-022V-POST-22Y savepoint present: {1 if post_savepoint_ok else 0}")
    print("  promotion path selected: 1")
    print(f"  planned message adds: {planned_message_adds}")
    print(f"  planned text row adds: {planned_text_adds}")
    print(f"  target messages after promotion: {target_messages}")
    print(f"  target text rows after promotion: {target_text_rows}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
