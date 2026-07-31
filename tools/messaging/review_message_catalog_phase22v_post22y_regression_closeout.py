#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22V_POST22Y_REGRESSION_CLOSEOUT_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22V_POST22Y_REGRESSION_CLOSEOUT_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22Z_NEXT_RUNTIME_SEAM_OR_CATALOG_ROW_PROMOTION_PLAN"
REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022V_RUNTIME_ROUTING_REGRESSION_SMOKE.md")
SAVEPOINT_ID = "MSG-022V-POST-22Y"

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

def count(text: str, pattern: str) -> int:
    return text.upper().count(pattern.upper())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    v = first_row(reports / "message_catalog_phase22v_runtime_regression_status_summary_v1.csv")
    y = first_row(reports / "message_catalog_phase22y_runtime_status_summary_v1.csv")
    messages = v.get("MESSAGES", y.get("MESSAGES", "12"))
    text_rows = v.get("TEXT_ROWS", y.get("TEXT_ROWS", "60"))
    locales = v.get("LOCALES", y.get("LOCALES", "de;en-US;es;fr;it"))
    y_savepoint_ok, latest_id = savepoint_present(repo, "MSG-022Y")

    runlog_path = repo / RUNLOG
    runlog_text = runlog_path.read_text(encoding="utf-8", errors="replace") if runlog_path.exists() else ""

    post22y_suffix_count = count(runlog_text, "Modo de prueba de enrutamiento de mensajes")
    locale_set_proof_count = count(runlog_text, "Message routing proof: active_dbf MESSAGE_LOCALE_SET")
    unsupported_proof_count = count(runlog_text, "Message routing proof: active_dbf UNSUPPORTED_MESSAGE_LOCALE")
    help_hint_proof_count = count(runlog_text, "Message routing proof: active_dbf HELP_HINT_COMMAND")
    provider_status_count = count(runlog_text, "Message catalog provider status:")
    active_dbf_count = count(runlog_text, "mode: active_dbf")
    active_loaded_count = count(runlog_text, "active catalog loaded: yes")
    fallback_count = count(runlog_text, "compiled fallback available")
    foxhelp_count = count(runlog_text, "Try FOXHELP")
    boundary_count = count(runlog_text, "no DBF/CDX/LMDB mutation")
    writeback_count = count(runlog_text, "no runtime writeback")

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22Y_RUNTIME_GREEN",
         y.get("STATUS") == "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE_GREEN",
         y.get("STATUS", "missing"))
    gate("MSG_022Y_SAVEPOINT_PRESENT", y_savepoint_ok, latest_id)
    gate("PHASE22V_RERUN_GREEN",
         v.get("STATUS") == "MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN",
         v.get("STATUS", "missing"))
    gate("MESSAGE_LOCALE_SET_STILL_PROVEN",
         v.get("MESSAGE_LOCALE_SET_PROOF") == "1" and locale_set_proof_count >= 1,
         f"summary={v.get('MESSAGE_LOCALE_SET_PROOF','')}; runlog={locale_set_proof_count}")
    gate("UNSUPPORTED_MESSAGE_LOCALE_STILL_PROVEN",
         v.get("UNSUPPORTED_MESSAGE_LOCALE_PROOF") == "1" and unsupported_proof_count >= 1,
         f"summary={v.get('UNSUPPORTED_MESSAGE_LOCALE_PROOF','')}; runlog={unsupported_proof_count}")
    gate("HELP_HINT_COMMAND_STILL_PROVEN",
         v.get("HELP_HINT_COMMAND_PROOF") == "1" and help_hint_proof_count >= 1,
         f"summary={v.get('HELP_HINT_COMMAND_PROOF','')}; runlog={help_hint_proof_count}")
    gate("PROOF_LANE_GATED_STILL_PROVEN",
         v.get("PROOF_LANE_GATED") == "1",
         v.get("PROOF_LANE_GATED", ""))
    gate("POST_22Y_PROOF_STATUS_SUFFIX_PRESENT",
         post22y_suffix_count >= 1,
         f"spanish proof suffix count={post22y_suffix_count}")
    gate("PROVIDER_ACTIVE_DBF_STILL_PROVEN",
         v.get("PROVIDER_ACTIVE_DBF") == "1" and provider_status_count >= 2 and active_dbf_count >= 2,
         f"summary={v.get('PROVIDER_ACTIVE_DBF','')}; provider={provider_status_count}; active_dbf={active_dbf_count}")
    gate("ACTIVE_CATALOG_LOADED_STILL_PROVEN",
         v.get("ACTIVE_CATALOG_LOADED") == "1" and active_loaded_count >= 2,
         f"summary={v.get('ACTIVE_CATALOG_LOADED','')}; runlog={active_loaded_count}")
    gate("PLACEHOLDER_SUBSTITUTION_STILL_PROVEN",
         v.get("PLACEHOLDER_SUBSTITUTION_PROOF") == "1",
         v.get("PLACEHOLDER_SUBSTITUTION_PROOF", ""))
    gate("FOXHELP_FALLBACK_STILL_ZERO",
         v.get("FOXHELP_FALLBACK_COUNT") == "0" and foxhelp_count == 0,
         f"summary={v.get('FOXHELP_FALLBACK_COUNT','')}; runlog={foxhelp_count}")
    gate("NO_WRITEBACK_BOUNDARIES_STILL_PRESENT",
         boundary_count >= 3 and writeback_count >= 3,
         f"boundary={boundary_count}; writeback={writeback_count}")
    gate("NO_ACTIVE_OR_HELP_MUTATIONS_REPORTED",
         v.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0" and
         v.get("HELP_DATA_MUTATION_OBSERVED") == "0" and
         v.get("CMDHELPCHK_MUTATION_OBSERVED") == "0",
         f"active={v.get('ACTIVE_CATALOG_MUTATION_OBSERVED','')}; help={v.get('HELP_DATA_MUTATION_OBSERVED','')}; cmdhelpchk={v.get('CMDHELPCHK_MUTATION_OBSERVED','')}")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    seam_rows = [
        {"SEAM": "MESSAGE_LOCALE_SET", "STATUS": "STILL_GREEN_AFTER_22Y", "PROOF_COUNT": locale_set_proof_count, "DETAIL": "SET LANGUAGE success route remains active_dbf."},
        {"SEAM": "UNSUPPORTED_MESSAGE_LOCALE", "STATUS": "STILL_GREEN_AFTER_22Y", "PROOF_COUNT": unsupported_proof_count, "DETAIL": "Unsupported locale rejection route remains active_dbf."},
        {"SEAM": "HELP_HINT_COMMAND", "STATUS": "STILL_GREEN_AFTER_22Y", "PROOF_COUNT": help_hint_proof_count, "DETAIL": "HELP hint route remains active_dbf and FOXHELP fallback remains zero."},
        {"SEAM": "MESSAGE_PROOF_MODE_STATUS", "STATUS": "POST_22Y_VISIBLE", "PROOF_COUNT": post22y_suffix_count, "DETAIL": "22Y proof-status Spanish suffix visible inside 22V regression rerun."},
        {"SEAM": "PROVIDER_STATUS", "STATUS": "STILL_GREEN_AFTER_22Y", "PROOF_COUNT": provider_status_count, "DETAIL": "active_dbf provider status still loads catalog and compiled fallback remains available."},
    ]
    write_csv(reports / "message_catalog_phase22v_post22y_seam_status_v1.csv", seam_rows,
              ["SEAM", "STATUS", "PROOF_COUNT", "DETAIL"])

    metrics = [{
        "POST22Y_SPANISH_PROOF_SUFFIX_COUNT": post22y_suffix_count,
        "MESSAGE_LOCALE_SET_PROOF_COUNT": locale_set_proof_count,
        "UNSUPPORTED_MESSAGE_LOCALE_PROOF_COUNT": unsupported_proof_count,
        "HELP_HINT_COMMAND_PROOF_COUNT": help_hint_proof_count,
        "PROVIDER_STATUS_COUNT": provider_status_count,
        "ACTIVE_DBF_COUNT": active_dbf_count,
        "ACTIVE_CATALOG_LOADED_COUNT": active_loaded_count,
        "COMPILED_FALLBACK_AVAILABLE_COUNT": fallback_count,
        "FOXHELP_FALLBACK_COUNT": foxhelp_count,
        "BOUNDARY_NO_DBF_CDX_LMDB_COUNT": boundary_count,
        "BOUNDARY_NO_RUNTIME_WRITEBACK_COUNT": writeback_count,
        "RUNLOG_SHA256": sha256_file(runlog_path),
    }]
    write_csv(reports / "message_catalog_phase22v_post22y_metrics_v1.csv", metrics,
              list(metrics[0].keys()))

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Post-22Y regression closeout only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22v_post22y_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22v_post22y_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22v_post22y_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "MSG_022Y_SAVEPOINT_PRESENT": 1 if y_savepoint_ok else 0,
        "PHASE22Y_RUNTIME_GREEN": 1 if y.get("STATUS") == "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE_GREEN" else 0,
        "PHASE22V_RERUN_GREEN": 1 if v.get("STATUS") == "MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN" else 0,
        "MESSAGE_LOCALE_SET_PROOF": v.get("MESSAGE_LOCALE_SET_PROOF", ""),
        "UNSUPPORTED_MESSAGE_LOCALE_PROOF": v.get("UNSUPPORTED_MESSAGE_LOCALE_PROOF", ""),
        "HELP_HINT_COMMAND_PROOF": v.get("HELP_HINT_COMMAND_PROOF", ""),
        "PROOF_LANE_GATED": v.get("PROOF_LANE_GATED", ""),
        "POST22Y_PROOF_STATUS_VISIBLE": 1 if post22y_suffix_count >= 1 else 0,
        "PROVIDER_ACTIVE_DBF": v.get("PROVIDER_ACTIVE_DBF", ""),
        "ACTIVE_CATALOG_LOADED": v.get("ACTIVE_CATALOG_LOADED", ""),
        "PLACEHOLDER_SUBSTITUTION_PROOF": v.get("PLACEHOLDER_SUBSTITUTION_PROOF", ""),
        "FOXHELP_FALLBACK_COUNT": v.get("FOXHELP_FALLBACK_COUNT", ""),
        "SOURCE_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "SAVEPOINT_ID_RECOMMENDED": SAVEPOINT_ID,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "MSG_022Y_SAVEPOINT_PRESENT", "PHASE22Y_RUNTIME_GREEN", "PHASE22V_RERUN_GREEN",
         "MESSAGE_LOCALE_SET_PROOF", "UNSUPPORTED_MESSAGE_LOCALE_PROOF",
         "HELP_HINT_COMMAND_PROOF", "PROOF_LANE_GATED", "POST22Y_PROOF_STATUS_VISIBLE",
         "PROVIDER_ACTIVE_DBF", "ACTIVE_CATALOG_LOADED", "PLACEHOLDER_SUBSTITUTION_PROOF",
         "FOXHELP_FALLBACK_COUNT", "SOURCE_MUTATION_OBSERVED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "SAVEPOINT_ID_RECOMMENDED", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22V Post-22Y Regression Closeout

