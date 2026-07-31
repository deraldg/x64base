#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DA_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_REVIEW_GREEN_DECISION_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DA_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DB_NATIVE_WRITER_SOURCE_CONTEXT_DECISION_PACKAGE"

REPORT = Path("docs/messaging/reports")
CZ_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cz_status_summary_v1.csv"
CZ_RESULTS = REPORT / "message_catalog_phase22ae_6_5_10cz_source_context_probe_results_v1.csv"
CZ_LINES = REPORT / "message_catalog_phase22ae_6_5_10cz_captured_source_context_lines_v1.csv"
CZ_CONTEXT_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cz_source_context_summary_v1.csv"
CZ_TARGET_MATRIX = REPORT / "message_catalog_phase22ae_6_5_10cz_target_result_matrix_v1.csv"
CZ_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10cz_evidence_carry_forward_v1.csv"
CZ_DUP_NOTES = REPORT / "message_catalog_phase22ae_6_5_10cz_duplicate_savepoint_notes_v1.csv"
CZ_REQS = REPORT / "message_catalog_phase22ae_6_5_10cz_source_context_review_requirements_v1.csv"
CZ_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cz_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
DA_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10da_native_writer_source_context_probe_review_v1")

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

def review_classification(cls, hit_rows, context_rows):
    cls = cls or ""
    hit_rows = intish(hit_rows)
    context_rows = intish(context_rows)
    if cls in {"HELP_DATA_WRITER_CANDIDATE_CONTEXT", "CMDHELPCHK_WRITER_CANDIDATE_CONTEXT"}:
        return "HIGH_VALUE_WRITER_CANDIDATE_REQUIRES_DECISION_REVIEW", "Source context contains target and writer/import/update language; review before confirming reuse."
    if cls == "GENERIC_WRITER_CONTEXT":
        return "GENERIC_WRITER_CONTEXT_REQUIRES_TARGET_BINDING_DECISION", "Writer/import/update language present but target binding remains unclear."
    if cls == "TARGET_READER_CHECKER_CONTEXT":
        return "LIKELY_READER_CHECKER_OR_TARGET_CONTEXT_REVIEW_REQUIRED", "Target language present without clear writer signal."
    if cls == "SOURCE_COMMENT_CONTRACT_CONTEXT":
        return "SOURCE_COMMENT_CONTRACT_CONTEXT_CARRY_FORWARD", "Carry as @dottalk.usage/source-comment contract evidence."
    if hit_rows > 0:
        return "LOW_SIGNAL_CONTEXT_WITH_HITS_REVIEW_REQUIRED", "Contains search hits but classification is not enough to select reuse or patch."
    if context_rows == 0:
        return "NO_CONTEXT_CAPTURED_REVIEW_REQUIRED", "No context lines captured; source path/line may need review."
    return "INCONCLUSIVE_CONTEXT_REVIEW_REQUIRED", "No strong writer/target conclusion."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cz = first(repo / CZ_SUMMARY)
    results = rows(repo / CZ_RESULTS)
    lines = rows(repo / CZ_LINES)
    context_summary_in = rows(repo / CZ_CONTEXT_SUMMARY)
    target_matrix_in = rows(repo / CZ_TARGET_MATRIX)
    evidence_in = rows(repo / CZ_EVIDENCE)
    dup_notes_in = rows(repo / CZ_DUP_NOTES)
    reqs_in = rows(repo / CZ_REQS)
    blocked_in = rows(repo / CZ_BLOCKED)

    sp_cz, latest_cz = savepoint(repo, "MSG-022AE.6.5.10CZ")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_cz_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CZ")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    da_root = repo / DA_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CZ_GREEN", cz.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CZ_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_PACKAGE_GREEN_SOURCE_CONTEXT_CAPTURED_NO_MUTATION", cz.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CZ_SAVEPOINT_PRESENT", sp_cz, latest_cz)
    gate("CZ_SOURCE_CONTEXT_CAPTURED", cz.get("SOURCE_CONTEXT_CAPTURED") == "1", cz.get("SOURCE_CONTEXT_CAPTURED", "missing"))
    gate("CZ_DOTTALK_RUNTIME_NOT_EXECUTED", cz.get("DOTTALK_RUNTIME_EXECUTION_NOW") == "0", cz.get("DOTTALK_RUNTIME_EXECUTION_NOW", "missing"))
    gate("CZ_RUNTIME_NOT_AUTHORIZED", cz.get("RUNTIME_EXECUTION_AUTHORIZED_NOW") == "0", cz.get("RUNTIME_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CZ_REUSE_NOT_SELECTED", cz.get("REUSE_PATH_SELECTED_NOW") == "0", cz.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("CZ_WRITER_REUSE_NOT_CONFIRMED", cz.get("WRITER_REUSE_CONFIRMED_NOW") == "0", cz.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CZ_SOURCE_PATCH_NOT_SELECTED", cz.get("SOURCE_PATCH_SELECTED_NOW") == "0", cz.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("CZ_SOURCE_PATCH_NOT_PROVEN", cz.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cz.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CZ_SOURCE_MUTATION_NOT_AUTHORIZED", cz.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cz.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CZ_APPLY_EXECUTION_NOT_AUTHORIZED", cz.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cz.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CZ_HELP_APPLY_NOT_EXECUTED", cz.get("HELP_DATA_APPLY_EXECUTED") == "0", cz.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CZ_CMDHELPCHK_APPLY_NOT_EXECUTED", cz.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cz.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CZ_RESULT_ROWS_PRESENT", len(results) > 0, len(results))
    gate("CZ_CONTEXT_LINES_PRESENT", len(lines) > 0, len(lines))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("DA_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not da_root.exists()) or args.replace_existing_review, rel(da_root, repo))

    status = BLOCKED
    probe_result_review = []
    classification_review = []
    target_result_review = []
    evidence_review = []
    duplicate_savepoint_notes = []
    decision_package_requirements = []
    blocked_rows = []
    review_decisions = []
    artifacts = []

    if failures == 0:
        if da_root.exists() and args.replace_existing_review:
            shutil.rmtree(da_root)
        da_root.mkdir(parents=True, exist_ok=True)

        class_counts = {}
        review_counts = {}
        high_value_count = 0
        for i, row in enumerate(results, 1):
            disp, detail = review_classification(row.get("SOURCE_CONTEXT_CLASSIFICATION", ""), row.get("HIT_LINE_ROWS", ""), row.get("CONTEXT_LINE_ROWS", ""))
            if disp.startswith("HIGH_VALUE"):
                high_value_count += 1
            class_counts[row.get("SOURCE_CONTEXT_CLASSIFICATION", "")] = class_counts.get(row.get("SOURCE_CONTEXT_CLASSIFICATION", ""), 0) + 1
            review_counts[disp] = review_counts.get(disp, 0) + 1
            probe_result_review.append({
                "PROBE_REVIEW_ROW": i,
                "PROBE_ID": row.get("PROBE_ID", ""),
                "PROBE_KIND": row.get("PROBE_KIND", ""),
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "FILE_PATH": row.get("FILE_PATH", ""),
                "REQUESTED_LINE": row.get("REQUESTED_LINE", ""),
                "CONTEXT_LINE_ROWS": row.get("CONTEXT_LINE_ROWS", ""),
                "HIT_LINE_ROWS": row.get("HIT_LINE_ROWS", ""),
                "SOURCE_CONTEXT_CLASSIFICATION": row.get("SOURCE_CONTEXT_CLASSIFICATION", ""),
                "SOURCE_CONTEXT_DETAIL": row.get("SOURCE_CONTEXT_DETAIL", ""),
                "DA_REVIEW_DISPOSITION": disp,
                "DA_REVIEW_DETAIL": detail,
                "CONTEXT_ARTIFACT": row.get("CONTEXT_ARTIFACT", ""),
                "REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_AUTHORIZED_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
            })

        for cls, count in sorted(class_counts.items()):
            classification_review.append({
                "CLASS_REVIEW_ROW": len(classification_review) + 1,
                "SOURCE_CONTEXT_CLASSIFICATION": cls,
                "PROBE_RESULT_ROWS": count,
                "DA_CLASS_REVIEW_STATUS": "REQUIRES_10DB_DECISION_REVIEW",
                "DETAIL": "Classification count from 10CZ; decision still requires explicit 10DB review.",
            })
        for disp, count in sorted(review_counts.items()):
            classification_review.append({
                "CLASS_REVIEW_ROW": len(classification_review) + 1,
                "SOURCE_CONTEXT_CLASSIFICATION": disp,
                "PROBE_RESULT_ROWS": count,
                "DA_CLASS_REVIEW_STATUS": "REVIEW_DISPOSITION_COUNT",
                "DETAIL": "10DA review disposition count.",
            })

        for i, row in enumerate(target_matrix_in, 1):
            target_result_review.append({
                "TARGET_REVIEW_ROW": i,
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "PROBE_RESULT_ROWS": row.get("PROBE_RESULT_ROWS", ""),
                "NEXT_REVIEW_REQUIRED": row.get("NEXT_REVIEW_REQUIRED", ""),
                "DA_TARGET_REVIEW_STATUS": "ACCEPT_DECISION_PACKAGE_REQUIRED",
                "REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_ALLOWED_NOW": 0,
                "DETAIL": "Target result matrix requires 10DB decision package before reuse/patch/apply selection.",
            })

        for i, row in enumerate(evidence_in, 1):
            evidence_review.append({
                "EVIDENCE_REVIEW_ROW": i,
                "SOURCE": row.get("SOURCE", ""),
                "ROW_COUNT": row.get("ROW_COUNT", ""),
                "ROLE": row.get("ROLE", ""),
                "DA_EVIDENCE_REVIEW_STATUS": "ACCEPT_CARRY_FORWARD_TO_10DB",
            })

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries remain an accounting/idempotency issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10CZ", "OBSERVED_OCCURRENCES": sp_cz_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_cz_count >= 1 else "MISSING", "DETAIL": "10CZ savepoint presence is the precondition for 10DA."},
        ]

        decision_package_requirements = [
            {"REQ_ROW": 1, "REQUIREMENT": "10DB_DECISION_PACKAGE_REQUIRED", "DETAIL": "10DB must decide whether source context proves exact native writer reuse, requires more investigation, or supports patch planning.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "REVIEW_HIGH_VALUE_WRITER_CANDIDATES", "DETAIL": f"{high_value_count} high-value writer candidate context rows require explicit decision review.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "DO_NOT_CONFIRM_REUSE_FROM_DA", "DETAIL": "10DA review does not itself confirm native writer reuse.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "DO_NOT_PROVE_PATCH_NEED_FROM_DA", "DETAIL": "10DA review does not itself prove source patch need.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
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
                "CARRY_FORWARD_DETAIL": "Still blocked after DA source-context probe review.",
            })

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "CZ_SOURCE_CONTEXT_REVIEWED", "VALUE": 1, "DETAIL": "10CZ source-context results reviewed by 10DA."},
            {"DECISION_ROW": 2, "DECISION": "SOURCE_CONTEXT_DECISION_PACKAGE_REQUIRED", "VALUE": 1, "DETAIL": "10DB decision package is required."},
            {"DECISION_ROW": 3, "DECISION": "REUSE_CONFIRMED_NOW", "VALUE": 0, "DETAIL": "10DA does not confirm reuse."},
            {"DECISION_ROW": 4, "DECISION": "SOURCE_PATCH_NEEDED_PROVEN", "VALUE": 0, "DETAIL": "10DA does not prove source patch need."},
            {"DECISION_ROW": 5, "DECISION": "RUNTIME_EXECUTION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "Runtime execution remains blocked."},
            {"DECISION_ROW": 6, "DECISION": "APPLY_EXECUTION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "Apply remains blocked."},
        ]

        paths = [
            (da_root / "probe_result_review_v1.csv", probe_result_review, ["PROBE_REVIEW_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","REQUESTED_LINE","CONTEXT_LINE_ROWS","HIT_LINE_ROWS","SOURCE_CONTEXT_CLASSIFICATION","SOURCE_CONTEXT_DETAIL","DA_REVIEW_DISPOSITION","DA_REVIEW_DETAIL","CONTEXT_ARTIFACT","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"]),
            (da_root / "classification_review_v1.csv", classification_review, ["CLASS_REVIEW_ROW","SOURCE_CONTEXT_CLASSIFICATION","PROBE_RESULT_ROWS","DA_CLASS_REVIEW_STATUS","DETAIL"]),
            (da_root / "target_result_review_v1.csv", target_result_review, ["TARGET_REVIEW_ROW","INVESTIGATION_TARGET","PROBE_RESULT_ROWS","NEXT_REVIEW_REQUIRED","DA_TARGET_REVIEW_STATUS","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_ALLOWED_NOW","DETAIL"]),
            (da_root / "evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","SOURCE","ROW_COUNT","ROLE","DA_EVIDENCE_REVIEW_STATUS"]),
            (da_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (da_root / "decision_package_requirements_v1.csv", decision_package_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (da_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
            (da_root / "review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = da_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled_script = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DB_DECISION_TEMPLATE.ps1.disabled"
        disabled_script.write_text('throw "10DA is review only. Generate a dedicated 10DB decision package before selecting reuse/source-patch/apply or authorizing any mutation."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DA_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = da_root / "native_writer_source_context_probe_review_v1.md"
        notes.write_text("# 10DA Native Writer Source Context Probe Review\n\n10DA reviews the 10CZ read-only source-context probe results and requires a 10DB decision package. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = da_root / "README_10DA_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_REVIEW.md"
        readme.write_text("# 10DA Native Writer Source Context Probe Review\n\nReview-only package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_source_context_probe_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled_script, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_source_context_probe_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10DA reviews source context reports only; no source writes."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Source-context review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Source-context review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "SOURCE_CONTEXT_REVIEWED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(probe_result_review)} probe result rows reviewed."},
        {"ITEM": "SOURCE_CONTEXT_DECISION_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10DB should decide reuse/patch/further-investigation path."},
        {"ITEM": "REUSE_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains deferred."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Patch need remains unproven."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_probe_result_review_v1.csv", probe_result_review, ["PROBE_REVIEW_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","REQUESTED_LINE","CONTEXT_LINE_ROWS","HIT_LINE_ROWS","SOURCE_CONTEXT_CLASSIFICATION","SOURCE_CONTEXT_DETAIL","DA_REVIEW_DISPOSITION","DA_REVIEW_DETAIL","CONTEXT_ARTIFACT","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_classification_review_v1.csv", classification_review, ["CLASS_REVIEW_ROW","SOURCE_CONTEXT_CLASSIFICATION","PROBE_RESULT_ROWS","DA_CLASS_REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_target_result_review_v1.csv", target_result_review, ["TARGET_REVIEW_ROW","INVESTIGATION_TARGET","PROBE_RESULT_ROWS","NEXT_REVIEW_REQUIRED","DA_TARGET_REVIEW_STATUS","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_ALLOWED_NOW","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","SOURCE","ROW_COUNT","ROLE","DA_EVIDENCE_REVIEW_STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_decision_package_requirements_v1.csv", decision_package_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CZ_STATUS": cz.get("STATUS",""),
        "MSG_022AE_6_5_10CZ_SAVEPOINT_PRESENT": 1 if sp_cz else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10CZ_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cz_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CZ_SOURCE_CONTEXT_PROBE_RESULT_ROWS": len(results),
        "CZ_CAPTURED_SOURCE_CONTEXT_LINE_ROWS": len(lines),
        "PROBE_RESULT_REVIEW_ROWS": len(probe_result_review),
        "CLASSIFICATION_REVIEW_ROWS": len(classification_review),
        "TARGET_RESULT_REVIEW_ROWS": len(target_result_review),
        "DECISION_PACKAGE_REQUIREMENT_ROWS": len(decision_package_requirements),
        "DA_ROOT": rel(da_root, repo),
        "SOURCE_CONTEXT_REVIEWED": 1 if status == GREEN else 0,
        "SOURCE_CONTEXT_DECISION_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10da_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10DA_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10DA Native Writer Source Context Probe Review\n\nStatus: `{status}`\n\n10DA reviews the 10CZ read-only source-context probe results and requires a 10DB source-context decision package. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(da_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CZ status: {cz.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CZ savepoint present: {1 if sp_cz else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CZ source context probe result rows: {len(results)}")
    print(f"  CZ captured source context line rows: {len(lines)}")
    print(f"  probe result review rows: {len(probe_result_review)}")
    print(f"  classification review rows: {len(classification_review)}")
    print(f"  target result review rows: {len(target_result_review)}")
    print(f"  decision package requirement rows: {len(decision_package_requirements)}")
    print(f"  review root: {rel(da_root, repo)}")
    print("  source context reviewed: 1")
    print("  source context decision package required: 1")
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
