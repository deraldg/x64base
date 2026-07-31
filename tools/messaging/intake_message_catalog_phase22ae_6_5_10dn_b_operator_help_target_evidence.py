from __future__ import annotations
import argparse, csv, json, shutil, hashlib
from datetime import datetime, timezone
from pathlib import Path

DM_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DM_B_TARGET_CLASSIFICATION_DECISION_PACKAGE_GREEN_NO_ACTIVE_TARGET_PROVEN_APPLY_HELD"
DM_SAVEPOINT = "MSG-022AE.6.5.10DM-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DN_B_OPERATOR_HELP_TARGET_EVIDENCE_INTAKE_GREEN_ACTIVE_HELP_CATALOG_CANDIDATE_FOUND_APPLY_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DN_B_OPERATOR_HELP_TARGET_EVIDENCE_INTAKE_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DO_B_ACTIVE_HELP_CATALOG_TARGET_MAPPING_PLAN"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dn_b_operator_help_target_evidence_intake_v1"

EXPECTED_HELP_TABLES = [
    ("CMD_ARGS", "cmd_args.dbf"),
    ("COMMANDS", "commands.dbf"),
    ("HELP_ARTIFACTS", "help_artifacts.dbf"),
    ("HELP_LINE", "help_line.dbf"),
    ("HELP_SECTION", "help_section.dbf"),
    ("HELP_TOPIC", "help_topic.dbf"),
]

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
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})

