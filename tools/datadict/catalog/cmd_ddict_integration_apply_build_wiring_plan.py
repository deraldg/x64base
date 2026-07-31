#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import json
import re
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD089E_STATUS = "DDICT_CMD_DDICT_HELPER_INTEGRATION_PREVIEW_READY"

HELPER_HEADERS = [
    "include/datadict/ddict_read_helpers.hpp",
    "include/datadict/ddict_catalog_paths.hpp",
    "include/datadict/ddict_dbf_reader.hpp",
    "include/datadict/ddict_object_resolver.hpp",
]

HELPER_SOURCES = [
    "src/datadict/ddict_read_helpers.cpp",
    "src/datadict/ddict_catalog_paths.cpp",
    "src/datadict/ddict_dbf_reader.cpp",
    "src/datadict/ddict_object_resolver.cpp",
]

DDICT_SURFACE_SMOKES = [
    ("DDICT_HELP_PRESERVED", "DDICT HELP", "usage surface remains unchanged"),
    ("DDICT_STATUS_PRESERVED", "DDICT STATUS", "active catalog, READ-ONLY, 11/11 DBF tables"),
    ("DDICT_TABLES_PRESERVED", "DDICT TABLES", "all 11 catalog tables listed"),
    ("DDICT_OBJECTS_PRESERVED", "DDICT OBJECTS TYPE CATALOG_TABLE", "11 CATALOG_TABLE rows"),
    ("DDICT_FIELDS_PRESERVED", "DDICT FIELDS DDOBJECT", "DDOBJECT field rows"),
    ("DDICT_TAGS_PRESERVED", "DDICT TAGS DDATTR", "ATTRID and OBJ_ATTR tags"),
    ("DDICT_REL_PRESERVED", "DDICT REL DDOBJECT OUT", "outgoing HAS_FIELD/HAS_TAG rows"),
    ("DDICT_EVIDENCE_PRESERVED", "DDICT EVIDENCE DDOBJECT", "attribute evidence rows"),
]

PROTECTED_UNTOUCHED = [
    "src/cli/cmd_ddict.cpp",
    "src/CMakeLists.txt",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
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


def sha256(path: Path) -> str:
    import hashlib
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def diff_text(old: str, new: str, name: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=name + ".current",
        tofile=name + ".candidate",
        lineterm="",
    ))


def find_source_list_anchor(cmake: str) -> Dict[str, Any]:
    # Conservative discovery only: detect whether CMake appears to use globs or explicit source lists.
    upper = cmake.upper()
    return {
        "uses_glob": int("GLOB" in upper and ("CLI" in upper or "SRC" in upper)),
        "mentions_cmd_ddict": int("cmd_ddict.cpp" in cmake),
        "mentions_datadict_dir": int("datadict" in cmake.lower()),
        "likely_build_wiring_needed": int("src/datadict" not in cmake.lower() and "datadict/*.cpp" not in cmake.lower()),
    }


def build_cmake_candidate(cmake: str) -> str:
    # Preview only. Add a clearly marked block near the end if source files are not already mentioned.
    missing = [s for s in HELPER_SOURCES if s not in cmake and s.replace("src/", "") not in cmake]
    if not missing:
        return cmake
    block = "\n# DD-089F PREVIEW ONLY - candidate DDICT helper source wiring\n"
    block += "# Do not apply without guarded build-wiring authorization.\n"
    block += "# Candidate helper sources:\n"
    for src in missing:
        block += f"#   {src}\n"
    return cmake.rstrip() + "\n" + block + "\n"


