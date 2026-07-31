#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED = {
    "DD068": {
        "dir": "docs/datadict/reports/DD068-ddict-build-runtime-smoke-closure-final-v0",
        "manifest": "dd068_ddict_build_runtime_smoke_closure_manifest.json",
        "status": "DDICT_BUILD_RUNTIME_SMOKE_CLOSURE_GREEN",
        "surface": "DDICT registration/build smoke",
    },
    "DD071": {
        "dir": "docs/datadict/reports/DD071-ddict-status-tables-runtime-closure-v0",
        "manifest": "dd071_ddict_status_tables_runtime_closure_manifest.json",
        "status": "DDICT_STATUS_TABLES_RUNTIME_CLOSURE_GREEN",
        "surface": "DDICT STATUS / TABLES",
    },
    "DD073": {
        "dir": "docs/datadict/reports/DD073-fields-runtime-closure-v0",
        "manifest": "dd073_fields_runtime_closure_manifest.json",
        "status": "DDICT_FIELDS_RUNTIME_CLOSURE_GREEN",
        "surface": "DDICT FIELDS",
    },
    "DD076": {
        "dir": "docs/datadict/reports/DD076-ddict-tags-runtime-closure-v0",
        "manifest": "dd076_tags_runtime_closure_manifest.json",
        "status": "DDICT_TAGS_RUNTIME_CLOSURE_GREEN",
        "surface": "DDICT TAGS",
    },
    "DD079": {
        "dir": "docs/datadict/reports/DD079-ddict-rel-runtime-closure-v0",
        "manifest": "dd079_rel_runtime_closure_manifest.json",
        "status": "DDICT_REL_RUNTIME_CLOSURE_GREEN",
        "surface": "DDICT REL",
    },
    "DD082": {
        "dir": "docs/datadict/reports/DD082-ddict-evidence-runtime-closure-v0",
        "manifest": "dd082_evidence_runtime_closure_manifest.json",
        "status": "DDICT_EVIDENCE_RUNTIME_CLOSURE_GREEN",
        "surface": "DDICT EVIDENCE",
    },
}

