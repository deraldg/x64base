#!/usr/bin/env python3
"""
PHASE23N - HELP locale active promotion execution staging.

Stages a guarded local apply script to copy the four candidate HELP locale
companion table artifact sets from the PHASE23K candidate root into the active
HELP DBF/CDX/LMDB roots. This staging script does not copy active files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

PHASE = "PHASE23N"
STATUS = "PHASE23N_HELP_LOCALE_ACTIVE_PROMOTION_EXECUTION_STAGING_GREEN_APPLY_SCRIPT_READY"
CANDIDATE_NAME = "PHASE23N-HELP-LOCALE-ACTIVE-PROMOTION-EXECUTION-STAGING"
PHASE23K_NAME = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"
PHASE23M_NAME = "PHASE23M-HELP-LOCALE-ACTIVE-PROMOTION-PLAN"
TABLES = [
    "HELP_TOPIC_LOCALE",
    "HELP_SECTION_LOCALE",
    "HELP_LINE_LOCALE",
    "HELP_ARTIFACT_LOCALE",
]


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def norm(path: str) -> str:
    return path.replace("/", "\\")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_dir(path: Path) -> str:
    h = hashlib.sha256()
    if not path.exists():
        return ""
    for p in sorted([x for x in path.rglob("*") if x.is_file()]):
        rp = str(p.relative_to(path)).replace("\\", "/")
        h.update(rp.encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_file(p).encode("ascii"))
        h.update(b"\0")
    return h.hexdigest()


def artifact_hash(path: Path) -> str:
    if path.is_dir():
        return sha256_dir(path)
    if path.is_file():
        return sha256_file(path)
    return ""


def copy_plan_rows(repo: Path) -> List[Dict[str, Any]]:
    kroot = repo / "docs" / "locale" / "candidates" / PHASE23K_NAME
    rows: List[Dict[str, Any]] = []
    for table in TABLES:
        rows.append({
            "table": table,
            "kind": "DBF",
            "source": kroot / "dbf" / f"{table}.dbf",
            "target": repo / "dottalkpp" / "data" / "HELP" / f"{table}.dbf",
        })
        rows.append({
            "table": table,
            "kind": "CDX",
            "source": kroot / "indexes" / f"{table}.cdx",
            "target": repo / "dottalkpp" / "data" / "INDEXES" / "HELP" / f"{table}.cdx",
        })
        rows.append({
            "table": table,
            "kind": "LMDB",
            "source": kroot / "lmdb" / f"{table}.cdx.d",
            "target": repo / "dottalkpp" / "data" / "LMDB" / "HELP" / f"{table}.cdx.d",
        })
    return rows


def find_phase23m_green(repo: Path) -> int:
    mroot = repo / "docs" / "locale" / "candidates" / PHASE23M_NAME
    if not mroot.exists():
        return 0
    needles = [
        "PHASE23M_HELP_LOCALE_ACTIVE_PROMOTION_PLAN_GREEN_REPORT_ONLY_APPLY_HELD",
        "phase23ls_green: 1",
        '"phase23ls_green"',
    ]
    for p in mroot.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".json", ".md", ".txt", ".csv"}:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if needles[0] in txt or (needles[1] in txt and "candidate_dbf_exists" in txt):
            return 1
        if needles[2] in txt and "PHASE23M" in txt:
            return 1
    return 0


def write_apply_script(path: Path) -> None:
    # Use a single-quoted here-doc style escaped PowerShell string by writing raw text.
    text = r'''param(
  [string]$RepoRoot = ".",
  [switch]$ConfirmPhase23N
)

$ErrorActionPreference = "Stop"

if (-not $ConfirmPhase23N) {
  Write-Host "PHASE23N_APPLY_REFUSED_CONFIRM_FLAG_REQUIRED"
  Write-Host "Rerun with: -ConfirmPhase23N"
  exit 2
}

$root = (Resolve-Path $RepoRoot).Path
$phaseRoot = Join-Path $root "docs\locale\candidates\PHASE23N-HELP-LOCALE-ACTIVE-PROMOTION-EXECUTION-STAGING"
$kroot = Join-Path $root "docs\locale\candidates\PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"
$activeHelp = Join-Path $root "dottalkpp\data\HELP"
$activeIndexes = Join-Path $root "dottalkpp\data\INDEXES\HELP"
$activeLmdb = Join-Path $root "dottalkpp\data\LMDB\HELP"
$rollbackRoot = Join-Path $phaseRoot ("rollback\active_help_locale_pre_phase23n_" + (Get-Date -Format "yyyyMMdd-HHmmss"))
$applyLog = Join-Path $phaseRoot "reports\PHASE23N_APPLY_ACTIVE_PROMOTION_LOG.txt"

New-Item -ItemType Directory -Force -Path $activeHelp,$activeIndexes,$activeLmdb,$rollbackRoot,(Split-Path $applyLog) | Out-Null

$tables = @("HELP_TOPIC_LOCALE", "HELP_SECTION_LOCALE", "HELP_LINE_LOCALE", "HELP_ARTIFACT_LOCALE")
$copied = 0
$backedUp = 0
$missing = 0

function Backup-IfExists($sourcePath, $relativeName) {
  if (Test-Path $sourcePath) {
    $dest = Join-Path $rollbackRoot $relativeName
    New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
    if ((Get-Item $sourcePath).PSIsContainer) {
      Copy-Item -Recurse -Force $sourcePath $dest
    } else {
      Copy-Item -Force $sourcePath $dest
    }
    return 1
  }
  return 0
}

function Copy-Required($src, $dst, $label) {
  if (-not (Test-Path $src)) {
    Add-Content -Path $applyLog -Value "MISSING $label source=$src"
    return 0
  }
  New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
  if ((Get-Item $src).PSIsContainer) {
    if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
    Copy-Item -Recurse -Force $src $dst
  } else {
    Copy-Item -Force $src $dst
  }
  Add-Content -Path $applyLog -Value "COPIED $label source=$src target=$dst"
  return 1
}

"PHASE23N_APPLY_ACTIVE_PROMOTION_START" | Set-Content -Path $applyLog
"repo_root=$root" | Add-Content -Path $applyLog
"rollback_root=$rollbackRoot" | Add-Content -Path $applyLog

foreach ($t in $tables) {
  $srcDbf = Join-Path $kroot "dbf\$t.dbf"
  $srcCdx = Join-Path $kroot "indexes\$t.cdx"
  $srcLmdb = Join-Path $kroot "lmdb\$t.cdx.d"
  $dstDbf = Join-Path $activeHelp "$t.dbf"
  $dstCdx = Join-Path $activeIndexes "$t.cdx"
  $dstLmdb = Join-Path $activeLmdb "$t.cdx.d"

  $backedUp += Backup-IfExists $dstDbf "HELP\$t.dbf"
  $backedUp += Backup-IfExists $dstCdx "INDEXES\HELP\$t.cdx"
  $backedUp += Backup-IfExists $dstLmdb "LMDB\HELP\$t.cdx.d"

  $copied += Copy-Required $srcDbf $dstDbf "$t DBF"
  $copied += Copy-Required $srcCdx $dstCdx "$t CDX"
  $copied += Copy-Required $srcLmdb $dstLmdb "$t LMDB"
}

"copied_artifacts=$copied" | Add-Content -Path $applyLog
"backed_up_artifacts=$backedUp" | Add-Content -Path $applyLog
"PHASE23N_APPLY_ACTIVE_PROMOTION_END" | Add-Content -Path $applyLog

Write-Host "PHASE23N_APPLY_ACTIVE_PROMOTION_COMPLETED"
Write-Host "copied_artifacts: $copied"
Write-Host "backed_up_artifacts: $backedUp"
Write-Host "rollback_root: $rollbackRoot"
Write-Host "apply_log: $applyLog"
'''
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()

    cdir = repo / "docs" / "locale" / "candidates" / CANDIDATE_NAME
    reports = cdir / "reports"
    manifests = cdir / "manifests"
    runtime = cdir / "runtime"
    for d in (reports, manifests, runtime):
        d.mkdir(parents=True, exist_ok=True)

    rows = copy_plan_rows(repo)
    phase23m_green = find_phase23m_green(repo)

    candidate_dbf_exists = sum(1 for r in rows if r["kind"] == "DBF" and r["source"].is_file())
    candidate_cdx_exists = sum(1 for r in rows if r["kind"] == "CDX" and r["source"].is_file())
    candidate_lmdb_exists = sum(1 for r in rows if r["kind"] == "LMDB" and r["source"].is_dir())
    active_existing = sum(1 for r in rows if r["target"].exists())

    for r in rows:
        r["source_exists"] = r["source"].exists()
        r["target_exists_before_apply"] = r["target"].exists()
        r["source_hash"] = artifact_hash(r["source"])
        r["source"] = rel(r["source"], repo)
        r["target"] = rel(r["target"], repo)

    apply_script = runtime / "phase23n_apply_active_help_locale_promotion.ps1"
    write_apply_script(apply_script)

    csv_path = reports / "phase23n_artifact_copy_plan.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["table", "kind", "source", "target", "source_exists", "target_exists_before_apply", "source_hash"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    md_path = reports / "PHASE23N_HELP_LOCALE_ACTIVE_PROMOTION_EXECUTION_STAGING.md"
    md = [
        f"# {PHASE} HELP Locale Active Promotion Execution Staging",
        "",
        f"Status: `{STATUS}`" if phase23m_green and candidate_dbf_exists == 4 and candidate_cdx_exists == 4 and candidate_lmdb_exists == 4 else "Status: `PHASE23N_REVIEW_REQUIRED`",
        "",
        "This package stages a guarded local apply script. The staging script itself does not copy active HELP files.",
        "",
        "## Apply command",
        "",
        "```powershell",
        ".\\docs\\locale\\candidates\\PHASE23N-HELP-LOCALE-ACTIVE-PROMOTION-EXECUTION-STAGING\\runtime\\phase23n_apply_active_help_locale_promotion.ps1 -RepoRoot . -ConfirmPhase23N",
        "```",
        "",
        "## Active targets",
        "",
        "- `dottalkpp\\data\\HELP`",
        "- `dottalkpp\\data\\INDEXES\\HELP`",
        "- `dottalkpp\\data\\LMDB\\HELP`",
        "",
        "## Boundary",
        "",
        "No source, CMDHELP, CMDHELPCHK, MAINT, or BBOX behavior is changed by staging.",
    ]
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    manifest: Dict[str, Any] = {
        "phase": PHASE,
        "status": STATUS if phase23m_green and candidate_dbf_exists == 4 and candidate_cdx_exists == 4 and candidate_lmdb_exists == 4 else "PHASE23N_REVIEW_REQUIRED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo),
        "phase23m_green": phase23m_green,
        "phase23k_candidate_dir": str(repo / "docs" / "locale" / "candidates" / PHASE23K_NAME),
        "candidate_dir": str(cdir),
        "candidate_tables": len(TABLES),
        "candidate_dbf_exists": f"{candidate_dbf_exists}/4",
        "candidate_cdx_exists": f"{candidate_cdx_exists}/4",
        "candidate_lmdb_exists": f"{candidate_lmdb_exists}/4",
        "active_existing_artifact_count": active_existing,
        "artifact_plan_rows": len(rows),
        "apply_script": rel(apply_script, repo),
        "artifact_copy_plan_csv": rel(csv_path, repo),
        "promotion_execution_staging_report": rel(md_path, repo),
        "artifacts": rows,
        "source_files_written": 0,
        "active_help_dbf_written": 0,
        "active_help_cdx_written": 0,
        "active_help_lmdb_written": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "maint_behavior_changed": 0,
        "bbox_behavior_changed": 0,
        "runtime_execution_by_python": 0,
        "active_promotion_executed_by_staging": 0,
        "next_gate": "HOLD_OR_RUN_PHASE23N_APPLY_SCRIPT_THEN_REVIEW_ACTIVE_ARTIFACTS",
    }
    manifest_path = manifests / "phase23n_help_locale_active_promotion_execution_staging_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(manifest["status"])
    print(f"candidate_dir: {norm(rel(cdir, repo))}")
    print(f"phase23m_green: {phase23m_green}")
    print(f"phase23k_candidate_dir: {norm(rel(repo / 'docs' / 'locale' / 'candidates' / PHASE23K_NAME, repo))}")
    print(f"candidate_tables: {len(TABLES)}")
    print(f"candidate_dbf_exists: {candidate_dbf_exists}/4")
    print(f"candidate_cdx_exists: {candidate_cdx_exists}/4")
    print(f"candidate_lmdb_exists: {candidate_lmdb_exists}/4")
    print(f"active_existing_artifact_count: {active_existing}")
    print(f"artifact_plan_rows: {len(rows)}")
    print(f"active_target_roots: dottalkpp\\data\\HELP,dottalkpp\\data\\INDEXES\\HELP,dottalkpp\\data\\LMDB\\HELP")
    print(f"manifest: {norm(rel(manifest_path, repo))}")
    print(f"artifact_copy_plan: {norm(rel(csv_path, repo))}")
    print(f"apply_script: {norm(rel(apply_script, repo))}")
    print(f"apply_command: .\\{norm(rel(apply_script, repo))} -RepoRoot . -ConfirmPhase23N")
    print("source_files_written: 0")
    print("active_help_dbf_written: 0")
    print("active_help_cdx_written: 0")
    print("active_help_lmdb_written: 0")
    print("cmdhelp_behavior_changed: 0")
    print("cmdhelpchk_behavior_changed: 0")
    print("maint_behavior_changed: 0")
    print("bbox_behavior_changed: 0")
    print("runtime_execution_by_python: 0")
    print("active_promotion_executed_by_staging: 0")
    print("next_gate: HOLD_OR_RUN_PHASE23N_APPLY_SCRIPT_THEN_REVIEW_ACTIVE_ARTIFACTS")
    return 0 if manifest["status"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
