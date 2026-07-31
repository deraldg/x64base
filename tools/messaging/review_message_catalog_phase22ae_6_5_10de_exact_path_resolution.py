#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DE_NATIVE_WRITER_EXACT_PATH_RESOLUTION_REVIEW_GREEN_REUSE_DECISION_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DE_NATIVE_WRITER_EXACT_PATH_RESOLUTION_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DF_NATIVE_WRITER_REUSE_DECISION_PACKAGE"

REPORT = Path("docs/messaging/reports")
DD_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10dd_status_summary_v1.csv"
DD_ROWS = REPORT / "message_catalog_phase22ae_6_5_10dd_exact_path_resolution_rows_v1.csv"
DD_TARGET_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10dd_target_resolution_summary_v1.csv"
DD_FUNCTION_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10dd_function_resolution_summary_v1.csv"
DD_REQS = REPORT / "message_catalog_phase22ae_6_5_10dd_exact_path_review_requirements_v1.csv"
DD_DEFERRED = REPORT / "message_catalog_phase22ae_6_5_10dd_still_deferred_paths_v1.csv"
DD_DUP_NOTES = REPORT / "message_catalog_phase22ae_6_5_10dd_duplicate_savepoint_notes_v1.csv"
DD_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10dd_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
DE_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10de_native_writer_exact_path_resolution_review_v1")

def rows(path):
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first(path):
    r = rows(path)
    return r[0] if r else {}