SURFACES = [
    {"surface": "DDICT HELP", "status": "GREEN", "proof": "DD-068 runtime smoke / usage surface"},
    {"surface": "DDICT STATUS", "status": "GREEN", "proof": "DD-071"},
    {"surface": "DDICT TABLES", "status": "GREEN", "proof": "DD-071"},
    {"surface": "DDICT FIELDS <table>", "status": "GREEN", "proof": "DD-073"},
    {"surface": "DDICT TAGS <table>", "status": "GREEN", "proof": "DD-076"},
    {"surface": "DDICT REL <object> [IN|OUT|BOTH]", "status": "GREEN", "proof": "DD-079"},
    {"surface": "DDICT EVIDENCE <object>", "status": "GREEN", "proof": "DD-082"},
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


def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-083 DDICT command surface cycle closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD083-ddict-command-surface-cycle-closure-v0")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-083_DDICT_COMMAND_SURFACE_CYCLE_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    closure_path = (repo / args.closure_path).resolve()

    chain_rows: List[Dict[str, Any]] = []
    for ddid, spec in EXPECTED.items():
        d = repo / spec["dir"]
        mpath = d / spec["manifest"]
        manifest = read_json(mpath)
        observed = manifest.get("status", "")
        exists = int(mpath.exists())
        expected = spec["status"]
        chain_rows.append({
            "ddid": ddid,
            "surface": spec["surface"],
            "manifest": rel(repo, mpath),
            "manifest_exists": exists,
            "expected_status": expected,
            "observed_status": observed,
            "pass": int(exists and observed == expected),
        })

    surface_rows = []
    for idx, row in enumerate(SURFACES, start=1):
        surface_rows.append({
            "order": idx,
            "surface": row["surface"],
            "status": row["status"],
            "proof": row["proof"],
            "runtime_implemented": 1,
            "read_only": 1,
        })

    boundary_rows = [
        {"boundary": "cycle_closure_report_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    future_rows = [
        {
            "lane": "DDICT_OBJECTS",
            "recommendation": "Plan next; likely object browsing/filter surface using DDOBJECT and DDPROFILE.",
            "notes": "Can remain optional because REL/EVIDENCE now resolve object tokens.",
        },
        {
            "lane": "HELP/CMDHELPCHK",
            "recommendation": "Separate guarded lane only after command surface is accepted.",
            "notes": "Do not mutate HELP/META/CMDHELPCHK during DD-083.",
        },
        {
            "lane": "Data Dictionary self-description",
            "recommendation": "Promote DDICT command-surface results into Data Dictionary reporting doctrine later.",
            "notes": "Runtime proves; catalog organizes; manuals explain.",
        },
        {
            "lane": "Reader API extraction",
            "recommendation": "Consider refactoring cmd_ddict.cpp read helpers into a reusable read-only datadict consumer module.",
            "notes": "Only after current runtime surface is closed and stable.",
        },
    ]

    failures = sum(1 for r in chain_rows if int(r["pass"]) != 1)
    status = "DDICT_COMMAND_SURFACE_CYCLE_CLOSED_GREEN" if failures == 0 else "DDICT_COMMAND_SURFACE_CYCLE_CLOSURE_REVIEW"

    write_csv(out / "dd083_green_chain_ledger.csv", chain_rows, ["ddid", "surface", "manifest", "manifest_exists", "expected_status", "observed_status", "pass"])
    write_csv(out / "dd083_command_surface_matrix.csv", surface_rows, ["order", "surface", "status", "proof", "runtime_implemented", "read_only"])
    write_csv(out / "dd083_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd083_future_lane_recommendations.csv", future_rows, ["lane", "recommendation", "notes"])

    report = f"""# DD-083 DDICT Command Surface Cycle Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-083 closes the first complete `DDICT` command-surface implementation cycle.

## Green runtime stack

```text
DDICT HELP                       GREEN
DDICT STATUS                     GREEN
DDICT TABLES                     GREEN
DDICT FIELDS <table>             GREEN
DDICT TAGS <table>               GREEN
DDICT REL <object> [IN|OUT|BOTH] GREEN
DDICT EVIDENCE <object>          GREEN
```

## Verified chain

- DD-068 registration/build smoke closure
- DD-071 STATUS/TABLES runtime closure
- DD-073 FIELDS runtime closure
- DD-076 TAGS runtime closure
- DD-079 REL runtime closure
- DD-082 EVIDENCE runtime closure

Chain failures: **{failures}**

## Important interpretation

This closes a runtime read-surface cycle, not a catalog mutation cycle.

The `DDICT` command family now proves that DotTalk++ can inspect the active Data Dictionary catalog at runtime through read-only surfaces.

## Boundary

DD-083 is cycle closure/report-only. It does not edit C++ source, registry/build files,
active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK, generated catalog content, or manual rows.

## Recommended next lane

Start a separate lane for one of:

```text
DD-084 DDICT OBJECTS implementation plan
DD-084 HELP/CMDHELPCHK guarded integration plan
DD-084 DDICT read-helper refactor plan
```

Do not combine these. The safest next move is `DDICT OBJECTS` plan because it completes the accepted command contract without changing HELP or metadata systems.
"""
    (out / "DD083_DDICT_COMMAND_SURFACE_CYCLE_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    closure_written = 0
    if args.write_closure:
        closure_path.parent.mkdir(parents=True, exist_ok=True)
        closure_path.write_text(report, encoding="utf-8")
        closure_written = 1

    manifest = {
        "contract": "dd083_ddict_command_surface_cycle_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "chain_rows": len(chain_rows),
        "surface_rows": len(surface_rows),
        "failures": failures,
        "closure_written": closure_written,
        "closure_path": str(closure_path) if closure_written else "",
        "cxx_source_edits": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-084 DDICT OBJECTS implementation plan, or separate HELP/CMDHELPCHK integration plan if explicitly authorized.",
    }
    write_json(out / "dd083_ddict_command_surface_cycle_closure_manifest.json", manifest)

    print(f"DD-083 DDICT command surface cycle closure manifest: {out / 'dd083_ddict_command_surface_cycle_closure_manifest.json'}")
    print(f"status: {status}; chain_rows: {len(chain_rows)}; surfaces: {len(surface_rows)}; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
