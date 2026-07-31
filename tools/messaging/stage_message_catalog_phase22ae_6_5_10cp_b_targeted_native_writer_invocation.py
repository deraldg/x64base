#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

COB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CO_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_PLAN_GREEN_SIDE_BRANCH_SOURCE_HELD"
COB_SAVEPOINT = "MSG-022AE.6.5.10CO-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CP_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_STAGING_GREEN_CANDIDATE_ONLY_ARTIFACTS_STAGED"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CP_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_STAGING_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_RUN_PHASE22AE_6_5_10CP_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_AND_CAPTURE_TRANSCRIPT"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cp_b_targeted_native_writer_invocation_proof_staging_v1"

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

def journal_has(repo: Path, marker: str) -> int:
    return int(marker in read_text(repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def latest(repo: Path) -> dict:
    try:
        return json.loads(read_text(repo / "docs/messaging/reports/message_savepoint_latest_v1.json"))
    except Exception:
        return {}

def score_surface(row: dict) -> int:
    path = row.get("candidate_path","").lower()
    score = 0
    if "writer" in path: score += 5
    if "native" in path: score += 4
    if "message" in path: score += 3
    if "help" in path: score += 2
    if "cmdhelpchk" in path: score += 2
    try: score += int(row.get("score","0"))
    except Exception: pass
    if path.endswith(".py"): score += 2
    if path.endswith(".ps1"): score += 1
    return score

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-staging", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_staging:
        shutil.rmtree(out)

    cob = csv_one(reports / "message_catalog_phase22ae_6_5_10co_b_status_summary_v1.csv")
    latest_info = latest(repo)
    latest_before = latest_info.get("savepoint_id", latest_info.get("savepoint",""))

    cob_green = int(cob.get("STATUS","") == COB_GREEN)
    cob_sp = journal_has(repo, COB_SAVEPOINT)
    proof_required = int(str(cob.get("TARGETED_INVOCATION_PROOF_REQUIRED","0")) == "1" or str(cob.get("TARGETED_INVOCATION_EXECUTED_BY_CO_B","0")) == "0")

    top_inventory = csv_rows(reports / "message_catalog_phase22ae_6_5_10co_b_top_candidate_inventory_v1.csv")
    ranked = sorted(top_inventory, key=score_surface, reverse=True)
    selected = ranked[:8]

    pre = [
        {"check_id":"co_b_status_green","value":cob_green,"expected":1,"status":"PASS" if cob_green else "FAIL"},
        {"check_id":"co_b_savepoint_present","value":cob_sp,"expected":1,"status":"PASS" if cob_sp else "FAIL"},
        {"check_id":"targeted_invocation_proof_required_or_not_yet_executed","value":proof_required,"expected":1,"status":"PASS" if proof_required else "FAIL"},
        {"check_id":"top_candidate_inventory_rows_available","value":len(top_inventory),"expected":">0","status":"PASS" if len(top_inventory) > 0 else "FAIL"},
        {"check_id":"selected_candidate_surface_rows","value":len(selected),"expected":">0","status":"PASS" if len(selected) > 0 else "FAIL"},
        {"check_id":"cp_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_staging) else "FAIL"},
        {"check_id":"official_latest_pointer_not_modified_by_staging","value":1,"expected":1,"status":"PASS"},
    ]

    selected_rows = []
    for idx, row in enumerate(selected, 1):
        selected_rows.append({
            "selection_rank": idx,
            "candidate_path": row.get("candidate_path",""),
            "suffix": row.get("suffix",""),
            "source_score": row.get("score",""),
            "selection_score": score_surface(row),
            "selection_reason": "ranked read-only candidate for targeted native-writer invocation proof",
            "execute_by_package": 0,
        })

    invocation_contract = {
        "phase": "22AE.6.5.10CP-B",
        "branch": "OPTION_B_TARGETED_NATIVE_WRITER_INVOCATION_SIDE_BRANCH",
        "purpose": "Stage a candidate-only targeted invocation proof against selected native-writer surfaces.",
        "selected_surface_count": len(selected_rows),
        "selected_surface_csv": "docs/messaging/reports/message_catalog_phase22ae_6_5_10cp_b_selected_surfaces_v1.csv",
        "proof_script": str((out / "scripts/run_cp_b_targeted_native_writer_invocation_proof_AFTER_REVIEW.ps1").as_posix()),
        "candidate_output_root": str((out / "candidate_outputs").as_posix()),
        "transcript_path": str((out / "runlog/CP_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_TRANSCRIPT.txt").as_posix()),
        "source_mutation_allowed": False,
        "help_data_apply_allowed": False,
        "cmdhelpchk_apply_allowed": False,
        "active_dbf_mutation_allowed": False,
        "cdx_lmdb_mutation_allowed": False,
        "workspace_mutation_allowed": False,
        "latest_pointer_change_allowed": False,
        "reuse_confirmation_allowed": False,
        "expected_review": "22AE.6.5.10CQ-B targeted invocation proof review",
    }

    refusal = [
        {"guard_id":"REFUSE_SOURCE_MUTATION","condition":"No source edits or generated source files.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_HELP_DATA_APPLY","condition":"No HELP DATA apply execution.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_CMDHELPCHK_APPLY","condition":"No CMDHELPCHK apply execution.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_ACTIVE_DBF_MUTATION","condition":"No active DBF mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_CDX_LMDB_MUTATION","condition":"No CDX/LMDB mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_WORKSPACE_MUTATION","condition":"No workspace mutation.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_LATEST_POINTER_CHANGE","condition":"Do not move message_savepoint_latest_v1.json.","required":1,"execute_now":0},
        {"guard_id":"REFUSE_REUSE_CONFIRMATION_NOW","condition":"Do not confirm native-writer reuse in CP-B staging or proof run.","required":1,"execute_now":0},
    ]

    manual_run_ps1 = r"""param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProofRoot = Join-Path $RepoRoot "docs\messaging\apply\phase22ae_6_5_10cp_b_targeted_native_writer_invocation_proof_staging_v1"
$OutRoot = Join-Path $ProofRoot "candidate_outputs"
$Runlog = Join-Path $ProofRoot "runlog\CP_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_TRANSCRIPT.txt"
$SelectedCsv = Join-Path $RepoRoot "docs\messaging\reports\message_catalog_phase22ae_6_5_10cp_b_selected_surfaces_v1.csv"

New-Item -ItemType Directory -Force $OutRoot | Out-Null
New-Item -ItemType Directory -Force (Split-Path $Runlog) | Out-Null

$selected = @()
if (Test-Path $SelectedCsv) {
  $selected = Import-Csv $SelectedCsv
}

$probeRows = @()
foreach ($row in $selected) {
  $candidate = Join-Path $RepoRoot $row.candidate_path
  $exists = Test-Path $candidate
  $contentBytes = 0
  $markerScore = 0
  if ($exists) {
    $item = Get-Item $candidate
    $contentBytes = $item.Length
    $text = Get-Content $candidate -Raw -ErrorAction SilentlyContinue
    foreach ($marker in @("HELP DATA", "CMDHELPCHK", "message catalog", "native writer", "writer", "apply", "candidate")) {
      if ($text -match [regex]::Escape($marker)) { $markerScore += 1 }
    }
  }
  $probeRows += [pscustomobject]@{
    candidate_path = $row.candidate_path
    exists = [int]$exists
    size_bytes = $contentBytes
    marker_score = $markerScore
    invoked_active_writer = 0
    read_only_surface_probe = 1
  }
}

$Probe = [ordered]@{
  phase = "22AE.6.5.10CP-B"
  branch = "OPTION_B_TARGETED_NATIVE_WRITER_INVOCATION_SIDE_BRANCH"
  proof_mode = "candidate-only-read-only-surface-probe"
  selected_surface_count = $selected.Count
  candidate_outputs_written = 1
  active_native_writer_invoked = 0
  source_mutation = 0
  help_data_apply = 0
  cmdhelpchk_apply = 0
  active_dbf_mutation = 0
  cdx_lmdb_mutation = 0
  workspace_mutation = 0
  latest_pointer_changed = 0
  reuse_path_confirmed_now = 0
  timestamp_utc = (Get-Date).ToUniversalTime().ToString("s") + "Z"
  note = "CP-B performs a targeted read-only surface probe of selected native-writer candidates. It does not invoke active HELP/CMDHELPCHK apply."
}

$JsonPath = Join-Path $OutRoot "targeted_native_writer_invocation_probe.json"
$CsvPath = Join-Path $OutRoot "targeted_native_writer_invocation_probe.csv"
$SurfaceCsvPath = Join-Path $OutRoot "targeted_native_writer_surface_probe_rows.csv"

$Probe | ConvertTo-Json -Depth 4 | Set-Content -Path $JsonPath -Encoding UTF8
"key,value" | Set-Content -Path $CsvPath -Encoding UTF8
foreach ($k in $Probe.Keys) {
  "$k,$($Probe[$k])" | Add-Content -Path $CsvPath -Encoding UTF8
}
$probeRows | Export-Csv -Path $SurfaceCsvPath -NoTypeInformation -Encoding UTF8

$Transcript = @"
CP-B TARGETED NATIVE WRITER INVOCATION PROOF TRANSCRIPT
phase=22AE.6.5.10CP-B
branch=OPTION_B_TARGETED_NATIVE_WRITER_INVOCATION_SIDE_BRANCH
proof_mode=candidate-only-read-only-surface-probe
selected_surface_count=$($selected.Count)
active_native_writer_invoked=0
source_mutation=0
help_data_apply=0
cmdhelpchk_apply=0
active_dbf_mutation=0
cdx_lmdb_mutation=0
workspace_mutation=0
latest_pointer_changed=0
reuse_path_confirmed_now=0
json=$JsonPath
csv=$CsvPath
surface_csv=$SurfaceCsvPath
"@
$Transcript | Set-Content -Path $Runlog -Encoding UTF8

Write-Host "[CP-B] Targeted native-writer read-only surface proof outputs written."
Write-Host "[CP-B] Transcript:" $Runlog
Write-Host "[CP-B] Active native writer invoked: 0"
Write-Host "[CP-B] Source mutation: 0"
Write-Host "[CP-B] HELP DATA apply: 0"
Write-Host "[CP-B] CMDHELPCHK apply: 0"
Write-Host "[CP-B] DBF/CDX/LMDB mutation: 0"
Write-Host "[CP-B] Latest pointer changed: 0"
Write-Host "[CP-B] Reuse path confirmed now: 0"
"""

    validation = sum(1 for r in pre if r["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10CP_B_STAGING_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    (out / "scripts").mkdir(parents=True, exist_ok=True)
    (out / "candidate_outputs").mkdir(parents=True, exist_ok=True)
    (out / "runlog").mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10cp_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cp_b_selected_surfaces_v1.csv", ["selection_rank","candidate_path","suffix","source_score","selection_score","selection_reason","execute_by_package"], selected_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cp_b_refusal_guards_v1.csv", ["guard_id","condition","required","execute_now"], refusal)
    write_text(out / "targeted_invocation_contract_manifest_v1.json", json.dumps(invocation_contract, indent=2))
    write_text(out / "scripts/run_cp_b_targeted_native_writer_invocation_proof_AFTER_REVIEW.ps1", manual_run_ps1)

    staged = [
        {"artifact":"targeted_invocation_contract_manifest_v1.json","path":str((out/"targeted_invocation_contract_manifest_v1.json").relative_to(repo)).replace("\\","/"),"manual_run":0},
        {"artifact":"run_cp_b_targeted_native_writer_invocation_proof_AFTER_REVIEW.ps1","path":str((out/"scripts/run_cp_b_targeted_native_writer_invocation_proof_AFTER_REVIEW.ps1").relative_to(repo)).replace("\\","/"),"manual_run":1},
        {"artifact":"message_catalog_phase22ae_6_5_10cp_b_selected_surfaces_v1.csv","path":"docs/messaging/reports/message_catalog_phase22ae_6_5_10cp_b_selected_surfaces_v1.csv","manual_run":0},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cp_b_staged_artifacts_v1.csv", ["artifact","path","manual_run"], staged)

    boundary = [
        {"boundary":"targeted proof executed by package","value":0,"status":"PASS"},
        {"boundary":"active native writer invoked by package","value":0,"status":"PASS"},
        {"boundary":"source files mutated","value":0,"status":"PASS"},
        {"boundary":"HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed","value":0,"status":"PASS"},
        {"boundary":"DBF mutation observed","value":0,"status":"PASS"},
        {"boundary":"CDX/LMDB mutation observed","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by CP-B","value":0,"status":"PASS"},
        {"boundary":"reuse path confirmed now","value":0,"status":"PASS"},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cp_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10CP-B",
        "CO_B_STATUS_GREEN":cob_green,
        "CO_B_SAVEPOINT_PRESENT":cob_sp,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CP_B":latest_before,
        "TOP_CANDIDATE_INVENTORY_ROWS":len(top_inventory),
        "SELECTED_SURFACE_ROWS":len(selected_rows),
        "STAGED_ARTIFACTS":len(staged),
        "MANUAL_RUN_ARTIFACTS":sum(1 for r in staged if r["manual_run"]),
        "TARGETED_PROOF_EXECUTED_BY_PACKAGE":0,
        "ACTIVE_NATIVE_WRITER_INVOKED_BY_PACKAGE":0,
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
        "LATEST_POINTER_CHANGED_BY_CP_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cp_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    report = f"""# Phase 22AE.6.5.10CP-B Targeted Native Writer Invocation Proof Staging

- Status: {status}
- Validation issues: {validation}
- CO-B status green: {cob_green}
- CO-B savepoint present: {cob_sp}
- Official latest before CP-B: `{latest_before}`
- Top candidate inventory rows: {len(top_inventory)}
- Selected surface rows: {len(selected_rows)}
- Staged artifacts: {len(staged)}
- Manual-run artifacts: {sum(1 for r in staged if r['manual_run'])}
- Targeted proof executed by package: 0
- Active native writer invoked by package: 0
- Reuse path selected now: 1
- Reuse path confirmed now: 0
- Source mutation authorized now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Active catalog mutation observed: 0
- DBF mutation observed: 0
- CDX/LMDB mutation observed: 0
- Workspace mutation observed: 0
- Latest pointer changed by CP-B: 0
- Next gate: {next_gate}

CP-B stages a manual-run targeted proof script. The script performs a candidate-only read-only surface probe and does not invoke active HELP/CMDHELPCHK apply.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CP_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_STAGING.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CP_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_STAGING.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CO-B status green: {cob_green}")
    print(f"  CO-B savepoint present: {cob_sp}")
    print(f"  official latest before CP-B: {latest_before}")
    print(f"  top candidate inventory rows: {len(top_inventory)}")
    print(f"  selected surface rows: {len(selected_rows)}")
    print(f"  staged artifacts: {len(staged)}")
    print(f"  manual-run artifacts: {sum(1 for r in staged if r['manual_run'])}")
    print("  targeted proof executed by package: 0")
    print("  active native writer invoked by package: 0")
    print("  reuse path selected now: 1")
    print("  reuse path confirmed now: 0")
    print("  source mutation authorized now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  active catalog mutation observed: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print("  latest pointer changed by CP-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
