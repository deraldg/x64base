#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List


EXPECTED_DD090_STATUS = "DDICT_READ_HELPER_REFACTOR_CYCLE_SAVEPOINT_GREEN"

DDICT_SURFACES = [
    "DDICT HELP",
    "DDICT STATUS",
    "DDICT TABLES",
    "DDICT OBJECTS",
    "DDICT FIELDS",
    "DDICT TAGS",
    "DDICT REL",
    "DDICT EVIDENCE",
]

HELP_CANDIDATES = [
    "dottalkpp/data/help",
    "dottalkpp/data/help/help_topic.dbf",
    "dottalkpp/data/help/commands.dbf",
    "dottalkpp/data/help/help_text.dbf",
    "dottalkpp/data/help/command_help.dbf",
    "dottalkpp/data/help/topics",
    "dottalkpp/data/help/generated",
    "dottalkpp/data/help/legacy",
    "docs/help",
    "docs/commands",
]

CMDHELPCHK_CANDIDATES = [
    "src/cli/cmd_cmdhelpchk.cpp",
    "include/cli/cmd_cmdhelpchk.hpp",
    "dottalkpp/data/help/cmdhelpchk",
    "dottalkpp/data/help/CMDHELPCHK",
    "tools/cmdhelp",
    "tools/help",
    "tools/datadict",
    "docs/cmdhelp",
]

DDICT_SOURCE_CANDIDATES = [
    "src/cli/cmd_ddict.cpp",
    "include/cli/cmd_ddict.hpp",
    "src/datadict/ddict_read_helpers.cpp",
    "src/datadict/ddict_catalog_paths.cpp",
    "src/datadict/ddict_dbf_reader.cpp",
    "src/datadict/ddict_object_resolver.cpp",
    "include/datadict/ddict_read_helpers.hpp",
    "include/datadict/ddict_catalog_paths.hpp",
    "include/datadict/ddict_dbf_reader.hpp",
    "include/datadict/ddict_object_resolver.hpp",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
]

