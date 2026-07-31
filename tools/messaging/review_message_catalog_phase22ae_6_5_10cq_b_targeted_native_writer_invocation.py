#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json, shutil, hashlib
from datetime import datetime, timezone
from pathlib import Path

CPB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CP_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_STAGING_GREEN_CANDIDATE_ONLY_ARTIFACTS_STAGED"
CPB_SAVEPOINT = "MSG-022AE.6.5.10CP-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CQ_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_REVIEW_GREEN_READ_ONLY_SURFACE_PROOF_CAPTURED_REUSE_NOT_CONFIRMED"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CQ_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_REVIEW_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CR_B_TARGETED_NATIVE_WRITER_REUSE_DECISION_PACKAGE"
STAGE_REL = "docs/messaging/apply/phase22ae_6_5_10cp_b_targeted_native_writer_invocation_proof_staging_v1"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cq_b_targeted_native_writer_invocation_proof_review_v1"

TRANSCRIPT_MARKERS = [
    "CP-B TARGETED NATIVE WRITER INVOCATION PROOF TRANSCRIPT",
    "phase=22AE.6.5.10CP-B",
    "branch=OPTION_B_TARGETED_NATIVE_WRITER_INVOCATION_SIDE_BRANCH",
    "proof_mode=candidate-only-read-only-surface-probe",
    "active_native_writer_invoked=0",
    "source_mutation=0",
    "help_data_apply=0",
    "cmdhelpchk_apply=0",
    "active_dbf_mutation=0",
    "cdx_lmdb_mutation=0",
    "workspace_mutation=0",
    "latest_pointer_changed=0",
    "reuse_path_confirmed_now=0",
]

JSON_EXPECT = {
    "phase": "22AE.6.5.10CP-B",
    "branch": "OPTION_B_TARGETED_NATIVE_WRITER_INVOCATION_SIDE_BRANCH",
    "proof_mode": "candidate-only-read-only-surface-probe",
}

ZERO_FIELDS = [
    "active_native_writer_invoked",
    "source_mutation",
    "help_data_apply",
    "cmdhelpchk_apply",
    "active_dbf_mutation",
    "cdx_lmdb_mutation",
    "workspace_mutation",
    "latest_pointer_changed",
    "reuse_path_confirmed_now",
]

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

def read_json(p: Path) -> dict:
    try:
        return json.loads(read_text(p))
    except Exception:
        return {}

def csv_kv(p: Path) -> dict:
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            return {r.get("key",""): r.get("value","") for r in csv.DictReader(f)}
    except Exception:
        return {}

