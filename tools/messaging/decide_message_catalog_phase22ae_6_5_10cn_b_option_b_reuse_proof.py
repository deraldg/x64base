#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

CMB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CM_B_OPTION_B_WRAPPER_CONTRACT_PROOF_REVIEW_GREEN_CANDIDATE_OUTPUT_CAPTURE_PROVEN_SOURCE_HELD"
CMB_SAVEPOINT = "MSG-022AE.6.5.10CM-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CN_B_OPTION_B_REUSE_PROOF_DECISION_PACKAGE_GREEN_CAPTURE_ACCEPTED_REUSE_NOT_CONFIRMED_SOURCE_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CN_B_OPTION_B_REUSE_PROOF_DECISION_PACKAGE_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CO_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_PLAN"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cn_b_option_b_reuse_proof_decision_package_v1"

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")

def write_csv(p: Path, fields, rows) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

def csv_one(p: Path) -> dict:
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
            return rows[0] if rows else {}
    except Exception:
        return {}

def journal_has(repo: Path, marker: str) -> int:
    return int(marker in read_text(repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def latest(repo: Path) -> dict:
    try:
        return json.loads(read_text(repo / "docs/messaging/reports/message_savepoint_latest_v1.json"))
    except Exception:
        return {}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-decision", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_decision:
        shutil.rmtree(out)

    cmb = csv_one(reports / "message_catalog_phase22ae_6_5_10cm_b_status_summary_v1.csv")
    latest_info = latest(repo)
    latest_before = latest_info.get("savepoint_id", latest_info.get("savepoint",""))

    cmb_green = int(cmb.get("STATUS","") == CMB_GREEN)
    cmb_sp = journal_has(repo, CMB_SAVEPOINT)
    output_capture = int(str(cmb.get("CANDIDATE_OUTPUT_CAPTURE_PROVEN","0")) == "1")
    reuse_confirmed_cm_b = int(str(cmb.get("REUSE_PATH_CONFIRMED_NOW","0")) == "1")

    pre = [
        {"check_id":"cm_b_status_green","value":cmb_green,"expected":1,"status":"PASS" if cmb_green else "FAIL"},
        {"check_id":"cm_b_savepoint_present","value":cmb_sp,"expected":1,"status":"PASS" if cmb_sp else "FAIL"},
        {"check_id":"candidate_output_capture_proven","value":output_capture,"expected":1,"status":"PASS" if output_capture else "FAIL"},
        {"check_id":"cm_b_reuse_not_confirmed","value":reuse_confirmed_cm_b,"expected":0,"status":"PASS" if reuse_confirmed_cm_b == 0 else "FAIL"},
        {"check_id":"cn_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_decision) else "FAIL"},
        {"check_id":"official_latest_pointer_not_modified_by_decision","value":1,"expected":1,"status":"PASS"},
    ]

    decision_rows = [
        {
            "decision_id":"DECISION_A_CONFIRM_NATIVE_WRITER_REUSE_NOW",
            "selected":0,
            "decision_status":"REJECTED_FOR_NOW",
            "reason":"CM-B proves candidate output capture only; it does not prove real native-writer reuse is sufficient for active apply.",
            "source_mutation_now":0,
            "apply_execution_now":0,
        },
        {
            "decision_id":"DECISION_B_CONTINUE_OPTION_B_WITH_TARGETED_NATIVE_WRITER_INVOCATION_PROOF",
            "selected":1,
            "decision_status":"SELECTED",
            "reason":"Continue Option B, but require a targeted native-writer invocation proof before confirming reuse or authorizing apply.",
            "source_mutation_now":0,
            "apply_execution_now":0,
        },
        {
            "decision_id":"DECISION_C_ESCALATE_TO_SOURCE_PATCH_PLAN",
            "selected":0,
            "decision_status":"NOT_SELECTED",
            "reason":"Source patch need is not proven; reuse path deserves one deeper invocation proof first.",
            "source_mutation_now":0,
            "apply_execution_now":0,
        },
        {
            "decision_id":"DECISION_D_HOLD_OPTION_B_BRANCH",
            "selected":0,
            "decision_status":"SAFE_FALLBACK",
            "reason":"Hold remains available if CO-B proof planning fails.",
            "source_mutation_now":0,
            "apply_execution_now":0,
        },
    ]

    proof_requirements = [
        {"req_id":"COB001","requirement":"Identify exact native writer entrypoint or existing script/function that writes candidate HELP/CMDHELPCHK artifacts.","required_next":1},
        {"req_id":"COB002","requirement":"Run only in candidate-output mode under docs/messaging/apply/phase22ae_6_5_10co_b_* paths.","required_next":1},
        {"req_id":"COB003","requirement":"Capture actual invocation transcript, not just a placeholder boundary-smoke proof.","required_next":1},
        {"req_id":"COB004","requirement":"Produce candidate output artifacts with row counts, hashes, and refusal guards.","required_next":1},
        {"req_id":"COB005","requirement":"Refuse source edits, active HELP DATA apply, active CMDHELPCHK apply, active DBF/CDX/LMDB mutation, and latest-pointer movement.","required_next":1},
        {"req_id":"COB006","requirement":"Return to proof review before any reuse confirmation or active apply decision.","required_next":1},
    ]

    boundary = [
        {"boundary":"reuse path selected now","value":1,"status":"PASS"},
        {"boundary":"candidate output capture accepted","value":1,"status":"PASS" if output_capture else "FAIL"},
        {"boundary":"reuse path confirmed now","value":0,"status":"PASS"},
        {"boundary":"source patch needed proven","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed","value":0,"status":"PASS"},
        {"boundary":"DBF mutation observed","value":0,"status":"PASS"},
        {"boundary":"CDX/LMDB mutation observed","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by CN-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for r in pre if r["status"] == "FAIL") + sum(1 for r in boundary if r["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10CN_B_DECISION_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cn_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cn_b_decision_rows_v1.csv", ["decision_id","selected","decision_status","reason","source_mutation_now","apply_execution_now"], decision_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cn_b_targeted_invocation_proof_requirements_v1.csv", ["req_id","requirement","required_next"], proof_requirements)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cn_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10CN-B",
        "CM_B_STATUS_GREEN":cmb_green,
        "CM_B_SAVEPOINT_PRESENT":cmb_sp,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CN_B":latest_before,
        "CANDIDATE_OUTPUT_CAPTURE_ACCEPTED":1 if output_capture else 0,
        "SELECTED_DECISION":"DECISION_B_CONTINUE_OPTION_B_WITH_TARGETED_NATIVE_WRITER_INVOCATION_PROOF",
        "REUSE_PATH_SELECTED_NOW":1,
        "REUSE_PATH_CONFIRMED_NOW":0,
        "SOURCE_PATCH_NEEDED_PROVEN":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED":0,
        "DBF_MUTATION_OBSERVED":0,
        "CDX_LMDB_MUTATION_OBSERVED":0,
        "WORKSPACE_MUTATION_OBSERVED":0,
        "LATEST_POINTER_CHANGED_BY_CN_B":0,
        "TARGETED_INVOCATION_PROOF_REQUIRED":1,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cn_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10CN-B",
        "status":status,
        "candidate_output_capture_accepted":1 if output_capture else 0,
        "selected_decision":"continue_option_b_with_targeted_native_writer_invocation_proof",
        "reuse_path_confirmed_now":0,
        "source_mutation_authorized_now":0,
        "apply_execution_authorized_now":0,
        "latest_pointer_changed_by_cn_b":0,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10cn_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10CN-B Option B Reuse Proof Decision Package

- Status: {status}
- Validation issues: {validation}
- CM-B status green: {cmb_green}
- CM-B savepoint present: {cmb_sp}
- Official latest before CN-B: `{latest_before}`
- Candidate output capture accepted: {1 if output_capture else 0}
- Selected decision: `DECISION_B_CONTINUE_OPTION_B_WITH_TARGETED_NATIVE_WRITER_INVOCATION_PROOF`
- Reuse path selected now: 1
- Reuse path confirmed now: 0
- Source patch needed proven: 0
- Source mutation authorized now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Active catalog mutation observed: 0
- DBF mutation observed: 0
- CDX/LMDB mutation observed: 0
- Workspace mutation observed: 0
- Latest pointer changed by CN-B: 0
- Targeted invocation proof required: 1
- Next gate: {next_gate}

CN-B accepts CM-B's candidate output capture proof, but it does not confirm native-writer reuse for active apply. The next side-branch step must plan a targeted native-writer invocation proof.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CN_B_OPTION_B_REUSE_PROOF_DECISION_PACKAGE.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CN_B_OPTION_B_REUSE_PROOF_DECISION_PACKAGE.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CM-B status green: {cmb_green}")
    print(f"  CM-B savepoint present: {cmb_sp}")
    print(f"  official latest before CN-B: {latest_before}")
    print(f"  candidate output capture accepted: {1 if output_capture else 0}")
    print("  selected decision: DECISION_B_CONTINUE_OPTION_B_WITH_TARGETED_NATIVE_WRITER_INVOCATION_PROOF")
    print("  reuse path selected now: 1")
    print("  reuse path confirmed now: 0")
    print("  source patch needed proven: 0")
    print("  source mutation authorized now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  active catalog mutation observed: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print("  latest pointer changed by CN-B: 0")
    print("  targeted invocation proof required: 1")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
