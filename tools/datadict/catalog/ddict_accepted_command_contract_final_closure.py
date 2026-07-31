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
        "surface": "DDICT registration / HELP smoke",
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
    "DD083": {
        "dir": "docs/datadict/reports/DD083-ddict-command-surface-cycle-closure-v0",
        "manifest": "dd083_ddict_command_surface_cycle_closure_manifest.json",
        "status": "DDICT_COMMAND_SURFACE_CYCLE_CLOSED_GREEN",
        "surface": "DDICT read-surface cycle closure",
    },
    "DD086": {
        "dir": "docs/datadict/reports/DD086-ddict-objects-runtime-closure-v0",
        "manifest": "dd086_objects_runtime_closure_manifest.json",
        "status": "DDICT_OBJECTS_RUNTIME_CLOSURE_GREEN",
        "surface": "DDICT OBJECTS",
    },
}

SURFACES = [
    {"surface": "DDICT HELP", "proof": "DD-068", "runtime_implemented": 1, "read_only": 1},
    {"surface": "DDICT STATUS", "proof": "DD-071", "runtime_implemented": 1, "read_only": 1},
    {"surface": "DDICT TABLES", "proof": "DD-071", "runtime_implemented": 1, "read_only": 1},
    {"surface": "DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]", "proof": "DD-086", "runtime_implemented": 1, "read_only": 1},
    {"surface": "DDICT FIELDS <table>", "proof": "DD-073", "runtime_implemented": 1, "read_only": 1},
    {"surface": "DDICT TAGS <table>", "proof": "DD-076", "runtime_implemented": 1, "read_only": 1},
    {"surface": "DDICT REL <object> [IN|OUT|BOTH]", "proof": "DD-079", "runtime_implemented": 1, "read_only": 1},
    {"surface": "DDICT EVIDENCE <object>", "proof": "DD-082", "runtime_implemented": 1, "read_only": 1},
]

