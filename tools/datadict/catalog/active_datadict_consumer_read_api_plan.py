#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List


CORE_TABLES = [
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

READ_SURFACES = [
    {
        "surface_id": "DDICT_STATUS",
        "consumer": "DotTalk++ command",
        "name": "DDICT STATUS",
        "purpose": "Show active Data Dictionary baseline/run/profile/runtime status.",
        "primary_tables": "DDRUN,DDBASE,DDPROFILE,DDGATE",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
    },
    {
        "surface_id": "DDICT_TABLES",
        "consumer": "DotTalk++ command",
        "name": "DDICT TABLES",
        "purpose": "List catalog tables and row counts from active catalog.",
        "primary_tables": ",".join(CORE_TABLES),
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
    },
    {
        "surface_id": "DDICT_OBJECTS",
        "consumer": "DotTalk++ command",
        "name": "DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]",
        "purpose": "Browse catalog objects such as tables, fields, tags, sources, and evidence records.",
        "primary_tables": "DDOBJECT,DDATTR,DDEDGE,DDEVID,DDPROFILE",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
    },
    {
        "surface_id": "DDICT_FIELDS",
        "consumer": "DotTalk++ command",
        "name": "DDICT FIELDS <table>",
        "purpose": "Resolve fields for a catalog table through DDOBJECT/DDEDGE/DDATTR.",
        "primary_tables": "DDOBJECT,DDEDGE,DDATTR",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
    },
    {
        "surface_id": "DDICT_TAGS",
        "consumer": "DotTalk++ command",
        "name": "DDICT TAGS <table>",
        "purpose": "Resolve planned/runtime tags for a catalog table through DDOBJECT/DDEDGE/DDATTR and CDX evidence.",
        "primary_tables": "DDOBJECT,DDEDGE,DDATTR",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
    },
    {
        "surface_id": "DDICT_REL",
        "consumer": "DotTalk++ command",
        "name": "DDICT REL <object-id-or-name>",
        "purpose": "Show incoming/outgoing relationships for a catalog object.",
        "primary_tables": "DDOBJECT,DDEDGE",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P2",
    },
    {
        "surface_id": "DDICT_EVIDENCE",
        "consumer": "DotTalk++ command",
        "name": "DDICT EVIDENCE <object-id-or-name>",
        "purpose": "Show source/evidence trace for catalog objects.",
        "primary_tables": "DDEVID,DDSOURCE,DDARTIF,DDATTR",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P2",
    },
    {
        "surface_id": "PYDD_OPEN",
        "consumer": "pydottalk",
        "name": "open_active_datadict(repo_root)",
        "purpose": "Open active Data Dictionary tables with known paths and row-count sanity checks.",
        "primary_tables": ",".join(CORE_TABLES),
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
    },
    {
        "surface_id": "PYDD_RESOLVE_OBJECT",
        "consumer": "pydottalk",
        "name": "resolve_object(name=None, objid=None, objtype=None)",
        "purpose": "Resolve catalog object identity and primary attributes.",
        "primary_tables": "DDOBJECT,DDATTR",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
    },
    {
        "surface_id": "PYDD_FIELDS_FOR_TABLE",
        "consumer": "pydottalk",
        "name": "fields_for_table(table_name)",
        "purpose": "Return field definitions for a catalog table.",
        "primary_tables": "DDOBJECT,DDEDGE,DDATTR",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
    },
    {
        "surface_id": "PYDD_TAGS_FOR_TABLE",
        "consumer": "pydottalk",
        "name": "tags_for_table(table_name)",
        "purpose": "Return tag definitions for a catalog table.",
        "primary_tables": "DDOBJECT,DDEDGE,DDATTR",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
    },
    {
        "surface_id": "PYDD_EDGES",
        "consumer": "pydottalk",
        "name": "edges_for_object(objid, direction='both')",
        "purpose": "Return relationship graph edges for a catalog object.",
        "primary_tables": "DDEDGE,DDOBJECT",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P2",
    },
]

QUERY_PATTERNS = [
    {
        "query_id": "Q_STATUS_BASELINE",
        "description": "Current active Data Dictionary baseline and run status.",
        "tables": "DDRUN,DDBASE,DDPROFILE,DDGATE",
        "indexes": "DDRUN.RUNID,DDBASE.BASEID,DDPROFILE.NAME,DDGATE.STATUS",
        "consumer": "DDICT STATUS / pydottalk status()",
        "priority": "P1",
    },
    {
        "query_id": "Q_TABLE_FIELDS",
        "description": "Fields belonging to a catalog table.",
        "tables": "DDOBJECT,DDEDGE,DDATTR",
        "indexes": "DDOBJECT.OBJID,DDEDGE.FROMOBJ,DDEDGE.TOOBJ,DDATTR.OBJID",
        "consumer": "DDICT FIELDS / fields_for_table()",
        "priority": "P1",
    },
    {
        "query_id": "Q_TABLE_TAGS",
        "description": "Tags belonging to a catalog table.",
        "tables": "DDOBJECT,DDEDGE,DDATTR",
        "indexes": "DDOBJECT.OBJID,DDEDGE.FROMOBJ,DDEDGE.TOOBJ,DDATTR.OBJID",
        "consumer": "DDICT TAGS / tags_for_table()",
        "priority": "P1",
    },
    {
        "query_id": "Q_OBJECT_ATTRS",
        "description": "Attributes for an object.",
        "tables": "DDOBJECT,DDATTR",
        "indexes": "DDOBJECT.OBJID,DDATTR.OBJID,DDATTR.ATTRNAME",
        "consumer": "DDICT OBJECT / attrs_for_object()",
        "priority": "P1",
    },
    {
        "query_id": "Q_OBJECT_GRAPH",
        "description": "Incoming/outgoing relationship edges.",
        "tables": "DDEDGE,DDOBJECT",
        "indexes": "DDEDGE.FROMOBJ,DDEDGE.TOOBJ,DDEDGE.EDGETYPE",
        "consumer": "DDICT REL / edges_for_object()",
        "priority": "P2",
    },
    {
        "query_id": "Q_EVIDENCE_TRACE",
        "description": "Source and evidence trace for object definitions.",
        "tables": "DDEVID,DDSOURCE,DDARTIF,DDATTR",
        "indexes": "DDEVID.EVID,DDEVID.OBJID,DDEVID.SRCID,DDSOURCE.SRCID,DDARTIF.ARTID",
        "consumer": "DDICT EVIDENCE / evidence_for_object()",
        "priority": "P2",
    },
    {
        "query_id": "Q_PROFILE_FILTER",
        "description": "Filter visible/overlay items by profile.",
        "tables": "DDPROFILE,DDOBJECT,DDSOURCE,DDRUN",
        "indexes": "DDPROFILE.NAME,DDOBJECT.OBJTYPE,DDSOURCE.KIND",
        "consumer": "PROFILE-aware DDICT views",
        "priority": "P2",
    },
]

PHASES = [
    {
        "phase": "DD-061",
        "name": "Consumer/read API plan",
        "status": "REPORT_ONLY_PLAN",
        "allowed": "Read reports/manifests and active artifact metadata; emit plans and candidate read-only API skeleton.",
        "forbidden": "Runtime command registration, C++ edits, DBF writes, HELP/META/CMDHELPCHK mutation.",
    },
    {
        "phase": "DD-062",
        "name": "pydottalk read-only helper prototype",
        "status": "FUTURE_GUARDED",
        "allowed": "Create tools/datadict/catalog/datadict_reader.py only after authorization; read-only pydottalk calls.",
        "forbidden": "DBF writes, catalog mutation, runtime C++ integration.",
    },
    {
        "phase": "DD-063",
        "name": "DotTalk++ command surface plan",
        "status": "FUTURE_REPORT_ONLY",
        "allowed": "Plan DDICT command syntax/help contracts.",
        "forbidden": "C++ command implementation until separately authorized.",
    },
    {
        "phase": "DD-064",
        "name": "Runtime read-only command implementation",
        "status": "FUTURE_AUTH_REQUIRED",
        "allowed": "Implement after DD-063 accepted.",
        "forbidden": "Mutation commands or automatic catalog repair.",
    },
]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


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


def inspect_active_artifacts(active_inventory_path: Path) -> Dict[str, Any]:
    if not active_inventory_path.exists():
        return {"exists": 0, "active_dbf": 0, "active_cdx": 0, "active_lmdb": 0}
    with active_inventory_path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f))
    return {
        "exists": 1,
        "active_dbf": sum(1 for r in rows if r.get("kind") == "DBF" and r.get("exists") == "1"),
        "active_cdx": sum(1 for r in rows if r.get("kind") == "CDX" and r.get("exists") == "1"),
        "active_lmdb": sum(1 for r in rows if r.get("kind") == "LMDB" and r.get("exists") == "1"),
        "rows": len(rows),
    }


