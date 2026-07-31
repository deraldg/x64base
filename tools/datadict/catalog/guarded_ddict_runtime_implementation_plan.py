#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_ACCEPTED_STATUS = "DDICT_COMMAND_CONTRACT_ACCEPTED"

COMMANDS = [
    {"command_id": "DDICT_STATUS", "syntax": "DDICT STATUS", "phase": "P1"},
    {"command_id": "DDICT_TABLES", "syntax": "DDICT TABLES", "phase": "P1"},
    {"command_id": "DDICT_OBJECTS", "syntax": "DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]", "phase": "P1"},
    {"command_id": "DDICT_FIELDS", "syntax": "DDICT FIELDS <table>", "phase": "P1"},
    {"command_id": "DDICT_TAGS", "syntax": "DDICT TAGS <table>", "phase": "P1"},
    {"command_id": "DDICT_REL", "syntax": "DDICT REL <object-id-or-name> [IN|OUT|BOTH]", "phase": "P2"},
    {"command_id": "DDICT_EVIDENCE", "syntax": "DDICT EVIDENCE <object-id-or-name>", "phase": "P2"},
    {"command_id": "DDICT_HELP", "syntax": "DDICT HELP | DDICT ?", "phase": "P1"},
]

COMPONENTS = [
    {
        "component": "cmd_ddict.cpp",
        "kind": "new_runtime_command_file",
        "purpose": "Parse DDICT subcommands and call read-only service layer.",
        "default_action": "PLAN_ONLY",
        "implementation_auth_required": 1,
    },
    {
        "component": "cmd_ddict.hpp",
        "kind": "new_header_or_declaration",
        "purpose": "Expose DDICT command registration/entrypoint declarations if project pattern requires it.",
        "default_action": "PLAN_ONLY",
        "implementation_auth_required": 1,
    },
    {
        "component": "datadict_reader_runtime",
        "kind": "new_or_existing_service_layer",
        "purpose": "Runtime C++ read-only service for active Data Dictionary DBFs; no mutation methods.",
        "default_action": "PLAN_ONLY",
        "implementation_auth_required": 1,
    },
    {
        "component": "command_dispatch_registration",
        "kind": "existing_dispatcher_hook",
        "purpose": "Register DDICT top-level command after implementation and tests are ready.",
        "default_action": "PLAN_ONLY",
        "implementation_auth_required": 1,
    },
    {
        "component": "usage_contract_report",
        "kind": "generated_report_artifact",
        "purpose": "Stage DDICT usage text separate from HELP DATA until later HELP authorization.",
        "default_action": "REPORT_ONLY",
        "implementation_auth_required": 0,
    },
    {
        "component": "runtime_tests",
        "kind": "test_script_or_smoke",
        "purpose": "Prove DDICT commands execute read-only and match DD-063R accepted tests.",
        "default_action": "PLAN_ONLY",
        "implementation_auth_required": 1,
    },
]

SOURCE_SCAN_PATTERNS = [
    ("command_dispatch", r"\b(register|dispatch|command|cmd_)\b"),
    ("help_surface", r"\b(HELP|usage|USAGE|cmdhelp|CMDHELPCHK)\b"),
    ("use_command", r"\bUSE\b|cmd_use"),
    ("set_index_order", r"SET\s+INDEX|SET\s+ORDER|cmd_set"),
    ("list_count", r"\bLIST\b|\bCOUNT\b|cmd_list|cmd_count"),
    ("data_dictionary", r"DDICT|Data Dictionary|datadict|metadata"),
    ("dbarea_read", r"DbArea|recCount|fieldCount|goto|go\("),
]

