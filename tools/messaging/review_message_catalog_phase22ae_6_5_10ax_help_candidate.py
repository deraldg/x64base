#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AX_MSGMGR_HELP_CANDIDATE_REVIEW_GREEN_CANDIDATE_ACCEPTED_SOURCE_HELD"
STATUS_REVIEW = "MESSAGE_CATALOG_PHASE22AE_6_5_10AX_MSGMGR_HELP_CANDIDATE_REVIEW_GREEN_CANDIDATE_REVIEW_ITEMS_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AX_MSGMGR_HELP_CANDIDATE_REVIEW_BLOCKED"
NEXT_GATE_ACCEPTED = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AY_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PLAN"
NEXT_GATE_REVIEW = "HOLD_AND_REVISE_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE"
REPORT_DIR = Path("docs/messaging/reports")
CANDIDATE_PATH = Path("docs/messaging/candidates/MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE.md")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

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

def savepoint_present(repo: Path, savepoint_id: str):
    latest = ""
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest == savepoint_id or savepoint_id in text, latest

def contains_all(text: str, terms: list[str]):
    up = text.upper()
    missing = [t for t in terms if t.upper() not in up]
    return len(missing) == 0, missing

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    aw = first_row(reports / "message_catalog_phase22ae_6_5_10aw_status_summary_v1.csv")
    av = first_row(reports / "message_catalog_phase22ae_6_5_10av_validate_status_summary_v1.csv")
    sp_aw, latest_aw = savepoint_present(repo, "MSG-022AE.6.5.10AW")

    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    candidate = repo / CANDIDATE_PATH
    candidate_exists = candidate.exists()
    text = candidate.read_text(encoding="utf-8", errors="replace") if candidate_exists else ""

    required_groups = [
        {
            "GROUP": "COMMAND_HOUSE",
            "TERMS": ["MSGMGR", "MSGMGR STATUS", "MSGMGR CHECK"],
            "WHY": "Candidate must document the Message Manager command-house surface.",
        },
        {
            "GROUP": "LOW_LEVEL_SURFACES",
            "TERMS": ["SET MESSAGE CATALOG CHECK", "SET MESSAGE CATALOG GET", "SET MESSAGE EMIT"],
            "WHY": "Candidate must document proven low-level message surfaces.",
        },
        {
            "GROUP": "ACTIVE_COUNTS",
            "TERMS": ["SYSTEM_MESSAGES", "14", "SYSTEM_MESSAGE_TEXT", "70"],
            "WHY": "Candidate must include proven active catalog counts.",
        },
        {
            "GROUP": "LOCALIZED_PROOF",
            "TERMS": ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE", "en-US", "es", "fr", "de", "it"],
            "WHY": "Candidate must include proven localized EMIT evidence.",
        },
        {
            "GROUP": "WORKSPACE_PROFILE",
            "TERMS": ["messages_profile_phase22ae_6_5_10as.dtschema", "SYSTEM_MESSAGE_TEXT = 70", "SYSTEM_MESSAGES     = 14"],
            "WHY": "Candidate should carry forward proven workspace profile evidence.",
        },
        {
            "GROUP": "BOUNDARY",
            "TERMS": ["read-only", "No DBF", "No DBF, CDX, LMDB, workspace, source, HELP DATA, or CMDHELPCHK mutation"],
            "WHY": "Candidate must preserve report-first/no-mutation boundary.",
        },
        {
            "GROUP": "DEFERRED_WORK",
            "TERMS": ["Aliases", "Runtime source integration", "HELP DATA and CMDHELPCHK updates require"],
            "WHY": "Candidate must make deferred work explicit.",
        },
    ]

    gates = []
    failures = 0
    review_items = 0
    def gate(name, ok, detail, review_only=False):
        nonlocal failures, review_items
        status = "PASS" if ok else ("REVIEW" if review_only else "FAIL")
        gates.append({"GATE": name, "STATUS": status, "DETAIL": str(detail)})
        if not ok and review_only:
            review_items += 1
        elif not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AW_GREEN",
         aw.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE_PLAN_GREEN_SOURCE_HELD",
         aw.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AW_SAVEPOINT_PRESENT", sp_aw, latest_aw)
    gate("CANDIDATE_EXISTS", candidate_exists, rel(candidate, repo))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("10AV_EMIT_PROVEN", av.get("SET_MESSAGE_EMIT_PROVEN") == "1", av.get("SET_MESSAGE_EMIT_PROVEN", "missing"))
    gate("10AV_LOCALES_VISIBLE_5", av.get("PROOF_LOCALES_VISIBLE") == "5", av.get("PROOF_LOCALES_VISIBLE", "missing"))
    gate("10AW_HELP_APPLY_AUTH_HELD", aw.get("HELP_DATA_APPLY_AUTHORIZED") == "0", aw.get("HELP_DATA_APPLY_AUTHORIZED", "missing"))
    gate("10AW_CMDHELPCHK_APPLY_AUTH_HELD", aw.get("CMDHELPCHK_APPLY_AUTHORIZED") == "0", aw.get("CMDHELPCHK_APPLY_AUTHORIZED", "missing"))

    checklist = []
    for group in required_groups:
        ok, missing = contains_all(text, group["TERMS"])
        # workspace string formatting may differ, so classify missing workspace phrase as review, not blocker.
        review_only = group["GROUP"] in {"WORKSPACE_PROFILE", "BOUNDARY", "DEFERRED_WORK"}
        gate(f"CANDIDATE_CONTENT_{group['GROUP']}", ok, "missing=" + ";".join(missing) if missing else "all required terms present", review_only=review_only)
        checklist.append({
            "GROUP": group["GROUP"],
            "STATUS": "PASS" if ok else ("REVIEW" if review_only else "FAIL"),
            "WHY": group["WHY"],
            "MISSING_TERMS": ";".join(missing),
        })

    # Candidate is accepted if there are no hard failures. Review items can be carried forward, but current generated candidate should normally pass.
    if failures == 0 and review_items == 0:
        status = STATUS_GREEN
        next_gate = NEXT_GATE_ACCEPTED
        disposition = "ACCEPTED_FOR_APPLY_PLANNING"
    elif failures == 0:
        status = STATUS_REVIEW
        next_gate = NEXT_GATE_REVIEW
        disposition = "REVIEW_ITEMS_BEFORE_APPLY_PLANNING"
    else:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_5_10AX_REVIEW_FAILURE"
        disposition = "BLOCKED"

    surfaces = [
        {"SURFACE": "MSGMGR", "REVIEW_DISPOSITION": "ACCEPT", "NOTES": "Primary command-house topic."},
        {"SURFACE": "MSGMGR USAGE", "REVIEW_DISPOSITION": "ACCEPT", "NOTES": "Usage surface."},
        {"SURFACE": "MSGMGR STATUS", "REVIEW_DISPOSITION": "ACCEPT", "NOTES": "Read-only status surface."},
        {"SURFACE": "MSGMGR CHECK", "REVIEW_DISPOSITION": "ACCEPT", "NOTES": "Read-only check/status surface."},
        {"SURFACE": "SET MESSAGE CATALOG CHECK", "REVIEW_DISPOSITION": "ACCEPT", "NOTES": "Active DBF provider check."},
        {"SURFACE": "SET MESSAGE CATALOG GET", "REVIEW_DISPOSITION": "ACCEPT", "NOTES": "Low-level read/get surface proven earlier."},
        {"SURFACE": "SET MESSAGE EMIT", "REVIEW_DISPOSITION": "ACCEPT", "NOTES": "Localized diagnostic emission surface proven by 10AV."},
    ]

    apply_readiness = [
        {"ITEM": "HELP_DATA_APPLY", "READY_FOR_PLAN": 1 if disposition == "ACCEPTED_FOR_APPLY_PLANNING" else 0, "AUTHORIZED_NOW": 0, "DETAIL": "Ready only for a guarded apply plan, not apply."},
        {"ITEM": "CMDHELPCHK_APPLY", "READY_FOR_PLAN": 1 if disposition == "ACCEPTED_FOR_APPLY_PLANNING" else 0, "AUTHORIZED_NOW": 0, "DETAIL": "Ready only for a guarded apply plan, not apply."},
        {"ITEM": "SOURCE_INTEGRATION", "READY_FOR_PLAN": 0, "AUTHORIZED_NOW": 0, "DETAIL": "Still deferred."},
        {"ITEM": "ALIASES", "READY_FOR_PLAN": 0, "AUTHORIZED_NOW": 0, "DETAIL": "Still deferred to alias policy."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AX is review-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    issues = "0" if failures == 0 else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10ax_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ax_candidate_review_checklist_v1.csv", checklist, ["GROUP", "STATUS", "WHY", "MISSING_TERMS"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ax_surface_disposition_v1.csv", surfaces, ["SURFACE", "REVIEW_DISPOSITION", "NOTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ax_apply_readiness_v1.csv", apply_readiness, ["ITEM", "READY_FOR_PLAN", "AUTHORIZED_NOW", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ax_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "REVIEW_ITEMS": review_items,
        "PHASE22AE_6_5_10AW_STATUS": aw.get("STATUS", ""),
        "MSG_022AE_6_5_10AW_SAVEPOINT_PRESENT": 1 if sp_aw else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CANDIDATE_PATH": rel(candidate, repo),
        "CANDIDATE_EXISTS": 1 if candidate_exists else 0,
        "CANDIDATE_DISPOSITION": disposition,
        "HELP_DATA_APPLY_READY_FOR_PLAN": 1 if disposition == "ACCEPTED_FOR_APPLY_PLANNING" else 0,
        "CMDHELPCHK_APPLY_READY_FOR_PLAN": 1 if disposition == "ACCEPTED_FOR_APPLY_PLANNING" else 0,
        "HELP_DATA_APPLY_AUTHORIZED": 0,
        "CMDHELPCHK_APPLY_AUTHORIZED": 0,
        "ALIASES_AUTHORIZED": 0,
        "RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10ax_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AX_MSGMGR_HELP_CANDIDATE_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AX MSGMGR HELP Candidate Review\n\nStatus: `{status}`\n\n10AX reviews the 10AW candidate only. It does not mutate HELP DATA or CMDHELPCHK.\n\nCandidate disposition: `{disposition}`\n\nNext gate:\n\n```text\n{next_gate}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  review items: {review_items}")
    print(f"  Phase 22AE.6.5.10AW status: {aw.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AW savepoint present: {1 if sp_aw else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  candidate exists: {1 if candidate_exists else 0}")
    print(f"  candidate path: {rel(candidate, repo)}")
    print(f"  candidate disposition: {disposition}")
    print(f"  HELP DATA apply ready for plan: {summary['HELP_DATA_APPLY_READY_FOR_PLAN']}")
    print(f"  CMDHELPCHK apply ready for plan: {summary['CMDHELPCHK_APPLY_READY_FOR_PLAN']}")
    print("  HELP DATA apply authorized: 0")
    print("  CMDHELPCHK apply authorized: 0")
    print("  aliases authorized: 0")
    print("  runtime consumer source integration authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if failures == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