def candidate_reader_api() -> str:
    # Use a joined line list to avoid nested triple-quote parser hazards in the generator.
    lines = [
        '"""Candidate DD-061 active Data Dictionary reader API skeleton.',
        "",
        "This file is emitted as a report artifact only. Do not install as production code",
        "until a later DD package explicitly authorizes it.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "from pathlib import Path",
        "from typing import Any, Dict, List, Optional",
        "",
        "",
        "CORE_TABLES = [",
        '    "DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE",',
        '    "DDEVID", "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE",',
        "]",
        "",
        "",
        "@dataclass(frozen=True)",
        "class DataDictPaths:",
        "    repo_root: Path",
        "    active_catalog: Path",
        "    index_path: Path",
        "    lmdb_path: Path",
        "",
        "",
        "class ActiveDataDictionaryReader:",
        '    """Read-only active Data Dictionary catalog reader."""',
        "",
        "    def __init__(self, paths: DataDictPaths) -> None:",
        "        self.paths = paths",
        "",
        "    def status(self) -> Dict[str, Any]:",
        '        """Return active baseline/run/profile status."""',
        '        raise NotImplementedError("DD-062 prototype target")',
        "",
        "    def table_counts(self) -> Dict[str, int]:",
        '        """Return row counts for all catalog tables."""',
        '        raise NotImplementedError("DD-062 prototype target")',
        "",
        "    def resolve_object(self, *, objid: Optional[str] = None, name: Optional[str] = None, objtype: Optional[str] = None) -> Dict[str, Any]:",
        '        """Resolve one object by id/name/type."""',
        '        raise NotImplementedError("DD-062 prototype target")',
        "",
        "    def attrs_for_object(self, objid: str) -> List[Dict[str, Any]]:",
        '        """Return DDATTR rows for an object."""',
        '        raise NotImplementedError("DD-062 prototype target")',
        "",
        "    def fields_for_table(self, table_name: str) -> List[Dict[str, Any]]:",
        '        """Return field definitions for a catalog table."""',
        '        raise NotImplementedError("DD-062 prototype target")',
        "",
        "    def tags_for_table(self, table_name: str) -> List[Dict[str, Any]]:",
        '        """Return tag definitions for a catalog table."""',
        '        raise NotImplementedError("DD-062 prototype target")',
        "",
        "    def edges_for_object(self, objid: str, direction: str = \"both\") -> List[Dict[str, Any]]:",
        '        """Return incoming/outgoing graph edges."""',
        '        raise NotImplementedError("DD-062 prototype target")',
        "",
        "    def evidence_for_object(self, objid: str) -> List[Dict[str, Any]]:",
        '        """Return source/evidence trace for an object."""',
        '        raise NotImplementedError("DD-062 prototype target")',
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-061 v1.1 report-only active Data Dictionary consumer/read API plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD061-active-datadict-consumer-read-api-plan-v1_1")
    ap.add_argument("--dd060-dir", default="docs/datadict/reports/DD060-datadict-promotion-cycle-savepoint-final-v0")
    ap.add_argument("--dd059-dir", default="docs/datadict/reports/DD059-active-catalog-promotion-closure-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd060_dir = (repo / args.dd060_dir).resolve()
    dd059_dir = (repo / args.dd059_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd060_manifest = read_json(dd060_dir / "dd060_datadict_promotion_cycle_savepoint_manifest.json")
    dd060_summary = read_json(dd060_dir / "dd060_promotion_cycle_savepoint_summary.json")
    dd059_summary = read_json(dd059_dir / "dd059_active_catalog_closure_summary.json")
    active_artifact = inspect_active_artifacts(dd059_dir / "dd059_active_artifact_inventory.csv")

    dd060_green = dd060_manifest.get("status") == "DATADICT_PROMOTION_CYCLE_SAVEPOINT_GREEN"
    active_state_ok = (
        dd060_summary.get("savepoint_state") == "DATADICT_ACTIVE_CATALOG_PROMOTION_CYCLE_CLOSED"
        or dd059_summary.get("active_catalog_state") == "ACTIVE_DATA_DICTIONARY_CATALOG_PROMOTED_AND_RUNTIME_VERIFIED"
    )
    active_artifacts_ok = active_artifact.get("active_dbf") == 11 and active_artifact.get("active_cdx") == 11 and active_artifact.get("active_lmdb") == 11

    gate_rows = [
        {
            "gate": "dd060_savepoint_green",
            "expected": "DATADICT_PROMOTION_CYCLE_SAVEPOINT_GREEN",
            "observed": dd060_manifest.get("status", ""),
            "pass": int(dd060_green),
        },
        {
            "gate": "promotion_cycle_closed",
            "expected": "DATADICT_ACTIVE_CATALOG_PROMOTION_CYCLE_CLOSED",
            "observed": dd060_summary.get("savepoint_state", dd059_summary.get("active_catalog_state", "")),
            "pass": int(active_state_ok),
        },
        {
            "gate": "active_catalog_artifacts_available",
            "expected": "11 DBF / 11 CDX / 11 LMDB",
            "observed": f"{active_artifact.get('active_dbf')} DBF / {active_artifact.get('active_cdx')} CDX / {active_artifact.get('active_lmdb')} LMDB",
            "pass": int(active_artifacts_ok),
        },
        {
            "gate": "consumer_plan_report_only",
            "expected": 1,
            "observed": 1,
            "pass": 1,
        },
    ]

    boundary_rows = [
        {"boundary": "consumer_read_api_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "runtime_command_registration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "ACTIVE_DATADICT_CONSUMER_READ_API_PLAN_READY" if failures == 0 else "ACTIVE_DATADICT_CONSUMER_READ_API_PLAN_REVIEW"

    write_csv(out / "dd061_read_surface_plan.csv", READ_SURFACES, [
        "surface_id", "consumer", "name", "purpose", "primary_tables", "read_only",
        "mutation_allowed", "priority",
    ])
    write_csv(out / "dd061_query_pattern_plan.csv", QUERY_PATTERNS, [
        "query_id", "description", "tables", "indexes", "consumer", "priority",
    ])
    write_csv(out / "dd061_phase_plan.csv", PHASES, ["phase", "name", "status", "allowed", "forbidden"])
    write_csv(out / "dd061_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd061_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    (out / "dd061_candidate_active_datadict_reader_api.py").write_text(candidate_reader_api(), encoding="utf-8")

    contract = f"""# DD-061 Active Data Dictionary Consumer / Read API Contract

Status: `{status}`

## Purpose

Define read-only consumer surfaces for the now-active Data Dictionary catalog.

## Active catalog prerequisite

```text
DD-060: {dd060_manifest.get('status', '')}
State: {dd060_summary.get('savepoint_state', dd059_summary.get('active_catalog_state', ''))}
```

## Read-only doctrine

Consumers may:

```text
open active Data Dictionary DBFs
use existing CDX/LMDB indexes
resolve catalog objects, fields, tags, relationships, evidence, profiles, and status
emit reports
```

Consumers may not:

```text
append rows
replace rows
delete/pack/zap
create DBFs
create/rebuild CDX or LMDB
mutate HELP/META/CMDHELPCHK
repair catalog content automatically
```

## Candidate surfaces

See:

```text
dd061_read_surface_plan.csv
dd061_query_pattern_plan.csv
dd061_candidate_active_datadict_reader_api.py
```
"""
    (out / "DD061_ACTIVE_DATADICT_CONSUMER_READ_API_CONTRACT.md").write_text(contract, encoding="utf-8")

    manifest = {
        "contract": "dd061_active_datadict_consumer_read_api_plan_v1_1",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "bugfix": "v1.1 fixes v0 nested-string SyntaxError in candidate_reader_api artifact generation.",
        "dd060_status": dd060_manifest.get("status", ""),
        "savepoint_state": dd060_summary.get("savepoint_state", ""),
        "active_catalog_state": dd059_summary.get("active_catalog_state", ""),
        "active_dbf_count": active_artifact.get("active_dbf"),
        "active_cdx_count": active_artifact.get("active_cdx"),
        "active_lmdb_count": active_artifact.get("active_lmdb"),
        "read_surfaces": len(READ_SURFACES),
        "query_patterns": len(QUERY_PATTERNS),
        "phase_rows": len(PHASES),
        "failures": failures,
        "active_catalog_mutation": 0,
        "source_edits": 0,
        "runtime_command_registration": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-062 guarded pydottalk read-only helper prototype, or DD-063 report-only DotTalk++ DDICT command contract.",
    }
    write_json(out / "dd061_active_datadict_consumer_read_api_plan_manifest.json", manifest)

    report = f"""# DD-061 Active Data Dictionary Consumer / Read API Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## v1.1 bugfix

DD-061 v1.1 fixes a v0 Python SyntaxError caused by nested string generation for
the candidate reader API skeleton.

## Purpose

DD-061 defines the first read-only consumer/API plan for the active Data
Dictionary catalog.

## Prerequisite state

```text
DD-060: {dd060_manifest.get('status', '')}
Savepoint: {dd060_summary.get('savepoint_state', '')}
Active catalog: {dd059_summary.get('active_catalog_state', '')}
```

## Active artifact evidence

- Active DBFs: **{active_artifact.get('active_dbf')}**
- Active CDX containers: **{active_artifact.get('active_cdx')}**
- Active LMDB environments: **{active_artifact.get('active_lmdb')}**

## Planned read surfaces

- Read surfaces: **{len(READ_SURFACES)}**
- Query patterns: **{len(QUERY_PATTERNS)}**
- Phase rows: **{len(PHASES)}**

## Boundary

DD-061 is report-only. It does not mutate the active catalog, edit source,
register runtime commands, mutate HELP/META/CMDHELPCHK, regenerate catalog
content, or repair rows.

## Next options

```text
DD-062 guarded pydottalk read-only helper prototype
DD-063 report-only DotTalk++ DDICT command contract
```
"""
    (out / "DD061_ACTIVE_DATADICT_CONSUMER_READ_API_PLAN.md").write_text(report, encoding="utf-8")

    print(f"DD-061 v1.1 active Data Dictionary consumer/read API plan manifest: {out / 'dd061_active_datadict_consumer_read_api_plan_manifest.json'}")
    print(f"status: {status}; surfaces: {len(READ_SURFACES)}; queries: {len(QUERY_PATTERNS)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
