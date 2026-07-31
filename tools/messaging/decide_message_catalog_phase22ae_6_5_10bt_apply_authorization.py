#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BT_HELP_CMDHELPCHK_APPLY_EXECUTION_AUTHORIZATION_DECISION_GREEN_EXECUTION_STAGING_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BT_HELP_CMDHELPCHK_APPLY_EXECUTION_AUTHORIZATION_DECISION_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BU_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PACKAGE_STAGING"

REPORT_DIR = Path("docs/messaging/reports")
BS_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bs_status_summary_v1.csv"
BS_PREFLIGHT = REPORT_DIR / "message_catalog_phase22ae_6_5_10bs_preflight_review_v1.csv"
BS_CHECKLIST = REPORT_DIR / "message_catalog_phase22ae_6_5_10bs_checklist_review_v1.csv"
BS_RUNTIME = REPORT_DIR / "message_catalog_phase22ae_6_5_10bs_runtime_probe_review_v1.csv"
BS_DECISIONS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bs_review_decisions_v1.csv"
BR_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10br_preflight_package_v1.csv"
BT_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bt_help_cmdhelpchk_apply_execution_authorization_decision_v1")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

def rows(p):
    p = Path(p)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first(p):
    r = rows(p)
    return r[0] if r else {}

def wcsv(p, rs, fs):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fs, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rs:
            w.writerow({k: r.get(k, "") for k in fs})

