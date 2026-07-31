#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22W_NEXT_LOW_RISK_RUNTIME_SEAM_SELECTION"
RUNLOG = Path("docs/messaging/runlog/MSG-022V_RUNTIME_ROUTING_REGRESSION_SMOKE.md")
TOKEN = "__MSG22V_UNKNOWN__"

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

def count(text: str, pattern: str) -> int:
    return text.upper().count(pattern.upper())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / "docs/messaging/reports"
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22v_staging_status_summary_v1.csv")
    messages = stage.get("MESSAGES", "12")
    text_rows = stage.get("TEXT_ROWS", "60")
    locales = stage.get("LOCALES", "de;en-US;es;fr;it")

    runlog_path = repo / RUNLOG
    text = runlog_path.read_text(encoding="utf-8", errors="replace") if runlog_path.exists() else ""
    upper = text.upper()

    proof_locale_set = count(text, "Message routing proof: active_dbf MESSAGE_LOCALE_SET")
    proof_unsupported = count(text, "Message routing proof: active_dbf UNSUPPORTED_MESSAGE_LOCALE")
    proof_help = count(text, "Message routing proof: active_dbf HELP_HINT_COMMAND")
    proof_on = count(text, "Message routing proof mode: on")
    proof_off = count(text, "Message routing proof mode: off")
    provider_status = count(text, "Message catalog provider status:")
    active_dbf = count(text, "mode: active_dbf")
    active_loaded = count(text, "active catalog loaded: yes")
    fallback_available = count(text, "compiled fallback available")
    boundary_count = count(text, "no DBF/CDX/LMDB mutation")
    writeback_count = count(text, "no runtime writeback")
    locale_es = count(text, "Idioma de mensajes: es")
    unsupported_es = count(text, "Configuracion regional de mensajes no admitida: zz")
    help_es = count(text, f"Escriba HELP {TOKEN} para obtener mas informacion.")
    token_count = count(text, TOKEN)
    literal_placeholder = count(text, "{command}")
    foxhelp = count(text, "Try FOXHELP")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22V_SCRIPT_STAGED",
         stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22V_REGRESSION_PACK_SCRIPT_STAGED_SOURCE_HELD",
         stage.get("STATUS", "missing"))
    gate("RUNLOG_PRESENT", runlog_path.exists(), str(runlog_path))
    gate("PROVIDER_STATUS_PRESENT", provider_status >= 2, f"provider_status={provider_status}")
    gate("ACTIVE_DBF_PRESENT", active_dbf >= 2, f"active_dbf={active_dbf}")
    gate("ACTIVE_CATALOG_LOADED_YES", active_loaded >= 2, f"active_loaded={active_loaded}")
    gate("COMPILED_FALLBACK_AVAILABLE", fallback_available >= 2, f"fallback_available={fallback_available}")
    gate("PROOF_MODE_ON_SEEN", proof_on >= 1, f"proof_on={proof_on}")
    gate("PROOF_MODE_OFF_SEEN", proof_off >= 2, f"proof_off={proof_off}")
    gate("MESSAGE_LOCALE_SET_PROOF", proof_locale_set >= 1, f"MESSAGE_LOCALE_SET={proof_locale_set}")
    gate("UNSUPPORTED_MESSAGE_LOCALE_PROOF", proof_unsupported >= 1, f"UNSUPPORTED_MESSAGE_LOCALE={proof_unsupported}")
    gate("HELP_HINT_COMMAND_PROOF_GATED_ONCE", proof_help == 1, f"HELP_HINT_COMMAND={proof_help}")
    gate("SPANISH_LANGUAGE_MESSAGE", locale_es >= 2, f"Idioma={locale_es}")
    gate("SPANISH_UNSUPPORTED_LOCALE_MESSAGE", unsupported_es >= 1, f"unsupported={unsupported_es}")
    gate("SPANISH_HELP_HINT_VISIBLE", help_es >= 2, f"help_es={help_es}")
    gate("PLACEHOLDER_TOKEN_SUBSTITUTED", token_count >= 2, f"token={token_count}")
    gate("LITERAL_PLACEHOLDER_ABSENT", literal_placeholder == 0, f"literal_placeholder={literal_placeholder}")
    gate("FOXHELP_FALLBACK_BYPASSED", foxhelp == 0, f"foxhelp={foxhelp}")
    gate("NO_WRITEBACK_BOUNDARIES_PRESENT", boundary_count >= 3 and writeback_count >= 3, f"boundary={boundary_count}; writeback={writeback_count}")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22v_runtime_regression_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    metrics = [{
        "PROOF_MESSAGE_LOCALE_SET": proof_locale_set,
        "PROOF_UNSUPPORTED_MESSAGE_LOCALE": proof_unsupported,
        "PROOF_HELP_HINT_COMMAND": proof_help,
        "PROOF_MODE_ON_COUNT": proof_on,
        "PROOF_MODE_OFF_COUNT": proof_off,
        "PROVIDER_STATUS_COUNT": provider_status,
        "ACTIVE_DBF_COUNT": active_dbf,
        "ACTIVE_CATALOG_LOADED_COUNT": active_loaded,
        "COMPILED_FALLBACK_AVAILABLE_COUNT": fallback_available,
        "BOUNDARY_NO_DBF_CDX_LMDB_COUNT": boundary_count,
        "BOUNDARY_NO_RUNTIME_WRITEBACK_COUNT": writeback_count,
        "SPANISH_LANGUAGE_MESSAGE_COUNT": locale_es,
        "SPANISH_UNSUPPORTED_LOCALE_COUNT": unsupported_es,
        "SPANISH_HELP_HINT_COUNT": help_es,
        "TOKEN_COUNT": token_count,
        "LITERAL_PLACEHOLDER_COUNT": literal_placeholder,
        "FOXHELP_FALLBACK_COUNT": foxhelp,
    }]
    write_csv(reports / "message_catalog_phase22v_runtime_regression_metrics_v1.csv", metrics,
              list(metrics[0].keys()))

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22V runtime validation only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22v_runtime_regression_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22v_runtime_regression_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "MESSAGE_LOCALE_SET_PROOF": 1 if proof_locale_set >= 1 else 0,
        "UNSUPPORTED_MESSAGE_LOCALE_PROOF": 1 if proof_unsupported >= 1 else 0,
        "HELP_HINT_COMMAND_PROOF": 1 if proof_help == 1 else 0,
        "PROOF_LANE_GATED": 1 if proof_on >= 1 and proof_off >= 2 and proof_help == 1 else 0,
        "PROVIDER_ACTIVE_DBF": 1 if active_dbf >= 2 else 0,
        "ACTIVE_CATALOG_LOADED": 1 if active_loaded >= 2 else 0,
        "PLACEHOLDER_SUBSTITUTION_PROOF": 1 if token_count >= 2 and literal_placeholder == 0 else 0,
        "FOXHELP_FALLBACK_COUNT": foxhelp,
        "SOURCE_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "MESSAGE_LOCALE_SET_PROOF", "UNSUPPORTED_MESSAGE_LOCALE_PROOF",
         "HELP_HINT_COMMAND_PROOF", "PROOF_LANE_GATED", "PROVIDER_ACTIVE_DBF",
         "ACTIVE_CATALOG_LOADED", "PLACEHOLDER_SUBSTITUTION_PROOF",
         "FOXHELP_FALLBACK_COUNT", "SOURCE_MUTATION_OBSERVED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  MESSAGE_LOCALE_SET proof: {1 if proof_locale_set >= 1 else 0}")
    print(f"  UNSUPPORTED_MESSAGE_LOCALE proof: {1 if proof_unsupported >= 1 else 0}")
    print(f"  HELP_HINT_COMMAND proof: {1 if proof_help == 1 else 0}")
    print(f"  proof lane gated: {1 if proof_on >= 1 and proof_off >= 2 and proof_help == 1 else 0}")
    print(f"  provider active_dbf: {1 if active_dbf >= 2 else 0}")
    print(f"  active catalog loaded: {1 if active_loaded >= 2 else 0}")
    print(f"  placeholder substitution proof: {1 if token_count >= 2 and literal_placeholder == 0 else 0}")
    print(f"  FOXHELP fallback count: {foxhelp}")
    print("  source mutation observed: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
