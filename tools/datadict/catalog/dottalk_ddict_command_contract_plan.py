#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List


COMMAND_CONTRACTS = [
    {
        "command_id": "DDICT_STATUS",
        "syntax": "DDICT STATUS",
        "purpose": "Show active Data Dictionary baseline, run, profile, artifact, and verification status.",
        "backing_tables": "DDRUN,DDBASE,DDPROFILE,DDGATE",
        "required_tags": "DDRUN.RUNID,DDBASE.BASEID,DDPROFILE.NAME,DDGATE.STATUS",
        "output_contract": "compact status report with baseline id, run id, profile names, gate status counts",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
        "implementation_phase": "DD-064_OR_LATER",
    },
    {
        "command_id": "DDICT_TABLES",
        "syntax": "DDICT TABLES",
        "purpose": "List active Data Dictionary catalog tables and row counts.",
        "backing_tables": "DDRUN,DDBASE,DDSOURCE,DDOBJECT,DDATTR,DDEDGE,DDEVID,DDGATE,DDREVIEW,DDARTIF,DDPROFILE",
        "required_tags": "natural/read-count path",
        "output_contract": "table name, records, fields, memo sidecar flag, index flag",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
        "implementation_phase": "DD-064_OR_LATER",
    },
    {
        "command_id": "DDICT_OBJECTS",
        "syntax": "DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]",
        "purpose": "Browse catalog objects such as tables, fields, tags, sources, artifacts, and evidence owners.",
        "backing_tables": "DDOBJECT,DDATTR,DDEDGE,DDPROFILE",
        "required_tags": "DDOBJECT.OBJID,DDOBJECT.OBJTYPE,DDATTR.OBJID,DDPROFILE.NAME",
        "output_contract": "object id, object type, name/logical name, profile visibility, status",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
        "implementation_phase": "DD-064_OR_LATER",
    },
    {
        "command_id": "DDICT_FIELDS",
        "syntax": "DDICT FIELDS <table>",
        "purpose": "Show field definitions for a catalog table/object.",
        "backing_tables": "DDOBJECT,DDEDGE,DDATTR",
        "required_tags": "DDOBJECT.OBJID,DDEDGE.FROMOBJ,DDEDGE.TOOBJ,DDATTR.OBJID,DDATTR.ATTRNAME",
        "output_contract": "field name, type, width, decimals, ordinal, memo flag, source evidence",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
        "implementation_phase": "DD-064_OR_LATER",
    },
    {
        "command_id": "DDICT_TAGS",
        "syntax": "DDICT TAGS <table>",
        "purpose": "Show tag/index definitions for a catalog table/object.",
        "backing_tables": "DDOBJECT,DDEDGE,DDATTR",
        "required_tags": "DDOBJECT.OBJID,DDEDGE.FROMOBJ,DDEDGE.TOOBJ,DDATTR.OBJID,DDATTR.ATTRNAME",
        "output_contract": "tag name, expression/field, source, CDX/LMDB status when available",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
        "implementation_phase": "DD-064_OR_LATER",
    },
    {
        "command_id": "DDICT_REL",
        "syntax": "DDICT REL <object-id-or-name> [IN|OUT|BOTH]",
        "purpose": "Show incoming and outgoing Data Dictionary relationship edges for an object.",
        "backing_tables": "DDEDGE,DDOBJECT",
        "required_tags": "DDEDGE.FROMOBJ,DDEDGE.TOOBJ,DDEDGE.EDGETYPE,DDOBJECT.OBJID",
        "output_contract": "direction, edge type, from object, to object, status",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P2",
        "implementation_phase": "DD-064_OR_LATER",
    },
    {
        "command_id": "DDICT_EVIDENCE",
        "syntax": "DDICT EVIDENCE <object-id-or-name>",
        "purpose": "Show provenance/evidence trace for a catalog object.",
        "backing_tables": "DDEVID,DDSOURCE,DDARTIF,DDATTR,DDOBJECT",
        "required_tags": "DDEVID.EVID,DDEVID.OBJID,DDEVID.SRCID,DDARTIF.ARTID,DDSOURCE.SRCID",
        "output_contract": "evidence id, source id, artifact, kind, note/memo excerpt",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P2",
        "implementation_phase": "DD-064_OR_LATER",
    },
    {
        "command_id": "DDICT_HELP",
        "syntax": "DDICT HELP | DDICT ?",
        "purpose": "Show DDICT command family usage without mutating HELP DATA.",
        "backing_tables": "none or generated command contract",
        "required_tags": "none",
        "output_contract": "usage text from command contract; not a HELP DATA mutation",
        "read_only": 1,
        "mutation_allowed": 0,
        "priority": "P1",
        "implementation_phase": "DD-064_OR_LATER",
    },
]

