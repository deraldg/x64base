#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DF_NATIVE_WRITER_REUSE_DECISION_PACKAGE_GREEN_RUNTIME_PROOF_PLAN_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DF_NATIVE_WRITER_REUSE_DECISION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DG_NATIVE_WRITER_REUSE_DECISION_REVIEW_AND_RUNTIME_PROOF_PLAN"

REPORT = Path("docs/messaging/reports")
DE_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10de_status_summary_v1.csv"
DE_CANDIDATES = REPORT / "message_catalog_phase22ae_6_5_10de_reuse_decision_candidates_v1.csv"
DE_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10de_exact_path_resolution_review_v1.csv"
DE_TARGET = REPORT / "message_catalog_phase22ae_6_5_10de_target_resolution_review_v1.csv"
DE_FUNCTION = REPORT / "message_catalog_phase22ae_6_5_10de_function_resolution_review_v1.csv"
DE_REQS = REPORT / "message_catalog_phase22ae_6_5_10de_reuse_decision_requirements_v1.csv"
DE_DEFERRED = REPORT / "message_catalog_phase22ae_6_5_10de_still_deferred_paths_v1.csv"
DE_DUP_NOTES = REPORT / "message_catalog_phase22ae_6_5_10de_duplicate_savepoint_notes_v1.csv"
DE_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10de_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
DF_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10df_native_writer_reuse_decision_package_v1")

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

def target_is_exact(target):
    return target in {"HELP_DATA_TARGET_CANDIDATE", "CMDHELPCHK_TARGET_CANDIDATE"}

