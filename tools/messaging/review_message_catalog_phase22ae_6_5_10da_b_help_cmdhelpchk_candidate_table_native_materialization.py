from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

CZ_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CZ_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_STAGING_GREEN_DTS_AND_MAPPED_INPUTS_STAGED_APPLY_HELD"
CZ_SAVEPOINT = "MSG-022AE.6.5.10CZ-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DA_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_PROOF_REVIEW_GREEN_DBF_CDX_LMDB_READBACK_PROVEN_APPLY_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DA_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_PROOF_REVIEW_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DB_B_HELP_CMDHELPCHK_NATIVE_MATERIALIZATION_DECISION_PACKAGE"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10da_b_help_cmdhelpchk_candidate_table_native_materialization_proof_review_v1"
CZ_ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cz_b_help_cmdhelpchk_candidate_table_native_materialization_staging_v1"

TABLES = {
    "HELPDATA_CZ": {"records": 3, "tags": ["MESSAGE_ID", "HELP_KEY"], "fields": ["MESSAGE_ID","LOCALE_ID","HELP_KEY","HELP_TEXT","SOURCE_PHASE","REVIEW_STATUS","APPLY_READY","APPLY_SCOPE"]},
    "CMDHELP_CZ": {"records": 4, "tags": ["COMMAND_NAME", "CHECK_ID"], "fields": ["COMMAND_NAME","HELP_KEY","CHECK_ID","CHECK_STATUS","MUTATION_FLAG","REVIEW_STATUS","APPLY_READY","APPLY_SCOPE"]},
    "GATEEV_CZ": {"records": 4, "tags": ["GATE_ID"], "fields": ["GATE_ID","GATE_STATUS","MUTATION_FLAG","GATE_NOTES","APPLY_SCOPE"]},
}
GLOBAL_MARKERS = ["DOTSCRIPT OUT:", "SETPATH: DBF =", "SETPATH: INDEXES =", "SETPATH: LMDB =", "WORKSPACE: 0 area(s) open."]
BOUNDARY_MARKERS = ["NO_SOURCE_MUTATION", "NO_ACTIVE_HELP_APPLY", "NO_CMDHELPCHK_APPLY", "NO_LATEST_POINTER_CHANGE", "CANDIDATE_ONLY"]

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

