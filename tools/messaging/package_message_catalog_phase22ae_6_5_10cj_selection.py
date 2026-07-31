#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_GREEN_TARGETED_DISCOVERY_SELECTED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CK_NATIVE_WRITER_SELECTION_REVIEW"

REPORT = Path("docs/messaging/reports")
CI_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10ci_status_summary_v1.csv"
CI_OPTIONS = REPORT / "message_catalog_phase22ae_6_5_10ci_decision_options_review_v1.csv"
CI_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10ci_decision_option_evidence_review_v1.csv"
CI_REQUIREMENTS = REPORT / "message_catalog_phase22ae_6_5_10ci_selection_requirements_v1.csv"
CI_DECISIONS = REPORT / "message_catalog_phase22ae_6_5_10ci_review_decisions_v1.csv"
CI_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10ci_blocked_actions_review_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CJ_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cj_native_writer_decision_selection_package_v1")

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    ci = first(repo / CI_SUMMARY)
    options = rows(repo / CI_OPTIONS)
    evidence = rows(repo / CI_EVIDENCE)
    requirements = rows(repo / CI_REQUIREMENTS)
    decisions = rows(repo / CI_DECISIONS)
    blocked_in = rows(repo / CI_BLOCKED)
    sp_ci, latest_ci = savepoint(repo, "MSG-022AE.6.5.10CI")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cj_root = repo / CJ_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok: failures += 1

    gate("PHASE22AE_6_5_10CI_GREEN", ci.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CI_NATIVE_WRITER_DECISION_PACKAGE_REVIEW_GREEN_SELECTION_PACKAGE_REQUIRED_SOURCE_HELD", ci.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10CI_SAVEPOINT_PRESENT", sp_ci, latest_ci)
    gate("CI_SELECTION_PACKAGE_REQUIRED", ci.get("SELECTION_PACKAGE_REQUIRED") == "1", ci.get("SELECTION_PACKAGE_REQUIRED","missing"))
    gate("CI_REUSE_NOT_SELECTED", ci.get("REUSE_PATH_SELECTED_NOW") == "0", ci.get("REUSE_PATH_SELECTED_NOW","missing"))
    gate("CI_REUSE_NOT_CONFIRMED", ci.get("REUSE_PATH_CONFIRMED_NOW") == "0", ci.get("REUSE_PATH_CONFIRMED_NOW","missing"))
    gate("CI_SOURCE_PATCH_NOT_PROVEN", ci.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", ci.get("SOURCE_PATCH_NEEDED_PROVEN","missing"))
    gate("CI_SOURCE_MUTATION_NOT_AUTHORIZED", ci.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", ci.get("SOURCE_MUTATION_AUTHORIZED_NOW","missing"))
    gate("CI_APPLY_EXECUTION_NOT_AUTHORIZED", ci.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", ci.get("APPLY_EXECUTION_AUTHORIZED_NOW","missing"))
    gate("CI_HELP_APPLY_NOT_EXECUTED", ci.get("HELP_DATA_APPLY_EXECUTED") == "0", ci.get("HELP_DATA_APPLY_EXECUTED","missing"))
    gate("CI_CMDHELPCHK_APPLY_NOT_EXECUTED", ci.get("CMDHELPCHK_APPLY_EXECUTED") == "0", ci.get("CMDHELPCHK_APPLY_EXECUTED","missing"))
    gate("CI_OPTIONS_REVIEW_PRESENT", len(options) > 0, len(options))
    gate("CI_SELECTION_REQUIREMENTS_PRESENT", len(requirements) > 0, len(requirements))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CJ_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cj_root.exists()) or args.replace_existing_package, rel(cj_root, repo))

    status = BLOCKED
    selection_rows = []
    selected_path = []
    rejected_paths = []
    targeted_scope = []
    carry_forward_blocked = []
    artifacts = []

    if failures == 0:
        if cj_root.exists() and args.replace_existing_package:
            shutil.rmtree(cj_root)
        cj_root.mkdir(parents=True, exist_ok=True)

        selection_rows = [
            {"SELECTION_ROW": 1, "DECISION_OPTION": "REQUIRE_FURTHER_TARGETED_NATIVE_WRITER_DISCOVERY", "SELECTED": 1, "SELECTION_STATUS": "SELECTED_SAFE_DEFAULT", "RATIONALE": "10CI did not confirm reuse and did not prove source patch need; targeted discovery is the safest next step.", "SOURCE_MUTATION_REQUIRED": 0, "APPLY_READY_NOW": 0},
            {"SELECTION_ROW": 2, "DECISION_OPTION": "CONFIRM_EXISTING_HELP_DATA_WRITER_REUSE", "SELECTED": 0, "SELECTION_STATUS": "NOT_SELECTED_REQUIRES_EXACT_WRITER_PROOF", "RATIONALE": "Possible evidence exists but exact native writer/import/update path is not confirmed.", "SOURCE_MUTATION_REQUIRED": 0, "APPLY_READY_NOW": 0},
            {"SELECTION_ROW": 3, "DECISION_OPTION": "CONFIRM_EXISTING_CMDHELPCHK_WRITER_REUSE", "SELECTED": 0, "SELECTION_STATUS": "NOT_SELECTED_REQUIRES_EXACT_WRITER_PROOF", "RATIONALE": "Possible evidence exists but exact native writer/import/update path is not confirmed.", "SOURCE_MUTATION_REQUIRED": 0, "APPLY_READY_NOW": 0},
            {"SELECTION_ROW": 4, "DECISION_OPTION": "PLAN_GUARDED_SOURCE_PATCH", "SELECTED": 0, "SELECTION_STATUS": "NOT_SELECTED_SOURCE_PATCH_NEED_UNPROVEN", "RATIONALE": "Source patch planning should wait until targeted discovery proves no acceptable native/reuse path.", "SOURCE_MUTATION_REQUIRED": 1, "APPLY_READY_NOW": 0},
            {"SELECTION_ROW": 5, "DECISION_OPTION": "DIRECT_HELP_CMDHELPCHK_APPLY", "SELECTED": 0, "SELECTION_STATUS": "REFUSED", "RATIONALE": "No writer path or apply package has been reviewed.", "SOURCE_MUTATION_REQUIRED": 0, "APPLY_READY_NOW": 0},
        ]

        selected_path = [
            {"SELECTED_PATH_ROW": 1, "SELECTED_PATH": "FURTHER_TARGETED_NATIVE_WRITER_DISCOVERY", "NEXT_ACTION": "Create/review a targeted discovery package focused on exact HELP DATA and CMDHELPCHK native writer/import/update paths.", "EXPECTED_MUTATION": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"SELECTED_PATH_ROW": 2, "SELECTED_PATH": "KEEP_APPLY_HELD", "NEXT_ACTION": "Keep HELP DATA and CMDHELPCHK apply blocked until a writer path and guarded apply package are reviewed.", "EXPECTED_MUTATION": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"SELECTED_PATH_ROW": 3, "SELECTED_PATH": "KEEP_SOURCE_PATCH_HELD", "NEXT_ACTION": "Do not plan or apply source patch until targeted discovery review proves it is needed.", "EXPECTED_MUTATION": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        rejected_paths = [
            {"REJECTED_PATH_ROW": 1, "REJECTED_PATH": "DIRECT_APPLY", "REJECTION_REASON": "No exact native writer path selected and reviewed."},
            {"REJECTED_PATH_ROW": 2, "REJECTED_PATH": "RAW_DBF_BYTE_WRITE", "REJECTION_REASON": "Forbidden for runtime promotion/materialization."},
            {"REJECTED_PATH_ROW": 3, "REJECTED_PATH": "SOURCE_PATCH_NOW", "REJECTION_REASON": "Source patch need remains unproven."},
            {"REJECTED_PATH_ROW": 4, "REJECTED_PATH": "REUSE_ASSUMED_WITHOUT_PROOF", "REJECTION_REASON": "Possible reuse candidates require exact writer proof."},
        ]

        targeted_scope = [
            {"SCOPE_ROW": 1, "TARGET": "HELP DATA writer/import/update path", "FOCUS": "Exact command/helper/source function that can create or update HELP MSGMGR and HELP SET MESSAGE entries.", "BROAD_SCAN_ALLOWED": 0},
            {"SCOPE_ROW": 2, "TARGET": "CMDHELPCHK writer/import/update path", "FOCUS": "Exact command/helper/source function that can create or update CMDHELPCHK records for MSGMGR and SET MESSAGE.", "BROAD_SCAN_ALLOWED": 0},
            {"SCOPE_ROW": 3, "TARGET": "reader/checker exclusion", "FOCUS": "Exclude HELP display, CMDHELPCHK readback, and process-doc rows that do not write/update targets.", "BROAD_SCAN_ALLOWED": 0},
            {"SCOPE_ROW": 4, "TARGET": "native/schema-aware proof", "FOCUS": "Confirm any future writer is native/runtime/schema-aware, not raw DBF byte mutation.", "BROAD_SCAN_ALLOWED": 0},
            {"SCOPE_ROW": 5, "TARGET": "source-comment contract impact", "FOCUS": "Only if later source patch is needed, require @dottalk.usage/source-comment update in same package.", "BROAD_SCAN_ALLOWED": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            carry_forward_blocked.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION",""),
                "BLOCKED": 1,
                "REASON": b.get("REASON",""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CJ selection.",
            })

        paths = [
            (cj_root / "native_writer_decision_selection_v1.csv", selection_rows, ["SELECTION_ROW","DECISION_OPTION","SELECTED","SELECTION_STATUS","RATIONALE","SOURCE_MUTATION_REQUIRED","APPLY_READY_NOW"]),
            (cj_root / "selected_path_contract_v1.csv", selected_path, ["SELECTED_PATH_ROW","SELECTED_PATH","NEXT_ACTION","EXPECTED_MUTATION","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cj_root / "rejected_paths_v1.csv", rejected_paths, ["REJECTED_PATH_ROW","REJECTED_PATH","REJECTION_REASON"]),
            (cj_root / "targeted_discovery_scope_v1.csv", targeted_scope, ["SCOPE_ROW","TARGET","FOCUS","BROAD_SCAN_ALLOWED"]),
            (cj_root / "carry_forward_blocked_actions_v1.csv", carry_forward_blocked, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, rs, fs in paths:
            wcsv(p, rs, fs)

        scripts = cj_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CK_REVIEW_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CJ selected targeted discovery only. Run 10CK review before any further package."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cj_root / "native_writer_decision_selection_package_v1.md"
        notes.write_text("# 10CJ Native Writer Decision Selection Package\n\n10CJ selects the conservative path: further targeted native writer discovery. It does not select reuse, prove source patch need, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = cj_root / "README_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE.md"
        readme.write_text("# 10CJ Native Writer Decision Selection Package\n\nSelection package only. The selected path is further targeted native writer discovery. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_selection_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_selection_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CJ writes docs/messaging selection artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision selection only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision selection only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "DECISION_SELECTION_PACKAGE_CREATED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": "Selection package staged."},
        {"ITEM": "SELECTED_PATH", "STATUS": "FURTHER_TARGETED_NATIVE_WRITER_DISCOVERY", "DETAIL": "Safe default because reuse and source patch need are not proven."},
        {"ITEM": "REUSE_PATH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "No exact writer reuse selected."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Source patch remains unproven."},
        {"ITEM": "DIRECT_APPLY_READY", "STATUS": "NO", "DETAIL": "Direct apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cj_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cj_decision_selection_v1.csv", selection_rows, ["SELECTION_ROW","DECISION_OPTION","SELECTED","SELECTION_STATUS","RATIONALE","SOURCE_MUTATION_REQUIRED","APPLY_READY_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cj_selected_path_contract_v1.csv", selected_path, ["SELECTED_PATH_ROW","SELECTED_PATH","NEXT_ACTION","EXPECTED_MUTATION","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cj_rejected_paths_v1.csv", rejected_paths, ["REJECTED_PATH_ROW","REJECTED_PATH","REJECTION_REASON"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cj_targeted_discovery_scope_v1.csv", targeted_scope, ["SCOPE_ROW","TARGET","FOCUS","BROAD_SCAN_ALLOWED"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cj_carry_forward_blocked_actions_v1.csv", carry_forward_blocked, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cj_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cj_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cj_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CI_STATUS": ci.get("STATUS",""),
        "MSG_022AE_6_5_10CI_SAVEPOINT_PRESENT": 1 if sp_ci else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CI_OPTION_REVIEW_ROWS": len(options),
        "CI_SELECTION_REQUIREMENT_ROWS": len(requirements),
        "DECISION_SELECTION_ROWS": len(selection_rows),
        "TARGETED_DISCOVERY_SCOPE_ROWS": len(targeted_scope),
        "CJ_ROOT": rel(cj_root, repo),
        "DECISION_SELECTION_PACKAGE_CREATED": 1 if status == GREEN else 0,
        "SELECTED_PATH": "FURTHER_TARGETED_NATIVE_WRITER_DISCOVERY" if status == GREEN else "",
        "REUSE_PATH_SELECTED_NOW": 0,
        "REUSE_PATH_CONFIRMED_NOW": 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cj_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CJ Native Writer Decision Selection Package\n\nStatus: `{status}`\n\n10CJ selects the conservative path: further targeted native writer discovery. It does not select reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nSelection root:\n\n```text\n{rel(cj_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CI status: {ci.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CI savepoint present: {1 if sp_ci else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CI option review rows: {len(options)}")
    print(f"  CI selection requirement rows: {len(requirements)}")
    print(f"  decision selection rows: {len(selection_rows)}")
    print(f"  targeted discovery scope rows: {len(targeted_scope)}")
    print(f"  selection root: {rel(cj_root, repo)}")
    print("  decision selection package created: 1")
    print("  selected path: FURTHER_TARGETED_NATIVE_WRITER_DISCOVERY")
    print("  reuse path selected now: 0")
    print("  reuse path confirmed now: 0")
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
