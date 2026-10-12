#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: datadict
# layer: tooling
# project: project.x64base.runtime
# owner: member.derald
# status: experimental
# @dottalk.end
"""Bounded, report-only DDICT curation inventory. Never executes inventoried tools.

Reads only explicit files and direct children of the directories below. Uses the
repository DBF reader; memo pointers remain unresolved. Writes one JSON report
under docs/maintenance/reviews. Does not select, migrate, or repair catalogs.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
TOOL_DIRS = (
    "baseline", "catalog", "diff", "disposition", "extractors", "orchestrate",
    "parsers", "reconcile", "review", "validate",
)
LEGACY = (
    "DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE", "DDEVID",
    "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE",
)
PAIRS = {
    "DDRUN": ("DATA_DICTIONARY_RUNS", "RUNID", "RUN_RECORD_ID"),
    "DDOBJECT": ("DATA_DICTIONARY_OBJECTS", "OBJID", "CATALOG_OBJECT_ID"),
    "DDATTR": ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", "ATTRID", "CATALOG_ATTRIBUTE_ID"),
    "DDEDGE": ("DATA_DICTIONARY_RELATION_EDGES", "EDGEID", "RELATION_EDGE_ID"),
    "DDEVID": ("DATA_DICTIONARY_EVIDENCE_RECORDS", "EVID", "EVIDENCE_RECORD_ID"),
    "DDGATE": ("DATA_DICTIONARY_GATE_RECORDS", "GATEID", "GATE_RECORD_ID"),
}
TRIAGE = "docs/datadict/reports/DD096ZD2ZG-post-apply-smoke-triage-v0"
EXECUTION = "docs/datadict/reports/DD096ZD2ZF-guarded-active-replacement-execution-v0"
EXPLICIT = {
    "src/cli/cmd_ddict.cpp": "active-command-source",
    "include/cli/cmd_ddict.hpp": "active-command-header",
    "src/cli/shell_commands.cpp": "shared-registration-consumer",
    "src/gui/wx/main_frame.cpp": "shared-gui-consumer",
    "src/gui/core/CMakeLists.txt": "shared-build-consumer",
    "src/CMakeLists.txt": "shared-build-consumer",
    "src/help/helpdata_messages.cpp": "shared-help-consumer",
    "src/tests/test_ddict_catalog_dir.cpp": "focused-regression-source",
    "src/tests/CMakeLists.txt": "shared-test-registration",
    "dottalkpp/data/workspaces/ddbase.dtschema": "legacy-workspace-consumer",
    "dottalkpp/data/scripts/ddict_help.dts": "runtime-script",
    "docs/datadict/README.md": "maintained-entry-point",
    "tools/datadict/README.md": "maintained-entry-point",
    "labtalk/ai_portal/PORTAL_SEARCH_MAP_V1.md": "maintained-navigation",
    "docs/datadict/specs/README.md": "historical-status-index",
    "docs/datadict/policy/DD095_DATADICT_LAYOUT_POLICY.md": "historical-layout-policy",
    "docs/datadict/policy/DD096_DATADICT_SCHEMA_PROMOTION_POLICY.md": "historical-promotion-policy",
    "docs/datadict/baselines/current_baseline.json": "baseline-pointer",
    "docs/datadict/reports/DD098_DATADICT_BASELINE_CLOSEOUT.md": "historical-closeout",
    f"{EXECUTION}/dd096zd2zf_active_replacement_execution_manifest.json": "historical-execution-record",
    f"{EXECUTION}/dd096zd2zf_execution_copy_plan.csv": "historical-copy-plan",
    f"{TRIAGE}/dd096zd2zg_post_apply_smoke_triage_manifest.json": "historical-triage-record",
    f"{TRIAGE}/DD096ZD2ZG_POST_APPLY_SMOKE_TRIAGE_REPORT.md": "historical-triage-record",
    "docs/maintenance/reviews/DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md": "historical-help-proof",
    "docs/maintenance/reviews/DDICT_CROSSWALK_2026-10-09.md": "current-review",
    "docs/maintenance/reviews/DDICT_CATALOG_AUTHORITY_2026-10-09.md": "current-review",
    "docs/maintenance/reviews/DDICT_CONSOLIDATION_PLAN_2026-10-09.md": "current-review",
    "tools/fullstack_docs/dbfread.py": "shared-read-only-parser",
    "tools/datadict/dd-status.ps1": "status-wrapper-review-before-use",
}


def safe_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Path leaves repository: {relative}")
    return path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool_metadata(path: Path) -> dict:
    """Extract declared documentation/options without importing or running code."""
    if path.suffix != ".py":
        return {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        flags = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "add_argument":
                    flags.update(arg.value for arg in node.args
                                 if isinstance(arg, ast.Constant)
                                 and isinstance(arg.value, str)
                                 and arg.value.startswith("--"))
        doc = ast.get_docstring(tree) or ""
        return {"declared_summary": doc.splitlines()[0] if doc else "",
                "declared_options": sorted(flags),
                "safety_assessment": "not-certified-by-static-inventory"}
    except (SyntaxError, UnicodeError) as exc:
        return {"metadata_error": str(exc)}


def collect() -> dict:
    sys.path.insert(0, str(ROOT / "tools/fullstack_docs"))
    import dbfread

    selected = dict(EXPLICIT)
    scopes = {"src/datadict": "active-helper-source",
              "include/datadict": "active-helper-header",
              "dottalkpp/scripts/datadict": "runtime-template"}
    scopes.update({f"dottalkpp/scripts/datadict/{part}": "runtime-template"
                   for part in ("capture_templates", "proof_templates", "staging_templates", "templates")})
    scopes.update({f"tools/datadict/{part}": "engineering-tool-review-required"
                   for part in TOOL_DIRS})
    errors = []
    for relative, role in scopes.items():
        folder = safe_path(relative)
        if not folder.is_dir():
            errors.append(f"Missing inventory directory: {relative}")
            continue
        for path in sorted(folder.iterdir()):
            if path.is_file() and not path.is_symlink():
                selected[path.relative_to(ROOT).as_posix()] = role
    catalog = safe_path("dottalkpp/data/datadict")
    for folder, role in ((catalog, "catalog-data-preserve"),
                         (catalog / "datadict", "nested-copy-review-required")):
        if folder.is_dir():
            for path in sorted(folder.iterdir()):
                if path.is_file() and path.suffix.lower() in {".dbf", ".dtx", ".dbt"}:
                    selected[path.relative_to(ROOT).as_posix()] = role

    prefixes = list(scopes) + list(EXPLICIT) + ["dottalkpp/data/datadict"]
    tracked = set(subprocess.check_output(
        ["git", "ls-files", "--", *prefixes], cwd=ROOT, text=True).splitlines())
    ignored = subprocess.run(
        ["git", "check-ignore", "--stdin"], cwd=ROOT,
        input="\n".join(selected) + "\n", text=True, capture_output=True)
    if ignored.returncode not in (0, 1):
        raise RuntimeError(ignored.stderr)
    ignored_paths = set(ignored.stdout.splitlines())
    files = []
    for relative, role in sorted(selected.items()):
        path = safe_path(relative)
        if not path.is_file():
            errors.append(f"Missing explicit file: {relative}")
            continue
        item = {"path": relative, "role": role, "bytes": path.stat().st_size,
                "sha256": sha(path), "tracked": relative in tracked,
                "ignored": relative in ignored_paths,
                "owner": "member.derald (repository owner; individual tool steward unverified)",
                "disposition": "retain-in-place",
                "replacement": None}
        if relative.startswith("tools/datadict/"):
            item.update(tool_metadata(path))
        files.append(item)

    tables, rows = {}, {}
    for name in (*LEGACY, *(pair[0] for pair in PAIRS.values())):
        path = catalog / (name + ".dbf")
        try:
            table = dbfread.read(path)
            rows[name] = table.rows
            tables[name] = {"live_rows": table.live, "header_rows": table.header_rows,
                            "deleted_rows": table.deleted,
                            "fields": [{"name": f.name, "type": f.type, "width": f.width}
                                       for f in table.fields]}
            type_field = "OBJTYPE" if name == "DDOBJECT" else "CATALOG_OBJECT_TYPE"
            if name in {"DDOBJECT", "DATA_DICTIONARY_OBJECTS"}:
                tables[name]["object_types"] = dict(Counter(r[type_field] for r in table.rows))
                tables[name]["objects"] = list(table.rows)
        except (OSError, RuntimeError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
    comparisons = []
    for legacy, (long_name, legacy_id, long_id) in PAIRS.items():
        if legacy not in rows or long_name not in rows:
            continue
        left_fields = {f["name"] for f in tables[legacy]["fields"]}
        right_fields = {f["name"] for f in tables[long_name]["fields"]}
        if legacy_id not in left_fields or long_id not in right_fields:
            errors.append(f"Identifier mapping needs review: {legacy}/{long_name}")
            continue
        left, right = {r[legacy_id] for r in rows[legacy]}, {r[long_id] for r in rows[long_name]}
        comparisons.append({"legacy": legacy, "long_name": long_name,
                            "legacy_id": legacy_id, "long_id": long_id,
                            "shared_ids": sorted(left & right),
                            "legacy_only_ids": sorted(left - right),
                            "long_only_ids": sorted(right - left)})
    duplicate_pairs = []
    for name in LEGACY:
        parent, nested = catalog / (name + ".dbf"), catalog / "datadict" / (name + ".dbf")
        if parent.is_file() and nested.is_file():
            duplicate_pairs.append({"source": nested.relative_to(ROOT).as_posix(),
                                    "retain": parent.relative_to(ROOT).as_posix(),
                                    "source_sha256": sha(nested), "retain_sha256": sha(parent),
                                    "identical": sha(nested) == sha(parent),
                                    "proposed_action": "hold-pending-sidecar-and-reference-review"})
    by_path = {entry["path"]: entry for entry in files}
    consolidation_candidates = []
    for entry in files:
        if entry["role"] != "nested-copy-review-required":
            continue
        retained_path = entry["path"].replace("/datadict/datadict/", "/datadict/")
        retained = by_path.get(retained_path)
        consolidation_candidates.append({"source": entry["path"],
            "retain": retained_path,
            "proposed_archive": "docs/datadict/backups/curation_20261009/nested_catalog/" + Path(entry["path"]).name,
            "source_sha256": entry["sha256"],
            "retain_sha256": retained["sha256"] if retained else None,
            "identical": bool(retained and entry["sha256"] == retained["sha256"]),
            "action": "planned-only-no-move",
            "prerequisites": ["fresh hash match", "exact-scope approval", "consumer and fallback proof",
                              "complete sidecar/index dependency review", "archive and restore proof"]})
    historical_copy_comparison = []
    with safe_path(f"{EXECUTION}/dd096zd2zf_execution_copy_plan.csv").open(encoding="utf-8-sig", newline="") as stream:
        for entry in csv.DictReader(stream):
            target = Path(entry["Target"])
            if entry["Kind"] != "file" or target.suffix.lower() != ".dbf":
                continue
            # The historical ledger uses Windows paths; the basename alone is
            # portable. Do not use its absolute path as authority for a read.
            filename = entry["Target"].replace("\\", "/").rsplit("/", 1)[-1]
            if filename not in {p[0] + ".dbf" for p in PAIRS.values()}:
                errors.append(f"Unexpected historical copy target: {filename}")
                continue
            active = catalog / filename
            historical_copy_comparison.append({"path": active.relative_to(ROOT).as_posix(),
                "recorded_source_sha256": entry["SourceSha256"].lower(),
                "current_sha256": sha(active),
                "matches_recorded_source": sha(active) == entry["SourceSha256"].lower()})
    return {"schema": "ddict-curation-inventory-v1", "created_utc": datetime.now(timezone.utc).isoformat(),
            "baseline_commit": subprocess.check_output(["git", "log", "-1", "--format=%H"], cwd=ROOT, text=True).strip(),
            "enumeration": "explicit files and direct children only; no recursive discovery",
            "limitations": ["No runtime execution", "Memo pointers unresolved", "No index integrity checks",
                            "Tool options are declarations, not safety certification", "No mutation or deletion authorization"],
            "directory_scopes": scopes, "files": files, "catalog_tables": tables,
            "family_comparisons": comparisons, "duplicate_dbf_pairs": duplicate_pairs,
            "historical_copy_comparison": historical_copy_comparison,
            "consolidation_candidates": consolidation_candidates,
            "historical_records": {
                relative: json.loads(safe_path(relative).read_text(encoding="utf-8-sig"))
                for relative in (
                    f"{EXECUTION}/dd096zd2zf_active_replacement_execution_manifest.json",
                    f"{TRIAGE}/dd096zd2zg_post_apply_smoke_triage_manifest.json")},
            "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="JSON path under docs/maintenance/reviews")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if not output.is_relative_to(safe_path("docs/maintenance/reviews")) or output.suffix != ".json":
        parser.error("output must be a .json file under docs/maintenance/reviews")
    if output.exists():
        try:
            existing = json.loads(output.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            parser.error(f"refusing to overwrite an unrelated or unreadable report: {exc}")
        if not isinstance(existing, dict) or existing.get("schema") != "ddict-curation-inventory-v1":
            parser.error("refusing to overwrite an unrelated report")
    result = collect()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "files": len(result["files"]),
                      "tables": len(result["catalog_tables"]), "errors": result["errors"]}))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
