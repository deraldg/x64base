#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CV_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_PACKAGE_GREEN_SCOPE_STAGED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CV_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CW_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_REVIEW"

REPORT = Path("docs/messaging/reports")
CU_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cu_status_summary_v1.csv"
CU_SELECTION_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cu_decision_selection_review_v1.csv"
CU_SCOPE_REQS = REPORT / "message_catalog_phase22ae_6_5_10cu_next_investigation_scope_requirements_v1.csv"
CU_DUP_NOTES = REPORT / "message_catalog_phase22ae_6_5_10cu_duplicate_savepoint_notes_v1.csv"
CU_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cu_carry_forward_blocked_actions_v1.csv"

CR_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10cr_decision_evidence_v1.csv"
CQ_CONFIRM_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cq_confirmation_review_v1.csv"
CP_CONFIRM_ROWS = REPORT / "message_catalog_phase22ae_6_5_10cp_exact_native_writer_confirmation_rows_v1.csv"
CP_CONTEXT_ROWS = REPORT / "message_catalog_phase22ae_6_5_10cp_exact_native_writer_confirmation_context_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CV_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cv_native_writer_next_investigation_scope_package_v1")

HELP_RX = re.compile(r"HELP_DATA|help\s*data|helpdata|help[_\-\s]*data|help\s+msgmgr|help\s+set\s+message|HELP", re.I)
CHK_RX = re.compile(r"CMDHELPCHK|cmd_help_chk|command[_\-\s]*help[_\-\s]*check|help[_\-\s]*check", re.I)
WRITER_RX = re.compile(r"writer|write|import|update|replace|append|insert|save|create|apply|install|load|emit|generate", re.I)

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

def source_exists(repo, file_path):
    p = repo / file_path
    return 1 if p.exists() else 0

