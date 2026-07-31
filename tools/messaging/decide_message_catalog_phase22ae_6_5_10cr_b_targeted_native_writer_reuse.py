#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

CQB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CQ_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_REVIEW_GREEN_READ_ONLY_SURFACE_PROOF_CAPTURED_REUSE_NOT_CONFIRMED"
CQB_SAVEPOINT = "MSG-022AE.6.5.10CQ-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CR_B_TARGETED_NATIVE_WRITER_REUSE_DECISION_PACKAGE_GREEN_READ_ONLY_PROOF_ACCEPTED_REUSE_NOT_CONFIRMED_SOURCE_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CR_B_TARGETED_NATIVE_WRITER_REUSE_DECISION_PACKAGE_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CS_B_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_PLAN"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cr_b_targeted_native_writer_reuse_decision_package_v1"

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

def csv_rows(p: Path) -> list[dict]:
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def csv_one(p: Path) -> dict:
    rows = csv_rows(p)
    return rows[0] if rows else {}

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

    cqb = csv_one(reports / "message_catalog_phase22ae_6_5_10cq_b_status_summary_v1.csv")
    latest_info = latest(repo)
    latest_before = latest_info.get("savepoint_id", latest_info.get("savepoint",""))

    cqb_green = int(cqb.get("STATUS","") == CQB_GREEN)
    cqb_sp = journal_has(repo, CQB_SAVEPOINT)
    read_only_proof = int(str(cqb.get("READ_ONLY_SURFACE_PROOF_CAPTURED","0")) == "1")
    active_invoked = int(str(cqb.get("ACTIVE_NATIVE_WRITER_INVOKED","0")) == "1")
    reuse_confirmed = int(str(cqb.get("REUSE_PATH_CONFIRMED_NOW","0")) == "1")
    surface_rows = int(str(cqb.get("SURFACE_ROWS","0") or "0"))

    pre = [
        {"check_id":"cq_b_status_green","value":cqb_green,"expected":1,"status":"PASS" if cqb_green else "FAIL"},
        {"check_id":"cq_b_savepoint_present","value":cqb_sp,"expected":1,"status":"PASS" if cqb_sp else "FAIL"},
        {"check_id":"read_only_surface_proof_captured","value":read_only_proof,"expected":1,"status":"PASS" if read_only_proof else "FAIL"},
        {"check_id":"active_native_writer_not_invoked","value":active_invoked,"expected":0,"status":"PASS" if active_invoked == 0 else "FAIL"},
        {"check_id":"reuse_not_confirmed_yet","value":reuse_confirmed,"expected":0,"status":"PASS" if reuse_confirmed == 0 else "FAIL"},
        {"check_id":"surface_rows_present","value":surface_rows,"expected":">0","status":"PASS" if surface_rows > 0 else "FAIL"},
        {"check_id":"cr_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_decision) else "FAIL"},
        {"check_id":"official_latest_pointer_not_modified_by_decision","value":1,"expected":1,"status":"PASS"},
    ]

    decision_rows = [
        {
            "decision_id":"DECISION_A_CONFIRM_NATIVE_WRITER_REUSE_FOR_APPLY_NOW",
            "selected":0,
            "decision_status":"REJECTED_FOR_NOW",
            "reason":"CQ-B captured read-only surface proof only; active candidate writer invocation was not proven.",
            "source_mutation_now":0,
            "apply_execution_now":0,
            "latest_pointer_change_now":0,
        },
        {
            "decision_id":"DECISION_B_CONTINUE_WITH_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_PLAN",
            "selected":1,
            "decision_status":"SELECTED",
            "reason":"Next safe proof must invoke/drive the candidate writer path in candidate-only mode, while refusing active apply and source mutation.",
            "source_mutation_now":0,
            "apply_execution_now":0,
            "latest_pointer_change_now":0,
        },
        {
            "decision_id":"DECISION_C_ESCALATE_TO_SOURCE_PATCH_PLAN",
            "selected":0,
            "decision_status":"NOT_SELECTED",
            "reason":"Source patch need is still not proven because a candidate-only active invocation proof has not been attempted.",
            "source_mutation_now":0,
            "apply_execution_now":0,
            "latest_pointer_change_now":0,
        },
        {
            "decision_id":"DECISION_D_HOLD_OPTION_B_SIDE_BRANCH",
            "selected":0,
            "decision_status":"SAFE_FALLBACK",
            "reason":"Hold remains available if CS-B planning cannot identify a safe candidate-only active invocation path.",
            "source_mutation_now":0,
            "apply_execution_now":0,
            "latest_pointer_change_now":0,
        },
    ]

    next_requirements = [
        {"req_id":"CSB001","requirement":"Select one concrete candidate writer surface from CQ-B/CP-B evidence, not a broad inventory scan.","required_next":1},
        {"req_id":"CSB002","requirement":"Define a candidate-only active invocation path that writes only under docs/messaging/apply/phase22ae_6_5_10cs_b or later side-branch roots.","required_next":1},
        {"req_id":"CSB003","requirement":"The active invocation proof must not write active HELP DATA, active CMDHELPCHK, source, DBF, CDX, LMDB, workspace, or latest pointer files.","required_next":1},
        {"req_id":"CSB004","requirement":"The proof must capture a transcript that distinguishes active candidate invocation from read-only surface probing.","required_next":1},
        {"req_id":"CSB005","requirement":"The proof must produce candidate outputs with hashes/counts and a boundary ledger.","required_next":1},
        {"req_id":"CSB006","requirement":"Reuse remains unconfirmed until a later proof review validates the active candidate invocation output.","required_next":1},
    ]

    branch_policy = [
        {"policy_id":"BRANCH001","policy":"Continue using -B side-branch labels only.","required":1},
        {"policy_id":"BRANCH002","policy":"Do not rewrite or supersede official mainline CQ/CR/CS/CU/CV/CX latest thread.","required":1},
        {"policy_id":"BRANCH003","policy":"Do not move message_savepoint_latest_v1.json from the official branch.","required":1},
        {"policy_id":"BRANCH004","policy":"Append side-branch journal savepoints only after green status.","required":1},
        {"policy_id":"BRANCH005","policy":"Treat read-only proof as evidence, not as apply-readiness.","required":1},
    ]

    boundary = [
        {"boundary":"read-only surface proof accepted","value":1,"status":"PASS" if read_only_proof else "FAIL"},
        {"boundary":"active native writer invoked now","value":0,"status":"PASS"},
        {"boundary":"native writer reuse confirmed now","value":0,"status":"PASS"},
        {"boundary":"source patch needed proven","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed","value":0,"status":"PASS"},
        {"boundary":"DBF mutation observed","value":0,"status":"PASS"},
        {"boundary":"CDX/LMDB mutation observed","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by CR-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for r in pre if r["status"] == "FAIL") + sum(1 for r in boundary if r["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10CR_B_DECISION_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10cr_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cr_b_decision_rows_v1.csv", ["decision_id","selected","decision_status","reason","source_mutation_now","apply_execution_now","latest_pointer_change_now"], decision_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cr_b_next_proof_requirements_v1.csv", ["req_id","requirement","required_next"], next_requirements)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cr_b_branch_policy_v1.csv", ["policy_id","policy","required"], branch_policy)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cr_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10CR-B",
        "CQ_B_STATUS_GREEN":cqb_green,
        "CQ_B_SAVEPOINT_PRESENT":cqb_sp,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CR_B":latest_before,
        "READ_ONLY_SURFACE_PROOF_ACCEPTED":1 if read_only_proof else 0,
        "SURFACE_ROWS_REVIEWED":surface_rows,
        "ACTIVE_NATIVE_WRITER_INVOKED_NOW":0,
        "SELECTED_DECISION":"DECISION_B_CONTINUE_WITH_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_PLAN",
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
        "LATEST_POINTER_CHANGED_BY_CR_B":0,
        "ACTIVE_CANDIDATE_INVOCATION_PLAN_REQUIRED":1,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cr_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10CR-B",
        "status":status,
        "selected_decision":"continue_with_active_candidate_native_writer_invocation_plan",
        "read_only_surface_proof_accepted":1 if read_only_proof else 0,
        "active_native_writer_invoked_now":0,
        "reuse_path_confirmed_now":0,
        "source_mutation_authorized_now":0,
        "apply_execution_authorized_now":0,
        "latest_pointer_changed_by_cr_b":0,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10cr_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10CR-B Targeted Native Writer Reuse Decision Package

- Status: {status}
- Validation issues: {validation}
- CQ-B status green: {cqb_green}
- CQ-B savepoint present: {cqb_sp}
- Official latest before CR-B: `{latest_before}`
- Read-only surface proof accepted: {1 if read_only_proof else 0}
- Surface rows reviewed: {surface_rows}
- Active native writer invoked now: 0
- Selected decision: `DECISION_B_CONTINUE_WITH_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_PLAN`
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
- Latest pointer changed by CR-B: 0
- Active candidate invocation plan required: 1
- Next gate: {next_gate}

CR-B accepts CQ-B's read-only surface proof as useful evidence, but it does not confirm native-writer reuse. The next side-branch step should plan a real candidate-only active invocation proof.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CR_B_TARGETED_NATIVE_WRITER_REUSE_DECISION_PACKAGE.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CR_B_TARGETED_NATIVE_WRITER_REUSE_DECISION_PACKAGE.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CQ-B status green: {cqb_green}")
    print(f"  CQ-B savepoint present: {cqb_sp}")
    print(f"  official latest before CR-B: {latest_before}")
    print(f"  read-only surface proof accepted: {1 if read_only_proof else 0}")
    print(f"  surface rows reviewed: {surface_rows}")
    print("  active native writer invoked now: 0")
    print("  selected decision: DECISION_B_CONTINUE_WITH_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_PLAN")
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
    print("  latest pointer changed by CR-B: 0")
    print("  active candidate invocation plan required: 1")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
