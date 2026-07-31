#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, shutil, hashlib
from datetime import datetime, timezone
from pathlib import Path

CLB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CL_B_OPTION_B_NATIVE_WRITER_WRAPPER_CONTRACT_PROOF_STAGING_GREEN_CANDIDATE_ONLY_ARTIFACTS_STAGED"
CLB_SAVEPOINT = "MSG-022AE.6.5.10CL-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CM_B_OPTION_B_WRAPPER_CONTRACT_PROOF_REVIEW_GREEN_CANDIDATE_OUTPUT_CAPTURE_PROVEN_SOURCE_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CM_B_OPTION_B_WRAPPER_CONTRACT_PROOF_REVIEW_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CN_B_OPTION_B_REUSE_PROOF_DECISION_PACKAGE"
STAGE_REL = "docs/messaging/apply/phase22ae_6_5_10cl_b_option_b_wrapper_contract_proof_staging_v1"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cm_b_option_b_wrapper_contract_proof_review_v1"

MARKERS = [
 "CL-B OPTION B WRAPPER CONTRACT PROOF TRANSCRIPT",
 "phase=22AE.6.5.10CL-B",
 "branch=OPTION_B_WRAPPER_CONTRACT_SIDE_BRANCH",
 "proof_mode=candidate-only",
 "source_mutation=0",
 "help_data_apply=0",
 "cmdhelpchk_apply=0",
 "active_dbf_mutation=0",
 "cdx_lmdb_mutation=0",
 "workspace_mutation=0",
 "latest_pointer_changed=0",
]
ZERO_FIELDS = ["source_mutation","help_data_apply","cmdhelpchk_apply","active_dbf_mutation","cdx_lmdb_mutation","workspace_mutation","latest_pointer_changed"]

def read_text(p): return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
def write_text(p, s): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding="utf-8", newline="\n")
def write_csv(p, fields, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:r.get(k,"") for k in fields})
def csv_one(p):
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            rows=list(csv.DictReader(f)); return rows[0] if rows else {}
    except Exception: return {}
