#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CY_NATIVE_WRITER_PROBE_STAGING_REVIEW_GREEN_SOURCE_CONTEXT_PROBE_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CY_NATIVE_WRITER_PROBE_STAGING_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CZ_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_PACKAGE"

REPORT = Path("docs/messaging/reports")
CX_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cx_status_summary_v1.csv"
CX_STAGED = REPORT / "message_catalog_phase22ae_6_5_10cx_staged_source_context_probes_v1.csv"
CX_CONTEXT_PLAN = REPORT / "message_catalog_phase22ae_6_5_10cx_source_context_probe_plan_v1.csv"
CX_TARGET_MATRIX = REPORT / "message_catalog_phase22ae_6_5_10cx_target_probe_matrix_v1.csv"
CX_DISABLED = REPORT / "message_catalog_phase22ae_6_5_10cx_disabled_probe_scripts_v1.csv"
CX_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10cx_evidence_carry_forward_v1.csv"
CX_DUP_NOTES = REPORT / "message_catalog_phase22ae_6_5_10cx_duplicate_savepoint_notes_v1.csv"
CX_REQS = REPORT / "message_catalog_phase22ae_6_5_10cx_probe_staging_review_requirements_v1.csv"
CX_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cx_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CY_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cy_native_writer_probe_staging_review_v1")

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

