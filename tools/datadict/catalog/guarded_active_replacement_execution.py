#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, os, hashlib
from pathlib import Path

TABLES = [
    ("DATA_DICTIONARY_OBJECTS", "DDOBJECT", 10, ["CATALOG_OBJECT_ID", "CATALOG_OBJECT_NAME"]),
    ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", "DDATTR", 127, ["CATALOG_OBJECT_ID", "CATALOG_ATTRIBUTE_NAME"]),
    ("DATA_DICTIONARY_RELATION_EDGES", "DDEDGE", 16, ["RELATION_FROM_OBJECT_ID", "RELATION_TO_OBJECT_ID"]),
    ("DATA_DICTIONARY_EVIDENCE_RECORDS", "DDEVID", 7, ["CATALOG_OBJECT_ID"]),
    ("DATA_DICTIONARY_GATE_RECORDS", "DDGATE", 3, ["GATE_RECORD_ID"]),
    ("DATA_DICTIONARY_RUNS", "DDRUN", 2, ["RUN_RECORD_ID"]),
]

REQUIRED = [
    ("DD096ZD2ZC", "docs/datadict/reports/DD096ZD2ZC-current-session-select-clean-tiny-rebuild-v0/dd096zd2zc_current_session_select_clean_tiny_rebuild_manifest.json", ["DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_REBUILD_GREEN"]),
    ("DD096ZD2ZD", "docs/datadict/reports/DD096ZD2ZD-candidate-promotion-readiness-gate-v0/dd096zd2zd_candidate_promotion_readiness_gate_manifest.json", ["DD096ZD2ZD_CANDIDATE_PROMOTION_READINESS_READY"]),
    ("DD096ZD2ZE", "docs/datadict/reports/DD096ZD2ZE-guarded-active-replacement-apply-plan-v0/dd096zd2ze_guarded_active_replacement_apply_plan_manifest.json", ["DD096ZD2ZE_GUARDED_ACTIVE_REPLACEMENT_APPLY_PLAN_READY"]),
]

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

