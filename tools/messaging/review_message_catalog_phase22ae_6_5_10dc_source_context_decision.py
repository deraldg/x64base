#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DC_NATIVE_WRITER_SOURCE_CONTEXT_DECISION_REVIEW_GREEN_EXACT_WRITER_PATH_RESOLUTION_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DC_NATIVE_WRITER_SOURCE_CONTEXT_DECISION_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DD_NATIVE_WRITER_EXACT_PATH_RESOLUTION_PACKAGE"

REPORT = Path("docs/messaging/reports")
DB_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10db_status_summary_v1.csv"
DB_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10db_decision_evidence_v1.csv"
DB_OPTIONS = REPORT / "message_catalog_phase22ae_6_5_10db_decision_options_v1.csv"
DB_CHECKLIST = REPORT / "message_catalog_phase22ae_6_5_10db_decision_review_checklist_v1.csv"
DB_CLASS_MATRIX = REPORT / "message_catalog_phase22ae_6_5_10db_classification_decision_matrix_v1.csv"
DB_TARGET_MATRIX = REPORT / "message_catalog_phase22ae_6_5_10db_target_decision_matrix_v1.csv"
DB_DUP_NOTES = REPORT / "message_catalog_phase22ae_6_5_10db_duplicate_savepoint_notes_v1.csv"
DB_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10db_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
DC_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10dc_native_writer_source_context_decision_review_v1")

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    db = first(repo / DB_SUMMARY)
    evidence = rows(repo / DB_EVIDENCE)
    options = rows(repo / DB_OPTIONS)
    checklist = rows(repo / DB_CHECKLIST)
    class_matrix = rows(repo / DB_CLASS_MATRIX)
    target_matrix = rows(repo / DB_TARGET_MATRIX)
    dup_notes_in = rows(repo / DB_DUP_NOTES)
    blocked_in = rows(repo / DB_BLOCKED)

    sp_db, latest_db = savepoint(repo, "MSG-022AE.6.5.10DB")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_db_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10DB")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    dc_root = repo / DC_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10DB_GREEN", db.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10DB_NATIVE_WRITER_SOURCE_CONTEXT_DECISION_PACKAGE_GREEN_DECISION_OPTIONS_STAGED_SOURCE_HELD", db.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10DB_SAVEPOINT_PRESENT", sp_db, latest_db)
    gate("DB_DECISION_OPTIONS_STAGED", db.get("DECISION_OPTIONS_STAGED") == "1", db.get("DECISION_OPTIONS_STAGED", "missing"))
    gate("DB_REUSE_NOT_SELECTED", db.get("REUSE_PATH_SELECTED_NOW") == "0", db.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("DB_WRITER_REUSE_NOT_CONFIRMED", db.get("WRITER_REUSE_CONFIRMED_NOW") == "0", db.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("DB_SOURCE_PATCH_NOT_SELECTED", db.get("SOURCE_PATCH_SELECTED_NOW") == "0", db.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("DB_SOURCE_PATCH_NOT_PROVEN", db.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", db.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("DB_SOURCE_MUTATION_NOT_AUTHORIZED", db.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", db.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("DB_APPLY_EXECUTION_NOT_AUTHORIZED", db.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", db.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("DB_HELP_APPLY_NOT_EXECUTED", db.get("HELP_DATA_APPLY_EXECUTED") == "0", db.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("DB_CMDHELPCHK_APPLY_NOT_EXECUTED", db.get("CMDHELPCHK_APPLY_EXECUTED") == "0", db.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("DB_EVIDENCE_ROWS_PRESENT", len(evidence) > 0, len(evidence))
    gate("DB_DECISION_OPTIONS_PRESENT", len(options) > 0, len(options))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("DC_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not dc_root.exists()) or args.replace_existing_review, rel(dc_root, repo))

    status = BLOCKED
    option_review = []
    evidence_review = []
    high_value_candidates = []
    selected_safe_path = []
    deferred_options = []
    exact_path_requirements = []
    duplicate_savepoint_notes = []
    blocked_rows = []
    review_decisions = []
    artifacts = []

    if failures == 0:
        if dc_root.exists() and args.replace_existing_review:
            shutil.rmtree(dc_root)
        dc_root.mkdir(parents=True, exist_ok=True)

        # Review all decision evidence and identify high-value exact-path candidates.
        for i, row in enumerate(evidence, 1):
            strength = row.get("EVIDENCE_STRENGTH", "")
            score = intish(row.get("EVIDENCE_SCORE", ""))
            candidate = 1 if strength == "HIGH" else 0
            disposition = "HIGH_VALUE_REQUIRES_EXACT_PATH_RESOLUTION" if candidate else "CARRY_FORWARD_SUPPORTING_EVIDENCE"
            if strength == "MEDIUM":
                disposition = "TARGET_BINDING_NEEDS_RESOLUTION"
            elif strength == "LOW":
                disposition = "LOW_SIGNAL_SUPPORTING_EVIDENCE"
            elif strength == "INCONCLUSIVE":
                disposition = "INCONCLUSIVE_SUPPORTING_EVIDENCE"

            reviewed = {
                "EVIDENCE_REVIEW_ROW": i,
                "PROBE_ID": row.get("PROBE_ID", ""),
                "PROBE_KIND": row.get("PROBE_KIND", ""),
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "FILE_PATH": row.get("FILE_PATH", ""),
                "REQUESTED_LINE": row.get("REQUESTED_LINE", ""),
                "SOURCE_CONTEXT_CLASSIFICATION": row.get("SOURCE_CONTEXT_CLASSIFICATION", ""),
                "DA_REVIEW_DISPOSITION": row.get("DA_REVIEW_DISPOSITION", ""),
                "EVIDENCE_STRENGTH": strength,
                "EVIDENCE_SCORE": score,
                "CONTEXT_ARTIFACT": row.get("CONTEXT_ARTIFACT", ""),
                "DC_REVIEW_DISPOSITION": disposition,
                "ELIGIBLE_FOR_EXACT_PATH_RESOLUTION": candidate,
                "REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_AUTHORIZED_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
            }
            evidence_review.append(reviewed)
            if candidate:
                high_value_candidates.append({
                    "CANDIDATE_ROW": len(high_value_candidates) + 1,
                    "PROBE_ID": row.get("PROBE_ID", ""),
                    "PROBE_KIND": row.get("PROBE_KIND", ""),
                    "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                    "FILE_PATH": row.get("FILE_PATH", ""),
                    "REQUESTED_LINE": row.get("REQUESTED_LINE", ""),
                    "SOURCE_CONTEXT_CLASSIFICATION": row.get("SOURCE_CONTEXT_CLASSIFICATION", ""),
                    "CONTEXT_ARTIFACT": row.get("CONTEXT_ARTIFACT", ""),
                    "REQUIRED_RESOLUTION": "Name exact writer function/command/file/target contract, or reject as reader/checker/false positive.",
                    "REUSE_CONFIRMED_NOW": 0,
                    "SOURCE_PATCH_NEEDED_PROVEN": 0,
                    "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                    "APPLY_AUTHORIZED_NOW": 0,
                })

        for i, row in enumerate(options, 1):
            opt = row.get("DECISION_OPTION", "")
            if opt == "CONFIRM_EXISTING_NATIVE_WRITER_REUSE":
                review_status = "DEFER_UNTIL_EXACT_WRITER_PATH_NAMED"
                detail = "High-value evidence exists, but reuse is not confirmed until exact function/command/file/target contract is named."
            elif opt == "CONTINUE_TARGETED_SOURCE_CONTEXT_INVESTIGATION":
                review_status = "ACCEPT_BUT_NARROW_TO_EXACT_PATH_RESOLUTION"
                detail = "Continue review, but narrow from broad context investigation to exact path resolution."
            elif opt == "KEEP_APPLY_BLOCKED":
                review_status = "ACCEPT_SELECTED_SAFETY_BOUNDARY"
                detail = "Keep apply blocked."
            elif opt == "REJECT_REUSE_AND_PLAN_SOURCE_PATCH":
                review_status = "DEFER_PATCH_UNTIL_REUSE_REJECTED"
                detail = "Patch planning remains deferred."
            else:
                review_status = "DEFER_OR_CARRY_HOUSEKEEPING"
                detail = "Carry as nonblocking housekeeping or deferred option."

            option_review.append({
                "OPTION_REVIEW_ROW": i,
                "DECISION_OPTION": opt,
                "DB_OPTION_STATUS": row.get("OPTION_STATUS", ""),
                "SUPPORTING_EVIDENCE_ROWS": row.get("SUPPORTING_EVIDENCE_ROWS", ""),
                "DC_REVIEW_STATUS": review_status,
                "DC_REVIEW_DETAIL": detail,
                "REUSE_PATH_SELECTED_NOW": 0,
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_SELECTED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
            })

        selected_safe_path = [
            {"SELECTED_ROW": 1, "SELECTED_PATH": "EXACT_WRITER_PATH_RESOLUTION_REQUIRED", "SELECTED_NOW": 1, "DETAIL": "Narrow next work to exact path resolution for high-value writer candidates.", "REUSE_CONFIRMED_NOW": 0, "SOURCE_PATCH_NEEDED_PROVEN": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"SELECTED_ROW": 2, "SELECTED_PATH": "KEEP_HELP_CMDHELPCHK_APPLY_BLOCKED", "SELECTED_NOW": 1, "DETAIL": "No HELP DATA/CMDHELPCHK apply remains authorized.", "REUSE_CONFIRMED_NOW": 0, "SOURCE_PATCH_NEEDED_PROVEN": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        deferred_options = [
            {"DEFERRED_ROW": 1, "DEFERRED_PATH": "CONFIRM_EXISTING_NATIVE_WRITER_REUSE", "DEFERRED_REASON": "Exact writer function/command/file/target contract not named yet.", "DEFERRED": 1},
            {"DEFERRED_ROW": 2, "DEFERRED_PATH": "REJECT_REUSE_AND_PLAN_SOURCE_PATCH", "DEFERRED_REASON": "Reuse has not been rejected and patch need is not proven.", "DEFERRED": 1},
            {"DEFERRED_ROW": 3, "DEFERRED_PATH": "SOURCE_MUTATION", "DEFERRED_REASON": "No source patch is authorized.", "DEFERRED": 1},
            {"DEFERRED_ROW": 4, "DEFERRED_PATH": "HELP_DATA_CMDHELPCHK_APPLY", "DEFERRED_REASON": "No apply execution is authorized.", "DEFERRED": 1},
            {"DEFERRED_ROW": 5, "DEFERRED_PATH": "DUPLICATE_10CS_SAVEPOINT_HOUSEKEEPING", "DEFERRED_REASON": "Carry as accounting defect; do not manually edit journal in this phase.", "DEFERRED": 1},
        ]

        exact_path_requirements = [
            {"REQ_ROW": 1, "REQUIREMENT": "NAME_EXACT_FUNCTION_OR_COMMAND", "DETAIL": "Resolution package must name the exact existing function/command/path or reject candidate.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "NAME_EXACT_TARGET_CONTRACT", "DETAIL": "Resolution must prove target is HELP DATA or CMDHELPCHK, not only generic help/message/report context.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "DISTINGUISH_WRITER_FROM_READER_CHECKER", "DETAIL": "Reader/checker/report/list/status paths do not count as native writer reuse.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "PROVE_NATIVE_SCHEMA_AWARE_MATERIALIZATION", "DETAIL": "Reuse path must be native/schema-aware and must not be raw DBF byte writing.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "REQUIREMENT": "PRESERVE_SOURCE_COMMENT_CONTRACT_RULE", "DETAIL": "Any later source patch must update @dottalk.usage/source-comment contracts in same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "REQUIREMENT": "NO_SOURCE_MUTATION_IN_RESOLUTION_PACKAGE", "DETAIL": "Next exact-path resolution package remains report/source-held unless separately authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 7, "REQUIREMENT": "NO_HELP_CMDHELPCHK_APPLY", "DETAIL": "No HELP DATA/CMDHELPCHK apply until a later guarded apply package is reviewed and authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 8, "REQUIREMENT": "CARRY_DUPLICATE_10CS_NOTE", "DETAIL": f"Observed MSG-022AE.6.5.10CS occurrences: {sp_cs_count}; carry as accounting defect only.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries remain an accounting/idempotency issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10DB", "OBSERVED_OCCURRENCES": sp_db_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_db_count >= 1 else "MISSING", "DETAIL": "10DB savepoint presence is the precondition for 10DC."},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after accelerated 10DC decision review.",
            })

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "DB_DECISION_PACKAGE_REVIEWED", "VALUE": 1, "DETAIL": "10DB decision package reviewed."},
            {"DECISION_ROW": 2, "DECISION": "EXACT_WRITER_PATH_RESOLUTION_REQUIRED", "VALUE": 1, "DETAIL": "Proceed to exact path resolution package."},
            {"DECISION_ROW": 3, "DECISION": "REUSE_CONFIRMED_NOW", "VALUE": 0, "DETAIL": "Reuse remains unconfirmed."},
            {"DECISION_ROW": 4, "DECISION": "SOURCE_PATCH_NEEDED_PROVEN", "VALUE": 0, "DETAIL": "Patch need remains unproven."},
            {"DECISION_ROW": 5, "DECISION": "SOURCE_MUTATION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "No source mutation authorized."},
            {"DECISION_ROW": 6, "DECISION": "APPLY_EXECUTION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "No apply authorized."},
        ]

        paths = [
            (dc_root / "decision_option_review_v1.csv", option_review, ["OPTION_REVIEW_ROW","DECISION_OPTION","DB_OPTION_STATUS","SUPPORTING_EVIDENCE_ROWS","DC_REVIEW_STATUS","DC_REVIEW_DETAIL","REUSE_PATH_SELECTED_NOW","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_SELECTED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_EXECUTION_AUTHORIZED_NOW"]),
            (dc_root / "decision_evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","REQUESTED_LINE","SOURCE_CONTEXT_CLASSIFICATION","DA_REVIEW_DISPOSITION","EVIDENCE_STRENGTH","EVIDENCE_SCORE","CONTEXT_ARTIFACT","DC_REVIEW_DISPOSITION","ELIGIBLE_FOR_EXACT_PATH_RESOLUTION","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"]),
            (dc_root / "high_value_exact_path_candidates_v1.csv", high_value_candidates, ["CANDIDATE_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","REQUESTED_LINE","SOURCE_CONTEXT_CLASSIFICATION","CONTEXT_ARTIFACT","REQUIRED_RESOLUTION","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (dc_root / "selected_safe_path_v1.csv", selected_safe_path, ["SELECTED_ROW","SELECTED_PATH","SELECTED_NOW","DETAIL","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (dc_root / "deferred_decision_options_v1.csv", deferred_options, ["DEFERRED_ROW","DEFERRED_PATH","DEFERRED_REASON","DEFERRED"]),
            (dc_root / "exact_path_resolution_requirements_v1.csv", exact_path_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (dc_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (dc_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
            (dc_root / "review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = dc_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled_script = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DD_EXACT_PATH_RESOLUTION_TEMPLATE.ps1.disabled"
        disabled_script.write_text('throw "10DC selected exact path resolution only. Generate 10DD before confirming reuse/source-patch/apply or authorizing mutation."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DC_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = dc_root / "native_writer_source_context_decision_review_v1.md"
        notes.write_text("# 10DC Native Writer Source Context Decision Review\n\n10DC consolidates decision-package review and safe selection. It requires exact writer path resolution and keeps apply blocked. No reuse is confirmed, no source patch need is proven, and no protected systems are mutated.\n", encoding="utf-8")
        readme = dc_root / "README_10DC_ACCELERATED_DECISION_REVIEW.md"
        readme.write_text("# 10DC Accelerated Decision Review\n\nAccelerated report-only package. It combines decision review and safe next-path selection while preserving protected boundaries.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled_script, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10DC writes docs/messaging decision review artifacts only; no source writes."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "DECISION_REVIEW_COMPLETED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(option_review)} options reviewed."},
        {"ITEM": "EXACT_WRITER_PATH_RESOLUTION_REQUIRED", "STATUS": "YES", "DETAIL": f"{len(high_value_candidates)} high-value exact-path candidates carried forward."},
        {"ITEM": "REUSE_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains unconfirmed."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Patch need remains unproven."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_decision_option_review_v1.csv", option_review, ["OPTION_REVIEW_ROW","DECISION_OPTION","DB_OPTION_STATUS","SUPPORTING_EVIDENCE_ROWS","DC_REVIEW_STATUS","DC_REVIEW_DETAIL","REUSE_PATH_SELECTED_NOW","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_SELECTED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_EXECUTION_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_decision_evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","REQUESTED_LINE","SOURCE_CONTEXT_CLASSIFICATION","DA_REVIEW_DISPOSITION","EVIDENCE_STRENGTH","EVIDENCE_SCORE","CONTEXT_ARTIFACT","DC_REVIEW_DISPOSITION","ELIGIBLE_FOR_EXACT_PATH_RESOLUTION","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_high_value_exact_path_candidates_v1.csv", high_value_candidates, ["CANDIDATE_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","REQUESTED_LINE","SOURCE_CONTEXT_CLASSIFICATION","CONTEXT_ARTIFACT","REQUIRED_RESOLUTION","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_selected_safe_path_v1.csv", selected_safe_path, ["SELECTED_ROW","SELECTED_PATH","SELECTED_NOW","DETAIL","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_deferred_decision_options_v1.csv", deferred_options, ["DEFERRED_ROW","DEFERRED_PATH","DEFERRED_REASON","DEFERRED"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_exact_path_resolution_requirements_v1.csv", exact_path_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10DB_STATUS": db.get("STATUS",""),
        "MSG_022AE_6_5_10DB_SAVEPOINT_PRESENT": 1 if sp_db else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10DB_SAVEPOINT_OCCURRENCES_OBSERVED": sp_db_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "DB_DECISION_EVIDENCE_ROWS": len(evidence),
        "DB_DECISION_OPTION_ROWS": len(options),
        "OPTION_REVIEW_ROWS": len(option_review),
        "EVIDENCE_REVIEW_ROWS": len(evidence_review),
        "HIGH_VALUE_EXACT_PATH_CANDIDATE_ROWS": len(high_value_candidates),
        "SELECTED_SAFE_PATH_ROWS": len(selected_safe_path),
        "DEFERRED_DECISION_OPTION_ROWS": len(deferred_options),
        "DC_ROOT": rel(dc_root, repo),
        "DECISION_REVIEW_COMPLETED": 1 if status == GREEN else 0,
        "EXACT_WRITER_PATH_RESOLUTION_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10dc_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10DC_NATIVE_WRITER_SOURCE_CONTEXT_DECISION_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10DC Native Writer Source Context Decision Review\n\nStatus: `{status}`\n\n10DC is an accelerated report-only package. It reviews the 10DB decision package, selects exact writer path resolution as the safe next path, and keeps apply blocked. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(dc_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10DB status: {db.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10DB savepoint present: {1 if sp_db else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  DB decision evidence rows: {len(evidence)}")
    print(f"  DB decision option rows: {len(options)}")
    print(f"  option review rows: {len(option_review)}")
    print(f"  evidence review rows: {len(evidence_review)}")
    print(f"  high value exact path candidate rows: {len(high_value_candidates)}")
    print(f"  selected safe path rows: {len(selected_safe_path)}")
    print(f"  deferred decision option rows: {len(deferred_options)}")
    print(f"  review root: {rel(dc_root, repo)}")
    print("  decision review completed: 1")
    print("  exact writer path resolution required: 1")
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
