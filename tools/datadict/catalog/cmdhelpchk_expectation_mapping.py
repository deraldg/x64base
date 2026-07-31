#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD092_STATUS = "DDICT_HELP_CMDHELPCHK_INTEGRATION_PLAN_READY"
EXPECTED_DD092A_STATUS = "DDICT_HELP_TOPIC_CANDIDATE_GENERATED_REVIEW_READY"
EXPECTED_DD093C_STATUS = "DDICT_FULL_PATH_REMAP_RUNTIME_CLOSURE_GREEN"

SURFACES = [
    {
        "surface": "DDICT HELP",
        "command": "DDICT",
        "subsurface": "HELP",
        "expectation": "Usage/help surface exists and documents all DDICT read-only subcommands.",
        "required_runtime_proof": "DDICT HELP output or candidate HELP topic includes DDICT syntax.",
    },
    {
        "surface": "DDICT STATUS",
        "command": "DDICT",
        "subsurface": "STATUS",
        "expectation": "Status reports active catalog root, READ-ONLY mode, DBF table count, and catalog state.",
        "required_runtime_proof": "Active catalog data/datadict and DBF tables 11 / 11.",
    },
    {
        "surface": "DDICT TABLES",
        "command": "DDICT",
        "subsurface": "TABLES",
        "expectation": "Tables lists the 11 Data Dictionary catalog tables with DBF/DTX presence.",
        "required_runtime_proof": "DDRUN,DDBASE,DDSOURCE,DDOBJECT,DDATTR,DDEDGE,DDEVID,DDGATE,DDREVIEW,DDARTIF,DDPROFILE.",
    },
    {
        "surface": "DDICT OBJECTS",
        "command": "DDICT",
        "subsurface": "OBJECTS",
        "expectation": "Objects supports catalog object listing and optional TYPE/PROFILE filters.",
        "required_runtime_proof": "DDICT OBJECTS TYPE CATALOG_TABLE or equivalent object listing proof.",
    },
    {
        "surface": "DDICT FIELDS <table>",
        "command": "DDICT",
        "subsurface": "FIELDS",
        "expectation": "Fields resolves table token and lists CATALOG_FIELD rows.",
        "required_runtime_proof": "DDICT FIELDS DDOBJECT or DDATTR field rows.",
    },
    {
        "surface": "DDICT TAGS <table>",
        "command": "DDICT",
        "subsurface": "TAGS",
        "expectation": "Tags resolves table token, reports CDX artifact and LMDB mirror under datadict subroots, and lists CATALOG_TAG rows.",
        "required_runtime_proof": "DDICT TAGS DDATTR and DDOBJECT show CDX/LMDB subroot artifacts.",
    },
    {
        "surface": "DDICT REL <object> [IN|OUT|BOTH]",
        "command": "DDICT",
        "subsurface": "REL",
        "expectation": "Rel resolves object token and shows inbound/outbound DDEDGE relationships.",
        "required_runtime_proof": "DDICT REL DDOBJECT OUT shows HAS_FIELD and HAS_TAG rows.",
    },
    {
        "surface": "DDICT EVIDENCE <object>",
        "command": "DDICT",
        "subsurface": "EVIDENCE",
        "expectation": "Evidence resolves object token and shows direct evidence and attribute evidence sections.",
        "required_runtime_proof": "DDICT EVIDENCE DDOBJECT shows object identity and attribute evidence rows.",
    },
]

CANDIDATE_HELP_PATH = "docs/datadict/reports/DD092A-ddict-help-topic-candidate-generation-v0/generated_help_candidates/DDICT_HELP_TOPIC_CANDIDATE.md"

CMDHELPCHK_CANDIDATES = [
    "src/cli/cmd_cmdhelpchk.cpp",
    "include/cli/cmd_cmdhelpchk.hpp",
    "src/cli/cmdhelpchk.cpp",
    "src/help/cmdhelpchk.cpp",
    "tools/cmdhelp",
    "tools/help",
    "dottalkpp/data/help",
    "docs/cmdhelp",
    "docs/help",
]

