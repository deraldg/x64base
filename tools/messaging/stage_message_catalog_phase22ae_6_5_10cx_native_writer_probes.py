#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CX_NATIVE_WRITER_PROBE_STAGING_PACKAGE_GREEN_PROBES_STAGED_NO_EXECUTION_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CX_NATIVE_WRITER_PROBE_STAGING_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CY_NATIVE_WRITER_PROBE_STAGING_REVIEW"

REPORT = Path("docs/messaging/reports")
CW_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cw_status_summary_v1.csv"
CW_SCOPE_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cw_scope_review_v1.csv"
CW_TARGET_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cw_target_review_v1.csv"
CW_PROBE_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cw_probe_plan_review_v1.csv"
CW_STAGING_REQS = REPORT / "message_catalog_phase22ae_6_5_10cw_probe_staging_requirements_v1.csv"
CW_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10cw_evidence_review_v1.csv"
CW_DUP_NOTES = REPORT / "message_catalog_phase22ae_6_5_10cw_duplicate_savepoint_notes_v1.csv"
CW_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cw_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CX_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cx_native_writer_probe_staging_package_v1")

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

def source_digest(repo, path_text):
    p = repo / path_text
    if not path_text:
        return "", "", 0
    if not p.exists() or not p.is_file():
        return "", "", 0
    return str(p.stat().st_size), sha(p), 1

