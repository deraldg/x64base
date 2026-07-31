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

def make_preview_ps1(candidate_dbf: Path, candidate_indexes: Path, candidate_lmdb: Path, active_dbf: Path, active_indexes: Path, active_lmdb: Path, backup_root: Path) -> str:
    return f"""# DD096Z-D2ZE guarded active replacement apply-plan preview
# Report-only preview. This script does NOT copy or delete files.

$CandidateDbf = "{candidate_dbf}"
$CandidateIndexes = "{candidate_indexes}"
$CandidateLmdb = "{candidate_lmdb}"
$ActiveDbf = "{active_dbf}"
$ActiveIndexes = "{active_indexes}"
$ActiveLmdb = "{active_lmdb}"
$BackupRoot = "{backup_root}"

Write-Host "DD096Z-D2ZE apply-plan preview only"
Write-Host "Candidate DBF:     $CandidateDbf"
Write-Host "Candidate INDEXES: $CandidateIndexes"
Write-Host "Candidate LMDB:    $CandidateLmdb"
Write-Host "Active DBF:        $ActiveDbf"
Write-Host "Active INDEXES:    $ActiveIndexes"
Write-Host "Active LMDB:       $ActiveLmdb"
Write-Host "Backup root:       $BackupRoot"
Write-Host ""
Write-Host "Candidate artifact counts:"
Get-ChildItem $CandidateDbf -Filter "*.dbf" -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count
Get-ChildItem $CandidateIndexes -Filter "*.cdx" -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count
Get-ChildItem $CandidateLmdb -Directory -Filter "*.cdx.d" -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count
Write-Host ""
Write-Host "Active artifact counts:"
Get-ChildItem $ActiveDbf -Filter "*.dbf" -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count
Get-ChildItem $ActiveIndexes -Filter "*.cdx" -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count
Get-ChildItem $ActiveLmdb -Directory -Filter "*.cdx.d" -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count
Write-Host ""
Write-Host "No active replacement was performed."
"""

