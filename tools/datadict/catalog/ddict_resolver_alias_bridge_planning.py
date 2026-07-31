#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List

REQUIRED = {
    "DD096ZB": ("docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json", ["DD096ZB_BACKUP_CANDIDATE_STAGING_EXECUTED"]),
    "DD096ZC": ("docs/datadict/reports/DD096ZC-candidate-root-readback-validation-v0/dd096zc_candidate_root_readback_validation_manifest.json", ["DD096ZC_CANDIDATE_ROOT_READBACK_READY", "DD096ZC_CANDIDATE_ROOT_READBACK_GREEN"]),
    "DD096ZD": ("docs/datadict/reports/DD096ZD-candidate-cdx-lmdb-rebuild-planning-v0/dd096zd_candidate_cdx_lmdb_rebuild_planning_manifest.json", ["DD096ZD_CANDIDATE_CDX_LMDB_REBUILD_PLAN_READY"]),
}

TABLE_MAP = [
    ("DDRUN", "DATA_DICTIONARY_RUNS", "run catalog", "RUN_RECORD_ID"),
    ("DDOBJECT", "DATA_DICTIONARY_OBJECTS", "object catalog", "CATALOG_OBJECT_ID"),
    ("DDATTR", "DATA_DICTIONARY_OBJECT_ATTRIBUTES", "object attributes", "CATALOG_ATTRIBUTE_ID"),
    ("DDEDGE", "DATA_DICTIONARY_RELATION_EDGES", "relation graph", "RELATION_EDGE_ID"),
    ("DDEVID", "DATA_DICTIONARY_EVIDENCE_RECORDS", "evidence catalog", "EVIDENCE_RECORD_ID"),
    ("DDGATE", "DATA_DICTIONARY_GATE_RECORDS", "gate catalog", "GATE_RECORD_ID"),
]

