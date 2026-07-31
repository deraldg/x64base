#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_COMMANDS = [
    "DDICT STATUS",
    "DDICT TABLES",
    "DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]",
    "DDICT FIELDS <table>",
    "DDICT TAGS <table>",
    "DDICT REL <object-id-or-name> [IN|OUT|BOTH]",
    "DDICT EVIDENCE <object-id-or-name>",
    "DDICT HELP | DDICT ?",
]

EXPECTED_TESTS = [
    "DDICT_STATUS_SMOKE",
    "DDICT_TABLES_COUNTS",
    "DDICT_FIELDS_DDOBJECT",
    "DDICT_TAGS_DDATTR",
    "DDICT_REL_DDOBJECT",
    "DDICT_EVIDENCE_DDRUN",
    "DDICT_UNKNOWN_OBJECT",
    "DDICT_USAGE",
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


def acceptance_markdown(run_id: str, dd063_status: str, command_rows: List[Dict[str, str]], test_rows: List[Dict[str, str]]) -> str:
    command_lines = "\n".join(f"- `{r.get('syntax', '')}`" for r in command_rows)
    test_lines = "\n".join(f"- `{r.get('test_id', '')}` — {r.get('command', '')}" for r in test_rows)
    return f"""# DD-063R DDICT Command Contract Acceptance Record

Run id: `{run_id}`
Created UTC: `{utc_now()}`

## Acceptance

The DD-063 DotTalk++ `DDICT` command contract is accepted as the implementation
baseline for a later guarded runtime implementation package.

Accepted prerequisite:

```text
DD-063: {dd063_status}
```

## Accepted command family

{command_lines}

## Accepted runtime test baseline

{test_lines}

## Read-only doctrine

The accepted `DDICT` command family is read-only.

It may:

```text
open active Data Dictionary DBFs
use existing CDX/LMDB indexes
resolve catalog objects, fields, tags, relationships, evidence, profiles, and status
emit reports
```

It may not:

```text
append rows
replace rows
delete/pack/zap
create DBFs
create/rebuild CDX or LMDB
mutate HELP/META/CMDHELPCHK
repair catalog content automatically
```

## Boundary

DD-063R is an acceptance record only. It does not edit C++ source, register
runtime commands, mutate the active catalog, mutate HELP/META/CMDHELPCHK,
regenerate catalog content, or repair rows.

## Next

DD-064 may plan guarded runtime implementation, but runtime implementation still
requires explicit authorization.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-063R report-only DDICT command contract acceptance record")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD063R-ddict-command-contract-acceptance-v0")
    ap.add_argument("--dd063-dir", default="docs/datadict/reports/DD063-dottalk-ddict-command-contract-plan-v0")
    ap.add_argument("--write-acceptance", action="store_true")
    ap.add_argument("--acceptance-path", default="docs/datadict/runlog/DD-063R_DDICT_COMMAND_CONTRACT_ACCEPTANCE_RECORD.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd063_dir = (repo / args.dd063_dir).resolve()
    acceptance_path = (repo / args.acceptance_path).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd063_manifest = read_json(dd063_dir / "dd063_dottalk_ddict_command_contract_plan_manifest.json")
    command_rows = read_csv_dict(dd063_dir / "dd063_ddict_command_contracts.csv")
    test_rows = read_csv_dict(dd063_dir / "dd063_test_plan.csv")
    boundary_rows_in = read_csv_dict(dd063_dir / "dd063_no_mutation_boundary_ledger.csv")
    help_rows = read_csv_dict(dd063_dir / "dd063_help_contracts_report_only.csv")

    dd063_ready = dd063_manifest.get("status") == "DOTTALK_DDICT_COMMAND_CONTRACT_PLAN_READY"
    observed_commands = [r.get("syntax", "") for r in command_rows]
    observed_tests = [r.get("test_id", "") for r in test_rows]
    command_set_ok = all(cmd in observed_commands for cmd in EXPECTED_COMMANDS) and len(command_rows) >= 8
    test_set_ok = all(test in observed_tests for test in EXPECTED_TESTS) and len(test_rows) >= 8
    boundary_ok = bool(boundary_rows_in) and all(str(r.get("pass", "")).strip() == "1" for r in boundary_rows_in)
    help_report_only_ok = bool(help_rows) and all(str(r.get("help_mutation_authorized", "")).strip() == "0" for r in help_rows)

    acceptance_written = 0
    if args.write_acceptance:
        acceptance_path.parent.mkdir(parents=True, exist_ok=True)
        acceptance_path.write_text(acceptance_markdown(args.run_id, dd063_manifest.get("status", ""), command_rows, test_rows), encoding="utf-8")
        acceptance_written = 1

    gate_rows = [
        {
            "gate": "dd063_command_contract_plan_ready",
            "expected": "DOTTALK_DDICT_COMMAND_CONTRACT_PLAN_READY",
            "observed": dd063_manifest.get("status", ""),
            "pass": int(dd063_ready),
        },
        {
            "gate": "accepted_command_family_complete",
            "expected": len(EXPECTED_COMMANDS),
            "observed": len(command_rows),
            "pass": int(command_set_ok),
        },
        {
            "gate": "accepted_test_baseline_complete",
            "expected": len(EXPECTED_TESTS),
            "observed": len(test_rows),
            "pass": int(test_set_ok),
        },
        {
            "gate": "dd063_boundary_clean",
            "expected": 1,
            "observed": int(boundary_ok),
            "pass": int(boundary_ok),
        },
        {
            "gate": "help_contracts_report_only",
            "expected": 1,
            "observed": int(help_report_only_ok),
            "pass": int(help_report_only_ok),
        },
        {
            "gate": "acceptance_written_when_requested",
            "expected": int(args.write_acceptance),
            "observed": acceptance_written,
            "pass": int((not args.write_acceptance) or acceptance_written == 1),
        },
    ]

    boundary_rows = [
        {"boundary": "acceptance_record_only", "observed": 1, "required": 1, "pass": 1},
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
    status = "DDICT_COMMAND_CONTRACT_ACCEPTED" if failures == 0 else "DDICT_COMMAND_CONTRACT_ACCEPTANCE_REVIEW"

    accepted_command_rows = []
    for r in command_rows:
        accepted_command_rows.append({
            "command_id": r.get("command_id", ""),
            "syntax": r.get("syntax", ""),
            "accepted": 1,
            "read_only": r.get("read_only", ""),
            "mutation_allowed": r.get("mutation_allowed", ""),
            "implementation_phase": "DD-064_OR_LATER_AUTH_REQUIRED",
        })

    accepted_test_rows = []
    for r in test_rows:
        accepted_test_rows.append({
            "test_id": r.get("test_id", ""),
            "command": r.get("command", ""),
            "accepted": 1,
            "priority": r.get("priority", ""),
            "implementation_phase": "DD-064_OR_LATER_AUTH_REQUIRED",
        })

    write_csv(out / "dd063r_accepted_command_family.csv", accepted_command_rows, [
        "command_id", "syntax", "accepted", "read_only", "mutation_allowed", "implementation_phase",
    ])
    write_csv(out / "dd063r_accepted_test_baseline.csv", accepted_test_rows, [
        "test_id", "command", "accepted", "priority", "implementation_phase",
    ])
    write_csv(out / "dd063r_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd063r_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    (out / "DD063R_DDICT_COMMAND_CONTRACT_ACCEPTANCE_RECORD.md").write_text(
        acceptance_markdown(args.run_id, dd063_manifest.get("status", ""), command_rows, test_rows),
        encoding="utf-8",
    )

    manifest = {
        "contract": "dd063r_ddict_command_contract_acceptance_record_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd063_status": dd063_manifest.get("status", ""),
        "accepted_commands": len(accepted_command_rows),
        "accepted_tests": len(accepted_test_rows),
        "acceptance_written": acceptance_written,
        "acceptance_path": str(acceptance_path) if acceptance_written else "",
        "failures": failures,
        "cxx_source_edits": 0,
        "runtime_command_registration": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-064 guarded runtime implementation plan; implementation still requires explicit authorization.",
    }
    write_json(out / "dd063r_ddict_command_contract_acceptance_manifest.json", manifest)

    report = f"""# DD-063R DDICT Command Contract Acceptance Record

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-063R formally accepts the DD-063 DotTalk++ `DDICT` command contract as the
baseline for a later guarded runtime implementation package.

## Accepted baseline

- DD-063 status: `{dd063_manifest.get('status', '')}`
- Accepted commands: **{len(accepted_command_rows)}**
- Accepted tests: **{len(accepted_test_rows)}**
- Acceptance written: **{acceptance_written}**

## Boundary

DD-063R is acceptance-record only. It does not edit C++ source, register runtime
commands, mutate the active catalog, append/replace/delete/pack/zap, rebuild CDX
or LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair rows.

## Next

DD-064 may plan guarded runtime implementation, but actual implementation still
requires explicit authorization.
"""
    (out / "DD063R_DDICT_COMMAND_CONTRACT_ACCEPTANCE_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-063R DDICT command contract acceptance manifest: {out / 'dd063r_ddict_command_contract_acceptance_manifest.json'}")
    print(f"status: {status}; commands: {len(accepted_command_rows)}; tests: {len(accepted_test_rows)}; failures: {failures}; acceptance_written: {acceptance_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
