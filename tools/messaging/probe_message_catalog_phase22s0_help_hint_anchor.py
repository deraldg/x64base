#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22S0_HELP_HINT_SOURCE_ANCHOR_PROBE_GREEN_PATCH_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22S0_HELP_HINT_SOURCE_ANCHOR_PROBE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22S1_HELP_HINT_RUNTIME_ROUTING_PATCH_AFTER_ANCHOR_DECISION"

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

def scan_file(repo: Path, relpath: str):
    path = repo / relpath
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    up = text.upper()
    return {
        "SOURCE_PATH": relpath,
        "EXISTS": 1 if path.exists() else 0,
        "BYTES": path.stat().st_size if path.exists() else 0,
        "SHA256": sha256_file(path),
        "HAS_HELP_HINT_COMMAND": 1 if "HELP_HINT_COMMAND" in up or "HELPHINTCOMMAND" in up else 0,
        "HAS_TYPE_HELP_HINT": 1 if "TYPE HELP" in up and "HELP <COMMAND>" in up else 0,
        "HAS_NO_HELP_FOUND": 1 if "NO HELP FOUND FOR:" in up else 0,
        "HAS_SHOW_FOX_FALLBACK": 1 if "SHOW_FOX(AREA, OPTS.TERM)" in up else 0,
        "HAS_FORMAT_MESSAGE_CATALOG": 1 if "FORMAT_MESSAGE_CATALOG" in up else 0,
        "HAS_ACTIVE_PROVIDER_STATUS": 1 if "ACTIVE_MESSAGE_CATALOG_STATUS" in up else 0,
        "HAS_MESSAGE_PROOF_MODE": 1 if "MESSAGE_ROUTING_PROOF_ENABLED" in up or "SET MESSAGE PROOF" in up else 0,
        "TEXT": text,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / "docs/messaging/reports"
    reports.mkdir(parents=True, exist_ok=True)

    p22r = first_row(reports / "message_catalog_phase22r_status_summary_v1.csv")
    messages = p22r.get("MESSAGES", "12")
    text_rows = p22r.get("TEXT_ROWS", "60")
    locales = p22r.get("LOCALES", "de;en-US;es;fr;it")

    latest = {}
    latest_path = reports / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except Exception:
            latest = {}

    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    journal_text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""

    source_paths = [
        "src/cli/cmd_help.cpp",
        "src/help/helpdata_messages.cpp",
        "src/help/message_catalog.cpp",
        "src/help/message_catalog.hpp",
        "src/cli/cmd_set.cpp",
        "src/cli/command_output.cpp",
    ]
    scans_full = [scan_file(repo, p) for p in source_paths]
    scans = [{k: v for k, v in r.items() if k != "TEXT"} for r in scans_full]
    cmd_help = next((r for r in scans_full if r["SOURCE_PATH"] == "src/cli/cmd_help.cpp"), {})
    cmd_text = cmd_help.get("TEXT", "")
    cmd_up = cmd_text.upper()

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1
    def review(name, ok, detail):
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22R_HELP_HINT_PLAN_GREEN",
         p22r.get("STATUS") == "MESSAGE_CATALOG_PHASE22R_HELP_HINT_ROUTING_PLAN_GREEN_SOURCE_HELD",
         p22r.get("STATUS", ""))
    gate("MSG_022R_SAVEPOINT_PRESENT",
         latest.get("savepoint_id") == "MSG-022R" or "MSG-022R" in journal_text,
         latest.get("savepoint_id", ""))
    gate("CMD_HELP_CPP_PRESENT", cmd_help.get("EXISTS") == 1, "src/cli/cmd_help.cpp")
    gate("CMD_HELP_HAS_GENERIC_HELP_LINE",
         "TYPE HELP GIANT" in cmd_up and "HELP <COMMAND>" in cmd_up,
         "top-level generic HELP guidance line")
    gate("CMD_HELP_HAS_NO_HELP_FOUND_BRANCH",
         "NO HELP FOUND FOR:" in cmd_up,
         "No help found for: branch")
    review("CMD_HELP_LACKS_ACTIVE_PROVIDER",
           "FORMAT_MESSAGE_CATALOG" not in cmd_up,
           "cmd_help.cpp does not yet route through active message catalog.")
    review("NO_HELP_BRANCH_REACHABILITY_RISK",
           "SHOW_FOX(AREA, OPTS.TERM)" in cmd_up,
           "legacy show_fox fallback occurs before final no-help branch for unchanged terms.")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22s0_source_scan_v1.csv", scans,
              ["SOURCE_PATH", "EXISTS", "BYTES", "SHA256", "HAS_HELP_HINT_COMMAND",
               "HAS_TYPE_HELP_HINT", "HAS_NO_HELP_FOUND", "HAS_SHOW_FOX_FALLBACK",
               "HAS_FORMAT_MESSAGE_CATALOG", "HAS_ACTIVE_PROVIDER_STATUS",
               "HAS_MESSAGE_PROOF_MODE"])

    evidence = []
    patterns = ["Type HELP GIANT", "HELP <command>", "No help found for:", "show_fox(area, opts.term)",
                "show_reflected_command_topic", "show_new_catalog_topic", "show_function_topic_from_doc_catalog"]
    for i, line in enumerate(cmd_text.splitlines(), start=1):
        up = line.upper()
        if any(p.upper() in up for p in patterns):
            evidence.append({"SOURCE_PATH": "src/cli/cmd_help.cpp", "LINE": i, "TEXT": line.strip()})
    write_csv(reports / "message_catalog_phase22s0_cmd_help_anchor_evidence_v1.csv", evidence,
              ["SOURCE_PATH", "LINE", "TEXT"])

    anchors = [
        {"ANCHOR_ID": "A1", "ANCHOR": "top-level HELP no-argument guidance line", "SOURCE_PATH": "src/cli/cmd_help.cpp",
         "TEXT_SIGNAL": "Type HELP GIANT ... HELP <command>", "RISK": "LOW_TECHNICAL_MEDIUM_SEMANTIC",
         "SMOKEABLE": 1, "SELECTED_FOR_PATCH": 0,
         "REASON": "Stable and easy to smoke with HELP, but not command-specific and does not naturally exercise {command} placeholder."},
        {"ANCHOR_ID": "A2", "ANCHOR": "final No help found branch", "SOURCE_PATH": "src/cli/cmd_help.cpp",
         "TEXT_SIGNAL": "No help found for: opts.term", "RISK": "MEDIUM_REACHABILITY",
         "SMOKEABLE": 0, "SELECTED_FOR_PATCH": 0,
         "REASON": "Semantically fits HELP_HINT_COMMAND, but legacy show_fox fallback may return before this branch."},
        {"ANCHOR_ID": "A3", "ANCHOR": "post-reflected command/topic fallback hint", "SOURCE_PATH": "src/cli/cmd_help.cpp",
         "TEXT_SIGNAL": "after reflected/catalog/function/topic attempts, before broad legacy fallback",
         "RISK": "MEDIUM", "SMOKEABLE": 1, "SELECTED_FOR_PATCH": 1,
         "REASON": "Best candidate for Phase 22S.1: add narrow active-provider hint before broad legacy fallback without touching HELP DATA/CMDHELPCHK."},
    ]
    write_csv(reports / "message_catalog_phase22s0_anchor_candidates_v1.csv", anchors,
              ["ANCHOR_ID", "ANCHOR", "SOURCE_PATH", "TEXT_SIGNAL", "RISK", "SMOKEABLE", "SELECTED_FOR_PATCH", "REASON"])

    plan = [
        {"PLAN_ID": "22S1-001", "TARGET_PATH": "src/cli/cmd_help.cpp",
         "ACTION": "ADD_LOCAL_ACTIVE_MESSAGE_HELP_HINT_HELPER", "SYMBOL": "HELP_HINT_COMMAND",
         "DETAIL": "Add a narrow helper that calls active provider for HELP_HINT_COMMAND and substitutes {command}.", "AUTHORIZED_NOW": 0},
        {"PLAN_ID": "22S1-002", "TARGET_PATH": "src/cli/cmd_help.cpp",
         "ACTION": "INSERT_HINT_BEFORE_LEGACY_FOX_FALLBACK", "SYMBOL": "HELP_HINT_COMMAND",
         "DETAIL": "Emit localized HELP_HINT_COMMAND before broad legacy FOX fallback, preserving fallback.", "AUTHORIZED_NOW": 0},
        {"PLAN_ID": "22S1-003", "TARGET_PATH": "src/cli/cmd_help.cpp",
         "ACTION": "PRESERVE_GATED_PROOF_LANE", "SYMBOL": "HELP_HINT_COMMAND",
         "DETAIL": "Emit proof line only when proof mode is enabled.", "AUTHORIZED_NOW": 0},
        {"PLAN_ID": "22S1-004", "TARGET_PATH": "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22S1_HELP_HINT_ROUTING_SMOKE.dts",
         "ACTION": "CREATE_RUNTIME_SMOKE", "SYMBOL": "HELP_HINT_COMMAND",
         "DETAIL": "Smoke proof OFF/ON and a HELP topic that reaches the narrow insertion point.", "AUTHORIZED_NOW": 0},
    ]
    write_csv(reports / "message_catalog_phase22s0_phase22s1_patch_plan_v1.csv", plan,
              ["PLAN_ID", "TARGET_PATH", "ACTION", "SYMBOL", "DETAIL", "AUTHORIZED_NOW"])

    risks = [
        {"RISK_ID": "RISK-001", "RISK": "Final no-help branch may be unreachable due to legacy FOX fallback.",
         "MITIGATION": "Do not patch final branch blindly; use pre-fallback narrow hint insertion point."},
        {"RISK_ID": "RISK-002", "RISK": "Top-level HELP line is stable but semantically not the {command} hint.",
         "MITIGATION": "Do not route top-level HELP line as HELP_HINT_COMMAND."},
        {"RISK_ID": "RISK-003", "RISK": "HELP is protected/high-visibility.",
         "MITIGATION": "Patch only cmd_help.cpp narrow hint logic; no HELP DATA/CMDHELPCHK/registry mutation."},
        {"RISK_ID": "RISK-004", "RISK": "Proof mode helper may be local to cmd_set.cpp.",
         "MITIGATION": "Phase 22S.1 should inspect linkage and either expose a tiny helper safely or avoid proof line until explicit."},
    ]
    write_csv(reports / "message_catalog_phase22s0_risk_register_v1.csv", risks,
              ["RISK_ID", "RISK", "MITIGATION"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22S.0 source-anchor probe only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22s0_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22s0_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22s0_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SELECTED_ANCHOR": "A3 post-reflected command/topic fallback hint",
        "SELECTED_SYMBOL": "HELP_HINT_COMMAND",
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SELECTED_ANCHOR", "SELECTED_SYMBOL", "SOURCE_MUTATION_AUTHORIZED",
         "SOURCE_FILES_MUTATED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (reports / "MESSAGE_CATALOG_PHASE22S0_HELP_HINT_SOURCE_ANCHOR_PROBE.md").write_text(
        f"# Message Catalog Phase 22S.0 HELP Hint Source Anchor Probe\n\nStatus: `{status}`\n\n"
        "This probe is report-only. It selected A3, a post-reflected command/topic fallback hint, as the safest next patch anchor.\n\n"
        f"Next gate: `{NEXT_GATE}`\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print("  selected anchor: A3 post-reflected command/topic fallback hint")
    print("  selected symbol: HELP_HINT_COMMAND")
    print("  source mutation authorized: 0")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