def wt(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def wj(path: Path, obj):
    wt(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def wc(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def file_sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total

def ps_path(path: Path) -> str:
    return str(path).replace("'", "''")

def make_execute_ps1(candidate_dbf: Path, candidate_indexes: Path, candidate_lmdb: Path, active_dbf: Path, active_indexes: Path, active_lmdb: Path, backup_root: Path, report_root: Path) -> str:
    lines = []
    lines.append("# DD096Z-D2ZF guarded active Data Dictionary replacement execution")
    lines.append("param(")
    lines.append("  [switch]$ExecuteActiveReplacement")
    lines.append(")")
    lines.append('$ErrorActionPreference = "Stop"')
    lines.append(f"$CandidateDbf = '{ps_path(candidate_dbf)}'")
    lines.append(f"$CandidateIndexes = '{ps_path(candidate_indexes)}'")
    lines.append(f"$CandidateLmdb = '{ps_path(candidate_lmdb)}'")
    lines.append(f"$ActiveDbf = '{ps_path(active_dbf)}'")
    lines.append(f"$ActiveIndexes = '{ps_path(active_indexes)}'")
    lines.append(f"$ActiveLmdb = '{ps_path(active_lmdb)}'")
    lines.append(f"$BackupRoot = '{ps_path(backup_root)}'")
    lines.append(f"$ReportRoot = '{ps_path(report_root)}'")
    lines.append("")
    lines.append("function Assert-Contains($PathValue, $Needle, $Label) {")
    lines.append("  if (-not $PathValue.ToLowerInvariant().Contains($Needle.ToLowerInvariant())) {")
    lines.append('    throw "$Label failed safety check: $PathValue"')
    lines.append("  }")
    lines.append("}")
    lines.append("function Get-Status($PathValue) {")
    lines.append("  if (-not (Test-Path $PathValue)) { return 'MISSING' }")
    lines.append("  try { return [string]((Get-Content $PathValue -Raw | ConvertFrom-Json).status) } catch { return 'UNREADABLE' }")
    lines.append("}")
    lines.append("function Get-Bytes($PathValue) {")
    lines.append("  if (-not (Test-Path $PathValue)) { return 0 }")
    lines.append("  $item = Get-Item $PathValue -Force")
    lines.append("  if (-not $item.PSIsContainer) { return [int64]$item.Length }")
    lines.append("  return [int64]((Get-ChildItem $PathValue -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum)")
    lines.append("}")
    lines.append("function Get-HashOrBlank($PathValue) {")
    lines.append("  if (Test-Path $PathValue -PathType Leaf) { return (Get-FileHash -Algorithm SHA256 $PathValue).Hash }")
    lines.append("  return ''")
    lines.append("}")
    lines.append("")
    lines.append("Assert-Contains $CandidateDbf 'docs\\datadict\\candidates' 'candidate dbf'")
    lines.append("Assert-Contains $CandidateIndexes 'docs\\datadict\\candidates' 'candidate indexes'")
    lines.append("Assert-Contains $CandidateLmdb 'docs\\datadict\\candidates' 'candidate lmdb'")
    lines.append("Assert-Contains $ActiveDbf 'dottalkpp\\data\\datadict' 'active dbf'")
    lines.append("Assert-Contains $ActiveIndexes 'dottalkpp\\data\\indexes\\datadict' 'active indexes'")
    lines.append("Assert-Contains $ActiveLmdb 'dottalkpp\\data\\lmdb\\datadict' 'active lmdb'")
    lines.append("New-Item -ItemType Directory -Force -Path $ReportRoot | Out-Null")
    lines.append("")
    lines.append("$Preconditions = @(")
    lines.append("  [pscustomobject]@{ Lane='DD096ZD2ZC'; Path='docs\\datadict\\reports\\DD096ZD2ZC-current-session-select-clean-tiny-rebuild-v0\\dd096zd2zc_current_session_select_clean_tiny_rebuild_manifest.json'; Expected='DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_REBUILD_GREEN' },")
    lines.append("  [pscustomobject]@{ Lane='DD096ZD2ZD'; Path='docs\\datadict\\reports\\DD096ZD2ZD-candidate-promotion-readiness-gate-v0\\dd096zd2zd_candidate_promotion_readiness_gate_manifest.json'; Expected='DD096ZD2ZD_CANDIDATE_PROMOTION_READINESS_READY' },")
    lines.append("  [pscustomobject]@{ Lane='DD096ZD2ZE'; Path='docs\\datadict\\reports\\DD096ZD2ZE-guarded-active-replacement-apply-plan-v0\\dd096zd2ze_guarded_active_replacement_apply_plan_manifest.json'; Expected='DD096ZD2ZE_GUARDED_ACTIVE_REPLACEMENT_APPLY_PLAN_READY' }")
    lines.append(")")
    lines.append("$PreRows = @()")
    lines.append("foreach ($p in $Preconditions) {")
    lines.append("  $observed = Get-Status $p.Path")
    lines.append("  $PreRows += [pscustomobject]@{ Lane=$p.Lane; Path=$p.Path; Expected=$p.Expected; Observed=$observed; Pass=[int]($observed -eq $p.Expected) }")
    lines.append("}")
    lines.append("$PreRows | Export-Csv (Join-Path $ReportRoot 'dd096zd2zf_precondition_ledger.csv') -NoTypeInformation")
    lines.append("if (($PreRows | Where-Object { $_.Pass -ne 1 }).Count -gt 0) { throw 'Precondition failure. Refusing active replacement.' }")
    lines.append("")
    lines.append("$CopyPlan = @(")
    entry_lines = []
    for table, legacy, expected, tags in TABLES:
        entry_lines.append(f"  [pscustomobject]@{{ Table='{table}'; Kind='file'; Source=(Join-Path $CandidateDbf '{table}.dbf'); Target=(Join-Path $ActiveDbf '{table}.dbf'); Backup=(Join-Path $BackupRoot 'dbf\\{table}.dbf') }}")
        entry_lines.append(f"  [pscustomobject]@{{ Table='{table}'; Kind='file'; Source=(Join-Path $CandidateIndexes '{table}.cdx'); Target=(Join-Path $ActiveIndexes '{table}.cdx'); Backup=(Join-Path $BackupRoot 'indexes\\{table}.cdx') }}")
        entry_lines.append(f"  [pscustomobject]@{{ Table='{table}'; Kind='directory'; Source=(Join-Path $CandidateLmdb '{table}.cdx.d'); Target=(Join-Path $ActiveLmdb '{table}.cdx.d'); Backup=(Join-Path $BackupRoot 'lmdb\\{table}.cdx.d') }}")
    lines.append(",\n".join(entry_lines))
    lines.append(")")
    lines.append("$PlanRows = @()")
    lines.append("foreach ($e in $CopyPlan) {")
    lines.append("  $PlanRows += [pscustomobject]@{ Table=$e.Table; Kind=$e.Kind; Source=$e.Source; SourceExists=[int](Test-Path $e.Source); SourceBytes=Get-Bytes $e.Source; SourceSha256=Get-HashOrBlank $e.Source; Target=$e.Target; TargetExistsBefore=[int](Test-Path $e.Target); TargetBytesBefore=Get-Bytes $e.Target; TargetSha256Before=Get-HashOrBlank $e.Target; Backup=$e.Backup }")
    lines.append("}")
    lines.append("$PlanRows | Export-Csv (Join-Path $ReportRoot 'dd096zd2zf_execution_copy_plan.csv') -NoTypeInformation")
    lines.append("if (($PlanRows | Where-Object { $_.SourceExists -ne 1 }).Count -gt 0) { throw 'Candidate source artifacts missing. Refusing active replacement.' }")
    lines.append("if (-not $ExecuteActiveReplacement) {")
    lines.append("  $manifest = [ordered]@{ contract='dd096zd2zf_guarded_active_replacement_execution_v0'; status='DD096ZD2ZF_ACTIVE_REPLACEMENT_PREVIEW_READY'; active_replacement_executed=0; backup_root=$BackupRoot; report_root=$ReportRoot; created_utc=(Get-Date).ToUniversalTime().ToString('s') + 'Z' }")
    lines.append("  $manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $ReportRoot 'dd096zd2zf_active_replacement_execution_manifest.json')")
    lines.append("  Write-Host 'Preview only. Rerun with -ExecuteActiveReplacement to perform backup and copy.'")
    lines.append("  return")
    lines.append("}")
    lines.append("")
    lines.append("New-Item -ItemType Directory -Force -Path (Join-Path $BackupRoot 'dbf') | Out-Null")
    lines.append("New-Item -ItemType Directory -Force -Path (Join-Path $BackupRoot 'indexes') | Out-Null")
    lines.append("New-Item -ItemType Directory -Force -Path (Join-Path $BackupRoot 'lmdb') | Out-Null")
    lines.append("$ActionRows = @()")
    lines.append("foreach ($e in $CopyPlan) {")
    lines.append("  New-Item -ItemType Directory -Force -Path (Split-Path $e.Backup -Parent) | Out-Null")
    lines.append("  New-Item -ItemType Directory -Force -Path (Split-Path $e.Target -Parent) | Out-Null")
    lines.append("  $backupPerformed = 0")
    lines.append("  if (Test-Path $e.Target) { Copy-Item $e.Target $e.Backup -Recurse -Force; $backupPerformed = 1; Remove-Item $e.Target -Recurse -Force }")
    lines.append("  Copy-Item $e.Source $e.Target -Recurse -Force")
    lines.append("  $ActionRows += [pscustomobject]@{ Table=$e.Table; Kind=$e.Kind; Source=$e.Source; Target=$e.Target; Backup=$e.Backup; BackupPerformed=$backupPerformed; TargetExistsAfter=[int](Test-Path $e.Target); TargetBytesAfter=Get-Bytes $e.Target; TargetSha256After=Get-HashOrBlank $e.Target }")
    lines.append("}")
    lines.append("$ActionRows | Export-Csv (Join-Path $ReportRoot 'dd096zd2zf_execution_action_ledger.csv') -NoTypeInformation")
    lines.append("$missingAfter = ($ActionRows | Where-Object { $_.TargetExistsAfter -ne 1 }).Count")
    lines.append("$status = if ($missingAfter -eq 0) { 'DD096ZD2ZF_ACTIVE_REPLACEMENT_EXECUTED_PENDING_SMOKE' } else { 'DD096ZD2ZF_ACTIVE_REPLACEMENT_EXECUTION_REVIEW' }")
    lines.append("$manifest = [ordered]@{ contract='dd096zd2zf_guarded_active_replacement_execution_v0'; status=$status; active_replacement_executed=1; missing_after_copy=$missingAfter; backup_root=$BackupRoot; report_root=$ReportRoot; created_utc=(Get-Date).ToUniversalTime().ToString('s') + 'Z' }")
    lines.append("$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $ReportRoot 'dd096zd2zf_active_replacement_execution_manifest.json')")
    lines.append("Write-Host \"DD096Z-D2ZF status: $status\"")
    return "\n".join(lines) + "\n"

def make_rollback_ps1(active_dbf: Path, active_indexes: Path, active_lmdb: Path) -> str:
    return f"""# DD096Z-D2ZF rollback helper
param(
  [Parameter(Mandatory=$true)][string]$BackupRoot,
  [switch]$ExecuteRollback
)
$ActiveDbf = '{ps_path(active_dbf)}'
$ActiveIndexes = '{ps_path(active_indexes)}'
$ActiveLmdb = '{ps_path(active_lmdb)}'
if (-not $ExecuteRollback) {{
  Write-Host 'Preview only. Rerun with -ExecuteRollback to restore backup artifacts.'
  return
}}
if (-not (Test-Path $BackupRoot)) {{ throw "BackupRoot not found: $BackupRoot" }}
Copy-Item (Join-Path $BackupRoot 'dbf\\*') $ActiveDbf -Recurse -Force
Copy-Item (Join-Path $BackupRoot 'indexes\\*') $ActiveIndexes -Recurse -Force
Copy-Item (Join-Path $BackupRoot 'lmdb\\*') $ActiveLmdb -Recurse -Force
Write-Host 'Rollback copy complete. Run DDICT/workspace smoke.'
"""

def make_post_apply_dts() -> str:
    return """* DD096Z-D2ZF post-apply smoke draft
* Read-only smoke after active replacement.
DDICT STATUS
DDICT TABLES
DDICT FIELDS DATA_DICTIONARY_OBJECTS
DDICT FIELDS DDOBJECT
DDICT TAGS DATA_DICTIONARY_OBJECTS
DDICT REL DDICT BOTH
DDICT EVIDENCE DDICT

"""

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZF guarded active replacement execution package generator")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZF-guarded-active-replacement-execution-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--write-execution-scripts", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_guarded_active_replacement_execution"
    gen.mkdir(parents=True, exist_ok=True)

    pre_rows = []
    blockers = 0
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        data = read_json(p)
        observed = data.get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zf_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    ze = read_json(repo / "docs/datadict/reports/DD096ZD2ZE-guarded-active-replacement-apply-plan-v0/dd096zd2ze_guarded_active_replacement_apply_plan_manifest.json")
    candidate_dbf = Path(ze.get("candidate_dbf_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/dbf"))
    candidate_indexes = Path(ze.get("candidate_indexes_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/indexes"))
    candidate_lmdb = Path(ze.get("candidate_lmdb_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/lmdb"))
    active_dbf = Path(ze.get("active_dbf_root", repo / "dottalkpp/data/datadict"))
    active_indexes = Path(ze.get("active_indexes_root", repo / "dottalkpp/data/indexes/datadict"))
    active_lmdb = Path(ze.get("active_lmdb_root", repo / "dottalkpp/data/lmdb/datadict"))

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = repo / f"docs/datadict/backups/DD096ZD2ZF-active-datadict-backup-{stamp}"

    artifact_rows = []
    missing = 0
    for table, legacy, expected, tags in TABLES:
        for kind, src, target in [
            ("dbf", candidate_dbf / f"{table}.dbf", active_dbf / f"{table}.dbf"),
            ("cdx", candidate_indexes / f"{table}.cdx", active_indexes / f"{table}.cdx"),
            ("lmdb_envdir", candidate_lmdb / f"{table}.cdx.d", active_lmdb / f"{table}.cdx.d"),
        ]:
            exists = int(src.exists())
            missing += 0 if exists else 1
            artifact_rows.append({
                "table": table,
                "legacy_bridge_name": legacy,
                "kind": kind,
                "candidate_source": str(src),
                "candidate_exists": exists,
                "candidate_bytes": size_bytes(src),
                "candidate_sha256": file_sha256(src) if kind != "lmdb_envdir" else "",
                "active_target": str(target),
                "active_exists": int(target.exists()),
                "active_bytes": size_bytes(target),
                "future_backup_root": str(backup_root),
            })
    wc(gen / "dd096zd2zf_execution_artifact_matrix.csv", artifact_rows, ["table","legacy_bridge_name","kind","candidate_source","candidate_exists","candidate_bytes","candidate_sha256","active_target","active_exists","active_bytes","future_backup_root"])

    execute_ps1 = make_execute_ps1(candidate_dbf, candidate_indexes, candidate_lmdb, active_dbf, active_indexes, active_lmdb, backup_root, out)
    rollback_ps1 = make_rollback_ps1(active_dbf, active_indexes, active_lmdb)
    smoke_dts = make_post_apply_dts()
    wt(gen / "DD096ZD2ZF_GUARDED_ACTIVE_REPLACEMENT_EXECUTE.ps1", execute_ps1)
    wt(gen / "DD096ZD2ZF_ROLLBACK_HELPER.ps1", rollback_ps1)
    wt(gen / "DD096ZD2ZF_POST_APPLY_SMOKE.dts", smoke_dts)

    scripts_written = 0
    if args.write_execution_scripts:
        wt(repo / "tools/datadict/catalog/DD096ZD2ZF_GUARDED_ACTIVE_REPLACEMENT_EXECUTE.ps1", execute_ps1)
        wt(repo / "tools/datadict/catalog/DD096ZD2ZF_ROLLBACK_HELPER.ps1", rollback_ps1)
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZF_POST_APPLY_SMOKE.dts", smoke_dts)
        scripts_written = 1

    gate_rows = [
        {"gate": "preconditions_green", "observed": blockers, "required": 0, "pass": int(blockers == 0)},
        {"gate": "candidate_artifacts_present", "observed": missing, "required": 0, "pass": int(missing == 0)},
        {"gate": "execution_scripts_written_if_requested", "observed": scripts_written, "required": int(args.write_execution_scripts), "pass": int(scripts_written == int(args.write_execution_scripts))},
        {"gate": "active_replacement_executed_by_generator", "observed": 0, "required": 0, "pass": 1},
    ]
    failures = sum(1 for g in gate_rows if int(g["pass"]) != 1)
    wc(out / "dd096zd2zf_gate_ledger.csv", gate_rows, ["gate","observed","required","pass"])

    boundary_rows = [
        {"boundary": "guarded_active_replacement_execution_package_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_replacement_executed_by_generator", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_dbf_copy_or_write_by_generator", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_cdx_lmdb_rebuild_by_generator", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zf_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary","observed","required","pass"])

    status = "DD096ZD2ZF_GUARDED_ACTIVE_REPLACEMENT_EXECUTION_READY" if failures == 0 else "DD096ZD2ZF_GUARDED_ACTIVE_REPLACEMENT_EXECUTION_REVIEW"

    report = f"""# DD096Z-D2ZF Guarded Active Replacement Execution

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2ZF is the authorized implementation package after D2ZE green.

The generator writes guarded execution scripts but does not itself mutate active catalogs. The PowerShell execution script requires `-ExecuteActiveReplacement`.

## Summary

- Precondition blockers: **{blockers}**
- Missing candidate artifacts: **{missing}**
- Execution scripts written: **{scripts_written}**
- Active replacement executed by generator: **0**
- Active DBF copy/write by generator: **0**
- Active CDX/LMDB rebuild by generator: **0**

## Generated scripts

- `DD096ZD2ZF_GUARDED_ACTIVE_REPLACEMENT_EXECUTE.ps1`
- `DD096ZD2ZF_ROLLBACK_HELPER.ps1`
- `DD096ZD2ZF_POST_APPLY_SMOKE.dts`
"""
    wt(out / "DD096ZD2ZF_GUARDED_ACTIVE_REPLACEMENT_EXECUTION_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zf_guarded_active_replacement_execution_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "candidate_dbf_root": str(candidate_dbf),
        "candidate_indexes_root": str(candidate_indexes),
        "candidate_lmdb_root": str(candidate_lmdb),
        "active_dbf_root": str(active_dbf),
        "active_indexes_root": str(active_indexes),
        "active_lmdb_root": str(active_lmdb),
        "backup_root_planned": str(backup_root),
        "precondition_blockers": blockers,
        "missing_candidate_artifacts": missing,
        "execution_scripts_written": scripts_written,
        "active_replacement_executed_by_generator": 0,
        "active_catalog_replacement": 0,
        "source_edits": 0,
        "failures": failures,
    }
    wj(out / "dd096zd2zf_guarded_active_replacement_execution_manifest.json", manifest)

    print(f"DD096Z-D2ZF guarded active replacement execution manifest: {out / 'dd096zd2zf_guarded_active_replacement_execution_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; missing_candidate_artifacts: {missing}; execution_scripts_written: {scripts_written}; active_replacement_executed_by_generator: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
