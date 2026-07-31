#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, List

REQUIRED = {
    "DD096YQ": ("docs/datadict/reports/DD096YQ-post-import-validation-readback-v0/dd096yq_post_import_validation_readback_manifest.json", "DD096YQ_POST_IMPORT_VALIDATION_GREEN"),
    "DD096Z": ("docs/datadict/reports/DD096Z-guarded-promotion-planning-v0/dd096z_guarded_promotion_planning_manifest.json", "DD096Z_PROMOTION_PLAN_READY"),
    "DD096ZA": ("docs/datadict/reports/DD096ZA-guarded-apply-package-design-v0/dd096za_guarded_apply_package_design_manifest.json", "DD096ZA_GUARDED_APPLY_PACKAGE_DESIGN_READY"),
}

X64_TABLES = [
    "DATA_DICTIONARY_OBJECTS",
    "DATA_DICTIONARY_OBJECT_ATTRIBUTES",
    "DATA_DICTIONARY_RELATION_EDGES",
    "DATA_DICTIONARY_EVIDENCE_RECORDS",
    "DATA_DICTIONARY_GATE_RECORDS",
    "DATA_DICTIONARY_RUNS",
]

ACTIVE_FAMILIES = [
    ("active_dbf_root", "dottalkpp/data/datadict"),
    ("active_index_root", "dottalkpp/data/indexes/datadict"),
    ("active_lmdb_root", "dottalkpp/data/lmdb/datadict"),
    ("workspace_schema", "dottalkpp/data/workspaces/ddbase.dtschema"),
]

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def safe_run_id(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in s)