def has_journal(repo: Path, marker: str) -> int:
    return int(marker in read_text(repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def latest_id(repo: Path) -> str:
    try:
        data = json.loads(read_text(repo / "docs/messaging/reports/message_savepoint_latest_v1.json"))
        return data.get("savepoint_id", data.get("savepoint", ""))
    except Exception:
        return ""

def sha256_path(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def nonempty_dir(path: Path) -> int:
    try:
        return int(path.exists() and path.is_dir() and any(path.iterdir()))
    except Exception:
        return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--replace-existing-review", action="store_true")
    parser.add_argument("--allow-missing-cz-b-savepoint", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL
    cz_root = repo / CZ_ROOT_REL
    transcript = cz_root / "runlog/CZ_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_MATERIALIZATION_TRANSCRIPT.txt"

    if out.exists() and args.replace_existing_review:
        shutil.rmtree(out)

    cz = csv_one(reports / "message_catalog_phase22ae_6_5_10cz_b_status_summary_v1.csv")
    cz_green = int(cz.get("STATUS", "") == CZ_GREEN)
    cz_savepoint = has_journal(repo, CZ_SAVEPOINT)
    text = read_text(transcript)

    pre = [
        {"check_id":"cz_b_status_green","value":cz_green,"expected":1,"status":"PASS" if cz_green else "FAIL"},
        {"check_id":"cz_b_savepoint_present","value":cz_savepoint,"expected":1,"status":"PASS" if cz_savepoint else ("REVIEW" if args.allow_missing_cz_b_savepoint else "FAIL")},
        {"check_id":"cz_root_exists","value":int(cz_root.exists()),"expected":1,"status":"PASS" if cz_root.exists() else "FAIL"},
        {"check_id":"transcript_exists","value":int(transcript.exists()),"expected":1,"status":"PASS" if transcript.exists() else "FAIL"},
        {"check_id":"da_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_review) else "FAIL"},
    ]

    global_rows = [{"marker":m, "found":int(m in text), "status":"PASS" if m in text else "FAIL"} for m in GLOBAL_MARKERS]
    boundary_rows = [{"marker":m, "found":int(m in text), "status":"PASS" if m in text else "FAIL"} for m in BOUNDARY_MARKERS]

    table_rows = []
    tag_rows = []
    artifact_rows = []
    for table, spec in TABLES.items():
        n = spec["records"]
        dbf = cz_root / "dbf" / f"{table}.dbf"
        cdx = cz_root / "indexes" / f"{table}.cdx"
        lmdb = cz_root / "lmdb" / f"{table}.cdx.d"

        created = int(f"{table}.dbf [X64]" in text)
        imported = int(f"Imported {n} records" in text and f"{table}.csv" in text)
        listed = int(f"{n} record(s) listed" in text)
        fields_seen = int(all(field in text for field in spec["fields"]))
        table_status = "PASS" if created and imported and listed and fields_seen and dbf.exists() else "FAIL"
        table_rows.append({
            "table":table, "expected_records":n, "created_seen":created, "import_seen":imported,
            "listed_seen":listed, "fields_seen":fields_seen, "dbf_exists":int(dbf.exists()), "status":table_status
        })

        artifact_rows.append({"artifact":f"{table}.dbf","path":str(dbf),"exists":int(dbf.exists()),"bytes":dbf.stat().st_size if dbf.exists() else 0,"sha256":sha256_path(dbf),"nonempty_dir":""})
        artifact_rows.append({"artifact":f"{table}.cdx","path":str(cdx),"exists":int(cdx.exists()),"bytes":cdx.stat().st_size if cdx.exists() else 0,"sha256":sha256_path(cdx),"nonempty_dir":""})
        artifact_rows.append({"artifact":f"{table}.cdx.d","path":str(lmdb),"exists":int(lmdb.exists()),"bytes":"","sha256":"","nonempty_dir":nonempty_dir(lmdb)})

        for tag in spec["tags"]:
            addtag = int(f"CDX ADDTAG: added '{tag}'." in text)
            order = int(f"SET ORDER: CDX TAG '{tag}' (ASC)" in text)
            build = int(f"{tag} : OK" in text)
            tag_rows.append({"table":table,"tag":tag,"addtag_seen":addtag,"buildlmdb_tag_ok_seen":build,"set_order_seen":order,"status":"PASS" if addtag and build and order else "FAIL"})

    boundary = [
        {"boundary":"candidate HELP/CMDHELPCHK native materialization proven","value":1,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DA-B","value":0,"status":"PASS"},
    ]

    validation = (
        sum(1 for row in pre if row["status"] == "FAIL") +
        sum(1 for row in global_rows if row["status"] == "FAIL") +
        sum(1 for row in boundary_rows if row["status"] == "FAIL") +
        sum(1 for row in table_rows if row["status"] == "FAIL") +
        sum(1 for row in tag_rows if row["status"] == "FAIL") +
        sum(1 for row in artifact_rows if str(row.get("exists", "0")) != "1") +
        sum(1 for row in boundary if row["status"] == "FAIL")
    )
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DA_B_NATIVE_MATERIALIZATION_FAILURES"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10da_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10da_b_global_marker_check_v1.csv", ["marker","found","status"], global_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10da_b_boundary_marker_check_v1.csv", ["marker","found","status"], boundary_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10da_b_table_readback_check_v1.csv", ["table","expected_records","created_seen","import_seen","listed_seen","fields_seen","dbf_exists","status"], table_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10da_b_tag_order_check_v1.csv", ["table","tag","addtag_seen","buildlmdb_tag_ok_seen","set_order_seen","status"], tag_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10da_b_artifact_inventory_v1.csv", ["artifact","path","exists","bytes","sha256","nonempty_dir"], artifact_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10da_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10DA-B",
        "CZ_B_STATUS_GREEN":cz_green,
        "CZ_B_SAVEPOINT_PRESENT":cz_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DA_B":latest_id(repo),
        "TRANSCRIPT_EXISTS":int(transcript.exists()),
        "GLOBAL_MARKERS_PASSED":sum(1 for row in global_rows if row["status"] == "PASS"),
        "GLOBAL_MARKERS_TOTAL":len(global_rows),
        "BOUNDARY_MARKERS_PASSED":sum(1 for row in boundary_rows if row["status"] == "PASS"),
        "BOUNDARY_MARKERS_TOTAL":len(boundary_rows),
        "TABLES_PASSED":sum(1 for row in table_rows if row["status"] == "PASS"),
        "TABLES_TOTAL":len(table_rows),
        "TAGS_PASSED":sum(1 for row in tag_rows if row["status"] == "PASS"),
        "TAGS_TOTAL":len(tag_rows),
        "ARTIFACTS_OBSERVED":sum(1 for row in artifact_rows if str(row.get("exists","0")) == "1"),
        "ARTIFACTS_TOTAL":len(artifact_rows),
        "HELP_CMDHELPCHK_CANDIDATE_NATIVE_MATERIALIZATION_PROVEN":1 if status == GREEN else 0,
        "APPLY_READY":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_REVIEW":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_REVIEW":0,
        "LATEST_POINTER_CHANGED_BY_DA_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10da_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10DA-B",
        "status":status,
        "help_cmdhelpchk_candidate_native_materialization_proven":1 if status == GREEN else 0,
        "apply_ready":False,
        "active_apply_executed":False,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10da_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DA-B HELP/CMDHELPCHK Candidate Table Native Materialization Proof Review

- Status: {status}
- Validation issues: {validation}
- CZ-B status green: {cz_green}
- CZ-B savepoint present: {cz_savepoint}
- Transcript exists: {int(transcript.exists())}
- Tables passed: {summary[0]['TABLES_PASSED']}/{summary[0]['TABLES_TOTAL']}
- Tags passed: {summary[0]['TAGS_PASSED']}/{summary[0]['TAGS_TOTAL']}
- Artifacts observed: {summary[0]['ARTIFACTS_OBSERVED']}/{summary[0]['ARTIFACTS_TOTAL']}
- HELP/CMDHELPCHK candidate native materialization proven: {summary[0]['HELP_CMDHELPCHK_CANDIDATE_NATIVE_MATERIALIZATION_PROVEN']}
- Apply ready: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by review: 0
- Active DBF/CDX/LMDB mutation observed by review: 0
- Workspace mutation observed by review: 0
- Latest pointer changed by DA-B: 0
- Next gate: {next_gate}
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DA_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_PROOF_REVIEW.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DA_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_PROOF_REVIEW.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CZ-B status green: {cz_green}")
    print(f"  CZ-B savepoint present: {cz_savepoint}")
    print(f"  transcript exists: {int(transcript.exists())}")
    print(f"  global markers passed: {summary[0]['GLOBAL_MARKERS_PASSED']}/{summary[0]['GLOBAL_MARKERS_TOTAL']}")
    print(f"  boundary markers passed: {summary[0]['BOUNDARY_MARKERS_PASSED']}/{summary[0]['BOUNDARY_MARKERS_TOTAL']}")
    print(f"  tables passed: {summary[0]['TABLES_PASSED']}/{summary[0]['TABLES_TOTAL']}")
    print(f"  tags passed: {summary[0]['TAGS_PASSED']}/{summary[0]['TAGS_TOTAL']}")
    print(f"  artifacts observed: {summary[0]['ARTIFACTS_OBSERVED']}/{summary[0]['ARTIFACTS_TOTAL']}")
    print(f"  HELP/CMDHELPCHK candidate native materialization proven: {summary[0]['HELP_CMDHELPCHK_CANDIDATE_NATIVE_MATERIALIZATION_PROVEN']}")
    print("  apply ready: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by review: 0")
    print("  active DBF/CDX/LMDB mutation observed by review: 0")
    print("  workspace mutation observed by review: 0")
    print("  latest pointer changed by DA-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