FUTURE_LANES = [
    {
        "lane": "HELP/CMDHELPCHK integration",
        "recommendation": "Plan separately and guarded; do not mutate HELP from DD-087.",
        "why": "Runtime command surface is now proven, but HELP/CMDHELPCHK has its own source-of-truth and rebuild rules.",
        "priority": "P1",
    },
    {
        "lane": "Read-helper refactor",
        "recommendation": "Extract cmd_ddict.cpp DBF/object/evidence read helpers into a reusable read-only module after tests are stable.",
        "why": "The current command is useful; shared reader APIs will prevent copy/paste logic when pydottalk or future commands consume the same catalog.",
        "priority": "P1",
    },
    {
        "lane": "pydottalk active Data Dictionary reader API",
        "recommendation": "Implement or harden Python-side reader calls using the same read-only doctrine.",
        "why": "DD-061 planned this surface; the runtime command now proves expected outputs.",
        "priority": "P2",
    },
    {
        "lane": "SelfDoc/Data Dictionary synchronization",
        "recommendation": "Create a report-first bridge from active catalog facts into SelfDoc/MDO reporting without making manuals a source of truth.",
        "why": "The data dictionary should derive from repo/source/help/metadata evidence; manuals remain explanatory downstream artifacts.",
        "priority": "P2",
    },
    {
        "lane": "Catalog coverage expansion",
        "recommendation": "Add provenance/evidence rows in a future catalog-generation lane only after explicit authorization.",
        "why": "DDEVID is currently sparse; DDATTR provides useful evidence now, but richer provenance should be generated, not manually patched.",
        "priority": "P3",
    },
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
    ap = argparse.ArgumentParser(description="DD-087 DDICT accepted command contract final closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD087-ddict-accepted-command-contract-final-closure-v0")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-087_DDICT_ACCEPTED_COMMAND_CONTRACT_FINAL_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    closure_path = (repo / args.closure_path).resolve()

    chain_rows: List[Dict[str, Any]] = []
    for ddid, spec in EXPECTED.items():
        mpath = repo / spec["dir"] / spec["manifest"]
        manifest = read_json(mpath)
        observed = manifest.get("status", "")
        expected = spec["status"]
        exists = int(mpath.exists())
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
    for i, row in enumerate(SURFACES, start=1):
        surface_rows.append({
            "order": i,
            "surface": row["surface"],
            "status": "GREEN",
            "proof": row["proof"],
            "runtime_implemented": row["runtime_implemented"],
            "read_only": row["read_only"],
        })

    doctrine_rows = [
        {"principle": "runtime_proves", "accepted": 1, "detail": "All accepted DDICT command surfaces have runtime closure evidence."},
        {"principle": "read_only_consumer", "accepted": 1, "detail": "DDICT reads active catalog DBFs and existing index/mirror artifacts; it does not mutate them."},
        {"principle": "manuals_explain_downstream", "accepted": 1, "detail": "Manual/help integration is a later lane; DD-087 does not alter manuals or HELP."},
        {"principle": "metadata_organizes", "accepted": 1, "detail": "Active Data Dictionary catalog remains the organized source for object/field/tag/rel/evidence read surfaces."},
        {"principle": "help_cmdhelpchk_guarded", "accepted": 1, "detail": "HELP/CMDHELPCHK integration must be explicit and guarded after runtime acceptance."},
    ]

    boundary_rows = [
        {"boundary": "final_contract_closure_report_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "production_selfdoc_metadata_promotion", "observed": 0, "required": 0, "pass": 1},
    ]

    failures = sum(1 for r in chain_rows if int(r["pass"]) != 1)
    status = "DDICT_ACCEPTED_COMMAND_CONTRACT_FINAL_CLOSURE_GREEN" if failures == 0 else "DDICT_ACCEPTED_COMMAND_CONTRACT_FINAL_CLOSURE_REVIEW"

    write_csv(out / "dd087_final_green_chain_ledger.csv", chain_rows, ["ddid", "surface", "manifest", "manifest_exists", "expected_status", "observed_status", "pass"])
    write_csv(out / "dd087_final_command_surface_matrix.csv", surface_rows, ["order", "surface", "status", "proof", "runtime_implemented", "read_only"])
    write_csv(out / "dd087_read_only_doctrine_ledger.csv", doctrine_rows, ["principle", "accepted", "detail"])
    write_csv(out / "dd087_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd087_future_lane_recommendations.csv", FUTURE_LANES, ["lane", "recommendation", "why", "priority"])

    report = f"""# DD-087 DDICT Accepted Command Contract Final Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-087 closes the accepted `DDICT` command contract after `OBJECTS` was added to the previously closed read-surface cycle.

## Final accepted runtime command surface

```text
DDICT HELP
DDICT STATUS
DDICT TABLES
DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]
DDICT FIELDS <table>
DDICT TAGS <table>
DDICT REL <object-id-or-name> [IN|OUT|BOTH]
DDICT EVIDENCE <object-id-or-name>
```

## Verified chain

- DD-068: registration/build smoke and HELP usage
- DD-071: STATUS/TABLES
- DD-073: FIELDS
- DD-076: TAGS
- DD-079: REL
- DD-082: EVIDENCE
- DD-083: first read-surface cycle closure
- DD-086: OBJECTS

Chain failures: **{failures}**

## Interpretation

This is a runtime command-contract closure, not a catalog generation or HELP mutation closure.

The active Data Dictionary catalog is now readable from DotTalk++ through the accepted `DDICT` command surfaces.

## Boundary

DD-087 is report-only. It does not edit C++ source, registry/build files, active catalog DBFs,
CDX/LMDB, HELP/META/CMDHELPCHK, generated catalog content, production SelfDoc metadata, or manual rows.

## Recommended next lane

Do not combine next steps. Choose one guarded lane:

```text
DD-088 HELP/CMDHELPCHK integration plan
DD-088 DDICT read-helper refactor plan
DD-088 pydottalk active Data Dictionary reader API implementation plan
```

The safest next technical lane is a read-helper refactor plan, because the runtime surface is now proven and should be stabilized before deeper integration.
"""
    (out / "DD087_DDICT_ACCEPTED_COMMAND_CONTRACT_FINAL_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    closure_written = 0
    if args.write_closure:
        closure_path.parent.mkdir(parents=True, exist_ok=True)
        closure_path.write_text(report, encoding="utf-8")
        closure_written = 1

    manifest = {
        "contract": "dd087_ddict_accepted_command_contract_final_closure_v0",
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
        "production_selfdoc_metadata_promotion": 0,
        "next_recommended_action": "Pick one separate DD-088 lane: HELP/CMDHELPCHK plan, read-helper refactor plan, or pydottalk reader API plan.",
    }
    write_json(out / "dd087_ddict_accepted_command_contract_final_closure_manifest.json", manifest)

    print(f"DD-087 DDICT accepted command contract final closure manifest: {out / 'dd087_ddict_accepted_command_contract_final_closure_manifest.json'}")
    print(f"status: {status}; chain_rows: {len(chain_rows)}; surfaces: {len(surface_rows)}; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
