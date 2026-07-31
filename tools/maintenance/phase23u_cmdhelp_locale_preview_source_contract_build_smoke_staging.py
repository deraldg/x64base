#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path

PHASE23U_NAME = "PHASE23U-CMDHELP-LOCALE-PREVIEW-SOURCE-CONTRACT-BUILD-SMOKE"
PHASE23T_NAME = "PHASE23T-CMDHELP-LOCALE-PREVIEW-SOURCE-PATCH-APPLY-STAGING"
SOURCE_TARGET = Path("src/cli/cmdhelp.cpp")

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()

    cand = repo / "docs/locale/candidates" / PHASE23U_NAME
    reports = cand / "reports"
    runtime = cand / "runtime"
    manifests = cand / "manifests"
    transcripts = cand / "transcripts"
    for d in (reports, runtime, manifests, transcripts):
        d.mkdir(parents=True, exist_ok=True)

    t_dir = repo / "docs/locale/candidates" / PHASE23T_NAME
    t_apply_manifest = t_dir / "manifests/phase23t_source_contract_patch_apply_manifest.json"
    t_apply_log = t_dir / "reports/PHASE23T_SOURCE_CONTRACT_PATCH_APPLY_LOG.txt"
    t_review_report = t_dir / "reports/PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_REVIEW.md"

    source_path = repo / SOURCE_TARGET
    source_text = read_text(source_path)
    marker_present = ("CMDHELP locale preview" in source_text and "PREVIEW LOCALE" in source_text) or ("PHASE23T" in source_text and "CMDHELP" in source_text and "locale" in source_text)
    source_exists = source_path.exists()
    source_hash = sha256_file(source_path) if source_exists else ""

    phase23t_apply_evidence = t_apply_manifest.exists() or ("PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_PATCH_APPLIED_GREEN" in read_text(t_apply_log))
    phase23t_review_evidence = "PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_PATCH_REVIEW_GREEN" in (read_text(t_review_report) + read_text(t_apply_log))
    build_dir_exists = (repo / "build").exists()

    dts = runtime / "phase23u_cmdhelp_default_behavior_smoke_probe.dts"
    transcript = transcripts / "phase23u_cmdhelp_default_behavior_smoke_probe_transcript.txt"
    dts.write_text("""ECHO ON
SET PAGING OFF
ECHO PHASE23U_DOTSCRIPT_START
ECHO PHASE23U_SCOPE_DEFAULT_CMDHELP_BEHAVIOR_UNCHANGED_SMOKE
CMDHELP AREA
CMDHELP USAGE AREA
ECHO PHASE23U_DOTSCRIPT_END
""", encoding="utf-8")

    build_script = runtime / "phase23u_build_cmdhelp_source_contract_smoke.ps1"
    build_script.write_text(r'''param(
  [string]$RepoRoot = ".",
  [switch]$ConfirmPhase23U
)
$ErrorActionPreference = "Stop"
if (-not $ConfirmPhase23U) { throw "Refusing PHASE23U build smoke without -ConfirmPhase23U" }
$Repo = (Resolve-Path $RepoRoot).Path
$CandidateDir = Join-Path $Repo "docs\locale\candidates\PHASE23U-CMDHELP-LOCALE-PREVIEW-SOURCE-CONTRACT-BUILD-SMOKE"
$ReportDir = Join-Path $CandidateDir "reports"
$Log = Join-Path $ReportDir "PHASE23U_BUILD_SMOKE_LOG.txt"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
"PHASE23U_BUILD_SMOKE_START" | Set-Content -Encoding UTF8 $Log
"repo_root: $Repo" | Add-Content -Encoding UTF8 $Log
Push-Location $Repo
try {
  if (-not (Test-Path ".\build")) { throw "build directory not found: .\build" }
  "build_command: cmake --build .\build --config Release --target dottalkpp" | Add-Content -Encoding UTF8 $Log
  & cmake --build .\build --config Release --target dottalkpp 2>&1 | Tee-Object -FilePath $Log -Append
  if ($LASTEXITCODE -ne 0) { throw "cmake build failed with exit code $LASTEXITCODE" }
  $exeCandidates = @(".\build\Release\dottalkpp.exe", ".\build\dottalkpp.exe", ".\build\src\cli\Release\dottalkpp.exe")
  $found = @($exeCandidates | Where-Object { Test-Path $_ })
  "exe_candidates_found: $($found.Count)" | Add-Content -Encoding UTF8 $Log
  foreach ($f in $found) { "exe: $f" | Add-Content -Encoding UTF8 $Log }
  "PHASE23U_BUILD_SMOKE_END" | Add-Content -Encoding UTF8 $Log
  Write-Host "PHASE23U_BUILD_SMOKE_COMPLETED"
  Write-Host "build_log: docs\locale\candidates\PHASE23U-CMDHELP-LOCALE-PREVIEW-SOURCE-CONTRACT-BUILD-SMOKE\reports\PHASE23U_BUILD_SMOKE_LOG.txt"
  Write-Host "next_manual_dotscript: DOTSCRIPT TRACE D:\code\ccode\docs\locale\candidates\PHASE23U-CMDHELP-LOCALE-PREVIEW-SOURCE-CONTRACT-BUILD-SMOKE\runtime\phase23u_cmdhelp_default_behavior_smoke_probe.dts OUT D:\code\ccode\docs\locale\candidates\PHASE23U-CMDHELP-LOCALE-PREVIEW-SOURCE-CONTRACT-BUILD-SMOKE\transcripts\phase23u_cmdhelp_default_behavior_smoke_probe_transcript.txt"
} finally {
  Pop-Location
}
''', encoding="utf-8")

    reviewer = repo / "tools/maintenance/phase23u_review_cmdhelp_locale_preview_build_smoke.py"
    reviewer.write_text(r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
PHASE23U_NAME = "PHASE23U-CMDHELP-LOCALE-PREVIEW-SOURCE-CONTRACT-BUILD-SMOKE"

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    cand = repo / "docs/locale/candidates" / PHASE23U_NAME
    log = cand / "reports/PHASE23U_BUILD_SMOKE_LOG.txt"
    transcript = cand / "transcripts/phase23u_cmdhelp_default_behavior_smoke_probe_transcript.txt"
    src = repo / "src/cli/cmdhelp.cpp"
    log_text = read(log)
    tr = read(transcript)
    src_text = read(src)
    build_started = "PHASE23U_BUILD_SMOKE_START" in log_text
    build_ended = "PHASE23U_BUILD_SMOKE_END" in log_text
    source_contract_marker_present = (("CMDHELP locale preview" in src_text and "PREVIEW LOCALE" in src_text) or ("PHASE23T" in src_text and "CMDHELP" in src_text and "locale" in src_text))
    transcript_exists = transcript.exists()
    transcript_markers_ok = all(x in tr for x in ["PHASE23U_DOTSCRIPT_START", "PHASE23U_SCOPE_DEFAULT_CMDHELP_BEHAVIOR_UNCHANGED_SMOKE", "PHASE23U_DOTSCRIPT_END"])
    cmdhelp_area_seen = "CMDHELP AREA" in tr and ("AREA" in tr or "DOT|AREA" in tr)
    usage_area_seen = "CMDHELP USAGE AREA" in tr or "USAGE AREA" in tr
    bad_patterns = ["not recognized", "fatal error", "error C", "cmake build failed"]
    bad_hits = [p for p in bad_patterns if p.lower() in (log_text + tr).lower()]
    green = build_started and build_ended and source_contract_marker_present and transcript_markers_ok and cmdhelp_area_seen and usage_area_seen and not bad_hits
    print("PHASE23U_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_BUILD_SMOKE_GREEN" if green else "PHASE23U_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_BUILD_SMOKE_REVIEW_REQUIRED")
    print(f"candidate_dir: docs\\locale\\candidates\\{PHASE23U_NAME}")
    print(f"build_log_exists: {1 if log.exists() else 0}")
    print(f"build_started: {1 if build_started else 0}")
    print(f"build_ended: {1 if build_ended else 0}")
    print(f"source_contract_marker_present: {1 if source_contract_marker_present else 0}")
    print(f"transcript_exists: {1 if transcript_exists else 0}")
    print(f"transcript_markers_ok: {1 if transcript_markers_ok else 0}")
    print(f"cmdhelp_area_seen: {1 if cmdhelp_area_seen else 0}")
    print(f"usage_area_seen: {1 if usage_area_seen else 0}")
    print(f"bad_hits_count: {len(bad_hits)}")
    print("source_files_written_by_review: 0")
    print("cmdhelp_behavior_changed_by_review: 0")
    print("active_help_dbf_written_by_review: 0")
    print("active_help_cdx_written_by_review: 0")
    print("active_help_lmdb_written_by_review: 0")
    print("next_gate: HOLD_OR_AUTHORIZE_PHASE23V_CMDHELP_LOCALE_PREVIEW_BEHAVIOR_PATCH_PLAN" if green else "FIX_OR_RERUN_PHASE23U_BUILD_OR_DOTSCRIPT_SMOKE")
    return 0 if green else 1
if __name__ == "__main__":
    raise SystemExit(main())
''', encoding="utf-8")

    write_csv(reports / "phase23u_build_smoke_plan.csv", [
        {"step": 1, "action": "verify PHASE23T source contract marker", "mutation": "none"},
        {"step": 2, "action": "cmake --build .\\build --config Release --target dottalkpp", "mutation": "build artifacts only"},
        {"step": 3, "action": "run retained DotScript smoke for default CMDHELP AREA and CMDHELP USAGE AREA", "mutation": "none"},
        {"step": 4, "action": "review build log and transcript", "mutation": "none"},
    ])

    status_green = source_exists and marker_present
    status = "PHASE23U_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_BUILD_SMOKE_STAGING_GREEN_MANUAL_BUILD_AND_DOTSCRIPT_REQUIRED" if status_green else "PHASE23U_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_BUILD_SMOKE_STAGING_REVIEW_REQUIRED"
    manifest = {
        "status": status,
        "candidate_dir": str(cand.relative_to(repo)),
        "phase23t_candidate_dir": str(t_dir.relative_to(repo)),
        "phase23t_apply_evidence": phase23t_apply_evidence,
        "phase23t_review_evidence": phase23t_review_evidence,
        "selected_source_target": str(SOURCE_TARGET).replace("\\", "/"),
        "source_target_exists": source_exists,
        "source_contract_marker_present": marker_present,
        "source_hash": source_hash,
        "build_dir_exists": build_dir_exists,
        "build_script": str(build_script.relative_to(repo)),
        "retained_dotscript": str(dts.relative_to(repo)),
        "expected_transcript": str(transcript.relative_to(repo)),
        "source_files_written": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "active_help_dbf_written": 0,
        "active_help_cdx_written": 0,
        "active_help_lmdb_written": 0,
        "next_gate": "HOLD_OR_RUN_PHASE23U_BUILD_SCRIPT_AND_DOTSCRIPT_THEN_REVIEW" if status_green else "FIX_PHASE23T_SOURCE_CONTRACT_MARKER_OR_SOURCE_TARGET",
    }
    (manifests / "phase23u_cmdhelp_locale_preview_source_contract_build_smoke_staging_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (reports / "PHASE23U_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_BUILD_SMOKE_STAGING.md").write_text(f"""# PHASE23U CMDHELP Locale Preview Source Contract Build Smoke Staging

Status: `{status}`

Selected source target: `{manifest['selected_source_target']}`

Build apply command:

```powershell
.\\docs\\locale\\candidates\\{PHASE23U_NAME}\\runtime\\phase23u_build_cmdhelp_source_contract_smoke.ps1 -RepoRoot . -ConfirmPhase23U
```

DotTalk++ smoke command after build:

```text
DOTSCRIPT TRACE D:\\code\\ccode\\docs\\locale\\candidates\\{PHASE23U_NAME}\\runtime\\phase23u_cmdhelp_default_behavior_smoke_probe.dts OUT D:\\code\\ccode\\docs\\locale\\candidates\\{PHASE23U_NAME}\\transcripts\\phase23u_cmdhelp_default_behavior_smoke_probe_transcript.txt
```

Review command:

```powershell
& $py12 .\\tools\\maintenance\\phase23u_review_cmdhelp_locale_preview_build_smoke.py --repo-root .
```
""", encoding="utf-8")

    print(status)
    print(f"candidate_dir: docs\\locale\\candidates\\{PHASE23U_NAME}")
    print(f"phase23t_apply_evidence: {1 if phase23t_apply_evidence else 0}")
    print(f"source_target_exists: {1 if source_exists else 0}")
    print(f"source_contract_marker_present: {1 if marker_present else 0}")
    print(f"build_dir_exists: {1 if build_dir_exists else 0}")
    print(f"selected_source_target: {manifest['selected_source_target']}")
    print(f"manifest: docs\\locale\\candidates\\{PHASE23U_NAME}\\manifests\\phase23u_cmdhelp_locale_preview_source_contract_build_smoke_staging_manifest.json")
    print(f"build_smoke_staging_report: docs\\locale\\candidates\\{PHASE23U_NAME}\\reports\\PHASE23U_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_BUILD_SMOKE_STAGING.md")
    print(f"build_script: docs\\locale\\candidates\\{PHASE23U_NAME}\\runtime\\phase23u_build_cmdhelp_source_contract_smoke.ps1")
    print(f"retained_dotscript: docs\\locale\\candidates\\{PHASE23U_NAME}\\runtime\\phase23u_cmdhelp_default_behavior_smoke_probe.dts")
    print(f"manual_build_command: .\\docs\\locale\\candidates\\{PHASE23U_NAME}\\runtime\\phase23u_build_cmdhelp_source_contract_smoke.ps1 -RepoRoot . -ConfirmPhase23U")
    print(f"manual_dotscript_command: DOTSCRIPT TRACE D:\\code\\ccode\\docs\\locale\\candidates\\{PHASE23U_NAME}\\runtime\\phase23u_cmdhelp_default_behavior_smoke_probe.dts OUT D:\\code\\ccode\\docs\\locale\\candidates\\{PHASE23U_NAME}\\transcripts\\phase23u_cmdhelp_default_behavior_smoke_probe_transcript.txt")
    print("source_files_written: 0")
    print("cmdhelp_behavior_changed: 0")
    print("cmdhelpchk_behavior_changed: 0")
    print("maint_behavior_changed: 0")
    print("bbox_behavior_changed: 0")
    print("active_help_dbf_written: 0")
    print("active_help_cdx_written: 0")
    print("active_help_lmdb_written: 0")
    print(f"next_gate: {manifest['next_gate']}")
    return 0 if status_green else 1

if __name__ == "__main__":
    raise SystemExit(main())