PROTECTED_SOURCE_ARTIFACTS = [
    "src/cli/cmd_ddict.cpp",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
    "src/CMakeLists.txt",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return {"_read_error": str(exc)}


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def text_of(path: Path, limit_bytes: int = 2_000_000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        data = path.read_bytes()
    except Exception:
        return ""
    if len(data) > limit_bytes:
        data = data[:limit_bytes]
    return data.decode("utf-8", errors="replace")


def safe_size(path: Path) -> int:
    try:
        if path.exists() and path.is_file():
            return path.stat().st_size
        if path.exists() and path.is_dir():
            return sum(1 for _ in path.iterdir())
    except Exception:
        return 0
    return 0


def file_or_dir_row(repo: Path, rel_path: str, role: str) -> Dict[str, Any]:
    p = repo / rel_path
    text = text_of(p)
    upper = text.upper()
    return {
        "role": role,
        "path": rel_path,
        "exists": int(p.exists()),
        "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
        "size_or_children": safe_size(p),
        "mentions_ddict": int("DDICT" in upper),
        "mentions_cmdhelpchk": int("CMDHELPCHK" in upper),
        "sha256": sha256(p),
    }


def scan_dir_for_mentions(root: Path, repo: Path, max_files: int = 200) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not root.exists() or not root.is_dir():
        return rows
    count = 0
    for path in sorted(root.rglob("*")):
        if count >= max_files:
            break
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".txt", ".dts", ".csv", ".hpp", ".cpp", ".h", ".json", ".yaml", ".yml", ".dbf"}:
            continue
        text = text_of(path, limit_bytes=500_000)
        upper = text.upper()
        if "DDICT" in upper or "CMDHELPCHK" in upper or "HELP" in upper:
            count += 1
            try:
                rel = path.resolve().relative_to(repo.resolve()).as_posix()
            except Exception:
                rel = path.as_posix()
            rows.append({
                "path": rel,
                "bytes": path.stat().st_size,
                "mentions_ddict": int("DDICT" in upper),
                "mentions_cmdhelpchk": int("CMDHELPCHK" in upper),
                "mentions_help": int("HELP" in upper),
                "sha256": sha256(path),
            })
    return rows


def surface_plan_rows() -> List[Dict[str, Any]]:
    rows = []
    for i, surface in enumerate(DDICT_SURFACES, start=1):
        rows.append({
            "order": i,
            "surface": surface,
            "help_topic_candidate": surface.replace(" ", "_"),
            "cmdhelpchk_expectation": "registered command surface has usage/help coverage",
            "integration_phase": "plan_only",
            "mutation_now": 0,
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-092 Data Dictionary HELP/CMDHELPCHK integration plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD092-datadict-help-cmdhelpchk-integration-plan-v0")
    ap.add_argument("--dd090-dir", default="docs/datadict/reports/DD090-ddict-read-helper-refactor-cycle-savepoint-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd090_manifest_path = repo / args.dd090_dir / "dd090_ddict_read_helper_refactor_cycle_savepoint_manifest.json"
    dd090 = read_json(dd090_manifest_path)

    dd090_green = int(dd090.get("status") == EXPECTED_DD090_STATUS)

    artifact_rows: List[Dict[str, Any]] = []
    for p in HELP_CANDIDATES:
        artifact_rows.append(file_or_dir_row(repo, p, "help_candidate"))
    for p in CMDHELPCHK_CANDIDATES:
        artifact_rows.append(file_or_dir_row(repo, p, "cmdhelpchk_candidate"))
    for p in DDICT_SOURCE_CANDIDATES:
        artifact_rows.append(file_or_dir_row(repo, p, "ddict_source_candidate"))

    mention_roots = [
        repo / "dottalkpp/data/help",
        repo / "docs",
        repo / "tools",
        repo / "src/cli",
        repo / "include/cli",
    ]
    mention_rows: List[Dict[str, Any]] = []
    for root in mention_roots:
        mention_rows.extend(scan_dir_for_mentions(root, repo, max_files=80))

    surface_rows = surface_plan_rows()

    gap_rows = [
        {
            "gap_id": "G1_RUNTIME_HELP_SURFACE",
            "question": "Should DDICT HELP remain embedded in cmd_ddict.cpp or be backed by catalog/help files?",
            "recommended_resolution": "Keep runtime fallback embedded, then add generated/canonical HELP topic only after plan acceptance.",
            "mutation_now": 0,
        },
        {
            "gap_id": "G2_CMDHELPCHK_COVERAGE",
            "question": "Does CMDHELPCHK currently validate DDICT and DDICT sub-surfaces?",
            "recommended_resolution": "Discover CMDHELPCHK expectations first; do not mutate HELP DATA in DD-092.",
            "mutation_now": 0,
        },
        {
            "gap_id": "G3_HELP_TOPIC_GRANULARITY",
            "question": "Single DDICT topic or separate DDICT STATUS/TABLES/FIELDS/TAGS/REL/EVIDENCE topics?",
            "recommended_resolution": "Use one canonical DDICT topic with subcommand sections first; add subtopics only if existing HELP doctrine requires it.",
            "mutation_now": 0,
        },
        {
            "gap_id": "G4_PROVEN_RUNTIME_TO_HELP_SYNC",
            "question": "How should proven DD-089I surfaces be reflected in help/catalog metadata?",
            "recommended_resolution": "Use DD-089I/DD-090 reports as provenance, not as source of truth for command semantics.",
            "mutation_now": 0,
        },
        {
            "gap_id": "G5_DDICT_CATALOG_NO_DEPENDENCY_ON_MANUALS",
            "question": "Should manuals feed the Data Dictionary help?",
            "recommended_resolution": "No. Manuals explain downstream; DDICT help should derive from source/help metadata evidence.",
            "mutation_now": 0,
        },
    ]

    proposed_steps = [
        {"step": 1, "phase": "discover", "action": "Inventory existing HELP/CMDHELPCHK artifacts and DDICT mentions.", "mutation_now": 0},
        {"step": 2, "phase": "map", "action": "Map DDICT runtime surfaces to HELP topic sections and CMDHELPCHK expectations.", "mutation_now": 0},
        {"step": 3, "phase": "review", "action": "Review whether one DDICT topic or subtopic expansion best matches existing HELP doctrine.", "mutation_now": 0},
        {"step": 4, "phase": "candidate", "action": "Future package may generate candidate HELP text/report only.", "mutation_now": 0},
        {"step": 5, "phase": "apply_later", "action": "HELP/CMDHELPCHK mutation requires explicit later authorization.", "mutation_now": 0},
    ]

    protected_rows = []
    for rel_path in PROTECTED_SOURCE_ARTIFACTS:
        p = repo / rel_path
        protected_rows.append({
            "protected_path": rel_path,
            "exists": int(p.exists()),
            "sha256": sha256(p),
            "mutation_in_dd092": 0,
        })

    boundary_rows = [
        {"boundary": "help_cmdhelpchk_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    help_artifacts_present = sum(1 for r in artifact_rows if r["role"] == "help_candidate" and int(r["exists"]) == 1)
    cmdhelpchk_artifacts_present = sum(1 for r in artifact_rows if r["role"] == "cmdhelpchk_candidate" and int(r["exists"]) == 1)
    ddict_sources_present = sum(1 for r in artifact_rows if r["role"] == "ddict_source_candidate" and int(r["exists"]) == 1)
    ddict_mentions = sum(1 for r in mention_rows if int(r["mentions_ddict"]) == 1)

    gate_rows = [
        {"gate": "dd090_green", "expected": EXPECTED_DD090_STATUS, "observed": dd090.get("status", ""), "pass": dd090_green},
        {"gate": "ddict_runtime_parity_8_of_8", "expected": "8/8", "observed": f"{dd090.get('parity_passed', '')}/{dd090.get('parity_total', '')}", "pass": int(dd090.get("parity_passed") == 8 and dd090.get("parity_total") == 8)},
        {"gate": "runtime_surfaces_seen_8_of_8", "expected": 8, "observed": dd090.get("runtime_surfaces_seen", ""), "pass": int(dd090.get("runtime_surfaces_seen") == 8)},
        {"gate": "ddict_source_artifacts_present", "expected": ">=1", "observed": ddict_sources_present, "pass": int(ddict_sources_present >= 1)},
        {"gate": "help_artifact_candidates_present", "expected": ">=1", "observed": help_artifacts_present, "pass": int(help_artifacts_present >= 1)},
        {"gate": "cmdhelpchk_artifact_candidates_present", "expected": ">=0", "observed": cmdhelpchk_artifacts_present, "pass": 1},
        {"gate": "ddict_mentions_found", "expected": ">=1", "observed": ddict_mentions, "pass": int(ddict_mentions >= 1)},
        {"gate": "plan_only", "expected": 1, "observed": 1, "pass": 1},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_HELP_CMDHELPCHK_INTEGRATION_PLAN_READY" if failures == 0 else "DDICT_HELP_CMDHELPCHK_INTEGRATION_PLAN_REVIEW"

    next_rows = [
        {"next_id": "DD092A", "title": "DDICT HELP topic candidate generation", "allowed_scope": "generate candidate text/report only; no HELP mutation"},
        {"next_id": "DD092B", "title": "CMDHELPCHK expectation mapping", "allowed_scope": "report-only mapping from DDICT runtime surfaces to validation expectations"},
        {"next_id": "DD092C", "title": "guarded HELP/CMDHELPCHK apply package", "allowed_scope": "only after explicit authorization and reviewed candidates"},
    ]

    write_csv(out / "dd092_artifact_inventory.csv", artifact_rows, ["role", "path", "exists", "kind", "size_or_children", "mentions_ddict", "mentions_cmdhelpchk", "sha256"])
    write_csv(out / "dd092_ddict_mention_scan.csv", mention_rows, ["path", "bytes", "mentions_ddict", "mentions_cmdhelpchk", "mentions_help", "sha256"])
    write_csv(out / "dd092_surface_help_mapping_plan.csv", surface_rows, ["order", "surface", "help_topic_candidate", "cmdhelpchk_expectation", "integration_phase", "mutation_now"])
    write_csv(out / "dd092_gap_review.csv", gap_rows, ["gap_id", "question", "recommended_resolution", "mutation_now"])
    write_csv(out / "dd092_proposed_sequence.csv", proposed_steps, ["step", "phase", "action", "mutation_now"])
    write_csv(out / "dd092_protected_file_ledger.csv", protected_rows, ["protected_path", "exists", "sha256", "mutation_in_dd092"])
    write_csv(out / "dd092_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd092_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd092_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-092 Data Dictionary HELP/CMDHELPCHK Integration Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-092 starts the Data Dictionary HELP/CMDHELPCHK integration lane as a report-only plan.

The goal is to connect the runtime-proven DDICT command surface to HELP/CMDHELPCHK without mutating HELP DATA,
metadata catalogs, command registries, DBFs, CDX/LMDB, generated catalog content, or manuals in this step.

## Preconditions

- DD-090 manifest: `{dd090_manifest_path}`
- DD-090 status: `{dd090.get('status', '')}`
- DD-090 runtime parity: **{dd090.get('parity_passed', '')} / {dd090.get('parity_total', '')}**
- DD-090 runtime surfaces: **{dd090.get('runtime_surfaces_seen', '')} / 8**

## Findings

- DDICT source artifacts present: **{ddict_sources_present}**
- HELP artifact candidates present: **{help_artifacts_present}**
- CMDHELPCHK artifact candidates present: **{cmdhelpchk_artifacts_present}**
- DDICT mention scan rows: **{len(mention_rows)}**
- DDICT mention rows: **{ddict_mentions}**

## Runtime surfaces to map

```text
DDICT HELP
DDICT STATUS
DDICT TABLES
DDICT OBJECTS
DDICT FIELDS
DDICT TAGS
DDICT REL
DDICT EVIDENCE
```

## Recommended doctrine

Keep the runtime `DDICT HELP` fallback in source so DDICT remains explainable even if HELP DATA is absent.
Then generate a reviewed canonical HELP topic and CMDHELPCHK expectation map in separate report-only sublanes.
Apply/mutate HELP DATA only after explicit authorization.

## Boundary

DD-092 is plan/report-only. It does not edit C++ source, edit build files, edit command registration,
mutate active catalog DBFs, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB,
mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.

## Recommended next lanes

```text
DD092A  DDICT HELP topic candidate generation
DD092B  CMDHELPCHK expectation mapping
DD092C  guarded HELP/CMDHELPCHK apply package only after explicit authorization
```
"""

    (out / "DD092_DATADICT_HELP_CMDHELPCHK_INTEGRATION_PLAN_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd092_datadict_help_cmdhelpchk_integration_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd090_status": dd090.get("status", ""),
        "dd090_parity": f"{dd090.get('parity_passed', '')}/{dd090.get('parity_total', '')}",
        "dd090_runtime_surfaces": dd090.get("runtime_surfaces_seen", ""),
        "ddict_source_artifacts_present": ddict_sources_present,
        "help_artifact_candidates_present": help_artifacts_present,
        "cmdhelpchk_artifact_candidates_present": cmdhelpchk_artifacts_present,
        "ddict_mentions": ddict_mentions,
        "failures": failures,
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD092A DDICT HELP topic candidate generation, or DD092B CMDHELPCHK expectation mapping.",
    }
    write_json(out / "dd092_datadict_help_cmdhelpchk_integration_plan_manifest.json", manifest)

    print(f"DD-092 Data Dictionary HELP/CMDHELPCHK integration plan manifest: {out / 'dd092_datadict_help_cmdhelpchk_integration_plan_manifest.json'}")
    print(f"status: {status}; help_candidates: {help_artifacts_present}; cmdhelpchk_candidates: {cmdhelpchk_artifacts_present}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
