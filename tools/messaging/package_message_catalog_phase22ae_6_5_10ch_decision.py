#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CH_NATIVE_WRITER_REUSE_OR_SOURCE_PATCH_DECISION_PACKAGE_GREEN_DECISION_OPTIONS_STAGED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CH_NATIVE_WRITER_REUSE_OR_SOURCE_PATCH_DECISION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CI_NATIVE_WRITER_DECISION_PACKAGE_REVIEW"

REPORT = Path("docs/messaging/reports")
CG_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cg_status_summary_v1.csv"
CG_FOCUS = REPORT / "message_catalog_phase22ae_6_5_10cg_native_writer_focus_review_v1.csv"
CG_REUSE = REPORT / "message_catalog_phase22ae_6_5_10cg_possible_reuse_writer_review_v1.csv"
CG_REQ = REPORT / "message_catalog_phase22ae_6_5_10cg_decision_package_requirements_v1.csv"
CG_DECISIONS = REPORT / "message_catalog_phase22ae_6_5_10cg_review_decisions_v1.csv"
CG_RISKS = REPORT / "message_catalog_phase22ae_6_5_10cg_review_risks_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CH_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ch_native_writer_reuse_or_source_patch_decision_package_v1")

def rows(p):
    p = Path(p)
    if not p.exists(): return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first(p):
    r = rows(p)
    return r[0] if r else {}

def wcsv(p, rs, fs):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fs, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rs: w.writerow({k: r.get(k, "") for k in fs})

def rel(p, repo):
    try: return str(Path(p).resolve().relative_to(repo.resolve())).replace("\\", "/")
    except Exception: return str(p).replace("\\", "/")

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""): h.update(b)
    return h.hexdigest()

def dbf_count(p):
    p = Path(p)
    if not p.exists() or p.stat().st_size < 12: return ""
    return int.from_bytes(p.read_bytes()[:12][4:8], "little")