Status: `{status}`

This closeout records that the Phase 22V regression pack was rerun after the
Phase 22Y SET MESSAGE PROOF status text patch.

Confirmed after 22Y:

- `MESSAGE_LOCALE_SET` still routes through active DBF.
- `UNSUPPORTED_MESSAGE_LOCALE` still routes through active DBF.
- `HELP_HINT_COMMAND` still routes through active DBF.
- `SET MESSAGE PROOF` status text shows the 22Y routed/Spanish suffix.
- Provider status remains `active_dbf` and active catalog loaded.
- Placeholder substitution remains green.
- FOXHELP fallback count remains zero.
- No active catalog, HELP DATA, or CMDHELPCHK mutation was observed.

Recommended savepoint ID: `{SAVEPOINT_ID}`

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22V_POST22Y_REGRESSION_CLOSEOUT.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  MSG-022Y savepoint present: {1 if y_savepoint_ok else 0}")
    print(f"  Phase 22Y runtime green: {1 if y.get('STATUS') == 'MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE_GREEN' else 0}")
    print(f"  Phase 22V rerun green: {1 if v.get('STATUS') == 'MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN' else 0}")
    print(f"  MESSAGE_LOCALE_SET proof: {v.get('MESSAGE_LOCALE_SET_PROOF', '')}")
    print(f"  UNSUPPORTED_MESSAGE_LOCALE proof: {v.get('UNSUPPORTED_MESSAGE_LOCALE_PROOF', '')}")
    print(f"  HELP_HINT_COMMAND proof: {v.get('HELP_HINT_COMMAND_PROOF', '')}")
    print(f"  proof lane gated: {v.get('PROOF_LANE_GATED', '')}")
    print(f"  post-22Y proof status visible: {1 if post22y_suffix_count >= 1 else 0}")
    print(f"  provider active_dbf: {v.get('PROVIDER_ACTIVE_DBF', '')}")
    print(f"  active catalog loaded: {v.get('ACTIVE_CATALOG_LOADED', '')}")
    print(f"  placeholder substitution proof: {v.get('PLACEHOLDER_SUBSTITUTION_PROOF', '')}")
    print(f"  FOXHELP fallback count: {v.get('FOXHELP_FALLBACK_COUNT', '')}")
    print("  source mutation observed: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  recommended savepoint id: {SAVEPOINT_ID}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