IMPLEMENTATION_GATES = [
    {
        "gate": "active_catalog_available",
        "expected": "DD060/61/62 green",
        "rationale": "DDICT commands must read an active promoted catalog, not regenerate it.",
    },
    {
        "gate": "read_only_runtime_path",
        "expected": "no append/replace/delete/pack/zap/buildlmdb",
        "rationale": "DDICT command family is a consumer of catalog truth, not a repair tool.",
    },
    {
        "gate": "engine_safe",
        "expected": "no LabTalk/student artifact dependency",
        "rationale": "x64base/DotTalk++ engine must operate without educational overlays.",
    },
    {
        "gate": "help_surface_report_first",
        "expected": "usage contracts generated as report artifacts before HELP mutation",
        "rationale": "HELP/META/CMDHELPCHK changes require a later guarded package.",
    },
    {
        "gate": "test_before_registration",
        "expected": "command tests specified before C++ registration",
        "rationale": "Avoid adding a command surface without runtime proof.",
    },
]

TEST_PLAN = [
    {
        "test_id": "DDICT_STATUS_SMOKE",
        "command": "DDICT STATUS",
        "expected": "prints active baseline/run/profile/gate status without mutation",
        "requires_catalog": 1,
        "priority": "P1",
    },
    {
        "test_id": "DDICT_TABLES_COUNTS",
        "command": "DDICT TABLES",
        "expected": "shows 11 catalog tables and known row counts",
        "requires_catalog": 1,
        "priority": "P1",
    },
    {
        "test_id": "DDICT_FIELDS_DDOBJECT",
        "command": "DDICT FIELDS DDOBJECT",
        "expected": "shows DDOBJECT field definitions from DDOBJECT/DDEDGE/DDATTR",
        "requires_catalog": 1,
        "priority": "P1",
    },
    {
        "test_id": "DDICT_TAGS_DDATTR",
        "command": "DDICT TAGS DDATTR",
        "expected": "shows DDATTR tags including OBJID and ATTRNAME",
        "requires_catalog": 1,
        "priority": "P1",
    },
    {
        "test_id": "DDICT_REL_DDOBJECT",
        "command": "DDICT REL DDOBJECT BOTH",
        "expected": "shows relationship edges for DDOBJECT",
        "requires_catalog": 1,
        "priority": "P2",
    },
    {
        "test_id": "DDICT_EVIDENCE_DDRUN",
        "command": "DDICT EVIDENCE DDRUN",
        "expected": "shows evidence/source trace or a clear no-evidence message",
        "requires_catalog": 1,
        "priority": "P2",
    },
    {
        "test_id": "DDICT_UNKNOWN_OBJECT",
        "command": "DDICT FIELDS NOSUCHTABLE",
        "expected": "clean not-found message, no exception, no mutation",
        "requires_catalog": 1,
        "priority": "P1",
    },
    {
        "test_id": "DDICT_USAGE",
        "command": "DDICT HELP",
        "expected": "shows usage for all DDICT subcommands",
        "requires_catalog": 0,
        "priority": "P1",
    },
]

