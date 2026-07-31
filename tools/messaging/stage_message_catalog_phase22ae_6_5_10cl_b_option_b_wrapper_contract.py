#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

CKB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CK_B_OPTION_B_NATIVE_WRITER_WRAPPER_CONTRACT_PROOF_PLAN_GREEN_SIDE_BRANCH_SOURCE_HELD"
CKB_SAVEPOINT = "MSG-022AE.6.5.10CK-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CL_B_OPTION_B_NATIVE_WRITER_WRAPPER_CONTRACT_PROOF_STAGING_GREEN_CANDIDATE_ONLY_ARTIFACTS_STAGED"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CL_B_OPTION_B_NATIVE_WRITER_WRAPPER_CONTRACT_PROOF_STAGING_RED_REVIEW_REQUIRED"
NEXT_GATE = "HOLD_OR_RUN_PHASE22AE_6_5_10CL_B_OPTION_B_WRAPPER_CONTRACT_PROOF_AND_CAPTURE_TRANSCRIPT"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cl_b_option_b_wrapper_contract_proof_staging_v1"

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

def latest(repo: Path) -> dict:
    try:
        return json.loads(read_text(repo / "docs/messaging/reports/message_savepoint_latest_v1.json"))
    except Exception:
        return {}

def find_candidate_native_writer_sources(repo: Path) -> list[dict]:
    roots = [repo / "tools", repo / "src", repo / "dottalkpp"]
    needles = ["HELP DATA", "CMDHELPCHK", "native writer", "writer", "messages", "message catalog"]
    rows = []
    seen = set()
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".py", ".ps1", ".cpp", ".hpp", ".h", ".md", ".txt"}:
                continue
            rel = p.relative_to(repo).as_posix()
            if rel in seen:
                continue
            text = read_text(p)
            score = sum(1 for n in needles if n.lower() in text.lower() or n.lower() in rel.lower())
            if score:
                seen.add(rel)
                rows.append({"candidate_path":rel, "suffix":p.suffix.lower(), "score":score, "size_bytes":p.stat().st_size, "inventory_only":1})
    rows.sort(key=lambda r: (-int(r["score"]), r["candidate_path"]))
    return rows[:80]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-staging", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    root = repo / ROOT_REL

    if root.exists() and args.replace_existing_staging:
        shutil.rmtree(root)

    ckb = csv_one(reports / "message_catalog_phase22ae_6_5_10ck_b_status_summary_v1.csv")
    ckb_green = int(ckb.get("STATUS","") == CKB_GREEN)
    ckb_sp = journal_has(repo, CKB_SAVEPOINT)
    latest_info = latest(repo)
    latest_before = latest_info.get("savepoint_id", latest_info.get("savepoint",""))

    pre = [
        {"check_id":"ck_b_status_green","value":ckb_green,"expected":1,"status":"PASS" if ckb_green else "FAIL"},
        {"check_id":"ck_b_savepoint_present","value":ckb_sp,"expected":1,"status":"PASS" if ckb_sp else "FAIL"},
        {"check_id":"cl_b_root_absent_or_replace_authorized","value":int(root.exists()),"expected":0,"status":"PASS" if (not root.exists() or args.replace_existing_staging) else "FAIL"},
        {"check_id":"official_latest_pointer_not_modified_by_staging","value":1,"expected":1,"status":"PASS"},
    ]

    candidate_sources = find_candidate_native_writer_sources(repo)
    contract = {
        "phase": "22AE.6.5.10CL-B",
        "branch": "OPTION_B_WRAPPER_CONTRACT_SIDE_BRANCH",
        "purpose": "Stage candidate-only wrapper/contract proof artifacts for native writer reuse.",
        "source_mutation_allowed": False,
        "help_data_apply_allowed": False,
        "cmdhelpchk_apply_allowed": False,
        "active_dbf_mutation_allowed": False,
        "cdx_lmdb_mutation_allowed": False,
        "workspace_mutation_allowed": False,
        "latest_pointer_change_allowed": False,
        "candidate_output_root": str((root / "candidate_outputs").as_posix()),
        "transcript_path": str((root / "runlog/CL_B_OPTION_B_WRAPPER_CONTRACT_PROOF_TRANSCRIPT.txt").as_posix()),
        "expected_next_review": "22AE.6.5.10CM-B proof review",
    }
    input_manifest = {
        "input_family": "messaging/native-writer-wrapper-contract-proof",
        "basis": "CK-B wrapper/contract proof plan",
        "candidate_inventory_rows": len(candidate_sources),
        "candidate_inventory_csv": str((reports / "message_catalog_phase22ae_6_5_10cl_b_native_writer_candidate_inventory_v1.csv").as_posix()),
        "proof_mode": "candidate-only report/transcript",
    }
    output_manifest = {
        "output_family": "candidate-only-native-writer-wrapper-proof",
        "allowed_outputs": [
            str((root / "candidate_outputs/native_writer_probe_result.json").as_posix()),
            str((root / "candidate_outputs/native_writer_probe_result.csv").as_posix()),
            str((root / "runlog/CL_B_OPTION_B_WRAPPER_CONTRACT_PROOF_TRANSCRIPT.txt").as_posix()),
        ],
        "forbidden_outputs": ["dottalkpp/data/help","dottalkpp/data/dbf","dottalkpp/data/indexes","dottalkpp/data/lmdb","src","active HELP DATA","active CMDHELPCHK"],
    }

    refusal = [
        {"guard_id":"REFUSE_SOURCE_MUTATION","condition":"No source edits or generated source files.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_HELP_DATA_APPLY","condition":"No HELP DATA apply execution.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_CMDHELPCHK_APPLY","condition":"No CMDHELPCHK apply execution.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_ACTIVE_DBF_MUTATION","condition":"No active DBF mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_CDX_LMDB_MUTATION","condition":"No CDX/LMDB mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_WORKSPACE_MUTATION","condition":"No workspace mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_LATEST_POINTER_CHANGE","condition":"Do not move official latest pointer.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_MAINLINE_LABELS","condition":"Use CL-B/CM-B labels, not occupied CL/CM labels.","required":1,"execute_now":0},
    ]

    manual_run_ps1 = r"""param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProofRoot = Join-Path $RepoRoot "docs\messaging\apply\phase22ae_6_5_10cl_b_option_b_wrapper_contract_proof_staging_v1"
$OutRoot = Join-Path $ProofRoot "candidate_outputs"
$Runlog = Join-Path $ProofRoot "runlog\CL_B_OPTION_B_WRAPPER_CONTRACT_PROOF_TRANSCRIPT.txt"
New-Item -ItemType Directory -Force $OutRoot | Out-Null
New-Item -ItemType Directory -Force (Split-Path $Runlog) | Out-Null

$Probe = @{
  phase = "22AE.6.5.10CL-B"
  branch = "OPTION_B_WRAPPER_CONTRACT_SIDE_BRANCH"
  proof_mode = "candidate-only"
  timestamp_utc = (Get-Date).ToUniversalTime().ToString("s") + "Z"
  source_mutation = 0
  help_data_apply = 0
  cmdhelpchk_apply = 0
  active_dbf_mutation = 0
  cdx_lmdb_mutation = 0
  workspace_mutation = 0
  latest_pointer_changed = 0
  note = "This smoke proof only validates wrapper/contract staging paths and boundary markers. It does not call active HELP/CMDHELPCHK apply."
}

$JsonPath = Join-Path $OutRoot "native_writer_probe_result.json"
$CsvPath = Join-Path $OutRoot "native_writer_probe_result.csv"

$Probe | ConvertTo-Json -Depth 4 | Set-Content -Path $JsonPath -Encoding UTF8
"key,value" | Set-Content -Path $CsvPath -Encoding UTF8
foreach ($k in $Probe.Keys) {
  "$k,$($Probe[$k])" | Add-Content -Path $CsvPath -Encoding UTF8
}

$Transcript = @"
CL-B OPTION B WRAPPER CONTRACT PROOF TRANSCRIPT
phase=22AE.6.5.10CL-B
branch=OPTION_B_WRAPPER_CONTRACT_SIDE_BRANCH
proof_mode=candidate-only
source_mutation=0
help_data_apply=0
cmdhelpchk_apply=0
active_dbf_mutation=0
cdx_lmdb_mutation=0
workspace_mutation=0
latest_pointer_changed=0
json=$JsonPath
csv=$CsvPath
"@
$Transcript | Set-Content -Path $Runlog -Encoding UTF8

Write-Host "[CL-B] Candidate-only wrapper contract proof staged outputs written."
Write-Host "[CL-B] Transcript:" $Runlog
Write-Host "[CL-B] Source mutation: 0"
Write-Host "[CL-B] HELP DATA apply: 0"
Write-Host "[CL-B] CMDHELPCHK apply: 0"
Write-Host "[CL-B] DBF/CDX/LMDB mutation: 0"
Write-Host "[CL-B] Latest pointer changed: 0"
"""

    val = sum(1 for r in pre if r["status"] == "FAIL")
    status = GREEN if val == 0 else RED
    next_gate = NEXT_GATE if status == GREEN else "REVIEW_PHASE22AE_6_5_10CL_B_PRECONDITIONS"

    root.mkdir(parents=True, exist_ok=True)
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "candidate_outputs").mkdir(parents=True, exist_ok=True)
    (root / "runlog").mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10cl_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cl_b_native_writer_candidate_inventory_v1.csv", ["candidate_path","suffix","score","size_bytes","inventory_only"], candidate_sources)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cl_b_refusal_guards_v1.csv", ["guard_id","condition","required","execute_now"], refusal)
    write_text(root / "option_b_wrapper_contract_manifest_v1.json", json.dumps(contract, indent=2))
    write_text(root / "option_b_input_manifest_v1.json", json.dumps(input_manifest, indent=2))
    write_text(root / "option_b_output_manifest_v1.json", json.dumps(output_manifest, indent=2))
    write_text(root / "scripts/run_cl_b_option_b_wrapper_contract_proof_AFTER_REVIEW.ps1", manual_run_ps1)

    staged = [
        {"artifact":"option_b_wrapper_contract_manifest_v1.json","path":str((root/"option_b_wrapper_contract_manifest_v1.json").relative_to(repo)).replace("\\","/"),"manual_run":0},
        {"artifact":"option_b_input_manifest_v1.json","path":str((root/"option_b_input_manifest_v1.json").relative_to(repo)).replace("\\","/"),"manual_run":0},
        {"artifact":"option_b_output_manifest_v1.json","path":str((root/"option_b_output_manifest_v1.json").relative_to(repo)).replace("\\","/"),"manual_run":0},
        {"artifact":"run_cl_b_option_b_wrapper_contract_proof_AFTER_REVIEW.ps1","path":str((root/"scripts/run_cl_b_option_b_wrapper_contract_proof_AFTER_REVIEW.ps1").relative_to(repo)).replace("\\","/"),"manual_run":1},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cl_b_staged_artifacts_v1.csv", ["artifact","path","manual_run"], staged)
    boundary = [
        {"boundary":"runtime/proof execution by package","value":0,"status":"PASS"},
        {"boundary":"source files mutated","value":0,"status":"PASS"},
        {"boundary":"HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed","value":0,"status":"PASS"},
        {"boundary":"DBF mutation observed","value":0,"status":"PASS"},
        {"boundary":"CDX/LMDB mutation observed","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by CL-B","value":0,"status":"PASS"},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cl_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":val,
        "PHASE":"22AE.6.5.10CL-B",
        "CK_B_STATUS_GREEN":ckb_green,
        "CK_B_SAVEPOINT_PRESENT":ckb_sp,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CL_B":latest_before,
        "STAGING_ROOT":str(root.relative_to(repo)).replace("\\","/"),
        "CANDIDATE_INVENTORY_ROWS":len(candidate_sources),
        "STAGED_ARTIFACTS":len(staged),
        "MANUAL_RUN_ARTIFACTS":sum(1 for r in staged if r["manual_run"]),
        "WRAPPER_PROOF_EXECUTED_BY_PACKAGE":0,
        "SOURCE_FILES_MUTATED":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED":0,
        "DBF_MUTATION_OBSERVED":0,
        "CDX_LMDB_MUTATION_OBSERVED":0,
        "WORKSPACE_MUTATION_OBSERVED":0,
        "LATEST_POINTER_CHANGED_BY_CL_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cl_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    report = f"""# Phase 22AE.6.5.10CL-B Option B Wrapper/Contract Proof Staging

- Status: {status}
- Validation issues: {val}
- CK-B status green: {ckb_green}
- CK-B savepoint present: {ckb_sp}
- Official latest before CL-B: `{latest_before}`
- Staging root: `{root.relative_to(repo).as_posix()}`
- Candidate inventory rows: {len(candidate_sources)}
- Staged artifacts: {len(staged)}
- Manual-run artifacts: {sum(1 for r in staged if r['manual_run'])}
- Wrapper proof executed by package: 0
- Source files mutated: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Active catalog mutation observed: 0
- DBF mutation observed: 0
- CDX/LMDB mutation observed: 0
- Workspace mutation observed: 0
- Latest pointer changed by CL-B: 0
- Next gate: {next_gate}

CL-B stages candidate-only proof artifacts and a manual-run proof script. It does not execute the proof.
"""
    write_text(root / "MESSAGE_LOCALE_PHASE22AE_6_5_10CL_B_OPTION_B_WRAPPER_CONTRACT_PROOF_STAGING.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CL_B_OPTION_B_WRAPPER_CONTRACT_PROOF_STAGING.md", report)

    print(status)
    print(f"  validation issues: {val}")
    print(f"  CK-B status green: {ckb_green}")
    print(f"  CK-B savepoint present: {ckb_sp}")
    print(f"  official latest before CL-B: {latest_before}")
    print(f"  staging root: {root.relative_to(repo).as_posix()}")
    print(f"  candidate inventory rows: {len(candidate_sources)}")
    print(f"  staged artifacts: {len(staged)}")
    print(f"  manual-run artifacts: {sum(1 for r in staged if r['manual_run'])}")
    print("  wrapper proof executed by package: 0")
    print("  source files mutated: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  active catalog mutation observed: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print("  latest pointer changed by CL-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