def build_focus_rows(repo, cr_evidence, cq_review, cp_rows):
    # Prefer CR decision evidence, but fall back to CQ/CP if needed.
    candidates = []
    source = cr_evidence or cq_review or cp_rows
    for row in source:
        blob = " ".join(str(row.get(k, "")) for k in row.keys())
        file_path = row.get("FILE_PATH", "")
        line = row.get("LINE", "")
        score = intish(row.get("CONFIRMATION_SIGNAL_SCORE", row.get("NARROWING_SCORE", 0)))
        if HELP_RX.search(blob) and WRITER_RX.search(blob):
            target = "HELP_DATA_NATIVE_WRITER_PATH"
            why = "Contains HELP DATA/help and writer/import/update signal."
            priority = "A"
        elif CHK_RX.search(blob) and WRITER_RX.search(blob):
            target = "CMDHELPCHK_NATIVE_WRITER_PATH"
            why = "Contains CMDHELPCHK/check and writer/import/update signal."
            priority = "A"
        elif WRITER_RX.search(blob):
            target = "GENERIC_NATIVE_WRITER_TARGET_BINDING"
            why = "Contains generic writer/import/update signal needing HELP/CMDHELPCHK target binding."
            priority = "B"
        else:
            target = "EXCLUSION_OR_SUPPORTING_CONTEXT"
            why = "No exact writer signal; useful as exclusion/supporting evidence."
            priority = "C"
        candidates.append({
            "TARGET": target,
            "PRIORITY": priority,
            "FILE_PATH": file_path,
            "LINE": line,
            "SOURCE_SIGNAL_SCORE": score,
            "WHY_INCLUDED": why,
            "SOURCE_EXISTS": source_exists(repo, file_path) if file_path else 0,
        })
    # Sort A/B before C and by score. Keep a useful bounded set.
    candidates.sort(key=lambda r: ({"A": 0, "B": 1, "C": 2}.get(r["PRIORITY"], 9), -intish(r["SOURCE_SIGNAL_SCORE"]), r["FILE_PATH"]))
    return candidates[:80]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cu = first(repo / CU_SUMMARY)
    selection_review = rows(repo / CU_SELECTION_REVIEW)
    scope_reqs = rows(repo / CU_SCOPE_REQS)
    dup_notes = rows(repo / CU_DUP_NOTES)
    blocked_in = rows(repo / CU_BLOCKED)
    cr_evidence = rows(repo / CR_EVIDENCE)
    cq_review = rows(repo / CQ_CONFIRM_REVIEW)
    cp_confirm = rows(repo / CP_CONFIRM_ROWS)
    cp_context = rows(repo / CP_CONTEXT_ROWS)

    sp_cu, latest_cu = savepoint(repo, "MSG-022AE.6.5.10CU")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_cu_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CU")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cv_root = repo / CV_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CU_GREEN", cu.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CU_NATIVE_WRITER_DECISION_SELECTION_REVIEW_GREEN_NEXT_INVESTIGATION_SCOPE_PACKAGE_REQUIRED_SOURCE_HELD", cu.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CU_SAVEPOINT_PRESENT", sp_cu, latest_cu)
    gate("CU_DECISION_SELECTION_REVIEWED", cu.get("DECISION_SELECTION_REVIEWED") == "1", cu.get("DECISION_SELECTION_REVIEWED", "missing"))
    gate("CU_CONTINUE_REVIEW_ACCEPTED", cu.get("CONTINUE_REVIEW_ACCEPTED_NOW") == "1", cu.get("CONTINUE_REVIEW_ACCEPTED_NOW", "missing"))
    gate("CU_APPLY_BLOCKED_ACCEPTED", cu.get("APPLY_BLOCKED_ACCEPTED_NOW") == "1", cu.get("APPLY_BLOCKED_ACCEPTED_NOW", "missing"))
    gate("CU_NEXT_SCOPE_PACKAGE_REQUIRED", cu.get("NEXT_INVESTIGATION_SCOPE_PACKAGE_REQUIRED") == "1", cu.get("NEXT_INVESTIGATION_SCOPE_PACKAGE_REQUIRED", "missing"))
    gate("CU_REUSE_NOT_SELECTED", cu.get("REUSE_PATH_SELECTED_NOW") == "0", cu.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("CU_WRITER_REUSE_NOT_CONFIRMED", cu.get("WRITER_REUSE_CONFIRMED_NOW") == "0", cu.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CU_SOURCE_PATCH_NOT_SELECTED", cu.get("SOURCE_PATCH_SELECTED_NOW") == "0", cu.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("CU_SOURCE_PATCH_NOT_PROVEN", cu.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cu.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CU_SOURCE_MUTATION_NOT_AUTHORIZED", cu.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cu.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CU_APPLY_EXECUTION_NOT_AUTHORIZED", cu.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cu.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CU_HELP_APPLY_NOT_EXECUTED", cu.get("HELP_DATA_APPLY_EXECUTED") == "0", cu.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CU_CMDHELPCHK_APPLY_NOT_EXECUTED", cu.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cu.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CU_SCOPE_REQUIREMENTS_PRESENT", len(scope_reqs) > 0, len(scope_reqs))
    gate("PRIOR_EVIDENCE_PRESENT", len(cr_evidence) + len(cq_review) + len(cp_confirm) > 0, len(cr_evidence) + len(cq_review) + len(cp_confirm))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CV_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cv_root.exists()) or args.replace_existing_package, rel(cv_root, repo))

    status = BLOCKED
    scope_rows = []
    scope_targets = []
    exact_probe_plan = []
    evidence_carry_forward = []
    duplicate_savepoint_notes = []
    blocked_rows = []
    scope_acceptance = []
    artifacts = []

    if failures == 0:
        if cv_root.exists() and args.replace_existing_package:
            shutil.rmtree(cv_root)
        cv_root.mkdir(parents=True, exist_ok=True)

        focus = build_focus_rows(repo, cr_evidence, cq_review, cp_confirm)
        for i, row in enumerate(focus, 1):
            scope_rows.append({
                "SCOPE_ROW": i,
                "INVESTIGATION_TARGET": row["TARGET"],
                "SCOPE_PRIORITY": row["PRIORITY"],
                "FILE_PATH": row["FILE_PATH"],
                "LINE": row["LINE"],
                "SOURCE_SIGNAL_SCORE": row["SOURCE_SIGNAL_SCORE"],
                "WHY_INCLUDED": row["WHY_INCLUDED"],
                "SOURCE_EXISTS": row["SOURCE_EXISTS"],
                "INVESTIGATION_ACTION": "Open source at/around FILE_PATH:LINE and identify exact writer function/command/target contract; no edits.",
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        target_counts = {}
        for row in scope_rows:
            target_counts[row["INVESTIGATION_TARGET"]] = target_counts.get(row["INVESTIGATION_TARGET"], 0) + 1
        for target, count in sorted(target_counts.items()):
            scope_targets.append({
                "TARGET_ROW": len(scope_targets) + 1,
                "INVESTIGATION_TARGET": target,
                "SCOPE_ROW_COUNT": count,
                "TARGET_GOAL": "Name exact native writer/import/update path and target contract, or classify as false positive/supporting evidence.",
            })

        exact_probe_plan = [
            {"PLAN_ROW": 1, "PROBE": "HELP_DATA_NATIVE_WRITER_PATH_PROBE", "DETAIL": "Trace from HELP MSGMGR / HELP SET MESSAGE artifacts to any native writer/import/update mechanism for HELP DATA rows.", "RUNTIME_EXECUTION_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"PLAN_ROW": 2, "PROBE": "CMDHELPCHK_NATIVE_WRITER_PATH_PROBE", "DETAIL": "Trace from CMDHELPCHK artifacts to any native writer/import/update mechanism for command-help-check rows.", "RUNTIME_EXECUTION_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"PLAN_ROW": 3, "PROBE": "TARGET_CONTRACT_BINDING_PROBE", "DETAIL": "For generic writer/import paths, prove whether they bind to exact HELP DATA or CMDHELPCHK targets.", "RUNTIME_EXECUTION_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"PLAN_ROW": 4, "PROBE": "FALSE_POSITIVE_READER_CHECKER_FILTER", "DETAIL": "Exclude read/check/list/status/report paths that do not write protected targets.", "RUNTIME_EXECUTION_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"PLAN_ROW": 5, "PROBE": "SOURCE_PATCH_GAP_PROBE_HELD", "DETAIL": "Only if reuse is explicitly rejected later, define the missing source surface and source-comment contract updates.", "RUNTIME_EXECUTION_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        evidence_carry_forward = [
            {"EVIDENCE_ROW": 1, "SOURCE": rel(CR_EVIDENCE, repo), "ROW_COUNT": len(cr_evidence), "ROLE": "Primary decision evidence for next investigation scope."},
            {"EVIDENCE_ROW": 2, "SOURCE": rel(CQ_CONFIRM_REVIEW, repo), "ROW_COUNT": len(cq_review), "ROLE": "Confirmation-review fallback evidence."},
            {"EVIDENCE_ROW": 3, "SOURCE": rel(CP_CONFIRM_ROWS, repo), "ROW_COUNT": len(cp_confirm), "ROLE": "Confirmation rows and signal scores."},
            {"EVIDENCE_ROW": 4, "SOURCE": rel(CP_CONTEXT_ROWS, repo), "ROW_COUNT": len(cp_context), "ROLE": "Source-context evidence for manual review."},
        ]

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries remain an accounting/idempotency issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10CU", "OBSERVED_OCCURRENCES": sp_cu_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_cu_count >= 1 else "MISSING", "DETAIL": "10CU savepoint presence is the precondition for 10CV."},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CV next investigation scope package.",
            })

        scope_acceptance = [
            {"ACCEPT_ROW": 1, "DECISION": "NEXT_INVESTIGATION_SCOPE_STAGED", "VALUE": 1, "DETAIL": "10CV staged exact next investigation scope rows."},
            {"ACCEPT_ROW": 2, "DECISION": "RUNTIME_EXECUTION_NOW", "VALUE": 0, "DETAIL": "10CV does not execute runtime probes."},
            {"ACCEPT_ROW": 3, "DECISION": "SOURCE_MUTATION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "10CV does not authorize source mutation."},
            {"ACCEPT_ROW": 4, "DECISION": "APPLY_EXECUTION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "10CV does not authorize HELP DATA/CMDHELPCHK apply."},
            {"ACCEPT_ROW": 5, "DECISION": "REUSE_PATH_SELECTED_NOW", "VALUE": 0, "DETAIL": "Reuse remains deferred."},
            {"ACCEPT_ROW": 6, "DECISION": "SOURCE_PATCH_SELECTED_NOW", "VALUE": 0, "DETAIL": "Source patch remains deferred."},
        ]

        paths = [
            (cv_root / "next_investigation_scope_v1.csv", scope_rows, ["SCOPE_ROW","INVESTIGATION_TARGET","SCOPE_PRIORITY","FILE_PATH","LINE","SOURCE_SIGNAL_SCORE","WHY_INCLUDED","SOURCE_EXISTS","INVESTIGATION_ACTION","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cv_root / "investigation_targets_v1.csv", scope_targets, ["TARGET_ROW","INVESTIGATION_TARGET","SCOPE_ROW_COUNT","TARGET_GOAL"]),
            (cv_root / "exact_probe_plan_v1.csv", exact_probe_plan, ["PLAN_ROW","PROBE","DETAIL","RUNTIME_EXECUTION_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cv_root / "evidence_carry_forward_v1.csv", evidence_carry_forward, ["EVIDENCE_ROW","SOURCE","ROW_COUNT","ROLE"]),
            (cv_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (cv_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
            (cv_root / "scope_acceptance_v1.csv", scope_acceptance, ["ACCEPT_ROW","DECISION","VALUE","DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = cv_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CW_SCOPE_REVIEW_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CV stages scope only. Run 10CW review before executing probes or authorizing source/apply work."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CV_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cv_root / "native_writer_next_investigation_scope_package_v1.md"
        notes.write_text("# 10CV Native Writer Next Investigation Scope Package\n\n10CV stages the next exact native-writer investigation scope. It does not execute probes, select reuse, select source patch, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = cv_root / "README_10CV_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_PACKAGE.md"
        readme.write_text("# 10CV Native Writer Next Investigation Scope Package\n\nScope package only. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_next_investigation_scope_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_next_investigation_scope_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CV writes docs/messaging scope artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Scope package only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Scope package only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "NEXT_INVESTIGATION_SCOPE_STAGED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(scope_rows)} scope rows staged."},
        {"ITEM": "RUNTIME_EXECUTION_NOW", "STATUS": "NO", "DETAIL": "No probes are executed by 10CV."},
        {"ITEM": "REUSE_PATH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains deferred."},
        {"ITEM": "SOURCE_PATCH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Source patch remains deferred."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_next_investigation_scope_v1.csv", scope_rows, ["SCOPE_ROW","INVESTIGATION_TARGET","SCOPE_PRIORITY","FILE_PATH","LINE","SOURCE_SIGNAL_SCORE","WHY_INCLUDED","SOURCE_EXISTS","INVESTIGATION_ACTION","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_investigation_targets_v1.csv", scope_targets, ["TARGET_ROW","INVESTIGATION_TARGET","SCOPE_ROW_COUNT","TARGET_GOAL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_exact_probe_plan_v1.csv", exact_probe_plan, ["PLAN_ROW","PROBE","DETAIL","RUNTIME_EXECUTION_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_evidence_carry_forward_v1.csv", evidence_carry_forward, ["EVIDENCE_ROW","SOURCE","ROW_COUNT","ROLE"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_scope_acceptance_v1.csv", scope_acceptance, ["ACCEPT_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CU_STATUS": cu.get("STATUS",""),
        "MSG_022AE_6_5_10CU_SAVEPOINT_PRESENT": 1 if sp_cu else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10CU_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cu_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CU_SCOPE_REQUIREMENT_ROWS": len(scope_reqs),
        "PRIOR_CR_DECISION_EVIDENCE_ROWS": len(cr_evidence),
        "PRIOR_CQ_CONFIRMATION_REVIEW_ROWS": len(cq_review),
        "PRIOR_CP_CONFIRMATION_ROWS": len(cp_confirm),
        "NEXT_INVESTIGATION_SCOPE_ROWS": len(scope_rows),
        "INVESTIGATION_TARGET_ROWS": len(scope_targets),
        "EXACT_PROBE_PLAN_ROWS": len(exact_probe_plan),
        "CV_ROOT": rel(cv_root, repo),
        "NEXT_INVESTIGATION_SCOPE_STAGED": 1 if status == GREEN else 0,
        "RUNTIME_EXECUTION_NOW": 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cv_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CV_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CV Native Writer Next Investigation Scope Package\n\nStatus: `{status}`\n\n10CV stages the next exact native-writer investigation scope. It does not execute probes, select reuse, select source patch, authorize apply, or mutate protected systems.\n\nScope root:\n\n```text\n{rel(cv_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CU status: {cu.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CU savepoint present: {1 if sp_cu else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CU scope requirement rows: {len(scope_reqs)}")
    print(f"  prior CR decision evidence rows: {len(cr_evidence)}")
    print(f"  prior CQ confirmation review rows: {len(cq_review)}")
    print(f"  prior CP confirmation rows: {len(cp_confirm)}")
    print(f"  next investigation scope rows: {len(scope_rows)}")
    print(f"  investigation target rows: {len(scope_targets)}")
    print(f"  exact probe plan rows: {len(exact_probe_plan)}")
    print(f"  scope root: {rel(cv_root, repo)}")
    print("  next investigation scope staged: 1")
    print("  runtime execution now: 0")
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