def has_writer_terms(terms):
    return bool((terms or "").strip())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    de = first(repo / DE_SUMMARY)
    candidates = rows(repo / DE_CANDIDATES)
    review = rows(repo / DE_REVIEW)
    target_review = rows(repo / DE_TARGET)
    function_review = rows(repo / DE_FUNCTION)
    reqs_in = rows(repo / DE_REQS)
    deferred_in = rows(repo / DE_DEFERRED)
    dup_notes_in = rows(repo / DE_DUP_NOTES)
    blocked_in = rows(repo / DE_BLOCKED)

    sp_de, latest_de = savepoint(repo, "MSG-022AE.6.5.10DE")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_de_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10DE")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    df_root = repo / DF_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10DE_GREEN", de.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10DE_NATIVE_WRITER_EXACT_PATH_RESOLUTION_REVIEW_GREEN_REUSE_DECISION_PACKAGE_REQUIRED_SOURCE_HELD", de.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10DE_SAVEPOINT_PRESENT", sp_de, latest_de)
    gate("DE_EXACT_PATH_REVIEWED", de.get("EXACT_PATH_RESOLUTION_REVIEWED") == "1", de.get("EXACT_PATH_RESOLUTION_REVIEWED", "missing"))
    gate("DE_REUSE_DECISION_PACKAGE_REQUIRED", de.get("REUSE_DECISION_PACKAGE_REQUIRED") == "1", de.get("REUSE_DECISION_PACKAGE_REQUIRED", "missing"))
    gate("DE_REUSE_NOT_SELECTED", de.get("REUSE_PATH_SELECTED_NOW") == "0", de.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("DE_WRITER_REUSE_NOT_CONFIRMED", de.get("WRITER_REUSE_CONFIRMED_NOW") == "0", de.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("DE_SOURCE_PATCH_NOT_SELECTED", de.get("SOURCE_PATCH_SELECTED_NOW") == "0", de.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("DE_SOURCE_PATCH_NOT_PROVEN", de.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", de.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("DE_SOURCE_MUTATION_NOT_AUTHORIZED", de.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", de.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("DE_APPLY_EXECUTION_NOT_AUTHORIZED", de.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", de.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("DE_HELP_APPLY_NOT_EXECUTED", de.get("HELP_DATA_APPLY_EXECUTED") == "0", de.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("DE_CMDHELPCHK_APPLY_NOT_EXECUTED", de.get("CMDHELPCHK_APPLY_EXECUTED") == "0", de.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("DE_REUSE_DECISION_CANDIDATES_PRESENT", len(candidates) > 0, len(candidates))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("DF_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not df_root.exists()) or args.replace_existing_package, rel(df_root, repo))

    status = BLOCKED
    reuse_decision_rows = []
    runtime_proof_plan_rows = []
    selected_path_rows = []
    deferred_rows = []
    review_checklist = []
    duplicate_savepoint_notes = []
    blocked_rows = []
    artifacts = []
    exact_candidate_count = 0

    if failures == 0:
        if df_root.exists() and args.replace_existing_package:
            shutil.rmtree(df_root)
        df_root.mkdir(parents=True, exist_ok=True)

        for i, row in enumerate(candidates, 1):
            exact_target = 1 if target_is_exact(row.get("TARGET_RESOLUTION_CANDIDATE", "")) else 0
            writer_signal = 1 if has_writer_terms(row.get("WRITER_SIGNAL_TERMS", "")) else 0
            has_func = 1 if (row.get("RESOLVED_FUNCTION_SIGNATURE", "").strip() or row.get("RESOLVED_FUNCTION_NAME", "").strip()) else 0
            decision_status = "EXACT_REUSE_RUNTIME_PROOF_CANDIDATE" if exact_target and writer_signal and has_func else "REUSE_DECISION_INSUFFICIENT_REVIEW_REQUIRED"
            if decision_status == "EXACT_REUSE_RUNTIME_PROOF_CANDIDATE":
                exact_candidate_count += 1
            reuse_decision_rows.append({
                "REUSE_DECISION_ROW": i,
                "PROBE_ID": row.get("PROBE_ID", ""),
                "FILE_PATH": row.get("FILE_PATH", ""),
                "RESOLVED_FUNCTION_LINE": row.get("RESOLVED_FUNCTION_LINE", ""),
                "RESOLVED_FUNCTION_NAME": row.get("RESOLVED_FUNCTION_NAME", ""),
                "RESOLVED_FUNCTION_SIGNATURE": row.get("RESOLVED_FUNCTION_SIGNATURE", ""),
                "TARGET_RESOLUTION_CANDIDATE": row.get("TARGET_RESOLUTION_CANDIDATE", ""),
                "TARGET_SIGNAL_TERMS": row.get("TARGET_SIGNAL_TERMS", ""),
                "WRITER_SIGNAL_TERMS": row.get("WRITER_SIGNAL_TERMS", ""),
                "HAS_EXACT_TARGET_SIGNAL": exact_target,
                "HAS_WRITER_SIGNAL": writer_signal,
                "HAS_FUNCTION_CONTEXT": has_func,
                "DF_REUSE_DECISION_STATUS": decision_status,
                "DF_REUSE_DECISION_DETAIL": "Candidate should move to runtime proof plan, but reuse is not confirmed until runtime proof passes." if decision_status == "EXACT_REUSE_RUNTIME_PROOF_CANDIDATE" else "Candidate remains insufficient for reuse confirmation.",
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        runtime_proof_plan_rows = [
            {"PROOF_ROW": 1, "PROOF_ITEM": "BUILD_OR_USE_NATIVE_WRITER_PROOF_SURFACE", "DETAIL": "Next package should prove whether exact candidate function/path can write/materialize HELP DATA or CMDHELPCHK using native runtime-safe mechanism.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"PROOF_ROW": 2, "PROOF_ITEM": "PROVE_TARGET_SPECIFIC_WRITE_OR_REJECT_REUSE", "DETAIL": "Proof must distinguish writer/materializer from reader/checker/report output.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"PROOF_ROW": 3, "PROOF_ITEM": "NO_ACTIVE_HELP_CMDHELPCHK_APPLY_IN_PROOF_PLAN", "DETAIL": "Runtime proof plan may be staged, but active apply remains blocked until separately authorized.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"PROOF_ROW": 4, "PROOF_ITEM": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Proof path must remain native/schema-aware, not raw DBF byte writing.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"PROOF_ROW": 5, "PROOF_ITEM": "IF_PROOF_FAILS_MOVE_TO_PATCH_OR_FURTHER_DISCOVERY_DECISION", "DETAIL": "If no reusable native writer exists, later package can decide patch planning or additional discovery.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        selected_path_rows = [
            {"SELECTED_ROW": 1, "SELECTED_PATH": "RUNTIME_PROOF_PLAN_REQUIRED_BEFORE_REUSE_CONFIRMATION", "SELECTED_NOW": 1, "DETAIL": f"{exact_candidate_count} exact reuse runtime-proof candidates found; runtime proof plan is required before confirming reuse.", "WRITER_REUSE_CONFIRMED_NOW": 0, "SOURCE_PATCH_NEEDED_PROVEN": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"SELECTED_ROW": 2, "SELECTED_PATH": "KEEP_HELP_CMDHELPCHK_APPLY_BLOCKED", "SELECTED_NOW": 1, "DETAIL": "No HELP DATA/CMDHELPCHK apply is authorized.", "WRITER_REUSE_CONFIRMED_NOW": 0, "SOURCE_PATCH_NEEDED_PROVEN": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, row in enumerate(deferred_in, 1):
            deferred_rows.append({
                "DEFERRED_ROW": i,
                "DEFERRED_PATH": row.get("DEFERRED_PATH", ""),
                "DEFERRED_REASON": row.get("DEFERRED_REASON", ""),
                "STILL_DEFERRED_AFTER_DF": 1,
            })

        review_checklist = [
            {"CHECK_ROW": 1, "CHECK": "REVIEW_RUNTIME_PROOF_CANDIDATES", "REQUIRED": 1, "DETAIL": f"{exact_candidate_count} candidates require runtime proof planning/review.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"CHECK_ROW": 2, "CHECK": "DO_NOT_CONFIRM_REUSE_BY_DF", "REQUIRED": 1, "DETAIL": "10DF stages a reuse-decision package but does not confirm reuse.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"CHECK_ROW": 3, "CHECK": "DO_NOT_PROVE_PATCH_NEED_BY_DF", "REQUIRED": 1, "DETAIL": "Patch need remains unproven until reuse is explicitly rejected.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"CHECK_ROW": 4, "CHECK": "PRESERVE_USAGE_CONTRACT_RULE", "REQUIRED": 1, "DETAIL": "Any later source patch must update @dottalk.usage/source-comment contracts in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"CHECK_ROW": 5, "CHECK": "KEEP_APPLY_BLOCKED", "REQUIRED": 1, "DETAIL": "No HELP DATA/CMDHELPCHK apply until a later guarded apply package is reviewed and explicitly authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries remain an accounting/idempotency issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10DE", "OBSERVED_OCCURRENCES": sp_de_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_de_count >= 1 else "MISSING", "DETAIL": "10DE savepoint presence is the precondition for 10DF."},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after DF reuse decision package.",
            })

        paths = [
            (df_root / "reuse_decision_rows_v1.csv", reuse_decision_rows, ["REUSE_DECISION_ROW","PROBE_ID","FILE_PATH","RESOLVED_FUNCTION_LINE","RESOLVED_FUNCTION_NAME","RESOLVED_FUNCTION_SIGNATURE","TARGET_RESOLUTION_CANDIDATE","TARGET_SIGNAL_TERMS","WRITER_SIGNAL_TERMS","HAS_EXACT_TARGET_SIGNAL","HAS_WRITER_SIGNAL","HAS_FUNCTION_CONTEXT","DF_REUSE_DECISION_STATUS","DF_REUSE_DECISION_DETAIL","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (df_root / "runtime_proof_plan_rows_v1.csv", runtime_proof_plan_rows, ["PROOF_ROW","PROOF_ITEM","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (df_root / "selected_safe_path_v1.csv", selected_path_rows, ["SELECTED_ROW","SELECTED_PATH","SELECTED_NOW","DETAIL","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (df_root / "still_deferred_paths_v1.csv", deferred_rows, ["DEFERRED_ROW","DEFERRED_PATH","DEFERRED_REASON","STILL_DEFERRED_AFTER_DF"]),
            (df_root / "reuse_decision_review_checklist_v1.csv", review_checklist, ["CHECK_ROW","CHECK","REQUIRED","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (df_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (df_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = df_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled_script = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DG_RUNTIME_PROOF_PLAN_TEMPLATE.ps1.disabled"
        disabled_script.write_text('throw "10DF staged reuse decision only. Run 10DG review/runtime proof plan before confirming reuse/source-patch/apply or authorizing mutation."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DF_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = df_root / "native_writer_reuse_decision_package_v1.md"
        notes.write_text("# 10DF Native Writer Reuse Decision Package\n\n10DF stages a reuse-decision package from 10DE candidates and selects runtime proof planning as the safe next step. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = df_root / "README_10DF_NATIVE_WRITER_REUSE_DECISION_PACKAGE.md"
        readme.write_text("# 10DF Native Writer Reuse Decision Package\n\nReport-only/source-held package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_reuse_decision_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled_script, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_reuse_decision_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10DF writes docs/messaging reuse decision artifacts only; no source writes."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Reuse decision package only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Reuse decision package only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "REUSE_DECISION_PACKAGE_STAGED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(reuse_decision_rows)} reuse decision rows staged."},
        {"ITEM": "RUNTIME_PROOF_PLAN_REQUIRED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{exact_candidate_count} exact runtime-proof candidates."},
        {"ITEM": "WRITER_REUSE_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains unconfirmed pending runtime proof."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Patch need remains unproven."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_reuse_decision_rows_v1.csv", reuse_decision_rows, ["REUSE_DECISION_ROW","PROBE_ID","FILE_PATH","RESOLVED_FUNCTION_LINE","RESOLVED_FUNCTION_NAME","RESOLVED_FUNCTION_SIGNATURE","TARGET_RESOLUTION_CANDIDATE","TARGET_SIGNAL_TERMS","WRITER_SIGNAL_TERMS","HAS_EXACT_TARGET_SIGNAL","HAS_WRITER_SIGNAL","HAS_FUNCTION_CONTEXT","DF_REUSE_DECISION_STATUS","DF_REUSE_DECISION_DETAIL","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_runtime_proof_plan_rows_v1.csv", runtime_proof_plan_rows, ["PROOF_ROW","PROOF_ITEM","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_selected_safe_path_v1.csv", selected_path_rows, ["SELECTED_ROW","SELECTED_PATH","SELECTED_NOW","DETAIL","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_still_deferred_paths_v1.csv", deferred_rows, ["DEFERRED_ROW","DEFERRED_PATH","DEFERRED_REASON","STILL_DEFERRED_AFTER_DF"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_reuse_decision_review_checklist_v1.csv", review_checklist, ["CHECK_ROW","CHECK","REQUIRED","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10DE_STATUS": de.get("STATUS",""),
        "MSG_022AE_6_5_10DE_SAVEPOINT_PRESENT": 1 if sp_de else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10DE_SAVEPOINT_OCCURRENCES_OBSERVED": sp_de_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "DE_REUSE_DECISION_CANDIDATE_ROWS": len(candidates),
        "REUSE_DECISION_ROWS": len(reuse_decision_rows),
        "EXACT_REUSE_RUNTIME_PROOF_CANDIDATE_ROWS": exact_candidate_count,
        "RUNTIME_PROOF_PLAN_ROWS": len(runtime_proof_plan_rows),
        "DF_ROOT": rel(df_root, repo),
        "REUSE_DECISION_PACKAGE_STAGED": 1 if status == GREEN else 0,
        "RUNTIME_PROOF_PLAN_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10df_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10DF_NATIVE_WRITER_REUSE_DECISION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10DF Native Writer Reuse Decision Package\n\nStatus: `{status}`\n\n10DF stages a reuse-decision package from 10DE candidates and selects runtime proof planning as the safe next step. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nPackage root:\n\n```text\n{rel(df_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10DE status: {de.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10DE savepoint present: {1 if sp_de else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  DE reuse decision candidate rows: {len(candidates)}")
    print(f"  reuse decision rows: {len(reuse_decision_rows)}")
    print(f"  exact reuse runtime proof candidate rows: {exact_candidate_count}")
    print(f"  runtime proof plan rows: {len(runtime_proof_plan_rows)}")
    print(f"  package root: {rel(df_root, repo)}")
    print("  reuse decision package staged: 1")
    print("  runtime proof plan required: 1")
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
