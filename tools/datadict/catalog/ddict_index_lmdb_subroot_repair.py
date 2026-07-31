#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple


TARGET_SOURCE = "src/datadict/ddict_catalog_paths.cpp"

EXPECTED_DD_TABLES = [
    "DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE",
    "DDEVID", "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE",
]

EXPECTED_CDX = [
    "ddrun.cdx", "ddbase.cdx", "ddsource.cdx", "ddobject.cdx", "ddattr.cdx",
    "ddedge.cdx", "ddevid.cdx", "ddgate.cdx", "ddreview.cdx", "ddartif.cdx", "ddprofile.cdx",
]

EXPECTED_LMDB = [name + ".d" for name in EXPECTED_CDX]

PROTECTED_UNTOUCHED = [
    "src/cli/cmd_ddict.cpp",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
    "src/CMakeLists.txt",
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
]

SMOKE = """SETPATH
DO ddbase
DDICT STATUS
DDICT TABLES
DDICT TAGS DDATTR
DDICT TAGS DDOBJECT
DDICT REL DDOBJECT OUT
DDICT EVIDENCE DDOBJECT

"""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def diff_text(old: str, new: str, name: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=name + ".before",
        tofile=name + ".after",
        lineterm="",
    ))


def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def artifact_rows(repo: Path) -> Tuple[int, int, List[Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    cdx_root = repo / "dottalkpp/data/indexes/datadict"
    lmdb_root = repo / "dottalkpp/data/lmdb/datadict"

    cdx_count = 0
    for name in EXPECTED_CDX:
        p = cdx_root / name
        exists = int(p.exists())
        cdx_count += exists
        rows.append({
            "artifact_group": "cdx",
            "root": rel(repo, cdx_root),
            "name": name,
            "exists": exists,
            "bytes_or_children": p.stat().st_size if p.exists() and p.is_file() else 0,
        })

    lmdb_count = 0
    for name in EXPECTED_LMDB:
        p = lmdb_root / name
        exists = int(p.exists())
        lmdb_count += exists
        rows.append({
            "artifact_group": "lmdb",
            "root": rel(repo, lmdb_root),
            "name": name,
            "exists": exists,
            "bytes_or_children": sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else 0,
        })
    return cdx_count, lmdb_count, rows


def dbf_table_count(repo: Path) -> int:
    root = repo / "dottalkpp/data/datadict"
    return sum(1 for t in EXPECTED_DD_TABLES if (root / f"{t}.dbf").exists())


def source_context_rows(text: str) -> List[Dict[str, Any]]:
    rows = []
    lines = text.splitlines()
    terms = ["find_cdx_file", "find_lmdb_dir", "indexes", "lmdb", "datadict"]
    for i, line in enumerate(lines, start=1):
        lower = line.lower()
        hit = [t for t in terms if t in lower]
        if not hit:
            continue
        start = max(1, i - 2)
        end = min(len(lines), i + 2)
        snippet = "\\n".join(f"{j}: {lines[j-1]}" for j in range(start, end + 1))
        rows.append({"start_line": start, "end_line": end, "terms": ";".join(hit), "snippet": snippet})
    return rows


def patch_source(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    out = text
    rows: List[Dict[str, Any]] = []

    idx_needles = [
        'root / "data" / "indexes" / (lower + ".cdx"),',
        'root / "data" / "indexes" / (upper + ".cdx"),',
        'root / "dottalkpp" / "data" / "indexes" / (lower + ".cdx"),',
        'root / "dottalkpp" / "data" / "indexes" / (upper + ".cdx"),',
    ]

    idx_insert = [
        '            root / "data" / "indexes" / "datadict" / (lower + ".cdx"),',
        '            root / "data" / "indexes" / "datadict" / (upper + ".cdx"),',
        '            root / "dottalkpp" / "data" / "indexes" / "datadict" / (lower + ".cdx"),',
        '            root / "dottalkpp" / "data" / "indexes" / "datadict" / (upper + ".cdx"),',
    ]

    if '"indexes" / "datadict"' in out:
        rows.append({"patch_part": "cdx_subroot_candidates", "safe": 1, "reason": "already contains indexes/datadict candidates"})
    elif all(n in out for n in idx_needles):
        first = idx_needles[0]
        out = out.replace(first, "\n".join(idx_insert) + "\n" + first, 1)
        rows.append({"patch_part": "cdx_subroot_candidates", "safe": 1, "reason": "inserted indexes/datadict candidates before legacy flat candidates"})
    else:
        rows.append({"patch_part": "cdx_subroot_candidates", "safe": 0, "reason": "expected flat CDX candidate block not found"})

    lmdb_needles = [
        'root / "data" / "lmdb" / (lower + ".cdx.d"),',
        'root / "data" / "lmdb" / (upper + ".cdx.d"),',
        'root / "dottalkpp" / "data" / "lmdb" / (lower + ".cdx.d"),',
        'root / "dottalkpp" / "data" / "lmdb" / (upper + ".cdx.d"),',
    ]

    lmdb_insert = [
        '            root / "data" / "lmdb" / "datadict" / (lower + ".cdx.d"),',
        '            root / "data" / "lmdb" / "datadict" / (upper + ".cdx.d"),',
        '            root / "dottalkpp" / "data" / "lmdb" / "datadict" / (lower + ".cdx.d"),',
        '            root / "dottalkpp" / "data" / "lmdb" / "datadict" / (upper + ".cdx.d"),',
    ]

    if '"lmdb" / "datadict"' in out:
        rows.append({"patch_part": "lmdb_subroot_candidates", "safe": 1, "reason": "already contains lmdb/datadict candidates"})
    elif all(n in out for n in lmdb_needles):
        first = lmdb_needles[0]
        out = out.replace(first, "\n".join(lmdb_insert) + "\n" + first, 1)
        rows.append({"patch_part": "lmdb_subroot_candidates", "safe": 1, "reason": "inserted lmdb/datadict candidates before legacy flat candidates"})
    else:
        rows.append({"patch_part": "lmdb_subroot_candidates", "safe": 0, "reason": "expected flat LMDB candidate block not found"})

    return out, rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-093B DDICT index/LMDB subroot resolver repair")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD093B-ddict-index-lmdb-subroot-repair-v1")
    ap.add_argument("--apply-source-patch", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    target = repo / TARGET_SOURCE
    before = read_text(target)
    candidate, patch_rows = patch_source(before)
    changed = int(candidate != before)
    safe_patch = int(all(int(r["safe"]) == 1 for r in patch_rows) and changed)

    generated = out / "generated_index_lmdb_subroot_repair"
    candidate_path = generated / TARGET_SOURCE
    diff_path = generated / (TARGET_SOURCE + ".diff")
    smoke_path = generated / "dd093b_ddict_index_lmdb_subroot_smoke.dts"
    write_text(candidate_path, candidate)
    write_text(diff_path, diff_text(before, candidate, TARGET_SOURCE))
    write_text(smoke_path, SMOKE)

    cdx_count, lmdb_count, art_rows = artifact_rows(repo)
    dbf_count = dbf_table_count(repo)
    ctx_rows = source_context_rows(before)

    review_rows: List[Dict[str, Any]] = []
    if not target.exists():
        review_rows.append({"issue": "TARGET_SOURCE_MISSING", "detail": TARGET_SOURCE})
    if dbf_count != 11:
        review_rows.append({"issue": "DATADICT_DBF_TABLE_COUNT_NOT_11", "detail": str(dbf_count)})
    if cdx_count == 0:
        review_rows.append({"issue": "NO_CDX_FILES_IN_INDEXES_DATADICT", "detail": "dottalkpp/data/indexes/datadict"})
    if lmdb_count == 0:
        review_rows.append({"issue": "NO_LMDB_MIRRORS_IN_LMDB_DATADICT", "detail": "dottalkpp/data/lmdb/datadict"})
    if not safe_patch:
        review_rows.append({"issue": "SAFE_PATCH_NOT_AVAILABLE", "detail": "; ".join(f"{r['patch_part']}={r['reason']}" for r in patch_rows)})

    applied = 0
    backup_path = ""
    if args.apply_source_patch and safe_patch and target.exists():
        backup_dir = (repo / args.backup_root) / f"{args.run_id}_{stamp()}"
        backup = backup_dir / TARGET_SOURCE
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        backup_path = str(backup)
        target.write_text(candidate, encoding="utf-8")
        applied = 1

    protected_rows = []
    for rp in PROTECTED_UNTOUCHED:
        p = repo / rp
        protected_rows.append({
            "protected_path": rp,
            "exists": int(p.exists()),
            "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
            "sha256": sha256(p),
            "mutation_in_dd093b": 0,
        })

    gate_rows = [
        {"gate": "target_source_exists", "expected": 1, "observed": int(target.exists()), "pass": int(target.exists())},
        {"gate": "datadict_dbf_tables_present", "expected": 11, "observed": dbf_count, "pass": int(dbf_count == 11)},
        {"gate": "cdx_artifacts_present_in_subroot", "expected": ">=1", "observed": cdx_count, "pass": int(cdx_count >= 1)},
        {"gate": "lmdb_mirrors_present_in_subroot", "expected": ">=1", "observed": lmdb_count, "pass": int(lmdb_count >= 1)},
        {"gate": "safe_patch_available", "expected": 1, "observed": safe_patch, "pass": safe_patch},
        {"gate": "candidate_diff_generated", "expected": 1, "observed": int(diff_path.exists()), "pass": int(diff_path.exists())},
        {"gate": "apply_when_requested", "expected": int(args.apply_source_patch), "observed": applied, "pass": int((not args.apply_source_patch) or applied == 1)},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    if args.apply_source_patch and failures == 0:
        status = "DDICT_INDEX_LMDB_SUBROOT_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"
    elif failures == 0:
        status = "DDICT_INDEX_LMDB_SUBROOT_SOURCE_PATCH_READY"
    else:
        status = "DDICT_INDEX_LMDB_SUBROOT_SOURCE_PATCH_REVIEW"

    boundary_rows = [
        {"boundary": "guarded_index_lmdb_subroot_repair", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "target_source_modified", "observed": applied, "required": int(args.apply_source_patch), "pass": int((not args.apply_source_patch) or applied == 1)},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    next_rows = [
        {"next_id": "BUILD", "title": "Build dottalkpp after DD093B source patch", "allowed_scope": "cmake --build build --config Release --target dottalkpp"},
        {"next_id": "DD093C", "title": "DDICT full path remap runtime closure", "allowed_scope": "prove DBF, CDX, LMDB all use datadict subroots"},
        {"next_id": "ARTIFACT_PLACEMENT", "title": "Complete missing CDX/LMDB file placement if artifact counts are low", "allowed_scope": "move/copy existing artifacts only; no rebuild unless separately authorized"},
    ]

    write_csv(out / "dd093b_artifact_presence.csv", art_rows, ["artifact_group", "root", "name", "exists", "bytes_or_children"])
    write_csv(out / "dd093b_source_contexts.csv", ctx_rows, ["start_line", "end_line", "terms", "snippet"])
    write_csv(out / "dd093b_patch_part_ledger.csv", patch_rows, ["patch_part", "safe", "reason"])
    write_csv(out / "dd093b_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd093b_protected_file_ledger.csv", protected_rows, ["protected_path", "exists", "kind", "sha256", "mutation_in_dd093b"])
    write_csv(out / "dd093b_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd093b_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd093b_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-093B DDICT Index/LMDB Subroot Resolver Repair

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-093B repairs DDICT artifact discovery after the Data Dictionary catalog moved to first-class subroots:

```text
dottalkpp/data/datadict
dottalkpp/data/indexes/datadict
dottalkpp/data/lmdb/datadict
```

DD093R proved the DBF catalog root is now found. The remaining issue is that `DDICT TAGS` still reports `CDX artifact: NO` and `LMDB mirror: NO` even after BUILDLMDB writes to the new subroots.

## Findings

- DBF catalog tables present: **{dbf_count} / 11**
- CDX artifacts in `indexes/datadict`: **{cdx_count} / 11**
- LMDB mirrors in `lmdb/datadict`: **{lmdb_count} / 11**
- Safe patch available: **{safe_patch}**
- Apply requested: **{int(args.apply_source_patch)}**
- Applied: **{applied}**

## Candidate repair

- Target: `{TARGET_SOURCE}`
- Candidate file: `{candidate_path}`
- Diff file: `{diff_path}`
- Runtime smoke file: `{smoke_path}`

The candidate inserts `indexes/datadict` and `lmdb/datadict` artifact candidates before legacy flat artifact candidates.

## Boundary

DD-093B may patch only `{TARGET_SOURCE}` when `--apply-source-patch` is supplied. It does not edit build files,
command registration, active catalog DBFs, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB,
mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    write_text(out / "DD093B_DDICT_INDEX_LMDB_SUBROOT_REPAIR_REPORT.md", report)

    manifest = {
        "contract": "dd093b_ddict_index_lmdb_subroot_repair_v1",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "target_source": TARGET_SOURCE,
        "dbf_tables_present": dbf_count,
        "cdx_artifacts_present": cdx_count,
        "lmdb_mirrors_present": lmdb_count,
        "safe_patch_available": safe_patch,
        "changed_candidate": changed,
        "apply_source_patch": int(args.apply_source_patch),
        "applied": applied,
        "backup_path": backup_path,
        "failures": failures,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Build dottalkpp and run DD093C full path remap runtime closure.",
    }
    write_json(out / "dd093b_ddict_index_lmdb_subroot_repair_manifest.json", manifest)

    print(f"DD-093B DDICT index/LMDB subroot repair manifest: {out / 'dd093b_ddict_index_lmdb_subroot_repair_manifest.json'}")
    print(f"status: {status}; dbf: {dbf_count}/11; cdx: {cdx_count}/11; lmdb: {lmdb_count}/11; safe_patch: {safe_patch}; applied: {applied}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