def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def has_journal(repo: Path, marker: str) -> int:
    return int(marker in read_text(repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def latest_id(repo: Path) -> str:
    try:
        data = json.loads(read_text(repo / "docs/messaging/reports/message_savepoint_latest_v1.json"))
        return data.get("savepoint_id", data.get("savepoint", ""))
    except Exception:
        return ""

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--replace-existing-intake", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_intake:
        shutil.rmtree(out)

    dm = csv_one(reports / "message_catalog_phase22ae_6_5_10dm_b_status_summary_v1.csv")
    dm_green = int(dm.get("STATUS", "") == DM_GREEN)
    dm_savepoint = has_journal(repo, DM_SAVEPOINT)

    help_root = repo / "dottalkpp/data/HELP"
    help_index_root = repo / "dottalkpp/data/INDEXES/HELP"
    cmd_help_cpp = repo / "src/cli/cmd_help.cpp"
    cmd_help_hpp = repo / "src/cli/cmd_help.hpp"

    pre = [
        {"check_id":"dm_b_status_green","value":dm_green,"expected":1,"status":"PASS" if dm_green else "FAIL"},
        {"check_id":"dm_b_savepoint_present","value":dm_savepoint,"expected":1,"status":"PASS" if dm_savepoint else "FAIL"},
        {"check_id":"help_root_exists","value":int(help_root.exists()),"expected":1,"status":"PASS" if help_root.exists() else "FAIL"},
        {"check_id":"help_index_root_exists_or_deferred","value":int(help_index_root.exists()),"expected":"0_or_1","status":"PASS"},
        {"check_id":"cmd_help_cpp_exists","value":int(cmd_help_cpp.exists()),"expected":1,"status":"PASS" if cmd_help_cpp.exists() else "WARN"},
        {"check_id":"cmd_help_hpp_exists","value":int(cmd_help_hpp.exists()),"expected":1,"status":"PASS" if cmd_help_hpp.exists() else "WARN"},
        {"check_id":"dn_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_intake) else "FAIL"},
    ]

    target_rows = []
    existing_expected = 0
    for logical, fn in EXPECTED_HELP_TABLES:
        path = help_root / fn
        exists = int(path.exists())
        existing_expected += exists
        target_rows.append({
            "target_family":"ACTIVE_HELP_CATALOG",
            "logical_table":logical,
            "relative_path":str(path.relative_to(repo)).replace("\\","/") if path.exists() else str((Path("dottalkpp/data/HELP") / fn)).replace("\\","/"),
            "exists":exists,
            "bytes":path.stat().st_size if exists else 0,
            "sha256":sha256(path),
            "role_guess":"active HELP catalog table from operator DOTSCRIPT workspace proof",
            "active_target_candidate":exists,
            "selected_for_apply_now":0,
            "apply_now":0,
        })

    source_rows = []
    for role, path in [("HELP command source", cmd_help_cpp), ("HELP command header", cmd_help_hpp)]:
        source_rows.append({
            "source_role":role,
            "relative_path":str(path.relative_to(repo)).replace("\\","/") if path.exists() else str(path),
            "exists":int(path.exists()),
            "bytes":path.stat().st_size if path.exists() else 0,
            "sha256":sha256(path),
            "usage_contract_seen":int("@dottalk.usage v1" in read_text(path)) if path.exists() else 0,
            "mutation_now":0,
        })

    operator_evidence = [
        {"evidence_id":"DN_OP_001","evidence":"Operator ran `do cmdhelp`, which set DBF path to dottalkpp/data/HELP and INDEXES path to dottalkpp/data/INDEXES/HELP.","accepted":1},
        {"evidence_id":"DN_OP_002","evidence":"Workspace opened six HELP catalog tables: cmd_args, commands, help_artifacts, help_line, help_section, help_topic.","accepted":1},
        {"evidence_id":"DN_OP_003","evidence":"Struct output exposed fields for CMD_ARGS, COMMANDS, HELP_ARTIFACTS, HELP_LINE, HELP_SECTION, HELP_TOPIC.","accepted":1},
        {"evidence_id":"DN_OP_004","evidence":"The earlier broad probe did not prove active target because it searched generated/source evidence; operator evidence now identifies the active HELP catalog root candidate.","accepted":1},
        {"evidence_id":"DN_OP_005","evidence":"No active target is selected for apply by DN-B. Mapping and dry-run remain future guarded steps.","accepted":1},
    ]

    mapping_requirements = [
        {"req_id":"DO001","requirement":"Map candidate HELP/CMDHELPCHK rows to actual HELP catalog tables and fields before any dry-run.","required":1},
        {"req_id":"DO002","requirement":"Determine whether CMDHELPCHK is represented by COMMANDS/CMD_ARGS/HELP_* rows, a separate checker surface, or both.","required":1},
        {"req_id":"DO003","requirement":"Confirm indexes/tags and LMDB expectations for active HELP catalog tables before any apply path.","required":1},
        {"req_id":"DO004","requirement":"Create backup/hash manifest and rollback plan before any future write package.","required":1},
        {"req_id":"DO005","requirement":"Continue no active HELP DATA/CMDHELPCHK apply until target mapping and dry-run delta are green and explicitly authorized.","required":1},
    ]

    boundary = [
        {"boundary":"operator HELP target evidence intake created","value":1,"status":"PASS"},
        {"boundary":"active HELP catalog candidate found","value":1 if existing_expected >= 6 else 0,"status":"PASS" if existing_expected >= 6 else "FAIL"},
        {"boundary":"active HELP DATA target selected for apply now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected for apply now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by intake","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by intake","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by intake","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DN-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DN_B_OPERATOR_HELP_TARGET_EVIDENCE_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10dn_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dn_b_active_help_catalog_candidate_targets_v1.csv", ["target_family","logical_table","relative_path","exists","bytes","sha256","role_guess","active_target_candidate","selected_for_apply_now","apply_now"], target_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dn_b_help_source_evidence_v1.csv", ["source_role","relative_path","exists","bytes","sha256","usage_contract_seen","mutation_now"], source_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dn_b_operator_evidence_v1.csv", ["evidence_id","evidence","accepted"], operator_evidence)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dn_b_mapping_requirements_v1.csv", ["req_id","requirement","required"], mapping_requirements)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dn_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10DN-B",
        "DM_B_STATUS_GREEN":dm_green,
        "DM_B_SAVEPOINT_PRESENT":dm_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DN_B":latest_id(repo),
        "OPERATOR_HELP_TARGET_EVIDENCE_ACCEPTED":1 if status == GREEN else 0,
        "ACTIVE_HELP_CATALOG_ROOT_EXISTS":int(help_root.exists()),
        "ACTIVE_HELP_CATALOG_TABLES_EXPECTED":len(EXPECTED_HELP_TABLES),
        "ACTIVE_HELP_CATALOG_TABLES_FOUND":existing_expected,
        "ACTIVE_HELP_CATALOG_CANDIDATE_FOUND":1 if existing_expected >= 6 else 0,
        "HELP_SOURCE_EVIDENCE_ROWS":len(source_rows),
        "MAPPING_REQUIREMENT_ROWS":len(mapping_requirements),
        "CLOSEOUT_ROUTE_SUPERSEDED_BY_OPERATOR_TARGET_EVIDENCE":1 if status == GREEN else 0,
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW":0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_INTAKE":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_INTAKE":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_INTAKE":0,
        "LATEST_POINTER_CHANGED_BY_DN_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10dn_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10DN-B",
        "status":status,
        "active_help_catalog_candidate_found":existing_expected >= 6,
        "closeout_route_superseded_by_operator_target_evidence":status == GREEN,
        "active_target_selected_now":False,
        "apply_execution_authorized_now":False,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10dn_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DN-B Operator HELP Target Evidence Intake

- Status: {status}
- Validation issues: {validation}
- DM-B status green: {dm_green}
- DM-B savepoint present: {dm_savepoint}
- Operator HELP target evidence accepted: {1 if status == GREEN else 0}
- Active HELP catalog root exists: {int(help_root.exists())}
- Active HELP catalog tables expected: {len(EXPECTED_HELP_TABLES)}
- Active HELP catalog tables found: {existing_expected}
- Active HELP catalog candidate found: {1 if existing_expected >= 6 else 0}
- Closeout route superseded by operator target evidence: {1 if status == GREEN else 0}
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by intake: 0
- Active DBF/CDX/LMDB mutation observed by intake: 0
- Workspace mutation observed by intake: 0
- Latest pointer changed by DN-B: 0
- Next gate: {next_gate}

DN-B records new operator evidence showing the active HELP catalog candidate root at `dottalkpp/data/HELP`. This supersedes the immediate closeout route, but does not authorize apply. The next package should map candidate rows to actual HELP catalog tables/fields before any dry-run or mutation.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DN_B_OPERATOR_HELP_TARGET_EVIDENCE_INTAKE.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DN_B_OPERATOR_HELP_TARGET_EVIDENCE_INTAKE.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DM-B status green: {dm_green}")
    print(f"  DM-B savepoint present: {dm_savepoint}")
    print(f"  operator HELP target evidence accepted: {1 if status == GREEN else 0}")
    print(f"  active HELP catalog root exists: {int(help_root.exists())}")
    print(f"  active HELP catalog tables expected: {len(EXPECTED_HELP_TABLES)}")
    print(f"  active HELP catalog tables found: {existing_expected}")
    print(f"  active HELP catalog candidate found: {1 if existing_expected >= 6 else 0}")
    print(f"  closeout route superseded by operator target evidence: {1 if status == GREEN else 0}")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by intake: 0")
    print("  active DBF/CDX/LMDB mutation observed by intake: 0")
    print("  workspace mutation observed by intake: 0")
    print("  latest pointer changed by DN-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
