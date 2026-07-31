#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD068_STATUS = "DDICT_BUILD_RUNTIME_SMOKE_CLOSURE_GREEN"

CATALOG_TABLES = [
    "ddrun", "ddbase", "ddsource", "ddobject", "ddattr", "ddedge",
    "ddevid", "ddgate", "ddreview", "ddartif", "ddprofile",
]

READ_SURFACES = [
    {
        "surface_id": "S1_DDICT_STATUS",
        "command": "DDICT STATUS",
        "phase": "P1",
        "tables": "DDRUN,DDBASE,DDPROFILE,DDGATE",
        "purpose": "Show active Data Dictionary baseline, run id, profiles, gates, and catalog health.",
        "implementation_note": "Open active catalog read-only; prefer existing CDX/LMDB indexes; no mutation.",
    },
    {
        "surface_id": "S2_DDICT_TABLES",
        "command": "DDICT TABLES",
        "phase": "P1",
        "tables": "DDOBJECT,DDATTR,DDEDGE",
        "purpose": "List catalog table objects and basic counts/visibility.",
        "implementation_note": "Start with table object rows; later add counts from DBF open/readback.",
    },
    {
        "surface_id": "S3_DDICT_FIELDS",
        "command": "DDICT FIELDS <table>",
        "phase": "P2",
        "tables": "DDOBJECT,DDEDGE,DDATTR",
        "purpose": "Resolve a table and list its field objects/attributes.",
        "implementation_note": "Requires object lookup and HAS_FIELD edge traversal.",
    },
    {
        "surface_id": "S4_DDICT_TAGS",
        "command": "DDICT TAGS <table>",
        "phase": "P2",
        "tables": "DDOBJECT,DDEDGE,DDATTR",
        "purpose": "Resolve a table and list indexed/tagged fields.",
        "implementation_note": "Read existing catalog/index metadata only; do not rebuild CDX/LMDB.",
    },
    {
        "surface_id": "S5_DDICT_OBJECTS",
        "command": "DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]",
        "phase": "P3",
        "tables": "DDOBJECT,DDATTR,DDPROFILE",
        "purpose": "Browse catalog objects by type/profile.",
        "implementation_note": "Profile overlay should remain read-only.",
    },
    {
        "surface_id": "S6_DDICT_REL",
        "command": "DDICT REL <object-id-or-name> [IN|OUT|BOTH]",
        "phase": "P3",
        "tables": "DDOBJECT,DDEDGE",
        "purpose": "Show incoming/outgoing relationships.",
        "implementation_note": "Graph traversal after FIELDS/TAGS prove edge traversal.",
    },
    {
        "surface_id": "S7_DDICT_EVIDENCE",
        "command": "DDICT EVIDENCE <object-id-or-name>",
        "phase": "P4",
        "tables": "DDEVID,DDSOURCE,DDARTIF,DDATTR,DDOBJECT",
        "purpose": "Show source/evidence provenance for catalog definitions.",
        "implementation_note": "Memo output must be bounded; no evidence repair.",
    },
]

IMPLEMENTATION_SLICES = [
    {
        "slice_id": "DD069A_STATUS_ONLY",
        "commands": "DDICT STATUS",
        "allowed_future_edits": "cmd_ddict.cpp only, plus optional read-only helper file if explicitly authorized",
        "risk": "LOW",
        "success_smoke": "DDICT STATUS prints active catalog path and table health",
    },
    {
        "slice_id": "DD069B_STATUS_TABLES",
        "commands": "DDICT STATUS; DDICT TABLES",
        "allowed_future_edits": "cmd_ddict.cpp/read-only helper; no registry/build patch expected",
        "risk": "LOW_MEDIUM",
        "success_smoke": "DDICT TABLES lists canonical DD* table set from active catalog",
    },
    {
        "slice_id": "DD069C_FIELDS_TAGS",
        "commands": "DDICT FIELDS <table>; DDICT TAGS <table>",
        "allowed_future_edits": "read-only traversal helper",
        "risk": "MEDIUM",
        "success_smoke": "DDICT FIELDS DDOBJECT and DDICT TAGS DDATTR return catalog-defined rows",
    },
]