def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def wt(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def wj(path: Path, obj):
    wt(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def wc(path: Path, rows: List[Dict], fields: List[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def iter_tree_files(root: Path):
    if root.is_file():
        yield root
    elif root.is_dir():
        for p in sorted(root.rglob("*")):
            if p.is_file():
                yield p

def copy_tree_or_file(src: Path, dst: Path) -> List[Dict]:
    rows = []
    if not src.exists():
        rows.append({"src": str(src), "dst": str(dst), "kind": "missing", "bytes": 0, "sha256": "", "copied": 0})
        return rows
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        rows.append({"src": str(src), "dst": str(dst), "kind": "file", "bytes": dst.stat().st_size, "sha256": sha256_file(dst), "copied": 1})
        return rows
    dst.mkdir(parents=True, exist_ok=True)
    for f in iter_tree_files(src):
        rel = f.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        rows.append({"src": str(f), "dst": str(target), "kind": "file", "bytes": target.stat().st_size, "sha256": sha256_file(target), "copied": 1})
    return rows

def candidate_sidecar_candidates(src_root: Path, table: str) -> List[Path]:
    # Collect DBF + likely memo/x64 sidecars. Do not collect CDX/LMDB here; that is later.
    lower = table.lower()
    upper = table.upper()
    candidates: List[Path] = []
    if not src_root.exists():
        return candidates
    for p in sorted(src_root.iterdir()):
        if not p.is_file():
            continue
        stem = p.stem.upper()
        name = p.name.upper()
        if stem == upper or name.startswith(upper + "."):
            candidates.append(p)
            continue
        # tolerate lower/mixed-case sidecars
        if p.stem.lower() == lower or p.name.lower().startswith(lower + "."):
            candidates.append(p)
    return candidates

def main():
    ap = argparse.ArgumentParser(description="DD096Z-B backup and inactive candidate-root staging")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZB-backup-and-inactive-candidate-staging-v0")
    ap.add_argument("--execute-staging", action="store_true")
    ap.add_argument("--backup-root", default="")
    ap.add_argument("--candidate-root", default="")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_backup_candidate_staging"
    gen.mkdir(parents=True, exist_ok=True)

    rid = safe_run_id(args.run_id)
    backup_root = Path(args.backup_root).resolve() if args.backup_root else repo / "docs/datadict/backups" / rid
    candidate_root = Path(args.candidate_root).resolve() if args.candidate_root else repo / "docs/datadict/candidates" / rid

    pre = []
    blockers = 0
    for lane, (rel, expected) in REQUIRED.items():
        path = repo / rel
        data = read_json(path)
        observed = data.get("status", "MISSING")
        passed = int(bool(data) and observed == expected)
        blockers += 0 if passed else 1
        pre.append({
            "lane": lane,
            "manifest_path": str(path),
            "observed_status": observed,
            "expected_status": expected,
            "pass": passed,
        })
    wc(gen / "dd096zb_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    backup_plan = []
    for family, rel in ACTIVE_FAMILIES:
        src = repo / rel
        dst = backup_root / rel
        exists = int(src.exists())
        kind = "dir" if src.is_dir() else "file" if src.is_file() else "missing"
        file_count = sum(1 for _ in iter_tree_files(src)) if src.exists() else 0
        backup_plan.append({
            "family": family,
            "src": str(src),
            "backup_dst": str(dst),
            "src_exists": exists,
            "src_kind": kind,
            "src_file_count": file_count,
            "execute_staging": int(args.execute_staging),
        })
    wc(gen / "dd096zb_backup_plan.csv", backup_plan, ["family","src","backup_dst","src_exists","src_kind","src_file_count","execute_staging"])

    sandbox_dbf = repo / "dottalkpp/data/dbf/sandbox"
    candidate_dbf = candidate_root / "dbf"
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"
    candidate_workspace = candidate_root / "workspaces"

    table_plan = []
    missing_tables = 0
    for table in X64_TABLES:
        files = candidate_sidecar_candidates(sandbox_dbf, table)
        dbf_exists = int((sandbox_dbf / f"{table}.dbf").exists() or (sandbox_dbf / f"{table}.DBF").exists())
        if not dbf_exists:
            missing_tables += 1
        table_plan.append({
            "table": table,
            "sandbox_root": str(sandbox_dbf),
            "candidate_dbf_root": str(candidate_dbf),
            "dbf_exists": dbf_exists,
            "sidecar_file_count": len(files),
            "files": ";".join(str(p.name) for p in files),
        })
    wc(gen / "dd096zb_candidate_table_staging_plan.csv", table_plan, ["table","sandbox_root","candidate_dbf_root","dbf_exists","sidecar_file_count","files"])

    backup_copy_rows = []
    candidate_copy_rows = []
    dirs_created = []
    executed = int(args.execute_staging and blockers == 0 and missing_tables == 0)

    if args.execute_staging and blockers == 0 and missing_tables == 0:
        for p in [backup_root, candidate_dbf, candidate_index, candidate_lmdb, candidate_workspace]:
            p.mkdir(parents=True, exist_ok=True)
            dirs_created.append({"path": str(p), "created_or_exists": 1})

        for family, rel in ACTIVE_FAMILIES:
            src = repo / rel
            dst = backup_root / rel
            backup_copy_rows.extend(copy_tree_or_file(src, dst))

        # Stage x64 proof DBFs/memo/metadata sidecars only.
        for table in X64_TABLES:
            for src in candidate_sidecar_candidates(sandbox_dbf, table):
                dst = candidate_dbf / src.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                candidate_copy_rows.append({
                    "table": table,
                    "src": str(src),
                    "dst": str(dst),
                    "bytes": dst.stat().st_size,
                    "sha256": sha256_file(dst),
                    "copied": 1,
                })

        # Write a candidate README so the staging root is self-describing.
        wt(candidate_root / "README_DD096ZB_CANDIDATE_ROOT.md",
           f"# DD096Z-B inactive candidate root\n\nRun id: `{args.run_id}`\nCreated UTC: `{now()}`\n\nThis is an inactive candidate Data Dictionary root. It is not the active catalog.\n")
    else:
        reason = []
        if not args.execute_staging:
            reason.append("execute_staging_not_requested")
        if blockers:
            reason.append("precondition_blockers")
        if missing_tables:
            reason.append("missing_sandbox_tables")
        dirs_created.append({"path": str(candidate_root), "created_or_exists": 0, "reason": ",".join(reason)})

    wc(gen / "dd096zb_dirs_created.csv", dirs_created, ["path","created_or_exists","reason"])
    wc(gen / "dd096zb_backup_copy_ledger.csv", backup_copy_rows, ["src","dst","kind","bytes","sha256","copied"])
    wc(gen / "dd096zb_candidate_copy_ledger.csv", candidate_copy_rows, ["table","src","dst","bytes","sha256","copied"])

    validation_plan = [
        ("candidate_root_exists", str(candidate_root), "required_after_execute"),
        ("candidate_dbf_root_exists", str(candidate_dbf), "required_after_execute"),
        ("candidate_tables_present", "six DATA_DICTIONARY_*.dbf plus sidecars", "required_after_execute"),
        ("active_catalog_unchanged", "dottalkpp/data/datadict untouched by this package", "required"),
        ("candidate_readback_runtime", "future DD096Z-C", "next_lane"),
        ("candidate_cdx_lmdb_rebuild", "future DD096Z-D", "next_lane"),
        ("candidate_ddict_smoke", "future DD096Z-E", "next_lane"),
    ]
    wc(gen / "dd096zb_candidate_validation_plan.csv",
       [{"check": a, "target": b, "status": c} for a,b,c in validation_plan],
       ["check","target","status"])

    boundary = [
        ("backup_and_inactive_candidate_staging", executed, int(args.execute_staging), 1),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("candidate_root_write", executed, int(args.execute_staging), 1),
        ("backup_root_write", executed, int(args.execute_staging), 1),
        ("source_edits", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zb_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    gate_rows = [
        {"gate": "preconditions_green", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "sandbox_x64_tables_present", "expected": 0, "observed": missing_tables, "pass": int(missing_tables == 0)},
        {"gate": "execute_staging_requested", "expected": "operator_choice", "observed": int(args.execute_staging), "pass": 1},
        {"gate": "active_replacement_performed", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    wc(out / "dd096zb_gate_ledger.csv", gate_rows, ["gate","expected","observed","pass"])

    if failures:
        status = "DD096ZB_BACKUP_CANDIDATE_STAGING_REVIEW"
    elif executed:
        status = "DD096ZB_BACKUP_CANDIDATE_STAGING_EXECUTED"
    else:
        status = "DD096ZB_BACKUP_CANDIDATE_STAGING_READY"

    report = f"""# DD096Z-B Backup and Inactive Candidate-Root Staging

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-B backs up active Data Dictionary roots and stages the x64 proof tables into an inactive candidate root.

It does **not** replace the active Data Dictionary catalog.

## Summary

- Precondition blockers: **{blockers}**
- Missing sandbox proof tables: **{missing_tables}**
- Execute staging requested: **{int(args.execute_staging)}**
- Staging executed: **{executed}**
- Active catalog replacement: **0**
- Active catalog DBF copy/write: **0**
- Active CDX/LMDB rebuild: **0**

## Roots

- Backup root: `{backup_root}`
- Candidate root: `{candidate_root}`
- Candidate DBF root: `{candidate_dbf}`

## Next lane

DD096Z-C should validate candidate-root readback. CDX/LMDB rebuild and DDICT candidate smoke remain separate later gates.
"""
    wt(out / "DD096ZB_BACKUP_AND_INACTIVE_CANDIDATE_STAGING_REPORT.md", report)

    manifest = {
        "contract": "dd096zb_backup_and_inactive_candidate_staging_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "missing_sandbox_tables": missing_tables,
        "execute_staging_requested": int(args.execute_staging),
        "staging_executed": executed,
        "backup_root": str(backup_root),
        "candidate_root": str(candidate_root),
        "candidate_dbf_root": str(candidate_dbf),
        "active_catalog_replacement": 0,
        "active_catalog_dbf_copy_or_write": 0,
        "active_cdx_lmdb_rebuild": 0,
        "failures": failures,
        "next_recommended_action": "DD096Z-C candidate-root readback validation; no active replacement yet.",
    }
    wj(out / "dd096zb_backup_and_inactive_candidate_staging_manifest.json", manifest)

    print(f"DD096Z-B backup/candidate staging manifest: {out / 'dd096zb_backup_and_inactive_candidate_staging_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; missing_sandbox_tables: {missing_tables}; staging_executed: {executed}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
