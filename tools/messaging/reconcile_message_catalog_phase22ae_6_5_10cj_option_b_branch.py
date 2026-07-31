#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

PHASE = "22AE.6.5.10CJ-OPTIONB-RECON"
STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_OPTION_B_BRANCH_RECONCILIATION_GREEN_REPORT_ONLY_BRANCH_COLLISION_DOCUMENTED"
STATUS_RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_OPTION_B_BRANCH_RECONCILIATION_RED_REVIEW_REQUIRED"
OPTION_B_STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_GREEN_OPTION_B_REUSE_WITH_WRAPPER_CONTRACT_SELECTED_SOURCE_HELD"
OLDER_CJ_STATUS_FRAGMENT = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_GREEN_TARGETED_DISCOVERY_SELECTED_SOURCE_HELD"
CL_STATUS_FRAGMENT = "MESSAGE_CATALOG_PHASE22AE_6_5_10CL_TARGETED_NATIVE_WRITER_DISCOVERY_PACKAGE_GREEN_DISCOVERY_REPORTED_SOURCE_HELD"
NEXT_GATE = "HOLD_OR_CHOOSE_MESSAGING_NATIVE_WRITER_BRANCH_AFTER_CJ_OPTION_B_COLLISION"

RECON_ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cj_option_b_branch_reconciliation_v1"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})

def csv_rows(path: Path) -> list[dict]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def read_current_cj_summary(repo: Path) -> dict:
    p = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10cj_status_summary_v1.csv"
    rows = csv_rows(p)
    return rows[0] if rows else {}

def read_latest(repo: Path) -> dict:
    p = repo / "docs/messaging/reports/message_savepoint_latest_v1.json"
    try:
        return json.loads(read_text(p))
    except Exception:
        return {}