SURFACES = [
    ("DDICT STATUS", "Must report active/candidate catalog roots, schema generation, and read mode."),
    ("DDICT TABLES", "Must list either legacy DD* names, x64 DATA_DICTIONARY_* names, or both depending resolver mode."),
    ("DDICT FIELDS <table>", "Must resolve DDOBJECT and DATA_DICTIONARY_OBJECTS to the same logical catalog family when bridge mode is enabled."),
    ("DDICT TAGS <table>", "Must distinguish catalog tag definitions from physical CDX availability."),
    ("DDICT REL <object> [IN|OUT|BOTH]", "Must use relation bridge for DATA_DICTIONARY_RELATION_EDGES."),
    ("DDICT EVIDENCE <object>", "Must use evidence bridge for DATA_DICTIONARY_EVIDENCE_RECORDS."),
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

def wc(path: Path, rows: List[Dict], fields: List[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def make_smoke_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-E DDICT resolver/alias bridge smoke draft")
    lines.append("* REVIEW ONLY: this script assumes candidate path SETPATH is acceptable in current runtime.")
    lines.append("* It does not modify HELP/CMDHELPCHK/source or active catalog data.")
    lines.append("")
    lines.append("* Candidate path setup:")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("")
    lines.append("* Candidate raw table readback:")
    for legacy, x64, desc, key in TABLE_MAP:
        lines.append(f"USE {x64}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("LIST")
        lines.append("CLOSE ALL")
        lines.append("")
    lines.append("* DDICT bridge smoke is deferred until resolver mode/API is implemented.")
    lines.append("* Desired future smoke:")
    for surf, desc in SURFACES:
        lines.append(f"*   {surf}")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def main():
    ap = argparse.ArgumentParser(description="DD096Z-E DDICT resolver/alias bridge planning")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZE-ddict-resolver-alias-bridge-planning-v0")
    ap.add_argument("--write-smoke-draft", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_ddict_resolver_alias_bridge_plan"
    gen.mkdir(parents=True, exist_ok=True)

    pre = []
    blockers = 0
    manifests = {}
    for lane, (rel, expected_list) in REQUIRED.items():
        path = repo / rel
        data = read_json(path)
        manifests[lane] = data
        observed = data.get("status", "MISSING")
        passed = int(observed in expected_list)
        blockers += 0 if passed else 1
        pre.append({
            "lane": lane,
            "manifest_path": str(path),
            "observed_status": observed,
            "expected_status": "|".join(expected_list),
            "pass": passed,
        })
    wc(gen / "dd096ze_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    candidate_root = Path(manifests.get("DD096ZB", {}).get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(manifests.get("DD096ZB", {}).get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    wc(gen / "dd096ze_table_alias_map.csv",
       [{"legacy_table": a, "x64_table": b, "catalog_family": c, "primary_key": d, "bridge_required": 1} for a,b,c,d in TABLE_MAP],
       ["legacy_table","x64_table","catalog_family","primary_key","bridge_required"])

    resolver_modes = [
        ("legacy_active", "Use current active DD* tables under dottalkpp/data/datadict.", "current compatibility mode"),
        ("x64_candidate", "Use inactive candidate DATA_DICTIONARY_* tables under docs/datadict/candidates/<run>/dbf.", "candidate validation mode"),
        ("x64_active", "Use promoted DATA_DICTIONARY_* tables under active datadict root.", "future promoted mode"),
        ("dual_bridge", "Accept both legacy DD* names and DATA_DICTIONARY_* names as aliases.", "recommended transition mode"),
    ]
    wc(gen / "dd096ze_resolver_mode_plan.csv",
       [{"mode": a, "meaning": b, "status": c} for a,b,c in resolver_modes],
       ["mode","meaning","status"])

    surface_rows = [
        {"surface": surf, "bridge_expectation": desc, "mutation_in_this_package": 0}
        for surf, desc in SURFACES
    ]
    wc(gen / "dd096ze_ddict_surface_bridge_expectations.csv", surface_rows,
       ["surface","bridge_expectation","mutation_in_this_package"])

    implementation_options = [
        ("OPTION_A_PATH_ALIAS_CONFIG", "External resolver config maps logical families to physical x64 table names/roots.", "good first candidate; minimal source changes later"),
        ("OPTION_B_SOURCE_RESOLVER_LAYER", "Central C++ DDICT resolver maps catalog family -> physical table based on mode.", "best long-term architecture"),
        ("OPTION_C_COMPATIBILITY_DBF_VIEWS", "Generate legacy DD* compatibility tables/views from DATA_DICTIONARY_*.", "safe but duplicates catalog data"),
        ("OPTION_D_DIRECT_ACTIVE_RENAME", "Rename DATA_DICTIONARY_* to DD* for active use.", "not recommended; loses long-name proof value"),
    ]
    wc(gen / "dd096ze_implementation_option_register.csv",
       [{"option_id": a, "description": b, "assessment": c} for a,b,c in implementation_options],
       ["option_id","description","assessment"])

    risks = [
        ("ZE-RISK-001", "DDICT code may hard-code DDOBJECT/DDATTR/etc.", "Find and centralize table-family resolver before any source change."),
        ("ZE-RISK-002", "Active cutover could break current DDICT if aliases are not proven.", "Keep legacy_active mode and require dual_bridge smoke before promotion."),
        ("ZE-RISK-003", "HELP/CMDHELPCHK may expect DDICT as one command with sub-surfaces.", "Do not mutate HELP/CMDHELPCHK in this lane; keep DD092D separate."),
        ("ZE-RISK-004", "Candidate CDX/LMDB rebuild may need resolver-aware tag names.", "Use tag manifest plan from DD096Z-D and do candidate-only rebuild later."),
        ("ZE-RISK-005", "Workspace schema may still refer to old table names.", "Plan workspace bridge/versioning separately before active switch."),
    ]
    wc(gen / "dd096ze_risk_register.csv",
       [{"risk_id": a, "risk": b, "mitigation": c} for a,b,c in risks],
       ["risk_id","risk","mitigation"])

    smoke_text = make_smoke_dts(candidate_dbf, candidate_index, candidate_lmdb)
    preview = gen / "DD096ZE_DDICT_RESOLVER_ALIAS_BRIDGE_SMOKE_DRAFT.dts"
    wt(preview, smoke_text)

    smoke_written = 0
    smoke_path = repo / "dottalkpp/data/scripts/DD096ZE_DDICT_RESOLVER_ALIAS_BRIDGE_SMOKE_DRAFT.dts"
    if args.write_smoke_draft:
        wt(smoke_path, smoke_text)
        smoke_written = 1

    boundary = [
        ("ddict_resolver_alias_bridge_planning_only", 1, 1, 1),
        ("source_edits", 0, 0, 1),
        ("build_file_edits", 0, 0, 1),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("candidate_cdx_lmdb_rebuild", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096ze_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    gate_rows = [
        {"gate": "preconditions_green", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "alias_map_written", "expected": len(TABLE_MAP), "observed": len(TABLE_MAP), "pass": 1},
        {"gate": "surface_expectations_written", "expected": len(SURFACES), "observed": len(SURFACES), "pass": 1},
        {"gate": "source_edits_performed", "expected": 0, "observed": 0, "pass": 1},
        {"gate": "active_replacement_performed", "expected": 0, "observed": 0, "pass": 1},
        {"gate": "smoke_draft_written_if_requested", "expected": int(args.write_smoke_draft), "observed": smoke_written, "pass": int(smoke_written == int(args.write_smoke_draft))},
    ]
    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    wc(out / "dd096ze_gate_ledger.csv", gate_rows, ["gate","expected","observed","pass"])

    status = "DD096ZE_DDICT_RESOLVER_ALIAS_BRIDGE_PLAN_READY" if failures == 0 else "DD096ZE_DDICT_RESOLVER_ALIAS_BRIDGE_PLAN_REVIEW"

    report = f"""# DD096Z-E DDICT Resolver/Alias Bridge Planning

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-E plans the compatibility bridge between current DDICT legacy DD* catalog access and the new x64 DATA_DICTIONARY_* candidate schema.

This is planning only. It does not edit source, mutate HELP/CMDHELPCHK, rebuild indexes, or replace the active catalog.

## Summary

- Precondition blockers: **{blockers}**
- Alias map rows: **{len(TABLE_MAP)}**
- DDICT surface expectations: **{len(SURFACES)}**
- Smoke draft written: **{smoke_written}**
- Source edits: **0**
- Active catalog replacement: **0**

## Recommended architecture

Prefer a centralized DDICT catalog-family resolver:

```text
logical family: objects
legacy physical table: DDOBJECT
x64 physical table: DATA_DICTIONARY_OBJECTS
mode: legacy_active | x64_candidate | x64_active | dual_bridge
```

Do not scatter table-name conditionals across DDICT subcommands.

## Next lane

DD096Z-F should be resolver bridge design-to-source plan or candidate-only resolver smoke design. Active cutover remains unauthorized.
"""
    wt(out / "DD096ZE_DDICT_RESOLVER_ALIAS_BRIDGE_PLANNING_REPORT.md", report)

    manifest = {
        "contract": "dd096ze_ddict_resolver_alias_bridge_planning_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "candidate_root": str(candidate_root),
        "candidate_dbf_root": str(candidate_dbf),
        "precondition_blockers": blockers,
        "alias_map_rows": len(TABLE_MAP),
        "surface_expectation_rows": len(SURFACES),
        "smoke_draft_written": smoke_written,
        "source_edits": 0,
        "active_catalog_replacement": 0,
        "candidate_cdx_lmdb_rebuild": 0,
        "active_cdx_lmdb_rebuild": 0,
        "failures": failures,
        "next_recommended_action": "DD096Z-F resolver bridge source-plan/candidate smoke design; no active replacement.",
    }
    wj(out / "dd096ze_ddict_resolver_alias_bridge_planning_manifest.json", manifest)

    print(f"DD096Z-E DDICT resolver/alias bridge plan manifest: {out / 'dd096ze_ddict_resolver_alias_bridge_planning_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; alias_map_rows: {len(TABLE_MAP)}; source_edits: 0; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