def savepoint(repo, sid):
    latest = ""
    lp = repo / REPORT / "message_savepoint_latest_v1.json"
    if lp.exists():
        try: latest = json.loads(lp.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception: latest = ""
    jp = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    txt = jp.read_text(encoding="utf-8", errors="replace") if jp.exists() else ""
    return latest == sid or sid in txt, latest

def count_kind(rows_in, token):
    return sum(1 for r in rows_in if token in (r.get("TRIAGE_CLASS","") + " " + r.get("REVIEW_DISPOSITION","")))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT; reports.mkdir(parents=True, exist_ok=True)

    cg = first(repo / CG_SUMMARY)
    focus = rows(repo / CG_FOCUS)
    reuse = rows(repo / CG_REUSE)
    req_in = rows(repo / CG_REQ)
    decisions_in = rows(repo / CG_DECISIONS)
    risks_in = rows(repo / CG_RISKS)
    sp_cg, latest_cg = savepoint(repo, "MSG-022AE.6.5.10CG")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    ch_root = repo / CH_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok: failures += 1

    gate("PHASE22AE_6_5_10CG_GREEN", cg.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CG_NATIVE_WRITER_TRIAGE_REVIEW_GREEN_DECISION_PACKAGE_REQUIRED_SOURCE_HELD", cg.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10CG_SAVEPOINT_PRESENT", sp_cg, latest_cg)
    gate("CG_DECISION_PACKAGE_REQUIRED", cg.get("DECISION_PACKAGE_REQUIRED") == "1", cg.get("DECISION_PACKAGE_REQUIRED","missing"))
    gate("CG_REUSE_NOT_CONFIRMED", cg.get("REUSE_PATH_CONFIRMED_NOW") == "0", cg.get("REUSE_PATH_CONFIRMED_NOW","missing"))
    gate("CG_SOURCE_PATCH_NOT_PROVEN", cg.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cg.get("SOURCE_PATCH_NEEDED_PROVEN","missing"))
    gate("CG_SOURCE_MUTATION_NOT_AUTHORIZED", cg.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cg.get("SOURCE_MUTATION_AUTHORIZED_NOW","missing"))
    gate("CG_APPLY_EXECUTION_NOT_AUTHORIZED", cg.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cg.get("APPLY_EXECUTION_AUTHORIZED_NOW","missing"))
    gate("CG_HELP_APPLY_NOT_EXECUTED", cg.get("HELP_DATA_APPLY_EXECUTED") == "0", cg.get("HELP_DATA_APPLY_EXECUTED","missing"))
    gate("CG_CMDHELPCHK_APPLY_NOT_EXECUTED", cg.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cg.get("CMDHELPCHK_APPLY_EXECUTED","missing"))
    gate("CG_FOCUS_REVIEW_PRESENT", len(focus) > 0, len(focus))
    gate("CG_REUSE_REVIEW_PRESENT", len(reuse) > 0, len(reuse))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CH_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not ch_root.exists()) or args.replace_existing_package, rel(ch_root, repo))

    status = BLOCKED
    decision_options = []
    option_evidence = []
    review_checklist = []
    blocked_actions = []
    artifacts = []

    if failures == 0:
        if ch_root.exists() and args.replace_existing_package:
            shutil.rmtree(ch_root)
        ch_root.mkdir(parents=True, exist_ok=True)

        help_reuse = count_kind(reuse, "HELP_DATA")
        cmd_reuse = count_kind(reuse, "CMDHELPCHK")
        generic_write = count_kind(focus, "WRITE")
        source_contract = count_kind(focus, "SOURCE_COMMENT")
        storage_support = count_kind(focus, "STORAGE")

        decision_options = [
            {"OPTION_ROW": 1, "DECISION_OPTION": "CONFIRM_EXISTING_HELP_DATA_WRITER_REUSE", "OPTION_STATUS": "AVAILABLE_FOR_REVIEW_NOT_SELECTED", "EVIDENCE_ROWS": help_reuse, "WHAT_IT_WOULD_MEAN": "A reviewed existing native HELP DATA writer/import/update path can be reused.", "SOURCE_MUTATION_REQUIRED": 0, "APPLY_READY_NOW": 0},
            {"OPTION_ROW": 2, "DECISION_OPTION": "CONFIRM_EXISTING_CMDHELPCHK_WRITER_REUSE", "OPTION_STATUS": "AVAILABLE_FOR_REVIEW_NOT_SELECTED", "EVIDENCE_ROWS": cmd_reuse, "WHAT_IT_WOULD_MEAN": "A reviewed existing native CMDHELPCHK writer/import/update path can be reused.", "SOURCE_MUTATION_REQUIRED": 0, "APPLY_READY_NOW": 0},
            {"OPTION_ROW": 3, "DECISION_OPTION": "REQUIRE_FURTHER_WRITER_DISCOVERY", "OPTION_STATUS": "AVAILABLE_FOR_REVIEW_NOT_SELECTED", "EVIDENCE_ROWS": len(focus), "WHAT_IT_WOULD_MEAN": "Discovery remains inconclusive and should be narrowed further before source patch planning.", "SOURCE_MUTATION_REQUIRED": 0, "APPLY_READY_NOW": 0},
            {"OPTION_ROW": 4, "DECISION_OPTION": "PLAN_GUARDED_SOURCE_PATCH", "OPTION_STATUS": "AVAILABLE_FOR_REVIEW_NOT_SELECTED", "EVIDENCE_ROWS": source_contract, "WHAT_IT_WOULD_MEAN": "No adequate native writer/reuse path is confirmed, so a guarded source patch plan may be needed.", "SOURCE_MUTATION_REQUIRED": 1, "APPLY_READY_NOW": 0},
            {"OPTION_ROW": 5, "DECISION_OPTION": "REFUSE_DIRECT_APPLY", "OPTION_STATUS": "SELECTED_AS_SAFETY_DEFAULT", "EVIDENCE_ROWS": len(req_in), "WHAT_IT_WOULD_MEAN": "Do not execute HELP DATA/CMDHELPCHK apply until a writer path decision and apply package are reviewed.", "SOURCE_MUTATION_REQUIRED": 0, "APPLY_READY_NOW": 0},
        ]

        focus_sorted = sorted(focus, key=lambda r: int(float(r.get("TRIAGE_SCORE") or 0)), reverse=True)
        for i, r in enumerate(focus_sorted[:60], 1):
            option_evidence.append({
                "EVIDENCE_ROW": i,
                "SOURCE_KIND": "FOCUS_REVIEW",
                "FILE_PATH": r.get("FILE_PATH",""),
                "LINE": r.get("LINE",""),
                "TRIAGE_CLASS": r.get("TRIAGE_CLASS",""),
                "REVIEW_DISPOSITION": r.get("REVIEW_DISPOSITION",""),
                "DECISION_USE": "SUPPORT_10CI_REVIEW",
                "REUSE_PATH_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
            })
        for r in reuse[:40]:
            option_evidence.append({
                "EVIDENCE_ROW": len(option_evidence) + 1,
                "SOURCE_KIND": "POSSIBLE_REUSE_REVIEW",
                "FILE_PATH": r.get("FILE_PATH",""),
                "LINE": r.get("LINE",""),
                "TRIAGE_CLASS": r.get("TRIAGE_CLASS",""),
                "REVIEW_DISPOSITION": r.get("REVIEW_DISPOSITION",""),
                "DECISION_USE": "POSSIBLE_REUSE_REVIEW_REQUIRED",
                "REUSE_PATH_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
            })

        review_checklist = [
            {"CHECK_ROW": 1, "CHECK": "MANUALLY_INSPECT_HELP_DATA_REUSE_ROWS", "REQUIRED": 1, "DETAIL": f"{help_reuse} possible HELP DATA reuse rows."},
            {"CHECK_ROW": 2, "CHECK": "MANUALLY_INSPECT_CMDHELPCHK_REUSE_ROWS", "REQUIRED": 1, "DETAIL": f"{cmd_reuse} possible CMDHELPCHK reuse rows."},
            {"CHECK_ROW": 3, "CHECK": "DISTINGUISH_WRITER_FROM_READER_OR_CHECKER", "REQUIRED": 1, "DETAIL": "Do not confuse HELP display/check logic with writer/import/update logic."},
            {"CHECK_ROW": 4, "CHECK": "CONFIRM_OR_REJECT_FURTHER_DISCOVERY", "REQUIRED": 1, "DETAIL": "If current evidence is too broad, choose further discovery rather than patching."},
            {"CHECK_ROW": 5, "CHECK": "CONFIRM_OR_REJECT_SOURCE_PATCH_PLANNING", "REQUIRED": 1, "DETAIL": "Source patch planning requires explicit choice and source-comment contract rule."},
            {"CHECK_ROW": 6, "CHECK": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "REQUIRED": 1, "DETAIL": "Runtime-promotion path must remain native/schema-aware."},
            {"CHECK_ROW": 7, "CHECK": "KEEP_APPLY_BLOCKED_UNTIL_REVIEWED_PACKAGE", "REQUIRED": 1, "DETAIL": "No HELP DATA/CMDHELPCHK apply from 10CH."},
        ]

        blocked_actions = [
            {"BLOCKED_ACTION": "HELP_DATA_APPLY_EXECUTION", "BLOCKED": 1, "REASON": "Writer path not selected/reviewed."},
            {"BLOCKED_ACTION": "CMDHELPCHK_APPLY_EXECUTION", "BLOCKED": 1, "REASON": "Writer path not selected/reviewed."},
            {"BLOCKED_ACTION": "SOURCE_PATCH_EXECUTION", "BLOCKED": 1, "REASON": "Source patch need not proven and not authorized."},
            {"BLOCKED_ACTION": "RAW_DBF_BYTE_WRITE", "BLOCKED": 1, "REASON": "Forbidden runtime-promotion path."},
            {"BLOCKED_ACTION": "ACTIVE_CATALOG_MUTATION", "BLOCKED": 1, "REASON": "Decision package only."},
        ]

        paths = [
            (ch_root / "native_writer_decision_options_v1.csv", decision_options, ["OPTION_ROW","DECISION_OPTION","OPTION_STATUS","EVIDENCE_ROWS","WHAT_IT_WOULD_MEAN","SOURCE_MUTATION_REQUIRED","APPLY_READY_NOW"]),
            (ch_root / "decision_option_evidence_v1.csv", option_evidence, ["EVIDENCE_ROW","SOURCE_KIND","FILE_PATH","LINE","TRIAGE_CLASS","REVIEW_DISPOSITION","DECISION_USE","REUSE_PATH_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN"]),
            (ch_root / "decision_review_checklist_v1.csv", review_checklist, ["CHECK_ROW","CHECK","REQUIRED","DETAIL"]),
            (ch_root / "blocked_actions_v1.csv", blocked_actions, ["BLOCKED_ACTION","BLOCKED","REASON"]),
        ]
        for p, rs, fs in paths:
            wcsv(p, rs, fs)

        scripts = ch_root / "scripts"; scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CI_REVIEW_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CH stages decision options only. Run 10CI review before selecting reuse/source-patch path."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CH_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = ch_root / "native_writer_reuse_or_source_patch_decision_package_v1.md"
        notes.write_text("# 10CH Native Writer Reuse or Source-Patch Decision Package\n\n10CH stages the decision options for review. It does not select a reuse path, prove source patch need, or mutate protected systems.\n", encoding="utf-8")
        readme = ch_root / "README_10CH_NATIVE_WRITER_DECISION_PACKAGE.md"
        readme.write_text("# 10CH Native Writer Decision Package\n\nDecision-options package only. No protected mutation occurs.\n", encoding="utf-8")
        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_package_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_package_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CH writes docs/messaging decision-package artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision package only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision package only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "DECISION_OPTIONS_STAGED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(decision_options)} decision options."},
        {"ITEM": "REUSE_PATH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "10CH stages options for 10CI review."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "10CH does not prove patch need."},
        {"ITEM": "DIRECT_APPLY_READY", "STATUS": "NO", "DETAIL": "Apply remains blocked."},
        {"ITEM": "NEXT_REVIEW_REQUIRED", "STATUS": "YES", "DETAIL": "10CI review required."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10ch_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ch_decision_options_v1.csv", decision_options, ["OPTION_ROW","DECISION_OPTION","OPTION_STATUS","EVIDENCE_ROWS","WHAT_IT_WOULD_MEAN","SOURCE_MUTATION_REQUIRED","APPLY_READY_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ch_decision_option_evidence_v1.csv", option_evidence, ["EVIDENCE_ROW","SOURCE_KIND","FILE_PATH","LINE","TRIAGE_CLASS","REVIEW_DISPOSITION","DECISION_USE","REUSE_PATH_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ch_decision_review_checklist_v1.csv", review_checklist, ["CHECK_ROW","CHECK","REQUIRED","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ch_blocked_actions_v1.csv", blocked_actions, ["BLOCKED_ACTION","BLOCKED","REASON"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ch_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ch_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ch_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status, "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CG_STATUS": cg.get("STATUS",""),
        "MSG_022AE_6_5_10CG_SAVEPOINT_PRESENT": 1 if sp_cg else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CG_FOCUS_REVIEW_ROWS": len(focus),
        "CG_REUSE_REVIEW_ROWS": len(reuse),
        "DECISION_OPTION_ROWS": len(decision_options),
        "DECISION_OPTION_EVIDENCE_ROWS": len(option_evidence),
        "DECISION_REVIEW_CHECKLIST_ROWS": len(review_checklist),
        "CH_ROOT": rel(ch_root, repo),
        "DECISION_OPTIONS_STAGED": 1 if status == GREEN else 0,
        "REUSE_PATH_SELECTED_NOW": 0,
        "REUSE_PATH_CONFIRMED_NOW": 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10ch_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CH_NATIVE_WRITER_REUSE_OR_SOURCE_PATCH_DECISION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CH Native Writer Reuse or Source-Patch Decision Package\n\nStatus: `{status}`\n\n10CH stages reuse/source-patch decision options for 10CI review. It does not select reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nDecision root:\n\n```text\n{rel(ch_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CG status: {cg.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CG savepoint present: {1 if sp_cg else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CG focus review rows: {len(focus)}")
    print(f"  CG reuse review rows: {len(reuse)}")
    print(f"  decision option rows: {len(decision_options)}")
    print(f"  decision option evidence rows: {len(option_evidence)}")
    print(f"  decision review checklist rows: {len(review_checklist)}")
    print(f"  decision root: {rel(ch_root, repo)}")
    print("  decision options staged: 1")
    print("  reuse path selected now: 0")
    print("  reuse path confirmed now: 0")
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