HELP_CONTRACTS = [
    {
        "topic": "DDICT",
        "summary": "Read-only Data Dictionary command family.",
        "body_contract": "Explain read-only doctrine, active catalog prerequisite, and subcommands.",
        "help_mutation_authorized": 0,
    },
    {
        "topic": "DDICT STATUS",
        "summary": "Show active Data Dictionary status.",
        "body_contract": "Syntax, output fields, examples, no mutation note.",
        "help_mutation_authorized": 0,
    },
    {
        "topic": "DDICT TABLES",
        "summary": "List active Data Dictionary tables and counts.",
        "body_contract": "Syntax, row count meaning, examples.",
        "help_mutation_authorized": 0,
    },
    {
        "topic": "DDICT OBJECTS",
        "summary": "Browse Data Dictionary objects.",
        "body_contract": "Filters, object types, profile visibility.",
        "help_mutation_authorized": 0,
    },
    {
        "topic": "DDICT FIELDS",
        "summary": "Show field definitions.",
        "body_contract": "Table/object argument resolution and output contract.",
        "help_mutation_authorized": 0,
    },
    {
        "topic": "DDICT TAGS",
        "summary": "Show tag/index definitions.",
        "body_contract": "Tag name/expression/CDX/LMDB evidence contract.",
        "help_mutation_authorized": 0,
    },
    {
        "topic": "DDICT REL",
        "summary": "Show object relationships.",
        "body_contract": "IN/OUT/BOTH direction semantics.",
        "help_mutation_authorized": 0,
    },
    {
        "topic": "DDICT EVIDENCE",
        "summary": "Show provenance/evidence trace.",
        "body_contract": "Evidence/source/artifact relation and memo excerpt policy.",
        "help_mutation_authorized": 0,
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


def usage_contract_text() -> str:
    lines: List[str] = [
        "# DD-063 Candidate DDICT Usage Contracts",
        "",
        "These are report artifacts only. Do not apply to HELP DATA or source comments until a later guarded package authorizes it.",
        "",
    ]
    for c in COMMAND_CONTRACTS:
        lines.extend(
            [
                f"## {c['command_id']}",
                "",
                "```text",
                f"Syntax: {c['syntax']}",
                f"Purpose: {c['purpose']}",
                f"Read-only: {c['read_only']}",
                f"Mutation allowed: {c['mutation_allowed']}",
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def command_contract_markdown(status: str, dd062_status: str) -> str:
    lines = [
        "# DD-063 DotTalk++ DDICT Command Contract",
        "",
        f"Status: `{status}`",
        "",
        "## Prerequisite",
        "",
        "```text",
        f"DD-062: {dd062_status}",
        "Active Data Dictionary catalog promoted and read through pydottalk.",
        "```",
        "",
        "## Doctrine",
        "",
        "DDICT is a read-only command family. It consumes the active Data Dictionary catalog and must not repair, rebuild, or mutate it.",
        "",
        "Consumers may open active Data Dictionary DBFs, use existing CDX/LMDB indexes, resolve catalog objects, report relationships/evidence, and emit reports.",
        "",
        "Consumers may not append rows, replace rows, delete/pack/zap, create DBFs, rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, or automatically repair catalog content.",
        "",
        "## Command family",
        "",
    ]
    for c in COMMAND_CONTRACTS:
        lines.extend(
            [
                f"### {c['syntax']}",
                "",
                c["purpose"],
                "",
                f"- Backing tables: `{c['backing_tables']}`",
                f"- Required tags: `{c['required_tags']}`",
                f"- Output contract: {c['output_contract']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-063 report-only DotTalk++ DDICT command contract plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD063-dottalk-ddict-command-contract-plan-v0")
    ap.add_argument("--dd061-dir", default="docs/datadict/reports/DD061-active-datadict-consumer-read-api-plan-v1_1")
    ap.add_argument("--dd062-dir", default="docs/datadict/reports/DD062-pydottalk-readonly-helper-install-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd061_dir = (repo / args.dd061_dir).resolve()
    dd062_dir = (repo / args.dd062_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd061_manifest = read_json(dd061_dir / "dd061_active_datadict_consumer_read_api_plan_manifest.json")
    dd062_manifest = read_json(dd062_dir / "dd062_pydottalk_readonly_datadict_helper_manifest.json")

    dd061_ready = dd061_manifest.get("status") == "ACTIVE_DATADICT_CONSUMER_READ_API_PLAN_READY"
    dd062_ready = dd062_manifest.get("status") in {
        "PYDOTTALK_READONLY_DATADICT_HELPER_INSTALLED_AND_SMOKE_GREEN",
        "PYDOTTALK_READONLY_DATADICT_SMOKE_GREEN",
        "PYDOTTALK_READONLY_DATADICT_HELPER_INSTALLED",
    }

    gate_rows = [
        {
            "gate": "dd061_read_api_plan_ready",
            "expected": "ACTIVE_DATADICT_CONSUMER_READ_API_PLAN_READY",
            "observed": dd061_manifest.get("status", ""),
            "pass": int(dd061_ready),
        },
        {
            "gate": "dd062_readonly_helper_or_smoke_green",
            "expected": "PYDOTTALK_READONLY_DATADICT_HELPER_INSTALLED_AND_SMOKE_GREEN",
            "observed": dd062_manifest.get("status", ""),
            "pass": int(dd062_ready),
        },
        {
            "gate": "command_contracts_defined",
            "expected": ">=8",
            "observed": len(COMMAND_CONTRACTS),
            "pass": int(len(COMMAND_CONTRACTS) >= 8),
        },
        {
            "gate": "test_plan_defined",
            "expected": ">=8",
            "observed": len(TEST_PLAN),
            "pass": int(len(TEST_PLAN) >= 8),
        },
        {
            "gate": "help_contracts_report_only",
            "expected": 0,
            "observed": sum(int(r["help_mutation_authorized"]) for r in HELP_CONTRACTS),
            "pass": int(sum(int(r["help_mutation_authorized"]) for r in HELP_CONTRACTS) == 0),
        },
    ]

    boundary_rows = [
        {"boundary": "command_contract_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "runtime_command_registration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DOTTALK_DDICT_COMMAND_CONTRACT_PLAN_READY" if failures == 0 else "DOTTALK_DDICT_COMMAND_CONTRACT_PLAN_REVIEW"

    write_csv(out / "dd063_ddict_command_contracts.csv", COMMAND_CONTRACTS, [
        "command_id", "syntax", "purpose", "backing_tables", "required_tags",
        "output_contract", "read_only", "mutation_allowed", "priority", "implementation_phase",
    ])
    write_csv(out / "dd063_implementation_gates.csv", IMPLEMENTATION_GATES, ["gate", "expected", "rationale"])
    write_csv(out / "dd063_test_plan.csv", TEST_PLAN, ["test_id", "command", "expected", "requires_catalog", "priority"])
    write_csv(out / "dd063_help_contracts_report_only.csv", HELP_CONTRACTS, ["topic", "summary", "body_contract", "help_mutation_authorized"])
    write_csv(out / "dd063_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd063_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    (out / "DD063_DDICT_COMMAND_CONTRACT.md").write_text(command_contract_markdown(status, dd062_manifest.get("status", "")), encoding="utf-8")
    (out / "DD063_CANDIDATE_DDICT_USAGE_CONTRACTS.md").write_text(usage_contract_text(), encoding="utf-8")

    manifest = {
        "contract": "dd063_dottalk_ddict_command_contract_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd061_status": dd061_manifest.get("status", ""),
        "dd062_status": dd062_manifest.get("status", ""),
        "command_contracts": len(COMMAND_CONTRACTS),
        "implementation_gates": len(IMPLEMENTATION_GATES),
        "test_plan_rows": len(TEST_PLAN),
        "help_contract_rows": len(HELP_CONTRACTS),
        "failures": failures,
        "cxx_source_edits": 0,
        "runtime_command_registration": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-064 guarded runtime implementation plan or DD-063R command contract review/acceptance record.",
    }
    write_json(out / "dd063_dottalk_ddict_command_contract_plan_manifest.json", manifest)

    report = f"""# DD-063 DotTalk++ DDICT Command Contract Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-063 defines the report-only command contract for a future DotTalk++ `DDICT`
read-only command family.

## Inputs

- DD-061 status: `{dd061_manifest.get('status', '')}`
- DD-062 status: `{dd062_manifest.get('status', '')}`

## Contract counts

- Commands: **{len(COMMAND_CONTRACTS)}**
- Implementation gates: **{len(IMPLEMENTATION_GATES)}**
- Tests: **{len(TEST_PLAN)}**
- HELP contract rows: **{len(HELP_CONTRACTS)}**

## Boundary

DD-063 does not edit C++ source, register runtime commands, mutate the active
catalog, append/replace/delete/pack/zap DBFs, create/rebuild CDX or LMDB,
mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair rows.

## Next

DD-064 may implement the runtime command only after explicit authorization.
"""
    (out / "DD063_DOTTALK_DDICT_COMMAND_CONTRACT_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-063 DotTalk++ DDICT command contract manifest: {out / 'dd063_dottalk_ddict_command_contract_plan_manifest.json'}")
    print(f"status: {status}; commands: {len(COMMAND_CONTRACTS)}; tests: {len(TEST_PLAN)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
