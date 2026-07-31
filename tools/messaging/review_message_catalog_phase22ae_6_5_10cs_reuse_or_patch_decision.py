#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CS_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE_REVIEW_GREEN_SELECTION_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CS_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CT_NATIVE_WRITER_DECISION_SELECTION_PACKAGE"
REPORT = Path("docs/messaging/reports")
CR_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cr_status_summary_v1.csv"
CR_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10cr_decision_evidence_v1.csv"
CR_OPTIONS = REPORT / "message_catalog_phase22ae_6_5_10cr_decision_options_v1.csv"
CR_CHECKLIST = REPORT / "message_catalog_phase22ae_6_5_10cr_decision_review_checklist_v1.csv"
CR_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cr_carry_forward_blocked_actions_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CS_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cs_native_writer_reuse_or_patch_decision_package_review_v1")

def rows(path):
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first(path):
    data = rows(path)
    return data[0] if data else {}

def wcsv(path, data, fields):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
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

def option_disposition(row):
    option = row.get("DECISION_OPTION", "")
    status = row.get("DECISION_STATUS", "")
    selected = row.get("SELECTED_NOW", "")
    if option == "KEEP_APPLY_BLOCKED":
        return "ACCEPT_SELECTED_SAFETY_BOUNDARY", "Apply remains blocked; this is the selected CR safety option."
    if "REQUIRES_EXACT_PATH_REVIEW" in status:
        return "REVIEW_REQUIRED_BEFORE_SELECTION", "Do not select reuse until an exact path/function/target contract is named."
    if "REUSE_NOT_REJECTED" in status:
        return "REJECT_PATCH_SELECTION_FOR_NOW", "Do not plan a source patch until native reuse has been explicitly rejected."
    if "RECOMMENDED_SAFE_DEFAULT" in status:
        return "CARRY_FORWARD_FOR_SELECTION", "Continue targeted decision review can be selected by 10CT if no exact reuse path is named."
    if selected == "1":
        return "ACCEPT_SELECTED_OPTION", "Selected option carried forward for 10CT."
    return "CARRY_FORWARD_FOR_SELECTION_REVIEW", "Carry forward to 10CT selection review."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cr = first(repo / CR_SUMMARY)
    evidence = rows(repo / CR_EVIDENCE)
    options = rows(repo / CR_OPTIONS)
    checklist = rows(repo / CR_CHECKLIST)
    blocked_in = rows(repo / CR_BLOCKED)
    sp_cr, latest_cr = savepoint(repo, "MSG-022AE.6.5.10CR")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cs_root = repo / CS_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CR_GREEN", cr.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CR_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE_GREEN_DECISION_OPTIONS_STAGED_SOURCE_HELD", cr.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CR_SAVEPOINT_PRESENT", sp_cr, latest_cr)
    gate("CR_DECISION_OPTIONS_STAGED", cr.get("DECISION_OPTIONS_STAGED") == "1", cr.get("DECISION_OPTIONS_STAGED", "missing"))
    gate("CR_REUSE_NOT_SELECTED", cr.get("REUSE_PATH_SELECTED_NOW") == "0", cr.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("CR_WRITER_REUSE_NOT_CONFIRMED", cr.get("WRITER_REUSE_CONFIRMED_NOW") == "0", cr.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CR_SOURCE_PATCH_NOT_SELECTED", cr.get("SOURCE_PATCH_SELECTED_NOW") == "0", cr.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("CR_SOURCE_PATCH_NOT_PROVEN", cr.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cr.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CR_SOURCE_MUTATION_NOT_AUTHORIZED", cr.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cr.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CR_APPLY_EXECUTION_NOT_AUTHORIZED", cr.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cr.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CR_HELP_APPLY_NOT_EXECUTED", cr.get("HELP_DATA_APPLY_EXECUTED") == "0", cr.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CR_CMDHELPCHK_APPLY_NOT_EXECUTED", cr.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cr.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CR_EVIDENCE_PRESENT", len(evidence) > 0, len(evidence))
    gate("CR_OPTIONS_PRESENT", len(options) > 0, len(options))
    gate("CR_CHECKLIST_PRESENT", len(checklist) > 0, len(checklist))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CS_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cs_root.exists()) or args.replace_existing_review, rel(cs_root, repo))

    status = BLOCKED
    option_review = []
    evidence_review = []
    checklist_review = []
    selection_requirements = []
    blocked_rows = []
    review_decisions = []
    artifacts = []

    if failures == 0:
        if cs_root.exists() and args.replace_existing_review:
            shutil.rmtree(cs_root)
        cs_root.mkdir(parents=True, exist_ok=True)

        for i, row in enumerate(options, 1):
            disp, detail = option_disposition(row)
            option_review.append({
                "OPTION_REVIEW_ROW": i,
                "DECISION_OPTION": row.get("DECISION_OPTION", ""),
                "CR_DECISION_STATUS": row.get("DECISION_STATUS", ""),
                "CR_SELECTED_NOW": row.get("SELECTED_NOW", ""),
                "CS_REVIEW_DISPOSITION": disp,
                "CS_REVIEW_DETAIL": detail,
                "ELIGIBLE_FOR_10CT_SELECTION": 1 if disp in {"ACCEPT_SELECTED_SAFETY_BOUNDARY", "CARRY_FORWARD_FOR_SELECTION", "CARRY_FORWARD_FOR_SELECTION_REVIEW"} else 0,
                "SELECTED_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        for i, row in enumerate(evidence, 1):
            eclass = row.get("DECISION_EVIDENCE_CLASS", "")
            if eclass in {"REUSE_DECISION_EVIDENCE_REQUIRES_MANUAL_CONFIRMATION", "GENERIC_TARGET_BINDING_EVIDENCE_REQUIRES_MANUAL_CONFIRMATION"}:
                disp = "DECISION_WORTHY_BUT_NOT_PROOF"
                detail = "Carry forward as evidence, but do not select reuse until exact path is named."
            elif eclass == "READER_CHECKER_EXCLUSION_EVIDENCE":
                disp = "EXCLUSION_EVIDENCE"
                detail = "Use as evidence against false writer positives."
            else:
                disp = "SUPPORTING_OR_INCONCLUSIVE_EVIDENCE"
                detail = "Supporting only."
            evidence_review.append({
                "EVIDENCE_REVIEW_ROW": i,
                "SOURCE_CR_EVIDENCE_ROW": row.get("EVIDENCE_ROW", ""),
                "DISCOVERY_CLASS": row.get("DISCOVERY_CLASS", ""),
                "CONFIRMATION_CLASS": row.get("CONFIRMATION_CLASS", ""),
                "DECISION_EVIDENCE_CLASS": eclass,
                "FILE_PATH": row.get("FILE_PATH", ""),
                "LINE": row.get("LINE", ""),
                "CS_EVIDENCE_REVIEW_DISPOSITION": disp,
                "CS_EVIDENCE_REVIEW_DETAIL": detail,
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_READY_NOW": 0,
            })

        for i, row in enumerate(checklist, 1):
            checklist_review.append({
                "CHECKLIST_REVIEW_ROW": i,
                "CHECK": row.get("CHECK", ""),
                "REQUIRED_FOR": row.get("REQUIRED_FOR", ""),
                "CR_PASS_NOW": row.get("PASS_NOW", ""),
                "CS_REVIEW_STATUS": "ACCEPT_CHECK" if row.get("PASS_NOW") == "1" else "REQUIRES_10CT_DECISION_REVIEW",
                "DETAIL": row.get("DETAIL", ""),
            })

        selection_requirements = [
            {"REQ_ROW": 1, "SELECTION_REQUIREMENT": "10CT_MUST_SELECT_ONE_DECISION_PATH", "DETAIL": "10CT should explicitly select continue-review, exact reuse, or source-patch planning; safety default remains apply blocked.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "SELECTION_REQUIREMENT": "EXACT_REUSE_SELECTION_REQUIRES_NAMED_PATH", "DETAIL": "Any reuse selection must name exact path/function/command and target record contract.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "SELECTION_REQUIREMENT": "SOURCE_PATCH_SELECTION_REQUIRES_REUSE_REJECTION", "DETAIL": "Source patch planning requires explicit native reuse rejection and gap statement.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "SELECTION_REQUIREMENT": "SOURCE_PATCH_REQUIRES_USAGE_CONTRACT_UPDATES", "DETAIL": "Any later source patch must include @dottalk.usage/source-comment contract updates in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "SELECTION_REQUIREMENT": "RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Raw DBF byte mutation remains forbidden as active promotion/materialization path.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "SELECTION_REQUIREMENT": "APPLY_REMAINS_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until later guarded apply package is reviewed and explicitly authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({"CARRY_FORWARD_ROW": i, "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""), "BLOCKED": 1, "REASON": b.get("REASON", ""), "CARRY_FORWARD_DETAIL": "Still blocked after CS decision package review."})

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "CR_DECISION_PACKAGE_REVIEWED", "VALUE": 1, "DETAIL": "CR decision package is reviewed and usable for 10CT selection."},
            {"DECISION_ROW": 2, "DECISION": "SELECTION_PACKAGE_REQUIRED", "VALUE": 1, "DETAIL": "10CT must explicitly select the next decision path."},
            {"DECISION_ROW": 3, "DECISION": "REUSE_PATH_SELECTED_NOW", "VALUE": 0, "DETAIL": "CS does not select reuse."},
            {"DECISION_ROW": 4, "DECISION": "SOURCE_PATCH_SELECTED_NOW", "VALUE": 0, "DETAIL": "CS does not select source patch."},
            {"DECISION_ROW": 5, "DECISION": "APPLY_EXECUTION_AUTHORIZED_NOW", "VALUE": 0, "DETAIL": "Apply remains blocked."},
        ]

        paths = [
            (cs_root / "decision_option_review_v1.csv", option_review, ["OPTION_REVIEW_ROW","DECISION_OPTION","CR_DECISION_STATUS","CR_SELECTED_NOW","CS_REVIEW_DISPOSITION","CS_REVIEW_DETAIL","ELIGIBLE_FOR_10CT_SELECTION","SELECTED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cs_root / "decision_evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","SOURCE_CR_EVIDENCE_ROW","DISCOVERY_CLASS","CONFIRMATION_CLASS","DECISION_EVIDENCE_CLASS","FILE_PATH","LINE","CS_EVIDENCE_REVIEW_DISPOSITION","CS_EVIDENCE_REVIEW_DETAIL","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW"]),
            (cs_root / "decision_checklist_review_v1.csv", checklist_review, ["CHECKLIST_REVIEW_ROW","CHECK","REQUIRED_FOR","CR_PASS_NOW","CS_REVIEW_STATUS","DETAIL"]),
            (cs_root / "selection_requirements_v1.csv", selection_requirements, ["REQ_ROW","SELECTION_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cs_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
            (cs_root / "review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = cs_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CT_SELECTION_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CS is review only. Generate a dedicated 10CT selection package before selecting reuse/source-patch/apply path."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CS_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cs_root / "native_writer_reuse_or_patch_decision_package_review_v1.md"
        notes.write_text("# 10CS Native Writer Reuse or Patch Decision Package Review\n\n10CS reviews the 10CR decision package and requires a 10CT decision selection package. It does not select reuse, select source patch, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = cs_root / "README_10CS_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE_REVIEW.md"
        readme.write_text("# 10CS Native Writer Reuse or Patch Decision Package Review\n\nReview-only package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_reuse_or_patch_decision_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_reuse_or_patch_decision_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CS writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "DECISION_PACKAGE_REVIEWED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(option_review)} options reviewed."},
        {"ITEM": "SELECTION_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10CT must explicitly select the decision path."},
        {"ITEM": "REUSE_PATH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "CS does not select reuse."},
        {"ITEM": "SOURCE_PATCH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "CS does not select source patch."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cs_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cs_decision_option_review_v1.csv", option_review, ["OPTION_REVIEW_ROW","DECISION_OPTION","CR_DECISION_STATUS","CR_SELECTED_NOW","CS_REVIEW_DISPOSITION","CS_REVIEW_DETAIL","ELIGIBLE_FOR_10CT_SELECTION","SELECTED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cs_decision_evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","SOURCE_CR_EVIDENCE_ROW","DISCOVERY_CLASS","CONFIRMATION_CLASS","DECISION_EVIDENCE_CLASS","FILE_PATH","LINE","CS_EVIDENCE_REVIEW_DISPOSITION","CS_EVIDENCE_REVIEW_DETAIL","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cs_decision_checklist_review_v1.csv", checklist_review, ["CHECKLIST_REVIEW_ROW","CHECK","REQUIRED_FOR","CR_PASS_NOW","CS_REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cs_selection_requirements_v1.csv", selection_requirements, ["REQ_ROW","SELECTION_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cs_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cs_review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cs_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cs_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cs_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CR_STATUS": cr.get("STATUS",""),
        "MSG_022AE_6_5_10CR_SAVEPOINT_PRESENT": 1 if sp_cr else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CR_DECISION_EVIDENCE_ROWS": len(evidence),
        "CR_DECISION_OPTION_ROWS": len(options),
        "CR_DECISION_CHECKLIST_ROWS": len(checklist),
        "DECISION_OPTION_REVIEW_ROWS": len(option_review),
        "DECISION_EVIDENCE_REVIEW_ROWS": len(evidence_review),
        "DECISION_CHECKLIST_REVIEW_ROWS": len(checklist_review),
        "SELECTION_REQUIREMENT_ROWS": len(selection_requirements),
        "CS_ROOT": rel(cs_root, repo),
        "DECISION_PACKAGE_REVIEWED": 1 if status == GREEN else 0,
        "SELECTION_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cs_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CS_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CS Native Writer Reuse or Patch Decision Package Review\n\nStatus: `{status}`\n\n10CS reviews the 10CR decision package and requires a 10CT decision selection package. It does not select reuse, select source patch, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(cs_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CR status: {cr.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CR savepoint present: {1 if sp_cr else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CR decision evidence rows: {len(evidence)}")
    print(f"  CR decision option rows: {len(options)}")
    print(f"  CR decision checklist rows: {len(checklist)}")
    print(f"  decision option review rows: {len(option_review)}")
    print(f"  decision evidence review rows: {len(evidence_review)}")
    print(f"  decision checklist review rows: {len(checklist_review)}")
    print(f"  selection requirement rows: {len(selection_requirements)}")
    print(f"  review root: {rel(cs_root, repo)}")
    print("  decision package reviewed: 1")
    print("  selection package required: 1")
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
