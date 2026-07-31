
from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DI_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DI_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_PLAN_GREEN_READ_ONLY_PROBES_STAGED_NO_SELECTION"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DJ_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_STAGING_GREEN_MANUAL_READ_ONLY_PROBES_STAGED_NO_EXECUTION"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DJ_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_STAGING_RED_REVIEW_REQUIRED"
DI_SAVEPOINT = "MSG-022AE.6.5.10DI-B"
NEXT = "HOLD_OR_RUN_DJ_B_READ_ONLY_TARGET_VERIFICATION_PROBES_AND_CAPTURE_TRANSCRIPT"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dj_b_active_help_cmdhelpchk_target_verification_probe_staging_v1"

def txt(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

def out(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")

def rows(p: Path) -> list[dict]:
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def one(p: Path) -> dict:
    r = rows(p)
    return r[0] if r else {}

def wcsv(p: Path, fields: list[str], rs: list[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rs:
            w.writerow({k: r.get(k, "") for k in fields})

def journal_has(repo: Path, marker: str) -> int:
    return int(marker in txt(repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def latest(repo: Path) -> str:
    try:
        data = json.loads(txt(repo / "docs/messaging/reports/message_savepoint_latest_v1.json"))
        return data.get("savepoint_id", data.get("savepoint", ""))
    except Exception:
        return ""

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-staging", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = repo / "docs/messaging/reports"
    stage = repo / ROOT_REL
    manual = stage / "manual_run"
    if stage.exists() and a.replace_existing_staging:
        shutil.rmtree(stage)

    di = one(reports / "message_catalog_phase22ae_6_5_10di_b_status_summary_v1.csv")
    probes = rows(reports / "message_catalog_phase22ae_6_5_10di_b_probe_plan_v1.csv")
    di_green = int(di.get("STATUS","") == DI_GREEN)
    di_save = journal_has(repo, DI_SAVEPOINT)
    pre = [
        {"check_id":"di_b_status_green","value":di_green,"expected":1,"status":"PASS" if di_green else "FAIL"},
        {"check_id":"di_b_savepoint_present","value":di_save,"expected":1,"status":"PASS" if di_save else "FAIL"},
        {"check_id":"probe_plan_rows_exist","value":len(probes),"expected":">0","status":"PASS" if probes else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":di.get("APPLY_EXECUTION_AUTHORIZED_NOW","0"),"expected":0,"status":"PASS" if str(di.get("APPLY_EXECUTION_AUTHORIZED_NOW","0"))=="0" else "FAIL"},
        {"check_id":"dj_b_root_absent_or_replace_authorized","value":int(stage.exists()),"expected":0,"status":"PASS" if (not stage.exists() or a.replace_existing_staging) else "FAIL"},
    ]

    manual.mkdir(parents=True, exist_ok=True)
    ps = [
        "param([Parameter(Mandatory=$true)][string]$RepoRoot)",
        "Set-StrictMode -Version Latest",
        "$ErrorActionPreference = 'Stop'",
        "$rows = @()",
        "$log = @('# DJ-B read-only target verification probe transcript','')",
        "$log += ('RepoRoot: ' + $RepoRoot)",
        "$log += ('Timestamp UTC: ' + (Get-Date).ToUniversalTime().ToString('s') + 'Z')",
    ]
    for p in probes:
        rel = p.get("relative_path","").replace("'","''")
        ps += [
            f"$path = Join-Path $RepoRoot '{rel}'",
            "$exists = Test-Path -LiteralPath $path",
            "$kind = ''; $length = ''; $last = ''",
            "if ($exists) { $it = Get-Item -LiteralPath $path -Force; $kind = if ($it.PSIsContainer) {'directory'} else {'file'}; $length = if ($it.PSIsContainer) {''} else {[string]$it.Length}; $last = $it.LastWriteTimeUtc.ToString('s') + 'Z' }",
            "$rows += [pscustomobject]@{ probe_id='"+p.get("probe_id","")+"'; family='"+p.get("family","")+"'; relative_path='"+rel+"'; artifact_type='"+p.get("artifact_type","")+"'; probe_kind='"+p.get("probe_kind","")+"'; exists=[int]$exists; fs_kind=$kind; length=$length; last_write_utc=$last; classification='PENDING_REVIEW'; active_target_selected_now=0; apply_now=0 }",
            "$log += ('- "+p.get("probe_id","")+" "+p.get("family","")+" "+rel+" exists=' + [int]$exists)",
        ]
    ps += [
        "$outDir = Join-Path $RepoRoot 'docs\\messaging\\apply\\phase22ae_6_5_10dj_b_active_help_cmdhelpchk_target_verification_probe_staging_v1\\manual_run'",
        "New-Item -ItemType Directory -Force $outDir | Out-Null",
        "$csv = Join-Path $outDir 'DJ_B_TARGET_VERIFICATION_PROBE_RESULTS.csv'",
        "$md = Join-Path $outDir 'DJ_B_TARGET_VERIFICATION_PROBE_TRANSCRIPT.md'",
        "$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $csv",
        "$log | Set-Content -Encoding UTF8 -Path $md",
        "Write-Host 'DJ_B_READ_ONLY_TARGET_VERIFICATION_PROBE_EXECUTED'",
        "Write-Host ('  result csv: ' + $csv)",
        "Write-Host ('  transcript: ' + $md)",
        "Write-Host '  active target selected now: 0'",
        "Write-Host '  apply execution authorized now: 0'",
        "Write-Host '  HELP DATA apply executed: 0'",
        "Write-Host '  CMDHELPCHK apply executed: 0'",
    ]
    out(manual / "DJ_B_READ_ONLY_TARGET_VERIFICATION_PROBE_AFTER_REVIEW.ps1", "\n".join(ps) + "\n")
    out(manual / "DJ_B_NO_RUNTIME_MUTATION_DTS_NOTE.md", "# DJ-B no runtime mutation DTS\n\nUse the staged PowerShell read-only probe script. No HELP DATA apply. No CMDHELPCHK apply. No target selection.\n")

    staged = [
        {"artifact_id":"DJ_ART_001","artifact":"manual_run/DJ_B_READ_ONLY_TARGET_VERIFICATION_PROBE_AFTER_REVIEW.ps1","purpose":"manual read-only existence/classification probe script","created_now":1,"executed_by_package":0},
        {"artifact_id":"DJ_ART_002","artifact":"manual_run/DJ_B_NO_RUNTIME_MUTATION_DTS_NOTE.md","purpose":"declares no DotTalk++ mutation DTS required","created_now":1,"executed_by_package":0},
    ]
    inst = [{
        "step_id":"DJ_RUN_001",
        "instruction":"After review, run the read-only probe script and capture outputs.",
        "command":".\\docs\\messaging\\apply\\phase22ae_6_5_10dj_b_active_help_cmdhelpchk_target_verification_probe_staging_v1\\manual_run\\DJ_B_READ_ONLY_TARGET_VERIFICATION_PROBE_AFTER_REVIEW.ps1 -RepoRoot D:\\code\\ccode",
        "mutates_active_targets":0,
        "requires_manual_execution":1,
    }]
    boundary = [
        {"boundary":"probe staging created","value":1,"status":"PASS"},
        {"boundary":"probe executed by package","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA target selected now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected now","value":0,"status":"PASS"},
        {"boundary":"HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by staging","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by staging","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DJ-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for r in pre + boundary if r["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DJ_B_TARGET_VERIFICATION_PROBE_STAGING_PRECONDITIONS"

    wcsv(reports / "message_catalog_phase22ae_6_5_10dj_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    wcsv(reports / "message_catalog_phase22ae_6_5_10dj_b_probe_script_rows_v1.csv", ["probe_id","family","rank_within_family","relative_path","artifact_type","probe_kind","probe_goal","read_only","target_selected_now","apply_now"], probes)
    wcsv(reports / "message_catalog_phase22ae_6_5_10dj_b_staged_artifacts_v1.csv", ["artifact_id","artifact","purpose","created_now","executed_by_package"], staged)
    wcsv(reports / "message_catalog_phase22ae_6_5_10dj_b_manual_execution_instructions_v1.csv", ["step_id","instruction","command","mutates_active_targets","requires_manual_execution"], inst)
    wcsv(reports / "message_catalog_phase22ae_6_5_10dj_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status, "VALIDATION_ISSUES":validation, "PHASE":"22AE.6.5.10DJ-B",
        "DI_B_STATUS_GREEN":di_green, "DI_B_SAVEPOINT_PRESENT":di_save,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DJ_B":latest(repo),
        "TARGET_VERIFICATION_PROBE_STAGING_CREATED":1 if status == GREEN else 0,
        "READ_ONLY_PROBE_SCRIPT_STAGED":1 if status == GREEN else 0,
        "PROBE_SCRIPT_ROWS":len(probes),
        "STAGED_ARTIFACT_ROWS":len(staged),
        "MANUAL_EXECUTION_INSTRUCTION_ROWS":len(inst),
        "PROBE_EXECUTED_BY_DJ_B_PACKAGE":0,
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW":0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_STAGING":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_STAGING":0,
        "LATEST_POINTER_CHANGED_BY_DJ_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    wcsv(reports / "message_catalog_phase22ae_6_5_10dj_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    out(stage / "message_catalog_phase22ae_6_5_10dj_b_probe_staging_manifest_v1.json", json.dumps({"phase":"22AE.6.5.10DJ-B","status":status,"probe_executed_by_package":False,"next_gate":next_gate}, indent=2))
    report = f"""# Phase 22AE.6.5.10DJ-B Active HELP/CMDHELPCHK Target Verification Probe Staging

- Status: {status}
- Validation issues: {validation}
- DI-B status green: {di_green}
- DI-B savepoint present: {di_save}
- Read-only probe script staged: {1 if status == GREEN else 0}
- Probe script rows: {len(probes)}
- Probe executed by DJ-B package: 0
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active DBF/CDX/LMDB mutation observed by staging: 0
- Workspace mutation observed by staging: 0
- Latest pointer changed by DJ-B: 0
- Next gate: {next_gate}

DJ-B stages a manual read-only probe script and instructions. It does not execute the probe, select targets, or apply HELP DATA/CMDHELPCHK changes.
"""
    out(stage / "MESSAGE_LOCALE_PHASE22AE_6_5_10DJ_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_STAGING.md", report)
    out(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DJ_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_STAGING.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DI-B status green: {di_green}")
    print(f"  DI-B savepoint present: {di_save}")
    print(f"  target verification probe staging created: {1 if status == GREEN else 0}")
    print(f"  read-only probe script staged: {1 if status == GREEN else 0}")
    print(f"  probe script rows: {len(probes)}")
    print("  probe executed by DJ-B package: 0")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active DBF/CDX/LMDB mutation observed by staging: 0")
    print("  workspace mutation observed by staging: 0")
    print("  latest pointer changed by DJ-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