RULES = [
    {"rule_id": "R01_ACTIVE_PATH", "rule": "Default active catalog path is dottalkpp/data/metadata/datadict."},
    {"rule_id": "R02_NO_CREATE_IMPORT", "rule": "DDICT must not CREATE, IMPORT, APPEND, REPLACE, DELETE, PACK, or ZAP."},
    {"rule_id": "R03_NO_INDEX_REBUILD", "rule": "DDICT must not CDX CREATE, CDX ADDTAG, or BUILDLMDB."},
    {"rule_id": "R04_NO_PROMOTION", "rule": "DDICT must not promote staging catalogs into active catalog."},
    {"rule_id": "R05_ENGINE_LAYER", "rule": "DDICT belongs to the engine/runtime metadata layer and must not depend on LabTalk/student artifacts."},
    {"rule_id": "R06_TEST_EACH_SURFACE", "rule": "Each implemented surface needs runtime smoke proof and no-mutation boundary evidence."},
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
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


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def table_ledger(repo: Path, active_dir: Path, staging_dir: Path, index_dir: Path, lmdb_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for name in CATALOG_TABLES:
        active_dbf = active_dir / f"{name}.dbf"
        active_dtx = active_dir / f"{name}.dtx"
        staging_dbf = staging_dir / f"{name}.dbf"
        cdx = index_dir / f"{name}.cdx"
        lmdb_table = lmdb_dir / name
        rows.append({
            "table": name.upper(),
            "active_dbf": rel(repo, active_dbf),
            "active_dbf_exists": int(active_dbf.exists()),
            "active_dbf_bytes": active_dbf.stat().st_size if active_dbf.exists() else 0,
            "active_dtx_exists": int(active_dtx.exists()),
            "active_dtx_bytes": active_dtx.stat().st_size if active_dtx.exists() else 0,
            "staging_dbf_exists": int(staging_dbf.exists()),
            "cdx_exists": int(cdx.exists()),
            "lmdb_dir_exists": int(lmdb_table.exists()),
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-069 DDICT read surface implementation plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD069-ddict-read-surface-implementation-plan-v0")
    ap.add_argument("--dd068-dir", default="docs/datadict/reports/DD068-ddict-build-runtime-smoke-closure-final-v0")
    ap.add_argument("--active-catalog-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--staging-catalog-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--index-path", default="dottalkpp/data/indexes/metadata/datadict")
    ap.add_argument("--lmdb-path", default="dottalkpp/data/lmdb/metadata/datadict")
    ap.add_argument("--cmd-ddict-source", default="src/cli/cmd_ddict.cpp")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd068_dir = (repo / args.dd068_dir).resolve()
    dd068_manifest = read_json(dd068_dir / "dd068_ddict_build_runtime_smoke_closure_manifest.json")

    active_dir = (repo / args.active_catalog_path).resolve()
    staging_dir = (repo / args.staging_catalog_path).resolve()
    index_dir = (repo / args.index_path).resolve()
    lmdb_dir = (repo / args.lmdb_path).resolve()
    cmd_source = (repo / args.cmd_ddict_source).resolve()
    cmd_text = read_text(cmd_source)

    table_rows = table_ledger(repo, active_dir, staging_dir, index_dir, lmdb_dir)
    active_table_count = sum(1 for r in table_rows if int(r["active_dbf_exists"]) == 1)
    active_dtx_count = sum(1 for r in table_rows if int(r["active_dtx_exists"]) == 1)
    staging_table_count = sum(1 for r in table_rows if int(r["staging_dbf_exists"]) == 1)

    dd068_green = int(dd068_manifest.get("status") == EXPECTED_DD068_STATUS)
    active_dir_exists = int(active_dir.exists())
    source_exists = int(cmd_source.exists())
    source_has_pending_shell = int("runtime read implementation is pending" in cmd_text.lower())
    source_has_house_shape = int("void cmd_DDICT" in cmd_text and "std::istringstream" in cmd_text)

    gate_rows = [
        {"gate": "dd068_runtime_smoke_green", "expected": EXPECTED_DD068_STATUS, "observed": dd068_manifest.get("status", ""), "pass": dd068_green},
        {"gate": "active_catalog_dir_exists", "expected": 1, "observed": active_dir_exists, "pass": active_dir_exists},
        {"gate": "active_catalog_tables_present", "expected": len(CATALOG_TABLES), "observed": active_table_count, "pass": int(active_table_count == len(CATALOG_TABLES))},
        {"gate": "staging_catalog_tables_present", "expected": len(CATALOG_TABLES), "observed": staging_table_count, "pass": int(staging_table_count == len(CATALOG_TABLES))},
        {"gate": "cmd_ddict_source_exists", "expected": 1, "observed": source_exists, "pass": source_exists},
        {"gate": "cmd_ddict_house_handler_shape", "expected": 1, "observed": source_has_house_shape, "pass": source_has_house_shape},
        {"gate": "cmd_ddict_pending_shell_detected", "expected": 1, "observed": source_has_pending_shell, "pass": source_has_pending_shell},
        {"gate": "implementation_plan_only", "expected": 1, "observed": 1, "pass": 1},
    ]
    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_READ_SURFACE_IMPLEMENTATION_PLAN_READY" if failures == 0 else "DDICT_READ_SURFACE_IMPLEMENTATION_PLAN_REVIEW"

    boundary_rows = [
        {"boundary": "read_surface_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd069_catalog_table_presence_ledger.csv", table_rows, [
        "table", "active_dbf", "active_dbf_exists", "active_dbf_bytes",
        "active_dtx_exists", "active_dtx_bytes", "staging_dbf_exists",
        "cdx_exists", "lmdb_dir_exists",
    ])
    write_csv(out / "dd069_read_surface_plan.csv", READ_SURFACES, [
        "surface_id", "command", "phase", "tables", "purpose", "implementation_note",
    ])
    write_csv(out / "dd069_implementation_slice_plan.csv", IMPLEMENTATION_SLICES, [
        "slice_id", "commands", "allowed_future_edits", "risk", "success_smoke",
    ])
    write_csv(out / "dd069_readonly_rules.csv", RULES, ["rule_id", "rule"])
    write_csv(out / "dd069_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd069_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-069 DDICT Read Surface Implementation Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-069 plans the first real read surfaces behind the now-compiled `DDICT`
runtime shell.

## Inputs

- DD-068 status: `{dd068_manifest.get('status', '')}`
- Active catalog path: `{rel(repo, active_dir)}`
- Staging catalog path: `{rel(repo, staging_dir)}`
- DDICT source: `{rel(repo, cmd_source)}`

## Catalog readiness

- Active catalog dir exists: **{active_dir_exists}**
- Active DBF tables present: **{active_table_count} / {len(CATALOG_TABLES)}**
- Active DTX sidecars present: **{active_dtx_count} / {len(CATALOG_TABLES)}**
- Staging DBF tables present: **{staging_table_count} / {len(CATALOG_TABLES)}**

## Implementation order

```text
1. DDICT STATUS
2. DDICT TABLES
3. DDICT FIELDS <table>
4. DDICT TAGS <table>
5. DDICT OBJECTS / REL / EVIDENCE after core traversal is proven
```

## Boundary

DD-069 is plan/readiness only. It does not edit C++ source, edit build files,
mutate active catalog data, append/replace/delete/pack/zap DBFs, rebuild
CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair rows.
"""
    (out / "DD069_DDICT_READ_SURFACE_IMPLEMENTATION_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd069_ddict_read_surface_implementation_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd068_status": dd068_manifest.get("status", ""),
        "active_catalog_path": rel(repo, active_dir),
        "staging_catalog_path": rel(repo, staging_dir),
        "active_table_count": active_table_count,
        "active_dtx_count": active_dtx_count,
        "staging_table_count": staging_table_count,
        "read_surfaces": len(READ_SURFACES),
        "implementation_slices": len(IMPLEMENTATION_SLICES),
        "failures": failures,
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "DD-070 guarded DDICT STATUS/TABLES implementation package after explicit authorization.",
    }
    write_json(out / "dd069_ddict_read_surface_implementation_plan_manifest.json", manifest)

    print(f"DD-069 DDICT read surface implementation plan manifest: {out / 'dd069_ddict_read_surface_implementation_plan_manifest.json'}")
    print(f"status: {status}; active_tables: {active_table_count}; surfaces: {len(READ_SURFACES)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
