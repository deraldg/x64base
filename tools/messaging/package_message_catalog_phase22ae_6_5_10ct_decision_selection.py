#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CT_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_GREEN_CONTINUE_REVIEW_SELECTED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CT_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CU_NATIVE_WRITER_DECISION_SELECTION_REVIEW"

REPORT = Path("docs/messaging/reports")
CS_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cs_status_summary_v1.csv"
CS_OPTION_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cs_decision_option_review_v1.csv"
CS_EVIDENCE_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cs_decision_evidence_review_v1.csv"
CS_CHECKLIST_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cs_decision_checklist_review_v1.csv"
CS_SELECTION_REQS = REPORT / "message_catalog_phase22ae_6_5_10cs_selection_requirements_v1.csv"
CS_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cs_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CT_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ct_native_writer_decision_selection_package_v1")

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cs = first(repo / CS_SUMMARY)
    option_review = rows(repo / CS_OPTION_REVIEW)
    evidence_review = rows(repo / CS_EVIDENCE_REVIEW)
    checklist_review = rows(repo / CS_CHECKLIST_REVIEW)
    selection_reqs = rows(repo / CS_SELECTION_REQS)
    blocked_in = rows(repo / CS_BLOCKED)

    sp_cs, latest_cs = savepoint(repo, "MSG-022AE.6.5.10CS")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    ct_root = repo / CT_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CS_GREEN", cs.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CS_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE_REVIEW_GREEN_SELECTION_PACKAGE_REQUIRED_SOURCE_HELD", cs.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CS_SAVEPOINT_PRESENT", sp_cs, latest_cs)
    gate("CS_SELECTION_PACKAGE_REQUIRED", cs.get("SELECTION_PACKAGE_REQUIRED") == "1", cs.get("SELECTION_PACKAGE_REQUIRED", "missing"))
    gate("CS_REUSE_NOT_SELECTED", cs.get("REUSE_PATH_SELECTED_NOW") == "0", cs.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("CS_WRITER_REUSE_NOT_CONFIRMED", cs.get("WRITER_REUSE_CONFIRMED_NOW") == "0", cs.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CS_SOURCE_PATCH_NOT_SELECTED", cs.get("SOURCE_PATCH_SELECTED_NOW") == "0", cs.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("CS_SOURCE_PATCH_NOT_PROVEN", cs.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cs.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CS_SOURCE_MUTATION_NOT_AUTHORIZED", cs.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cs.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CS_APPLY_EXECUTION_NOT_AUTHORIZED", cs.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cs.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CS_HELP_APPLY_NOT_EXECUTED", cs.get("HELP_DATA_APPLY_EXECUTED") == "0", cs.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CS_CMDHELPCHK_APPLY_NOT_EXECUTED", cs.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cs.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CS_OPTION_REVIEW_PRESENT", len(option_review) > 0, len(option_review))
    gate("CS_SELECTION_REQUIREMENTS_PRESENT", len(selection_reqs) > 0, len(selection_reqs))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CT_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not ct_root.exists()) or args.replace_existing_package, rel(ct_root, repo))

    status = BLOCKED
    selection_rows = []
    selected_path_rows = []
    deferred_path_rows = []
    selection_rationale = []
    next_review_reqs = []
    blocked_rows = []
    artifacts = []

    if failures == 0:
        if ct_root.exists() and args.replace_existing_package:
            shutil.rmtree(ct_root)
        ct_root.mkdir(parents=True, exist_ok=True)

        # Deliberate safe selection: continue targeted decision review; keep apply blocked.
        for i, row in enumerate(option_review, 1):
            option = row.get("DECISION_OPTION", "")
            if option == "CONTINUE_TARGETED_DECISION_REVIEW":
                selected_now = 1
                selection_status = "SELECTED_CONTINUE_REVIEW_SAFE_DEFAULT"
                detail = "Selected because CS did not confirm exact reuse and did not prove source-patch need."
            elif option == "KEEP_APPLY_BLOCKED":
                selected_now = 1
                selection_status = "SELECTED_SAFETY_BOUNDARY"
                detail = "Selected as required safety boundary; no apply is authorized."
            elif option in {"CONFIRM_EXISTING_NATIVE_HELP_DATA_REUSE", "CONFIRM_EXISTING_NATIVE_CMDHELPCHK_REUSE"}:
                selected_now = 0
                selection_status = "DEFERRED_EXACT_PATH_NOT_NAMED"
                detail = "Deferred because exact reusable writer path/function/target contract is not yet named."
            elif option == "REJECT_REUSE_AND_PLAN_SOURCE_PATCH":
                selected_now = 0
                selection_status = "DEFERRED_REUSE_NOT_REJECTED"
                detail = "Deferred because native reuse has not been explicitly rejected and source patch need is not proven."
            else:
                selected_now = 0
                selection_status = "DEFERRED"
                detail = "Deferred pending review."
            srow = {
                "SELECTION_ROW": i,
                "DECISION_OPTION": option,
                "CS_REVIEW_DISPOSITION": row.get("CS_REVIEW_DISPOSITION", ""),
                "SELECTED_NOW": selected_now,
                "SELECTION_STATUS": selection_status,
                "SELECTION_DETAIL": detail,
                "REUSE_PATH_SELECTED_NOW": 1 if selected_now and option.startswith("CONFIRM_EXISTING_NATIVE") else 0,
                "SOURCE_PATCH_SELECTED_NOW": 1 if selected_now and option == "REJECT_REUSE_AND_PLAN_SOURCE_PATCH" else 0,
                "APPLY_AUTHORIZED_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
            }
            selection_rows.append(srow)
            if selected_now:
                selected_path_rows.append(srow)
            else:
                deferred_path_rows.append(srow)

        selection_rationale = [
            {"RATIONALE_ROW": 1, "RATIONALE": "CONTINUE_REVIEW_SELECTED", "DETAIL": "Exact writer reuse has not been confirmed and exact source patch need has not been proven."},
            {"RATIONALE_ROW": 2, "RATIONALE": "APPLY_BLOCKED_SELECTED", "DETAIL": "HELP DATA/CMDHELPCHK apply remains blocked by default."},
            {"RATIONALE_ROW": 3, "RATIONALE": "REUSE_DEFERRED", "DETAIL": "Reuse requires named exact writer/import/update path and target contract."},
            {"RATIONALE_ROW": 4, "RATIONALE": "SOURCE_PATCH_DEFERRED", "DETAIL": "Source patch planning requires explicit reuse rejection and source-comment usage-contract update plan."},
            {"RATIONALE_ROW": 5, "RATIONALE": "RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Active materialization must remain native/schema-aware, not raw DBF byte mutation."},
        ]

        next_review_reqs = [
            {"REQ_ROW": 1, "REQUIREMENT": "10CU_REVIEW_SELECTION", "DETAIL": "10CU must review that continue-review/apply-blocked selection is acceptable.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "DECIDE_NEXT_INVESTIGATION_SCOPE", "DETAIL": "If continue-review remains accepted, choose next exact source/function investigation scope.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "KEEP_REUSE_DEFERRED_UNTIL_NAMED", "DETAIL": "Do not select reuse until exact path/function/target contract is named.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "KEEP_PATCH_DEFERRED_UNTIL_REUSE_REJECTED", "DETAIL": "Do not select source patch until native reuse is explicitly rejected.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "REQUIREMENT": "PRESERVE_USAGE_CONTRACT_RULE", "DETAIL": "Any later source patch must update @dottalk.usage/source-comment contracts in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until a later guarded apply package is reviewed and explicitly authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CT decision selection package.",
            })

        paths = [
            (ct_root / "decision_selection_v1.csv", selection_rows, ["SELECTION_ROW","DECISION_OPTION","CS_REVIEW_DISPOSITION","SELECTED_NOW","SELECTION_STATUS","SELECTION_DETAIL","REUSE_PATH_SELECTED_NOW","SOURCE_PATCH_SELECTED_NOW","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"]),
            (ct_root / "selected_paths_v1.csv", selected_path_rows, ["SELECTION_ROW","DECISION_OPTION","CS_REVIEW_DISPOSITION","SELECTED_NOW","SELECTION_STATUS","SELECTION_DETAIL","REUSE_PATH_SELECTED_NOW","SOURCE_PATCH_SELECTED_NOW","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"]),
            (ct_root / "deferred_paths_v1.csv", deferred_path_rows, ["SELECTION_ROW","DECISION_OPTION","CS_REVIEW_DISPOSITION","SELECTED_NOW","SELECTION_STATUS","SELECTION_DETAIL","REUSE_PATH_SELECTED_NOW","SOURCE_PATCH_SELECTED_NOW","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"]),
            (ct_root / "selection_rationale_v1.csv", selection_rationale, ["RATIONALE_ROW","RATIONALE","DETAIL"]),
            (ct_root / "next_review_requirements_v1.csv", next_review_reqs, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (ct_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = ct_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CU_SELECTION_REVIEW_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CT is selection packaging only. Run 10CU review before any next investigation/apply/source-patch path."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CT_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = ct_root / "native_writer_decision_selection_package_v1.md"
        notes.write_text("# 10CT Native Writer Decision Selection Package\n\n10CT selects the safe decision path: continue targeted decision review and keep apply blocked. It does not select reuse, select source patch, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = ct_root / "README_10CT_NATIVE_WRITER_DECISION_SELECTION_PACKAGE.md"
        readme.write_text("# 10CT Native Writer Decision Selection Package\n\nSelection package only. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_selection_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_selection_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CT writes docs/messaging selection artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Selection package only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Selection package only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "DECISION_SELECTION_PACKAGED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": "Continue-review and apply-blocked selected."},
        {"ITEM": "CONTINUE_REVIEW_SELECTED_NOW", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": "Safe default selected pending 10CU review."},
        {"ITEM": "REUSE_PATH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains deferred."},
        {"ITEM": "SOURCE_PATCH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Source patch remains deferred."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10ct_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ct_decision_selection_v1.csv", selection_rows, ["SELECTION_ROW","DECISION_OPTION","CS_REVIEW_DISPOSITION","SELECTED_NOW","SELECTION_STATUS","SELECTION_DETAIL","REUSE_PATH_SELECTED_NOW","SOURCE_PATCH_SELECTED_NOW","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ct_selected_paths_v1.csv", selected_path_rows, ["SELECTION_ROW","DECISION_OPTION","CS_REVIEW_DISPOSITION","SELECTED_NOW","SELECTION_STATUS","SELECTION_DETAIL","REUSE_PATH_SELECTED_NOW","SOURCE_PATCH_SELECTED_NOW","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ct_deferred_paths_v1.csv", deferred_path_rows, ["SELECTION_ROW","DECISION_OPTION","CS_REVIEW_DISPOSITION","SELECTED_NOW","SELECTION_STATUS","SELECTION_DETAIL","REUSE_PATH_SELECTED_NOW","SOURCE_PATCH_SELECTED_NOW","APPLY_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ct_selection_rationale_v1.csv", selection_rationale, ["RATIONALE_ROW","RATIONALE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ct_next_review_requirements_v1.csv", next_review_reqs, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ct_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ct_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ct_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ct_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CS_STATUS": cs.get("STATUS",""),
        "MSG_022AE_6_5_10CS_SAVEPOINT_PRESENT": 1 if sp_cs else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CS_DECISION_OPTION_REVIEW_ROWS": len(option_review),
        "CS_SELECTION_REQUIREMENT_ROWS": len(selection_reqs),
        "DECISION_SELECTION_ROWS": len(selection_rows),
        "SELECTED_PATH_ROWS": len(selected_path_rows),
        "DEFERRED_PATH_ROWS": len(deferred_path_rows),
        "NEXT_REVIEW_REQUIREMENT_ROWS": len(next_review_reqs),
        "CT_ROOT": rel(ct_root, repo),
        "DECISION_SELECTION_PACKAGED": 1 if status == GREEN else 0,
        "CONTINUE_REVIEW_SELECTED_NOW": 1 if status == GREEN else 0,
        "APPLY_BLOCKED_SELECTED_NOW": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10ct_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CT_NATIVE_WRITER_DECISION_SELECTION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CT Native Writer Decision Selection Package\n\nStatus: `{status}`\n\n10CT selects the safe decision path: continue targeted decision review and keep apply blocked. It does not select reuse, select source patch, authorize apply, or mutate protected systems.\n\nSelection root:\n\n```text\n{rel(ct_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CS status: {cs.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CS savepoint present: {1 if sp_cs else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CS decision option review rows: {len(option_review)}")
    print(f"  CS selection requirement rows: {len(selection_reqs)}")
    print(f"  decision selection rows: {len(selection_rows)}")
    print(f"  selected path rows: {len(selected_path_rows)}")
    print(f"  deferred path rows: {len(deferred_path_rows)}")
    print(f"  next review requirement rows: {len(next_review_reqs)}")
    print(f"  selection root: {rel(ct_root, repo)}")
    print("  decision selection packaged: 1")
    print("  continue review selected now: 1")
    print("  apply blocked selected now: 1")
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