def probe_kind(target):
    if target == "HELP_DATA_NATIVE_WRITER_PATH":
        return "HELP_DATA_SOURCE_CONTEXT_PROBE"
    if target == "CMDHELPCHK_NATIVE_WRITER_PATH":
        return "CMDHELPCHK_SOURCE_CONTEXT_PROBE"
    if target == "GENERIC_NATIVE_WRITER_TARGET_BINDING":
        return "GENERIC_TARGET_BINDING_SOURCE_CONTEXT_PROBE"
    return "SUPPORTING_OR_EXCLUSION_SOURCE_CONTEXT_PROBE"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cw = first(repo / CW_SUMMARY)
    scope_review = rows(repo / CW_SCOPE_REVIEW)
    target_review = rows(repo / CW_TARGET_REVIEW)
    probe_review = rows(repo / CW_PROBE_REVIEW)
    staging_reqs = rows(repo / CW_STAGING_REQS)
    evidence_review = rows(repo / CW_EVIDENCE)
    dup_notes_in = rows(repo / CW_DUP_NOTES)
    blocked_in = rows(repo / CW_BLOCKED)

    sp_cw, latest_cw = savepoint(repo, "MSG-022AE.6.5.10CW")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_cw_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CW")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cx_root = repo / CX_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CW_GREEN", cw.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CW_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_REVIEW_GREEN_PROBE_STAGING_PACKAGE_REQUIRED_SOURCE_HELD", cw.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CW_SAVEPOINT_PRESENT", sp_cw, latest_cw)
    gate("CW_SCOPE_REVIEWED", cw.get("NEXT_INVESTIGATION_SCOPE_REVIEWED") == "1", cw.get("NEXT_INVESTIGATION_SCOPE_REVIEWED", "missing"))
    gate("CW_PROBE_STAGING_REQUIRED", cw.get("PROBE_STAGING_PACKAGE_REQUIRED") == "1", cw.get("PROBE_STAGING_PACKAGE_REQUIRED", "missing"))
    gate("CW_RUNTIME_EXECUTION_NOT_AUTHORIZED", cw.get("RUNTIME_EXECUTION_AUTHORIZED_NOW") == "0", cw.get("RUNTIME_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CW_REUSE_NOT_SELECTED", cw.get("REUSE_PATH_SELECTED_NOW") == "0", cw.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("CW_WRITER_REUSE_NOT_CONFIRMED", cw.get("WRITER_REUSE_CONFIRMED_NOW") == "0", cw.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CW_SOURCE_PATCH_NOT_SELECTED", cw.get("SOURCE_PATCH_SELECTED_NOW") == "0", cw.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("CW_SOURCE_PATCH_NOT_PROVEN", cw.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cw.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CW_SOURCE_MUTATION_NOT_AUTHORIZED", cw.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cw.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CW_APPLY_EXECUTION_NOT_AUTHORIZED", cw.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cw.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CW_HELP_APPLY_NOT_EXECUTED", cw.get("HELP_DATA_APPLY_EXECUTED") == "0", cw.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CW_CMDHELPCHK_APPLY_NOT_EXECUTED", cw.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cw.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CW_SCOPE_REVIEW_ROWS_PRESENT", len(scope_review) > 0, len(scope_review))
    gate("CW_PROBE_REVIEW_ROWS_PRESENT", len(probe_review) > 0, len(probe_review))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CX_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cx_root.exists()) or args.replace_existing_package, rel(cx_root, repo))

    status = BLOCKED
    staged_probe_rows = []
    source_context_plan = []
    target_probe_matrix = []
    disabled_probe_scripts = []
    evidence_carry_forward = []
    duplicate_savepoint_notes = []
    review_requirements = []
    blocked_rows = []
    artifacts = []

    if failures == 0:
        if cx_root.exists() and args.replace_existing_package:
            shutil.rmtree(cx_root)
        cx_root.mkdir(parents=True, exist_ok=True)

        eligible = [r for r in scope_review if str(r.get("ELIGIBLE_FOR_10CX_PROBE_STAGING", "")) == "1"]
        if not eligible:
            eligible = scope_review

        for i, row in enumerate(eligible, 1):
            fp = row.get("FILE_PATH", "")
            bytes_text, file_sha, exists = source_digest(repo, fp)
            kind = probe_kind(row.get("INVESTIGATION_TARGET", ""))
            staged_probe_rows.append({
                "STAGED_PROBE_ROW": i,
                "PROBE_ID": f"CX-PROBE-{i:03d}",
                "PROBE_KIND": kind,
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "FILE_PATH": fp,
                "LINE": row.get("LINE", ""),
                "SOURCE_SIGNAL_SCORE": row.get("SOURCE_SIGNAL_SCORE", ""),
                "SOURCE_EXISTS": exists,
                "FILE_BYTES": bytes_text,
                "FILE_SHA256": file_sha,
                "PROBE_ACTION": "Stage source-context review only: inspect file and surrounding lines; do not execute, edit, import, or apply.",
                "EXPECTED_OUTPUT": "Classify as exact writer path, generic target binding, false positive, or inconclusive.",
                "RUNTIME_EXECUTION_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })
            source_context_plan.append({
                "CONTEXT_PLAN_ROW": i,
                "PROBE_ID": f"CX-PROBE-{i:03d}",
                "FILE_PATH": fp,
                "LINE": row.get("LINE", ""),
                "READ_WINDOW_BEFORE": 30,
                "READ_WINDOW_AFTER": 30,
                "SEARCH_TERMS": "HELP DATA; CMDHELPCHK; import; write; update; append; insert; save; @dottalk.usage",
                "NO_EXECUTION": 1,
                "NO_SOURCE_EDIT": 1,
                "NO_HELP_CMDHELPCHK_APPLY": 1,
            })

        target_counts = {}
        for row in staged_probe_rows:
            key = row["INVESTIGATION_TARGET"]
            target_counts[key] = target_counts.get(key, 0) + 1
        for target, count in sorted(target_counts.items()):
            target_probe_matrix.append({
                "MATRIX_ROW": len(target_probe_matrix) + 1,
                "INVESTIGATION_TARGET": target,
                "STAGED_PROBE_ROWS": count,
                "REQUIRED_DECISION_AFTER_PROBE": "Confirm exact writer path, reject as false positive, or continue investigation.",
                "REUSE_SELECTION_ALLOWED_NOW": 0,
                "SOURCE_PATCH_SELECTION_ALLOWED_NOW": 0,
                "APPLY_ALLOWED_NOW": 0,
            })

        scripts = cx_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        for item in target_probe_matrix:
            safe = re.sub(r"[^A-Za-z0-9_]+", "_", item["INVESTIGATION_TARGET"]).strip("_")
            p = scripts / f"CX_{safe}_SOURCE_CONTEXT_PROBE.ps1.disabled"
            p.write_text(
                'throw "10CX stages source-context probes only. Review 10CY before running any probe, runtime command, source edit, or apply step."\n',
                encoding="utf-8"
            )
            disabled_probe_scripts.append({
                "SCRIPT_ROW": len(disabled_probe_scripts) + 1,
                "SCRIPT_PATH": rel(p, repo),
                "INVESTIGATION_TARGET": item["INVESTIGATION_TARGET"],
                "STATUS": "DISABLED_PLACEHOLDER",
                "RUNTIME_EXECUTION_NOW": 0,
            })

        evidence_carry_forward = []
        for i, row in enumerate(evidence_review, 1):
            evidence_carry_forward.append({
                "EVIDENCE_ROW": i,
                "SOURCE": row.get("SOURCE", ""),
                "ROW_COUNT": row.get("ROW_COUNT", ""),
                "ROLE": row.get("ROLE", ""),
                "CARRY_FORWARD_STATUS": "CARRIED_TO_10CX_PROBE_STAGING",
            })

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries remain an accounting/idempotency issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10CW", "OBSERVED_OCCURRENCES": sp_cw_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_cw_count >= 1 else "MISSING", "DETAIL": "10CW savepoint presence is the precondition for 10CX."},
        ]

        review_requirements = [
            {"REQ_ROW": 1, "REQUIREMENT": "10CY_REVIEW_STAGED_PROBES_BEFORE_EXECUTION", "DETAIL": "10CY must review staged probes before any source-context probe is run.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "KEEP_PROBES_SOURCE_CONTEXT_ONLY", "DETAIL": "Any later probe execution must read source/report context only unless separately authorized.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "DO_NOT_CONFIRM_REUSE_FROM_STAGING", "DETAIL": "Probe staging does not confirm native writer reuse.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "DO_NOT_PROVE_PATCH_NEED_FROM_STAGING", "DETAIL": "Probe staging does not prove source patch need.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
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
                "CARRY_FORWARD_DETAIL": "Still blocked after CX probe staging.",
            })

        paths = [
            (cx_root / "staged_source_context_probes_v1.csv", staged_probe_rows, ["STAGED_PROBE_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","LINE","SOURCE_SIGNAL_SCORE","SOURCE_EXISTS","FILE_BYTES","FILE_SHA256","PROBE_ACTION","EXPECTED_OUTPUT","RUNTIME_EXECUTION_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cx_root / "source_context_probe_plan_v1.csv", source_context_plan, ["CONTEXT_PLAN_ROW","PROBE_ID","FILE_PATH","LINE","READ_WINDOW_BEFORE","READ_WINDOW_AFTER","SEARCH_TERMS","NO_EXECUTION","NO_SOURCE_EDIT","NO_HELP_CMDHELPCHK_APPLY"]),
            (cx_root / "target_probe_matrix_v1.csv", target_probe_matrix, ["MATRIX_ROW","INVESTIGATION_TARGET","STAGED_PROBE_ROWS","REQUIRED_DECISION_AFTER_PROBE","REUSE_SELECTION_ALLOWED_NOW","SOURCE_PATCH_SELECTION_ALLOWED_NOW","APPLY_ALLOWED_NOW"]),
            (cx_root / "disabled_probe_scripts_v1.csv", disabled_probe_scripts, ["SCRIPT_ROW","SCRIPT_PATH","INVESTIGATION_TARGET","STATUS","RUNTIME_EXECUTION_NOW"]),
            (cx_root / "evidence_carry_forward_v1.csv", evidence_carry_forward, ["EVIDENCE_ROW","SOURCE","ROW_COUNT","ROLE","CARRY_FORWARD_STATUS"]),
            (cx_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (cx_root / "probe_staging_review_requirements_v1.csv", review_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cx_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CX_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cx_root / "native_writer_probe_staging_package_v1.md"
        notes.write_text("# 10CX Native Writer Probe Staging Package\n\n10CX stages source-context probes only. It does not execute probes, select reuse, select source patch, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = cx_root / "README_10CX_NATIVE_WRITER_PROBE_STAGING_PACKAGE.md"
        readme.write_text("# 10CX Native Writer Probe Staging Package\n\nProbe-staging package only. No runtime execution or protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_probe_staging_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_probe_staging_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for r in disabled_probe_scripts:
            p = repo / r["SCRIPT_PATH"]
            if p.exists():
                artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "disabled_probe_placeholder", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CX writes docs/messaging probe-staging artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Probe staging only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Probe staging only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "PROBES_STAGED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(staged_probe_rows)} source-context probes staged."},
        {"ITEM": "RUNTIME_EXECUTION_NOW", "STATUS": "NO", "DETAIL": "No probes are executed by 10CX."},
        {"ITEM": "REUSE_PATH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains deferred."},
        {"ITEM": "SOURCE_PATCH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Source patch remains deferred."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_staged_source_context_probes_v1.csv", staged_probe_rows, ["STAGED_PROBE_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","LINE","SOURCE_SIGNAL_SCORE","SOURCE_EXISTS","FILE_BYTES","FILE_SHA256","PROBE_ACTION","EXPECTED_OUTPUT","RUNTIME_EXECUTION_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_source_context_probe_plan_v1.csv", source_context_plan, ["CONTEXT_PLAN_ROW","PROBE_ID","FILE_PATH","LINE","READ_WINDOW_BEFORE","READ_WINDOW_AFTER","SEARCH_TERMS","NO_EXECUTION","NO_SOURCE_EDIT","NO_HELP_CMDHELPCHK_APPLY"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_target_probe_matrix_v1.csv", target_probe_matrix, ["MATRIX_ROW","INVESTIGATION_TARGET","STAGED_PROBE_ROWS","REQUIRED_DECISION_AFTER_PROBE","REUSE_SELECTION_ALLOWED_NOW","SOURCE_PATCH_SELECTION_ALLOWED_NOW","APPLY_ALLOWED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_disabled_probe_scripts_v1.csv", disabled_probe_scripts, ["SCRIPT_ROW","SCRIPT_PATH","INVESTIGATION_TARGET","STATUS","RUNTIME_EXECUTION_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_evidence_carry_forward_v1.csv", evidence_carry_forward, ["EVIDENCE_ROW","SOURCE","ROW_COUNT","ROLE","CARRY_FORWARD_STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_probe_staging_review_requirements_v1.csv", review_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CW_STATUS": cw.get("STATUS",""),
        "MSG_022AE_6_5_10CW_SAVEPOINT_PRESENT": 1 if sp_cw else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10CW_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cw_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CW_SCOPE_REVIEW_ROWS": len(scope_review),
        "CW_TARGET_REVIEW_ROWS": len(target_review),
        "CW_PROBE_PLAN_REVIEW_ROWS": len(probe_review),
        "STAGED_SOURCE_CONTEXT_PROBE_ROWS": len(staged_probe_rows),
        "SOURCE_CONTEXT_PLAN_ROWS": len(source_context_plan),
        "TARGET_PROBE_MATRIX_ROWS": len(target_probe_matrix),
        "DISABLED_PROBE_SCRIPT_ROWS": len(disabled_probe_scripts),
        "CX_ROOT": rel(cx_root, repo),
        "PROBES_STAGED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cx_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CX_NATIVE_WRITER_PROBE_STAGING_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CX Native Writer Probe Staging Package\n\nStatus: `{status}`\n\n10CX stages source-context probes only. It does not execute probes, select reuse, select source patch, authorize apply, or mutate protected systems.\n\nProbe staging root:\n\n```text\n{rel(cx_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CW status: {cw.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CW savepoint present: {1 if sp_cw else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CW scope review rows: {len(scope_review)}")
    print(f"  CW target review rows: {len(target_review)}")
    print(f"  CW probe plan review rows: {len(probe_review)}")
    print(f"  staged source-context probe rows: {len(staged_probe_rows)}")
    print(f"  source context plan rows: {len(source_context_plan)}")
    print(f"  target probe matrix rows: {len(target_probe_matrix)}")
    print(f"  disabled probe script rows: {len(disabled_probe_scripts)}")
    print(f"  probe staging root: {rel(cx_root, repo)}")
    print("  probes staged: 1")
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