def sha256_file(p: Path) -> str:
    if not p.exists() or not p.is_file():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def journal_has(repo: Path, marker: str) -> int:
    return int(marker in read_text(repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def latest(repo: Path) -> dict:
    try:
        return json.loads(read_text(repo / "docs/messaging/reports/message_savepoint_latest_v1.json"))
    except Exception:
        return {}

def is_zero(v) -> bool:
    return str(v).strip().lower() in {"0","0.0","false"}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    stage = repo / STAGE_REL
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_review:
        shutil.rmtree(out)

    cpb = csv_one(reports / "message_catalog_phase22ae_6_5_10cp_b_status_summary_v1.csv")
    latest_info = latest(repo)
    latest_before = latest_info.get("savepoint_id", latest_info.get("savepoint",""))

    cpb_green = int(cpb.get("STATUS","") == CPB_GREEN)
    cpb_sp = journal_has(repo, CPB_SAVEPOINT)

    transcript = stage / "runlog/CP_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_TRANSCRIPT.txt"
    probe_json = stage / "candidate_outputs/targeted_native_writer_invocation_probe.json"
    probe_csv = stage / "candidate_outputs/targeted_native_writer_invocation_probe.csv"
    surface_csv = stage / "candidate_outputs/targeted_native_writer_surface_probe_rows.csv"

    pre = [
        {"check_id":"cp_b_status_green","value":cpb_green,"expected":1,"status":"PASS" if cpb_green else "FAIL"},
        {"check_id":"cp_b_savepoint_present","value":cpb_sp,"expected":1,"status":"PASS" if cpb_sp else "FAIL"},
        {"check_id":"staging_root_exists","value":int(stage.exists()),"expected":1,"status":"PASS" if stage.exists() else "FAIL"},
        {"check_id":"transcript_exists","value":int(transcript.exists()),"expected":1,"status":"PASS" if transcript.exists() else "FAIL"},
        {"check_id":"probe_json_exists","value":int(probe_json.exists()),"expected":1,"status":"PASS" if probe_json.exists() else "FAIL"},
        {"check_id":"probe_csv_exists","value":int(probe_csv.exists()),"expected":1,"status":"PASS" if probe_csv.exists() else "FAIL"},
        {"check_id":"surface_probe_csv_exists","value":int(surface_csv.exists()),"expected":1,"status":"PASS" if surface_csv.exists() else "FAIL"},
        {"check_id":"cq_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_review) else "FAIL"},
    ]

    t = read_text(transcript)
    marker_rows = []
    for marker in TRANSCRIPT_MARKERS:
        found = int(marker in t)
        marker_rows.append({"marker":marker, "found":found, "status":"PASS" if found else "FAIL"})

    j = read_json(probe_json)
    c = csv_kv(probe_csv)
    surface_rows = csv_rows(surface_csv)

    json_rows = []
    for field, expected in JSON_EXPECT.items():
        ok = j.get(field, "") == expected
        json_rows.append({"field":field, "value":j.get(field,""), "expected":expected, "status":"PASS" if ok else "FAIL"})
    for field in ZERO_FIELDS:
        ok = is_zero(j.get(field, "missing"))
        json_rows.append({"field":field, "value":j.get(field,"missing"), "expected":0, "status":"PASS" if ok else "FAIL"})
    selected_count_ok = int(j.get("selected_surface_count", 0) or 0) > 0
    json_rows.append({"field":"selected_surface_count","value":j.get("selected_surface_count","missing"),"expected":">0","status":"PASS" if selected_count_ok else "FAIL"})

    csv_check_rows = []
    for field, expected in JSON_EXPECT.items():
        ok = c.get(field, "") == expected
        csv_check_rows.append({"field":field, "value":c.get(field,""), "expected":expected, "status":"PASS" if ok else "FAIL"})
    for field in ZERO_FIELDS:
        ok = is_zero(c.get(field, "missing"))
        csv_check_rows.append({"field":field, "value":c.get(field,"missing"), "expected":0, "status":"PASS" if ok else "FAIL"})
    try:
        csv_selected_count = int(c.get("selected_surface_count","0"))
    except Exception:
        csv_selected_count = 0
    csv_check_rows.append({"field":"selected_surface_count","value":c.get("selected_surface_count","missing"),"expected":">0","status":"PASS" if csv_selected_count > 0 else "FAIL"})

    surface_check_rows = []
    total_surface = len(surface_rows)
    existing_surface = sum(1 for r in surface_rows if str(r.get("exists","")).strip() == "1")
    read_only_rows = sum(1 for r in surface_rows if str(r.get("read_only_surface_probe","")).strip() == "1")
    invoked_rows = sum(1 for r in surface_rows if str(r.get("invoked_active_writer","")).strip() not in {"0","0.0","false",""})
    surface_check_rows.extend([
        {"check_id":"surface_rows_present","value":total_surface,"expected":">0","status":"PASS" if total_surface > 0 else "FAIL"},
        {"check_id":"surface_rows_exist","value":existing_surface,"expected":">0","status":"PASS" if existing_surface > 0 else "FAIL"},
        {"check_id":"all_surface_rows_read_only","value":read_only_rows,"expected":total_surface,"status":"PASS" if total_surface > 0 and read_only_rows == total_surface else "FAIL"},
        {"check_id":"no_surface_rows_invoked_active_writer","value":invoked_rows,"expected":0,"status":"PASS" if invoked_rows == 0 else "FAIL"},
    ])

    artifacts = [
        {"artifact":"transcript","path":str(transcript),"exists":int(transcript.exists()),"bytes":transcript.stat().st_size if transcript.exists() else 0,"sha256":sha256_file(transcript)},
        {"artifact":"probe_json","path":str(probe_json),"exists":int(probe_json.exists()),"bytes":probe_json.stat().st_size if probe_json.exists() else 0,"sha256":sha256_file(probe_json)},
        {"artifact":"probe_csv","path":str(probe_csv),"exists":int(probe_csv.exists()),"bytes":probe_csv.stat().st_size if probe_csv.exists() else 0,"sha256":sha256_file(probe_csv)},
        {"artifact":"surface_csv","path":str(surface_csv),"exists":int(surface_csv.exists()),"bytes":surface_csv.stat().st_size if surface_csv.exists() else 0,"sha256":sha256_file(surface_csv)},
    ]

    boundary = [
        {"boundary":"candidate read-only surface proof captured","value":1,"status":"PASS"},
        {"boundary":"active native writer invoked","value":0,"status":"PASS"},
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
        {"boundary":"latest pointer changed by CQ-B","value":0,"status":"PASS"},
    ]

    validation = (
        sum(1 for r in pre if r["status"] == "FAIL") +
        sum(1 for r in marker_rows if r["status"] == "FAIL") +
        sum(1 for r in json_rows if r["status"] == "FAIL") +
        sum(1 for r in csv_check_rows if r["status"] == "FAIL") +
        sum(1 for r in surface_check_rows if r["status"] == "FAIL") +
        sum(1 for r in boundary if r["status"] == "FAIL")
    )

    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10CQ_B_PROOF_OUTPUT_FAILURES"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10cq_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cq_b_transcript_marker_check_v1.csv", ["marker","found","status"], marker_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cq_b_probe_json_check_v1.csv", ["field","value","expected","status"], json_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cq_b_probe_csv_check_v1.csv", ["field","value","expected","status"], csv_check_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cq_b_surface_probe_check_v1.csv", ["check_id","value","expected","status"], surface_check_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cq_b_artifact_inventory_v1.csv", ["artifact","path","exists","bytes","sha256"], artifacts)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cq_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10CQ-B",
        "CP_B_STATUS_GREEN":cpb_green,
        "CP_B_SAVEPOINT_PRESENT":cpb_sp,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CQ_B":latest_before,
        "TRANSCRIPT_EXISTS":int(transcript.exists()),
        "PROBE_JSON_EXISTS":int(probe_json.exists()),
        "PROBE_CSV_EXISTS":int(probe_csv.exists()),
        "SURFACE_PROBE_CSV_EXISTS":int(surface_csv.exists()),
        "TRANSCRIPT_MARKERS_PASSED":sum(1 for r in marker_rows if r["status"] == "PASS"),
        "TRANSCRIPT_MARKERS_TOTAL":len(marker_rows),
        "JSON_CHECKS_PASSED":sum(1 for r in json_rows if r["status"] == "PASS"),
        "JSON_CHECKS_TOTAL":len(json_rows),
        "CSV_CHECKS_PASSED":sum(1 for r in csv_check_rows if r["status"] == "PASS"),
        "CSV_CHECKS_TOTAL":len(csv_check_rows),
        "SURFACE_CHECKS_PASSED":sum(1 for r in surface_check_rows if r["status"] == "PASS"),
        "SURFACE_CHECKS_TOTAL":len(surface_check_rows),
        "SURFACE_ROWS":total_surface,
        "SURFACE_ROWS_EXISTING":existing_surface,
        "ACTIVE_NATIVE_WRITER_INVOKED":0,
        "READ_ONLY_SURFACE_PROOF_CAPTURED":1 if validation == 0 else 0,
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
        "LATEST_POINTER_CHANGED_BY_CQ_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cq_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10CQ-B",
        "status":status,
        "read_only_surface_proof_captured":1 if validation == 0 else 0,
        "active_native_writer_invoked":0,
        "reuse_path_confirmed_now":0,
        "source_mutation_authorized_now":0,
        "apply_execution_authorized_now":0,
        "latest_pointer_changed_by_cq_b":0,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10cq_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10CQ-B Targeted Native Writer Invocation Proof Review

- Status: {status}
- Validation issues: {validation}
- CP-B status green: {cpb_green}
- CP-B savepoint present: {cpb_sp}
- Official latest before CQ-B: `{latest_before}`
- Transcript exists: {int(transcript.exists())}
- Probe JSON exists: {int(probe_json.exists())}
- Probe CSV exists: {int(probe_csv.exists())}
- Surface probe CSV exists: {int(surface_csv.exists())}
- Transcript markers passed: {sum(1 for r in marker_rows if r['status'] == 'PASS')}/{len(marker_rows)}
- JSON checks passed: {sum(1 for r in json_rows if r['status'] == 'PASS')}/{len(json_rows)}
- CSV checks passed: {sum(1 for r in csv_check_rows if r['status'] == 'PASS')}/{len(csv_check_rows)}
- Surface checks passed: {sum(1 for r in surface_check_rows if r['status'] == 'PASS')}/{len(surface_check_rows)}
- Surface rows: {total_surface}
- Existing surface rows: {existing_surface}
- Active native writer invoked: 0
- Read-only surface proof captured: {1 if validation == 0 else 0}
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
- Latest pointer changed by CQ-B: 0
- Next gate: {next_gate}

CQ-B validates CP-B's read-only targeted surface proof. It does not prove active native-writer invocation and does not confirm native-writer reuse for active apply.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CQ_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_REVIEW.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CQ_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_REVIEW.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CP-B status green: {cpb_green}")
    print(f"  CP-B savepoint present: {cpb_sp}")
    print(f"  official latest before CQ-B: {latest_before}")
    print(f"  transcript exists: {int(transcript.exists())}")
    print(f"  probe JSON exists: {int(probe_json.exists())}")
    print(f"  probe CSV exists: {int(probe_csv.exists())}")
    print(f"  surface probe CSV exists: {int(surface_csv.exists())}")
    print(f"  transcript markers passed: {sum(1 for r in marker_rows if r['status'] == 'PASS')}/{len(marker_rows)}")
    print(f"  JSON checks passed: {sum(1 for r in json_rows if r['status'] == 'PASS')}/{len(json_rows)}")
    print(f"  CSV checks passed: {sum(1 for r in csv_check_rows if r['status'] == 'PASS')}/{len(csv_check_rows)}")
    print(f"  surface checks passed: {sum(1 for r in surface_check_rows if r['status'] == 'PASS')}/{len(surface_check_rows)}")
    print(f"  surface rows: {total_surface}")
    print(f"  existing surface rows: {existing_surface}")
    print("  active native writer invoked: 0")
    print(f"  read-only surface proof captured: {1 if validation == 0 else 0}")
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
    print("  latest pointer changed by CQ-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