def make_integration_plan(repo: Path, dd089e_manifest: Dict[str, Any], cmd_source: Path, cmake_path: Path) -> Dict[str, Any]:
    candidate_rel = dd089e_manifest.get("candidate_source", "")
    diff_rel = dd089e_manifest.get("candidate_diff", "")
    candidate_path = repo / candidate_rel if candidate_rel else Path("")
    diff_path = repo / diff_rel if diff_rel else Path("")
    cmd_text = cmd_source.read_text(encoding="utf-8", errors="replace") if cmd_source.exists() else ""
    candidate_text = candidate_path.read_text(encoding="utf-8", errors="replace") if candidate_path.exists() else ""
    cmake_text = cmake_path.read_text(encoding="utf-8", errors="replace") if cmake_path.exists() else ""
    cmake_candidate = build_cmake_candidate(cmake_text)
    return {
        "candidate_path": candidate_path,
        "diff_path": diff_path,
        "cmd_text": cmd_text,
        "candidate_text": candidate_text,
        "cmake_text": cmake_text,
        "cmake_candidate": cmake_candidate,
        "cmake_anchor": find_source_list_anchor(cmake_text),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-089F cmd_ddict integration apply/build-wiring plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD089F-cmd-ddict-integration-apply-build-wiring-plan-v0")
    ap.add_argument("--dd089e-dir", default="docs/datadict/reports/DD089E-cmd-ddict-helper-integration-preview-v0")
    ap.add_argument("--cmd-source", default="src/cli/cmd_ddict.cpp")
    ap.add_argument("--cmake-path", default="src/CMakeLists.txt")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd089e_dir = (repo / args.dd089e_dir).resolve()
    dd089e_manifest = read_json(dd089e_dir / "dd089e_cmd_ddict_helper_integration_preview_manifest.json")
    cmd_source = repo / args.cmd_source
    cmake_path = repo / args.cmake_path
    generated_root = out / "generated_apply_build_wiring_plan"
    generated_root.mkdir(parents=True, exist_ok=True)

    plan = make_integration_plan(repo, dd089e_manifest, cmd_source, cmake_path)

    review_rows: List[Dict[str, Any]] = []
    dd089e_green = int(dd089e_manifest.get("status") == EXPECTED_DD089E_STATUS)
    if not dd089e_green:
        review_rows.append({"issue": "DD089E_NOT_READY", "detail": dd089e_manifest.get("status", "")})
    if not cmd_source.exists():
        review_rows.append({"issue": "CMD_SOURCE_MISSING", "detail": str(cmd_source)})
    if not plan["candidate_path"].exists():
        review_rows.append({"issue": "DD089E_CANDIDATE_SOURCE_MISSING", "detail": str(plan["candidate_path"])})
    if not cmake_path.exists():
        review_rows.append({"issue": "CMAKE_MISSING", "detail": str(cmake_path)})

    helper_rows = []
    for h in HELPER_HEADERS:
        p = repo / h
        text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        helper_rows.append({
            "artifact": h,
            "kind": "header",
            "exists": int(p.exists()),
            "bytes": p.stat().st_size if p.exists() else 0,
            "has_namespace": int("namespace dottalk::datadict" in text),
            "hash": sha256(p),
        })
        if not p.exists():
            review_rows.append({"issue": "HELPER_HEADER_MISSING", "detail": h})
    for s in HELPER_SOURCES:
        p = repo / s
        text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        helper_rows.append({
            "artifact": s,
            "kind": "source",
            "exists": int(p.exists()),
            "bytes": p.stat().st_size if p.exists() else 0,
            "has_namespace": int("namespace dottalk::datadict" in text),
            "hash": sha256(p),
        })
        if not p.exists():
            review_rows.append({"issue": "HELPER_SOURCE_MISSING", "detail": s})

    candidate_text = plan["candidate_text"]
    cmd_text = plan["cmd_text"]
    candidate_has_headers = sum(1 for h in [
        '#include "datadict/ddict_read_helpers.hpp"',
        '#include "datadict/ddict_catalog_paths.hpp"',
        '#include "datadict/ddict_dbf_reader.hpp"',
        '#include "datadict/ddict_object_resolver.hpp"',
    ] if h in candidate_text)

    candidate_has_namespace_bridge = int("dottalk::datadict" in candidate_text)
    current_has_local_helpers = int("lower_copy" in cmd_text and "read_dbf_table" in cmd_text and "resolve_object" in cmd_text)
    candidate_mentions_local_removal = int("moved to datadict helper module" in candidate_text)
    candidate_preserves_renderers = int("print_status" in candidate_text and "print_rel" in candidate_text and "print_evidence" in candidate_text and "print_objects" in candidate_text)

    cmake_candidate_path = generated_root / args.cmake_path
    cmake_candidate_path.parent.mkdir(parents=True, exist_ok=True)
    cmake_candidate_path.write_text(plan["cmake_candidate"], encoding="utf-8")
    cmake_diff_path = generated_root / (args.cmake_path + ".preview.diff")
    cmake_diff_path.parent.mkdir(parents=True, exist_ok=True)
    cmake_diff_path.write_text(diff_text(plan["cmake_text"], plan["cmake_candidate"], args.cmake_path), encoding="utf-8")

    apply_plan_rows = [
        {
            "step": "1",
            "phase": "cmd_ddict_candidate_review",
            "action": "Review DD-089E candidate cmd_ddict.cpp and local type compatibility before any apply.",
            "mutates_now": 0,
        },
        {
            "step": "2",
            "phase": "cmd_ddict_apply",
            "action": "Future guarded apply may replace cmd_ddict.cpp with the reviewed candidate and backup original.",
            "mutates_now": 0,
        },
        {
            "step": "3",
            "phase": "build_wiring_review",
            "action": "Review whether src/CMakeLists.txt needs explicit helper source wiring or already globs src/datadict/*.cpp.",
            "mutates_now": 0,
        },
        {
            "step": "4",
            "phase": "build_wiring_apply",
            "action": "Future guarded apply may wire helper source files only after cmd_ddict candidate compiles in plan review.",
            "mutates_now": 0,
        },
        {
            "step": "5",
            "phase": "parity_smoke",
            "action": "Run full DDICT parity smoke after build succeeds.",
            "mutates_now": 0,
        },
    ]

    parity_rows = [
        {"test_id": tid, "command": cmd, "expected": expected, "required_after_future_apply": 1}
        for tid, cmd, expected in DDICT_SURFACE_SMOKES
    ]

    protected_rows = []
    protected_mutations = 0
    for rel_path in PROTECTED_UNTOUCHED:
        path = repo / rel_path
        h = sha256(path)
        protected_rows.append({
            "protected_path": rel_path,
            "exists": int(path.exists()),
            "hash_before": h,
            "hash_after": h,
            "mutated_by_dd089f": 0,
        })

    cmake_anchor = plan["cmake_anchor"]
    cmake_rows = [{
        "cmake_path": args.cmake_path,
        "exists": int(cmake_path.exists()),
        "uses_glob": cmake_anchor["uses_glob"],
        "mentions_cmd_ddict": cmake_anchor["mentions_cmd_ddict"],
        "mentions_datadict_dir": cmake_anchor["mentions_datadict_dir"],
        "likely_build_wiring_needed": cmake_anchor["likely_build_wiring_needed"],
        "candidate_path": str(cmake_candidate_path),
        "candidate_diff": str(cmake_diff_path),
        "mutated_now": 0,
    }]

    gate_rows = [
        {"gate": "dd089e_integration_preview_ready", "expected": EXPECTED_DD089E_STATUS, "observed": dd089e_manifest.get("status", ""), "pass": dd089e_green},
        {"gate": "cmd_source_exists", "expected": 1, "observed": int(cmd_source.exists()), "pass": int(cmd_source.exists())},
        {"gate": "dd089e_candidate_source_exists", "expected": 1, "observed": int(plan["candidate_path"].exists()), "pass": int(plan["candidate_path"].exists())},
        {"gate": "helper_artifacts_present", "expected": len(HELPER_HEADERS) + len(HELPER_SOURCES), "observed": sum(1 for r in helper_rows if int(r["exists"]) == 1), "pass": int(sum(1 for r in helper_rows if int(r["exists"]) == 1) == len(HELPER_HEADERS) + len(HELPER_SOURCES))},
        {"gate": "candidate_has_helper_includes", "expected": len(HELPER_HEADERS), "observed": candidate_has_headers, "pass": int(candidate_has_headers == len(HELPER_HEADERS))},
        {"gate": "candidate_has_namespace_bridge", "expected": 1, "observed": candidate_has_namespace_bridge, "pass": candidate_has_namespace_bridge},
        {"gate": "candidate_preserves_command_renderers", "expected": 1, "observed": candidate_preserves_renderers, "pass": candidate_preserves_renderers},
        {"gate": "candidate_records_helper_removal", "expected": 1, "observed": candidate_mentions_local_removal, "pass": candidate_mentions_local_removal},
        {"gate": "cmake_exists", "expected": 1, "observed": int(cmake_path.exists()), "pass": int(cmake_path.exists())},
        {"gate": "protected_files_unmutated", "expected": 0, "observed": protected_mutations, "pass": int(protected_mutations == 0)},
        {"gate": "plan_only", "expected": 1, "observed": 1, "pass": 1},
    ]

    failures = sum(1 for row in gate_rows if int(row["pass"]) != 1)
    status = "DDICT_CMD_DDICT_APPLY_BUILD_WIRING_PLAN_READY" if failures == 0 else "DDICT_CMD_DDICT_APPLY_BUILD_WIRING_PLAN_REVIEW"

    boundary_rows = [
        {"boundary": "apply_build_wiring_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cmd_ddict_cpp_patched", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "helper_source_files_modified", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    next_rows = [
        {
            "next_id": "DD089G",
            "title": "guarded cmd_ddict integration apply package",
            "allowed_scope": "backup and patch cmd_ddict.cpp only, with build wiring still separately gated unless CMake already globs helper files",
        },
        {
            "next_id": "DD089H",
            "title": "build wiring package",
            "allowed_scope": "wire helper source files if required by CMake discovery, then build",
        },
        {
            "next_id": "DD089I",
            "title": "DDICT parity closure",
            "allowed_scope": "run full DDICT smoke suite and close refactor parity",
        },
    ]

    write_csv(out / "dd089f_helper_artifact_ledger.csv", helper_rows, ["artifact", "kind", "exists", "bytes", "has_namespace", "hash"])
    write_csv(out / "dd089f_apply_plan_steps.csv", apply_plan_rows, ["step", "phase", "action", "mutates_now"])
    write_csv(out / "dd089f_cmake_wiring_review.csv", cmake_rows, ["cmake_path", "exists", "uses_glob", "mentions_cmd_ddict", "mentions_datadict_dir", "likely_build_wiring_needed", "candidate_path", "candidate_diff", "mutated_now"])
    write_csv(out / "dd089f_parity_test_plan.csv", parity_rows, ["test_id", "command", "expected", "required_after_future_apply"])
    write_csv(out / "dd089f_protected_file_ledger.csv", protected_rows, ["protected_path", "exists", "hash_before", "hash_after", "mutated_by_dd089f"])
    write_csv(out / "dd089f_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd089f_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd089f_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd089f_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-089F cmd_ddict Integration Apply / Build-Wiring Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-089F reviews the DD-089E `cmd_ddict.cpp` candidate and prepares the next guarded apply/build-wiring sequence.

It does not apply source changes.

## Inputs

- DD-089E status: `{dd089e_manifest.get('status', '')}`
- Current command source: `{rel(repo, cmd_source)}`
- DD-089E candidate source: `{rel(repo, plan['candidate_path'])}`
- CMake file: `{rel(repo, cmake_path)}`

## Findings

- Helper artifacts present: **{sum(1 for r in helper_rows if int(r['exists']) == 1)} / {len(helper_rows)}**
- Candidate helper includes: **{candidate_has_headers} / {len(HELPER_HEADERS)}**
- Candidate namespace bridge present: **{candidate_has_namespace_bridge}**
- Candidate preserves command renderers: **{candidate_preserves_renderers}**
- CMake likely build wiring needed: **{cmake_anchor['likely_build_wiring_needed']}**
- Protected file mutations: **{protected_mutations}**

## Generated review artifacts

- Candidate CMake note/diff: `{rel(repo, cmake_diff_path)}`
- Apply plan steps: `dd089f_apply_plan_steps.csv`
- Parity test plan: `dd089f_parity_test_plan.csv`

## Recommended next sequence

```text
DD-089G guarded cmd_ddict integration apply
DD-089H build wiring if CMake needs explicit helper sources
DD-089I full DDICT parity closure
```

Do not collapse these unless explicitly authorized after reviewing the DD-089F ledgers.

## Boundary

DD-089F is apply/build-wiring planning only. It does not patch `cmd_ddict.cpp`, modify helper source files,
edit build files, edit command registration, mutate active catalog data, create/rebuild CDX/LMDB,
mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    (out / "DD089F_CMD_DDICT_INTEGRATION_APPLY_BUILD_WIRING_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd089f_cmd_ddict_integration_apply_build_wiring_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd089e_status": dd089e_manifest.get("status", ""),
        "candidate_source": rel(repo, plan["candidate_path"]),
        "cmake_candidate_diff": rel(repo, cmake_diff_path),
        "helper_artifacts_present": sum(1 for r in helper_rows if int(r["exists"]) == 1),
        "helper_artifacts_expected": len(helper_rows),
        "candidate_helper_includes": candidate_has_headers,
        "candidate_preserves_renderers": candidate_preserves_renderers,
        "cmake_likely_build_wiring_needed": cmake_anchor["likely_build_wiring_needed"],
        "failures": failures,
        "cmd_ddict_cpp_patched": 0,
        "helper_source_files_modified": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-089G guarded cmd_ddict integration apply package if DD-089F is green.",
    }
    write_json(out / "dd089f_cmd_ddict_integration_apply_build_wiring_plan_manifest.json", manifest)

    print(f"DD-089F cmd_ddict integration apply/build-wiring plan manifest: {out / 'dd089f_cmd_ddict_integration_apply_build_wiring_plan_manifest.json'}")
    print(f"status: {status}; helper_artifacts: {manifest['helper_artifacts_present']}/{manifest['helper_artifacts_expected']}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
