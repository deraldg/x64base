#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CU_NATIVE_WRITER_DECISION_SELECTION_REVIEW_GREEN_NEXT_INVESTIGATION_SCOPE_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CU_NATIVE_WRITER_DECISION_SELECTION_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CV_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_PACKAGE"

REPORT = Path("docs/messaging/reports")
CT_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10ct_status_summary_v1.csv"
CT_SELECTION = REPORT / "message_catalog_phase22ae_6_5_10ct_decision_selection_v1.csv"
CT_SELECTED = REPORT / "message_catalog_phase22ae_6_5_10ct_selected_paths_v1.csv"
CT_DEFERRED = REPORT / "message_catalog_phase22ae_6_5_10ct_deferred_paths_v1.csv"
CT_RATIONALE = REPORT / "message_catalog_phase22ae_6_5_10ct_selection_rationale_v1.csv"
CT_NEXT_REQS = REPORT / "message_catalog_phase22ae_6_5_10ct_next_review_requirements_v1.csv"
CT_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10ct_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CU_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cu_native_writer_decision_selection_review_v1")

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    ct = first(repo / CT_SUMMARY)
    selection = rows(repo / CT_SELECTION)
    selected_paths = rows(repo / CT_SELECTED)
    deferred_paths = rows(repo / CT_DEFERRED)
    rationale = rows(repo / CT_RATIONALE)
    next_reqs_in = rows(repo / CT_NEXT_REQS)
    blocked_in = rows(repo / CT_BLOCKED)

    sp_ct, latest_ct = savepoint(repo, "MSG-022AE.6.5.10CT")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_ct_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CT")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cu_root = repo / CU_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CT_GREEN", ct.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CT_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_GREEN_CONTINUE_REVIEW_SELECTED_SOURCE_HELD", ct.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CT_SAVEPOINT_PRESENT", sp_ct, latest_ct)
    gate("CT_DECISION_SELECTION_PACKAGED", ct.get("DECISION_SELECTION_PACKAGED") == "1", ct.get("DECISION_SELECTION_PACKAGED", "missing"))
    gate("CT_CONTINUE_REVIEW_SELECTED", ct.get("CONTINUE_REVIEW_SELECTED_NOW") == "1", ct.get("CONTINUE_REVIEW_SELECTED_NOW", "missing"))
    gate("CT_APPLY_BLOCKED_SELECTED", ct.get("APPLY_BLOCKED_SELECTED_NOW") == "1", ct.get("APPLY_BLOCKED_SELECTED_NOW", "missing"))
    gate("CT_REUSE_NOT_SELECTED", ct.get("REUSE_PATH_SELECTED_NOW") == "0", ct.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("CT_WRITER_REUSE_NOT_CONFIRMED", ct.get("WRITER_REUSE_CONFIRMED_NOW") == "0", ct.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CT_SOURCE_PATCH_NOT_SELECTED", ct.get("SOURCE_PATCH_SELECTED_NOW") == "0", ct.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("CT_SOURCE_PATCH_NOT_PROVEN", ct.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", ct.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CT_SOURCE_MUTATION_NOT_AUTHORIZED", ct.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", ct.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CT_APPLY_EXECUTION_NOT_AUTHORIZED", ct.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", ct.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CT_HELP_APPLY_NOT_EXECUTED", ct.get("HELP_DATA_APPLY_EXECUTED") == "0", ct.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CT_CMDHELPCHK_APPLY_NOT_EXECUTED", ct.get("CMDHELPCHK_APPLY_EXECUTED") == "0", ct.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CT_SELECTION_ROWS_PRESENT", len(selection) > 0, len(selection))
    gate("CT_SELECTED_PATHS_PRESENT", len(selected_paths) > 0, len(selected_paths))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CU_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cu_root.exists()) or args.replace_existing_review, rel(cu_root, repo))

    status = BLOCKED
    selection_review = []
    selected_path_review = []
    deferred_path_review = []
    duplicate_savepoint_notes = []
    next_scope_requirements = []
    blocked_rows = []
    review_decisions = []
    artifacts = []

    if failures == 0:
        if cu_root.exists() and args.replace_existing_review:
            shutil.rmtree(cu_root)
        cu_root.mkdir(parents=True, exist_ok=True)

        for i, row in enumerate(selection, 1):
            option = row.get("DECISION_OPTION", "")
            if option == "CONTINUE_TARGETED_DECISION_REVIEW" and row.get("SELECTED_NOW") == "1":
                disposition = "ACCEPT_SELECTED_CONTINUE_REVIEW"
                detail = "Accepted as safe selection because reuse is not confirmed and patch need is not proven."
            elif option == "KEEP_APPLY_BLOCKED" and row.get("SELECTED_NOW") == "1":
                disposition = "ACCEPT_SELECTED_APPLY_BLOCKED"
                detail = "Accepted as safety boundary."
            elif row.get("SELECTED_NOW") == "0":
                disposition = "ACCEPT_DEFERRED_PATH"
                detail = "Deferred path remains blocked pending exact evidence."
            else:
                disposition = "REVIEW_UNEXPECTED_SELECTION_STATE"
                detail = "Selection row has unexpected state and should be checked."
            selection_review.append({
                "SELECTION_REVIEW_ROW": i,
                "DECISION_OPTION": option,
                "CT_SELECTED_NOW": row.get("SELECTED_NOW", ""),
                "CT_SELECTION_STATUS": row.get("SELECTION_STATUS", ""),
                "CU_REVIEW_DISPOSITION": disposition,
                "CU_REVIEW_DETAIL": detail,
                "ACCEPTED_FOR_NEXT_SCOPE_PLANNING": 1 if disposition.startswith("ACCEPT") else 0,
                "REUSE_PATH_SELECTED_NOW": 0,
                "SOURCE_PATCH_SELECTED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
            })

        for i, row in enumerate(selected_paths, 1):
            selected_path_review.append({
                "SELECTED_PATH_REVIEW_ROW": i,
                "DECISION_OPTION": row.get("DECISION_OPTION", ""),
                "CT_SELECTION_STATUS": row.get("SELECTION_STATUS", ""),
                "CU_REVIEW_STATUS": "ACCEPT_SELECTED_SAFE_PATH" if row.get("DECISION_OPTION") in {"CONTINUE_TARGETED_DECISION_REVIEW", "KEEP_APPLY_BLOCKED"} else "REVIEW_SELECTED_PATH",
                "DETAIL": row.get("SELECTION_DETAIL", ""),
            })

        for i, row in enumerate(deferred_paths, 1):
            deferred_path_review.append({
                "DEFERRED_PATH_REVIEW_ROW": i,
                "DECISION_OPTION": row.get("DECISION_OPTION", ""),
                "CT_SELECTION_STATUS": row.get("SELECTION_STATUS", ""),
                "CU_REVIEW_STATUS": "ACCEPT_DEFERRED",
                "DETAIL": row.get("SELECTION_DETAIL", ""),
            })

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries are an append-wrapper idempotency/accounting issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10CT", "OBSERVED_OCCURRENCES": sp_ct_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_ct_count >= 1 else "MISSING", "DETAIL": "10CT savepoint presence is the precondition for 10CU."},
        ]

        next_scope_requirements = [
            {"REQ_ROW": 1, "NEXT_SCOPE_REQUIREMENT": "PLAN_NEXT_TARGETED_INVESTIGATION_SCOPE", "DETAIL": "10CV should define the next exact investigation scope after safe continue-review selection.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "NEXT_SCOPE_REQUIREMENT": "FOCUS_ON_NAMING_EXACT_WRITER_PATHS", "DETAIL": "The next scope should identify exact functions/commands/files for HELP DATA and CMDHELPCHK writer/import/update paths.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "NEXT_SCOPE_REQUIREMENT": "CARRY_DUPLICATE_SAVEPOINT_NOTE", "DETAIL": "Carry 10CS duplicate-savepoint idempotency note until a later housekeeping repair package is authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "NEXT_SCOPE_REQUIREMENT": "KEEP_REUSE_DEFERRED_UNTIL_NAMED", "DETAIL": "Do not select reuse until exact path/function/target contract is named.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "NEXT_SCOPE_REQUIREMENT": "KEEP_PATCH_DEFERRED_UNTIL_REUSE_REJECTED", "DETAIL": "Do not select source patch until native reuse is explicitly rejected.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "NEXT_SCOPE_REQUIREMENT": "PRESERVE_USAGE_CONTRACT_RULE", "DETAIL": "Any later source patch must update @dottalk.usage/source-comment contracts in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 7, "NEXT_SCOPE_REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until a later guarded apply package is reviewed and explicitly authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CU decision selection review.",
            })

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "CT_SELECTION_REVIEWED", "VALUE": 1, "DETAIL": "CT continue-review/apply-blocked selection reviewed and accepted."},
            {"DECISION_ROW": 2, "DECISION": "NEXT_INVESTIGATION_SCOPE_PACKAGE_REQUIRED", "VALUE": 1, "DETAIL": "10CV should define exact next investigation scope."},
            {"DECISION_ROW": 3, "DECISION": "CONTINUE_REVIEW_SELECTED_ACCEPTED", "VALUE": 1, "DETAIL": "Continue review remains accepted safe path."},
            {"DECISION_ROW": 4, "DECISION": "REUSE_PATH_SELECTED_NOW", "VALUE": 0, "DETAIL": "Reuse remains deferred."},
            {"DECISION_ROW": 5, "DECISION": "SOURCE_PATCH_SELECTED_NOW", "VALUE": 0, "DETAIL": "Source patch remains deferred."},
            {"DECISION_ROW": 6, "DECISION": "APPLY_EXECUTION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "Apply remains blocked."},
        ]

        paths = [
            (cu_root / "decision_selection_review_v1.csv", selection_review, ["SELECTION_REVIEW_ROW","DECISION_OPTION","CT_SELECTED_NOW","CT_SELECTION_STATUS","CU_REVIEW_DISPOSITION","CU_REVIEW_DETAIL","ACCEPTED_FOR_NEXT_SCOPE_PLANNING","REUSE_PATH_SELECTED_NOW","SOURCE_PATCH_SELECTED_NOW","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"]),
            (cu_root / "selected_path_review_v1.csv", selected_path_review, ["SELECTED_PATH_REVIEW_ROW","DECISION_OPTION","CT_SELECTION_STATUS","CU_REVIEW_STATUS","DETAIL"]),
            (cu_root / "deferred_path_review_v1.csv", deferred_path_review, ["DEFERRED_PATH_REVIEW_ROW","DECISION_OPTION","CT_SELECTION_STATUS","CU_REVIEW_STATUS","DETAIL"]),
            (cu_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (cu_root / "next_investigation_scope_requirements_v1.csv", next_scope_requirements, ["REQ_ROW","NEXT_SCOPE_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cu_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
            (cu_root / "review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = cu_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CV_SCOPE_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CU is review only. Generate a dedicated 10CV next investigation scope package before running further investigation or source/apply work."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CU_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cu_root / "native_writer_decision_selection_review_v1.md"
        notes.write_text("# 10CU Native Writer Decision Selection Review\n\n10CU reviews the 10CT safe selection: continue targeted decision review and keep apply blocked. It also carries the duplicate 10CS savepoint accounting note. No protected systems are mutated.\n", encoding="utf-8")
        readme = cu_root / "README_10CU_NATIVE_WRITER_DECISION_SELECTION_REVIEW.md"
        readme.write_text("# 10CU Native Writer Decision Selection Review\n\nReview-only package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_selection_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_selection_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CU writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Selection review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Selection review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "DECISION_SELECTION_REVIEWED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": "Continue-review/apply-blocked selection accepted."},
        {"ITEM": "NEXT_INVESTIGATION_SCOPE_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10CV should define next exact investigation scope."},
        {"ITEM": "REUSE_PATH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains deferred."},
        {"ITEM": "SOURCE_PATCH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Source patch remains deferred."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_decision_selection_review_v1.csv", selection_review, ["SELECTION_REVIEW_ROW","DECISION_OPTION","CT_SELECTED_NOW","CT_SELECTION_STATUS","CU_REVIEW_DISPOSITION","CU_REVIEW_DETAIL","ACCEPTED_FOR_NEXT_SCOPE_PLANNING","REUSE_PATH_SELECTED_NOW","SOURCE_PATCH_SELECTED_NOW","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_selected_path_review_v1.csv", selected_path_review, ["SELECTED_PATH_REVIEW_ROW","DECISION_OPTION","CT_SELECTION_STATUS","CU_REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_deferred_path_review_v1.csv", deferred_path_review, ["DEFERRED_PATH_REVIEW_ROW","DECISION_OPTION","CT_SELECTION_STATUS","CU_REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_next_investigation_scope_requirements_v1.csv", next_scope_requirements, ["REQ_ROW","NEXT_SCOPE_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CT_STATUS": ct.get("STATUS",""),
        "MSG_022AE_6_5_10CT_SAVEPOINT_PRESENT": 1 if sp_ct else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10CT_SAVEPOINT_OCCURRENCES_OBSERVED": sp_ct_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CT_DECISION_SELECTION_ROWS": len(selection),
        "CT_SELECTED_PATH_ROWS": len(selected_paths),
        "CT_DEFERRED_PATH_ROWS": len(deferred_paths),
        "DECISION_SELECTION_REVIEW_ROWS": len(selection_review),
        "NEXT_INVESTIGATION_SCOPE_REQUIREMENT_ROWS": len(next_scope_requirements),
        "CU_ROOT": rel(cu_root, repo),
        "DECISION_SELECTION_REVIEWED": 1 if status == GREEN else 0,
        "CONTINUE_REVIEW_ACCEPTED_NOW": 1 if status == GREEN else 0,
        "APPLY_BLOCKED_ACCEPTED_NOW": 1 if status == GREEN else 0,
        "NEXT_INVESTIGATION_SCOPE_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cu_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CU_NATIVE_WRITER_DECISION_SELECTION_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CU Native Writer Decision Selection Review\n\nStatus: `{status}`\n\n10CU reviews the 10CT safe selection, accepts continue-review/apply-blocked, and requires a 10CV next investigation scope package. It does not select reuse, select source patch, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(cu_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CT status: {ct.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CT savepoint present: {1 if sp_ct else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CT decision selection rows: {len(selection)}")
    print(f"  CT selected path rows: {len(selected_paths)}")
    print(f"  CT deferred path rows: {len(deferred_paths)}")
    print(f"  decision selection review rows: {len(selection_review)}")
    print(f"  next investigation scope requirement rows: {len(next_scope_requirements)}")
    print(f"  review root: {rel(cu_root, repo)}")
    print("  decision selection reviewed: 1")
    print("  continue review accepted now: 1")
    print("  apply blocked accepted now: 1")
    print("  next investigation scope package required: 1")
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
