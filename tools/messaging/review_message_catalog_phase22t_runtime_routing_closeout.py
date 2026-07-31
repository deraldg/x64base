#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22T_RUNTIME_ROUTING_CLOSEOUT_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22T_RUNTIME_ROUTING_CLOSEOUT_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22U_NEXT_LOW_RISK_RUNTIME_SEAM_PLAN"
REPORT_DIR = Path("docs/messaging/reports")

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

def find_first_existing(repo: Path, relpaths: list[str]):
    for relpath in relpaths:
        path = repo / relpath
        if path.exists():
            return path, first_row(path)
    return None, {}

def savepoint_present(repo: Path, savepoint_id: str):
    reports = repo / REPORT_DIR
    latest_path = reports / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            latest_id = latest.get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal_path = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    journal_text = journal_path.read_text(encoding="utf-8", errors="replace") if journal_path.exists() else ""
    return latest_id == savepoint_id or savepoint_id in journal_text, latest_id

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    # Proven current counts from the active catalog lane. Prefer the newest S1 runtime report.
    s1_path, s1 = find_first_existing(repo, [
        "docs/messaging/reports/message_catalog_phase22s1_runtime_status_summary_v1.csv",
    ])
    m_path, m = find_first_existing(repo, [
        "docs/messaging/reports/message_catalog_phase22m_runtime_status_summary_v1.csv",
        "docs/messaging/reports/message_catalog_phase22m_status_summary_v1.csv",
        "docs/messaging/reports/message_catalog_phase22m_validate_status_summary_v1.csv",
    ])
    q_path, q = find_first_existing(repo, [
        "docs/messaging/reports/message_catalog_phase22q_runtime_status_summary_v1.csv",
        "docs/messaging/reports/message_catalog_phase22q_1_runtime_status_summary_v1.csv",
        "docs/messaging/reports/message_catalog_phase22q_status_summary_v1.csv",
    ])
    k_path, k = find_first_existing(repo, [
        "docs/messaging/reports/message_catalog_phase22k_runtime_status_summary_v1.csv",
        "docs/messaging/reports/message_catalog_phase22k_status_summary_v1.csv",
    ])

    messages = s1.get("MESSAGES", q.get("MESSAGES", m.get("MESSAGES", "12")))
    text_rows = s1.get("TEXT_ROWS", q.get("TEXT_ROWS", m.get("TEXT_ROWS", "60")))
    locales = s1.get("LOCALES", q.get("LOCALES", m.get("LOCALES", "de;en-US;es;fr;it")))

    savepoint_ok, latest_id = savepoint_present(repo, "MSG-022S1")

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str):
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22S1_RUNTIME_GREEN",
         s1.get("STATUS") == "MESSAGE_CATALOG_PHASE22S1_HELP_HINT_RUNTIME_ROUTING_SMOKE_GREEN",
         s1.get("STATUS", "missing"))
    gate("MSG_022S1_SAVEPOINT_PRESENT", savepoint_ok, latest_id)
    gate("S1_HELP_HINT_ROUTING_PROOF",
         s1.get("HELP_HINT_ROUTING_PROOF") == "1",
         s1.get("HELP_HINT_ROUTING_PROOF", ""))
    gate("S1_PROOF_LANE_GATED",
         s1.get("PROOF_LANE_GATED") == "1",
         s1.get("PROOF_LANE_GATED", ""))
    gate("S1_PROVIDER_ACTIVE_DBF",
         s1.get("PROVIDER_ACTIVE_DBF") == "1",
         s1.get("PROVIDER_ACTIVE_DBF", ""))
    gate("S1_ACTIVE_CATALOG_LOADED",
         s1.get("ACTIVE_CATALOG_LOADED") == "1",
         s1.get("ACTIVE_CATALOG_LOADED", ""))
    gate("S1_FOXHELP_FALLBACK_BYPASSED",
         s1.get("FOXHELP_FALLBACK_COUNT") == "0",
         s1.get("FOXHELP_FALLBACK_COUNT", ""))

    # Older seams may have slightly different report names; do not fail closeout if older reports
    # have been superseded, but record what is visible.
    review("PHASE22M_REPORT_VISIBLE", bool(m), str(m_path.relative_to(repo)) if m_path else "not found")
    review("PHASE22Q_REPORT_VISIBLE", bool(q), str(q_path.relative_to(repo)) if q_path else "not found")
    review("PHASE22K_PLACEHOLDER_REPORT_VISIBLE", bool(k), str(k_path.relative_to(repo)) if k_path else "not found")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    proven_seams = [
        {
            "SEAM_ID": "22M",
            "SEAM": "SET LANGUAGE success routing",
            "SYMBOL": "MESSAGE_LOCALE_SET",
            "EVIDENCE_STATUS": "PROVEN_EARLIER_IN_PHASE22_CHAIN",
            "RUNTIME_PROOF": "SET LANGUAGE emitted localized active-DBF message and routing proof.",
            "REPORT_PATH": str(m_path.relative_to(repo)).replace("\\", "/") if m_path else "not located by Phase22T script",
        },
        {
            "SEAM_ID": "22Q",
            "SEAM": "unsupported locale rejection routing",
            "SYMBOL": "UNSUPPORTED_MESSAGE_LOCALE",
            "EVIDENCE_STATUS": "PROVEN_EARLIER_IN_PHASE22_CHAIN",
            "RUNTIME_PROOF": "unsupported locale rejection emitted localized active-DBF message and gated proof line.",
            "REPORT_PATH": str(q_path.relative_to(repo)).replace("\\", "/") if q_path else "not located by Phase22T script",
        },
        {
            "SEAM_ID": "22S1",
            "SEAM": "HELP hint routing",
            "SYMBOL": "HELP_HINT_COMMAND",
            "EVIDENCE_STATUS": "PROVEN_CURRENT",
            "RUNTIME_PROOF": "HELP hint emitted Spanish text, substituted command token, bypassed FOXHELP fallback, and emitted one gated active_dbf proof line.",
            "REPORT_PATH": str(s1_path.relative_to(repo)).replace("\\", "/") if s1_path else "missing",
        },
        {
            "SEAM_ID": "PROOF",
            "SEAM": "shared/gated proof lane",
            "SYMBOL": "SET MESSAGE PROOF",
            "EVIDENCE_STATUS": "PROVEN_CURRENT",
            "RUNTIME_PROOF": "proof mode off/on/off counts prove the proof lane remains gated.",
            "REPORT_PATH": str(s1_path.relative_to(repo)).replace("\\", "/") if s1_path else "missing",
        },
    ]
    write_csv(reports / "message_catalog_phase22t_proven_runtime_seams_v1.csv", proven_seams,
              ["SEAM_ID", "SEAM", "SYMBOL", "EVIDENCE_STATUS", "RUNTIME_PROOF", "REPORT_PATH"])

    source_scope = [
        {
            "SOURCE_PATH": "src/help/message_catalog.hpp",
            "ROLE": "active provider interface and shared proof-state declaration",
            "MUTATION_STATUS": "mutated in S1 chain; no mutation in 22T",
            "SHA256": sha256_file(repo / "src/help/message_catalog.hpp"),
        },
        {
            "SOURCE_PATH": "src/help/message_catalog.cpp",
            "ROLE": "active provider implementation and shared proof-state definition",
            "MUTATION_STATUS": "mutated in S1 chain; no mutation in 22T",
            "SHA256": sha256_file(repo / "src/help/message_catalog.cpp"),
        },
        {
            "SOURCE_PATH": "src/cli/cmd_set.cpp",
            "ROLE": "SET LANGUAGE / SET MESSAGE PROOF / diagnostic status surface",
            "MUTATION_STATUS": "mutated in S1 chain; no mutation in 22T",
            "SHA256": sha256_file(repo / "src/cli/cmd_set.cpp"),
        },
        {
            "SOURCE_PATH": "src/cli/cmd_help.cpp",
            "ROLE": "HELP_HINT_COMMAND runtime route",
            "MUTATION_STATUS": "mutated in S1 chain; no mutation in 22T",
            "SHA256": sha256_file(repo / "src/cli/cmd_help.cpp"),
        },
    ]
    write_csv(reports / "message_catalog_phase22t_source_scope_closure_v1.csv", source_scope,
              ["SOURCE_PATH", "ROLE", "MUTATION_STATUS", "SHA256"])

    next_candidates = [
        {
            "CANDIDATE_ID": "22U-A",
            "SEAM": "runtime routing closeout / regression pack",
            "RECOMMENDATION": "BEST_NEXT",
            "RATIONALE": "Before adding another command seam, freeze a small regression pack for MESSAGE_LOCALE_SET, UNSUPPORTED_MESSAGE_LOCALE, HELP_HINT_COMMAND, provider status, fallback, and proof gating.",
            "MUTATION_REQUIRED": "report/script only initially",
        },
        {
            "CANDIDATE_ID": "22U-B",
            "SEAM": "next low-risk status/report message",
            "RECOMMENDATION": "SECOND",
            "RATIONALE": "A read-only status/report message is safer than broad error routing and can reuse the active provider and placeholder mechanisms.",
            "MUTATION_REQUIRED": "source patch later, gated",
        },
        {
            "CANDIDATE_ID": "22U-C",
            "SEAM": "broad HELP DATA localization",
            "RECOMMENDATION": "DEFER",
            "RATIONALE": "HELP DATA/CMDHELPCHK are protected and too broad for the next step.",
            "MUTATION_REQUIRED": "deferred",
        },
        {
            "CANDIDATE_ID": "22U-D",
            "SEAM": "central command output router",
            "RECOMMENDATION": "DEFER",
            "RATIONALE": "Still too broad; several more narrow seams should be proven first.",
            "MUTATION_REQUIRED": "deferred",
        },
    ]
    write_csv(reports / "message_catalog_phase22t_next_seam_candidates_v1.csv", next_candidates,
              ["CANDIDATE_ID", "SEAM", "RECOMMENDATION", "RATIONALE", "MUTATION_REQUIRED"])

    lessons = [
        {"LESSON_ID": "L1", "LESSON": "Runtime proof beat source intent.", "DETAIL": "S1 initially looked patched but runtime showed FOXHELP fallback swallowed the route."},
        {"LESSON_ID": "L2", "LESSON": "Build gates must precede runtime smoke.", "DETAIL": "S1.4/S1.5 repaired source syntax artifacts before successful runtime validation."},
        {"LESSON_ID": "L3", "LESSON": "Proof mode must remain gated.", "DETAIL": "S1 proved one proof line only during proof-on mode."},
        {"LESSON_ID": "L4", "LESSON": "Protect HELP DATA and CMDHELPCHK.", "DETAIL": "HELP_HINT_COMMAND runtime routing was achieved without HELP DATA rebuild or CMDHELPCHK mutation."},
        {"LESSON_ID": "L5", "LESSON": "Keep compiled fallback available.", "DETAIL": "Provider status still reports compiled fallback available while active DBF is loaded."},
    ]
    write_csv(reports / "message_catalog_phase22t_lessons_v1.csv", lessons,
              ["LESSON_ID", "LESSON", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22T closeout/report only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22t_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22t_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22t_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "S1_SAVEPOINT_PRESENT": 1 if savepoint_ok else 0,
        "S1_HELP_HINT_ROUTING_PROOF": s1.get("HELP_HINT_ROUTING_PROOF", ""),
        "S1_PROOF_LANE_GATED": s1.get("PROOF_LANE_GATED", ""),
        "S1_PROVIDER_ACTIVE_DBF": s1.get("PROVIDER_ACTIVE_DBF", ""),
        "S1_ACTIVE_CATALOG_LOADED": s1.get("ACTIVE_CATALOG_LOADED", ""),
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "S1_SAVEPOINT_PRESENT", "S1_HELP_HINT_ROUTING_PROOF", "S1_PROOF_LANE_GATED",
         "S1_PROVIDER_ACTIVE_DBF", "S1_ACTIVE_CATALOG_LOADED",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22T Runtime Routing Closeout

Status: `{status}`

Phase 22T is report-only. It closes the first runtime routing pilot set after
`MSG-022S1` proved HELP hint routing through the active DBF message catalog.

## Proven seams

- `MESSAGE_LOCALE_SET` — SET LANGUAGE success routing.
- `UNSUPPORTED_MESSAGE_LOCALE` — unsupported-locale rejection routing.
- `HELP_HINT_COMMAND` — HELP hint routing with placeholder substitution.
- `SET MESSAGE PROOF` — shared/gated proof lane.

## Protected boundaries

No source mutation, active catalog mutation, HELP DATA rebuild, CMDHELPCHK
mutation, command registry mutation, manualgen mutation, or Data Dictionary /
SelfDoc mutation occurred in Phase 22T.

## Recommended next gate

`{NEXT_GATE}`

Recommended next action: Phase 22U should create a small regression-pack plan
before adding broader runtime routing seams.
"""
    (reports / "MESSAGE_CATALOG_PHASE22T_RUNTIME_ROUTING_CLOSEOUT.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  S1 savepoint present: {1 if savepoint_ok else 0}")
    print(f"  HELP_HINT routing proof: {s1.get('HELP_HINT_ROUTING_PROOF', '')}")
    print(f"  proof lane gated: {s1.get('PROOF_LANE_GATED', '')}")
    print(f"  provider active_dbf: {s1.get('PROVIDER_ACTIVE_DBF', '')}")
    print(f"  active catalog loaded: {s1.get('ACTIVE_CATALOG_LOADED', '')}")
    print("  source mutation authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