def journal_contains(repo: Path, text: str) -> int:
    return int(text in read_text(repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-reconciliation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    journal = docs / "MESSAGING_SAVEPOINT_JOURNAL.md"
    recon_root = repo / RECON_ROOT_REL

    if recon_root.exists() and args.replace_existing_reconciliation:
        shutil.rmtree(recon_root)

    cj = read_current_cj_summary(repo)
    latest = read_latest(repo)
    journal_text = read_text(journal)

    current_cj_status = cj.get("STATUS", "")
    current_selected = cj.get("SELECTED_OPTION", "")
    current_next_gate = cj.get("NEXT_GATE", "")
    latest_savepoint = latest.get("savepoint_id", latest.get("savepoint", ""))
    latest_status = latest.get("status", "")

    option_b_summary_present = int(current_cj_status == OPTION_B_STATUS and current_selected == "OPTION_B_REUSE_NATIVE_WRITER_WITH_WRAPPER_OR_CONTRACT")
    old_cj_savepoint_present = int("MSG-022AE.6.5.10CJ" in journal_text and OLDER_CJ_STATUS_FRAGMENT in journal_text)
    ck_present = int("MSG-022AE.6.5.10CK" in journal_text)
    cl_present = int("MSG-022AE.6.5.10CL" in journal_text or latest_savepoint == "MSG-022AE.6.5.10CL")
    latest_points_to_cl = int(latest_savepoint == "MSG-022AE.6.5.10CL" or CL_STATUS_FRAGMENT in latest_status)
    branch_collision_detected = int(option_b_summary_present and old_cj_savepoint_present and (ck_present or cl_present or latest_points_to_cl))

    boundary_ok = all(str(cj.get(k, "0")) == "0" for k in [
        "REUSE_PATH_CONFIRMED_NOW",
        "SOURCE_PATCH_NEEDED_PROVEN",
        "SOURCE_MUTATION_AUTHORIZED_NOW",
        "APPLY_EXECUTION_AUTHORIZED_NOW",
        "HELP_DATA_APPLY_EXECUTED",
        "CMDHELPCHK_APPLY_EXECUTED",
        "HELP_DATA_MUTATION_OBSERVED",
        "CMDHELPCHK_MUTATION_OBSERVED",
        "SOURCE_FILES_MUTATED",
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_SELECTION",
        "DBF_MUTATION_OBSERVED",
        "CDX_LMDB_MUTATION_OBSERVED",
        "WORKSPACE_MUTATION_OBSERVED",
    ])

    preconditions = [
        {"check_id":"current_cj_option_b_summary_present", "value":option_b_summary_present, "expected":1, "status":"PASS" if option_b_summary_present else "FAIL"},
        {"check_id":"older_cj_targeted_discovery_savepoint_present", "value":old_cj_savepoint_present, "expected":1, "status":"PASS" if old_cj_savepoint_present else "FAIL"},
        {"check_id":"later_ck_or_cl_branch_entries_present", "value":int(ck_present or cl_present or latest_points_to_cl), "expected":1, "status":"PASS" if (ck_present or cl_present or latest_points_to_cl) else "FAIL"},
        {"check_id":"latest_pointer_at_cl_or_later_branch", "value":latest_points_to_cl, "expected":1, "status":"PASS" if latest_points_to_cl else "REVIEW"},
        {"check_id":"option_b_summary_boundary_clean", "value":int(boundary_ok), "expected":1, "status":"PASS" if boundary_ok else "FAIL"},
        {"check_id":"reconciliation_root_absent_or_replace_authorized", "value":int(recon_root.exists()), "expected":0, "status":"PASS" if (not recon_root.exists() or args.replace_existing_reconciliation) else "FAIL"},
    ]

    validation_issues = sum(1 for r in preconditions if r["status"] == "FAIL")
    status = STATUS_GREEN if validation_issues == 0 else STATUS_RED
    next_gate = NEXT_GATE if status == STATUS_GREEN else "REVIEW_CJ_OPTION_B_RECONCILIATION_PRECONDITIONS"

    recon_root.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    branch_rows = [
        {
            "branch_id":"EXISTING_TARGETED_DISCOVERY_BRANCH",
            "evidence":"Journal already contains MSG-022AE.6.5.10CJ targeted discovery plus CK/CL entries; latest pointer is CL.",
            "status":"ACTIVE_IN_JOURNAL",
            "recommended_action":"Continue only if the user chooses to keep the earlier targeted-discovery path.",
            "mutate_now":0,
        },
        {
            "branch_id":"NEW_OPTION_B_WRAPPER_CONTRACT_BRANCH",
            "evidence":"Current 10CJ summary file now contains Option B selected, but journal cannot accept duplicate MSG-022AE.6.5.10CJ.",
            "status":"CANDIDATE_BRANCH_NEEDS_DISTINCT_ID",
            "recommended_action":"Continue only under a distinct branch/savepoint id such as MSG-022AE.6.5.10CJ-B or 10CJ2, then CK-B.",
            "mutate_now":0,
        },
    ]

    decision_rows = [
        {
            "decision":"CONTINUE_EXISTING_TARGETED_DISCOVERY_BRANCH",
            "meaning":"Ignore the overwritten Option B CJ summary for lane advancement and proceed from current CL latest.",
            "requires":"No new Option B branch; preserve CL as current latest.",
        },
        {
            "decision":"CREATE_DISTINCT_OPTION_B_BRANCH",
            "meaning":"Preserve Option B as a new branch using distinct savepoint labels, then create CK-B wrapper/contract proof plan.",
            "requires":"Journal addendum and future packages must not reuse occupied CJ/CK/CL identifiers.",
        },
        {
            "decision":"REBUILD_CJ_OPTION_B_AS_OFFICIAL_REPLACEMENT",
            "meaning":"Treat Option B as superseding the earlier targeted-discovery branch.",
            "requires":"Explicit supersession package that marks CJ/CK/CL targeted-discovery entries as superseded for accounting; higher risk.",
        },
    ]

    boundary_rows = [
        {"boundary":"source files mutated", "value":0, "status":"PASS"},
        {"boundary":"HELP DATA apply executed", "value":0, "status":"PASS"},
        {"boundary":"CMDHELPCHK apply executed", "value":0, "status":"PASS"},
        {"boundary":"active catalog mutation", "value":0, "status":"PASS"},
        {"boundary":"DBF mutation", "value":0, "status":"PASS"},
        {"boundary":"CDX/LMDB mutation", "value":0, "status":"PASS"},
        {"boundary":"workspace mutation", "value":0, "status":"PASS"},
        {"boundary":"latest pointer changed by reconciliation", "value":0, "status":"PASS"},
        {"boundary":"journal appended by run step", "value":0, "status":"PASS"},
    ]

    summary_rows = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation_issues,
        "CURRENT_CJ_STATUS":current_cj_status,
        "CURRENT_SELECTED_OPTION":current_selected,
        "CURRENT_CJ_NEXT_GATE":current_next_gate,
        "OLDER_CJ_TARGETED_DISCOVERY_SAVEPOINT_PRESENT":old_cj_savepoint_present,
        "CK_PRESENT_IN_JOURNAL":ck_present,
        "CL_PRESENT_OR_LATEST":cl_present,
        "LATEST_SAVEPOINT":latest_savepoint,
        "LATEST_STATUS":latest_status,
        "BRANCH_COLLISION_DETECTED":branch_collision_detected,
        "OPTION_B_SUMMARY_BOUNDARY_CLEAN":int(boundary_ok),
        "RECON_ROOT":str(recon_root.relative_to(repo)).replace("\\","/"),
        "JOURNAL_APPEND_EXECUTED_BY_RUN":0,
        "LATEST_POINTER_CHANGED_BY_RUN":0,
        "SOURCE_FILES_MUTATED":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED":0,
        "DBF_MUTATION_OBSERVED":0,
        "CDX_LMDB_MUTATION_OBSERVED":0,
        "WORKSPACE_MUTATION_OBSERVED":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]

    write_csv(reports / "message_catalog_phase22ae_6_5_10cj_option_b_reconciliation_preconditions_v1.csv",
              ["check_id","value","expected","status"], preconditions)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cj_option_b_reconciliation_branch_rows_v1.csv",
              ["branch_id","evidence","status","recommended_action","mutate_now"], branch_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cj_option_b_reconciliation_decision_rows_v1.csv",
              ["decision","meaning","requires"], decision_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cj_option_b_reconciliation_boundary_v1.csv",
              ["boundary","value","status"], boundary_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cj_option_b_reconciliation_status_summary_v1.csv",
              list(summary_rows[0].keys()), summary_rows)

    manifest = {
        "phase": PHASE,
        "status": status,
        "branch_collision_detected": branch_collision_detected,
        "current_cj_status": current_cj_status,
        "current_selected_option": current_selected,
        "latest_savepoint": latest_savepoint,
        "latest_status": latest_status,
        "journal_append_executed_by_run": 0,
        "latest_pointer_changed_by_run": 0,
        "next_gate": next_gate,
    }
    write_text(recon_root / "message_catalog_phase22ae_6_5_10cj_option_b_reconciliation_manifest_v1.json",
               json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10CJ Option B Branch Reconciliation

- Status: {status}
- Validation issues: {validation_issues}
- Current CJ summary status: `{current_cj_status}`
- Current selected option: `{current_selected}`
- Existing CJ journal targeted-discovery savepoint present: {old_cj_savepoint_present}
- CK present in journal: {ck_present}
- CL present/latest: {cl_present}
- Latest savepoint: `{latest_savepoint}`
- Latest status: `{latest_status}`
- Branch collision detected: {branch_collision_detected}
- Option B summary boundary clean: {int(boundary_ok)}
- Journal append executed by run: 0
- Latest pointer changed by run: 0
- Source files mutated: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- DBF/CDX/LMDB mutation observed: 0
- Workspace mutation observed: 0
- Next gate: {next_gate}

## Interpretation

The current CJ summary file contains Option B, but the journal already has a CJ savepoint for the earlier targeted-discovery branch and later CK/CL targeted-discovery entries. This is a branch/accounting collision, not evidence of protected data mutation.

## Safe branch choices

1. Continue the existing targeted-discovery branch from CL.
2. Create a distinct Option B wrapper/contract branch with unique labels such as CJ-B / CK-B.
3. Explicitly supersede the earlier targeted-discovery branch before making Option B official.
"""
    write_text(recon_root / "MESSAGE_LOCALE_PHASE22AE_6_5_10CJ_OPTION_B_BRANCH_RECONCILIATION.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CJ_OPTION_B_BRANCH_RECONCILIATION.md", report)

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  current CJ status: {current_cj_status}")
    print(f"  current selected option: {current_selected}")
    print(f"  existing CJ targeted-discovery savepoint present: {old_cj_savepoint_present}")
    print(f"  CK present in journal: {ck_present}")
    print(f"  CL present/latest: {cl_present}")
    print(f"  latest savepoint: {latest_savepoint}")
    print(f"  branch collision detected: {branch_collision_detected}")
    print(f"  option B summary boundary clean: {int(boundary_ok)}")
    print("  journal append executed by run: 0")
    print("  latest pointer changed by run: 0")
    print("  source files mutated: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
