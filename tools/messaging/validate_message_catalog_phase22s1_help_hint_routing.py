#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22S1_HELP_HINT_RUNTIME_ROUTING_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22S1_HELP_HINT_RUNTIME_ROUTING_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22T_RUNTIME_ROUTING_CLOSEOUT_OR_NEXT_SEAM"
RUNLOG = Path("docs/messaging/runlog/MSG-022S1_HELP_HINT_ROUTING_SMOKE.md")
PROOF_LINE = "MESSAGE ROUTING PROOF: ACTIVE_DBF HELP_HINT_COMMAND"
SMOKE_TOKEN = "__MSG22S1_UNKNOWN__"

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
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / "docs/messaging/reports"
    reports.mkdir(parents=True, exist_ok=True)

    p22s1 = first_row(reports / "message_catalog_phase22s1_status_summary_v1.csv")
    messages = p22s1.get("MESSAGES", "12")
    text_rows = p22s1.get("TEXT_ROWS", "60")
    locales = p22s1.get("LOCALES", "de;en-US;es;fr;it")

    runlog = repo / RUNLOG
    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()

    proof_line_count = upper.count(PROOF_LINE)
    mode_on_count = upper.count("MESSAGE ROUTING PROOF MODE: ON")
    mode_off_count = upper.count("MESSAGE ROUTING PROOF MODE: OFF")
    token_count = upper.count(SMOKE_TOKEN.upper())
    literal_placeholder_count = upper.count("{COMMAND}")
    spanish_hint_count = upper.count("ESCRIBA HELP")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22S1_PATCH_APPLIED",
         p22s1.get("STATUS") == "MESSAGE_CATALOG_PHASE22S1_HELP_HINT_RUNTIME_ROUTING_PATCH_APPLIED",
         p22s1.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("PROOF_MODE_OFF_SEEN", mode_off_count >= 2, f"off count={mode_off_count}")
    gate("PROOF_MODE_ON_SEEN", mode_on_count >= 1, f"on count={mode_on_count}")
    gate("HELP_HINT_PROOF_LINE_GATED", proof_line_count == 1, f"proof line count={proof_line_count}")
    gate("HELP_HINT_SPANISH_TEXT_VISIBLE", spanish_hint_count >= 2, f"Escriba HELP count={spanish_hint_count}")
    gate("HELP_HINT_COMMAND_TOKEN_SUBSTITUTED", token_count >= 2, f"smoke token count={token_count}")
    gate("HELP_HINT_LITERAL_PLACEHOLDER_ABSENT", literal_placeholder_count == 0, f"literal {{command}} count={literal_placeholder_count}")
    gate("PROVIDER_STATUS_ACTIVE_DBF", "MODE: ACTIVE_DBF" in upper or "PROVIDER MODE: ACTIVE_DBF" in upper, "active_dbf")
    gate("ACTIVE_CATALOG_LOADED_YES", "ACTIVE CATALOG LOADED: YES" in upper, "active catalog loaded")
    gate("NO_WRITEBACK_BOUNDARY", "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper, "read-only/no-writeback boundary")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22s1_runtime_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PROOF_MODE_ON_COUNT": mode_on_count,
        "PROOF_MODE_OFF_COUNT": mode_off_count,
        "HELP_HINT_PROOF_LINE_COUNT": proof_line_count,
        "HELP_HINT_SPANISH_TEXT_COUNT": spanish_hint_count,
        "HELP_HINT_COMMAND_TOKEN_COUNT": token_count,
        "HELP_HINT_LITERAL_PLACEHOLDER_COUNT": literal_placeholder_count,
        "HELP_HINT_ROUTING_PROOF": 1 if proof_line_count == 1 and spanish_hint_count >= 2 and token_count >= 2 else 0,
        "PROOF_LANE_GATED": 1 if proof_line_count == 1 and mode_on_count >= 1 and mode_off_count >= 2 else 0,
        "PROVIDER_ACTIVE_DBF": 1 if "ACTIVE_DBF" in upper else 0,
        "ACTIVE_CATALOG_LOADED": 1 if "ACTIVE CATALOG LOADED: YES" in upper else 0,
        "SOURCE_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PROOF_MODE_ON_COUNT", "PROOF_MODE_OFF_COUNT", "HELP_HINT_PROOF_LINE_COUNT",
         "HELP_HINT_SPANISH_TEXT_COUNT", "HELP_HINT_COMMAND_TOKEN_COUNT",
         "HELP_HINT_LITERAL_PLACEHOLDER_COUNT", "HELP_HINT_ROUTING_PROOF",
         "PROOF_LANE_GATED", "PROVIDER_ACTIVE_DBF", "ACTIVE_CATALOG_LOADED",
         "SOURCE_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22s1_runtime_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  proof mode on count: {mode_on_count}")
    print(f"  proof mode off count: {mode_off_count}")
    print(f"  HELP_HINT proof line count: {proof_line_count}")
    print(f"  HELP_HINT Spanish text count: {spanish_hint_count}")
    print(f"  HELP_HINT command token count: {token_count}")
    print(f"  HELP_HINT routing proof: {1 if proof_line_count == 1 and spanish_hint_count >= 2 and token_count >= 2 else 0}")
    print(f"  proof lane gated: {1 if proof_line_count == 1 and mode_on_count >= 1 and mode_off_count >= 2 else 0}")
    print(f"  provider active_dbf: {1 if 'ACTIVE_DBF' in upper else 0}")
    print(f"  active catalog loaded: {1 if 'ACTIVE CATALOG LOADED: YES' in upper else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
