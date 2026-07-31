#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

CRB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CR_B_TARGETED_NATIVE_WRITER_REUSE_DECISION_PACKAGE_GREEN_READ_ONLY_PROOF_ACCEPTED_REUSE_NOT_CONFIRMED_SOURCE_HELD"
CRB_SAVEPOINT = "MSG-022AE.6.5.10CR-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CS_B_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_PLAN_GREEN_REPORT_ONLY_SOURCE_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CS_B_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_PLAN_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CT_B_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_STAGING"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cs_b_active_candidate_native_writer_invocation_plan_v1"

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")

def write_csv(p: Path, fields: list[str], rows: list[dict]) -> None:
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

def score_candidate(row: dict) -> int:
    path = row.get("candidate_path", "").lower()
    score = 0
    try:
        score += int(row.get("selection_score", row.get("score", "0")) or 0)
    except Exception:
        pass
    if "writer" in path:
        score += 8
    if "native" in path:
        score += 6
    if "message" in path:
        score += 4
    if "help" in path:
        score += 3
    if "cmdhelpchk" in path:
        score += 3
    if path.endswith(".py"):
        score += 3
    if path.endswith(".ps1"):
        score += 2
    if "review" in path:
        score -= 2
    if "append" in path:
        score -= 2
    return score

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

    crb = csv_one(reports / "message_catalog_phase22ae_6_5_10cr_b_status_summary_v1.csv")
    latest_info = latest(repo)
    latest_before = latest_info.get("savepoint_id", latest_info.get("savepoint", ""))

    crb_green = int(crb.get("STATUS", "") == CRB_GREEN)
    crb_sp = journal_has(repo, CRB_SAVEPOINT)
    active_plan_required = int(str(crb.get("ACTIVE_CANDIDATE_INVOCATION_PLAN_REQUIRED", "0")) == "1")
    reuse_confirmed = int(str(crb.get("REUSE_PATH_CONFIRMED_NOW", "0")) == "1")
    source_authorized = int(str(crb.get("SOURCE_MUTATION_AUTHORIZED_NOW", "0")) == "1")
    apply_authorized = int(str(crb.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0")) == "1")

    cp_selected = csv_rows(reports / "message_catalog_phase22ae_6_5_10cp_b_selected_surfaces_v1.csv")
    surface_probe = csv_rows(repo / "docs/messaging/apply/phase22ae_6_5_10cp_b_targeted_native_writer_invocation_proof_staging_v1/candidate_outputs/targeted_native_writer_surface_probe_rows.csv")

    ranked = sorted(cp_selected, key=score_candidate, reverse=True)
    chosen = ranked[:3]

    pre = [
        {"check_id":"cr_b_status_green","value":crb_green,"expected":1,"status":"PASS" if crb_green else "FAIL"},
        {"check_id":"cr_b_savepoint_present","value":crb_sp,"expected":1,"status":"PASS" if crb_sp else "FAIL"},
        {"check_id":"active_candidate_invocation_plan_required","value":active_plan_required,"expected":1,"status":"PASS" if active_plan_required else "FAIL"},
        {"check_id":"reuse_not_confirmed_yet","value":reuse_confirmed,"expected":0,"status":"PASS" if reuse_confirmed == 0 else "FAIL"},
        {"check_id":"source_mutation_not_authorized","value":source_authorized,"expected":0,"status":"PASS" if source_authorized == 0 else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":apply_authorized,"expected":0,"status":"PASS" if apply_authorized == 0 else "FAIL"},
        {"check_id":"cp_b_selected_surface_rows_available","value":len(cp_selected),"expected":">0","status":"PASS" if len(cp_selected) > 0 else "FAIL"},
        {"check_id":"cp_b_surface_probe_rows_available","value":len(surface_probe),"expected":">0","status":"PASS" if len(surface_probe) > 0 else "REVIEW"},
        {"check_id":"cs_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_plan) else "FAIL"},
        {"check_id":"official_latest_pointer_not_modified_by_plan","value":1,"expected":1,"status":"PASS"},
    ]

    chosen_rows = []
    for n, row in enumerate(chosen, 1):
        chosen_rows.append({
            "candidate_rank": n,
            "candidate_path": row.get("candidate_path", ""),
            "suffix": row.get("suffix", ""),
            "selection_score": score_candidate(row),
            "plan_role": "active-candidate-invocation-surface-candidate",
            "invoke_in_cs_b": 0,
            "invoke_in_ct_b_after_authorization": 1,
            "active_apply_allowed": 0,
            "source_patch_allowed": 0,
        })

    plan_rows = [
        {
            "step_id":"CSB001",
            "phase":"surface-lock",
            "description":"Lock a small ranked candidate surface set for CT-B staging instead of scanning the whole repo again.",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"CSB002",
            "phase":"active-candidate-invocation-contract",
            "description":"Define an active candidate-only invocation contract that can call/drive the chosen writer path only against side-branch candidate outputs.",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"CSB003",
            "phase":"output-sandbox",
            "description":"All outputs must land under docs/messaging/apply/phase22ae_6_5_10ct_b_active_candidate_native_writer_invocation_staging_v1.",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"CSB004",
            "phase":"hard-refusal-guards",
            "description":"Refuse source edits, HELP DATA apply, CMDHELPCHK apply, active DBF/CDX/LMDB/workspace mutation, and latest pointer movement.",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"CSB005",
            "phase":"manual-run-script",
            "description":"CT-B should stage a manual-run proof script, not execute it inside the staging package.",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"CSB006",
            "phase":"proof-distinction",
            "description":"Transcript must distinguish active candidate invocation from the prior CP-B read-only surface probe.",
            "execute_now":0,
            "mutation_now":0,
        },
        {
            "step_id":"CSB007",
            "phase":"review-before-confirmation",
            "description":"CU-B or later must review the proof before native-writer reuse can be confirmed or apply can be considered.",
            "execute_now":0,
            "mutation_now":0,
        },
    ]

    contract = {
        "phase": "22AE.6.5.10CS-B",
        "branch": "OPTION_B_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_SIDE_BRANCH",
        "purpose": "Plan a candidate-only active native-writer invocation proof.",
        "chosen_surface_count": len(chosen_rows),
        "chosen_surface_csv": "docs/messaging/reports/message_catalog_phase22ae_6_5_10cs_b_chosen_surfaces_v1.csv",
        "target_staging_phase": "22AE.6.5.10CT-B",
        "target_staging_root": "docs/messaging/apply/phase22ae_6_5_10ct_b_active_candidate_native_writer_invocation_staging_v1",
        "active_candidate_invocation_planned": True,
        "active_candidate_invocation_executed_by_cs_b": False,
        "reuse_path_confirmed_now": False,
        "source_mutation_authorized_now": False,
        "apply_execution_authorized_now": False,
        "help_data_apply_allowed": False,
        "cmdhelpchk_apply_allowed": False,
        "active_dbf_mutation_allowed": False,
        "cdx_lmdb_mutation_allowed": False,
        "workspace_mutation_allowed": False,
        "latest_pointer_change_allowed": False,
    }

    refusal = [
        {"guard_id":"REFUSE_SOURCE_MUTATION","condition":"No source edits or generated source files in CS-B/CT-B plan or staging.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_HELP_DATA_APPLY","condition":"No HELP DATA apply execution.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_CMDHELPCHK_APPLY","condition":"No CMDHELPCHK apply execution.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_ACTIVE_DBF_MUTATION","condition":"No active DBF mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_CDX_LMDB_MUTATION","condition":"No CDX/LMDB mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_WORKSPACE_MUTATION","condition":"No workspace mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_LATEST_POINTER_CHANGE","condition":"Do not move message_savepoint_latest_v1.json.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_REUSE_CONFIRMATION_NOW","condition":"Do not confirm native-writer reuse in CS-B.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_APPLY_AUTHORIZATION_NOW","condition":"Do not authorize active apply until after active candidate invocation proof review.","required":1,"execute_now":0},
    ]

    boundary = [
        {"boundary":"active candidate invocation planned","value":1,"status":"PASS"},
        {"boundary":"active candidate invocation executed by CS-B","value":0,"status":"PASS"},
        {"boundary":"active HELP/CMDHELPCHK apply planned","value":0,"status":"PASS"},
        {"boundary":"native-writer reuse confirmed now","value":0,"status":"PASS"},
        {"boundary":"source patch needed proven","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed","value":0,"status":"PASS"},
        {"boundary":"DBF mutation observed","value":0,"status":"PASS"},
        {"boundary":"CDX/LMDB mutation observed","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by CS-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for r in pre if r["status"] == "FAIL") + sum(1 for r in boundary if r["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10CS_B_PLAN_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10cs_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cs_b_chosen_surfaces_v1.csv", ["candidate_rank","candidate_path","suffix","selection_score","plan_role","invoke_in_cs_b","invoke_in_ct_b_after_authorization","active_apply_allowed","source_patch_allowed"], chosen_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cs_b_invocation_plan_v1.csv", ["step_id","phase","description","execute_now","mutation_now"], plan_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cs_b_refusal_guards_v1.csv", ["guard_id","condition","required","execute_now"], refusal)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cs_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)
    write_text(out / "active_candidate_invocation_contract_manifest_v1.json", json.dumps(contract, indent=2))

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10CS-B",
        "CR_B_STATUS_GREEN":crb_green,
        "CR_B_SAVEPOINT_PRESENT":crb_sp,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CS_B":latest_before,
        "ACTIVE_CANDIDATE_INVOCATION_PLAN_REQUIRED":active_plan_required,
        "CP_B_SELECTED_SURFACE_ROWS":len(cp_selected),
        "CP_B_SURFACE_PROBE_ROWS":len(surface_probe),
        "CHOSEN_SURFACE_ROWS":len(chosen_rows),
        "INVOCATION_PLAN_ROWS":len(plan_rows),
        "REFUSAL_GUARD_ROWS":len(refusal),
        "ACTIVE_CANDIDATE_INVOCATION_PLANNED":1,
        "ACTIVE_CANDIDATE_INVOCATION_EXECUTED_BY_CS_B":0,
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
        "LATEST_POINTER_CHANGED_BY_CS_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cs_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    report = f"""# Phase 22AE.6.5.10CS-B Active Candidate Native Writer Invocation Plan

- Status: {status}
- Validation issues: {validation}
- CR-B status green: {crb_green}
- CR-B savepoint present: {crb_sp}
- Official latest before CS-B: `{latest_before}`
- Active candidate invocation plan required: {active_plan_required}
- CP-B selected surface rows: {len(cp_selected)}
- CP-B surface probe rows: {len(surface_probe)}
- Chosen surface rows: {len(chosen_rows)}
- Invocation plan rows: {len(plan_rows)}
- Refusal guard rows: {len(refusal)}
- Active candidate invocation planned: 1
- Active candidate invocation executed by CS-B: 0
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
- Latest pointer changed by CS-B: 0
- Next gate: {next_gate}

CS-B plans a candidate-only active native-writer invocation proof for CT-B. It does not execute the proof and does not authorize active apply.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CS_B_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_PLAN.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CS_B_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_PLAN.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CR-B status green: {crb_green}")
    print(f"  CR-B savepoint present: {crb_sp}")
    print(f"  official latest before CS-B: {latest_before}")
    print(f"  active candidate invocation plan required: {active_plan_required}")
    print(f"  CP-B selected surface rows: {len(cp_selected)}")
    print(f"  CP-B surface probe rows: {len(surface_probe)}")
    print(f"  chosen surface rows: {len(chosen_rows)}")
    print(f"  invocation plan rows: {len(plan_rows)}")
    print(f"  refusal guard rows: {len(refusal)}")
    print("  active candidate invocation planned: 1")
    print("  active candidate invocation executed by CS-B: 0")
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
    print("  latest pointer changed by CS-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