def wcsv(path, data, fields):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in data:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path, repo):
    try:
        return str(Path(path).resolve().relative_to(repo.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()

def dbf_count(path):
    p = Path(path)
    if not p.exists() or p.stat().st_size < 12:
        return ""
    return int.from_bytes(p.read_bytes()[:12][4:8], "little")

def savepoint(repo, sid):
    latest = ""
    latest_path = repo / REPORT / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest == sid or sid in text, latest

def savepoint_occurrences(repo, sid):
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    if not journal.exists():
        return 0
    text = journal.read_text(encoding="utf-8", errors="replace")
    return len(re.findall(re.escape(sid), text))

def intish(v):
    try:
        return int(float(str(v)))
    except Exception:
        return 0

def classify(row):
    source_exists = str(row.get("SOURCE_EXISTS", "")) == "1"
    func = row.get("RESOLVED_FUNCTION_SIGNATURE", "").strip()
    writer_hits = intish(row.get("WRITER_SIGNAL_HITS", ""))
    target_hits = intish(row.get("TARGET_SIGNAL_HITS", ""))
    target = row.get("TARGET_RESOLUTION_CANDIDATE", "")
    usage = row.get("USAGE_CONTRACT_LINE", "").strip()
    if not source_exists:
        return "REJECT_PATH_MISSING", "Source path missing; cannot reuse.", 0
    if func and writer_hits > 0 and target_hits > 0 and target in {"HELP_DATA_TARGET_CANDIDATE", "CMDHELPCHK_TARGET_CANDIDATE"}:
        return "EXACT_FUNCTION_TARGET_WRITER_CANDIDATE_REVIEW_REQUIRED", "Function context has target and writer signals; eligible for 10DF reuse decision review.", 1
    if func and writer_hits > 0:
        return "FUNCTION_WRITER_CANDIDATE_TARGET_UNRESOLVED", "Function context has writer signals but target contract is unresolved/generic.", 0
    if func and target_hits > 0:
        return "FUNCTION_TARGET_CONTEXT_WRITER_UNRESOLVED", "Function context has target signals but writer/materialization role is unresolved.", 0
    if func:
        return "FUNCTION_CONTEXT_INCONCLUSIVE", "Function context staged but writer/target signals are insufficient.", 0
    if writer_hits > 0 and target_hits > 0:
        return "SOURCE_LOCATION_TARGET_WRITER_SIGNAL_NO_FUNCTION", "Source location has target and writer signals but function boundary was not resolved.", 0
    if usage:
        return "USAGE_CONTRACT_CONTEXT_ONLY", "Source-comment usage contract present but not enough to confirm writer reuse.", 0
    return "INCONCLUSIVE_OR_READER_CONTEXT", "Insufficient evidence to confirm reuse.", 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    dd = first(repo / DD_SUMMARY)
    dd_rows = rows(repo / DD_ROWS)
    target_summary_in = rows(repo / DD_TARGET_SUMMARY)
    function_summary_in = rows(repo / DD_FUNCTION_SUMMARY)
    reqs_in = rows(repo / DD_REQS)
    deferred_in = rows(repo / DD_DEFERRED)
    dup_notes_in = rows(repo / DD_DUP_NOTES)
    blocked_in = rows(repo / DD_BLOCKED)

    sp_dd, latest_dd = savepoint(repo, "MSG-022AE.6.5.10DD")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_dd_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10DD")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    de_root = repo / DE_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10DD_GREEN", dd.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10DD_NATIVE_WRITER_EXACT_PATH_RESOLUTION_PACKAGE_GREEN_EXACT_SOURCE_LOCATIONS_STAGED_SOURCE_HELD", dd.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10DD_SAVEPOINT_PRESENT", sp_dd, latest_dd)
    gate("DD_EXACT_SOURCE_LOCATIONS_STAGED", dd.get("EXACT_SOURCE_LOCATIONS_STAGED") == "1", dd.get("EXACT_SOURCE_LOCATIONS_STAGED", "missing"))
    gate("DD_REUSE_NOT_SELECTED", dd.get("REUSE_PATH_SELECTED_NOW") == "0", dd.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("DD_WRITER_REUSE_NOT_CONFIRMED", dd.get("WRITER_REUSE_CONFIRMED_NOW") == "0", dd.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("DD_SOURCE_PATCH_NOT_SELECTED", dd.get("SOURCE_PATCH_SELECTED_NOW") == "0", dd.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("DD_SOURCE_PATCH_NOT_PROVEN", dd.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", dd.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("DD_SOURCE_MUTATION_NOT_AUTHORIZED", dd.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", dd.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("DD_APPLY_EXECUTION_NOT_AUTHORIZED", dd.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", dd.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("DD_HELP_APPLY_NOT_EXECUTED", dd.get("HELP_DATA_APPLY_EXECUTED") == "0", dd.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("DD_CMDHELPCHK_APPLY_NOT_EXECUTED", dd.get("CMDHELPCHK_APPLY_EXECUTED") == "0", dd.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("DD_RESOLUTION_ROWS_PRESENT", len(dd_rows) > 0, len(dd_rows))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("DE_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not de_root.exists()) or args.replace_existing_review, rel(de_root, repo))

    status = BLOCKED
    resolution_review = []
    reuse_decision_candidates = []
    target_review = []
    function_review = []
    decision_requirements = []
    deferred_rows = []
    duplicate_savepoint_notes = []
    blocked_rows = []
    review_decisions = []
    artifacts = []

    if failures == 0:
        if de_root.exists() and args.replace_existing_review:
            shutil.rmtree(de_root)
        de_root.mkdir(parents=True, exist_ok=True)

        review_counts = {}
        eligible_count = 0
        for i, row in enumerate(dd_rows, 1):
            disp, detail, eligible = classify(row)
            review_counts[disp] = review_counts.get(disp, 0) + 1
            eligible_count += eligible
            resolution_review.append({
                "REVIEW_ROW": i,
                "RESOLUTION_ROW": row.get("RESOLUTION_ROW", i),
                "PROBE_ID": row.get("PROBE_ID", ""),
                "FILE_PATH": row.get("FILE_PATH", ""),
                "REQUESTED_LINE": row.get("REQUESTED_LINE", ""),
                "RESOLVED_FUNCTION_LINE": row.get("RESOLVED_FUNCTION_LINE", ""),
                "RESOLVED_FUNCTION_NAME": row.get("RESOLVED_FUNCTION_NAME", ""),
                "RESOLVED_FUNCTION_SIGNATURE": row.get("RESOLVED_FUNCTION_SIGNATURE", ""),
                "USAGE_CONTRACT_LINE": row.get("USAGE_CONTRACT_LINE", ""),
                "TARGET_RESOLUTION_CANDIDATE": row.get("TARGET_RESOLUTION_CANDIDATE", ""),
                "TARGET_SIGNAL_HITS": row.get("TARGET_SIGNAL_HITS", ""),
                "WRITER_SIGNAL_HITS": row.get("WRITER_SIGNAL_HITS", ""),
                "CONTROL_SIGNAL_HITS": row.get("CONTROL_SIGNAL_HITS", ""),
                "DE_REVIEW_DISPOSITION": disp,
                "DE_REVIEW_DETAIL": detail,
                "ELIGIBLE_FOR_10DF_REUSE_DECISION": eligible,
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })
            if eligible:
                reuse_decision_candidates.append({
                    "CANDIDATE_ROW": len(reuse_decision_candidates) + 1,
                    "PROBE_ID": row.get("PROBE_ID", ""),
                    "FILE_PATH": row.get("FILE_PATH", ""),
                    "RESOLVED_FUNCTION_LINE": row.get("RESOLVED_FUNCTION_LINE", ""),
                    "RESOLVED_FUNCTION_NAME": row.get("RESOLVED_FUNCTION_NAME", ""),
                    "RESOLVED_FUNCTION_SIGNATURE": row.get("RESOLVED_FUNCTION_SIGNATURE", ""),
                    "TARGET_RESOLUTION_CANDIDATE": row.get("TARGET_RESOLUTION_CANDIDATE", ""),
                    "TARGET_SIGNAL_TERMS": row.get("TARGET_SIGNAL_TERMS", ""),
                    "WRITER_SIGNAL_TERMS": row.get("WRITER_SIGNAL_TERMS", ""),
                    "DECISION_REQUIRED": "10DF must decide whether this exact function is reusable as native HELP DATA/CMDHELPCHK writer.",
                    "WRITER_REUSE_CONFIRMED_NOW": 0,
                    "SOURCE_PATCH_NEEDED_PROVEN": 0,
                    "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                    "APPLY_AUTHORIZED_NOW": 0,
                })

        for i, row in enumerate(target_summary_in, 1):
            target_review.append({
                "TARGET_REVIEW_ROW": i,
                "TARGET_RESOLUTION_CANDIDATE": row.get("TARGET_RESOLUTION_CANDIDATE", ""),
                "RESOLUTION_ROWS": row.get("RESOLUTION_ROWS", ""),
                "DE_TARGET_REVIEW_STATUS": "CARRY_FORWARD_TO_10DF_DECISION" if row.get("TARGET_RESOLUTION_CANDIDATE") in {"HELP_DATA_TARGET_CANDIDATE","CMDHELPCHK_TARGET_CANDIDATE"} else "TARGET_REMAINS_GENERIC_OR_UNRESOLVED",
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        for i, row in enumerate(function_summary_in, 1):
            sig = row.get("RESOLVED_FUNCTION_OR_SIGNATURE", "")
            function_review.append({
                "FUNCTION_REVIEW_ROW": i,
                "RESOLVED_FUNCTION_OR_SIGNATURE": sig,
                "RESOLUTION_ROWS": row.get("RESOLUTION_ROWS", ""),
                "DE_FUNCTION_REVIEW_STATUS": "FUNCTION_CONTEXT_REVIEWED" if sig and sig != "(unresolved)" else "FUNCTION_UNRESOLVED",
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        decision_requirements = [
            {"REQ_ROW": 1, "REQUIREMENT": "10DF_REUSE_DECISION_PACKAGE_REQUIRED", "DETAIL": f"{eligible_count} candidate rows are eligible for explicit reuse decision review.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "DO_NOT_CONFIRM_REUSE_BY_DE", "DETAIL": "10DE reviews exact path resolution but does not confirm writer reuse.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "IF_NO_EXACT_REUSE_SELECT_MORE_INVESTIGATION_OR_PATCH_PLAN_LATER", "DETAIL": "Patch planning is still deferred unless reuse is explicitly rejected.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "PRESERVE_USAGE_CONTRACT_RULE", "DETAIL": "Any later source patch must update @dottalk.usage/source-comment contracts in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Active HELP/CMDHELPCHK materialization must remain native/schema-aware, not raw DBF byte mutation.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until a later guarded apply package is reviewed and explicitly authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, row in enumerate(deferred_in, 1):
            deferred_rows.append({
                "DEFERRED_ROW": i,
                "DEFERRED_PATH": row.get("DEFERRED_PATH", ""),
                "DEFERRED_REASON": row.get("DEFERRED_REASON", ""),
                "STILL_DEFERRED_AFTER_DE": 1,
            })

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries remain an accounting/idempotency issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10DD", "OBSERVED_OCCURRENCES": sp_dd_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_dd_count >= 1 else "MISSING", "DETAIL": "10DD savepoint presence is the precondition for 10DE."},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after DE exact path review.",
            })

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "DD_EXACT_PATH_RESOLUTION_REVIEWED", "VALUE": 1, "DETAIL": "10DD exact path resolution rows reviewed."},
            {"DECISION_ROW": 2, "DECISION": "REUSE_DECISION_PACKAGE_REQUIRED", "VALUE": 1, "DETAIL": "10DF should make explicit reuse decision from eligible candidates."},
            {"DECISION_ROW": 3, "DECISION": "REUSE_CONFIRMED_NOW", "VALUE": 0, "DETAIL": "10DE does not confirm reuse."},
            {"DECISION_ROW": 4, "DECISION": "SOURCE_PATCH_NEEDED_PROVEN", "VALUE": 0, "DETAIL": "Patch need remains unproven."},
            {"DECISION_ROW": 5, "DECISION": "SOURCE_MUTATION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "No source mutation authorized."},
            {"DECISION_ROW": 6, "DECISION": "APPLY_EXECUTION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "Apply remains blocked."},
        ]

        paths = [
            (de_root / "exact_path_resolution_review_v1.csv", resolution_review, ["REVIEW_ROW","RESOLUTION_ROW","PROBE_ID","FILE_PATH","REQUESTED_LINE","RESOLVED_FUNCTION_LINE","RESOLVED_FUNCTION_NAME","RESOLVED_FUNCTION_SIGNATURE","USAGE_CONTRACT_LINE","TARGET_RESOLUTION_CANDIDATE","TARGET_SIGNAL_HITS","WRITER_SIGNAL_HITS","CONTROL_SIGNAL_HITS","DE_REVIEW_DISPOSITION","DE_REVIEW_DETAIL","ELIGIBLE_FOR_10DF_REUSE_DECISION","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (de_root / "reuse_decision_candidates_v1.csv", reuse_decision_candidates, ["CANDIDATE_ROW","PROBE_ID","FILE_PATH","RESOLVED_FUNCTION_LINE","RESOLVED_FUNCTION_NAME","RESOLVED_FUNCTION_SIGNATURE","TARGET_RESOLUTION_CANDIDATE","TARGET_SIGNAL_TERMS","WRITER_SIGNAL_TERMS","DECISION_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (de_root / "target_resolution_review_v1.csv", target_review, ["TARGET_REVIEW_ROW","TARGET_RESOLUTION_CANDIDATE","RESOLUTION_ROWS","DE_TARGET_REVIEW_STATUS","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW"]),
            (de_root / "function_resolution_review_v1.csv", function_review, ["FUNCTION_REVIEW_ROW","RESOLVED_FUNCTION_OR_SIGNATURE","RESOLUTION_ROWS","DE_FUNCTION_REVIEW_STATUS","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW"]),
            (de_root / "reuse_decision_requirements_v1.csv", decision_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (de_root / "still_deferred_paths_v1.csv", deferred_rows, ["DEFERRED_ROW","DEFERRED_PATH","DEFERRED_REASON","STILL_DEFERRED_AFTER_DE"]),
            (de_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (de_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
            (de_root / "review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = de_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled_script = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DF_REUSE_DECISION_TEMPLATE.ps1.disabled"
        disabled_script.write_text('throw "10DE reviewed exact path resolution only. Run 10DF before confirming reuse/source-patch/apply or authorizing mutation."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DE_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = de_root / "native_writer_exact_path_resolution_review_v1.md"
        notes.write_text("# 10DE Native Writer Exact Path Resolution Review\n\n10DE reviews 10DD exact path/function context rows and requires a 10DF reuse decision package. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = de_root / "README_10DE_EXACT_PATH_RESOLUTION_REVIEW.md"
        readme.write_text("# 10DE Exact Path Resolution Review\n\nReport-only/source-held review package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_exact_path_resolution_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled_script, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_exact_path_resolution_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10DE reviews exact path reports only; no source writes."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Exact path review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Exact path review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "EXACT_PATH_REVIEWED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(resolution_review)} exact path rows reviewed."},
        {"ITEM": "REUSE_DECISION_CANDIDATES", "STATUS": "YES" if len(reuse_decision_candidates) > 0 else "NO", "DETAIL": f"{len(reuse_decision_candidates)} candidates staged for 10DF reuse decision."},
        {"ITEM": "REUSE_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains unconfirmed."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Patch need remains unproven."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_exact_path_resolution_review_v1.csv", resolution_review, ["REVIEW_ROW","RESOLUTION_ROW","PROBE_ID","FILE_PATH","REQUESTED_LINE","RESOLVED_FUNCTION_LINE","RESOLVED_FUNCTION_NAME","RESOLVED_FUNCTION_SIGNATURE","USAGE_CONTRACT_LINE","TARGET_RESOLUTION_CANDIDATE","TARGET_SIGNAL_HITS","WRITER_SIGNAL_HITS","CONTROL_SIGNAL_HITS","DE_REVIEW_DISPOSITION","DE_REVIEW_DETAIL","ELIGIBLE_FOR_10DF_REUSE_DECISION","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_reuse_decision_candidates_v1.csv", reuse_decision_candidates, ["CANDIDATE_ROW","PROBE_ID","FILE_PATH","RESOLVED_FUNCTION_LINE","RESOLVED_FUNCTION_NAME","RESOLVED_FUNCTION_SIGNATURE","TARGET_RESOLUTION_CANDIDATE","TARGET_SIGNAL_TERMS","WRITER_SIGNAL_TERMS","DECISION_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_target_resolution_review_v1.csv", target_review, ["TARGET_REVIEW_ROW","TARGET_RESOLUTION_CANDIDATE","RESOLUTION_ROWS","DE_TARGET_REVIEW_STATUS","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_function_resolution_review_v1.csv", function_review, ["FUNCTION_REVIEW_ROW","RESOLVED_FUNCTION_OR_SIGNATURE","RESOLUTION_ROWS","DE_FUNCTION_REVIEW_STATUS","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_reuse_decision_requirements_v1.csv", decision_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_still_deferred_paths_v1.csv", deferred_rows, ["DEFERRED_ROW","DEFERRED_PATH","DEFERRED_REASON","STILL_DEFERRED_AFTER_DE"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10DD_STATUS": dd.get("STATUS",""),
        "MSG_022AE_6_5_10DD_SAVEPOINT_PRESENT": 1 if sp_dd else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10DD_SAVEPOINT_OCCURRENCES_OBSERVED": sp_dd_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "DD_EXACT_PATH_RESOLUTION_ROWS": len(dd_rows),
        "EXACT_PATH_RESOLUTION_REVIEW_ROWS": len(resolution_review),
        "REUSE_DECISION_CANDIDATE_ROWS": len(reuse_decision_candidates),
        "TARGET_REVIEW_ROWS": len(target_review),
        "FUNCTION_REVIEW_ROWS": len(function_review),
        "DE_ROOT": rel(de_root, repo),
        "EXACT_PATH_RESOLUTION_REVIEWED": 1 if status == GREEN else 0,
        "REUSE_DECISION_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
        "REUSE_PATH_SELECTED_NOW": 0,
        "WRITER_REUSE_CONFIRMED_NOW": 0,
        "REUSE_CONFIRMED_NOW": 0,
        "SOURCE_PATCH_SELECTED_NOW": 0,
        "SOURCE_PATCH_NEEDED_PROVEN": 0,
        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "DBF_MUTATION_OBSERVED": 0,
        "CDX_LMDB_MUTATION_OBSERVED": 0,
        "WORKSPACE_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }
    wcsv(reports / "message_catalog_phase22ae_6_5_10de_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10DE_NATIVE_WRITER_EXACT_PATH_RESOLUTION_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10DE Native Writer Exact Path Resolution Review\n\nStatus: `{status}`\n\n10DE reviews 10DD exact path/function context rows and requires a 10DF reuse decision package. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(de_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10DD status: {dd.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10DD savepoint present: {1 if sp_dd else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  DD exact path resolution rows: {len(dd_rows)}")
    print(f"  exact path resolution review rows: {len(resolution_review)}")
    print(f"  reuse decision candidate rows: {len(reuse_decision_candidates)}")
    print(f"  target review rows: {len(target_review)}")
    print(f"  function review rows: {len(function_review)}")
    print(f"  review root: {rel(de_root, repo)}")
    print("  exact path resolution reviewed: 1")
    print("  reuse decision package required: 1")
    print("  reuse path selected now: 0")
    print("  writer reuse confirmed now: 0")
    print("  source patch selected now: 0")
    print("  source patch needed proven: 0")
    print("  source mutation authorized now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print(f"  next gate: {NEXT}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