def make_future_apply_skeleton(candidate_dbf: Path, candidate_indexes: Path, candidate_lmdb: Path, active_dbf: Path, active_indexes: Path, active_lmdb: Path, backup_root: Path) -> str:
    return f"""# DD096Z-D2ZE FUTURE APPLY SKELETON - DO NOT RUN AS-IS
# This is a design artifact only. It intentionally does not include executable replacement commands.

# Future guarded apply package should:
# 1. Require an explicit execute flag, e.g. -ExecuteActiveReplacement.
# 2. Refuse unless D2ZC and D2ZD manifests are green.
# 3. Create backup snapshot first.
# 4. Copy candidate DBF/CDX/LMDB artifacts.
# 5. Run DDICT and workspace smoke.
# 6. Provide rollback command map.

# Candidate DBF:     {candidate_dbf}
# Candidate INDEXES: {candidate_indexes}
# Candidate LMDB:    {candidate_lmdb}
# Active DBF:        {active_dbf}
# Active INDEXES:    {active_indexes}
# Active LMDB:       {active_lmdb}
# Backup root:       {backup_root}
"""

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZE guarded active replacement apply-plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZE-guarded-active-replacement-apply-plan-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--write-preview-scripts", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_guarded_active_replacement_apply_plan"
    gen.mkdir(parents=True, exist_ok=True)

    pre_rows = []
    blockers = 0
    for lane, rel, expected in REQUIRED:
        path = repo / rel
        data = read_json(path)
        observed = data.get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(path), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2ze_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    zd = read_json(repo / "docs/datadict/reports/DD096ZD2ZD-candidate-promotion-readiness-gate-v0/dd096zd2zd_candidate_promotion_readiness_gate_manifest.json")
    candidate_dbf = Path(zd.get("candidate_dbf_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/dbf"))
    candidate_indexes = Path(zd.get("candidate_indexes_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/indexes"))
    candidate_lmdb = Path(zd.get("candidate_lmdb_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/lmdb"))

    active_dbf = Path(zd.get("active_dbf_root", repo / "dottalkpp/data/datadict"))
    active_indexes = Path(zd.get("active_indexes_root", repo / "dottalkpp/data/indexes/datadict"))
    active_lmdb = Path(zd.get("active_lmdb_root", repo / "dottalkpp/data/lmdb/datadict"))
    backup_root = repo / f"docs/datadict/backups/DD096ZD2ZE-active-datadict-backup-preview-{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    root_rows = []
    for role, p, policy in [
        ("candidate_dbf", candidate_dbf, "future_source"),
        ("candidate_indexes", candidate_indexes, "future_source"),
        ("candidate_lmdb", candidate_lmdb, "future_source"),
        ("active_dbf", active_dbf, "protected_target"),
        ("active_indexes", active_indexes, "protected_target"),
        ("active_lmdb", active_lmdb, "protected_target"),
        ("backup_root", backup_root, "future_backup_target"),
    ]:
        root_rows.append({"role": role, "path": str(p), "exists": int(p.exists()), "bytes": size_bytes(p), "policy": policy})
    wc(gen / "dd096zd2ze_root_plan.csv", root_rows, ["role","path","exists","bytes","policy"])

    artifact_rows = []
    missing_candidate = 0
    for table, legacy, expected, tags in TABLES:
        artifacts = [
            ("dbf", candidate_dbf / f"{table}.dbf", active_dbf / f"{table}.dbf", backup_root / "dbf" / f"{table}.dbf"),
            ("cdx", candidate_indexes / f"{table}.cdx", active_indexes / f"{table}.cdx", backup_root / "indexes" / f"{table}.cdx"),
            ("lmdb_envdir", candidate_lmdb / f"{table}.cdx.d", active_lmdb / f"{table}.cdx.d", backup_root / "lmdb" / f"{table}.cdx.d"),
        ]
        for kind, src, target, backup in artifacts:
            exists = int(src.exists())
            missing_candidate += 0 if exists else 1
            artifact_rows.append({
                "table": table,
                "legacy_bridge_name": legacy,
                "artifact_kind": kind,
                "candidate_source": str(src),
                "candidate_exists": exists,
                "candidate_bytes": size_bytes(src),
                "candidate_sha256": file_sha256(src) if kind != "lmdb_envdir" else "",
                "active_target": str(target),
                "active_exists": int(target.exists()),
                "active_bytes": size_bytes(target),
                "backup_target": str(backup),
                "future_action": "copy_candidate_to_active_later_after_explicit_authorization",
            })
    wc(gen / "dd096zd2ze_candidate_to_active_artifact_plan.csv", artifact_rows, ["table","legacy_bridge_name","artifact_kind","candidate_source","candidate_exists","candidate_bytes","candidate_sha256","active_target","active_exists","active_bytes","backup_target","future_action"])

    backup_rows = []
    for role, p in [("active_dbf", active_dbf), ("active_indexes", active_indexes), ("active_lmdb", active_lmdb)]:
        backup_rows.append({
            "source_role": role,
            "source_path": str(p),
            "backup_path": str(backup_root / role),
            "source_exists": int(p.exists()),
            "source_bytes": size_bytes(p),
            "future_action": "copy_active_to_backup_before_any_replacement",
        })
    wc(gen / "dd096zd2ze_backup_plan.csv", backup_rows, ["source_role","source_path","backup_path","source_exists","source_bytes","future_action"])

    rollback_rows = []
    for role in ["active_dbf", "active_indexes", "active_lmdb"]:
        rollback_rows.append({
            "rollback_source": str(backup_root / role),
            "rollback_target": str({"active_dbf": active_dbf, "active_indexes": active_indexes, "active_lmdb": active_lmdb}[role]),
            "future_action": "restore_backup_to_active_if_post_apply_smoke_fails",
            "requires_explicit_authorization": 1,
        })
    wc(gen / "dd096zd2ze_rollback_plan.csv", rollback_rows, ["rollback_source","rollback_target","future_action","requires_explicit_authorization"])

    smoke_rows = [
        {"smoke_id": "D2ZE-S01", "surface": "DDICT STATUS", "purpose": "confirm resolver/root mode and read-only status after future replacement"},
        {"smoke_id": "D2ZE-S02", "surface": "DDICT TABLES", "purpose": "confirm DATA_DICTIONARY_* and/or legacy aliases resolve"},
        {"smoke_id": "D2ZE-S03", "surface": "DDICT FIELDS DATA_DICTIONARY_OBJECTS", "purpose": "confirm x64 long table name resolves"},
        {"smoke_id": "D2ZE-S04", "surface": "DDICT FIELDS DDOBJECT", "purpose": "confirm legacy alias bridge resolves"},
        {"smoke_id": "D2ZE-S05", "surface": "DDICT TAGS DATA_DICTIONARY_OBJECTS", "purpose": "confirm candidate tag visibility"},
        {"smoke_id": "D2ZE-S06", "surface": "DDICT REL DDICT BOTH", "purpose": "confirm relation family bridge"},
        {"smoke_id": "D2ZE-S07", "surface": "DDICT EVIDENCE DDICT", "purpose": "confirm evidence family bridge"},
        {"smoke_id": "D2ZE-S08", "surface": "WORKSPACE OPEN ddbase", "purpose": "confirm workspace schema path/root compatibility"},
    ]
    wc(gen / "dd096zd2ze_post_apply_smoke_requirements.csv", smoke_rows, ["smoke_id","surface","purpose"])

    bridge_rows = []
    for table, legacy, expected, tags in TABLES:
        bridge_rows.append({
            "legacy_name": legacy,
            "new_x64_name": table,
            "status_required_before_apply": "resolver_or_alias_bridge_available",
            "notes": "Do not strand DDICT/help/workspace consumers on legacy compact names without bridge.",
        })
    wc(gen / "dd096zd2ze_alias_bridge_gate.csv", bridge_rows, ["legacy_name","new_x64_name","status_required_before_apply","notes"])

    preview = make_preview_ps1(candidate_dbf, candidate_indexes, candidate_lmdb, active_dbf, active_indexes, active_lmdb, backup_root)
    skeleton = make_future_apply_skeleton(candidate_dbf, candidate_indexes, candidate_lmdb, active_dbf, active_indexes, active_lmdb, backup_root)
    wt(gen / "DD096ZD2ZE_APPLY_PLAN_PREVIEW.ps1", preview)
    wt(gen / "DD096ZD2ZE_FUTURE_APPLY_SKELETON_DO_NOT_RUN.ps1", skeleton)

    scripts_written = 0
    if args.write_preview_scripts:
        wt(repo / "tools/datadict/catalog/DD096ZD2ZE_APPLY_PLAN_PREVIEW.ps1", preview)
        wt(repo / "tools/datadict/catalog/DD096ZD2ZE_FUTURE_APPLY_SKELETON_DO_NOT_RUN.ps1", skeleton)
        scripts_written = 1

    gate_rows = [
        {"gate": "preconditions_green", "observed": blockers, "required": 0, "pass": int(blockers == 0)},
        {"gate": "candidate_artifacts_present", "observed": missing_candidate, "required": 0, "pass": int(missing_candidate == 0)},
        {"gate": "preview_scripts_written_if_requested", "observed": scripts_written, "required": int(args.write_preview_scripts), "pass": int(scripts_written == int(args.write_preview_scripts))},
        {"gate": "active_replacement_authorized", "observed": 0, "required": 0, "pass": 1},
        {"gate": "active_replacement_executed", "observed": 0, "required": 0, "pass": 1},
    ]
    failures = sum(1 for row in gate_rows if int(row["pass"]) != 1)
    wc(out / "dd096zd2ze_gate_ledger.csv", gate_rows, ["gate","observed","required","pass"])

    boundary_rows = [
        {"boundary": "guarded_active_replacement_apply_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_dbf_copy_or_write", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_cdx_lmdb_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "workspace_schema_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2ze_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary","observed","required","pass"])

    status = "DD096ZD2ZE_GUARDED_ACTIVE_REPLACEMENT_APPLY_PLAN_READY" if failures == 0 else "DD096ZD2ZE_GUARDED_ACTIVE_REPLACEMENT_APPLY_PLAN_REVIEW"

    report = f"""# DD096Z-D2ZE Guarded Active Replacement Apply Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2ZE is the first active-replacement planning lane after D2ZD green.

It is not an execution package. It creates the backup map, copy map, rollback map, resolver bridge requirements, post-apply smoke requirements, and boundary ledger for a future guarded apply package.

## Summary

- Precondition blockers: **{blockers}**
- Missing candidate artifacts: **{missing_candidate}**
- Preview scripts written: **{scripts_written}**
- Active replacement authorized: **0**
- Active replacement executed: **0**
- Active DBF copy/write: **0**
- Active CDX/LMDB rebuild: **0**
- Source edits: **0**
- HELP/CMDHELPCHK mutation: **0**

## Candidate roots

- `{candidate_dbf}`
- `{candidate_indexes}`
- `{candidate_lmdb}`

## Protected active roots

- `{active_dbf}`
- `{active_indexes}`
- `{active_lmdb}`

## Future apply must require

- explicit execution authorization
- active backup snapshot first
- rollback map
- DDICT resolver/alias smoke
- workspace restore smoke
- no HELP/CMDHELPCHK mutation unless separately authorized
"""
    wt(out / "DD096ZD2ZE_GUARDED_ACTIVE_REPLACEMENT_APPLY_PLAN_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2ze_guarded_active_replacement_apply_plan_v0",
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
        "backup_root_preview": str(backup_root),
        "precondition_blockers": blockers,
        "missing_candidate_artifacts": missing_candidate,
        "preview_scripts_written": scripts_written,
        "active_replacement_authorized": 0,
        "active_replacement_executed": 0,
        "active_catalog_replacement": 0,
        "active_cdx_lmdb_rebuild": 0,
        "source_edits": 0,
        "failures": failures,
        "next_recommended_action": "Review apply plan outputs; only then authorize a separate guarded apply execution package if desired.",
    }
    wj(out / "dd096zd2ze_guarded_active_replacement_apply_plan_manifest.json", manifest)

    print(f"DD096Z-D2ZE guarded active replacement apply plan manifest: {out / 'dd096zd2ze_guarded_active_replacement_apply_plan_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; missing_candidate_artifacts: {missing_candidate}; active_replacement_executed: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
