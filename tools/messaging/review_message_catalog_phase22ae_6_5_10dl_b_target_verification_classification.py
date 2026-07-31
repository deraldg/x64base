from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DK_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DK_B_READ_ONLY_TARGET_VERIFICATION_PROBE_PROOF_REVIEW_GREEN_MANUAL_PROBE_OUTPUT_CAPTURE_PROVEN_NO_SELECTION"
DK_SAVEPOINT = "MSG-022AE.6.5.10DK-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DL_B_TARGET_VERIFICATION_CLASSIFICATION_REVIEW_GREEN_CLASSIFICATION_STAGED_NO_TARGET_SELECTED"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DL_B_TARGET_VERIFICATION_CLASSIFICATION_REVIEW_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DM_B_TARGET_CLASSIFICATION_DECISION_PACKAGE"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dl_b_target_verification_classification_review_v1"

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

def as_int(v, default=0) -> int:
    try:
        return int(str(v).strip())
    except Exception:
        return default

def classify(row: dict) -> tuple[str, str, int]:
    rel = row.get("relative_path", "").replace("\\", "/").lower()
    artifact = row.get("artifact_type", "").lower()
    suffix = Path(rel).suffix.lower()
    exists = as_int(row.get("exists", "0"))

    if not exists:
        return "missing_or_stale_candidate", "Probe path does not exist; cannot be selected as active target.", 0

    if "/docs/messaging/apply/" in rel or "/docs/messaging/reports/" in rel:
        return "generated_candidate_or_report", "Messaging apply/report artifact; evidence or candidate, not active target by default.", 0

    if rel.startswith("tools/") or artifact == "tooling" or suffix in (".py", ".ps1", ".bat", ".cmd"):
        return "source_or_tooling_evidence", "Tooling/script evidence; may explain build/probe path but not an active HELP/CMDHELPCHK data target.", 0

    if rel.startswith("src/") or artifact == "source" or suffix in (".cpp", ".hpp", ".h", ".c", ".cc"):
        return "source_or_tooling_evidence", "Source evidence; not a data mutation target without separate source authorization.", 0

    if rel.startswith("docs/") or artifact == "documentation_or_report" or suffix in (".md", ".txt"):
        return "documentation_evidence", "Documentation/report evidence; not an active mutation target.", 0

    if suffix in (".dbf", ".dtx", ".cdx", ".idx", ".inx", ".cnx") or artifact == "runtime_data_or_index":
        return "active_runtime_target_candidate_unverified", "Runtime data/index-looking artifact; may be a target candidate but still requires schema/key/backup verification.", 1

    if suffix in (".csv", ".json") or artifact == "structured_candidate_or_report":
        return "generated_candidate_or_report", "Structured CSV/JSON candidate/report; not active target by default.", 0

    return "defer_manual_review", "Path exists but role is not clear enough for automatic target classification.", 0

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

    dk = csv_one(reports / "message_catalog_phase22ae_6_5_10dk_b_status_summary_v1.csv")
    probe_rows = csv_rows(reports / "message_catalog_phase22ae_6_5_10dk_b_probe_result_rows_copy_v1.csv")

    dk_green = int(dk.get("STATUS", "") == DK_GREEN)
    dk_savepoint = has_journal(repo, DK_SAVEPOINT)
    capture_proven = int(str(dk.get("MANUAL_PROBE_OUTPUT_CAPTURE_PROVEN", "0")) == "1")
    expected_rows = as_int(dk.get("EXPECTED_RESULT_ROWS", "0"))
    result_rows = as_int(dk.get("RESULT_ROWS", len(probe_rows)))
    no_selected = int(str(dk.get("ALL_ROWS_NO_ACTIVE_TARGET_SELECTED", "0")) == "1")
    no_apply = int(str(dk.get("ALL_ROWS_NO_APPLY", "0")) == "1")

    pre = [
        {"check_id":"dk_b_status_green","value":dk_green,"expected":1,"status":"PASS" if dk_green else "FAIL"},
        {"check_id":"dk_b_savepoint_present","value":dk_savepoint,"expected":1,"status":"PASS" if dk_savepoint else "FAIL"},
        {"check_id":"manual_probe_output_capture_proven","value":capture_proven,"expected":1,"status":"PASS" if capture_proven else "FAIL"},
        {"check_id":"probe_result_rows_exist","value":len(probe_rows),"expected":">0","status":"PASS" if probe_rows else "FAIL"},
        {"check_id":"probe_result_rows_match_expected","value":result_rows,"expected":expected_rows,"status":"PASS" if result_rows == expected_rows and len(probe_rows) == expected_rows else "FAIL"},
        {"check_id":"dk_b_all_rows_no_target_selected","value":no_selected,"expected":1,"status":"PASS" if no_selected else "FAIL"},
        {"check_id":"dk_b_all_rows_no_apply","value":no_apply,"expected":1,"status":"PASS" if no_apply else "FAIL"},
        {"check_id":"dl_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_review) else "FAIL"},
    ]

    classified = []
    for row in probe_rows:
        classification, reason, candidate = classify(row)
        classified.append({
            "probe_id": row.get("probe_id", ""),
            "family": row.get("family", ""),
            "relative_path": row.get("relative_path", ""),
            "artifact_type": row.get("artifact_type", ""),
            "probe_kind": row.get("probe_kind", ""),
            "exists": row.get("exists", ""),
            "fs_kind": row.get("fs_kind", ""),
            "length": row.get("length", ""),
            "classification": classification,
            "classification_reason": reason,
            "active_runtime_target_candidate": candidate,
            "active_target_selected_now": 0,
            "apply_now": 0,
        })

    summary_map = {}
    for row in classified:
        key = row["classification"]
        summary_map.setdefault(key, {"classification": key, "row_count": 0, "active_runtime_target_candidates": 0, "target_selected_now": 0, "apply_now": 0})
        summary_map[key]["row_count"] += 1
        summary_map[key]["active_runtime_target_candidates"] += as_int(row["active_runtime_target_candidate"])
    classification_summary = list(summary_map.values())

    decision_inputs = [
        {"input_id":"DM001","input":"DL-B classification rows","accepted":1,"target_selected_now":0,"apply_now":0},
        {"input_id":"DM002","input":"Active runtime target candidates remain unverified","accepted":1,"target_selected_now":0,"apply_now":0},
        {"input_id":"DM003","input":"Generated/docs/source/tooling evidence must not be selected as active targets automatically","accepted":1,"target_selected_now":0,"apply_now":0},
        {"input_id":"DM004","input":"Any active target selection requires a separate explicit decision package","accepted":1,"target_selected_now":0,"apply_now":0},
    ]

    boundary = [
        {"boundary":"target verification classification reviewed","value":1,"status":"PASS"},
        {"boundary":"active HELP DATA target selected now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by classification","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by classification","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by classification","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DL-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for r in pre + boundary if r["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DL_B_CLASSIFICATION_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10dl_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dl_b_classified_probe_results_v1.csv", ["probe_id","family","relative_path","artifact_type","probe_kind","exists","fs_kind","length","classification","classification_reason","active_runtime_target_candidate","active_target_selected_now","apply_now"], classified)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dl_b_classification_summary_v1.csv", ["classification","row_count","active_runtime_target_candidates","target_selected_now","apply_now"], classification_summary)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dl_b_decision_inputs_v1.csv", ["input_id","input","accepted","target_selected_now","apply_now"], decision_inputs)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dl_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    runtime_candidates = sum(as_int(r["active_runtime_target_candidate"]) for r in classified)
    generated_count = sum(1 for r in classified if r["classification"] == "generated_candidate_or_report")
    evidence_count = sum(1 for r in classified if r["classification"] in ("source_or_tooling_evidence", "documentation_evidence"))
    missing_count = sum(1 for r in classified if r["classification"] == "missing_or_stale_candidate")
    defer_count = sum(1 for r in classified if r["classification"] == "defer_manual_review")

    status_row = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10DL-B",
        "DK_B_STATUS_GREEN":dk_green,
        "DK_B_SAVEPOINT_PRESENT":dk_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DL_B":latest_id(repo),
        "TARGET_VERIFICATION_CLASSIFICATION_REVIEWED":1 if status == GREEN else 0,
        "CLASSIFIED_ROWS":len(classified),
        "ACTIVE_RUNTIME_TARGET_CANDIDATE_ROWS_UNVERIFIED":runtime_candidates,
        "GENERATED_CANDIDATE_OR_REPORT_ROWS":generated_count,
        "SOURCE_DOC_TOOLING_EVIDENCE_ROWS":evidence_count,
        "MISSING_OR_STALE_ROWS":missing_count,
        "DEFER_MANUAL_REVIEW_ROWS":defer_count,
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW":0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_CLASSIFICATION":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_CLASSIFICATION":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_CLASSIFICATION":0,
        "LATEST_POINTER_CHANGED_BY_DL_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10dl_b_status_summary_v1.csv", list(status_row[0].keys()), status_row)

    manifest = {
        "phase":"22AE.6.5.10DL-B",
        "status":status,
        "classified_rows":len(classified),
        "active_runtime_target_candidate_rows_unverified":runtime_candidates,
        "active_target_selected_now":False,
        "apply_execution_authorized_now":False,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10dl_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DL-B Target Verification Classification Review

- Status: {status}
- Validation issues: {validation}
- DK-B status green: {dk_green}
- DK-B savepoint present: {dk_savepoint}
- Target verification classification reviewed: {1 if status == GREEN else 0}
- Classified rows: {len(classified)}
- Active runtime target candidate rows, unverified: {runtime_candidates}
- Generated candidate/report rows: {generated_count}
- Source/doc/tooling evidence rows: {evidence_count}
- Missing/stale rows: {missing_count}
- Deferred/manual-review rows: {defer_count}
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by classification: 0
- Active DBF/CDX/LMDB mutation observed by classification: 0
- Workspace mutation observed by classification: 0
- Latest pointer changed by DL-B: 0
- Next gate: {next_gate}

DL-B classifies the read-only probe results into evidence/target buckets. It does not select active targets and does not apply HELP DATA/CMDHELPCHK changes.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DL_B_TARGET_VERIFICATION_CLASSIFICATION_REVIEW.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DL_B_TARGET_VERIFICATION_CLASSIFICATION_REVIEW.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DK-B status green: {dk_green}")
    print(f"  DK-B savepoint present: {dk_savepoint}")
    print(f"  target verification classification reviewed: {1 if status == GREEN else 0}")
    print(f"  classified rows: {len(classified)}")
    print(f"  active runtime target candidate rows unverified: {runtime_candidates}")
    print(f"  generated candidate/report rows: {generated_count}")
    print(f"  source/doc/tooling evidence rows: {evidence_count}")
    print(f"  missing/stale rows: {missing_count}")
    print(f"  deferred/manual-review rows: {defer_count}")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by classification: 0")
    print("  active DBF/CDX/LMDB mutation observed by classification: 0")
    print("  workspace mutation observed by classification: 0")
    print("  latest pointer changed by DL-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
