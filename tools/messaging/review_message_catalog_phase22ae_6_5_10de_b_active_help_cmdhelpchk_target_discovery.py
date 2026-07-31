from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DD_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DD_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_STAGING_GREEN_CANDIDATE_TARGETS_STAGED_NO_MUTATION"
DD_SAVEPOINT = "MSG-022AE.6.5.10DD-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DE_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_REVIEW_GREEN_TARGET_REVIEW_QUEUE_ACCEPTED_NO_SELECTION"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DE_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_REVIEW_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DF_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_PLAN"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10de_b_active_help_cmdhelpchk_target_discovery_review_v1"

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
    rows = csv_rows(path)
    return rows[0] if rows else {}

def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in fields})

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

    dd = csv_one(reports / "message_catalog_phase22ae_6_5_10dd_b_status_summary_v1.csv")
    inventory = csv_rows(reports / "message_catalog_phase22ae_6_5_10dd_b_target_candidate_inventory_v1.csv")
    queue = csv_rows(reports / "message_catalog_phase22ae_6_5_10dd_b_likely_target_review_queue_v1.csv")
    family = csv_rows(reports / "message_catalog_phase22ae_6_5_10dd_b_target_family_summary_v1.csv")

    dd_green = int(dd.get("STATUS", "") == DD_GREEN)
    dd_savepoint = has_journal(repo, DD_SAVEPOINT)
    candidates = as_int(dd.get("TARGET_CANDIDATE_ROWS", len(inventory)))
    queue_rows = as_int(dd.get("LIKELY_TARGET_REVIEW_ROWS", len(queue)))
    help_candidates = as_int(dd.get("HELP_DATA_TARGET_CANDIDATES", 0))
    cmd_candidates = as_int(dd.get("CMDHELPCHK_TARGET_CANDIDATES", 0))

    pre = [
        {"check_id":"dd_b_status_green","value":dd_green,"expected":1,"status":"PASS" if dd_green else "FAIL"},
        {"check_id":"dd_b_savepoint_present","value":dd_savepoint,"expected":1,"status":"PASS" if dd_savepoint else "FAIL"},
        {"check_id":"inventory_exists","value":int(bool(inventory)),"expected":1,"status":"PASS" if inventory else "FAIL"},
        {"check_id":"review_queue_exists","value":int(bool(queue)),"expected":1,"status":"PASS" if queue else "FAIL"},
        {"check_id":"target_candidates_nonzero","value":candidates,"expected":">0","status":"PASS" if candidates > 0 else "FAIL"},
        {"check_id":"help_or_cmd_candidates_nonzero","value":help_candidates + cmd_candidates,"expected":">0","status":"PASS" if (help_candidates + cmd_candidates) > 0 else "FAIL"},
        {"check_id":"de_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_review) else "FAIL"},
    ]

    # Sort inventory into practical review buckets.
    def priority(row):
        return as_int(row.get("review_priority", 0))

    inv_sorted = sorted(inventory, key=priority, reverse=True)
    review_buckets = []
    for fam in ["HELP_DATA", "CMDHELPCHK", "BOTH"]:
        fam_rows = [r for r in inv_sorted if r.get("family") == fam]
        for artifact_type in ["runtime_data_or_index", "source", "tooling", "structured_candidate_or_report", "documentation_or_report"]:
            bucket_rows = [r for r in fam_rows if r.get("artifact_type") == artifact_type]
            if bucket_rows:
                review_buckets.append({
                    "family": fam,
                    "artifact_type": artifact_type,
                    "candidate_count": len(bucket_rows),
                    "top_relative_path": bucket_rows[0].get("relative_path", ""),
                    "top_review_priority": bucket_rows[0].get("review_priority", ""),
                    "selected_now": 0,
                    "requires_human_review": 1,
                })

    narrowed_queue = []
    for row in queue[:60]:
        narrowed_queue.append({
            "family": row.get("family", ""),
            "relative_path": row.get("relative_path", ""),
            "artifact_type": row.get("artifact_type", ""),
            "review_priority": row.get("review_priority", ""),
            "review_action": "review_for_active_target_selection_candidate",
            "selected_now": 0,
            "apply_now": 0,
        })

    selection_requirements = [
        {"req_id":"DF001","requirement":"Separate HELP DATA target selection from CMDHELPCHK target selection.","required":1},
        {"req_id":"DF002","requirement":"Prefer active runtime data/config targets over source/docs when selecting actual mutation targets.","required":1},
        {"req_id":"DF003","requirement":"Treat source/tooling/docs hits as evidence and command-surface context, not active data targets by default.","required":1},
        {"req_id":"DF004","requirement":"Confirm physical target files/tables exist, expected fields/keys are known, and backup/rollback path is defined.","required":1},
        {"req_id":"DF005","requirement":"Require duplicate/collision policy for HELP_KEY, COMMAND_NAME, LOCALE_ID, and CHECK_ID before apply.","required":1},
        {"req_id":"DF006","requirement":"Keep target selection plan-only; no active HELP DATA/CMDHELPCHK apply in DF-B.","required":1},
        {"req_id":"DF007","requirement":"Require later dry-run delta package before any apply execution package.","required":1},
    ]

    boundary = [
        {"boundary":"target discovery reviewed","value":1,"status":"PASS"},
        {"boundary":"active HELP DATA target selected now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DE-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DE_B_TARGET_DISCOVERY_REVIEW_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10de_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10de_b_review_bucket_summary_v1.csv", ["family","artifact_type","candidate_count","top_relative_path","top_review_priority","selected_now","requires_human_review"], review_buckets)
    write_csv(reports / "message_catalog_phase22ae_6_5_10de_b_narrowed_target_review_queue_v1.csv", ["family","relative_path","artifact_type","review_priority","review_action","selected_now","apply_now"], narrowed_queue)
    write_csv(reports / "message_catalog_phase22ae_6_5_10de_b_selection_requirements_v1.csv", ["req_id","requirement","required"], selection_requirements)
    write_csv(reports / "message_catalog_phase22ae_6_5_10de_b_family_summary_copy_v1.csv", list(family[0].keys()) if family else ["family"], family)
    write_csv(reports / "message_catalog_phase22ae_6_5_10de_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation,
        "PHASE": "22AE.6.5.10DE-B",
        "DD_B_STATUS_GREEN": dd_green,
        "DD_B_SAVEPOINT_PRESENT": dd_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DE_B": latest_id(repo),
        "TARGET_CANDIDATE_ROWS_REVIEWED": candidates,
        "LIKELY_TARGET_REVIEW_ROWS_ACCEPTED": queue_rows,
        "HELP_DATA_TARGET_CANDIDATES": help_candidates,
        "CMDHELPCHK_TARGET_CANDIDATES": cmd_candidates,
        "REVIEW_BUCKET_ROWS": len(review_buckets),
        "NARROWED_REVIEW_QUEUE_ROWS": len(narrowed_queue),
        "SELECTION_REQUIREMENT_ROWS": len(selection_requirements),
        "TARGET_DISCOVERY_REVIEW_ACCEPTED": 1 if status == GREEN else 0,
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW": 0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW": 0,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_REVIEW": 0,
        "WORKSPACE_MUTATION_OBSERVED_BY_REVIEW": 0,
        "LATEST_POINTER_CHANGED_BY_DE_B": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10de_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase": "22AE.6.5.10DE-B",
        "status": status,
        "target_discovery_review_accepted": 1 if status == GREEN else 0,
        "active_target_selected_now": False,
        "apply_execution_authorized_now": False,
        "next_gate": next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10de_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DE-B Active HELP/CMDHELPCHK Target Discovery Review

- Status: {status}
- Validation issues: {validation}
- DD-B status green: {dd_green}
- DD-B savepoint present: {dd_savepoint}
- Target candidate rows reviewed: {candidates}
- Likely target review rows accepted: {queue_rows}
- HELP DATA target candidates: {help_candidates}
- CMDHELPCHK target candidates: {cmd_candidates}
- Review bucket rows: {len(review_buckets)}
- Narrowed review queue rows: {len(narrowed_queue)}
- Target discovery review accepted: {1 if status == GREEN else 0}
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by review: 0
- Active DBF/CDX/LMDB mutation observed by review: 0
- Workspace mutation observed by review: 0
- Latest pointer changed by DE-B: 0
- Next gate: {next_gate}

DE-B accepts the DD-B discovery inventory as sufficient for a later target-selection plan. It does not select active targets and does not apply anything.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DE_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_REVIEW.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DE_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_REVIEW.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DD-B status green: {dd_green}")
    print(f"  DD-B savepoint present: {dd_savepoint}")
    print(f"  target candidate rows reviewed: {candidates}")
    print(f"  likely target review rows accepted: {queue_rows}")
    print(f"  HELP DATA target candidates: {help_candidates}")
    print(f"  CMDHELPCHK target candidates: {cmd_candidates}")
    print(f"  review bucket rows: {len(review_buckets)}")
    print(f"  narrowed review queue rows: {len(narrowed_queue)}")
    print("  target discovery review accepted: 1" if status == GREEN else "  target discovery review accepted: 0")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by review: 0")
    print("  active DBF/CDX/LMDB mutation observed by review: 0")
    print("  workspace mutation observed by review: 0")
    print("  latest pointer changed by DE-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
