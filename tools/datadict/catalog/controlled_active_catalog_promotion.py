#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


TABLES = [
    "DDRUN",
    "DDBASE",
    "DDSOURCE",
    "DDOBJECT",
    "DDATTR",
    "DDEDGE",
    "DDEVID",
    "DDGATE",
    "DDREVIEW",
    "DDARTIF",
    "DDPROFILE",
]

MEMO_TABLES = {
    "DDRUN",
    "DDBASE",
    "DDATTR",
    "DDEVID",
    "DDGATE",
    "DDREVIEW",
    "DDPROFILE",
}

EXPECTED_COUNTS = {
    "DDRUN": 1,
    "DDBASE": 1,
    "DDSOURCE": 7,
    "DDOBJECT": 100,
    "DDATTR": 423,
    "DDEDGE": 89,
    "DDEVID": 1,
    "DDGATE": 6,
    "DDREVIEW": 0,
    "DDARTIF": 7,
    "DDPROFILE": 3,
}


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def timestamp_id() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_summary(path: Path) -> Tuple[int, int, str]:
    if not path.exists() or not path.is_dir():
        return 0, 0, ""
    files = 0
    total = 0
    h = hashlib.sha256()
    for p in sorted(path.rglob("*"), key=lambda q: q.as_posix().lower()):
        if p.is_file():
            files += 1
            b = p.read_bytes()
            total += len(b)
            h.update(p.relative_to(path).as_posix().encode("utf-8"))
            h.update(b)
    return files, total, h.hexdigest()


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def harden_pydottalk_path(repo: Path) -> Dict[str, Any]:
    build_python = repo / "build" / "python"
    added = 0
    if build_python.exists():
        bp = str(build_python.resolve())
        if bp not in sys.path:
            sys.path.insert(0, bp)
            added = 1
    return {
        "build_python_path": str(build_python),
        "build_python_exists": int(build_python.exists()),
        "added_to_sys_path": added,
    }


def ensure_safe_paths(repo: Path, staged: Path, active: Path, backup_root: Path) -> None:
    if staged.resolve() == active.resolve():
        raise SystemExit("Refusing promotion because staged path equals active path")
    for p, label in [(staged, "staged"), (active, "active"), (backup_root, "backup_root")]:
        try:
            p.resolve().relative_to(repo.resolve())
        except Exception:
            raise SystemExit(f"{label} path must be inside repo: {p}")
    if "datadict_canonical_rebuild_v0" not in staged.resolve().as_posix().lower():
        raise SystemExit(f"Staged path lacks safety marker datadict_canonical_rebuild_v0: {staged}")
    if "metadata/datadict" not in active.resolve().as_posix().replace("\\", "/").lower():
        raise SystemExit(f"Active path does not look like metadata/datadict: {active}")


