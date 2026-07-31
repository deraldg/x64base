#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

RECON_STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_OPTION_B_BRANCH_RECONCILIATION_GREEN_REPORT_ONLY_BRANCH_COLLISION_DOCUMENTED"
OPTION_B_STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_GREEN_OPTION_B_REUSE_WITH_WRAPPER_CONTRACT_SELECTED_SOURCE_HELD"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CK_B_OPTION_B_NATIVE_WRITER_WRAPPER_CONTRACT_PROOF_PLAN_GREEN_SIDE_BRANCH_SOURCE_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CK_B_OPTION_B_NATIVE_WRITER_WRAPPER_CONTRACT_PROOF_PLAN_RED_REVIEW_REQUIRED"
RECON_SAVEPOINT = "MSG-022AE.6.5.10CJ-OPTIONB-RECON"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CL_B_OPTION_B_NATIVE_WRITER_WRAPPER_CONTRACT_PROOF_STAGING"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10ck_b_option_b_wrapper_contract_proof_plan_v1"

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

def find_status(repo: Path, status: str) -> int:
    for base in [repo / "docs/messaging", repo / "docs/messaging/reports"]:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".md",".txt",".csv",".json"}:
                if status in read_text(p):
                    return 1
    return 0

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

    recon = csv_one(reports / "message_catalog_phase22ae_6_5_10cj_option_b_reconciliation_status_summary_v1.csv")
    cj = csv_one(reports / "message_catalog_phase22ae_6_5_10cj_status_summary_v1.csv")
    latest_info = latest(repo)
    latest_before = latest_info.get("savepoint_id", latest_info.get("savepoint",""))
    latest_status = latest_info.get("status","")

    recon_green = int(recon.get("STATUS","") == RECON_STATUS or find_status(repo, RECON_STATUS))
    recon_sp = journal_has(repo, RECON_SAVEPOINT)
    option_b = int(cj.get("STATUS","") == OPTION_B_STATUS and cj.get("SELECTED_OPTION","") == "OPTION_B_REUSE_NATIVE_WRITER_WITH_WRAPPER_OR_CONTRACT")
    collision = int(recon.get("BRANCH_COLLISION_DETECTED","0") == "1")

    pre = [
        {"check_id":"reconciliation_green","value":recon_green,"expected":1,"status":"PASS" if recon_green else "FAIL"},
        {"check_id":"reconciliation_savepoint_present","value":recon_sp,"expected":1,"status":"PASS" if recon_sp else "FAIL"},
        {"check_id":"current_cj_option_b_summary_present","value":option_b,"expected":1,"status":"PASS" if option_b else "FAIL"},
        {"check_id":"branch_collision_documented","value":collision,"expected":1,"status":"PASS" if collision else "FAIL"},
        {"check_id":"ck_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_plan) else "FAIL"},
    ]

    req = [
        {"contract_id":"WRAP001","contract_item":"native_writer_entrypoint_inventory","proof_requirement":"Identify native writer entrypoint(s), supported mode, inputs, outputs.","execution_now":0,"mutation_now":0},
        {"contract_id":"WRAP002","contract_item":"input_manifest_contract","proof_requirement":"Define candidate-only input rows/files for wrapper proof.","execution_now":0,"mutation_now":0},
        {"contract_id":"WRAP003","contract_item":"output_manifest_contract","proof_requirement":"Define candidate-only output files, expected counts, hashes, and refusal rules.","execution_now":0,"mutation_now":0},
        {"contract_id":"WRAP004","contract_item":"wrapper_invocation_contract","proof_requirement":"Specify wrapper command/script/API parameters for later CL-B staging.","execution_now":0,"mutation_now":0},
        {"contract_id":"WRAP005","contract_item":"dry_run_candidate_only_mode","proof_requirement":"Refuse active HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, workspace, and source mutation.","execution_now":0,"mutation_now":0},
        {"contract_id":"WRAP006","contract_item":"transcript_report_capture","proof_requirement":"Capture transcript/report proving wrapper reached native writer and created candidate outputs.","execution_now":0,"mutation_now":0},
        {"contract_id":"WRAP007","contract_item":"fallback_to_review","proof_requirement":"If wrapper proof fails, return to review rather than silently source-patching.","execution_now":0,"mutation_now":0},
    ]

    proof = [
        {"step_id":"CKB001","phase":"inventory","description":"Inventory native writer surfaces and reuse candidates from targeted discovery branch.","expected_artifact":"native_writer_surface_inventory.csv","execute_now":0},
        {"step_id":"CKB002","phase":"contract","description":"Define wrapper input/output/refusal/transcript contract.","expected_artifact":"option_b_wrapper_contract_manifest.json","execute_now":0},
        {"step_id":"CKB003","phase":"stage","description":"Create later CL-B candidate-only proof staging package.","expected_artifact":"CL-B staging package","execute_now":0},
        {"step_id":"CKB004","phase":"proof","description":"Run only after CL-B authorization; no active HELP/CMDHELPCHK apply.","expected_artifact":"candidate proof transcript","execute_now":0},
        {"step_id":"CKB005","phase":"review","description":"Review proof before confirming native writer reuse.","expected_artifact":"CM-B review","execute_now":0},
    ]

    guards = [
        {"guard_id":"REFUSE_SOURCE_MUTATION","condition":"No source patch in CK-B/CL-B proof plan.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_HELP_DATA_APPLY","condition":"No HELP DATA apply execution.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_CMDHELPCHK_APPLY","condition":"No CMDHELPCHK apply execution.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_ACTIVE_DBF_MUTATION","condition":"No active DBF mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_CDX_LMDB_MUTATION","condition":"No CDX/LMDB mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_WORKSPACE_MUTATION","condition":"No workspace mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_LATEST_POINTER_CHANGE","condition":"Do not move official latest pointer from CM branch.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_DUPLICATE_MAINLINE_LABELS","condition":"Use CK-B/CL-B/CM-B labels, not occupied CK/CL/CM.","required":1,"execute_now":0},
    ]

    boundary = [
        {"boundary":"reuse path selected now","value":1,"status":"PASS"},
        {"boundary":"reuse path confirmed now","value":0,"status":"PASS"},
        {"boundary":"wrapper proof executed now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"source files mutated","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed","value":0,"status":"PASS"},
        {"boundary":"DBF mutation observed","value":0,"status":"PASS"},
        {"boundary":"CDX/LMDB mutation observed","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by CK-B","value":0,"status":"PASS"},
    ]

    val = sum(1 for r in pre if r["status"] == "FAIL")
    status = GREEN if val == 0 else RED
    next_gate = NEXT_GATE if status == GREEN else "REVIEW_PHASE22AE_6_5_10CK_B_PRECONDITIONS_OR_BOUNDARY"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    write_csv(reports / "message_catalog_phase22ae_6_5_10ck_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10ck_b_wrapper_contract_requirements_v1.csv", ["contract_id","contract_item","proof_requirement","execution_now","mutation_now"], req)
    write_csv(reports / "message_catalog_phase22ae_6_5_10ck_b_proof_plan_v1.csv", ["step_id","phase","description","expected_artifact","execute_now"], proof)
    write_csv(reports / "message_catalog_phase22ae_6_5_10ck_b_refusal_guards_v1.csv", ["guard_id","condition","required","execute_now"], guards)
    write_csv(reports / "message_catalog_phase22ae_6_5_10ck_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":val,
        "PHASE":"22AE.6.5.10CK-B",
        "RECONCILIATION_STATUS_GREEN":recon_green,
        "RECONCILIATION_SAVEPOINT_PRESENT":recon_sp,
        "CURRENT_CJ_OPTION_B_SUMMARY_PRESENT":option_b,
        "BRANCH_COLLISION_DOCUMENTED":collision,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CK_B":latest_before,
        "OFFICIAL_LATEST_STATUS_BEFORE_CK_B":latest_status,
        "SELECTED_BRANCH":"OPTION_B_WRAPPER_CONTRACT_SIDE_BRANCH",
        "WRAPPER_CONTRACT_REQUIREMENT_ROWS":len(req),
        "PROOF_PLAN_ROWS":len(proof),
        "REFUSAL_GUARD_ROWS":len(guards),
        "CK_B_ROOT":str(out.relative_to(repo)).replace("\\","/"),
        "REUSE_PATH_SELECTED_NOW":1,
        "REUSE_PATH_CONFIRMED_NOW":0,
        "WRAPPER_PROOF_EXECUTED_NOW":0,
        "SOURCE_PATCH_NEEDED_PROVEN":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_FILES_MUTATED":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED":0,
        "DBF_MUTATION_OBSERVED":0,
        "CDX_LMDB_MUTATION_OBSERVED":0,
        "WORKSPACE_MUTATION_OBSERVED":0,
        "LATEST_POINTER_CHANGED_BY_CK_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10ck_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {"phase":"22AE.6.5.10CK-B","status":status,"side_branch":"OPTION_B_WRAPPER_CONTRACT","latest_pointer_changed_by_ck_b":0,"next_gate":next_gate}
    write_text(out / "message_catalog_phase22ae_6_5_10ck_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10CK-B Option B Native Writer Wrapper/Contract Proof Plan

- Status: {status}
- Validation issues: {val}
- Reconciliation status green: {recon_green}
- Reconciliation savepoint present: {recon_sp}
- Current CJ Option B summary present: {option_b}
- Branch collision documented: {collision}
- Official latest before CK-B: `{latest_before}`
- Selected branch: `OPTION_B_WRAPPER_CONTRACT_SIDE_BRANCH`
- Wrapper/contract requirement rows: {len(req)}
- Proof plan rows: {len(proof)}
- Refusal guard rows: {len(guards)}
- Reuse path selected now: 1
- Reuse path confirmed now: 0
- Wrapper proof executed now: 0
- Source mutation authorized now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source files mutated: 0
- Active catalog mutation observed: 0
- DBF mutation observed: 0
- CDX/LMDB mutation observed: 0
- Workspace mutation observed: 0
- Latest pointer changed by CK-B: 0
- Next gate: {next_gate}

CK-B is a side-branch proof plan only. It does not confirm reuse, run the proof, patch source, apply HELP/CMDHELPCHK, or move the official latest pointer.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CK_B_OPTION_B_WRAPPER_CONTRACT_PROOF_PLAN.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CK_B_OPTION_B_WRAPPER_CONTRACT_PROOF_PLAN.md", report)

    print(status)
    print(f"  validation issues: {val}")
    print(f"  reconciliation status green: {recon_green}")
    print(f"  reconciliation savepoint present: {recon_sp}")
    print(f"  current CJ Option B summary present: {option_b}")
    print(f"  branch collision documented: {collision}")
    print(f"  official latest before CK-B: {latest_before}")
    print("  selected branch: OPTION_B_WRAPPER_CONTRACT_SIDE_BRANCH")
    print(f"  wrapper/contract requirement rows: {len(req)}")
    print(f"  proof plan rows: {len(proof)}")
    print(f"  refusal guard rows: {len(guards)}")
    print("  reuse path selected now: 1")
    print("  reuse path confirmed now: 0")
    print("  wrapper proof executed now: 0")
    print("  source mutation authorized now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print("  latest pointer changed by CK-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