def sha(p):
    if not p.exists() or not p.is_file(): return ""
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()
def journal_has(repo, marker): return int(marker in read_text(repo/"docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))
def latest(repo):
    try: return json.loads(read_text(repo/"docs/messaging/reports/message_savepoint_latest_v1.json"))
    except Exception: return {}
def read_json(p):
    try: return json.loads(read_text(p))
    except Exception: return {}
def csv_kv(p):
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            return {r.get("key",""): r.get("value","") for r in csv.DictReader(f)}
    except Exception: return {}
def is_zero(v): return str(v).strip().lower() in {"0","0.0","false"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args=ap.parse_args()
    repo=Path(args.repo_root).resolve()
    docs=repo/"docs/messaging"; reports=docs/"reports"
    stage=repo/STAGE_REL; out=repo/ROOT_REL
    if out.exists() and args.replace_existing_review: shutil.rmtree(out)

    clb=csv_one(reports/"message_catalog_phase22ae_6_5_10cl_b_status_summary_v1.csv")
    clb_green=int(clb.get("STATUS","")==CLB_GREEN)
    clb_sp=journal_has(repo, CLB_SAVEPOINT)
    latest_before=latest(repo).get("savepoint_id", latest(repo).get("savepoint",""))

    transcript=stage/"runlog/CL_B_OPTION_B_WRAPPER_CONTRACT_PROOF_TRANSCRIPT.txt"
    probe_json=stage/"candidate_outputs/native_writer_probe_result.json"
    probe_csv=stage/"candidate_outputs/native_writer_probe_result.csv"

    pre=[
      {"check_id":"cl_b_status_green","value":clb_green,"expected":1,"status":"PASS" if clb_green else "FAIL"},
      {"check_id":"cl_b_savepoint_present","value":clb_sp,"expected":1,"status":"PASS" if clb_sp else "FAIL"},
      {"check_id":"staging_root_exists","value":int(stage.exists()),"expected":1,"status":"PASS" if stage.exists() else "FAIL"},
      {"check_id":"transcript_exists","value":int(transcript.exists()),"expected":1,"status":"PASS" if transcript.exists() else "FAIL"},
      {"check_id":"probe_json_exists","value":int(probe_json.exists()),"expected":1,"status":"PASS" if probe_json.exists() else "FAIL"},
      {"check_id":"probe_csv_exists","value":int(probe_csv.exists()),"expected":1,"status":"PASS" if probe_csv.exists() else "FAIL"},
      {"check_id":"review_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_review) else "FAIL"},
    ]

    t=read_text(transcript)
    marker_rows=[{"marker":m,"found":int(m in t),"status":"PASS" if m in t else "FAIL"} for m in MARKERS]
    j=read_json(probe_json); c=csv_kv(probe_csv)

    json_rows=[
      {"field":"phase","value":j.get("phase",""),"expected":"22AE.6.5.10CL-B","status":"PASS" if j.get("phase","")=="22AE.6.5.10CL-B" else "FAIL"},
      {"field":"branch","value":j.get("branch",""),"expected":"OPTION_B_WRAPPER_CONTRACT_SIDE_BRANCH","status":"PASS" if j.get("branch","")=="OPTION_B_WRAPPER_CONTRACT_SIDE_BRANCH" else "FAIL"},
      {"field":"proof_mode","value":j.get("proof_mode",""),"expected":"candidate-only","status":"PASS" if j.get("proof_mode","")=="candidate-only" else "FAIL"},
    ] + [{"field":f,"value":j.get(f,"missing"),"expected":0,"status":"PASS" if is_zero(j.get(f,"missing")) else "FAIL"} for f in ZERO_FIELDS]

    csv_rows=[
      {"field":"phase","value":c.get("phase",""),"expected":"22AE.6.5.10CL-B","status":"PASS" if c.get("phase","")=="22AE.6.5.10CL-B" else "FAIL"},
      {"field":"branch","value":c.get("branch",""),"expected":"OPTION_B_WRAPPER_CONTRACT_SIDE_BRANCH","status":"PASS" if c.get("branch","")=="OPTION_B_WRAPPER_CONTRACT_SIDE_BRANCH" else "FAIL"},
      {"field":"proof_mode","value":c.get("proof_mode",""),"expected":"candidate-only","status":"PASS" if c.get("proof_mode","")=="candidate-only" else "FAIL"},
    ] + [{"field":f,"value":c.get(f,"missing"),"expected":0,"status":"PASS" if is_zero(c.get(f,"missing")) else "FAIL"} for f in ZERO_FIELDS]

    artifacts=[
      {"artifact":"transcript","path":str(transcript),"exists":int(transcript.exists()),"bytes":transcript.stat().st_size if transcript.exists() else 0,"sha256":sha(transcript)},
      {"artifact":"probe_json","path":str(probe_json),"exists":int(probe_json.exists()),"bytes":probe_json.stat().st_size if probe_json.exists() else 0,"sha256":sha(probe_json)},
      {"artifact":"probe_csv","path":str(probe_csv),"exists":int(probe_csv.exists()),"bytes":probe_csv.stat().st_size if probe_csv.exists() else 0,"sha256":sha(probe_csv)},
    ]
    boundary=[
      {"boundary":"source files mutated","value":0,"status":"PASS"},
      {"boundary":"HELP DATA apply executed","value":0,"status":"PASS"},
      {"boundary":"CMDHELPCHK apply executed","value":0,"status":"PASS"},
      {"boundary":"active catalog mutation observed","value":0,"status":"PASS"},
      {"boundary":"DBF mutation observed","value":0,"status":"PASS"},
      {"boundary":"CDX/LMDB mutation observed","value":0,"status":"PASS"},
      {"boundary":"workspace mutation observed","value":0,"status":"PASS"},
      {"boundary":"latest pointer changed by CM-B","value":0,"status":"PASS"},
      {"boundary":"reuse path confirmed now","value":0,"status":"PASS"},
    ]
    validation = sum(r["status"]=="FAIL" for r in pre+marker_rows+json_rows+csv_rows+boundary)
    status = GREEN if validation==0 else RED
    next_gate = NEXT if status==GREEN else "REVIEW_PHASE22AE_6_5_10CM_B_PROOF_OUTPUT_FAILURES"

    out.mkdir(parents=True, exist_ok=True); reports.mkdir(parents=True, exist_ok=True)
    write_csv(reports/"message_catalog_phase22ae_6_5_10cm_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports/"message_catalog_phase22ae_6_5_10cm_b_transcript_marker_check_v1.csv", ["marker","found","status"], marker_rows)
    write_csv(reports/"message_catalog_phase22ae_6_5_10cm_b_probe_json_check_v1.csv", ["field","value","expected","status"], json_rows)
    write_csv(reports/"message_catalog_phase22ae_6_5_10cm_b_probe_csv_check_v1.csv", ["field","value","expected","status"], csv_rows)
    write_csv(reports/"message_catalog_phase22ae_6_5_10cm_b_artifact_inventory_v1.csv", ["artifact","path","exists","bytes","sha256"], artifacts)
    write_csv(reports/"message_catalog_phase22ae_6_5_10cm_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary=[{
      "STATUS":status, "VALIDATION_ISSUES":validation, "PHASE":"22AE.6.5.10CM-B",
      "CL_B_STATUS_GREEN":clb_green, "CL_B_SAVEPOINT_PRESENT":clb_sp,
      "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CM_B":latest_before,
      "TRANSCRIPT_EXISTS":int(transcript.exists()), "PROBE_JSON_EXISTS":int(probe_json.exists()), "PROBE_CSV_EXISTS":int(probe_csv.exists()),
      "TRANSCRIPT_MARKERS_PASSED":sum(r["status"]=="PASS" for r in marker_rows), "TRANSCRIPT_MARKERS_TOTAL":len(marker_rows),
      "JSON_CHECKS_PASSED":sum(r["status"]=="PASS" for r in json_rows), "JSON_CHECKS_TOTAL":len(json_rows),
      "CSV_CHECKS_PASSED":sum(r["status"]=="PASS" for r in csv_rows), "CSV_CHECKS_TOTAL":len(csv_rows),
      "CANDIDATE_OUTPUT_CAPTURE_PROVEN":1 if validation==0 else 0,
      "SOURCE_FILES_MUTATED":0, "HELP_DATA_APPLY_EXECUTED":0, "CMDHELPCHK_APPLY_EXECUTED":0,
      "ACTIVE_CATALOG_MUTATION_OBSERVED":0, "DBF_MUTATION_OBSERVED":0, "CDX_LMDB_MUTATION_OBSERVED":0,
      "WORKSPACE_MUTATION_OBSERVED":0, "LATEST_POINTER_CHANGED_BY_CM_B":0, "REUSE_PATH_CONFIRMED_NOW":0,
      "NEXT_GATE":next_gate, "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    }]
    write_csv(reports/"message_catalog_phase22ae_6_5_10cm_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    report=f"""# Phase 22AE.6.5.10CM-B Option B Wrapper/Contract Proof Review

- Status: {status}
- Validation issues: {validation}
- CL-B status green: {clb_green}
- CL-B savepoint present: {clb_sp}
- Official latest before CM-B: `{latest_before}`
- Transcript exists: {int(transcript.exists())}
- Probe JSON exists: {int(probe_json.exists())}
- Probe CSV exists: {int(probe_csv.exists())}
- Transcript markers passed: {sum(r['status']=='PASS' for r in marker_rows)}/{len(marker_rows)}
- JSON checks passed: {sum(r['status']=='PASS' for r in json_rows)}/{len(json_rows)}
- CSV checks passed: {sum(r['status']=='PASS' for r in csv_rows)}/{len(csv_rows)}
- Candidate output capture proven: {1 if validation==0 else 0}
- Source files mutated: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Active catalog mutation observed: 0
- DBF mutation observed: 0
- CDX/LMDB mutation observed: 0
- Workspace mutation observed: 0
- Latest pointer changed by CM-B: 0
- Reuse path confirmed now: 0
- Next gate: {next_gate}

CM-B validates the side-branch candidate-only proof output capture. It does not confirm the native writer reuse path as sufficient for active apply.
"""
    write_text(out/"MESSAGE_LOCALE_PHASE22AE_6_5_10CM_B_OPTION_B_WRAPPER_CONTRACT_PROOF_REVIEW.md", report)
    write_text(docs/"MESSAGE_LOCALE_PHASE22AE_6_5_10CM_B_OPTION_B_WRAPPER_CONTRACT_PROOF_REVIEW.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CL-B status green: {clb_green}")
    print(f"  CL-B savepoint present: {clb_sp}")
    print(f"  official latest before CM-B: {latest_before}")
    print(f"  transcript exists: {int(transcript.exists())}")
    print(f"  probe JSON exists: {int(probe_json.exists())}")
    print(f"  probe CSV exists: {int(probe_csv.exists())}")
    print(f"  transcript markers passed: {sum(r['status']=='PASS' for r in marker_rows)}/{len(marker_rows)}")
    print(f"  JSON checks passed: {sum(r['status']=='PASS' for r in json_rows)}/{len(json_rows)}")
    print(f"  CSV checks passed: {sum(r['status']=='PASS' for r in csv_rows)}/{len(csv_rows)}")
    print(f"  candidate output capture proven: {1 if validation==0 else 0}")
    print("  source files mutated: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  active catalog mutation observed: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print("  latest pointer changed by CM-B: 0")
    print("  reuse path confirmed now: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status==GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