def required_staged_artifacts(repo: Path, staged_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for table in TABLES:
        stem = table.lower()
        dbf = staged_path / f"{stem}.dbf"
        rows.append({
            "table": table,
            "kind": "DBF",
            "required": 1,
            "path": safe_rel(repo, dbf),
            "exists": int(dbf.exists()),
            "bytes": dbf.stat().st_size if dbf.exists() else "",
            "sha256": sha256_file(dbf) if dbf.exists() else "",
        })
        dtx = staged_path / f"{stem}.dtx"
        rows.append({
            "table": table,
            "kind": "DTX",
            "required": int(table in MEMO_TABLES),
            "path": safe_rel(repo, dtx),
            "exists": int(dtx.exists()),
            "bytes": dtx.stat().st_size if dtx.exists() else "",
            "sha256": sha256_file(dtx) if dtx.exists() else "",
        })
    return rows


def cdx_lmdb_artifacts(repo: Path, index_path: Path, lmdb_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for table in TABLES:
        stem = table.lower()
        cdx = index_path / f"{stem}.cdx"
        rows.append({
            "table": table,
            "kind": "CDX",
            "path": safe_rel(repo, cdx),
            "exists": int(cdx.exists()),
            "bytes": cdx.stat().st_size if cdx.exists() else "",
            "sha256": sha256_file(cdx) if cdx.exists() else "",
        })
        env = lmdb_path / f"{stem}.cdx.d"
        files, total, digest = dir_summary(env)
        rows.append({
            "table": table,
            "kind": "LMDB",
            "path": safe_rel(repo, env),
            "exists": int(env.exists() and env.is_dir()),
            "bytes": total if env.exists() else "",
            "sha256": digest if env.exists() else "",
            "file_count": files if env.exists() else "",
        })
    return rows


def active_artifacts(repo: Path, active_path: Path, index_path: Path, lmdb_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for table in TABLES:
        stem = table.lower()
        for kind, path in [
            ("ACTIVE_DBF", active_path / f"{stem}.dbf"),
            ("ACTIVE_DTX", active_path / f"{stem}.dtx"),
            ("ACTIVE_CDX", index_path / f"{stem}.cdx"),
            ("ACTIVE_LMDB", lmdb_path / f"{stem}.cdx.d"),
        ]:
            if path.is_file():
                rows.append({
                    "table": table,
                    "kind": kind,
                    "path": safe_rel(repo, path),
                    "exists": 1,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                })
            elif path.is_dir():
                files, total, digest = dir_summary(path)
                rows.append({
                    "table": table,
                    "kind": kind,
                    "path": safe_rel(repo, path),
                    "exists": 1,
                    "bytes": total,
                    "sha256": digest,
                    "file_count": files,
                })
            else:
                rows.append({
                    "table": table,
                    "kind": kind,
                    "path": safe_rel(repo, path),
                    "exists": 0,
                    "bytes": "",
                    "sha256": "",
                })
    return rows


def copy_file_with_dirs(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_dir(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    if src.exists():
        shutil.copytree(src, dst)


def create_restore_script(repo: Path, backup_dir: Path, active_path: Path, index_path: Path, lmdb_path: Path) -> Path:
    restore = backup_dir / "restore_dd058_backup.ps1"
    content = f"""# Restore script generated by DD-058
# Run from PowerShell after reviewing paths.

$RepoRoot = "{repo}"
$BackupRoot = "{backup_dir}"

$ActiveCatalog = "{active_path}"
$IndexPath = "{index_path}"
$LmdbPath = "{lmdb_path}"

Write-Host "Restoring active catalog from DD-058 backup..."
if (Test-Path "$BackupRoot\\active_metadata_datadict") {{
  if (Test-Path $ActiveCatalog) {{ Remove-Item $ActiveCatalog -Recurse -Force }}
  Copy-Item "$BackupRoot\\active_metadata_datadict" $ActiveCatalog -Recurse -Force
}}

Write-Host "Restoring related CDX files..."
if (Test-Path "$BackupRoot\\indexes") {{
  Get-ChildItem "$BackupRoot\\indexes" -Filter "*.cdx" | ForEach-Object {{
    Copy-Item $_.FullName (Join-Path $IndexPath $_.Name) -Force
  }}
}}

Write-Host "Restoring related LMDB environments..."
if (Test-Path "$BackupRoot\\lmdb") {{
  Get-ChildItem "$BackupRoot\\lmdb" -Directory | ForEach-Object {{
    $dest = Join-Path $LmdbPath $_.Name
    if (Test-Path $dest) {{ Remove-Item $dest -Recurse -Force }}
    Copy-Item $_.FullName $dest -Recurse -Force
  }}
}}

Write-Host "DD-058 restore complete. Run post-restore verification before continuing."
"""
    restore.write_text(content, encoding="utf-8")
    return restore


def backup_existing(repo: Path, backup_dir: Path, active_path: Path, index_path: Path, lmdb_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Active metadata/datadict directory.
    active_backup = backup_dir / "active_metadata_datadict"
    if active_path.exists():
        copy_dir(active_path, active_backup)
        files, total, digest = dir_summary(active_backup)
        rows.append({
            "artifact_group": "active_metadata_datadict",
            "source": safe_rel(repo, active_path),
            "backup": safe_rel(repo, active_backup),
            "files": files,
            "bytes": total,
            "sha256": digest,
            "status": "BACKED_UP",
        })
    else:
        rows.append({
            "artifact_group": "active_metadata_datadict",
            "source": safe_rel(repo, active_path),
            "backup": safe_rel(repo, active_backup),
            "files": 0,
            "bytes": 0,
            "sha256": "",
            "status": "SOURCE_MISSING_BACKUP_SKIPPED",
        })

    # Related CDX files.
    index_backup = backup_dir / "indexes"
    index_backup.mkdir(parents=True, exist_ok=True)
    cdx_count = 0
    for table in TABLES:
        src = index_path / f"{table.lower()}.cdx"
        if src.exists():
            copy_file_with_dirs(src, index_backup / src.name)
            cdx_count += 1
    files, total, digest = dir_summary(index_backup)
    rows.append({
        "artifact_group": "related_cdx_files",
        "source": safe_rel(repo, index_path),
        "backup": safe_rel(repo, index_backup),
        "files": files,
        "bytes": total,
        "sha256": digest,
        "status": f"BACKED_UP_{cdx_count}_CDX",
    })

    # Related LMDB envs.
    lmdb_backup = backup_dir / "lmdb"
    lmdb_backup.mkdir(parents=True, exist_ok=True)
    env_count = 0
    for table in TABLES:
        src = lmdb_path / f"{table.lower()}.cdx.d"
        if src.exists() and src.is_dir():
            copy_dir(src, lmdb_backup / src.name)
            env_count += 1
    files, total, digest = dir_summary(lmdb_backup)
    rows.append({
        "artifact_group": "related_lmdb_envs",
        "source": safe_rel(repo, lmdb_path),
        "backup": safe_rel(repo, lmdb_backup),
        "files": files,
        "bytes": total,
        "sha256": digest,
        "status": f"BACKED_UP_{env_count}_LMDB_ENVS",
    })

    restore = create_restore_script(repo, backup_dir, active_path, index_path, lmdb_path)
    rows.append({
        "artifact_group": "restore_script",
        "source": "generated",
        "backup": safe_rel(repo, restore),
        "files": 1,
        "bytes": restore.stat().st_size,
        "sha256": sha256_file(restore),
        "status": "GENERATED",
    })
    return rows


def promote_dbf_dtx(repo: Path, staged_path: Path, active_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    active_path.mkdir(parents=True, exist_ok=True)
    for table in TABLES:
        stem = table.lower()
        for suffix, required in [(".dbf", 1), (".dtx", int(table in MEMO_TABLES))]:
            src = staged_path / f"{stem}{suffix}"
            dst = active_path / f"{stem}{suffix}"
            action = "SKIPPED_OPTIONAL_MISSING"
            if src.exists():
                copy_file_with_dirs(src, dst)
                action = "COPIED"
            elif required:
                action = "MISSING_REQUIRED_SOURCE"
            rows.append({
                "table": table,
                "kind": suffix.upper().lstrip("."),
                "source": safe_rel(repo, src),
                "destination": safe_rel(repo, dst),
                "required": required,
                "source_exists": int(src.exists()),
                "destination_exists": int(dst.exists()),
                "destination_bytes": dst.stat().st_size if dst.exists() else "",
                "destination_sha256": sha256_file(dst) if dst.exists() else "",
                "action": action,
            })
    return rows


def pydottalk_verify(repo: Path, active_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    path_info = harden_pydottalk_path(repo)
    try:
        mod = importlib.import_module("pydottalk")
        import_ok = 1
        import_error = ""
    except Exception as exc:
        mod = None
        import_ok = 0
        import_error = f"{type(exc).__name__}: {exc}"

    for table in TABLES:
        expected = EXPECTED_COUNTS[table]
        row = {
            "table": table,
            "expected_rows": expected,
            "import_ok": import_ok,
            "open_ok": 0,
            "rec_count": "",
            "row_count_match": 0,
            "field_count": "",
            "memo_path": "",
            "memo_kind": "",
            "error": import_error,
            "build_python_exists": path_info["build_python_exists"],
        }
        if import_ok and mod is not None:
            try:
                dbf = active_path / f"{table.lower()}.dbf"
                a = mod.Dbf()
                a.open(str(dbf))
                row["open_ok"] = int(a.isOpen())
                rc = int(a.recCount())
                row["rec_count"] = rc
                row["row_count_match"] = int(rc == expected)
                row["field_count"] = int(a.fieldCount())
                try:
                    row["memo_path"] = str(a.memoPath())
                except Exception:
                    pass
                try:
                    row["memo_kind"] = str(a.memoKind())
                except Exception:
                    pass
                a.close()
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
    return rows


def build_runtime_verify_script(active_slot: str = "metadata\\datadict") -> str:
    lines = [
        "* DD-058 post-promotion runtime verification script",
        "* Active Data Dictionary catalog verification.",
        f"setpath dbf {active_slot}",
        "",
    ]
    reps = [
        ("ddrun", "RUNID"),
        ("ddbase", "BASEID"),
        ("ddobject", "OBJID"),
        ("ddattr", "OBJID"),
        ("ddedge", "FROMOBJ"),
        ("ddgate", "STATUS"),
        ("ddprofile", "NAME"),
    ]
    for table, tag in reps:
        lines.extend([
            f"use {table}",
            f"set index to {table}",
            f"set order to tag {tag}",
            "count",
            "list",
            "",
        ])
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-058 controlled active Data Dictionary catalog promotion execution")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD058-controlled-active-catalog-promotion-v0")
    ap.add_argument("--staged-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--index-path", default="dottalkpp/data/indexes")
    ap.add_argument("--lmdb-path", default="dottalkpp/data/lmdb")
    ap.add_argument("--backup-root", default="dottalkpp/data/metadata/datadict_promotion_backups")
    ap.add_argument("--dd057-dir", default="docs/datadict/reports/DD057-active-catalog-promotion-readiness-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--execute-promotion", action="store_true", help="Actually promote staged DBF/DTX to active catalog after backup")
    ap.add_argument("--post-verify", action="store_true", help="Run active catalog pydottalk post-promotion verification")
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    staged_path = (repo / args.staged_path).resolve()
    active_path = (repo / args.active_path).resolve()
    index_path = (repo / args.index_path).resolve()
    lmdb_path = (repo / args.lmdb_path).resolve()
    backup_root = (repo / args.backup_root).resolve()
    dd057_dir = (repo / args.dd057_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    ensure_safe_paths(repo, staged_path, active_path, backup_root)

    dd057_manifest = read_json(dd057_dir / "dd057_active_catalog_promotion_readiness_manifest.json")
    dd057_ready = dd057_manifest.get("status") == "ACTIVE_CATALOG_PROMOTION_READINESS_PLAN_READY"

    staged_rows = required_staged_artifacts(repo, staged_path)
    index_rows = cdx_lmdb_artifacts(repo, index_path, lmdb_path)
    active_before_rows = active_artifacts(repo, active_path, index_path, lmdb_path)

    missing_required = [
        r for r in staged_rows
        if int(r.get("required", 0)) == 1 and int(r.get("exists", 0)) != 1
    ]
    missing_cdx_lmdb = [
        r for r in index_rows
        if int(r.get("exists", 0)) != 1
    ]

    failures = 0
    review_rows: List[Dict[str, Any]] = []
    if not dd057_ready:
        failures += 1
        review_rows.append({"issue": "DD057_NOT_READY", "detail": dd057_manifest.get("status", "")})
    if missing_required:
        failures += len(missing_required)
        for r in missing_required:
            review_rows.append({"issue": "MISSING_REQUIRED_STAGED_ARTIFACT", "detail": f"{r['table']} {r['kind']} {r['path']}"})
    if missing_cdx_lmdb:
        failures += len(missing_cdx_lmdb)
        for r in missing_cdx_lmdb:
            review_rows.append({"issue": "MISSING_CDX_OR_LMDB_ARTIFACT", "detail": f"{r['table']} {r['kind']} {r['path']}"})

    backup_rows: List[Dict[str, Any]] = []
    promotion_rows: List[Dict[str, Any]] = []
    active_after_rows: List[Dict[str, Any]] = []
    verify_rows: List[Dict[str, Any]] = []
    backup_dir = backup_root / f"{args.run_id}_{timestamp_id()}"
    restore_script = ""

    if args.execute_promotion and failures == 0:
        backup_rows = backup_existing(repo, backup_dir, active_path, index_path, lmdb_path)
        promotion_rows = promote_dbf_dtx(repo, staged_path, active_path)
        active_after_rows = active_artifacts(repo, active_path, index_path, lmdb_path)
        restore_script = str(backup_dir / "restore_dd058_backup.ps1")
        # Check copy actions.
        for r in promotion_rows:
            if int(r.get("required", 0)) == 1 and r.get("action") != "COPIED":
                failures += 1
                review_rows.append({"issue": "PROMOTION_COPY_FAILED", "detail": f"{r['table']} {r['kind']} {r.get('action')}"})

    if args.post_verify:
        verify_rows = pydottalk_verify(repo, active_path)
        for r in verify_rows:
            if int(r.get("row_count_match", 0)) != 1:
                failures += 1
                review_rows.append({"issue": "POST_VERIFY_ROW_COUNT_MISMATCH", "detail": f"{r['table']} expected {r['expected_rows']} observed {r.get('rec_count')} error {r.get('error')}"})

    if args.execute_promotion and args.post_verify:
        status = "ACTIVE_CATALOG_PROMOTION_EXECUTED_AND_VERIFIED" if failures == 0 else "ACTIVE_CATALOG_PROMOTION_EXECUTION_REVIEW"
    elif args.execute_promotion:
        status = "ACTIVE_CATALOG_PROMOTION_EXECUTED_BACKUP_CREATED" if failures == 0 else "ACTIVE_CATALOG_PROMOTION_EXECUTION_REVIEW"
    else:
        status = "ACTIVE_CATALOG_PROMOTION_EXECUTION_PREFLIGHT_READY" if failures == 0 else "ACTIVE_CATALOG_PROMOTION_EXECUTION_PREFLIGHT_REVIEW"

    gate_rows = [
        {
            "gate": "dd057_readiness_ready",
            "expected": "ACTIVE_CATALOG_PROMOTION_READINESS_PLAN_READY",
            "observed": dd057_manifest.get("status", ""),
            "pass": int(dd057_ready),
        },
        {
            "gate": "required_staged_dbf_dtx_present",
            "expected": 0,
            "observed": len(missing_required),
            "pass": int(len(missing_required) == 0),
        },
        {
            "gate": "cdx_lmdb_artifacts_present",
            "expected": 0,
            "observed": len(missing_cdx_lmdb),
            "pass": int(len(missing_cdx_lmdb) == 0),
        },
        {
            "gate": "backup_created_when_executing",
            "expected": int(args.execute_promotion),
            "observed": int(bool(backup_rows)),
            "pass": int((not args.execute_promotion) or bool(backup_rows)),
        },
        {
            "gate": "promotion_copy_executed_when_requested",
            "expected": int(args.execute_promotion),
            "observed": int(bool(promotion_rows)),
            "pass": int((not args.execute_promotion) or bool(promotion_rows)),
        },
        {
            "gate": "post_verify_pass_when_requested",
            "expected": int(args.post_verify),
            "observed": int(bool(verify_rows) and all(int(r.get("row_count_match", 0)) == 1 for r in verify_rows)),
            "pass": int((not args.post_verify) or (bool(verify_rows) and all(int(r.get("row_count_match", 0)) == 1 for r in verify_rows))),
        },
    ]

    boundary_rows = [
        {"boundary": "active_catalog_mutation_authorized_by_dd058", "observed": int(args.execute_promotion), "required": int(args.execute_promotion), "pass": 1},
        {"boundary": "backup_created_before_promotion", "observed": int(bool(backup_rows)), "required": int(args.execute_promotion), "pass": int((not args.execute_promotion) or bool(backup_rows))},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd058_staged_required_artifacts.csv", staged_rows, ["table", "kind", "required", "path", "exists", "bytes", "sha256"])
    write_csv(out / "dd058_cdx_lmdb_artifacts.csv", index_rows, ["table", "kind", "path", "exists", "bytes", "sha256", "file_count"])
    write_csv(out / "dd058_active_before_inventory.csv", active_before_rows, ["table", "kind", "path", "exists", "bytes", "sha256", "file_count"])
    write_csv(out / "dd058_backup_ledger.csv", backup_rows, ["artifact_group", "source", "backup", "files", "bytes", "sha256", "status"])
    write_csv(out / "dd058_promotion_copy_ledger.csv", promotion_rows, ["table", "kind", "source", "destination", "required", "source_exists", "destination_exists", "destination_bytes", "destination_sha256", "action"])
    write_csv(out / "dd058_active_after_inventory.csv", active_after_rows, ["table", "kind", "path", "exists", "bytes", "sha256", "file_count"])
    write_csv(out / "dd058_post_promotion_pydottalk_readback.csv", verify_rows, ["table", "expected_rows", "import_ok", "open_ok", "rec_count", "row_count_match", "field_count", "memo_path", "memo_kind", "error", "build_python_exists"])
    write_csv(out / "dd058_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd058_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd058_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    runtime_script = build_runtime_verify_script()
    (out / "dd058_post_promotion_runtime_verify.dts").write_text(runtime_script, encoding="utf-8")

    manifest = {
        "contract": "dd058_controlled_active_catalog_promotion_execution_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "staged_path": str(staged_path),
        "active_path": str(active_path),
        "index_path": str(index_path),
        "lmdb_path": str(lmdb_path),
        "backup_root": str(backup_root),
        "backup_dir": str(backup_dir) if backup_rows else "",
        "restore_script": restore_script,
        "dd057_status": dd057_manifest.get("status", ""),
        "execute_promotion": int(args.execute_promotion),
        "post_verify": int(args.post_verify),
        "required_missing": len(missing_required),
        "cdx_lmdb_missing": len(missing_cdx_lmdb),
        "backup_rows": len(backup_rows),
        "promotion_rows": len(promotion_rows),
        "post_verify_rows": len(verify_rows),
        "failures": failures,
        "active_catalog_mutation": int(args.execute_promotion),
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Run DotTalk++ post-promotion runtime verify script, then DD-059 active catalog closure if green.",
    }
    write_json(out / "dd058_controlled_active_catalog_promotion_manifest.json", manifest)

    report = f"""# DD-058 Controlled Active Catalog Promotion Execution

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-058 is the first controlled package authorized to promote the staged Data
Dictionary catalog into the active metadata catalog.

## Inputs

- DD-057 status: `{dd057_manifest.get('status', '')}`
- Staged path: `{safe_rel(repo, staged_path)}`
- Active path: `{safe_rel(repo, active_path)}`
- Index path: `{safe_rel(repo, index_path)}`
- LMDB path: `{safe_rel(repo, lmdb_path)}`

## Execution

- Execute promotion requested: **{int(args.execute_promotion)}**
- Backup rows: **{len(backup_rows)}**
- Promotion copy rows: **{len(promotion_rows)}**
- Post-verify requested: **{int(args.post_verify)}**
- Failures: **{failures}**

## Backup

```text
{backup_dir if backup_rows else 'not created in this run'}
```

## Boundary

DD-058 does not edit source, mutate HELP/META/CMDHELPCHK, regenerate catalog
content, or perform manual row repair.

## Post-promotion runtime verification

A DotTalk++ verification script was emitted to:

```text
{safe_rel(repo, out / 'dd058_post_promotion_runtime_verify.dts')}
```
"""
    (out / "DD058_CONTROLLED_ACTIVE_CATALOG_PROMOTION_EXECUTION_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-058 controlled active catalog promotion manifest: {out / 'dd058_controlled_active_catalog_promotion_manifest.json'}")
    print(f"status: {status}; execute: {int(args.execute_promotion)}; post_verify: {int(args.post_verify)}; failures: {failures}; backup_rows: {len(backup_rows)}; promotion_rows: {len(promotion_rows)}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
