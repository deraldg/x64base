#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, os, re
from pathlib import Path

TABLES = [
    "DATA_DICTIONARY_OBJECTS",
    "DATA_DICTIONARY_OBJECT_ATTRIBUTES",
    "DATA_DICTIONARY_RELATION_EDGES",
    "DATA_DICTIONARY_EVIDENCE_RECORDS",
    "DATA_DICTIONARY_GATE_RECORDS",
    "DATA_DICTIONARY_RUNS",
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

def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")

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

def dir_size(path: Path) -> int:
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

def scan_runtime(text: str):
    up = text.upper()
    return {
        "proof_supplied": int(bool(text)),
        "candidate_path_seen": int("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up),
        "active_datadict_path_seen": int("DOTTALKPP\\DATA\\DATADICT" in up or "DOTTALKPP/DATA/DATADICT" in up),
        "mdb_env_open_112_count": len(re.findall(r"MDB_ENV_OPEN FAILED:\s*112", up)),
        "not_enough_space_count": len(re.findall(r"NOT ENOUGH SPACE ON THE DISK", up)),
        "buildlmdb_failed_count": len(re.findall(r"BUILDLMDB:\s*FAILED TO BUILD LMDB ENVIRONMENT", up)),
        "buildlmdb_ok_count": len(re.findall(r"BUILDLMDB:\s*DONE\s+OK=", up)),
        "cdx_create_or_exists_count": len(re.findall(r"CDX (CREATED|CREATE:\s*FILE ALREADY EXISTS)", up)),
        "cdx_addtag_count": len(re.findall(r"CDX ADDTAG:\s*(ADDED|TAG ALREADY EXISTS)", up)),
        "set_order_backend_failed_count": len(re.findall(r"SET ORDER:\s*OPENCDX|SET ORDER:\s*OPENDCX", up)),
        "table_cdx_fallback_seen": int("\\INDEXES\\TABLE.CDX" in up or "/INDEXES/TABLE.CDX" in up),
    }

def make_space_report_ps1(candidate_root: Path, lmdb_root: Path) -> str:
    return """# DD096Z-D2Z candidate LMDB space report
# Read-only. No deletion.
$CandidateRoot = "__CANDIDATE_ROOT__"
$CandidateLmdb = "__LMDB_ROOT__"
Write-Host "DD096Z-D2Z candidate LMDB space report"
Write-Host "Candidate root: $CandidateRoot"
Write-Host "Candidate LMDB: $CandidateLmdb"
Write-Host ""
Write-Host "Drive space:"
Get-PSDrive -Name D | Format-Table Name,Used,Free,Provider,Root -AutoSize
Write-Host ""
Write-Host "Candidate LMDB top-level items:"
if (Test-Path $CandidateLmdb) {
  Get-ChildItem $CandidateLmdb -Force | ForEach-Object {
    $size = if ($_.PSIsContainer) { (Get-ChildItem $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum } else { $_.Length }
    [pscustomobject]@{ Name=$_.Name; Mode=$_.Mode; LastWriteTime=$_.LastWriteTime; Bytes=[int64]$size; Path=$_.FullName }
  } | Sort-Object Bytes -Descending | Format-Table Name,Mode,LastWriteTime,Bytes,Path -AutoSize
} else {
  Write-Host "Candidate LMDB path does not exist."
}
Write-Host ""
Write-Host "Candidate LMDB backups:"
$BackupRoot = Join-Path $CandidateLmdb "backups"
if (Test-Path $BackupRoot) {
  Get-ChildItem $BackupRoot -Force | ForEach-Object {
    $size = if ($_.PSIsContainer) { (Get-ChildItem $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum } else { $_.Length }
    [pscustomobject]@{ Name=$_.Name; Mode=$_.Mode; LastWriteTime=$_.LastWriteTime; Bytes=[int64]$size; Path=$_.FullName }
  } | Sort-Object Bytes -Descending | Format-Table Name,Mode,LastWriteTime,Bytes,Path -AutoSize
} else {
  Write-Host "No backups directory found."
}
""".replace("__CANDIDATE_ROOT__", str(candidate_root)).replace("__LMDB_ROOT__", str(lmdb_root))

def make_cleanup_review_ps1(candidate_root: Path, lmdb_root: Path) -> str:
    return """# DD096Z-D2Z candidate LMDB cleanup REVIEW script
# Preview only by default. Pass -ExecuteCandidateCleanup to delete candidate LMDB envdirs/backups.
param([switch]$ExecuteCandidateCleanup)
$CandidateRoot = "__CANDIDATE_ROOT__"
$CandidateLmdb = "__LMDB_ROOT__"
$ForbiddenActiveFragment = "dottalkpp\\data\\lmdb\\datadict"
Write-Host "DD096Z-D2Z candidate LMDB cleanup"
Write-Host "Candidate root: $CandidateRoot"
Write-Host "Candidate LMDB: $CandidateLmdb"
Write-Host "ExecuteCandidateCleanup: $ExecuteCandidateCleanup"
if (-not (Test-Path $CandidateLmdb)) { throw "Candidate LMDB path does not exist: $CandidateLmdb" }
if ($CandidateLmdb.ToLowerInvariant().Contains($ForbiddenActiveFragment)) { throw "REFUSING active datadict LMDB path: $CandidateLmdb" }
if (-not $CandidateLmdb.ToLowerInvariant().Contains("docs\\datadict\\candidates")) { throw "REFUSING non-candidate LMDB path: $CandidateLmdb" }
$Targets = @()
$Targets += Get-ChildItem $CandidateLmdb -Force -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*.cdx.d" }
$BackupRoot = Join-Path $CandidateLmdb "backups"
if (Test-Path $BackupRoot) { $Targets += Get-ChildItem $BackupRoot -Force -Directory -ErrorAction SilentlyContinue }
Write-Host ""
Write-Host "Candidate-only cleanup targets:"
$Targets | ForEach-Object {
  $size = (Get-ChildItem $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
  [pscustomobject]@{ Name=$_.Name; LastWriteTime=$_.LastWriteTime; Bytes=[int64]$size; Path=$_.FullName }
} | Sort-Object Bytes -Descending | Format-Table Name,LastWriteTime,Bytes,Path -AutoSize
if (-not $ExecuteCandidateCleanup) {
  Write-Host ""
  Write-Host "Preview only. Rerun with -ExecuteCandidateCleanup to delete these candidate-only LMDB envdirs/backups."
  return
}
foreach ($Target in $Targets) {
  Write-Host "Removing candidate-only LMDB path: $($Target.FullName)"
  Remove-Item $Target.FullName -Recurse -Force
}
Write-Host "Cleanup complete. Re-run D2Y after confirming drive space."
Get-PSDrive -Name D | Format-Table Name,Used,Free,Provider,Root -AutoSize
""".replace("__CANDIDATE_ROOT__", str(candidate_root)).replace("__LMDB_ROOT__", str(lmdb_root))

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2Z candidate LMDB disk-space recovery")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2Z-candidate-lmdb-space-recovery-v0")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--write-powershell-scripts", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_candidate_lmdb_space_recovery"
    gen.mkdir(parents=True, exist_ok=True)

    d2s = read_json(repo / "docs/datadict/reports/DD096ZD2S-single-table-cdx-lmdb-proof-closure-v0/dd096zd2s_single_table_cdx_lmdb_proof_closure_manifest.json")
    d2s_status = d2s.get("status", "MISSING")
    precondition_blockers = 0 if d2s_status == "DD096ZD2S_SINGLE_TABLE_CDX_LMDB_PROOF_GREEN" else 1
    wc(gen / "dd096zd2z_precondition_ledger.csv", [{
        "lane": "DD096ZD2S",
        "observed_status": d2s_status,
        "expected_status": "DD096ZD2S_SINGLE_TABLE_CDX_LMDB_PROOF_GREEN",
        "pass": int(precondition_blockers == 0),
    }], ["lane","observed_status","expected_status","pass"])

    zb = read_json(repo / "docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json")
    candidate_root = Path(zb.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_lmdb = candidate_root / "lmdb"
    candidate_indexes = candidate_root / "indexes"

    storage_rows = []
    roots = [
        ("candidate_root", candidate_root, "read_only"),
        ("candidate_indexes", candidate_indexes, "read_only"),
        ("candidate_lmdb", candidate_lmdb, "candidate_cleanup_allowed_with_explicit_flag"),
        ("candidate_lmdb_backups", candidate_lmdb / "backups", "candidate_cleanup_allowed_with_explicit_flag"),
        ("active_lmdb_datadict", repo / "dottalkpp/data/lmdb/datadict", "forbidden"),
    ]
    for name, p, policy in roots:
        storage_rows.append({"root": name, "path": str(p), "exists": int(p.exists()), "bytes": dir_size(p), "policy": policy})
    wc(gen / "dd096zd2z_storage_inventory.csv", storage_rows, ["root","path","exists","bytes","policy"])

    env_rows = []
    for table in TABLES:
        env = candidate_lmdb / f"{table}.cdx.d"
        env_rows.append({"table": table, "kind": "current_envdir", "path": str(env), "exists": int(env.exists()), "bytes": dir_size(env)})
    backups = candidate_lmdb / "backups"
    if backups.exists():
        for child in sorted(backups.iterdir()):
            if child.is_dir() and any(child.name.startswith(f"{table}.cdx.d") for table in TABLES):
                table = child.name.split(".cdx.d")[0]
                env_rows.append({"table": table, "kind": "backup_envdir", "path": str(child), "exists": 1, "bytes": dir_size(child)})
    wc(gen / "dd096zd2z_candidate_lmdb_envdir_inventory.csv", env_rows, ["table","kind","path","exists","bytes"])

    metrics = scan_runtime("")
    proof_supplied = 0
    if args.runtime_proof:
        p = Path(args.runtime_proof)
        if not p.is_absolute():
            p = repo / p
        metrics = scan_runtime(read_text(p))
        proof_supplied = metrics["proof_supplied"]
    wc(gen / "dd096zd2z_runtime_failure_scan.csv", [{"metric": k, "value": v} for k, v in sorted(metrics.items())], ["metric","value"])

    ps_report = make_space_report_ps1(candidate_root, candidate_lmdb)
    ps_cleanup = make_cleanup_review_ps1(candidate_root, candidate_lmdb)
    wt(gen / "DD096ZD2Z_CANDIDATE_LMDB_SPACE_REPORT.ps1", ps_report)
    wt(gen / "DD096ZD2Z_CANDIDATE_LMDB_CLEANUP_REVIEW.ps1", ps_cleanup)

    ps_written = 0
    if args.write_powershell_scripts:
        wt(repo / "tools/datadict/catalog/DD096ZD2Z_CANDIDATE_LMDB_SPACE_REPORT.ps1", ps_report)
        wt(repo / "tools/datadict/catalog/DD096ZD2Z_CANDIDATE_LMDB_CLEANUP_REVIEW.ps1", ps_cleanup)
        ps_written = 1

    findings = [
        {"finding_id": "D2Z-F01", "finding": "D2Y opened candidate DATA_DICTIONARY tables from docs/datadict/candidates.", "classification": "green"},
        {"finding_id": "D2Z-F02", "finding": "D2Y is blocked by LMDB mdb_env_open 112 / not enough disk space.", "classification": "red_environment"},
        {"finding_id": "D2Z-F03", "finding": "CDX containers and tags are created or reused before LMDB.", "classification": "green"},
        {"finding_id": "D2Z-F04", "finding": "SET ORDER failures are downstream of failed LMDB env creation.", "classification": "downstream"},
    ]
    wc(gen / "dd096zd2z_findings.csv", findings, ["finding_id","finding","classification"])

    proof_failures = 0
    if proof_supplied:
        if metrics.get("candidate_path_seen", 0) != 1:
            proof_failures += 1
        if metrics.get("mdb_env_open_112_count", 0) < 1 and metrics.get("not_enough_space_count", 0) < 1:
            proof_failures += 1
        if metrics.get("active_datadict_path_seen", 0) != 0:
            proof_failures += 1
        if metrics.get("table_cdx_fallback_seen", 0) != 0:
            proof_failures += 1

    failures = precondition_blockers + (proof_failures if proof_supplied else 0)
    if failures:
        status = "DD096ZD2Z_CANDIDATE_LMDB_SPACE_RECOVERY_REVIEW"
    elif proof_supplied:
        status = "DD096ZD2Z_CANDIDATE_LMDB_SPACE_RECOVERY_CONFIRMED"
    else:
        status = "DD096ZD2Z_CANDIDATE_LMDB_SPACE_RECOVERY_READY"

    wc(out / "dd096zd2z_no_mutation_boundary_ledger.csv", [
        {"boundary": "candidate_lmdb_space_recovery_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "powershell_scripts_written", "observed": ps_written, "required": int(args.write_powershell_scripts), "pass": int(ps_written == int(args.write_powershell_scripts))},
        {"boundary": "candidate_cleanup_executed_by_python", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_cdx_lmdb_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
    ], ["boundary","observed","required","pass"])

    report = f"# DD096Z-D2Z Candidate LMDB Space Recovery\n\nRun id: `{args.run_id}`\nStatus: **{status}**\nCreated UTC: `{now()}`\n\n## Purpose\n\nD2Y fixed candidate table identity and CDX/tag setup. The remaining blocker is LMDB environment creation:\n\n```text\nBUILDLMDB: mdb_env_open failed: 112 (There is not enough space on the disk.)\n```\n\n## Summary\n\n- Candidate root: `{candidate_root}`\n- Candidate LMDB root: `{candidate_lmdb}`\n- Precondition blockers: **{precondition_blockers}**\n- Runtime proof supplied: **{proof_supplied}**\n- mdb_env_open 112 count: **{metrics.get('mdb_env_open_112_count', 0)}**\n- not-enough-space count: **{metrics.get('not_enough_space_count', 0)}**\n- BUILDLMDB failed count: **{metrics.get('buildlmdb_failed_count', 0)}**\n- PowerShell scripts written: **{ps_written}**\n- Candidate cleanup executed by this generator: **0**\n- Active catalog replacement: **0**\n\n## Generated scripts\n\n- `DD096ZD2Z_CANDIDATE_LMDB_SPACE_REPORT.ps1`\n- `DD096ZD2Z_CANDIDATE_LMDB_CLEANUP_REVIEW.ps1`\n\nThe cleanup script is preview-only unless called with `-ExecuteCandidateCleanup`.\n"
    wt(out / "DD096ZD2Z_CANDIDATE_LMDB_SPACE_RECOVERY_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2z_candidate_lmdb_space_recovery_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "candidate_root": str(candidate_root),
        "candidate_lmdb_root": str(candidate_lmdb),
        "precondition_blockers": precondition_blockers,
        "runtime_proof_supplied": proof_supplied,
        "mdb_env_open_112_count": metrics.get("mdb_env_open_112_count", 0),
        "not_enough_space_count": metrics.get("not_enough_space_count", 0),
        "buildlmdb_failed_count": metrics.get("buildlmdb_failed_count", 0),
        "powershell_scripts_written": ps_written,
        "candidate_cleanup_executed_by_generator": 0,
        "active_catalog_replacement": 0,
        "source_edits": 0,
        "failures": failures,
    }
    wj(out / "dd096zd2z_candidate_lmdb_space_recovery_manifest.json", manifest)

    print(f"DD096Z-D2Z candidate LMDB space recovery manifest: {out / 'dd096zd2z_candidate_lmdb_space_recovery_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {precondition_blockers}; mdb_env_open_112_count: {metrics.get('mdb_env_open_112_count', 0)}; not_enough_space_count: {metrics.get('not_enough_space_count', 0)}; powershell_scripts_written: {ps_written}; active_catalog_replacement: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