SCAN_ROOTS = [
    "src",
    "include",
    "bindings",
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


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


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


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def scan_sources(repo: Path, max_rows: int = 500) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    files: List[Path] = []
    for root_name in SCAN_ROOTS:
        root = repo / root_name
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".cpp", ".hpp", ".h", ".cc", ".cxx", ".c"}:
                files.append(p)

    preferred_name_hits = [
        "cmd_", "command", "dispatch", "help", "use", "set", "list", "count", "area", "workspace", "metadata", "datadict"
    ]
    files.sort(key=lambda p: (
        0 if any(hit in p.name.lower() for hit in preferred_name_hits) else 1,
        p.as_posix().lower()
    ))

    compiled_patterns = [(name, re.compile(pattern, re.IGNORECASE)) for name, pattern in SOURCE_SCAN_PATTERNS]

    for p in files:
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for idx, line in enumerate(lines, start=1):
            hits = [name for name, rx in compiled_patterns if rx.search(line)]
            if not hits:
                continue
            rows.append({
                "path": safe_rel(repo, p),
                "line": idx,
                "hits": ",".join(hits),
                "text": line.strip()[:500],
                "implementation_relevance": classify_relevance(hits, p),
            })
            if len(rows) >= max_rows:
                return rows
    return rows


def classify_relevance(hits: List[str], path: Path) -> str:
    name = path.name.lower()
    if "dispatch" in ",".join(hits) or "cmd_" in name or "command" in name:
        return "COMMAND_HOOK_REVIEW"
    if "help" in name or "help_surface" in hits:
        return "HELP_SURFACE_REVIEW_ONLY"
    if "DbArea".lower() in ",".join(hits).lower() or "dbarea_read" in hits:
        return "READ_SERVICE_REVIEW"
    return "CONTEXT_REVIEW"


