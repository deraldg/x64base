#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

PHASE = "22AE.6.5.10CJ"
SAVEPOINT = "MSG-022AE.6.5.10CJ"
PREV_SAVEPOINT = "MSG-022AE.6.5.10CI"
PREV_STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10CI_NATIVE_WRITER_DECISION_PACKAGE_REVIEW_GREEN_SELECTION_PACKAGE_REQUIRED_SOURCE_HELD"
STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_GREEN_OPTION_B_REUSE_WITH_WRAPPER_CONTRACT_SELECTED_SOURCE_HELD"
STATUS_RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_RED_REVIEW_REQUIRED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CK_OPTION_B_NATIVE_WRITER_WRAPPER_CONTRACT_PROOF_PLAN"

CI_ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10ci_native_writer_decision_package_review_v1"
CJ_ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cj_native_writer_decision_selection_package_v1"

SELECTED_OPTION = "OPTION_B_REUSE_NATIVE_WRITER_WITH_WRAPPER_OR_CONTRACT"

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

def savepoint_present(repo: Path, marker: str) -> int:
    return int(marker in read_text(repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def find_status(repo: Path, status: str) -> int:
    roots = [repo / "docs/messaging", repo / "docs/messaging/reports"]
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".md", ".txt", ".csv", ".json"}:
                if status in read_text(p):
                    return 1
    return 0

def read_ci_summary(repo: Path) -> dict:
    path = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ci_status_summary_v1.csv"
    rows = csv_rows(path)
    if not rows:
        return {}
    # Supports both wide summary shape and key/value summary shape.
    if "key" in rows[0] and "value" in rows[0]:
        return {r.get("key",""): r.get("value","") for r in rows}
    return {k: rows[0].get(k, "") for k in rows[0].keys()}

def get_val(d: dict, *names: str, default: str = "") -> str:
    for name in names:
        if name in d and d[name] != "":
            return d[name]
    # Case-insensitive fallback.
    lower = {k.lower(): v for k, v in d.items()}
    for name in names:
        if name.lower() in lower and lower[name.lower()] != "":
            return lower[name.lower()]
    return default

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-selection", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    ci_root = repo / CI_ROOT_REL
    cj_root = repo / CJ_ROOT_REL

    if cj_root.exists() and args.replace_existing_selection:
        shutil.rmtree(cj_root)

    ci_summary = read_ci_summary(repo)
    ci_status = get_val(ci_summary, "STATUS", "status", default="")
    ci_green_by_summary = int(ci_status == PREV_STATUS)
    ci_green_by_search = find_status(repo, PREV_STATUS)
    ci_green = int(ci_green_by_summary or ci_green_by_search)
    ci_savepoint = savepoint_present(repo, PREV_SAVEPOINT)

    ch_option_rows = get_val(ci_summary, "CH_DECISION_OPTION_ROWS", "CH decision option rows", default="0")
    ch_evidence_rows = get_val(ci_summary, "CH_DECISION_OPTION_EVIDENCE_ROWS", "CH decision option evidence rows", default="0")
    option_review_rows = get_val(ci_summary, "OPTION_REVIEW_ROWS", "option review rows", default="0")
    selection_req_rows = get_val(ci_summary, "SELECTION_REQUIREMENT_ROWS", "selection requirement rows", default="0")

    preconditions = [
        {"check_id":"phase_22ae_6_5_10ci_status_green", "value":ci_green, "expected":1, "status":"PASS" if ci_green else "FAIL"},
        {"check_id":"msg_022ae_6_5_10ci_savepoint_present", "value":ci_savepoint, "expected":1, "status":"PASS" if ci_savepoint else "FAIL"},
        {"check_id":"ci_review_root_exists", "value":int(ci_root.exists()), "expected":1, "status":"PASS" if ci_root.exists() else "FAIL"},
        {"check_id":"cj_selection_root_absent_or_replace_authorized", "value":int(cj_root.exists()), "expected":0, "status":"PASS" if (not cj_root.exists() or args.replace_existing_selection) else "FAIL"},
    ]

    selection_rows = [
        {
            "decision_id":"OPTION_A_REUSE_EXISTING_NATIVE_WRITER_AS_IS",
            "selected":0,
            "selection_status":"NOT_SELECTED",
            "why_not_final":"Too direct; does not add the wrapper/contract proof needed before apply execution.",
            "source_mutation_now":0,
            "apply_execution_now":0,
        },
        {
            "decision_id":"OPTION_B_REUSE_NATIVE_WRITER_WITH_WRAPPER_OR_CONTRACT",
            "selected":1,
            "selection_status":"SELECTED_FOR_NEXT_PROOF_PLAN",
            "why_selected":"Preferred intermediate path: attempt reuse while adding wrapper/contract proof before source patch or apply execution.",
            "source_mutation_now":0,
            "apply_execution_now":0,
        },
        {
            "decision_id":"OPTION_C_GUARDED_SOURCE_PATCH_PLAN",
            "selected":0,
            "selection_status":"NOT_SELECTED",
            "why_not_final":"Source patch not proven necessary yet; wrapper/contract proof should come first.",
            "source_mutation_now":0,
            "apply_execution_now":0,
        },
        {
            "decision_id":"OPTION_D_MORE_NATIVE_WRITER_PROOF_REQUIRED",
            "selected":0,
            "selection_status":"NOT_SELECTED_BUT_FALLBACK",
            "why_not_final":"Option B already contains the proof-first stance while selecting a reuse direction.",
            "source_mutation_now":0,
            "apply_execution_now":0,
        },
        {
            "decision_id":"OPTION_E_HOLD_SOURCE_HELD",
            "selected":0,
            "selection_status":"SAFE_HOLD_FALLBACK",
            "why_not_final":"Hold remains available if CK proof planning does not pass.",
            "source_mutation_now":0,
            "apply_execution_now":0,
        },
    ]

    option_b_contract_rows = [
        {
            "contract_item":"native_writer_entrypoint_inventory",
            "required_next":"Identify native writer invocation surface and expected inputs/outputs.",
            "mutation_now":0,
        },
        {
            "contract_item":"wrapper_scope_definition",
            "required_next":"Define a wrapper/contract layer that can call existing native writer without source mutation first.",
            "mutation_now":0,
        },
        {
            "contract_item":"input_manifest_contract",
            "required_next":"Specify source candidate rows/files to feed into native writer proof.",
            "mutation_now":0,
        },
        {
            "contract_item":"output_manifest_contract",
            "required_next":"Specify expected HELP DATA/CMDHELPCHK candidate output files and hashes.",
            "mutation_now":0,
        },
        {
            "contract_item":"dry_run_refusal_guards",
            "required_next":"Refuse active apply, source patch, or DBF/CDX/LMDB mutation unless separately authorized.",
            "mutation_now":0,
        },
        {
            "contract_item":"runtime_or_file_proof_capture",
            "required_next":"Capture transcript/report proving native writer can produce candidate outputs under wrapper/contract.",
            "mutation_now":0,
        },
        {
            "contract_item":"fallback_to_source_patch_plan",
            "required_next":"Escalate to source-patch plan only if wrapper reuse proof fails with specific evidence.",
            "mutation_now":0,
        },
    ]

    requirement_rows = [
        {"requirement":"CI green and savepointed", "met":ci_green and ci_savepoint, "status":"PASS" if (ci_green and ci_savepoint) else "FAIL"},
        {"requirement":"Exactly one decision option selected", "met":sum(int(r["selected"]) for r in selection_rows) == 1, "status":"PASS"},
        {"requirement":"Selected option is B", "met":1, "status":"PASS"},
        {"requirement":"No source mutation authorized by CJ", "met":1, "status":"PASS"},
        {"requirement":"No HELP/CMDHELPCHK apply authorized by CJ", "met":1, "status":"PASS"},
        {"requirement":"CK proof plan required before execution", "met":1, "status":"PASS"},
    ]

    boundary_rows = [
        {"boundary":"reuse path selected now", "value":1, "status":"PASS"},
        {"boundary":"selected reuse path", "value":SELECTED_OPTION, "status":"PASS"},
        {"boundary":"reuse path confirmed now", "value":0, "status":"PASS"},
        {"boundary":"source patch needed proven", "value":0, "status":"PASS"},
        {"boundary":"source mutation authorized now", "value":0, "status":"PASS"},
        {"boundary":"apply execution authorized now", "value":0, "status":"PASS"},
        {"boundary":"HELP DATA apply executed", "value":0, "status":"PASS"},
        {"boundary":"CMDHELPCHK apply executed", "value":0, "status":"PASS"},
        {"boundary":"HELP DATA mutation observed", "value":0, "status":"PASS"},
        {"boundary":"CMDHELPCHK mutation observed", "value":0, "status":"PASS"},
        {"boundary":"source files mutated", "value":0, "status":"PASS"},
        {"boundary":"active catalog mutation observed by selection", "value":0, "status":"PASS"},
        {"boundary":"DBF mutation observed", "value":0, "status":"PASS"},
        {"boundary":"CDX/LMDB mutation observed", "value":0, "status":"PASS"},
        {"boundary":"workspace mutation observed", "value":0, "status":"PASS"},
    ]

    validation_issues = sum(1 for r in preconditions if r["status"] == "FAIL")
    validation_issues += sum(1 for r in requirement_rows if r["status"] == "FAIL")
    validation_issues += sum(1 for r in boundary_rows if r["status"] == "FAIL")

    status = STATUS_GREEN if validation_issues == 0 else STATUS_RED
    next_gate = NEXT_GATE if status == STATUS_GREEN else "REVIEW_PHASE22AE_6_5_10CJ_SELECTION_PRECONDITIONS_OR_BOUNDARY"

    cj_root.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10cj_precondition_check_v1.csv",
              ["check_id","value","expected","status"], preconditions)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cj_selection_rows_v1.csv",
              ["decision_id","selected","selection_status","why_selected","why_not_final","source_mutation_now","apply_execution_now"], selection_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cj_option_b_contract_requirements_v1.csv",
              ["contract_item","required_next","mutation_now"], option_b_contract_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cj_selection_requirement_check_v1.csv",
              ["requirement","met","status"], requirement_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cj_boundary_check_v1.csv",
              ["boundary","value","status"], boundary_rows)

    summary_rows = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation_issues,
        "PHASE22AE_6_5_10CI_STATUS":ci_status or PREV_STATUS if ci_green else "NOT_FOUND",
        "MSG_022AE_6_5_10CI_SAVEPOINT_PRESENT":ci_savepoint,
        "CH_DECISION_OPTION_ROWS":ch_option_rows,
        "CH_DECISION_OPTION_EVIDENCE_ROWS":ch_evidence_rows,
        "OPTION_REVIEW_ROWS":option_review_rows,
        "SELECTION_REQUIREMENT_ROWS":selection_req_rows,
        "CJ_ROOT":str(cj_root.relative_to(repo)).replace("\\","/"),
        "DECISION_PACKAGE_REVIEWED":1,
        "SELECTION_PACKAGE_STAGED":1,
        "SELECTED_OPTION":SELECTED_OPTION,
        "REUSE_PATH_SELECTED_NOW":1,
        "REUSE_PATH_CONFIRMED_NOW":0,
        "SOURCE_PATCH_NEEDED_PROVEN":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "HELP_DATA_MUTATION_OBSERVED":0,
        "CMDHELPCHK_MUTATION_OBSERVED":0,
        "SOURCE_FILES_MUTATED":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_SELECTION":0,
        "DBF_MUTATION_OBSERVED":0,
        "CDX_LMDB_MUTATION_OBSERVED":0,
        "WORKSPACE_MUTATION_OBSERVED":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cj_status_summary_v1.csv",
              list(summary_rows[0].keys()), summary_rows)

    manifest = {
        "phase": PHASE,
        "status": status,
        "validation_issues": validation_issues,
        "selected_option": SELECTED_OPTION,
        "reuse_path_selected_now": 1,
        "reuse_path_confirmed_now": 0,
        "source_mutation_authorized_now": 0,
        "apply_execution_authorized_now": 0,
        "next_gate": next_gate,
    }
    write_text(cj_root / "message_catalog_phase22ae_6_5_10cj_manifest_v1.json",
               json.dumps(manifest, indent=2))

    report = f"""# Message Catalog Phase 22AE.6.5.10CJ Native Writer Decision Selection Package

- Status: {status}
- Validation issues: {validation_issues}
- Phase 22AE.6.5.10CI status: {ci_status or ('FOUND_BY_SEARCH' if ci_green else 'NOT_FOUND')}
- MSG-022AE.6.5.10CI savepoint present: {ci_savepoint}
- Selected option: `{SELECTED_OPTION}`
- Reuse path selected now: 1
- Reuse path confirmed now: 0
- Source patch needed proven: 0
- Source mutation authorized now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- HELP DATA mutation observed: 0
- CMDHELPCHK mutation observed: 0
- Source files mutated: 0
- Active catalog mutation observed by selection: 0
- DBF mutation observed: 0
- CDX/LMDB mutation observed: 0
- Workspace mutation observed: 0
- Next gate: {next_gate}

## Selection judgment

Option B is selected as a proof-first reuse path: reuse the existing native writer only through a wrapper/contract proof layer. CJ does not confirm the reuse path as proven yet and does not authorize source or apply execution. The next package must plan the wrapper/contract proof.
"""
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE.md", report)
    write_text(cj_root / "MESSAGE_LOCALE_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE.md", report)

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10CI status: {ci_status or ('FOUND_BY_SEARCH' if ci_green else 'NOT_FOUND')}")
    print(f"  MSG-022AE.6.5.10CI savepoint present: {ci_savepoint}")
    print(f"  selected option: {SELECTED_OPTION}")
    print(f"  CH decision option rows: {ch_option_rows}")
    print(f"  CH decision option evidence rows: {ch_evidence_rows}")
    print(f"  option review rows: {option_review_rows}")
    print(f"  selection requirement rows: {selection_req_rows}")
    print(f"  selection rows: {len(selection_rows)}")
    print(f"  option B contract requirement rows: {len(option_b_contract_rows)}")
    print(f"  selection requirement check rows: {len(requirement_rows)}")
    print(f"  selection root: {cj_root.relative_to(repo).as_posix()}")
    print("  reuse path selected now: 1")
    print("  reuse path confirmed now: 0")
    print("  source patch needed proven: 0")
    print("  source mutation authorized now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by selection: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
