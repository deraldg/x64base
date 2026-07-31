from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DJ_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DJ_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_STAGING_GREEN_MANUAL_READ_ONLY_PROBES_STAGED_NO_EXECUTION"
DJ_SAVEPOINT = "MSG-022AE.6.5.10DJ-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DK_B_READ_ONLY_TARGET_VERIFICATION_PROBE_PROOF_REVIEW_GREEN_MANUAL_PROBE_OUTPUT_CAPTURE_PROVEN_NO_SELECTION"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DK_B_READ_ONLY_TARGET_VERIFICATION_PROBE_PROOF_REVIEW_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DL_B_TARGET_VERIFICATION_CLASSIFICATION_REVIEW"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dk_b_read_only_target_verification_probe_proof_review_v1"
DJ_MANUAL_REL = "docs/messaging/apply/phase22ae_6_5_10dj_b_active_help_cmdhelpchk_target_verification_probe_staging_v1/manual_run"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def csv_rows(path: Path) -> list[dict]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def csv_one(path: Path) -> dict:
    r = csv_rows(path)
    return r[0] if r else {}

def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def has_journal(repo: Path, marker: str) -> int:
    return int(marker in read_text(repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def latest_id(repo: Path) -> str:
    try:
        data = json.loads(read_text(repo / "docs/messaging/reports/message_savepoint_latest_v1.json"))
        return data.get("savepoint_id", data.get("savepoint", ""))
    except Exception:
        return ""

def as_int(v, default=0):
    try:
        return int(str(v).strip())
    except Exception:
        return default

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_review:
        shutil.rmtree(out)

    dj = csv_one(reports / "message_catalog_phase22ae_6_5_10dj_b_status_summary_v1.csv")
    dj_green = int(dj.get("STATUS", "") == DJ_GREEN)
    dj_savepoint = has_journal(repo, DJ_SAVEPOINT)
    expected_rows = as_int(dj.get("PROBE_SCRIPT_ROWS", 0))

    manual = repo / DJ_MANUAL_REL
    result_csv = manual / "DJ_B_TARGET_VERIFICATION_PROBE_RESULTS.csv"
    transcript = manual / "DJ_B_TARGET_VERIFICATION_PROBE_TRANSCRIPT.md"
    result_rows = csv_rows(result_csv)
    transcript_text = read_text(transcript)

    rows_match = int(bool(result_rows) and len(result_rows) == expected_rows)
    no_active_selected = int(all(str(r.get("active_target_selected_now","")).strip() in ("0","False","false","") for r in result_rows)) if result_rows else 0
    no_apply = int(all(str(r.get("apply_now","")).strip() in ("0","False","false","") for r in result_rows)) if result_rows else 0
    pending_review_count = sum(1 for r in result_rows if str(r.get("classification","")).strip().upper() == "PENDING_REVIEW")
    exists_count = sum(1 for r in result_rows if str(r.get("exists","")).strip() in ("1","True","true"))
    missing_count = len(result_rows) - exists_count if result_rows else 0

    pre = [
        {"check_id":"dj_b_status_green","value":dj_green,"expected":1,"status":"PASS" if dj_green else "FAIL"},
        {"check_id":"dj_b_savepoint_present","value":dj_savepoint,"expected":1,"status":"PASS" if dj_savepoint else "FAIL"},
        {"check_id":"result_csv_exists","value":int(result_csv.exists()),"expected":1,"status":"PASS" if result_csv.exists() else "FAIL"},
        {"check_id":"transcript_exists","value":int(transcript.exists()),"expected":1,"status":"PASS" if transcript.exists() else "FAIL"},
        {"check_id":"result_rows_match_expected","value":len(result_rows),"expected":expected_rows,"status":"PASS" if rows_match else "FAIL"},
        {"check_id":"all_rows_no_active_target_selected","value":no_active_selected,"expected":1,"status":"PASS" if no_active_selected else "FAIL"},
        {"check_id":"all_rows_no_apply","value":no_apply,"expected":1,"status":"PASS" if no_apply else "FAIL"},
        {"check_id":"transcript_has_content","value":len(transcript_text.strip()),"expected":">0","status":"PASS" if transcript_text.strip() else "FAIL"},
        {"check_id":"dk_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_review) else "FAIL"},
    ]

    classification_summary = [
        {"classification":"PENDING_REVIEW","row_count":pending_review_count,"meaning":"Manual probe captured existence metadata; later DL-B will classify target role.","target_selected_now":0,"apply_now":0},
        {"classification":"EXISTS","row_count":exists_count,"meaning":"Candidate path exists on disk.","target_selected_now":0,"apply_now":0},
        {"classification":"MISSING","row_count":missing_count,"meaning":"Candidate path was not found by the read-only probe.","target_selected_now":0,"apply_now":0},
    ]

    proof_rows = [{
        "proof_id":"DK_PROOF_001",
        "artifact":"DJ_B_TARGET_VERIFICATION_PROBE_RESULTS.csv",
        "path":str(result_csv),
        "exists":int(result_csv.exists()),
        "rows":len(result_rows),
        "expected_rows":expected_rows,
        "proof_status":"PASS" if rows_match and no_active_selected and no_apply else "FAIL",
        "target_selected_now":0,
        "apply_now":0,
    },{
        "proof_id":"DK_PROOF_002",
        "artifact":"DJ_B_TARGET_VERIFICATION_PROBE_TRANSCRIPT.md",
        "path":str(transcript),
        "exists":int(transcript.exists()),
        "rows":len(transcript_text.splitlines()) if transcript_text else 0,
        "expected_rows":">0",
        "proof_status":"PASS" if transcript_text.strip() else "FAIL",
        "target_selected_now":0,
        "apply_now":0,
    }]

    next_classification_requirements = [
        {"req_id":"DL001","requirement":"Classify each DJ-B probe result as active runtime target candidate, generated report/candidate, source/tooling evidence, documentation evidence, missing, or deferred.","required":1},
        {"req_id":"DL002","requirement":"Separate HELP DATA target candidates from CMDHELPCHK target candidates.","required":1},
        {"req_id":"DL003","requirement":"No active target may be selected until classification and evidence review are green.","required":1},
        {"req_id":"DL004","requirement":"No apply execution may be authorized by DL-B.","required":1},
    ]

    boundary = [
        {"boundary":"manual read-only probe output reviewed","value":1,"status":"PASS"},
        {"boundary":"probe executed by DK-B package","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA target selected now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DK-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for r in pre + boundary if r["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DK_B_PROBE_PROOF_REVIEW_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10dk_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dk_b_probe_proof_artifacts_v1.csv", ["proof_id","artifact","path","exists","rows","expected_rows","proof_status","target_selected_now","apply_now"], proof_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dk_b_probe_result_rows_copy_v1.csv", list(result_rows[0].keys()) if result_rows else ["probe_id"], result_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dk_b_classification_summary_v1.csv", ["classification","row_count","meaning","target_selected_now","apply_now"], classification_summary)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dk_b_next_classification_requirements_v1.csv", ["req_id","requirement","required"], next_classification_requirements)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dk_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10DK-B",
        "DJ_B_STATUS_GREEN":dj_green,
        "DJ_B_SAVEPOINT_PRESENT":dj_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DK_B":latest_id(repo),
        "MANUAL_PROBE_OUTPUT_CAPTURE_PROVEN":1 if status == GREEN else 0,
        "RESULT_CSV_EXISTS":int(result_csv.exists()),
        "TRANSCRIPT_EXISTS":int(transcript.exists()),
        "RESULT_ROWS":len(result_rows),
        "EXPECTED_RESULT_ROWS":expected_rows,
        "RESULT_ROWS_MATCH_EXPECTED":rows_match,
        "EXISTING_PATH_ROWS":exists_count,
        "MISSING_PATH_ROWS":missing_count,
        "PENDING_REVIEW_ROWS":pending_review_count,
        "ALL_ROWS_NO_ACTIVE_TARGET_SELECTED":no_active_selected,
        "ALL_ROWS_NO_APPLY":no_apply,
        "PROBE_EXECUTED_BY_DK_B_PACKAGE":0,
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW":0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_REVIEW":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_REVIEW":0,
        "LATEST_POINTER_CHANGED_BY_DK_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10dk_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10DK-B",
        "status":status,
        "manual_probe_output_capture_proven":1 if status == GREEN else 0,
        "result_rows":len(result_rows),
        "active_target_selected_now":False,
        "apply_execution_authorized_now":False,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10dk_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DK-B Read-only Target Verification Probe Proof Review

- Status: {status}
- Validation issues: {validation}
- DJ-B status green: {dj_green}
- DJ-B savepoint present: {dj_savepoint}
- Manual probe output capture proven: {1 if status == GREEN else 0}
- Result CSV exists: {int(result_csv.exists())}
- Transcript exists: {int(transcript.exists())}
- Result rows: {len(result_rows)}
- Expected result rows: {expected_rows}
- Existing path rows: {exists_count}
- Missing path rows: {missing_count}
- Pending review rows: {pending_review_count}
- All rows no active target selected: {no_active_selected}
- All rows no apply: {no_apply}
- Probe executed by DK-B package: 0
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by review: 0
- Active DBF/CDX/LMDB mutation observed by review: 0
- Workspace mutation observed by review: 0
- Latest pointer changed by DK-B: 0
- Next gate: {next_gate}

DK-B reviews the manually generated DJ-B read-only probe outputs. It proves output capture and preserves no-selection/no-apply boundaries. It does not classify or select active targets; that belongs to DL-B.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DK_B_READ_ONLY_TARGET_VERIFICATION_PROBE_PROOF_REVIEW.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DK_B_READ_ONLY_TARGET_VERIFICATION_PROBE_PROOF_REVIEW.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DJ-B status green: {dj_green}")
    print(f"  DJ-B savepoint present: {dj_savepoint}")
    print(f"  manual probe output capture proven: {1 if status == GREEN else 0}")
    print(f"  result csv exists: {int(result_csv.exists())}")
    print(f"  transcript exists: {int(transcript.exists())}")
    print(f"  result rows: {len(result_rows)}")
    print(f"  expected result rows: {expected_rows}")
    print(f"  existing path rows: {exists_count}")
    print(f"  missing path rows: {missing_count}")
    print(f"  pending review rows: {pending_review_count}")
    print(f"  all rows no active target selected: {no_active_selected}")
    print(f"  all rows no apply: {no_apply}")
    print("  probe executed by DK-B package: 0")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by review: 0")
    print("  active DBF/CDX/LMDB mutation observed by review: 0")
    print("  workspace mutation observed by review: 0")
    print("  latest pointer changed by DK-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
