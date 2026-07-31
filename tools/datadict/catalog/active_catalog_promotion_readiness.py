#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
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


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


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


def inventory_staged_tables(repo: Path, staged_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for table in TABLES:
        stem = table.lower()
        dbf = staged_path / f"{stem}.dbf"
        dtx = staged_path / f"{stem}.dtx"
        rows.append({
            "table": table,
            "artifact_kind": "DBF",
            "required": 1,
            "source_path": safe_rel(repo, dbf),
            "exists": int(dbf.exists()),
            "bytes": dbf.stat().st_size if dbf.exists() else "",
            "sha256": sha256_file(dbf) if dbf.exists() else "",
            "active_destination": f"dottalkpp/data/metadata/datadict/{stem}.dbf",
        })
        rows.append({
            "table": table,
            "artifact_kind": "DTX",
            "required": int(table in MEMO_TABLES),
            "source_path": safe_rel(repo, dtx),
            "exists": int(dtx.exists()),
            "bytes": dtx.stat().st_size if dtx.exists() else "",
            "sha256": sha256_file(dtx) if dtx.exists() else "",
            "active_destination": f"dottalkpp/data/metadata/datadict/{stem}.dtx",
        })
    return rows


def find_related_cdx(repo: Path, index_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    table_stems = {t.lower() for t in TABLES}
    if not index_path.exists():
        return rows
    for p in sorted(index_path.rglob("*.cdx"), key=lambda q: q.as_posix().lower()):
        stem = p.stem.lower()
        related = int(stem in table_stems)
        if related:
            rows.append({
                "table": stem.upper(),
                "artifact_kind": "CDX",
                "required": 1,
                "source_path": safe_rel(repo, p),
                "exists": 1,
                "bytes": p.stat().st_size,
                "sha256": sha256_file(p),
                "active_destination": f"dottalkpp/data/indexes/{p.name}",
            })
    return rows


def find_related_lmdb(repo: Path, lmdb_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    table_stems = {t.lower() for t in TABLES}
    if not lmdb_path.exists():
        return rows
    for p in sorted(lmdb_path.iterdir(), key=lambda q: q.name.lower()):
        if not p.is_dir():
            continue
        name = p.name.lower()
        table = ""
        # Typical env names may include table/tag or table.cdx.d.
        for stem in table_stems:
            if name == f"{stem}.cdx.d" or name.startswith(f"{stem}.") or name.startswith(f"{stem}_"):
                table = stem.upper()
                break
        if not table:
            continue
        files, bytes_total, digest = dir_summary(p)
        rows.append({
            "table": table,
            "artifact_kind": "LMDB",
            "required": 1,
            "source_path": safe_rel(repo, p),
            "exists": 1,
            "bytes": bytes_total,
            "sha256": digest,
            "active_destination": f"dottalkpp/data/lmdb/{p.name}",
            "file_count": files,
        })
    return rows


def load_row_count_status(dd053_dir: Path) -> Dict[str, Dict[str, Any]]:
    rows = read_csv_dict(dd053_dir / "dd053_table_readback_ledger.csv")
    out: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        table = (r.get("table") or "").strip().upper()
        if not table:
            continue
        out[table] = {
            "expected_rows": r.get("expected_rows", ""),
            "pydottalk_rows": r.get("pydottalk_rows", ""),
            "row_count_match": r.get("row_count_match", ""),
            "descriptor_status": r.get("descriptor_status", ""),
            "memo_sidecar_ok": r.get("memo_sidecar_ok", ""),
            "table_pass": r.get("table_pass", ""),
        }
    return out


def active_inventory(repo: Path, active_path: Path, index_path: Path, lmdb_path: Path) -> List[Dict[str, Any]]:
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
                    "artifact_kind": kind,
                    "path": safe_rel(repo, path),
                    "exists": 1,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                })
            elif path.is_dir():
                files, total, digest = dir_summary(path)
                rows.append({
                    "table": table,
                    "artifact_kind": kind,
                    "path": safe_rel(repo, path),
                    "exists": 1,
                    "bytes": total,
                    "sha256": digest,
                    "file_count": files,
                })
            else:
                rows.append({
                    "table": table,
                    "artifact_kind": kind,
                    "path": safe_rel(repo, path),
                    "exists": 0,
                    "bytes": "",
                    "sha256": "",
                })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-057 report-only active Data Dictionary catalog promotion readiness plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD057-active-catalog-promotion-readiness-v0")
    ap.add_argument("--staged-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--index-path", default="dottalkpp/data/indexes")
    ap.add_argument("--lmdb-path", default="dottalkpp/data/lmdb")
    ap.add_argument("--backup-root", default="dottalkpp/data/metadata/datadict_promotion_backups")
    ap.add_argument("--dd052-verify-dir", default="docs/datadict/reports/DD052-canonical-catalog-staging-verify-v0")
    ap.add_argument("--dd053-dir", default="docs/datadict/reports/DD053-canonical-catalog-runtime-readback-v0")
    ap.add_argument("--dd056r-dir", default="docs/datadict/reports/DD056R-canonical-cdx-buildlmdb-verify-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    staged_path = (repo / args.staged_path).resolve()
    active_path = (repo / args.active_path).resolve()
    index_path = (repo / args.index_path).resolve()
    lmdb_path = (repo / args.lmdb_path).resolve()
    backup_root = (repo / args.backup_root).resolve()
    dd052_verify_dir = (repo / args.dd052_verify_dir).resolve()
    dd053_dir = (repo / args.dd053_dir).resolve()
    dd056r_dir = (repo / args.dd056r_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    if staged_path.resolve() == active_path.resolve():
        raise SystemExit("Refusing readiness plan with staged path equal to active path")

    dd052_manifest = read_json(dd052_verify_dir / "dd052_canonical_catalog_staging_manifest.json")
    dd053_manifest = read_json(dd053_dir / "dd053_canonical_catalog_runtime_readback_manifest.json")
    dd056r_manifest = read_json(dd056r_dir / "dd056r_canonical_cdx_buildlmdb_execution_manifest.json")

    table_artifacts = inventory_staged_tables(repo, staged_path)
    cdx_artifacts = find_related_cdx(repo, index_path)
    lmdb_artifacts = find_related_lmdb(repo, lmdb_path)
    all_promotion_artifacts = table_artifacts + cdx_artifacts + lmdb_artifacts
    active_rows = active_inventory(repo, active_path, index_path, lmdb_path)
    row_status = load_row_count_status(dd053_dir)

    missing_required = [
        r for r in all_promotion_artifacts
        if int(r.get("required", 0)) == 1 and int(r.get("exists", 0)) != 1
    ]

    # Required cdx/lmdb coverage: each staged catalog table should have a related CDX and at least
    # enough LMDB evidence from DD-056R; exact per-tag env naming can vary, so report coverage separately.
    cdx_tables = {r["table"] for r in cdx_artifacts}
    lmdb_tables = {r["table"] for r in lmdb_artifacts}
    cdx_missing_tables = [t for t in TABLES if t not in cdx_tables]
    lmdb_missing_tables = [t for t in TABLES if t not in lmdb_tables]

    gate_rows = [
        {
            "gate": "dd052_staging_runtime_verify_green",
            "expected": "CANONICAL_CATALOG_STAGING_RUNTIME_VERIFY_GREEN",
            "observed": dd052_manifest.get("status", ""),
            "pass": int(dd052_manifest.get("status") == "CANONICAL_CATALOG_STAGING_RUNTIME_VERIFY_GREEN"),
        },
        {
            "gate": "dd053_runtime_readback_green",
            "expected": "CANONICAL_CATALOG_RUNTIME_READBACK_GREEN",
            "observed": dd053_manifest.get("status", ""),
            "pass": int(dd053_manifest.get("status") == "CANONICAL_CATALOG_RUNTIME_READBACK_GREEN"),
        },
        {
            "gate": "dd056r_cdx_buildlmdb_green",
            "expected": "CANONICAL_CDX_BUILDLMDB_STAGING_VERIFY_GREEN",
            "observed": dd056r_manifest.get("status", ""),
            "pass": int(dd056r_manifest.get("status") == "CANONICAL_CDX_BUILDLMDB_STAGING_VERIFY_GREEN"),
        },
        {
            "gate": "required_dbf_dtx_artifacts_present",
            "expected": 0,
            "observed": len(missing_required),
            "pass": int(len(missing_required) == 0),
        },
        {
            "gate": "cdx_tables_covered",
            "expected": len(TABLES),
            "observed": len(cdx_tables),
            "pass": int(len(cdx_missing_tables) == 0),
        },
        {
            "gate": "lmdb_artifacts_present",
            "expected": ">=1 and DD056R green",
            "observed": dd056r_manifest.get("lmdb_envs", 0),
            "pass": int(int(dd056r_manifest.get("lmdb_envs", 0) or 0) >= 1),
        },
        {
            "gate": "backup_root_planned",
            "expected": "path planned but not created by DD057",
            "observed": str(backup_root),
            "pass": 1,
        },
        {
            "gate": "promotion_execution_authorized",
            "expected": 0,
            "observed": 0,
            "pass": 1,
        },
    ]

    failures = sum(1 for r in gate_rows if int(r.get("pass", 0)) != 1)
    status = "ACTIVE_CATALOG_PROMOTION_READINESS_PLAN_READY" if failures == 0 else "ACTIVE_CATALOG_PROMOTION_READINESS_PLAN_REVIEW"

    promotion_rows: List[Dict[str, Any]] = []
    for r in all_promotion_artifacts:
        promotion_rows.append({
            "table": r.get("table", ""),
            "artifact_kind": r.get("artifact_kind", ""),
            "source_path": r.get("source_path", ""),
            "exists": r.get("exists", ""),
            "required": r.get("required", ""),
            "bytes": r.get("bytes", ""),
            "sha256": r.get("sha256", ""),
            "proposed_active_destination": r.get("active_destination", ""),
            "promotion_action": "PLAN_COPY_OR_REPLACE_IN_DD058",
        })

    row_status_rows: List[Dict[str, Any]] = []
    for table in TABLES:
        rs = row_status.get(table, {})
        row_status_rows.append({
            "table": table,
            "expected_rows": rs.get("expected_rows", EXPECTED_COUNTS[table]),
            "pydottalk_rows": rs.get("pydottalk_rows", ""),
            "row_count_match": rs.get("row_count_match", ""),
            "descriptor_status": rs.get("descriptor_status", ""),
            "memo_sidecar_ok": rs.get("memo_sidecar_ok", ""),
            "table_pass": rs.get("table_pass", ""),
        })

    review_rows: List[Dict[str, Any]] = []
    for t in cdx_missing_tables:
        review_rows.append({"issue": "MISSING_CDX_TABLE_COVERAGE", "table": t, "detail": "No related <table>.cdx found in index path"})
    for t in lmdb_missing_tables:
        # Informational because DD056R reported total LMDB env count and exact naming may differ.
        review_rows.append({"issue": "LMDB_TABLE_COVERAGE_REVIEW", "table": t, "detail": "No simple <table>.cdx.d env found; confirm from DD056R artifact ledger/naming"})
    for r in missing_required:
        review_rows.append({"issue": "MISSING_REQUIRED_ARTIFACT", "table": r.get("table", ""), "detail": r.get("source_path", "")})

    rollback_rows = [
        {
            "step": 1,
            "action": "CREATE_TIMESTAMPED_BACKUP_ROOT",
            "path": f"{safe_rel(repo, backup_root)}/<timestamp>",
            "executed_by_dd057": 0,
        },
        {
            "step": 2,
            "action": "COPY_EXISTING_ACTIVE_METADATA_DATADICT",
            "path": safe_rel(repo, active_path),
            "executed_by_dd057": 0,
        },
        {
            "step": 3,
            "action": "COPY_EXISTING_RELATED_CDX_FILES",
            "path": safe_rel(repo, index_path),
            "executed_by_dd057": 0,
        },
        {
            "step": 4,
            "action": "COPY_EXISTING_RELATED_LMDB_ENVS",
            "path": safe_rel(repo, lmdb_path),
            "executed_by_dd057": 0,
        },
        {
            "step": 5,
            "action": "WRITE_RESTORE_SCRIPT_AND_HASH_LEDGER",
            "path": f"{safe_rel(repo, backup_root)}/<timestamp>",
            "executed_by_dd057": 0,
        },
    ]

    boundary_rows = [
        {"boundary": "report_only_readiness_plan", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "staged_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "promotion_executed", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd057_promotion_artifact_manifest.csv", promotion_rows, [
        "table", "artifact_kind", "source_path", "exists", "required", "bytes", "sha256",
        "proposed_active_destination", "promotion_action",
    ])
    write_csv(out / "dd057_active_catalog_current_inventory.csv", active_rows, [
        "table", "artifact_kind", "path", "exists", "bytes", "sha256", "file_count",
    ])
    write_csv(out / "dd057_staged_catalog_row_status.csv", row_status_rows, [
        "table", "expected_rows", "pydottalk_rows", "row_count_match",
        "descriptor_status", "memo_sidecar_ok", "table_pass",
    ])
    write_csv(out / "dd057_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd057_review_rows.csv", review_rows, ["issue", "table", "detail"])
    write_csv(out / "dd057_rollback_backup_plan.csv", rollback_rows, ["step", "action", "path", "executed_by_dd057"])
    write_csv(out / "dd057_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    dd058_contract = f"""# DD-058 Candidate Active Catalog Promotion Execution Contract

DD-057 is report-only. DD-058 is the earliest package that may perform controlled promotion.

## Preconditions

```text
DD-052: {dd052_manifest.get('status', '')}
DD-053: {dd053_manifest.get('status', '')}
DD-056R: {dd056r_manifest.get('status', '')}
DD-057: {status}
```

## DD-058 required behavior

```text
1. Create timestamped rollback backup under:
   {backup_root}

2. Backup existing active catalog:
   {active_path}

3. Backup related current CDX/LMDB artifacts:
   {index_path}
   {lmdb_path}

4. Copy staged DBF/DTX artifacts from:
   {staged_path}

5. Promote or copy related CDX and LMDB artifacts only after exact artifact mapping is accepted.

6. Run post-promotion readback:
   pydottalk row counts
   DotTalk++ USE/SET INDEX/SET ORDER/LIST
   HELP/META/CMDHELPCHK mutation check remains 0
```

## DD-058 still disallowed unless separately authorized

```text
source edits
HELP/META/CMDHELPCHK mutation
catalog content regeneration
manual row repair
```
"""
    (out / "DD058_CANDIDATE_ACTIVE_PROMOTION_EXECUTION_CONTRACT.md").write_text(dd058_contract, encoding="utf-8")

    manifest = {
        "contract": "dd057_active_catalog_promotion_readiness_plan_v0",
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
        "dd052_status": dd052_manifest.get("status", ""),
        "dd053_status": dd053_manifest.get("status", ""),
        "dd056r_status": dd056r_manifest.get("status", ""),
        "tables": len(TABLES),
        "promotion_artifacts": len(promotion_rows),
        "required_missing": len(missing_required),
        "cdx_tables_covered": len(cdx_tables),
        "lmdb_artifact_rows": len(lmdb_artifacts),
        "review_rows": len(review_rows),
        "failures": failures,
        "promotion_execution_authorized": 0,
        "active_catalog_mutation": 0,
        "staged_catalog_mutation": 0,
        "cdx_lmdb_mutation": 0,
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "DD-058 controlled active catalog promotion execution package after explicit authorization.",
    }
    write_json(out / "dd057_active_catalog_promotion_readiness_manifest.json", manifest)

    report = f"""# DD-057 Active Catalog Promotion Readiness Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-057 checks whether the staged Data Dictionary catalog is ready for a controlled
active-catalog promotion package.

## Proven inputs

```text
DD-052: {dd052_manifest.get('status', '')}
DD-053: {dd053_manifest.get('status', '')}
DD-056R: {dd056r_manifest.get('status', '')}
```

## Artifact coverage

- Tables: **{len(TABLES)}**
- Promotion artifact rows: **{len(promotion_rows)}**
- Missing required DBF/DTX artifacts: **{len(missing_required)}**
- CDX tables covered: **{len(cdx_tables)}**
- LMDB artifact rows observed: **{len(lmdb_artifacts)}**
- Review rows: **{len(review_rows)}**

## Boundary

DD-057 is report-only. It does not mutate the active catalog, staged catalog,
CDX/LMDB artifacts, source, HELP/META/CMDHELPCHK, or promotion state.

## Next

If accepted, DD-058 may perform controlled promotion only after explicit
authorization and only with rollback backup and post-promotion readback gates.
"""
    (out / "DD057_ACTIVE_CATALOG_PROMOTION_READINESS_PLAN.md").write_text(report, encoding="utf-8")

    print(f"DD-057 active catalog promotion readiness manifest: {out / 'dd057_active_catalog_promotion_readiness_manifest.json'}")
    print(f"status: {status}; promotion_artifacts: {len(promotion_rows)}; required_missing: {len(missing_required)}; review_rows: {len(review_rows)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
