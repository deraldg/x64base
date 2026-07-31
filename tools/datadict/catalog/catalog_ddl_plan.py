#!/usr/bin/env python3
"""
DD-039 report-only Data Dictionary Catalog DBF/DDL Definition Plan.

This tool emits catalog DBF table/field/tag definition plans and gate ledgers.
It does not create DBFs, write records, run DotTalk++, mutate HELP/META/CMDHELPCHK,
or accept/promote any catalog.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List


TABLES = [
    ("DDRUN", "Data Dictionary run/baseline/check record", "ENGINE", "RUNID"),
    ("DDBASE", "Accepted baseline record and fingerprint", "ENGINE", "BASEID"),
    ("DDSOURCE", "Evidence source file/artifact identity", "ENGINE", "SRCID"),
    ("DDOBJECT", "Catalog object: command, table, field, script, help topic, artifact", "ENGINE", "OBJID"),
    ("DDATTR", "Flexible object attributes from evidence", "ENGINE", "ATTRID"),
    ("DDEDGE", "Relationship between catalog objects", "ENGINE", "EDGEID"),
    ("DDEVID", "Evidence row linking catalog objects to source/proof artifacts", "ENGINE", "EVID"),
    ("DDGATE", "Gate/check result rows", "ENGINE", "GATEID"),
    ("DDREVIEW", "Review, triage, disposition, and promotion-readiness rows", "ENGINE", "REVID"),
    ("DDARTIF", "Generated/accepted artifact inventory", "ENGINE", "ARTID"),
    ("DDPROFILE", "Profile/scope boundary rows", "ENGINE", "PROFID"),
]

GATES = [
    ("CATALOG_DEFINITION_REVIEWED", "Catalog DBF/DDL definition reviewed", "REQUIRED_BEFORE_DBF_WRITE"),
    ("SANDBOX_PATH_CONFIRMED", "Sandbox path confirmed", "REQUIRED_BEFORE_DBF_WRITE"),
    ("ROW_PROJECTION_DRY_RUN_GREEN", "Rows projected with exact counts and no blocking conflicts", "REQUIRED_BEFORE_DBF_WRITE"),
    ("WRITE_AUTHORIZED", "User explicitly authorizes sandbox DBF creation", "REQUIRED_BEFORE_DBF_WRITE"),
    ("READBACK_VALIDATED", "DBF readback matches projected rows and hashes", "REQUIRED_BEFORE_PROMOTION"),
    ("PROMOTION_AUTHORIZED", "User explicitly authorizes promotion from sandbox to active catalog", "REQUIRED_BEFORE_PROMOTION"),
]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv_dict(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-039 report-only catalog DBF/DDL definition planner")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD039-catalog-dbfdll-definition-plan")
    ap.add_argument("--baseline", default="DDBASE-stable-v2")
    ap.add_argument("--sandbox-path", default="dottalkpp/data/metadata/datadict_sandbox")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    table_rows = [
        {"table": t, "purpose": purpose, "profile": profile, "primary_key": pk, "write_allowed_dd039": 0}
        for t, purpose, profile, pk in TABLES
    ]
    gate_rows = [
        {"gate": g, "requirement": req, "stage": stage, "satisfied_dd039": 0}
        for g, req, stage in GATES
    ]
    terminology_rows = [
        {"term": "WORKSPACE", "use": "live/open area/session behavior", "avoid_confusion": "not DDL definition"},
        {"term": "DDL", "use": "table/field/index structural definition", "avoid_confusion": "not SQL schema namespace"},
        {"term": "catalog definition", "use": "Data Dictionary DBF layout definition", "avoid_confusion": "avoid generic schema wording"},
    ]

    write_csv_dict(out / "dd039_catalog_table_definition_plan_v0.csv", table_rows,
                   ["table", "purpose", "profile", "primary_key", "write_allowed_dd039"])
    write_csv_dict(out / "dd039_catalog_definition_gate_ledger_v0.csv", gate_rows,
                   ["gate", "requirement", "stage", "satisfied_dd039"])
    write_csv_dict(out / "dd039_terminology_boundary_v0.csv", terminology_rows,
                   ["term", "use", "avoid_confusion"])

    status = "CATALOG_DBF_DDL_DEFINITION_PLAN_READY"
    manifest = {
        "contract": "dd039_catalog_dbf_ddl_definition_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(Path(args.repo_root).resolve()),
        "baseline": args.baseline,
        "sandbox_path": args.sandbox_path,
        "active_path_future": args.active_path,
        "profiles": args.profile,
        "catalog_tables_planned": len(table_rows),
        "dbf_write_authorized": 0,
        "dbf_tables_created": 0,
        "dbf_rows_written": 0,
        "protected_system_mutations": 0,
        "next_recommended_package": "DD-040 Catalog Row Projection Dry-Run",
    }
    write_json(out / "dd039_catalog_dbf_ddl_definition_manifest.json", manifest)

    report = f"""# DD-039 Catalog DBF/DDL Definition Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Terminology boundary

- `WORKSPACE` means live/open area/session behavior.
- `DDL` means structural table/field/index definition.
- This package uses `catalog definition`, `DBF layout definition`, `table definition`, and `field definition`.
- This package intentionally avoids user-facing `schema` wording.

## Planned catalog DBFs

Planned table count: **{len(table_rows)}**

Primary tables:
- DDRUN
- DDBASE
- DDSOURCE
- DDOBJECT
- DDATTR
- DDEDGE
- DDEVID
- DDGATE
- DDREVIEW
- DDARTIF
- DDPROFILE

## Paths

Sandbox catalog path:

```text
{args.sandbox_path}
```

Future active catalog path, only after promotion authorization:

```text
{args.active_path}
```

## Boundary

DD-039 is report-only. It does not create DBFs, write rows, run builds,
launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data,
or promote dictionary facts.

## Next

DD-040 should project exact candidate rows from the accepted baseline and current
redocumentation manifests without writing DBFs.
"""
    (out / "DD039_CATALOG_DBF_DDL_DEFINITION_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-039 catalog DBF/DDL definition manifest: {out / 'dd039_catalog_dbf_ddl_definition_manifest.json'}")
    print(f"status: {status}; tables: {len(table_rows)}; dbf_write_authorized: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
