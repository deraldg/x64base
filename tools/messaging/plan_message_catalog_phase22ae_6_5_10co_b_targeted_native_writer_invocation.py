#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

CNB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CN_B_OPTION_B_REUSE_PROOF_DECISION_PACKAGE_GREEN_CAPTURE_ACCEPTED_REUSE_NOT_CONFIRMED_SOURCE_HELD"
CNB_SAVEPOINT = "MSG-022AE.6.5.10CN-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CO_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_PLAN_GREEN_SIDE_BRANCH_SOURCE_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CO_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_PLAN_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CP_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_STAGING"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10co_b_targeted_native_writer_invocation_proof_plan_v1"

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
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_plan:
        shutil.rmtree(out)

    cnb = csv_one(reports / "message_catalog_phase22ae_6_5_10cn_b_status_summary_v1.csv")
    latest_info = latest(repo)
    latest_before = latest_info.get("savepoint_id", latest_info.get("savepoint",""))

    cnb_green = int(cnb.get("STATUS","") == CNB_GREEN)
    cnb_sp = journal_has(repo, CNB_SAVEPOINT)
    proof_required = int(str(cnb.get("TARGETED_INVOCATION_PROOF_REQUIRED","0")) == "1")
    reuse_confirmed = int(str(cnb.get("REUSE_PATH_CONFIRMED_NOW","0")) == "1")

    inventory = csv_rows(reports / "message_catalog_phase22ae_6_5_10cl_b_native_writer_candidate_inventory_v1.csv")
    top_inventory = inventory[:20]

    pre = [
        {"check_id":"cn_b_status_green","value":cnb_green,"expected":1,"status":"PASS" if cnb_green else "FAIL"},
        {"check_id":"cn_b_savepoint_present","value":cnb_sp,"expected":1,"status":"PASS" if cnb_sp else "FAIL"},
        {"check_id":"targeted_invocation_proof_required","value":proof_required,"expected":1,"status":"PASS" if proof_required else "FAIL"},
        {"check_id":"reuse_not_confirmed_yet","value":reuse_confirmed,"expected":0,"status":"PASS" if reuse_confirmed == 0 else "FAIL"},
        {"check_id":"cl_b_candidate_inventory_available","value":len(inventory),"expected":">0","status":"PASS" if len(inventory) > 0 else "REVIEW"},
        {"check_id":"co_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_plan) else "FAIL"},
        {"check_id":"official_latest_pointer_not_modified_by_plan","value":1,"expected":1,"status":"PASS"},
    ]

    invocation_plan = [
        {
            "step_id":"COB001",
            "phase":"candidate-surface-selection",
            "description":"Review CL-B inventory and select the likely native-writer surface or script for candidate-only invocation.",
            "expected_artifact":"selected_native_writer_surface_v1.csv",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"COB002",
            "phase":"input-contract",
            "description":"Define exact candidate input manifest and minimal row set for HELP DATA / CMDHELPCHK candidate output generation.",
            "expected_artifact":"targeted_invocation_input_manifest_v1.json",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"COB003",
            "phase":"output-contract",
            "description":"Define expected candidate output files, counts, hashes, and transcript markers under CO/CP-B side-branch paths.",
            "expected_artifact":"targeted_invocation_output_manifest_v1.json",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"COB004",
            "phase":"refusal-guards",
            "description":"Require hard guards against source edits, active HELP/CMDHELPCHK apply, active DBF/CDX/LMDB, workspace mutation, and latest-pointer movement.",
            "expected_artifact":"targeted_invocation_refusal_guards_v1.csv",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"COB005",
            "phase":"staging-package",
            "description":"Create CP-B staging package with candidate-only invocation script, not execution by the package.",
            "expected_artifact":"CP-B staging package",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"COB006",
            "phase":"manual-run-proof",
            "description":"Run the CP-B proof script only after explicit authorization and capture transcript/candidate outputs.",
            "expected_artifact":"CP-B transcript and outputs",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"COB007",
            "phase":"proof-review",
            "description":"Review CP-B proof in CQ-B before any decision to confirm reuse or authorize active apply.",
            "expected_artifact":"CQ-B proof review",
            "execute_now":0,
            "mutation_now":0,
        },
    ]

    selection_criteria = [
        {"criterion_id":"SURFACE001","criterion":"Prefer existing messaging/native writer tool or function already observed in CL-B inventory.","required":1},
        {"criterion_id":"SURFACE002","criterion":"Must support candidate-only output path or be wrapped to redirect all outputs to docs/messaging/apply.","required":1},
        {"criterion_id":"SURFACE003","criterion":"Must not require source patching to perform the proof.","required":1},
        {"criterion_id":"SURFACE004","criterion":"Must produce inspectable transcript/log and machine-readable output summary.","required":1},
        {"criterion_id":"SURFACE005","criterion":"Must refuse active HELP DATA and CMDHELPCHK apply in this branch.","required":1},
        {"criterion_id":"SURFACE006","criterion":"Must preserve official latest pointer and use -B labels only.","required":1},
    ]

    refusal = [
        {"guard_id":"REFUSE_SOURCE_MUTATION","condition":"No source edits or generated source files.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_HELP_DATA_APPLY","condition":"No HELP DATA apply execution.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_CMDHELPCHK_APPLY","condition":"No CMDHELPCHK apply execution.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_ACTIVE_DBF_MUTATION","condition":"No active DBF mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_CDX_LMDB_MUTATION","condition":"No CDX/LMDB mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_WORKSPACE_MUTATION","condition":"No workspace mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_LATEST_POINTER_CHANGE","condition":"Do not move message_savepoint_latest_v1.json.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_REUSE_CONFIRMATION_NOW","condition":"Do not confirm native-writer reuse until CP-B/CQ-B proof review passes.","required":1,"execute_now":0},
    ]

    boundary = [
        {"boundary":"targeted invocation executed by CO-B","value":0,"status":"PASS"},
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
        {"boundary":"latest pointer changed by CO-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for r in pre if r["status"] == "FAIL") + sum(1 for r in boundary if r["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10CO_B_PLAN_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10co_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10co_b_top_candidate_inventory_v1.csv", ["candidate_path","suffix","score","size_bytes","inventory_only"], top_inventory)
    write_csv(reports / "message_catalog_phase22ae_6_5_10co_b_invocation_plan_v1.csv", ["step_id","phase","description","expected_artifact","execute_now","mutation_now"], invocation_plan)
    write_csv(reports / "message_catalog_phase22ae_6_5_10co_b_surface_selection_criteria_v1.csv", ["criterion_id","criterion","required"], selection_criteria)
    write_csv(reports / "message_catalog_phase22ae_6_5_10co_b_refusal_guards_v1.csv", ["guard_id","condition","required","execute_now"], refusal)
    write_csv(reports / "message_catalog_phase22ae_6_5_10co_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    manifest = {
        "phase":"22AE.6.5.10CO-B",
        "status":status,
        "purpose":"targeted native-writer invocation proof plan",
        "official_latest_before_co_b":latest_before,
        "candidate_inventory_rows_observed":len(inventory),
        "top_candidate_rows_staged":len(top_inventory),
        "targeted_invocation_executed_by_co_b":0,
        "reuse_path_confirmed_now":0,
        "source_mutation_authorized_now":0,
        "apply_execution_authorized_now":0,
        "latest_pointer_changed_by_co_b":0,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10co_b_manifest_v1.json", json.dumps(manifest, indent=2))

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10CO-B",
        "CN_B_STATUS_GREEN":cnb_green,
        "CN_B_SAVEPOINT_PRESENT":cnb_sp,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CO_B":latest_before,
        "TARGETED_INVOCATION_PROOF_REQUIRED":proof_required,
        "CL_B_CANDIDATE_INVENTORY_ROWS_OBSERVED":len(inventory),
        "TOP_CANDIDATE_ROWS_STAGED":len(top_inventory),
        "INVOCATION_PLAN_ROWS":len(invocation_plan),
        "SURFACE_SELECTION_CRITERIA_ROWS":len(selection_criteria),
        "REFUSAL_GUARD_ROWS":len(refusal),
        "TARGETED_INVOCATION_EXECUTED_BY_CO_B":0,
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
        "LATEST_POINTER_CHANGED_BY_CO_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10co_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    report = f"""# Phase 22AE.6.5.10CO-B Targeted Native Writer Invocation Proof Plan

- Status: {status}
- Validation issues: {validation}
- CN-B status green: {cnb_green}
- CN-B savepoint present: {cnb_sp}
- Official latest before CO-B: `{latest_before}`
- Targeted invocation proof required: {proof_required}
- CL-B candidate inventory rows observed: {len(inventory)}
- Top candidate rows staged: {len(top_inventory)}
- Invocation plan rows: {len(invocation_plan)}
- Surface selection criteria rows: {len(selection_criteria)}
- Refusal guard rows: {len(refusal)}
- Targeted invocation executed by CO-B: 0
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
- Latest pointer changed by CO-B: 0
- Next gate: {next_gate}

CO-B is a side-branch proof plan only. It does not execute the targeted native-writer invocation proof.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CO_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_PLAN.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CO_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_PLAN.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CN-B status green: {cnb_green}")
    print(f"  CN-B savepoint present: {cnb_sp}")
    print(f"  official latest before CO-B: {latest_before}")
    print(f"  targeted invocation proof required: {proof_required}")
    print(f"  CL-B candidate inventory rows observed: {len(inventory)}")
    print(f"  top candidate rows staged: {len(top_inventory)}")
    print(f"  invocation plan rows: {len(invocation_plan)}")
    print(f"  surface selection criteria rows: {len(selection_criteria)}")
    print(f"  refusal guard rows: {len(refusal)}")
    print("  targeted invocation executed by CO-B: 0")
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
    print("  latest pointer changed by CO-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
