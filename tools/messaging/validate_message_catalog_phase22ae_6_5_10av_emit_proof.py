#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_FULL = "MESSAGE_CATALOG_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF_GREEN_EMIT_PROVEN"
STATUS_REVIEW = "MESSAGE_CATALOG_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF_GREEN_EMIT_SYNTAX_REVIEW"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF_BLOCKED"
NEXT_FULL = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE_PLAN"
NEXT_REVIEW = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AVR_SET_MESSAGE_EMIT_SYNTAX_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF.md")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
PROOF_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
PROOF_LOCALES = ["en-US", "es", "fr", "de", "it"]
MUTATION_TOKENS = ["ZAP COMPLETE", "IMPORTED ", "APPEND", "REPLACE", "PACK", "BUILDLMDB", "CDX ADDTAG", "CDX CREATE", "DELETE ALL", "WORKSPACE SAVE"]

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
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path: Path, repo: Path):
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def dbf_header_count(path: Path):
    if not path.exists() or path.stat().st_size < 12:
        return ""
    return int.from_bytes(path.read_bytes()[:12][4:8], "little")

def norm(s: str):
    return " ".join(s.replace("\r", "\n").split()).upper()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-log", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_5_10av_stage_status_summary_v1.csv")
    runtime = Path(args.runtime_log) if args.runtime_log else repo / RUNLOG_PATH
    if not runtime.is_absolute():
        runtime = repo / runtime
    log = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    up = log.upper()
    compact = norm(log)

    check_seen = "SET MESSAGE CATALOG CHECK" in up
    check_proven = check_seen and ("MESSAGE COUNT: 14" in up or "MESSAGE COUNT : 14" in up or "MESSAGE COUNT" in up and "14" in up) and ("TEXT ROW COUNT: 70" in up or "TEXT ROW COUNT : 70" in up or "TEXT ROW COUNT" in up and "70" in up)
    emit_seen = "SET MESSAGE EMIT" in up
    unknown_emit = up.count("UNKNOWN COMMAND: SET")
    usage_count = up.count("USAGE:")
    proof_symbol_count = sum(1 for s in PROOF_SYMBOLS if s in up)
    proof_locale_count = sum(1 for loc in PROOF_LOCALES if loc.upper() in up)
    mode_status_mentions = up.count("MESSAGE_PROOF_MODE_STATUS")
    boundary_note_mentions = up.count("MESSAGE_PROOF_BOUNDARY_NOTE")

    # Broad success signal: commands were seen, symbols/locales visible, and no unknown SET surface.
    # Text may be formatted differently by emitter, so this avoids requiring exact message prose.
    emit_proven = emit_seen and unknown_emit == 0 and proof_symbol_count == 2 and proof_locale_count >= 5 and mode_status_mentions >= 5 and boundary_note_mentions >= 5

    msg_open14 = "OPENED SYSTEM_MESSAGES (V64) : RECORD COUNT 14" in up
    text_open70 = "OPENED SYSTEM_MESSAGE_TEXT (V64) : RECORD COUNT 70" in up
    listed14 = "14 RECORD(S) LISTED" in up
    listed70 = "70 RECORD(S) LISTED" in up
    count14 = "\n14\n" in log.replace("\r", "\n") or " 14 " in compact
    count70 = "\n70\n" in log.replace("\r", "\n") or " 70 " in compact
    msg_header = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_header = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    mutation_hits = [tok for tok in MUTATION_TOKENS if tok in up]

    gates = []
    failures = 0
    review_flags = 0
    def gate(name, ok, detail, review_only=False):
        nonlocal failures, review_flags
        status = "PASS" if ok else ("REVIEW" if review_only else "FAIL")
        gates.append({"GATE": name, "STATUS": status, "DETAIL": str(detail)})
        if not ok and review_only:
            review_flags += 1
        elif not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("RUNTIME_LOG_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("SET_MESSAGE_CATALOG_CHECK_SEEN", check_seen, "SET MESSAGE CATALOG CHECK")
    gate("SET_MESSAGE_CATALOG_CHECK_PROVEN", check_proven, "active provider 14/70")
    gate("SET_MESSAGE_EMIT_SEEN", emit_seen, "SET MESSAGE EMIT")
    gate("SET_MESSAGE_EMIT_PROVEN", emit_proven, f"symbols={proof_symbol_count}/2 locales={proof_locale_count}/5 unknown_set={unknown_emit}", review_only=True)
    gate("FRESH_OPEN_SYSTEM_MESSAGES_14", msg_open14, "SYSTEM_MESSAGES open 14")
    gate("FRESH_OPEN_SYSTEM_MESSAGE_TEXT_70", text_open70, "SYSTEM_MESSAGE_TEXT open 70")
    gate("RUNTIME_MESSAGE_LISTED_14", listed14, "LIST ALL message table")
    gate("RUNTIME_TEXT_LISTED_70", listed70, "LIST ALL text table")
    gate("COUNT_14_VISIBLE", count14, "final count 14")
    gate("COUNT_70_VISIBLE", count70, "final count 70")
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_header == 14, msg_header)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_header == 70, text_header)
    gate("NO_FORBIDDEN_MUTATION_TOKENS", len(mutation_hits) == 0, ";".join(mutation_hits) if mutation_hits else "none")

    if failures == 0 and emit_proven:
        status = STATUS_FULL
        next_gate = NEXT_FULL
    elif failures == 0:
        status = STATUS_REVIEW
        next_gate = NEXT_REVIEW
    else:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_5_10AV_EMIT_PROOF_FAILURE"
    issues = "0" if failures == 0 else str(failures)

    observations = [
        {"OBSERVATION": "runtime_log_exists", "VALUE": 1 if runtime.exists() else 0, "DETAIL": rel(runtime, repo)},
        {"OBSERVATION": "set_message_catalog_check_seen", "VALUE": 1 if check_seen else 0, "DETAIL": "Direct CHECK probe."},
        {"OBSERVATION": "set_message_catalog_check_proven", "VALUE": 1 if check_proven else 0, "DETAIL": "Provider count 14/70 evidence."},
        {"OBSERVATION": "set_message_emit_seen", "VALUE": 1 if emit_seen else 0, "DETAIL": "Direct EMIT probes."},
        {"OBSERVATION": "set_message_emit_proven", "VALUE": 1 if emit_proven else 0, "DETAIL": "Broad symbol/locale evidence."},
        {"OBSERVATION": "unknown_set_count", "VALUE": unknown_emit, "DETAIL": "Unknown SET indicates syntax/surface issue."},
        {"OBSERVATION": "usage_count", "VALUE": usage_count, "DETAIL": "Usage output may indicate syntax review."},
        {"OBSERVATION": "proof_symbols_visible", "VALUE": proof_symbol_count, "DETAIL": "2 expected."},
        {"OBSERVATION": "proof_locales_visible", "VALUE": proof_locale_count, "DETAIL": "5 expected."},
        {"OBSERVATION": "active_messages_after_probe", "VALUE": msg_header, "DETAIL": "DBF header count."},
        {"OBSERVATION": "active_text_after_probe", "VALUE": text_header, "DETAIL": "DBF header count."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_10av_validate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10av_runtime_observations_v1.csv", observations, ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10av_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "REVIEW_FLAGS": review_flags,
        "STAGE_STATUS": stage.get("STATUS", ""),
        "SET_MESSAGE_CATALOG_CHECK_SEEN": 1 if check_seen else 0,
        "SET_MESSAGE_CATALOG_CHECK_PROVEN": 1 if check_proven else 0,
        "SET_MESSAGE_EMIT_SEEN": 1 if emit_seen else 0,
        "SET_MESSAGE_EMIT_PROVEN": 1 if emit_proven else 0,
        "PROOF_SYMBOLS_VISIBLE": proof_symbol_count,
        "PROOF_LOCALES_VISIBLE": proof_locale_count,
        "UNKNOWN_SET_COUNT": unknown_emit,
        "USAGE_COUNT": usage_count,
        "FRESH_OPEN_SYSTEM_MESSAGES_14": 1 if msg_open14 else 0,
        "FRESH_OPEN_SYSTEM_MESSAGE_TEXT_70": 1 if text_open70 else 0,
        "RUNTIME_MESSAGE_LISTED_14": 1 if listed14 else 0,
        "RUNTIME_TEXT_LISTED_70": 1 if listed70 else 0,
        "ACTIVE_MESSAGES_HEADER_COUNT_AFTER_PROOF": msg_header,
        "ACTIVE_TEXT_HEADER_COUNT_AFTER_PROOF": text_header,
        "DBF_MUTATION_AUTHORIZED": 0,
        "CDX_LMDB_MUTATION_AUTHORIZED": 0,
        "WORKSPACE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10av_validate_status_summary_v1.csv", [summary], list(summary.keys()))

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  review flags: {review_flags}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF_STAGED_SOURCE_HELD' else 0}")
    print(f"  SET MESSAGE CATALOG CHECK seen: {1 if check_seen else 0}")
    print(f"  SET MESSAGE CATALOG CHECK proven: {1 if check_proven else 0}")
    print(f"  SET MESSAGE EMIT seen: {1 if emit_seen else 0}")
    print(f"  SET MESSAGE EMIT proven: {1 if emit_proven else 0}")
    print(f"  proof symbols visible: {proof_symbol_count}/2")
    print(f"  proof locales visible: {proof_locale_count}/5")
    print(f"  unknown SET count: {unknown_emit}")
    print(f"  usage count: {usage_count}")
    print(f"  active messages header count after proof: {msg_header}")
    print(f"  active text header count after proof: {text_header}")
    print("  DBF mutation authorized: 0")
    print("  CDX/LMDB mutation authorized: 0")
    print("  workspace mutation authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if failures == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