def implementation_stage_markdown(status: str, dd063r_status: str) -> str:
    lines = [
        "# DD-064 Guarded DDICT Runtime Implementation Plan",
        "",
        f"Status: `{status}`",
        "",
        "## Prerequisite",
        "",
        "```text",
        f"DD-063R: {dd063r_status}",
        "Accepted command family: 8 commands",
        "Accepted test baseline: 8 tests",
        "```",
        "",
        "## Plan",
        "",
        "DD-064 is a planning package only. It identifies likely runtime implementation targets and defines the implementation boundary for a future authorized package.",
        "",
        "## Read-only runtime doctrine",
        "",
        "The DDICT runtime command must only read the active Data Dictionary catalog. It must not append, replace, delete, pack, zap, create/rebuild CDX or LMDB, mutate HELP/META/CMDHELPCHK, or repair catalog content.",
        "",
        "## Proposed layers",
        "",
        "```text",
        "cmd_ddict.cpp / command entrypoint",
        "  parses DDICT subcommands",
        "  formats user-facing output",
        "",
        "datadict read-only service layer",
        "  opens active metadata/datadict DBFs",
        "  uses existing CDX/LMDB where available",
        "  exposes status/tables/objects/fields/tags/rel/evidence methods",
        "",
        "test harness",
        "  executes DD-063R accepted tests",
        "  verifies no mutation boundary",
        "```",
        "",
        "## Future implementation gate",
        "",
        "DD-065 or later may implement only after explicit authorization.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-064 report-only guarded runtime implementation plan for DDICT")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD064-guarded-ddict-runtime-implementation-plan-v0")
    ap.add_argument("--dd063r-dir", default="docs/datadict/reports/DD063R-ddict-command-contract-acceptance-final-v0")
    ap.add_argument("--scan-source", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd063r_dir = (repo / args.dd063r_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd063r_manifest = read_json(dd063r_dir / "dd063r_ddict_command_contract_acceptance_manifest.json")
    accepted_commands = read_csv_dict(dd063r_dir / "dd063r_accepted_command_family.csv")
    accepted_tests = read_csv_dict(dd063r_dir / "dd063r_accepted_test_baseline.csv")
    dd063r_ready = dd063r_manifest.get("status") == EXPECTED_ACCEPTED_STATUS
    accepted_commands_ok = len(accepted_commands) >= 8 and all(str(r.get("accepted", "")) == "1" for r in accepted_commands)
    accepted_tests_ok = len(accepted_tests) >= 8 and all(str(r.get("accepted", "")) == "1" for r in accepted_tests)

    source_rows = scan_sources(repo) if args.scan_source else []

    gate_rows = [
        {
            "gate": "dd063r_acceptance_green",
            "expected": EXPECTED_ACCEPTED_STATUS,
            "observed": dd063r_manifest.get("status", ""),
            "pass": int(dd063r_ready),
        },
        {
            "gate": "accepted_command_family_available",
            "expected": 8,
            "observed": len(accepted_commands),
            "pass": int(accepted_commands_ok),
        },
        {
            "gate": "accepted_test_baseline_available",
            "expected": 8,
            "observed": len(accepted_tests),
            "pass": int(accepted_tests_ok),
        },
        {
            "gate": "implementation_plan_report_only",
            "expected": 1,
            "observed": 1,
            "pass": 1,
        },
        {
            "gate": "source_scan_optional",
            "expected": "0 or >=1 if requested",
            "observed": len(source_rows),
            "pass": int((not args.scan_source) or len(source_rows) >= 1),
        },
    ]

    boundary_rows = [
        {"boundary": "runtime_implementation_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "new_source_files_created", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "runtime_command_registration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    service_rows = [
        {
            "service_method": "status()",
            "command": "DDICT STATUS",
            "tables": "DDRUN,DDBASE,DDPROFILE,DDGATE",
            "mutation_allowed": 0,
            "notes": "Return compact active catalog baseline/run/gate/profile status.",
        },
        {
            "service_method": "tables()",
            "command": "DDICT TABLES",
            "tables": "all DD* catalog tables",
            "mutation_allowed": 0,
            "notes": "Return row count and field count metadata.",
        },
        {
            "service_method": "objects(type, profile)",
            "command": "DDICT OBJECTS",
            "tables": "DDOBJECT,DDATTR,DDEDGE,DDPROFILE",
            "mutation_allowed": 0,
            "notes": "Profile filter is optional/read-only.",
        },
        {
            "service_method": "fields(table)",
            "command": "DDICT FIELDS",
            "tables": "DDOBJECT,DDEDGE,DDATTR",
            "mutation_allowed": 0,
            "notes": "Resolve table object then HAS_FIELD edges and field attributes.",
        },
        {
            "service_method": "tags(table)",
            "command": "DDICT TAGS",
            "tables": "DDOBJECT,DDEDGE,DDATTR",
            "mutation_allowed": 0,
            "notes": "Resolve table object then HAS_TAG/tag attributes; no CDX rebuild.",
        },
        {
            "service_method": "relationships(object, direction)",
            "command": "DDICT REL",
            "tables": "DDEDGE,DDOBJECT",
            "mutation_allowed": 0,
            "notes": "Read incoming/outgoing edges only.",
        },
        {
            "service_method": "evidence(object)",
            "command": "DDICT EVIDENCE",
            "tables": "DDEVID,DDSOURCE,DDARTIF,DDATTR,DDOBJECT",
            "mutation_allowed": 0,
            "notes": "Memo excerpts must be bounded; no evidence repair.",
        },
        {
            "service_method": "usage()",
            "command": "DDICT HELP",
            "tables": "compiled/report contract",
            "mutation_allowed": 0,
            "notes": "Usage surface only; no HELP DATA mutation in implementation package unless separately authorized.",
        },
    ]

    test_rows = []
    for r in accepted_tests:
        test_rows.append({
            "test_id": r.get("test_id", ""),
            "command": r.get("command", ""),
            "accepted_in_dd063r": r.get("accepted", ""),
            "implementation_phase": "DD-065_OR_LATER_AUTH_REQUIRED",
            "expected_boundary": "NO_MUTATION",
        })

    help_rows = [
        {
            "surface": "runtime_usage_text",
            "source": "DD-063R accepted usage contract",
            "allowed_in_dd064": 1,
            "help_data_mutation": 0,
            "notes": "May be staged as report text only.",
        },
        {
            "surface": "HELP DATA integration",
            "source": "future guarded HELP package",
            "allowed_in_dd064": 0,
            "help_data_mutation": 0,
            "notes": "Not authorized by DD-064 plan.",
        },
        {
            "surface": "CMDHELPCHK update",
            "source": "future guarded help validation package",
            "allowed_in_dd064": 0,
            "help_data_mutation": 0,
            "notes": "Not authorized by DD-064 plan.",
        },
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_GUARDED_RUNTIME_IMPLEMENTATION_PLAN_READY" if failures == 0 else "DDICT_GUARDED_RUNTIME_IMPLEMENTATION_PLAN_REVIEW"

    write_csv(out / "dd064_component_plan.csv", COMPONENTS, [
        "component", "kind", "purpose", "default_action", "implementation_auth_required",
    ])
    write_csv(out / "dd064_command_implementation_map.csv", [
        {
            "command_id": c["command_id"],
            "syntax": c["syntax"],
            "implementation_phase": "DD-065_OR_LATER_AUTH_REQUIRED",
            "runtime_registered_by_dd064": 0,
            "source_edited_by_dd064": 0,
        }
        for c in COMMANDS
    ], ["command_id", "syntax", "implementation_phase", "runtime_registered_by_dd064", "source_edited_by_dd064"])
    write_csv(out / "dd064_readonly_service_contract.csv", service_rows, [
        "service_method", "command", "tables", "mutation_allowed", "notes",
    ])
    write_csv(out / "dd064_runtime_test_plan.csv", test_rows, [
        "test_id", "command", "accepted_in_dd063r", "implementation_phase", "expected_boundary",
    ])
    write_csv(out / "dd064_help_usage_staging_plan.csv", help_rows, [
        "surface", "source", "allowed_in_dd064", "help_data_mutation", "notes",
    ])
    write_csv(out / "dd064_source_hook_inventory.csv", source_rows, [
        "path", "line", "hits", "text", "implementation_relevance",
    ])
    write_csv(out / "dd064_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd064_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    (out / "DD064_DDICT_GUARDED_RUNTIME_IMPLEMENTATION_PLAN.md").write_text(
        implementation_stage_markdown(status, dd063r_manifest.get("status", "")),
        encoding="utf-8",
    )

    manifest = {
        "contract": "dd064_guarded_ddict_runtime_implementation_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd063r_status": dd063r_manifest.get("status", ""),
        "commands": len(COMMANDS),
        "components": len(COMPONENTS),
        "service_methods": len(service_rows),
        "runtime_tests": len(test_rows),
        "source_scan_requested": int(args.scan_source),
        "source_hook_rows": len(source_rows),
        "failures": failures,
        "cxx_source_edits": 0,
        "new_source_files_created": 0,
        "runtime_command_registration": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-065 guarded DDICT runtime implementation package only after explicit authorization.",
    }
    write_json(out / "dd064_guarded_ddict_runtime_implementation_plan_manifest.json", manifest)

    report = f"""# DD-064 Guarded DDICT Runtime Implementation Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-064 plans a future guarded runtime implementation of the accepted `DDICT`
command family. It does not implement it.

## Inputs

- DD-063R status: `{dd063r_manifest.get('status', '')}`
- Accepted commands: **{len(accepted_commands)}**
- Accepted tests: **{len(accepted_tests)}**

## Plan outputs

- Components: **{len(COMPONENTS)}**
- Command implementation rows: **{len(COMMANDS)}**
- Read-only service methods: **{len(service_rows)}**
- Runtime tests: **{len(test_rows)}**
- Source hook inventory rows: **{len(source_rows)}**

## Boundary

DD-064 does not edit C++ source, create source files, register runtime commands,
mutate the active catalog, append/replace/delete/pack/zap DBFs, rebuild CDX or
LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair rows.

## Next

DD-065 may implement only after explicit authorization.
"""
    (out / "DD064_GUARDED_DDICT_RUNTIME_IMPLEMENTATION_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-064 guarded DDICT runtime implementation plan manifest: {out / 'dd064_guarded_ddict_runtime_implementation_plan_manifest.json'}")
    print(f"status: {status}; components: {len(COMPONENTS)}; tests: {len(test_rows)}; source_hooks: {len(source_rows)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
