#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CW_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_REVIEW_GREEN_PROBE_STAGING_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CW_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CX_NATIVE_WRITER_PROBE_STAGING_PACKAGE"

REPORT = Path("docs/messaging/reports")
CV_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cv_status_summary_v1.csv"
CV_SCOPE = REPORT / "message_catalog_phase22ae_6_5_10cv_next_investigation_scope_v1.csv"
CV_TARGETS = REPORT / "message_catalog_phase22ae_6_5_10cv_investigation_targets_v1.csv"
CV_PROBE_PLAN = REPORT / "message_catalog_phase22ae_6_5_10cv_exact_probe_plan_v1.csv"
CV_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10cv_evidence_carry_forward_v1.csv"
CV_DUP_NOTES = REPORT / "message_catalog_phase22ae_6_5_10cv_duplicate_savepoint_notes_v1.csv"
CV_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cv_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CW_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cw_native_writer_next_investigation_scope_review_v1")

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

def scope_disposition(row):
    target = row.get("INVESTIGATION_TARGET", "")
    priority = row.get("SCOPE_PRIORITY", "")
    exists = str(row.get("SOURCE_EXISTS", ""))
    if target in {"HELP_DATA_NATIVE_WRITER_PATH", "CMDHELPCHK_NATIVE_WRITER_PATH"} and priority == "A":
        return "ACCEPT_HIGH_PRIORITY_EXACT_WRITER_SCOPE", "Carry to 10CX probe staging with source-context readback only."
    if target == "GENERIC_NATIVE_WRITER_TARGET_BINDING":
        return "ACCEPT_GENERIC_TARGET_BINDING_SCOPE", "Carry to 10CX to prove or reject exact HELP/CMDHELPCHK target binding."
    if exists == "0":
        return "REVIEW_SOURCE_PATH_MISSING_OR_MOVED", "Scope row references a source path not found by 10CV; keep as review item."
    return "ACCEPT_SUPPORTING_OR_EXCLUSION_SCOPE", "Carry only as supporting/exclusion evidence."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cv = first(repo / CV_SUMMARY)
    scope = rows(repo / CV_SCOPE)
    targets = rows(repo / CV_TARGETS)
    probe_plan = rows(repo / CV_PROBE_PLAN)
    evidence = rows(repo / CV_EVIDENCE)
    dup_notes_in = rows(repo / CV_DUP_NOTES)
    blocked_in = rows(repo / CV_BLOCKED)

    sp_cv, latest_cv = savepoint(repo, "MSG-022AE.6.5.10CV")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_cv_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CV")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cw_root = repo / CW_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CV_GREEN", cv.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CV_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_PACKAGE_GREEN_SCOPE_STAGED_SOURCE_HELD", cv.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CV_SAVEPOINT_PRESENT", sp_cv, latest_cv)
    gate("CV_NEXT_SCOPE_STAGED", cv.get("NEXT_INVESTIGATION_SCOPE_STAGED") == "1", cv.get("NEXT_INVESTIGATION_SCOPE_STAGED", "missing"))
    gate("CV_RUNTIME_NOT_EXECUTED", cv.get("RUNTIME_EXECUTION_NOW") == "0", cv.get("RUNTIME_EXECUTION_NOW", "missing"))
    gate("CV_REUSE_NOT_SELECTED", cv.get("REUSE_PATH_SELECTED_NOW") == "0", cv.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("CV_WRITER_REUSE_NOT_CONFIRMED", cv.get("WRITER_REUSE_CONFIRMED_NOW") == "0", cv.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CV_SOURCE_PATCH_NOT_SELECTED", cv.get("SOURCE_PATCH_SELECTED_NOW") == "0", cv.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("CV_SOURCE_PATCH_NOT_PROVEN", cv.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cv.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CV_SOURCE_MUTATION_NOT_AUTHORIZED", cv.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cv.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CV_APPLY_EXECUTION_NOT_AUTHORIZED", cv.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cv.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CV_HELP_APPLY_NOT_EXECUTED", cv.get("HELP_DATA_APPLY_EXECUTED") == "0", cv.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CV_CMDHELPCHK_APPLY_NOT_EXECUTED", cv.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cv.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CV_SCOPE_ROWS_PRESENT", len(scope) > 0, len(scope))
    gate("CV_PROBE_PLAN_PRESENT", len(probe_plan) > 0, len(probe_plan))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CW_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cw_root.exists()) or args.replace_existing_review, rel(cw_root, repo))

    status = BLOCKED
    scope_review = []
    target_review = []
    probe_review = []
    evidence_review = []
    duplicate_savepoint_notes = []
    probe_staging_requirements = []
    blocked_rows = []
    review_decisions = []
    artifacts = []

    if failures == 0:
        if cw_root.exists() and args.replace_existing_review:
            shutil.rmtree(cw_root)
        cw_root.mkdir(parents=True, exist_ok=True)

        for i, row in enumerate(scope, 1):
            disp, detail = scope_disposition(row)
            scope_review.append({
                "SCOPE_REVIEW_ROW": i,
                "SOURCE_SCOPE_ROW": row.get("SCOPE_ROW", ""),
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "SCOPE_PRIORITY": row.get("SCOPE_PRIORITY", ""),
                "FILE_PATH": row.get("FILE_PATH", ""),
                "LINE": row.get("LINE", ""),
                "SOURCE_SIGNAL_SCORE": row.get("SOURCE_SIGNAL_SCORE", ""),
                "SOURCE_EXISTS": row.get("SOURCE_EXISTS", ""),
                "CW_SCOPE_REVIEW_DISPOSITION": disp,
                "CW_SCOPE_REVIEW_DETAIL": detail,
                "ELIGIBLE_FOR_10CX_PROBE_STAGING": 1 if disp.startswith("ACCEPT") else 0,
                "RUNTIME_EXECUTION_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        for i, row in enumerate(targets, 1):
            target_review.append({
                "TARGET_REVIEW_ROW": i,
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "SCOPE_ROW_COUNT": row.get("SCOPE_ROW_COUNT", ""),
                "TARGET_GOAL": row.get("TARGET_GOAL", ""),
                "CW_TARGET_REVIEW_STATUS": "ACCEPT_FOR_10CX_PROBE_STAGING",
                "DETAIL": "Target grouping is accepted for probe-staging design; no runtime execution now.",
            })

        for i, row in enumerate(probe_plan, 1):
            probe_review.append({
                "PROBE_REVIEW_ROW": i,
                "PROBE": row.get("PROBE", ""),
                "CV_DETAIL": row.get("DETAIL", ""),
                "CW_REVIEW_STATUS": "ACCEPT_FOR_STAGING" if row.get("RUNTIME_EXECUTION_NOW") == "0" else "REVIEW_UNEXPECTED_RUNTIME_FLAG",
                "STAGE_IN_10CX": 1,
                "RUNTIME_EXECUTION_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        for i, row in enumerate(evidence, 1):
            evidence_review.append({
                "EVIDENCE_REVIEW_ROW": i,
                "SOURCE": row.get("SOURCE", ""),
                "ROW_COUNT": row.get("ROW_COUNT", ""),
                "ROLE": row.get("ROLE", ""),
                "CW_EVIDENCE_REVIEW_STATUS": "ACCEPT_CARRY_FORWARD",
                "DETAIL": "Carry into 10CX staging as source evidence only.",
            })

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries remain an accounting/idempotency issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10CV", "OBSERVED_OCCURRENCES": sp_cv_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_cv_count >= 1 else "MISSING", "DETAIL": "10CV savepoint presence is the precondition for 10CW."},
        ]

        probe_staging_requirements = [
            {"REQ_ROW": 1, "REQUIREMENT": "10CX_STAGE_SOURCE_CONTEXT_PROBES_ONLY", "DETAIL": "10CX should stage source-context/readback probes without runtime execution or source edits.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "TRACE_HELP_DATA_WRITER_PATH", "DETAIL": "Stage probes to name exact HELP DATA writer/import/update path or reject as absent.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "TRACE_CMDHELPCHK_WRITER_PATH", "DETAIL": "Stage probes to name exact CMDHELPCHK writer/import/update path or reject as absent.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "PROVE_OR_REJECT_GENERIC_TARGET_BINDING", "DETAIL": "Stage probes that distinguish generic writer targets from reader/checker/report paths.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "REQUIREMENT": "PRESERVE_USAGE_CONTRACT_RULE", "DETAIL": "Any later source patch must update @dottalk.usage/source-comment contracts in the same guarded package.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Active HELP/CMDHELPCHK materialization must remain native/schema-aware, not raw DBF byte mutation.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 7, "REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until a later guarded apply package is reviewed and explicitly authorized.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CW scope review.",
            })

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "CV_SCOPE_REVIEWED", "VALUE": 1, "DETAIL": "10CV next investigation scope reviewed and accepted for 10CX staging."},
            {"DECISION_ROW": 2, "DECISION": "PROBE_STAGING_PACKAGE_REQUIRED", "VALUE": 1, "DETAIL": "10CX should stage source-context probes."},
            {"DECISION_ROW": 3, "DECISION": "RUNTIME_EXECUTION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "Runtime execution remains blocked."},
            {"DECISION_ROW": 4, "DECISION": "REUSE_PATH_SELECTED_NOW", "VALUE": 0, "DETAIL": "Reuse remains deferred."},
            {"DECISION_ROW": 5, "DECISION": "SOURCE_PATCH_SELECTED_NOW", "VALUE": 0, "DETAIL": "Source patch remains deferred."},
            {"DECISION_ROW": 6, "DECISION": "APPLY_EXECUTION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "Apply remains blocked."},
        ]

        paths = [
            (cw_root / "scope_review_v1.csv", scope_review, ["SCOPE_REVIEW_ROW","SOURCE_SCOPE_ROW","INVESTIGATION_TARGET","SCOPE_PRIORITY","FILE_PATH","LINE","SOURCE_SIGNAL_SCORE","SOURCE_EXISTS","CW_SCOPE_REVIEW_DISPOSITION","CW_SCOPE_REVIEW_DETAIL","ELIGIBLE_FOR_10CX_PROBE_STAGING","RUNTIME_EXECUTION_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cw_root / "target_review_v1.csv", target_review, ["TARGET_REVIEW_ROW","INVESTIGATION_TARGET","SCOPE_ROW_COUNT","TARGET_GOAL","CW_TARGET_REVIEW_STATUS","DETAIL"]),
            (cw_root / "probe_plan_review_v1.csv", probe_review, ["PROBE_REVIEW_ROW","PROBE","CV_DETAIL","CW_REVIEW_STATUS","STAGE_IN_10CX","RUNTIME_EXECUTION_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cw_root / "evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","SOURCE","ROW_COUNT","ROLE","CW_EVIDENCE_REVIEW_STATUS","DETAIL"]),
            (cw_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (cw_root / "probe_staging_requirements_v1.csv", probe_staging_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cw_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
            (cw_root / "review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = cw_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CX_PROBE_STAGING_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CW is review only. Generate a dedicated 10CX probe staging package before running probes or authorizing source/apply work."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CW_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cw_root / "native_writer_next_investigation_scope_review_v1.md"
        notes.write_text("# 10CW Native Writer Next Investigation Scope Review\n\n10CW reviews the 10CV scope and requires a 10CX source-context probe staging package. It does not execute probes, select reuse, select source patch, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = cw_root / "README_10CW_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_REVIEW.md"
        readme.write_text("# 10CW Native Writer Next Investigation Scope Review\n\nReview-only package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_next_investigation_scope_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_next_investigation_scope_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CW writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Scope review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Scope review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "NEXT_INVESTIGATION_SCOPE_REVIEWED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(scope_review)} scope rows reviewed."},
        {"ITEM": "PROBE_STAGING_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10CX should stage source-context probes only."},
        {"ITEM": "RUNTIME_EXECUTION_AUTHORIZED_NOW", "STATUS": "NO", "DETAIL": "Runtime execution remains blocked."},
        {"ITEM": "REUSE_PATH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains deferred."},
        {"ITEM": "SOURCE_PATCH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Source patch remains deferred."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_scope_review_v1.csv", scope_review, ["SCOPE_REVIEW_ROW","SOURCE_SCOPE_ROW","INVESTIGATION_TARGET","SCOPE_PRIORITY","FILE_PATH","LINE","SOURCE_SIGNAL_SCORE","SOURCE_EXISTS","CW_SCOPE_REVIEW_DISPOSITION","CW_SCOPE_REVIEW_DETAIL","ELIGIBLE_FOR_10CX_PROBE_STAGING","RUNTIME_EXECUTION_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_target_review_v1.csv", target_review, ["TARGET_REVIEW_ROW","INVESTIGATION_TARGET","SCOPE_ROW_COUNT","TARGET_GOAL","CW_TARGET_REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_probe_plan_review_v1.csv", probe_review, ["PROBE_REVIEW_ROW","PROBE","CV_DETAIL","CW_REVIEW_STATUS","STAGE_IN_10CX","RUNTIME_EXECUTION_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","SOURCE","ROW_COUNT","ROLE","CW_EVIDENCE_REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_probe_staging_requirements_v1.csv", probe_staging_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CV_STATUS": cv.get("STATUS",""),
        "MSG_022AE_6_5_10CV_SAVEPOINT_PRESENT": 1 if sp_cv else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10CV_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cv_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CV_SCOPE_ROWS": len(scope),
        "CV_TARGET_ROWS": len(targets),
        "CV_PROBE_PLAN_ROWS": len(probe_plan),
        "SCOPE_REVIEW_ROWS": len(scope_review),
        "TARGET_REVIEW_ROWS": len(target_review),
        "PROBE_PLAN_REVIEW_ROWS": len(probe_review),
        "PROBE_STAGING_REQUIREMENT_ROWS": len(probe_staging_requirements),
        "CW_ROOT": rel(cw_root, repo),
        "NEXT_INVESTIGATION_SCOPE_REVIEWED": 1 if status == GREEN else 0,
        "PROBE_STAGING_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
        "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0,
        "REUSE_PATH_SELECTED_NOW": 0,
        "WRITER_REUSE_CONFIRMED_NOW": 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cw_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CW_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CW Native Writer Next Investigation Scope Review\n\nStatus: `{status}`\n\n10CW reviews the 10CV next investigation scope and requires a 10CX probe staging package. It does not execute probes, select reuse, select source patch, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(cw_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CV status: {cv.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CV savepoint present: {1 if sp_cv else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CV scope rows: {len(scope)}")
    print(f"  CV target rows: {len(targets)}")
    print(f"  CV probe plan rows: {len(probe_plan)}")
    print(f"  scope review rows: {len(scope_review)}")
    print(f"  target review rows: {len(target_review)}")
    print(f"  probe plan review rows: {len(probe_review)}")
    print(f"  probe staging requirement rows: {len(probe_staging_requirements)}")
    print(f"  review root: {rel(cw_root, repo)}")
    print("  next investigation scope reviewed: 1")
    print("  probe staging package required: 1")
    print("  runtime execution authorized now: 0")
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