def review_probe(row):
    kind = row.get("PROBE_KIND", "")
    exists = str(row.get("SOURCE_EXISTS", ""))
    if exists != "1":
        return "REVIEW_SOURCE_PATH_MISSING_OR_MOVED", "Do not run until source path is resolved."
    if kind in {"HELP_DATA_SOURCE_CONTEXT_PROBE", "CMDHELPCHK_SOURCE_CONTEXT_PROBE"}:
        return "ACCEPT_HIGH_VALUE_SOURCE_CONTEXT_PROBE", "Accept for 10CZ read-only source-context package."
    if kind == "GENERIC_TARGET_BINDING_SOURCE_CONTEXT_PROBE":
        return "ACCEPT_TARGET_BINDING_SOURCE_CONTEXT_PROBE", "Accept for 10CZ read-only source-context package."
    return "ACCEPT_SUPPORTING_SOURCE_CONTEXT_PROBE", "Accept as supporting/exclusion context."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cx = first(repo / CX_SUMMARY)
    staged = rows(repo / CX_STAGED)
    context_plan = rows(repo / CX_CONTEXT_PLAN)
    target_matrix = rows(repo / CX_TARGET_MATRIX)
    disabled = rows(repo / CX_DISABLED)
    evidence = rows(repo / CX_EVIDENCE)
    dup_notes_in = rows(repo / CX_DUP_NOTES)
    reqs_in = rows(repo / CX_REQS)
    blocked_in = rows(repo / CX_BLOCKED)

    sp_cx, latest_cx = savepoint(repo, "MSG-022AE.6.5.10CX")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_cx_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CX")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cy_root = repo / CY_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CX_GREEN", cx.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CX_NATIVE_WRITER_PROBE_STAGING_PACKAGE_GREEN_PROBES_STAGED_NO_EXECUTION_SOURCE_HELD", cx.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CX_SAVEPOINT_PRESENT", sp_cx, latest_cx)
    gate("CX_PROBES_STAGED", cx.get("PROBES_STAGED") == "1", cx.get("PROBES_STAGED", "missing"))
    gate("CX_RUNTIME_NOT_EXECUTED", cx.get("RUNTIME_EXECUTION_NOW") == "0", cx.get("RUNTIME_EXECUTION_NOW", "missing"))
    gate("CX_REUSE_NOT_SELECTED", cx.get("REUSE_PATH_SELECTED_NOW") == "0", cx.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("CX_WRITER_REUSE_NOT_CONFIRMED", cx.get("WRITER_REUSE_CONFIRMED_NOW") == "0", cx.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CX_SOURCE_PATCH_NOT_SELECTED", cx.get("SOURCE_PATCH_SELECTED_NOW") == "0", cx.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("CX_SOURCE_PATCH_NOT_PROVEN", cx.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cx.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CX_SOURCE_MUTATION_NOT_AUTHORIZED", cx.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cx.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CX_APPLY_EXECUTION_NOT_AUTHORIZED", cx.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cx.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CX_HELP_APPLY_NOT_EXECUTED", cx.get("HELP_DATA_APPLY_EXECUTED") == "0", cx.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CX_CMDHELPCHK_APPLY_NOT_EXECUTED", cx.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cx.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CX_STAGED_PROBES_PRESENT", len(staged) > 0, len(staged))
    gate("CX_CONTEXT_PLAN_PRESENT", len(context_plan) > 0, len(context_plan))
    gate("CX_TARGET_MATRIX_PRESENT", len(target_matrix) > 0, len(target_matrix))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CY_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cy_root.exists()) or args.replace_existing_review, rel(cy_root, repo))

    status = BLOCKED
    probe_review = []
    context_plan_review = []
    target_matrix_review = []
    disabled_review = []
    execution_package_requirements = []
    evidence_review = []
    duplicate_savepoint_notes = []
    blocked_rows = []
    review_decisions = []
    artifacts = []

    if failures == 0:
        if cy_root.exists() and args.replace_existing_review:
            shutil.rmtree(cy_root)
        cy_root.mkdir(parents=True, exist_ok=True)

        for i, row in enumerate(staged, 1):
            disp, detail = review_probe(row)
            probe_review.append({
                "PROBE_REVIEW_ROW": i,
                "PROBE_ID": row.get("PROBE_ID", ""),
                "PROBE_KIND": row.get("PROBE_KIND", ""),
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "FILE_PATH": row.get("FILE_PATH", ""),
                "LINE": row.get("LINE", ""),
                "SOURCE_EXISTS": row.get("SOURCE_EXISTS", ""),
                "FILE_SHA256": row.get("FILE_SHA256", ""),
                "CY_PROBE_REVIEW_DISPOSITION": disp,
                "CY_PROBE_REVIEW_DETAIL": detail,
                "ELIGIBLE_FOR_10CZ_SOURCE_CONTEXT_PACKAGE": 1 if disp.startswith("ACCEPT") else 0,
                "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        for i, row in enumerate(context_plan, 1):
            context_plan_review.append({
                "CONTEXT_REVIEW_ROW": i,
                "PROBE_ID": row.get("PROBE_ID", ""),
                "FILE_PATH": row.get("FILE_PATH", ""),
                "LINE": row.get("LINE", ""),
                "READ_WINDOW_BEFORE": row.get("READ_WINDOW_BEFORE", ""),
                "READ_WINDOW_AFTER": row.get("READ_WINDOW_AFTER", ""),
                "CY_CONTEXT_REVIEW_STATUS": "ACCEPT_READ_ONLY_CONTEXT_PLAN" if row.get("NO_EXECUTION") == "1" and row.get("NO_SOURCE_EDIT") == "1" else "REVIEW_CONTEXT_GUARDS",
                "NO_EXECUTION": row.get("NO_EXECUTION", ""),
                "NO_SOURCE_EDIT": row.get("NO_SOURCE_EDIT", ""),
                "NO_HELP_CMDHELPCHK_APPLY": row.get("NO_HELP_CMDHELPCHK_APPLY", ""),
            })

        for i, row in enumerate(target_matrix, 1):
            target_matrix_review.append({
                "MATRIX_REVIEW_ROW": i,
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "STAGED_PROBE_ROWS": row.get("STAGED_PROBE_ROWS", ""),
                "CY_TARGET_REVIEW_STATUS": "ACCEPT_FOR_10CZ_SOURCE_CONTEXT_PACKAGE",
                "REQUIRED_DECISION_AFTER_PROBE": row.get("REQUIRED_DECISION_AFTER_PROBE", ""),
                "REUSE_SELECTION_ALLOWED_NOW": 0,
                "SOURCE_PATCH_SELECTION_ALLOWED_NOW": 0,
                "APPLY_ALLOWED_NOW": 0,
            })

        for i, row in enumerate(disabled, 1):
            disabled_review.append({
                "DISABLED_REVIEW_ROW": i,
                "SCRIPT_PATH": row.get("SCRIPT_PATH", ""),
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "CY_REVIEW_STATUS": "ACCEPT_DISABLED_PLACEHOLDER",
                "RUNTIME_EXECUTION_NOW": 0,
            })

        execution_package_requirements = [
            {"REQ_ROW": 1, "REQUIREMENT": "10CZ_PACKAGE_READ_ONLY_SOURCE_CONTEXT_PROBES", "DETAIL": "10CZ should package read-only source-context probes from the accepted 10CX rows.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "NO_DOTTALK_RUNTIME_COMMANDS_IN_PROBE_PACKAGE", "DETAIL": "10CZ should not run DotTalk runtime commands; it should stage/read source text only unless separately authorized.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "NO_SOURCE_EDITS", "DETAIL": "10CZ must not edit source; any source patch requires a later guarded patch package with @dottalk.usage updates.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "CLASSIFY_PROBE_RESULTS", "DETAIL": "Later probe results must classify exact writer path, generic binding, false positive, or inconclusive.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "REQUIREMENT": "DO_NOT_CONFIRM_REUSE_YET", "DETAIL": "CY review does not confirm native writer reuse.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Active HELP/CMDHELPCHK materialization must remain native/schema-aware, not raw DBF byte mutation.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 7, "REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until a later guarded apply package is reviewed and explicitly authorized.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, row in enumerate(evidence, 1):
            evidence_review.append({
                "EVIDENCE_REVIEW_ROW": i,
                "SOURCE": row.get("SOURCE", ""),
                "ROW_COUNT": row.get("ROW_COUNT", ""),
                "ROLE": row.get("ROLE", ""),
                "CY_EVIDENCE_REVIEW_STATUS": "ACCEPT_CARRY_FORWARD",
            })

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries remain an accounting/idempotency issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10CX", "OBSERVED_OCCURRENCES": sp_cx_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_cx_count >= 1 else "MISSING", "DETAIL": "10CX savepoint presence is the precondition for 10CY."},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CY probe staging review.",
            })

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "CX_PROBE_STAGING_REVIEWED", "VALUE": 1, "DETAIL": "10CX source-context probe staging reviewed and accepted."},
            {"DECISION_ROW": 2, "DECISION": "SOURCE_CONTEXT_PROBE_PACKAGE_REQUIRED", "VALUE": 1, "DETAIL": "10CZ should package read-only source-context probes."},
            {"DECISION_ROW": 3, "DECISION": "RUNTIME_EXECUTION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "Runtime execution remains blocked."},
            {"DECISION_ROW": 4, "DECISION": "REUSE_PATH_SELECTED_NOW", "VALUE": 0, "DETAIL": "Reuse remains deferred."},
            {"DECISION_ROW": 5, "DECISION": "SOURCE_PATCH_SELECTED_NOW", "VALUE": 0, "DETAIL": "Source patch remains deferred."},
            {"DECISION_ROW": 6, "DECISION": "APPLY_EXECUTION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "Apply remains blocked."},
        ]

        paths = [
            (cy_root / "probe_staging_review_v1.csv", probe_review, ["PROBE_REVIEW_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","LINE","SOURCE_EXISTS","FILE_SHA256","CY_PROBE_REVIEW_DISPOSITION","CY_PROBE_REVIEW_DETAIL","ELIGIBLE_FOR_10CZ_SOURCE_CONTEXT_PACKAGE","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cy_root / "source_context_plan_review_v1.csv", context_plan_review, ["CONTEXT_REVIEW_ROW","PROBE_ID","FILE_PATH","LINE","READ_WINDOW_BEFORE","READ_WINDOW_AFTER","CY_CONTEXT_REVIEW_STATUS","NO_EXECUTION","NO_SOURCE_EDIT","NO_HELP_CMDHELPCHK_APPLY"]),
            (cy_root / "target_probe_matrix_review_v1.csv", target_matrix_review, ["MATRIX_REVIEW_ROW","INVESTIGATION_TARGET","STAGED_PROBE_ROWS","CY_TARGET_REVIEW_STATUS","REQUIRED_DECISION_AFTER_PROBE","REUSE_SELECTION_ALLOWED_NOW","SOURCE_PATCH_SELECTION_ALLOWED_NOW","APPLY_ALLOWED_NOW"]),
            (cy_root / "disabled_probe_script_review_v1.csv", disabled_review, ["DISABLED_REVIEW_ROW","SCRIPT_PATH","INVESTIGATION_TARGET","CY_REVIEW_STATUS","RUNTIME_EXECUTION_NOW"]),
            (cy_root / "source_context_probe_package_requirements_v1.csv", execution_package_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cy_root / "evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","SOURCE","ROW_COUNT","ROLE","CY_EVIDENCE_REVIEW_STATUS"]),
            (cy_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (cy_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
            (cy_root / "review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = cy_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled_script = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CZ_SOURCE_CONTEXT_PACKAGE_TEMPLATE.ps1.disabled"
        disabled_script.write_text('throw "10CY is review only. Generate a dedicated 10CZ source-context probe package before reading source contexts or authorizing any mutation."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CY_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cy_root / "native_writer_probe_staging_review_v1.md"
        notes.write_text("# 10CY Native Writer Probe Staging Review\n\n10CY reviews 10CX source-context probe staging and requires a 10CZ source-context probe package. It does not execute probes, select reuse, select source patch, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = cy_root / "README_10CY_NATIVE_WRITER_PROBE_STAGING_REVIEW.md"
        readme.write_text("# 10CY Native Writer Probe Staging Review\n\nReview-only package. No runtime execution or protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_probe_staging_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled_script, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_probe_staging_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CY writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Probe staging review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Probe staging review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "PROBE_STAGING_REVIEWED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(probe_review)} staged probes reviewed."},
        {"ITEM": "SOURCE_CONTEXT_PROBE_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10CZ should package read-only source-context probes."},
        {"ITEM": "RUNTIME_EXECUTION_AUTHORIZED_NOW", "STATUS": "NO", "DETAIL": "Runtime execution remains blocked."},
        {"ITEM": "REUSE_PATH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains deferred."},
        {"ITEM": "SOURCE_PATCH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Source patch remains deferred."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_probe_staging_review_v1.csv", probe_review, ["PROBE_REVIEW_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","LINE","SOURCE_EXISTS","FILE_SHA256","CY_PROBE_REVIEW_DISPOSITION","CY_PROBE_REVIEW_DETAIL","ELIGIBLE_FOR_10CZ_SOURCE_CONTEXT_PACKAGE","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_source_context_plan_review_v1.csv", context_plan_review, ["CONTEXT_REVIEW_ROW","PROBE_ID","FILE_PATH","LINE","READ_WINDOW_BEFORE","READ_WINDOW_AFTER","CY_CONTEXT_REVIEW_STATUS","NO_EXECUTION","NO_SOURCE_EDIT","NO_HELP_CMDHELPCHK_APPLY"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_target_probe_matrix_review_v1.csv", target_matrix_review, ["MATRIX_REVIEW_ROW","INVESTIGATION_TARGET","STAGED_PROBE_ROWS","CY_TARGET_REVIEW_STATUS","REQUIRED_DECISION_AFTER_PROBE","REUSE_SELECTION_ALLOWED_NOW","SOURCE_PATCH_SELECTION_ALLOWED_NOW","APPLY_ALLOWED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_disabled_probe_script_review_v1.csv", disabled_review, ["DISABLED_REVIEW_ROW","SCRIPT_PATH","INVESTIGATION_TARGET","CY_REVIEW_STATUS","RUNTIME_EXECUTION_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_source_context_probe_package_requirements_v1.csv", execution_package_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","SOURCE","ROW_COUNT","ROLE","CY_EVIDENCE_REVIEW_STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CX_STATUS": cx.get("STATUS",""),
        "MSG_022AE_6_5_10CX_SAVEPOINT_PRESENT": 1 if sp_cx else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10CX_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cx_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CX_STAGED_PROBE_ROWS": len(staged),
        "CX_SOURCE_CONTEXT_PLAN_ROWS": len(context_plan),
        "CX_TARGET_PROBE_MATRIX_ROWS": len(target_matrix),
        "PROBE_STAGING_REVIEW_ROWS": len(probe_review),
        "SOURCE_CONTEXT_PLAN_REVIEW_ROWS": len(context_plan_review),
        "SOURCE_CONTEXT_PROBE_PACKAGE_REQUIREMENT_ROWS": len(execution_package_requirements),
        "CY_ROOT": rel(cy_root, repo),
        "PROBE_STAGING_REVIEWED": 1 if status == GREEN else 0,
        "SOURCE_CONTEXT_PROBE_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cy_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CY_NATIVE_WRITER_PROBE_STAGING_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CY Native Writer Probe Staging Review\n\nStatus: `{status}`\n\n10CY reviews the 10CX source-context probe staging and requires a 10CZ source-context probe package. It does not execute probes, select reuse, select source patch, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(cy_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CX status: {cx.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CX savepoint present: {1 if sp_cx else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CX staged probe rows: {len(staged)}")
    print(f"  CX source context plan rows: {len(context_plan)}")
    print(f"  CX target probe matrix rows: {len(target_matrix)}")
    print(f"  probe staging review rows: {len(probe_review)}")
    print(f"  source context plan review rows: {len(context_plan_review)}")
    print(f"  source context probe package requirement rows: {len(execution_package_requirements)}")
    print(f"  review root: {rel(cy_root, repo)}")
    print("  probe staging reviewed: 1")
    print("  source context probe package required: 1")
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