PROTECTED_ARTIFACTS = [
    "src/cli/cmd_ddict.cpp",
    "src/datadict/ddict_catalog_paths.cpp",
    "src/cli/cmd_cmdhelpchk.cpp",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
    "src/CMakeLists.txt",
    "dottalkpp/data/help",
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except Exception as exc:
        return {"_read_error": str(exc)}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


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


def artifact_row(repo: Path, rel_path: str, role: str) -> Dict[str, Any]:
    p = repo / rel_path
    return {
        "role": role,
        "path": rel_path,
        "exists": int(p.exists()),
        "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
        "bytes_or_children": p.stat().st_size if p.exists() and p.is_file() else sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else 0,
        "sha256": sha256(p),
    }


def scan_path_for_terms(repo: Path, rel_path: str, max_files: int = 120) -> List[Dict[str, Any]]:
    root = repo / rel_path
    rows: List[Dict[str, Any]] = []
    if not root.exists():
        return rows
    paths: List[Path]
    if root.is_file():
        paths = [root]
    else:
        paths = []
        for p in sorted(root.rglob("*")):
            if len(paths) >= max_files:
                break
            if p.is_file() and p.suffix.lower() in {".cpp", ".hpp", ".h", ".md", ".txt", ".dts", ".csv", ".json"}:
                paths.append(p)

    for p in paths:
        txt = read_text(p)
        upper = txt.upper()
        if any(term in upper for term in ["CMDHELPCHK", "DDICT", "HELP", "COMMANDS.DBF", "HELP_TOPIC"]):
            try:
                rel = p.resolve().relative_to(repo.resolve()).as_posix()
            except Exception:
                rel = p.as_posix()
            rows.append({
                "path": rel,
                "bytes": p.stat().st_size,
                "mentions_cmdhelpchk": int("CMDHELPCHK" in upper),
                "mentions_ddict": int("DDICT" in upper),
                "mentions_help": int("HELP" in upper),
                "mentions_commands_dbf": int("COMMANDS.DBF" in upper),
                "mentions_help_topic": int("HELP_TOPIC" in upper or "HELP_TOPIC.DBF" in upper),
                "sha256": sha256(p),
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD092B CMDHELPCHK expectation mapping")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD092B-cmdhelpchk-expectation-mapping-v0")
    ap.add_argument("--dd092-dir", default="docs/datadict/reports/DD092-datadict-help-cmdhelpchk-integration-plan-v0")
    ap.add_argument("--dd092a-dir", default="docs/datadict/reports/DD092A-ddict-help-topic-candidate-generation-v0")
    ap.add_argument("--dd093c-dir", default="docs/datadict/reports/DD093C-ddict-full-path-remap-runtime-closure-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd092_manifest_path = repo / args.dd092_dir / "dd092_datadict_help_cmdhelpchk_integration_plan_manifest.json"
    dd092a_manifest_path = repo / args.dd092a_dir / "dd092a_ddict_help_topic_candidate_generation_manifest.json"
    dd093c_manifest_path = repo / args.dd093c_dir / "dd093c_ddict_full_path_remap_runtime_closure_manifest.json"

    dd092 = read_json(dd092_manifest_path)
    dd092a = read_json(dd092a_manifest_path)
    dd093c = read_json(dd093c_manifest_path)

    candidate_help = read_text(repo / CANDIDATE_HELP_PATH)
    help_upper = candidate_help.upper()

    mapping_rows = []
    for item in SURFACES:
        surface = item["surface"]
        first_token = surface.split()[0] + " " + surface.split()[1] if len(surface.split()) > 1 else surface
        mapping_rows.append({
            "surface": surface,
            "command": item["command"],
            "subsurface": item["subsurface"],
            "expectation": item["expectation"],
            "required_runtime_proof": item["required_runtime_proof"],
            "candidate_help_mentions_surface": int(surface.replace(" <table>", "").replace(" <object>", "").split("[")[0].strip().upper() in help_upper or first_token.upper() in help_upper),
            "cmdhelpchk_validation_kind": "usage_contract_presence",
            "mutation_now": 0,
        })

    artifact_rows = [
        artifact_row(repo, str(Path(args.dd092_dir) / "dd092_datadict_help_cmdhelpchk_integration_plan_manifest.json"), "dd092_manifest"),
        artifact_row(repo, str(Path(args.dd092a_dir) / "dd092a_ddict_help_topic_candidate_generation_manifest.json"), "dd092a_manifest"),
        artifact_row(repo, str(Path(args.dd093c_dir) / "dd093c_ddict_full_path_remap_runtime_closure_manifest.json"), "dd093c_manifest"),
        artifact_row(repo, CANDIDATE_HELP_PATH, "candidate_help_topic"),
    ]
    for p in CMDHELPCHK_CANDIDATES:
        artifact_rows.append(artifact_row(repo, p, "cmdhelpchk_candidate"))
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))

    mention_rows = []
    for p in CMDHELPCHK_CANDIDATES + ["src/cli", "docs/datadict", "tools/datadict"]:
        mention_rows.extend(scan_path_for_terms(repo, p))

    # Deduplicate mention rows by path.
    seen_paths = set()
    deduped_mentions = []
    for r in mention_rows:
        if r["path"] in seen_paths:
            continue
        seen_paths.add(r["path"])
        deduped_mentions.append(r)
    mention_rows = deduped_mentions

    gap_rows = [
        {
            "gap_id": "B1_CMDHELPCHK_FORMAT",
            "question": "What exact data structure does CMDHELPCHK validate for subcommands?",
            "recommended_resolution": "Use this expectation map as review input; inspect existing CMDHELPCHK implementation before any apply lane.",
            "mutation_now": 0,
        },
        {
            "gap_id": "B2_DDICT_SINGLE_COMMAND_WITH_SUBSURFACES",
            "question": "Should DDICT sub-surfaces be registered as separate help topics or one command topic?",
            "recommended_resolution": "Treat DDICT as one registered command with subcommand sections until existing HELP doctrine requires subtopics.",
            "mutation_now": 0,
        },
        {
            "gap_id": "B3_RUNTIME_FALLBACK_VS_HELP_DATA",
            "question": "Should CMDHELPCHK require external HELP DATA when DDICT HELP is embedded?",
            "recommended_resolution": "Keep embedded DDICT HELP as fallback; CMDHELPCHK should validate canonical coverage later, not remove fallback.",
            "mutation_now": 0,
        },
        {
            "gap_id": "B4_PATH_REMAP_PROVENANCE",
            "question": "Should CMDHELPCHK expectation include Data Dictionary path layout?",
            "recommended_resolution": "Mention path layout in HELP topic notes, but CMDHELPCHK should focus on usage surface coverage.",
            "mutation_now": 0,
        },
    ]

    proposed_rows = [
        {"step": 1, "phase": "map", "action": "Accept DD092B expectation map for DDICT surfaces.", "mutation_now": 0},
        {"step": 2, "phase": "candidate", "action": "Generate CMDHELPCHK candidate rows/rules in DD092C report-only package.", "mutation_now": 0},
        {"step": 3, "phase": "review", "action": "Review candidate against current CMDHELPCHK data format.", "mutation_now": 0},
        {"step": 4, "phase": "apply_later", "action": "Apply HELP/CMDHELPCHK data only with explicit authorization.", "mutation_now": 0},
    ]

    boundary_rows = [
        {"boundary": "cmdhelpchk_expectation_mapping_only", "observed": 1, "required": 1, "pass": 1},
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

    gates = [
        {"gate": "dd092_plan_ready", "expected": EXPECTED_DD092_STATUS, "observed": dd092.get("status", ""), "pass": int(dd092.get("status") == EXPECTED_DD092_STATUS)},
        {"gate": "dd092a_candidate_ready", "expected": EXPECTED_DD092A_STATUS, "observed": dd092a.get("status", ""), "pass": int(dd092a.get("status") == EXPECTED_DD092A_STATUS)},
        {"gate": "dd093c_path_remap_closed", "expected": EXPECTED_DD093C_STATUS, "observed": dd093c.get("status", ""), "pass": int(dd093c.get("status") == EXPECTED_DD093C_STATUS)},
        {"gate": "candidate_help_exists", "expected": 1, "observed": int((repo / CANDIDATE_HELP_PATH).exists()), "pass": int((repo / CANDIDATE_HELP_PATH).exists())},
        {"gate": "surfaces_mapped", "expected": len(SURFACES), "observed": len(mapping_rows), "pass": int(len(mapping_rows) == len(SURFACES))},
        {"gate": "surface_help_mentions", "expected": len(SURFACES), "observed": sum(int(r["candidate_help_mentions_surface"]) for r in mapping_rows), "pass": int(sum(int(r["candidate_help_mentions_surface"]) for r in mapping_rows) == len(SURFACES))},
        {"gate": "cmdhelpchk_mentions_scanned", "expected": ">=0", "observed": len(mention_rows), "pass": 1},
        {"gate": "mapping_report_only", "expected": 1, "observed": 1, "pass": 1},
    ]

    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DDICT_CMDHELPCHK_EXPECTATION_MAPPING_READY" if failures == 0 else "DDICT_CMDHELPCHK_EXPECTATION_MAPPING_REVIEW"

    next_rows = [
        {
            "next_id": "DD092C",
            "title": "CMDHELPCHK candidate row/rule generation",
            "allowed_scope": "report-only candidate generation from DD092B expectation map",
        },
        {
            "next_id": "DD092D",
            "title": "guarded HELP/CMDHELPCHK apply package",
            "allowed_scope": "only after explicit authorization and reviewed candidate rows",
        },
        {
            "next_id": "DD094",
            "title": "Data Dictionary workspace schema savepoint",
            "allowed_scope": "capture ddbase.dtschema, workspace-load proof, and relation policy",
        },
    ]

    write_csv(out / "dd092b_cmdhelpchk_expectation_map.csv", mapping_rows, ["surface", "command", "subsurface", "expectation", "required_runtime_proof", "candidate_help_mentions_surface", "cmdhelpchk_validation_kind", "mutation_now"])
    write_csv(out / "dd092b_artifact_inventory.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd092b_mention_scan.csv", mention_rows, ["path", "bytes", "mentions_cmdhelpchk", "mentions_ddict", "mentions_help", "mentions_commands_dbf", "mentions_help_topic", "sha256"])
    write_csv(out / "dd092b_gap_review.csv", gap_rows, ["gap_id", "question", "recommended_resolution", "mutation_now"])
    write_csv(out / "dd092b_proposed_sequence.csv", proposed_rows, ["step", "phase", "action", "mutation_now"])
    write_csv(out / "dd092b_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd092b_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd092b_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD092B CMDHELPCHK Expectation Mapping

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD092B maps the runtime-proven DDICT command surface to CMDHELPCHK/help validation expectations.

This is report-only. It does not mutate HELP DATA, CMDHELPCHK, source files, command registration,
active catalog DBFs, CDX/LMDB, generated catalog content, or manuals.

## Preconditions

- DD092 status: `{dd092.get('status', '')}`
- DD092A status: `{dd092a.get('status', '')}`
- DD093C status: `{dd093c.get('status', '')}`

## Mapping summary

- DDICT surfaces mapped: **{len(mapping_rows)}**
- Candidate HELP mentions found: **{sum(int(r['candidate_help_mentions_surface']) for r in mapping_rows)} / {len(mapping_rows)}**
- Mention scan rows: **{len(mention_rows)}**

## Validation interpretation

For now, DDICT should be treated as a single command with sub-surfaces:

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

CMDHELPCHK should eventually validate that the command has usage/help coverage for these sub-surfaces, not force
Data Dictionary runtime logic into HELP DATA. The embedded `DDICT HELP` fallback should remain.

## Boundary

DD092B is expectation-mapping/report-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.

## Recommended next lanes

```text
DD092C  CMDHELPCHK candidate row/rule generation
DD092D  guarded HELP/CMDHELPCHK apply package only after explicit authorization
DD094   Data Dictionary workspace schema savepoint
```
"""
    write_text(out / "DD092B_CMDHELPCHK_EXPECTATION_MAPPING_REPORT.md", report)

    manifest = {
        "contract": "dd092b_cmdhelpchk_expectation_mapping_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd092_status": dd092.get("status", ""),
        "dd092a_status": dd092a.get("status", ""),
        "dd093c_status": dd093c.get("status", ""),
        "surfaces_mapped": len(mapping_rows),
        "candidate_help_mentions": sum(int(r["candidate_help_mentions_surface"]) for r in mapping_rows),
        "mention_scan_rows": len(mention_rows),
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
        "next_recommended_action": "DD092C CMDHELPCHK candidate row/rule generation, or DD094 workspace schema savepoint.",
    }
    write_json(out / "dd092b_cmdhelpchk_expectation_mapping_manifest.json", manifest)

    print(f"DD092B CMDHELPCHK expectation mapping manifest: {out / 'dd092b_cmdhelpchk_expectation_mapping_manifest.json'}")
    print(f"status: {status}; surfaces: {len(mapping_rows)}; help_mentions: {manifest['candidate_help_mentions']}/{len(mapping_rows)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
