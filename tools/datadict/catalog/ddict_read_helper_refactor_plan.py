#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD087_STATUS = "DDICT_ACCEPTED_COMMAND_CONTRACT_FINAL_CLOSURE_GREEN"

EXPECTED_HELPERS = [
    "lower_copy",
    "trim_copy",
    "upper_copy",
    "value_of",
    "exists_quiet",
    "size_quiet",
    "normalize_quiet",
    "base_roots",
    "catalog_candidates",
    "find_catalog_dir",
    "find_cdx_file",
    "find_lmdb_dir",
    "collect_stats",
    "plausible_name",
    "plausible_descriptor",
    "descriptor_start",
    "le16",
    "le32",
    "descriptor_name",
    "read_binary",
    "parse_fields",
    "read_dbf_table",
    "short_text",
    "resolve_object",
    "object_index",
    "print_status",
    "print_tables",
    "print_fields",
    "print_tags",
    "print_rel",
    "print_evidence",
    "print_objects",
]

READ_HELPER_CANDIDATES = [
    {
        "helper_group": "string_utils",
        "candidate_functions": "lower_copy;trim_copy;upper_copy;short_text;value_of",
        "proposed_target": "include/datadict/ddict_read_helpers.hpp; src/datadict/ddict_read_helpers.cpp",
        "purpose": "Reusable formatting and row-value helpers.",
        "phase": "DD089A_PLAN_ONLY",
    },
    {
        "helper_group": "filesystem_catalog_roots",
        "candidate_functions": "exists_quiet;size_quiet;normalize_quiet;base_roots;catalog_candidates;find_catalog_dir",
        "proposed_target": "include/datadict/ddict_catalog_paths.hpp; src/datadict/ddict_catalog_paths.cpp",
        "purpose": "Read-only active catalog path and artifact discovery.",
        "phase": "DD089A_PLAN_ONLY",
    },
    {
        "helper_group": "artifact_discovery",
        "candidate_functions": "find_cdx_file;find_lmdb_dir",
        "proposed_target": "include/datadict/ddict_catalog_paths.hpp; src/datadict/ddict_catalog_paths.cpp",
        "purpose": "Existing CDX/LMDB artifact discovery without create/rebuild.",
        "phase": "DD089A_PLAN_ONLY",
    },
    {
        "helper_group": "dbf_reader",
        "candidate_functions": "plausible_name;plausible_descriptor;descriptor_start;le16;le32;descriptor_name;read_binary;parse_fields;read_dbf_table",
        "proposed_target": "include/datadict/ddict_dbf_reader.hpp; src/datadict/ddict_dbf_reader.cpp",
        "purpose": "Reusable read-only x64 DBF row reader for active catalog tables.",
        "phase": "DD089B_AFTER_TESTS",
    },
    {
        "helper_group": "object_resolver",
        "candidate_functions": "resolve_object;object_index",
        "proposed_target": "include/datadict/ddict_object_resolver.hpp; src/datadict/ddict_object_resolver.cpp",
        "purpose": "Shared object token resolution for REL/EVIDENCE/OBJECTS.",
        "phase": "DD089B_AFTER_TESTS",
    },
    {
        "helper_group": "command_renderers",
        "candidate_functions": "print_status;print_tables;print_fields;print_tags;print_rel;print_evidence;print_objects",
        "proposed_target": "keep in src/cli/cmd_ddict.cpp for now",
        "purpose": "Command-specific presentation should remain near CLI until helper APIs stabilize.",
        "phase": "DEFER_KEEP_LOCAL",
    },
]