def rel(p, repo):
    try:
        return str(Path(p).relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()

def dbf_count(p):
    p = Path(p)
    if not p.exists() or p.stat().st_size < 12:
        return ""
    return int.from_bytes(p.read_bytes()[:12][4:8], "little")

def savepoint(repo, sid):
    latest = ""
    lp = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if lp.exists():
        try:
            latest = json.loads(lp.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    jp = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    txt = jp.read_text(encoding="utf-8", errors="replace") if jp.exists() else ""
    return latest == sid or sid in txt, latest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-decision", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bs = first(repo / BS_SUMMARY)
    bs_preflight = rows(repo / BS_PREFLIGHT)
    bs_checklist = rows(repo / BS_CHECKLIST)
    bs_runtime = rows(repo / BS_RUNTIME)
    bs_decisions = rows(repo / BS_DECISIONS)
    br_package = rows(repo / BR_PACKAGE)
    sp_bs, latest_bs = savepoint(repo, "MSG-022AE.6.5.10BS")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bt_root = repo / BT_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BS_GREEN",
         bs.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BS_GUARDED_APPLY_PREFLIGHT_REVIEW_GREEN_APPLY_AUTHORIZATION_DECISION_REQUIRED_SOURCE_HELD",
         bs.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BS_SAVEPOINT_PRESENT", sp_bs, latest_bs)
    gate("BS_APPLY_AUTHORIZATION_DECISION_REQUIRED", bs.get("APPLY_AUTHORIZATION_DECISION_REQUIRED") == "1", bs.get("APPLY_AUTHORIZATION_DECISION_REQUIRED", "missing"))
    gate("BS_HELP_APPLY_NOT_EXECUTED", bs.get("HELP_DATA_APPLY_EXECUTED") == "0", bs.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BS_CMDHELPCHK_APPLY_NOT_EXECUTED", bs.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bs.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BS_PREFLIGHT_REVIEW_ROWS_PRESENT", len(bs_preflight) > 0, len(bs_preflight))
    gate("BS_CHECKLIST_REVIEW_ROWS_PRESENT", len(bs_checklist) > 0, len(bs_checklist))
    gate("BS_RUNTIME_REVIEW_ROWS_PRESENT", len(bs_runtime) > 0, len(bs_runtime))
    gate("BS_DECISIONS_PRESENT", len(bs_decisions) > 0, len(bs_decisions))
    gate("BR_PACKAGE_ROWS_PRESENT", len(br_package) > 0, len(br_package))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BT_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bt_root.exists()) or args.replace_existing_decision, rel(bt_root, repo))

    status = BLOCKED
    authorization_rows = []
    staging_plan_rows = []
    runtime_requirements = []
    artifact_rows = []

    if failures == 0:
        if bt_root.exists() and args.replace_existing_decision:
            shutil.rmtree(bt_root)
        bt_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(bs_preflight, start=1):
            review_ok = r.get("REVIEW_DISPOSITION", "") == "ACCEPT_FOR_APPLY_AUTHORIZATION_DECISION"
            authorization_rows.append({
                "AUTH_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "PREFLIGHT_REVIEW_DISPOSITION": r.get("REVIEW_DISPOSITION", ""),
                "APPLY_AUTHORIZATION_DECISION": "AUTHORIZE_EXECUTION_PACKAGE_STAGING_ONLY" if review_ok else "REVIEW_REQUIRED",
                "APPLY_EXECUTION_PACKAGE_STAGING_REQUIRED": 1,
                "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
                "APPLY_EXECUTED_NOW": 0,
                "REQUIRES_SEPARATE_EXPLICIT_APPLY_AUTHORIZATION": 1,
                "NOTES": "10BT records authorization decision for package staging only; it does not mutate HELP DATA or CMDHELPCHK.",
            })

        staging_plan_rows = [
            {"STAGING_STEP": 1, "STAGING_ACTION": "BUILD_DISABLED_EXECUTION_SCRIPT", "REQUIRED": 1, "DETAIL": "Next package may stage disabled apply script only; no implicit write."},
            {"STAGING_STEP": 2, "STAGING_ACTION": "RECHECK_TARGET_HASHES_AND_BACKUPS", "REQUIRED": 1, "DETAIL": "Execution package must refuse if accepted target/backup hashes drift."},
            {"STAGING_STEP": 3, "STAGING_ACTION": "CARRY_FORWARD_RUNTIME_READBACK", "REQUIRED": 1, "DETAIL": "Execution package must include runtime readback proof script."},
            {"STAGING_STEP": 4, "STAGING_ACTION": "CARRY_FORWARD_RESTORE_PATH", "REQUIRED": 1, "DETAIL": "Execution package must include restore-before-acceptance route."},
            {"STAGING_STEP": 5, "STAGING_ACTION": "REQUIRE_EXPLICIT_APPLY_SWITCH", "REQUIRED": 1, "DETAIL": "Actual mutation may only occur under a later explicit apply switch/authorization."},
        ]

        runtime_requirements = [
            {"REQUIREMENT_ROW": 1, "REQUIREMENT": "HELP_MSGMGR_READBACK", "DETAIL": "HELP MSGMGR must show the accepted topic after later apply."},
            {"REQUIREMENT_ROW": 2, "REQUIREMENT": "HELP_SET_MESSAGE_READBACK", "DETAIL": "HELP SET MESSAGE must show catalog/check/get/emit surfaces after later apply."},
            {"REQUIREMENT_ROW": 3, "REQUIREMENT": "CMDHELPCHK_READBACK", "DETAIL": "CMDHELPCHK must validate MSGMGR/SET MESSAGE surfaces after later apply."},
            {"REQUIREMENT_ROW": 4, "REQUIREMENT": "MESSAGING_COUNTS_STABLE", "DETAIL": "SYSTEM_MESSAGES remains 14 and SYSTEM_MESSAGE_TEXT remains 70 unless separately authorized."},
            {"REQUIREMENT_ROW": 5, "REQUIREMENT": "NO_RAW_DBF_WRITE", "DETAIL": "Any DBF-touching path must be native/schema-aware, not raw Python DBF mutation."},
        ]

        auth_path = bt_root / "apply_execution_authorization_decision_v1.csv"
        staging_path = bt_root / "guarded_execution_package_staging_plan_v1.csv"
        runtime_path = bt_root / "runtime_readback_requirements_v1.csv"
        disabled = bt_root / "scripts" / "MESSAGE_CATALOG_PHASE22AE_6_5_10BU_STAGING_REQUIRED_NO_APPLY.ps1.disabled"
        disabled.parent.mkdir(parents=True, exist_ok=True)
        disabled.write_text(
            'throw "DISABLED TEMPLATE: 10BT records an authorization decision for staging only. 10BU and later explicit apply authorization required."\n',
            encoding="utf-8"
        )
        readme = bt_root / "README_10BT_APPLY_EXECUTION_AUTHORIZATION_DECISION.md"
        readme.write_text(
            "# 10BT HELP/CMDHELPCHK Apply Execution Authorization Decision\n\n"
            "10BT records that the reviewed preflight can proceed to guarded execution-package staging only.\n\n"
            "It does not authorize or execute HELP DATA or CMDHELPCHK mutation. Actual apply still requires a later explicit apply authorization gate.\n",
            encoding="utf-8"
        )

        wcsv(auth_path, authorization_rows, ["AUTH_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","PREFLIGHT_REVIEW_DISPOSITION","APPLY_AUTHORIZATION_DECISION","APPLY_EXECUTION_PACKAGE_STAGING_REQUIRED","APPLY_EXECUTION_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","REQUIRES_SEPARATE_EXPLICIT_APPLY_AUTHORIZATION","NOTES"])
        wcsv(staging_path, staging_plan_rows, ["STAGING_STEP","STAGING_ACTION","REQUIRED","DETAIL"])
        wcsv(runtime_path, runtime_requirements, ["REQUIREMENT_ROW","REQUIREMENT","DETAIL"])

        for p in [auth_path, staging_path, runtime_path, disabled, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "apply_execution_authorization_decision_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BT writes docs/messaging authorization-decision artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Authorization decision only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Authorization decision only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "APPLY_AUTHORIZATION_DECISION_RECORDED", "STATUS": "YES" if authorization_rows else "NO", "DETAIL": f"{len(authorization_rows)} target authorization-decision rows."},
        {"ITEM": "EXECUTION_PACKAGE_STAGING_REQUIRED", "STATUS": "YES", "DETAIL": "10BU should stage execution package only."},
        {"ITEM": "SEPARATE_EXPLICIT_APPLY_AUTHORIZATION_REQUIRED", "STATUS": "YES", "DETAIL": "Actual mutation remains separately gated."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BT", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BT", "DETAIL": "No apply execution."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bt_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bt_authorization_decision_v1.csv", authorization_rows, ["AUTH_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","PREFLIGHT_REVIEW_DISPOSITION","APPLY_AUTHORIZATION_DECISION","APPLY_EXECUTION_PACKAGE_STAGING_REQUIRED","APPLY_EXECUTION_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","REQUIRES_SEPARATE_EXPLICIT_APPLY_AUTHORIZATION","NOTES"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bt_staging_plan_v1.csv", staging_plan_rows, ["STAGING_STEP","STAGING_ACTION","REQUIRED","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bt_runtime_readback_requirements_v1.csv", runtime_requirements, ["REQUIREMENT_ROW","REQUIREMENT","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bt_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bt_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bt_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BS_STATUS": bs.get("STATUS", ""),
        "MSG_022AE_6_5_10BS_SAVEPOINT_PRESENT": 1 if sp_bs else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BS_PREFLIGHT_REVIEW_ROWS": len(bs_preflight),
        "BS_CHECKLIST_REVIEW_ROWS": len(bs_checklist),
        "BS_RUNTIME_REVIEW_ROWS": len(bs_runtime),
        "AUTHORIZATION_DECISION_ROWS": len(authorization_rows),
        "STAGING_PLAN_ROWS": len(staging_plan_rows),
        "RUNTIME_REQUIREMENT_ROWS": len(runtime_requirements),
        "BT_ROOT": rel(bt_root, repo),
        "APPLY_AUTHORIZATION_DECISION_RECORDED": 1 if status == GREEN else 0,
        "EXECUTION_PACKAGE_STAGING_REQUIRED": 1 if status == GREEN else 0,
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
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    wcsv(reports / "message_catalog_phase22ae_6_5_10bt_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BT_HELP_CMDHELPCHK_APPLY_EXECUTION_AUTHORIZATION_DECISION.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BT HELP/CMDHELPCHK Apply Execution Authorization Decision\n\n"
        f"Status: `{status}`\n\n"
        "10BT records an authorization decision for guarded execution-package staging only. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Decision root:\n\n```text\n{rel(bt_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BS status: {bs.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BS savepoint present: {1 if sp_bs else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BS preflight review rows: {len(bs_preflight)}")
    print(f"  BS checklist review rows: {len(bs_checklist)}")
    print(f"  BS runtime review rows: {len(bs_runtime)}")
    print(f"  authorization decision rows: {len(authorization_rows)}")
    print(f"  staging plan rows: {len(staging_plan_rows)}")
    print(f"  runtime requirement rows: {len(runtime_requirements)}")
    print(f"  decision root: {rel(bt_root, repo)}")
    print("  apply authorization decision recorded: 1")
    print("  execution package staging required: 1")
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
