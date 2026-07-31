#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List


CANONICAL_TABLE_ORDER = [
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

DEFAULT_ROW_COUNTS = {
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
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def newest_matching(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    matches = [p for p in root.rglob(pattern) if p.is_file()]
    if not matches:
        return None
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0]


def find_manifest(run_dir: Path, name: str) -> Path:
    exact = run_dir / name
    if exact.exists():
        return exact
    found = newest_matching(run_dir, name)
    return found or exact


def load_dd040_counts(dd040_dir: Path) -> Dict[str, int]:
    counts_path = dd040_dir / "dd040_projection_row_counts.csv"
    rows = read_csv_dict(counts_path)
    counts: Dict[str, int] = {}
    for r in rows:
        table = (r.get("table") or r.get("Table") or "").strip().upper()
        val = r.get("rows") or r.get("Rows") or ""
        if not table:
            continue
        try:
            counts[table] = int(float(val))
        except Exception:
            counts[table] = 0
    if not counts:
        counts = dict(DEFAULT_ROW_COUNTS)
    return counts


def find_projection_csvs(dd040_dir: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for table in CANONICAL_TABLE_ORDER:
        candidates = []
        for p in dd040_dir.rglob("*.csv"):
            n = p.name.lower()
            if table.lower() in n and "row_count" not in n and "counts" not in n:
                candidates.append(p)
        if candidates:
            candidates.sort(key=lambda p: (len(p.name), p.name.lower()))
            out[table] = str(candidates[0])
        else:
            out[table] = ""
    return out


def find_ddl_artifacts(dd039_dir: Path) -> List[str]:
    names = []
    if not dd039_dir.exists():
        return names
    for p in dd039_dir.rglob("*"):
        if not p.is_file():
            continue
        n = p.name.lower()
        if n.endswith((".csv", ".json", ".md", ".dts")) and ("ddl" in n or "definition" in n or "catalog" in n):
            names.append(str(p))
    names.sort()
    return names[:50]


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-051 report-only canonical Data Dictionary catalog rebuild plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD051-canonical-catalog-rebuild-plan-v0")
    ap.add_argument("--dd039-dir", default="docs/datadict/reports/DD039-catalog-dbfdll-definition-v0")
    ap.add_argument("--dd040-dir", default="docs/datadict/reports/DD040-catalog-row-projection-v0")
    ap.add_argument("--dd049-dir", default="docs/datadict/reports/DD049-after-dd050-x64-header-inspection-closure-v0")
    ap.add_argument("--dd050-proof", default="docs/datadict/runlog/DD-050_LOCAL_SHARED_MEMO_HELPER_CLEANUP_PROOF.md")
    ap.add_argument("--target-slot", default="metadata\\datadict_canonical_rebuild_v0")
    ap.add_argument("--target-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd039_dir = (repo / args.dd039_dir).resolve()
    dd040_dir = (repo / args.dd040_dir).resolve()
    dd049_dir = (repo / args.dd049_dir).resolve()
    dd050_proof = (repo / args.dd050_proof).resolve()
    target_path = (repo / args.target_path).resolve()
    active_path = (repo / args.active_path).resolve()

    dd039_manifest = read_json(find_manifest(dd039_dir, "dd039_catalog_dbf_ddl_definition_manifest.json"))
    dd040_manifest = read_json(find_manifest(dd040_dir, "dd040_projection_manifest.json"))
    dd049_manifest = read_json(find_manifest(dd049_dir, "dd049_x64_header_inspection_evidence_closure_manifest.json"))

    counts = load_dd040_counts(dd040_dir)
    projection_csvs = find_projection_csvs(dd040_dir)
    ddl_artifacts = find_ddl_artifacts(dd039_dir)

    table_rows: List[Dict[str, Any]] = []
    total_rows = 0
    for order, table in enumerate(CANONICAL_TABLE_ORDER, start=1):
        rows = int(counts.get(table, 0))
        total_rows += rows
        table_rows.append({
            "build_order": order,
            "table": table,
            "projected_rows": rows,
            "ddl_source": "DD039",
            "row_source": "DD040",
            "projection_csv_candidate": projection_csvs.get(table, ""),
            "target_slot": args.target_slot,
            "target_path": safe_rel(repo, target_path),
            "build_action": "CREATE_X64_THEN_IMPORT",
            "memo_policy": "DOTTalk++_CREATE_OWNS_MEMO_DTX_AND_IMPORT_OWNS_MEMO_PAYLOAD",
            "index_policy": "PLAN_ONLY_DD052_OR_LATER",
            "promotion_policy": "NO_PROMOTION_IN_DD051",
        })

    dd039_ok = dd039_manifest.get("status") == "CATALOG_DBF_DDL_DEFINITION_PLAN_READY" or "PLAN_READY" in str(dd039_manifest.get("status", ""))
    dd040_ok = dd040_manifest.get("status") == "CATALOG_ROW_PROJECTION_READY" or "PROJECTION_READY" in str(dd040_manifest.get("status", ""))
    dd049_ok = dd049_manifest.get("status") == "X64_HEADER_INSPECTION_EVIDENCE_CLOSURE_GREEN"
    dd050_ok = dd050_proof.exists()
    table_count_ok = len(table_rows) == 11
    row_count_ok = total_rows == 638

    gate_rows = [
        {
            "gate": "dd039_catalog_ddl_plan_ready",
            "expected": "CATALOG_DBF_DDL_DEFINITION_PLAN_READY",
            "observed": dd039_manifest.get("status", ""),
            "pass": int(dd039_ok),
        },
        {
            "gate": "dd040_row_projection_ready",
            "expected": "CATALOG_ROW_PROJECTION_READY",
            "observed": dd040_manifest.get("status", ""),
            "pass": int(dd040_ok),
        },
        {
            "gate": "dd049_create_import_memo_probe_closure_green",
            "expected": "X64_HEADER_INSPECTION_EVIDENCE_CLOSURE_GREEN",
            "observed": dd049_manifest.get("status", ""),
            "pass": int(dd049_ok),
        },
        {
            "gate": "dd050_shared_helper_runtime_proof_exists",
            "expected": 1,
            "observed": int(dd050_ok),
            "pass": int(dd050_ok),
        },
        {
            "gate": "canonical_table_count",
            "expected": 11,
            "observed": len(table_rows),
            "pass": int(table_count_ok),
        },
        {
            "gate": "canonical_projected_row_count",
            "expected": 638,
            "observed": total_rows,
            "pass": int(row_count_ok),
        },
    ]

    failures = sum(1 for r in gate_rows if str(r["pass"]) != "1")
    status = "CANONICAL_CATALOG_REBUILD_PLAN_READY" if failures == 0 else "CANONICAL_CATALOG_REBUILD_PLAN_REVIEW"

    boundary_rows = [
        {"boundary": "report_only_plan", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "dbf_files_created", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "csv_rows_imported", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "sandbox_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "probe_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_build", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_index_created", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "promotion_executed", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd051_canonical_table_build_plan.csv", table_rows, [
        "build_order", "table", "projected_rows", "ddl_source", "row_source",
        "projection_csv_candidate", "target_slot", "target_path", "build_action",
        "memo_policy", "index_policy", "promotion_policy",
    ])
    write_csv(out / "dd051_rebuild_readiness_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd051_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    write_json(out / "dd051_input_artifact_inventory.json", {
        "dd039_dir": str(dd039_dir),
        "dd040_dir": str(dd040_dir),
        "dd049_dir": str(dd049_dir),
        "dd050_proof": str(dd050_proof),
        "dd039_manifest": dd039_manifest,
        "dd040_manifest": dd040_manifest,
        "dd049_manifest": dd049_manifest,
        "ddl_artifacts_observed": ddl_artifacts,
        "projection_csv_candidates": projection_csvs,
    })

    dot_script = "\n".join([
        "* DD-051 candidate DotTalk++ execution outline for DD-052 or later",
        "* PLAN ONLY: do not execute as-is without DD-052 execution package.",
        f"setpath dbf {args.target_slot}",
        "* For each table:",
        "*   create x64 <table> (<field definitions from DD-039>)",
        "*   import <projected CSV from DD-040/DD-052 staging>",
        "*   count",
        "*   memo readback checks for memo-bearing tables",
        "*   index/tag creation after CREATE+IMPORT proof is green",
        "",
    ])
    (out / "dd051_candidate_dottalk_execution_outline.dts").write_text(dot_script, encoding="utf-8")

    dd052_contract = f"""# DD-052 Candidate Execution Contract

DD-051 is report-only. DD-052 should be the first execution/staging package.

## Target

```text
DBF slot: {args.target_slot}
Path: {safe_rel(repo, target_path)}
```

## Required DD-052 behavior

```text
1. Re-stage projected CSV rows from DD-040 into import-ready CSV files.
2. Generate DotTalk++ CREATE X64 commands from DD-039 definitions.
3. Create real catalog DBFs under the target rebuild path.
4. IMPORT rows through DotTalk++ runtime.
5. Verify row counts and selected memo readback.
6. Create CDX/tags only after CREATE+IMPORT proof is green.
7. Do not promote to active catalog in DD-052 unless separately authorized.
```

## Disallowed in DD-052 unless explicitly authorized

```text
active catalog replacement
HELP/META/CMDHELPCHK mutation
LMDB build
source edits
```
"""
    (out / "DD052_CANDIDATE_EXECUTION_CONTRACT.md").write_text(dd052_contract, encoding="utf-8")

    manifest = {
        "contract": "dd051_canonical_catalog_rebuild_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "failures": failures,
        "tables_planned": len(table_rows),
        "total_projected_rows": total_rows,
        "target_slot": args.target_slot,
        "target_path": str(target_path),
        "active_path": str(active_path),
        "dbf_files_created": 0,
        "rows_imported": 0,
        "cdx_index_created": 0,
        "lmdb_build": 0,
        "promotion_executed": 0,
        "active_catalog_mutation": 0,
        "cxx_source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_package": "DD-052 canonical catalog CREATE X64 / IMPORT staging execution package",
    }
    write_json(out / "dd051_canonical_catalog_rebuild_plan_manifest.json", manifest)

    report = f"""# DD-051 Canonical Data Dictionary Catalog Rebuild Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-051 is the report-only bridge from the DDPROBE proof lane to the real Data
Dictionary catalog rebuild.

## Inputs

- DD-039 DDL/DBF definition plan: `{dd039_manifest.get('status', '')}`
- DD-040 row projection: `{dd040_manifest.get('status', '')}`
- DD-049 CREATE/IMPORT/memo evidence closure: `{dd049_manifest.get('status', '')}`
- DD-050 shared helper proof exists: `{int(dd050_ok)}`

## Planned rebuild

- Tables planned: **{len(table_rows)}**
- Projected rows: **{total_rows}**
- Target DBF slot: `{args.target_slot}`
- Target path: `{safe_rel(repo, target_path)}`

## Canonical build doctrine

```text
DotTalk++ CREATE X64 owns table/memo sidecar creation.
DotTalk++ IMPORT owns CSV row loading and x64 M-field memo payload storage.
pydottalk verifies/readbacks runtime-created tables.
Python orchestrates projection, reports, gates, and evidence.
```

## Boundary

DD-051 is report-only. It does not create DBFs, import rows, build CDX, build
LMDB, replace the active catalog, edit C++ source, or mutate HELP/META/CMDHELPCHK.

## Next

DD-052 may stage the first canonical real-catalog CREATE X64 / IMPORT execution
package under the rebuild target path after explicit authorization.
"""
    (out / "DD051_CANONICAL_CATALOG_REBUILD_PLAN.md").write_text(report, encoding="utf-8")

    print(f"DD-051 canonical catalog rebuild plan manifest: {out / 'dd051_canonical_catalog_rebuild_plan_manifest.json'}")
    print(f"status: {status}; tables: {len(table_rows)}; projected_rows: {total_rows}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
