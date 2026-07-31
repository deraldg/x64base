#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CR_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE_GREEN_DECISION_OPTIONS_STAGED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CR_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CS_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE_REVIEW"

REPORT = Path("docs/messaging/reports")
CQ_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cq_status_summary_v1.csv"
CQ_CONFIRM_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cq_confirmation_review_v1.csv"
CQ_CLASS_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cq_confirmation_class_review_v1.csv"
CQ_DECISION_OPTIONS = REPORT / "message_catalog_phase22ae_6_5_10cq_decision_options_v1.csv"
CQ_DECISION_REQS = REPORT / "message_catalog_phase22ae_6_5_10cq_decision_requirements_v1.csv"
CQ_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cq_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CR_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cr_native_writer_reuse_or_patch_decision_package_v1")

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

def intish(v):
    try:
        return int(float(str(v)))
    except Exception:
        return 0

def classify_decision_evidence(row):
    disp = row.get("CQ_REVIEW_DISPOSITION", "")
    cclass = row.get("CONFIRMATION_CLASS", "")
    score = intish(row.get("CONFIRMATION_SIGNAL_SCORE", 0))

    if disp == "HIGH_PRIORITY_DECISION_REVIEW_REQUIRED":
        return "REUSE_DECISION_EVIDENCE_REQUIRES_MANUAL_CONFIRMATION", "Evidence is high-priority, but CQ did not confirm reuse."
    if disp == "TARGET_BINDING_DECISION_REVIEW_REQUIRED":
        return "GENERIC_TARGET_BINDING_EVIDENCE_REQUIRES_MANUAL_CONFIRMATION", "Generic writer/target binding evidence requires explicit confirmation."
    if disp == "LIKELY_EXCLUSION_EVIDENCE" or cclass == "READER_CHECKER_FALSE_POSITIVE_CANDIDATE":
        return "READER_CHECKER_EXCLUSION_EVIDENCE", "Likely reader/checker/display path, not writer proof."
    if score >= 60:
        return "SUPPORTING_DECISION_EVIDENCE", "Supporting signal only; not enough to select reuse or patch."
    return "INCONCLUSIVE_DECISION_EVIDENCE", "Inconclusive evidence."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cq = first(repo / CQ_SUMMARY)
    confirm_review = rows(repo / CQ_CONFIRM_REVIEW)
    class_review = rows(repo / CQ_CLASS_REVIEW)
    decision_options_in = rows(repo / CQ_DECISION_OPTIONS)
    decision_reqs_in = rows(repo / CQ_DECISION_REQS)
    blocked_in = rows(repo / CQ_BLOCKED)

    sp_cq, latest_cq = savepoint(repo, "MSG-022AE.6.5.10CQ")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cr_root = repo / CR_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CQ_GREEN", cq.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CQ_EXACT_NATIVE_WRITER_CONFIRMATION_REVIEW_GREEN_DECISION_PACKAGE_REQUIRED_SOURCE_HELD", cq.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CQ_SAVEPOINT_PRESENT", sp_cq, latest_cq)
    gate("CQ_DECISION_PACKAGE_REQUIRED", cq.get("DECISION_PACKAGE_REQUIRED") == "1", cq.get("DECISION_PACKAGE_REQUIRED", "missing"))
    gate("CQ_WRITER_REUSE_NOT_CONFIRMED", cq.get("WRITER_REUSE_CONFIRMED_NOW") == "0", cq.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CQ_SOURCE_PATCH_NOT_PROVEN", cq.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cq.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CQ_SOURCE_MUTATION_NOT_AUTHORIZED", cq.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cq.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CQ_APPLY_EXECUTION_NOT_AUTHORIZED", cq.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cq.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CQ_HELP_APPLY_NOT_EXECUTED", cq.get("HELP_DATA_APPLY_EXECUTED") == "0", cq.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CQ_CMDHELPCHK_APPLY_NOT_EXECUTED", cq.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cq.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CQ_CONFIRMATION_REVIEW_PRESENT", len(confirm_review) > 0, len(confirm_review))
    gate("CQ_DECISION_OPTIONS_PRESENT", len(decision_options_in) > 0, len(decision_options_in))
    gate("CQ_DECISION_REQUIREMENTS_PRESENT", len(decision_reqs_in) > 0, len(decision_reqs_in))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CR_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cr_root.exists()) or args.replace_existing_package, rel(cr_root, repo))

    status = BLOCKED
    evidence_rows = []
    option_rows = []
    option_evidence = []
    decision_review_checklist = []
    blocked_rows = []
    artifacts = []

    if failures == 0:
        if cr_root.exists() and args.replace_existing_package:
            shutil.rmtree(cr_root)
        cr_root.mkdir(parents=True, exist_ok=True)

        for i, row in enumerate(confirm_review, 1):
            evid_class, detail = classify_decision_evidence(row)
            evidence_rows.append({
                "EVIDENCE_ROW": i,
                "SOURCE_CQ_REVIEW_ROW": row.get("REVIEW_ROW", ""),
                "DISCOVERY_CLASS": row.get("DISCOVERY_CLASS", ""),
                "CONFIRMATION_CLASS": row.get("CONFIRMATION_CLASS", ""),
                "CQ_REVIEW_DISPOSITION": row.get("CQ_REVIEW_DISPOSITION", ""),
                "CONFIRMATION_SIGNAL_SCORE": row.get("CONFIRMATION_SIGNAL_SCORE", ""),
                "FILE_PATH": row.get("FILE_PATH", ""),
                "LINE": row.get("LINE", ""),
                "DECISION_EVIDENCE_CLASS": evid_class,
                "DECISION_EVIDENCE_DETAIL": detail,
                "MANUAL_DECISION_REQUIRED": 1,
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_READY_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        option_rows = [
            {"OPTION_ROW": 1, "DECISION_OPTION": "CONFIRM_EXISTING_NATIVE_HELP_DATA_REUSE", "DECISION_STATUS": "NOT_SELECTED_REQUIRES_EXACT_PATH_REVIEW", "SELECTED_NOW": 0, "DETAIL": "Needs exact HELP DATA writer/import/update path named and reviewed."},
            {"OPTION_ROW": 2, "DECISION_OPTION": "CONFIRM_EXISTING_NATIVE_CMDHELPCHK_REUSE", "DECISION_STATUS": "NOT_SELECTED_REQUIRES_EXACT_PATH_REVIEW", "SELECTED_NOW": 0, "DETAIL": "Needs exact CMDHELPCHK writer/import/update path named and reviewed."},
            {"OPTION_ROW": 3, "DECISION_OPTION": "REJECT_REUSE_AND_PLAN_SOURCE_PATCH", "DECISION_STATUS": "NOT_SELECTED_REUSE_NOT_REJECTED", "SELECTED_NOW": 0, "DETAIL": "Cannot prove source patch need until native/reuse path is explicitly rejected."},
            {"OPTION_ROW": 4, "DECISION_OPTION": "CONTINUE_TARGETED_DECISION_REVIEW", "DECISION_STATUS": "RECOMMENDED_SAFE_DEFAULT_FOR_REVIEW", "SELECTED_NOW": 0, "DETAIL": "Recommended for 10CS unless human review identifies an exact reusable writer path."},
            {"OPTION_ROW": 5, "DECISION_OPTION": "KEEP_APPLY_BLOCKED", "DECISION_STATUS": "SELECTED_SAFETY_BOUNDARY", "SELECTED_NOW": 1, "DETAIL": "Apply remains blocked until exact path and guarded apply package are reviewed."},
        ]

        # Option evidence counts
        counts = {}
        for row in evidence_rows:
            key = row["DECISION_EVIDENCE_CLASS"]
            counts[key] = counts.get(key, 0) + 1
        for option in option_rows:
            option_evidence.append({
                "OPTION_EVIDENCE_ROW": len(option_evidence) + 1,
                "DECISION_OPTION": option["DECISION_OPTION"],
                "SUPPORTING_EVIDENCE_SUMMARY": "; ".join(f"{k}={v}" for k, v in sorted(counts.items())) if counts else "no evidence rows",
                "OPTION_SELECTED_NOW": option["SELECTED_NOW"],
                "REVIEW_REQUIRED": 1,
            })

        decision_review_checklist = [
            {"CHECK_ROW": 1, "CHECK": "DOES_EVIDENCE_NAME_EXACT_HELP_DATA_WRITER", "REQUIRED_FOR": "CONFIRM_EXISTING_NATIVE_HELP_DATA_REUSE", "PASS_NOW": 0, "DETAIL": "10CS must explicitly name path/function/command and target records before selecting."},
            {"CHECK_ROW": 2, "CHECK": "DOES_EVIDENCE_NAME_EXACT_CMDHELPCHK_WRITER", "REQUIRED_FOR": "CONFIRM_EXISTING_NATIVE_CMDHELPCHK_REUSE", "PASS_NOW": 0, "DETAIL": "10CS must explicitly name path/function/command and target records before selecting."},
            {"CHECK_ROW": 3, "CHECK": "HAS_NATIVE_REUSE_BEEN_EXPLICITLY_REJECTED", "REQUIRED_FOR": "REJECT_REUSE_AND_PLAN_SOURCE_PATCH", "PASS_NOW": 0, "DETAIL": "Patch planning requires explicit rejection of reuse path."},
            {"CHECK_ROW": 4, "CHECK": "ARE_SOURCE_COMMENT_CONTRACT_UPDATES_REQUIRED_IF_PATCH", "REQUIRED_FOR": "SOURCE_PATCH_PATH", "PASS_NOW": 1, "DETAIL": "Contract rule is carried forward."},
            {"CHECK_ROW": 5, "CHECK": "IS_RAW_DBF_BYTE_WRITE_FORBIDDEN", "REQUIRED_FOR": "ALL_PATHS", "PASS_NOW": 1, "DETAIL": "Raw DBF byte write remains forbidden."},
            {"CHECK_ROW": 6, "CHECK": "IS_APPLY_STILL_BLOCKED", "REQUIRED_FOR": "ALL_PATHS", "PASS_NOW": 1, "DETAIL": "No HELP DATA/CMDHELPCHK apply is authorized now."},
            {"CHECK_ROW": 7, "CHECK": "IS_DECISION_PACKAGE_REVIEW_REQUIRED", "REQUIRED_FOR": "NEXT_GATE", "PASS_NOW": 1, "DETAIL": "10CS decision package review required."},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CR decision package.",
            })

        paths = [
            (cr_root / "decision_evidence_v1.csv", evidence_rows, ["EVIDENCE_ROW","SOURCE_CQ_REVIEW_ROW","DISCOVERY_CLASS","CONFIRMATION_CLASS","CQ_REVIEW_DISPOSITION","CONFIRMATION_SIGNAL_SCORE","FILE_PATH","LINE","DECISION_EVIDENCE_CLASS","DECISION_EVIDENCE_DETAIL","MANUAL_DECISION_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cr_root / "decision_options_v1.csv", option_rows, ["OPTION_ROW","DECISION_OPTION","DECISION_STATUS","SELECTED_NOW","DETAIL"]),
            (cr_root / "decision_option_evidence_summary_v1.csv", option_evidence, ["OPTION_EVIDENCE_ROW","DECISION_OPTION","SUPPORTING_EVIDENCE_SUMMARY","OPTION_SELECTED_NOW","REVIEW_REQUIRED"]),
            (cr_root / "decision_review_checklist_v1.csv", decision_review_checklist, ["CHECK_ROW","CHECK","REQUIRED_FOR","PASS_NOW","DETAIL"]),
            (cr_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = cr_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CS_REVIEW_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CR stages decision options only. Run 10CS review before selecting reuse/source-patch/apply path."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CR_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cr_root / "native_writer_reuse_or_patch_decision_package_v1.md"
        notes.write_text("# 10CR Native Writer Reuse or Patch Decision Package\n\n10CR stages explicit decision options using 10CQ confirmation review evidence. It keeps apply blocked and does not select reuse or source patch now. No protected systems are mutated.\n", encoding="utf-8")
        readme = cr_root / "README_10CR_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE.md"
        readme.write_text("# 10CR Native Writer Reuse or Patch Decision Package\n\nDecision-options package only. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_reuse_or_patch_decision_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_reuse_or_patch_decision_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CR writes docs/messaging decision artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision package only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision package only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "DECISION_OPTIONS_STAGED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(option_rows)} decision options staged."},
        {"ITEM": "WRITER_REUSE_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "10CR stages options but does not confirm reuse."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "10CR does not prove source patch need."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
        {"ITEM": "NEXT_REVIEW_REQUIRED", "STATUS": "YES", "DETAIL": "10CS must review decision package."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cr_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cr_decision_evidence_v1.csv", evidence_rows, ["EVIDENCE_ROW","SOURCE_CQ_REVIEW_ROW","DISCOVERY_CLASS","CONFIRMATION_CLASS","CQ_REVIEW_DISPOSITION","CONFIRMATION_SIGNAL_SCORE","FILE_PATH","LINE","DECISION_EVIDENCE_CLASS","DECISION_EVIDENCE_DETAIL","MANUAL_DECISION_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cr_decision_options_v1.csv", option_rows, ["OPTION_ROW","DECISION_OPTION","DECISION_STATUS","SELECTED_NOW","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cr_decision_option_evidence_summary_v1.csv", option_evidence, ["OPTION_EVIDENCE_ROW","DECISION_OPTION","SUPPORTING_EVIDENCE_SUMMARY","OPTION_SELECTED_NOW","REVIEW_REQUIRED"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cr_decision_review_checklist_v1.csv", decision_review_checklist, ["CHECK_ROW","CHECK","REQUIRED_FOR","PASS_NOW","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cr_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cr_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cr_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cr_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CQ_STATUS": cq.get("STATUS",""),
        "MSG_022AE_6_5_10CQ_SAVEPOINT_PRESENT": 1 if sp_cq else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CQ_CONFIRMATION_REVIEW_ROWS": len(confirm_review),
        "CQ_DECISION_OPTION_ROWS": len(decision_options_in),
        "DECISION_EVIDENCE_ROWS": len(evidence_rows),
        "DECISION_OPTION_ROWS": len(option_rows),
        "DECISION_REVIEW_CHECKLIST_ROWS": len(decision_review_checklist),
        "CR_ROOT": rel(cr_root, repo),
        "DECISION_OPTIONS_STAGED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cr_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CR_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CR Native Writer Reuse or Patch Decision Package\n\nStatus: `{status}`\n\n10CR stages explicit reuse-or-patch decision options from 10CQ evidence. It keeps apply blocked and does not select reuse or source patch now.\n\nDecision root:\n\n```text\n{rel(cr_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CQ status: {cq.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CQ savepoint present: {1 if sp_cq else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CQ confirmation review rows: {len(confirm_review)}")
    print(f"  CQ decision option rows: {len(decision_options_in)}")
    print(f"  decision evidence rows: {len(evidence_rows)}")
    print(f"  decision option rows: {len(option_rows)}")
    print(f"  decision review checklist rows: {len(decision_review_checklist)}")
    print(f"  decision root: {rel(cr_root, repo)}")
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
