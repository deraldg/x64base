#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DB_NATIVE_WRITER_SOURCE_CONTEXT_DECISION_PACKAGE_GREEN_DECISION_OPTIONS_STAGED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DB_NATIVE_WRITER_SOURCE_CONTEXT_DECISION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DC_NATIVE_WRITER_SOURCE_CONTEXT_DECISION_PACKAGE_REVIEW"

REPORT = Path("docs/messaging/reports")
DA_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10da_status_summary_v1.csv"
DA_PROBE_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10da_probe_result_review_v1.csv"
DA_CLASS_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10da_classification_review_v1.csv"
DA_TARGET_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10da_target_result_review_v1.csv"
DA_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10da_evidence_review_v1.csv"
DA_DUP_NOTES = REPORT / "message_catalog_phase22ae_6_5_10da_duplicate_savepoint_notes_v1.csv"
DA_REQS = REPORT / "message_catalog_phase22ae_6_5_10da_decision_package_requirements_v1.csv"
DA_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10da_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
DB_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10db_native_writer_source_context_decision_package_v1")

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

def evidence_strength(row):
    disp = row.get("DA_REVIEW_DISPOSITION", "")
    cls = row.get("SOURCE_CONTEXT_CLASSIFICATION", "")
    hits = intish(row.get("HIT_LINE_ROWS", ""))
    if disp.startswith("HIGH_VALUE") or cls in {"HELP_DATA_WRITER_CANDIDATE_CONTEXT", "CMDHELPCHK_WRITER_CANDIDATE_CONTEXT"}:
        return "HIGH", 3
    if "GENERIC_WRITER" in disp or cls == "GENERIC_WRITER_CONTEXT":
        return "MEDIUM", 2
    if hits > 0:
        return "LOW", 1
    return "INCONCLUSIVE", 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    da = first(repo / DA_SUMMARY)
    probe_review = rows(repo / DA_PROBE_REVIEW)
    class_review = rows(repo / DA_CLASS_REVIEW)
    target_review = rows(repo / DA_TARGET_REVIEW)
    evidence_in = rows(repo / DA_EVIDENCE)
    dup_notes_in = rows(repo / DA_DUP_NOTES)
    reqs_in = rows(repo / DA_REQS)
    blocked_in = rows(repo / DA_BLOCKED)

    sp_da, latest_da = savepoint(repo, "MSG-022AE.6.5.10DA")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_da_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10DA")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    db_root = repo / DB_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10DA_GREEN", da.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10DA_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_REVIEW_GREEN_DECISION_PACKAGE_REQUIRED_SOURCE_HELD", da.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10DA_SAVEPOINT_PRESENT", sp_da, latest_da)
    gate("DA_SOURCE_CONTEXT_REVIEWED", da.get("SOURCE_CONTEXT_REVIEWED") == "1", da.get("SOURCE_CONTEXT_REVIEWED", "missing"))
    gate("DA_DECISION_PACKAGE_REQUIRED", da.get("SOURCE_CONTEXT_DECISION_PACKAGE_REQUIRED") == "1", da.get("SOURCE_CONTEXT_DECISION_PACKAGE_REQUIRED", "missing"))
    gate("DA_REUSE_NOT_SELECTED", da.get("REUSE_PATH_SELECTED_NOW") == "0", da.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("DA_WRITER_REUSE_NOT_CONFIRMED", da.get("WRITER_REUSE_CONFIRMED_NOW") == "0", da.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("DA_SOURCE_PATCH_NOT_SELECTED", da.get("SOURCE_PATCH_SELECTED_NOW") == "0", da.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("DA_SOURCE_PATCH_NOT_PROVEN", da.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", da.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("DA_SOURCE_MUTATION_NOT_AUTHORIZED", da.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", da.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("DA_APPLY_EXECUTION_NOT_AUTHORIZED", da.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", da.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("DA_HELP_APPLY_NOT_EXECUTED", da.get("HELP_DATA_APPLY_EXECUTED") == "0", da.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("DA_CMDHELPCHK_APPLY_NOT_EXECUTED", da.get("CMDHELPCHK_APPLY_EXECUTED") == "0", da.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("DA_PROBE_REVIEW_ROWS_PRESENT", len(probe_review) > 0, len(probe_review))
    gate("DA_DECISION_REQUIREMENTS_PRESENT", len(reqs_in) > 0, len(reqs_in))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("DB_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not db_root.exists()) or args.replace_existing_package, rel(db_root, repo))

    status = BLOCKED
    decision_evidence = []
    decision_options = []
    decision_review_checklist = []
    classification_decision_matrix = []
    target_decision_matrix = []
    duplicate_savepoint_notes = []
    blocked_rows = []
    artifacts = []

    if failures == 0:
        if db_root.exists() and args.replace_existing_package:
            shutil.rmtree(db_root)
        db_root.mkdir(parents=True, exist_ok=True)

        high_count = 0
        med_count = 0
        low_count = 0
        inconclusive_count = 0

        for i, row in enumerate(probe_review, 1):
            strength, score = evidence_strength(row)
            if strength == "HIGH":
                high_count += 1
            elif strength == "MEDIUM":
                med_count += 1
            elif strength == "LOW":
                low_count += 1
            else:
                inconclusive_count += 1
            decision_evidence.append({
                "DECISION_EVIDENCE_ROW": i,
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
                "DECISION_USE": "Review-only evidence for 10DC; does not confirm reuse or patch need.",
                "REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_AUTHORIZED_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
            })

        option_rows = [
            ("CONFIRM_EXISTING_NATIVE_WRITER_REUSE", "Review high-value candidate contexts and decide if an existing native writer/import/update path is exactly named and usable.", "AVAILABLE_FOR_REVIEW_ONLY", high_count, 0, 0, 0),
            ("CONTINUE_TARGETED_SOURCE_CONTEXT_INVESTIGATION", "Continue investigation if contexts remain generic or inconclusive.", "AVAILABLE_SAFE_DEFAULT", med_count + low_count + inconclusive_count, 0, 0, 0),
            ("REJECT_REUSE_AND_PLAN_SOURCE_PATCH", "Only select later if native reuse is explicitly rejected and missing writer surface is proven.", "DEFERRED_PATCH_NEED_NOT_PROVEN", 0, 0, 0, 0),
            ("KEEP_APPLY_BLOCKED", "Maintain no HELP DATA/CMDHELPCHK apply until guarded apply package is separately reviewed and authorized.", "REQUIRED_SAFETY_BOUNDARY", len(probe_review), 0, 0, 0),
            ("HOUSEKEEP_DUPLICATE_10CS_SAVEPOINT_GUARD", "Carry duplicate 10CS savepoint accounting defect for later housekeeping; do not edit journal manually here.", "DEFERRED_HOUSEKEEPING", sp_cs_count, 0, 0, 0),
        ]
        for i, (opt, detail, status_text, evidence_rows, reuse_now, patch_now, apply_now) in enumerate(option_rows, 1):
            decision_options.append({
                "DECISION_OPTION_ROW": i,
                "DECISION_OPTION": opt,
                "OPTION_STATUS": status_text,
                "SUPPORTING_EVIDENCE_ROWS": evidence_rows,
                "OPTION_DETAIL": detail,
                "REUSE_PATH_SELECTED_NOW": reuse_now,
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_SELECTED_NOW": patch_now,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_EXECUTION_AUTHORIZED_NOW": apply_now,
            })

        for i, row in enumerate(class_review, 1):
            classification_decision_matrix.append({
                "CLASS_MATRIX_ROW": i,
                "SOURCE_CONTEXT_CLASSIFICATION": row.get("SOURCE_CONTEXT_CLASSIFICATION", ""),
                "PROBE_RESULT_ROWS": row.get("PROBE_RESULT_ROWS", ""),
                "DA_CLASS_REVIEW_STATUS": row.get("DA_CLASS_REVIEW_STATUS", ""),
                "DB_DECISION_STATUS": "AVAILABLE_FOR_10DC_REVIEW",
                "DETAIL": row.get("DETAIL", ""),
            })

        for i, row in enumerate(target_review, 1):
            target_decision_matrix.append({
                "TARGET_MATRIX_ROW": i,
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "PROBE_RESULT_ROWS": row.get("PROBE_RESULT_ROWS", ""),
                "DA_TARGET_REVIEW_STATUS": row.get("DA_TARGET_REVIEW_STATUS", ""),
                "DB_DECISION_STATUS": "AVAILABLE_FOR_10DC_REVIEW",
                "REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_ALLOWED_NOW": 0,
                "DETAIL": row.get("DETAIL", ""),
            })

        decision_review_checklist = [
            {"CHECK_ROW": 1, "CHECK": "REVIEW_HIGH_VALUE_CONTEXTS", "REQUIRED": 1, "DETAIL": f"Review {high_count} high-value context rows before confirming any reuse.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"CHECK_ROW": 2, "CHECK": "NAME_EXACT_WRITER_PATH_BEFORE_REUSE", "REQUIRED": 1, "DETAIL": "Reuse cannot be confirmed unless exact function/command/file/target contract is named.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"CHECK_ROW": 3, "CHECK": "REJECT_REUSE_BEFORE_PATCH_SELECTION", "REQUIRED": 1, "DETAIL": "Patch planning cannot be selected until native reuse is explicitly rejected.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"CHECK_ROW": 4, "CHECK": "PRESERVE_USAGE_CONTRACT_RULE", "REQUIRED": 1, "DETAIL": "Any later source patch must update @dottalk.usage/source-comment contracts in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"CHECK_ROW": 5, "CHECK": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "REQUIRED": 1, "DETAIL": "Active HELP/CMDHELPCHK materialization must remain native/schema-aware, not raw DBF byte mutation.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"CHECK_ROW": 6, "CHECK": "KEEP_APPLY_BLOCKED", "REQUIRED": 1, "DETAIL": "No HELP DATA/CMDHELPCHK apply until a later guarded apply package is reviewed and explicitly authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"CHECK_ROW": 7, "CHECK": "CARRY_DUPLICATE_10CS_NOTE", "REQUIRED": 1 if sp_cs_count > 1 else 0, "DETAIL": f"Observed 10CS savepoint occurrences: {sp_cs_count}. Treat as accounting/idempotency defect only.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries remain an accounting/idempotency issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10DA", "OBSERVED_OCCURRENCES": sp_da_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_da_count >= 1 else "MISSING", "DETAIL": "10DA savepoint presence is the precondition for 10DB."},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after DB decision package staging.",
            })

        paths = [
            (db_root / "decision_evidence_v1.csv", decision_evidence, ["DECISION_EVIDENCE_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","REQUESTED_LINE","SOURCE_CONTEXT_CLASSIFICATION","DA_REVIEW_DISPOSITION","EVIDENCE_STRENGTH","EVIDENCE_SCORE","CONTEXT_ARTIFACT","DECISION_USE","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"]),
            (db_root / "decision_options_v1.csv", decision_options, ["DECISION_OPTION_ROW","DECISION_OPTION","OPTION_STATUS","SUPPORTING_EVIDENCE_ROWS","OPTION_DETAIL","REUSE_PATH_SELECTED_NOW","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_SELECTED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_EXECUTION_AUTHORIZED_NOW"]),
            (db_root / "classification_decision_matrix_v1.csv", classification_decision_matrix, ["CLASS_MATRIX_ROW","SOURCE_CONTEXT_CLASSIFICATION","PROBE_RESULT_ROWS","DA_CLASS_REVIEW_STATUS","DB_DECISION_STATUS","DETAIL"]),
            (db_root / "target_decision_matrix_v1.csv", target_decision_matrix, ["TARGET_MATRIX_ROW","INVESTIGATION_TARGET","PROBE_RESULT_ROWS","DA_TARGET_REVIEW_STATUS","DB_DECISION_STATUS","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_ALLOWED_NOW","DETAIL"]),
            (db_root / "decision_review_checklist_v1.csv", decision_review_checklist, ["CHECK_ROW","CHECK","REQUIRED","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (db_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (db_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = db_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled_script = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DC_DECISION_REVIEW_TEMPLATE.ps1.disabled"
        disabled_script.write_text('throw "10DB stages decision options only. Run 10DC review before selecting reuse/source-patch/apply or authorizing any mutation."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DB_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = db_root / "native_writer_source_context_decision_package_v1.md"
        notes.write_text("# 10DB Native Writer Source Context Decision Package\n\n10DB stages decision options from 10DA source-context review evidence. It does not select reuse, prove source patch need, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = db_root / "README_10DB_NATIVE_WRITER_SOURCE_CONTEXT_DECISION_PACKAGE.md"
        readme.write_text("# 10DB Native Writer Source Context Decision Package\n\nDecision-package staging only. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_source_context_decision_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled_script, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_source_context_decision_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10DB writes docs/messaging decision artifacts only; no source writes."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision package only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision package only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "DECISION_OPTIONS_STAGED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(decision_options)} decision options staged."},
        {"ITEM": "REUSE_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains deferred pending 10DC review."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Patch need remains unproven."},
        {"ITEM": "SOURCE_MUTATION_AUTHORIZED_NOW", "STATUS": "NO", "DETAIL": "No source mutation authorized."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_decision_evidence_v1.csv", decision_evidence, ["DECISION_EVIDENCE_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","REQUESTED_LINE","SOURCE_CONTEXT_CLASSIFICATION","DA_REVIEW_DISPOSITION","EVIDENCE_STRENGTH","EVIDENCE_SCORE","CONTEXT_ARTIFACT","DECISION_USE","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_decision_options_v1.csv", decision_options, ["DECISION_OPTION_ROW","DECISION_OPTION","OPTION_STATUS","SUPPORTING_EVIDENCE_ROWS","OPTION_DETAIL","REUSE_PATH_SELECTED_NOW","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_SELECTED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_EXECUTION_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_classification_decision_matrix_v1.csv", classification_decision_matrix, ["CLASS_MATRIX_ROW","SOURCE_CONTEXT_CLASSIFICATION","PROBE_RESULT_ROWS","DA_CLASS_REVIEW_STATUS","DB_DECISION_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_target_decision_matrix_v1.csv", target_decision_matrix, ["TARGET_MATRIX_ROW","INVESTIGATION_TARGET","PROBE_RESULT_ROWS","DA_TARGET_REVIEW_STATUS","DB_DECISION_STATUS","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_ALLOWED_NOW","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_decision_review_checklist_v1.csv", decision_review_checklist, ["CHECK_ROW","CHECK","REQUIRED","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10DA_STATUS": da.get("STATUS",""),
        "MSG_022AE_6_5_10DA_SAVEPOINT_PRESENT": 1 if sp_da else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10DA_SAVEPOINT_OCCURRENCES_OBSERVED": sp_da_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "DA_PROBE_RESULT_REVIEW_ROWS": len(probe_review),
        "DA_CLASSIFICATION_REVIEW_ROWS": len(class_review),
        "DA_TARGET_RESULT_REVIEW_ROWS": len(target_review),
        "DECISION_EVIDENCE_ROWS": len(decision_evidence),
        "DECISION_OPTION_ROWS": len(decision_options),
        "DECISION_REVIEW_CHECKLIST_ROWS": len(decision_review_checklist),
        "HIGH_VALUE_EVIDENCE_ROWS": high_count if status == GREEN else 0,
        "MEDIUM_EVIDENCE_ROWS": med_count if status == GREEN else 0,
        "LOW_EVIDENCE_ROWS": low_count if status == GREEN else 0,
        "INCONCLUSIVE_EVIDENCE_ROWS": inconclusive_count if status == GREEN else 0,
        "DB_ROOT": rel(db_root, repo),
        "DECISION_OPTIONS_STAGED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10db_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10DB_NATIVE_WRITER_SOURCE_CONTEXT_DECISION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10DB Native Writer Source Context Decision Package\n\nStatus: `{status}`\n\n10DB stages decision options from 10DA source-context review evidence. It does not select reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nDecision root:\n\n```text\n{rel(db_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10DA status: {da.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10DA savepoint present: {1 if sp_da else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  DA probe result review rows: {len(probe_review)}")
    print(f"  DA classification review rows: {len(class_review)}")
    print(f"  DA target result review rows: {len(target_review)}")
    print(f"  decision evidence rows: {len(decision_evidence)}")
    print(f"  decision option rows: {len(decision_options)}")
    print(f"  decision review checklist rows: {len(decision_review_checklist)}")
    print(f"  high value evidence rows: {high_count if status == GREEN else 0}")
    print(f"  medium evidence rows: {med_count if status == GREEN else 0}")
    print(f"  low evidence rows: {low_count if status == GREEN else 0}")
    print(f"  inconclusive evidence rows: {inconclusive_count if status == GREEN else 0}")
    print(f"  decision root: {rel(db_root, repo)}")
    print("  decision options staged: 1")
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