TEST_PLAN = [
    {"test_id": "DDICT_HELP_PRESERVED", "command": "DDICT HELP", "expected": "usage surface remains unchanged"},
    {"test_id": "DDICT_STATUS_PRESERVED", "command": "DDICT STATUS", "expected": "active catalog, READ-ONLY, 11/11 DBF tables"},
    {"test_id": "DDICT_TABLES_PRESERVED", "command": "DDICT TABLES", "expected": "all 11 catalog tables listed"},
    {"test_id": "DDICT_OBJECTS_PRESERVED", "command": "DDICT OBJECTS TYPE CATALOG_TABLE", "expected": "11 CATALOG_TABLE rows"},
    {"test_id": "DDICT_FIELDS_PRESERVED", "command": "DDICT FIELDS DDOBJECT", "expected": "DDOBJECT field rows"},
    {"test_id": "DDICT_TAGS_PRESERVED", "command": "DDICT TAGS DDATTR", "expected": "ATTRID and OBJ_ATTR tags"},
    {"test_id": "DDICT_REL_PRESERVED", "command": "DDICT REL DDOBJECT OUT", "expected": "outgoing HAS_FIELD/HAS_TAG rows"},
    {"test_id": "DDICT_EVIDENCE_PRESERVED", "command": "DDICT EVIDENCE DDOBJECT", "expected": "attribute evidence rows"},
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


def extract_functions(source_text: str) -> List[Dict[str, Any]]:
    pattern = re.compile(
        r"(?m)^(?:[A-Za-z_][\w:<>,\s*&]+)\s+([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{"
    )
    rows: List[Dict[str, Any]] = []
    for m in pattern.finditer(source_text):
        name = m.group(1)
        start_line = source_text[:m.start()].count("\n") + 1
        # approximate function length by brace scan
        i = m.end() - 1
        depth = 0
        end = i
        for j in range(i, len(source_text)):
            if source_text[j] == "{":
                depth += 1
            elif source_text[j] == "}":
                depth -= 1
                if depth == 0:
                    end = j
                    break
        end_line = source_text[:end].count("\n") + 1
        rows.append({
            "function": name,
            "start_line": start_line,
            "end_line": end_line,
            "line_count": max(1, end_line - start_line + 1),
            "expected_helper": int(name in EXPECTED_HELPERS),
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-088 DDICT read-helper refactor plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD088-ddict-read-helper-refactor-plan-v0")
    ap.add_argument("--dd087-dir", default="docs/datadict/reports/DD087-ddict-accepted-command-contract-final-closure-v0")
    ap.add_argument("--source-path", default="src/cli/cmd_ddict.cpp")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd087_dir = (repo / args.dd087_dir).resolve()
    dd087_manifest = read_json(dd087_dir / "dd087_ddict_accepted_command_contract_final_closure_manifest.json")
    source = (repo / args.source_path).resolve()
    source_text = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""

    function_rows = extract_functions(source_text)
    found_functions = {row["function"] for row in function_rows}
    helper_presence = []
    for helper in EXPECTED_HELPERS:
        helper_presence.append({
            "helper": helper,
            "present": int(helper in found_functions),
            "category": next((c["helper_group"] for c in READ_HELPER_CANDIDATES if helper in c["candidate_functions"].split(";")), "command_or_other"),
        })

    dd087_green = int(dd087_manifest.get("status") == EXPECTED_DD087_STATUS)
    source_exists = int(source.exists())
    expected_present = sum(1 for row in helper_presence if int(row["present"]) == 1)
    missing_expected = len(helper_presence) - expected_present
    has_cmd_ddict = int("void cmd_DDICT" in source_text)
    has_no_mutation_markers = int(
        "BUILDLMDB" not in source_text
        and "CDX ADDTAG" not in source_text
        and "APPEND BLANK" not in source_text
        and "REPLACE " not in source_text
        and "DELETE " not in source_text
        and "PACK" not in source_text
        and "ZAP" not in source_text
    )

    gate_rows = [
        {"gate": "dd087_final_contract_closure_green", "expected": EXPECTED_DD087_STATUS, "observed": dd087_manifest.get("status", ""), "pass": dd087_green},
        {"gate": "cmd_ddict_source_exists", "expected": 1, "observed": source_exists, "pass": source_exists},
        {"gate": "cmd_DDICT_entrypoint_present", "expected": 1, "observed": has_cmd_ddict, "pass": has_cmd_ddict},
        {"gate": "expected_helpers_present", "expected": len(helper_presence), "observed": expected_present, "pass": int(missing_expected == 0)},
        {"gate": "source_has_no_mutation_markers", "expected": 1, "observed": has_no_mutation_markers, "pass": has_no_mutation_markers},
        {"gate": "refactor_plan_only", "expected": 1, "observed": 1, "pass": 1},
    ]
    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_READ_HELPER_REFACTOR_PLAN_READY" if failures == 0 else "DDICT_READ_HELPER_REFACTOR_PLAN_REVIEW"

    boundary_rows = [
        {"boundary": "read_helper_refactor_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "new_cxx_files_created", "observed": 0, "required": 0, "pass": 1},
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
            "lane": "DD-089A header-only/read-only helper skeleton",
            "allowed": "plan/package only unless explicitly authorized",
            "notes": "Create candidate interfaces but do not patch cmd_ddict.cpp yet.",
        },
        {
            "lane": "DD-089B guarded extraction with parity smoke",
            "allowed": "after DD-089A accepted",
            "notes": "Move DBF reader/path helpers and rerun all DDICT smoke tests.",
        },
        {
            "lane": "DD-089C pydottalk/shared reader API bridge",
            "allowed": "after C++ helper extraction is green",
            "notes": "Align with DD-061 active Data Dictionary reader API plan.",
        },
        {
            "lane": "HELP/CMDHELPCHK integration",
            "allowed": "separate explicit lane",
            "notes": "Do not combine with read-helper refactor.",
        },
    ]

    write_csv(out / "dd088_cmd_ddict_function_inventory.csv", function_rows, ["function", "start_line", "end_line", "line_count", "expected_helper"])
    write_csv(out / "dd088_expected_helper_presence.csv", helper_presence, ["helper", "present", "category"])
    write_csv(out / "dd088_refactor_group_plan.csv", READ_HELPER_CANDIDATES, ["helper_group", "candidate_functions", "proposed_target", "purpose", "phase"])
    write_csv(out / "dd088_parity_test_plan.csv", TEST_PLAN, ["test_id", "command", "expected"])
    write_csv(out / "dd088_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd088_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd088_future_lane_recommendations.csv", future_rows, ["lane", "allowed", "notes"])

    total_lines = source_text.count("\n") + (1 if source_text else 0)
    report = f"""# DD-088 DDICT Read-Helper Refactor Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-088 plans how to refactor the proven `DDICT` command implementation into reusable read-only helper modules without changing behavior yet.

## Inputs

- DD-087 status: `{dd087_manifest.get('status', '')}`
- Source inspected: `{rel(repo, source)}`
- Source lines: **{total_lines}**

## Findings

- Functions inventoried: **{len(function_rows)}**
- Expected helpers present: **{expected_present} / {len(helper_presence)}**
- Missing expected helpers: **{missing_expected}**
- Mutation marker scan passed: **{has_no_mutation_markers}**

## Recommended extraction sequence

```text
1. Keep command renderers in cmd_ddict.cpp for now.
2. Extract string/path helpers first.
3. Extract read-only DBF reader only after parity tests are locked.
4. Extract object resolver after REL/EVIDENCE parity tests are locked.
5. Do not mix this with HELP/CMDHELPCHK integration.
```

## Candidate modules

```text
include/datadict/ddict_read_helpers.hpp
src/datadict/ddict_read_helpers.cpp

include/datadict/ddict_catalog_paths.hpp
src/datadict/ddict_catalog_paths.cpp

include/datadict/ddict_dbf_reader.hpp
src/datadict/ddict_dbf_reader.cpp

include/datadict/ddict_object_resolver.hpp
src/datadict/ddict_object_resolver.cpp
```

## Boundary

DD-088 is refactor planning only. It does not edit C++ source, create new C++ files,
edit build files, mutate active catalog data, create/rebuild CDX/LMDB, mutate
HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    (out / "DD088_DDICT_READ_HELPER_REFACTOR_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd088_ddict_read_helper_refactor_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd087_status": dd087_manifest.get("status", ""),
        "source_path": rel(repo, source),
        "source_lines": total_lines,
        "functions_inventoried": len(function_rows),
        "expected_helpers_present": expected_present,
        "expected_helpers_total": len(helper_presence),
        "missing_expected_helpers": missing_expected,
        "failures": failures,
        "cxx_source_edits": 0,
        "new_cxx_files_created": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-089A read-helper skeleton/interface package, plan-only unless explicitly authorized.",
    }
    write_json(out / "dd088_ddict_read_helper_refactor_plan_manifest.json", manifest)

    print(f"DD-088 DDICT read-helper refactor plan manifest: {out / 'dd088_ddict_read_helper_refactor_plan_manifest.json'}")
    print(f"status: {status}; functions: {len(function_rows)}; helpers_present: {expected_present}/{len(helper_presence)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
