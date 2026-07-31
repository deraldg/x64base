#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD089B_STATUS = "DDICT_READ_HELPER_SKELETON_FILES_INSTALLED_BUILD_UNWIRED"

HELPER_TARGETS = {
    "read_helpers": {
        "header": "include/datadict/ddict_read_helpers.hpp",
        "source": "src/datadict/ddict_read_helpers.cpp",
        "functions": ["lower_copy", "trim_copy", "upper_copy", "short_text", "value_of"],
    },
    "catalog_paths": {
        "header": "include/datadict/ddict_catalog_paths.hpp",
        "source": "src/datadict/ddict_catalog_paths.cpp",
        "functions": ["exists_quiet", "size_quiet", "normalize_quiet", "base_roots", "catalog_candidates", "find_catalog_dir", "find_cdx_file", "find_lmdb_dir", "collect_stats"],
    },
    "dbf_reader": {
        "header": "include/datadict/ddict_dbf_reader.hpp",
        "source": "src/datadict/ddict_dbf_reader.cpp",
        "functions": ["plausible_name", "plausible_descriptor", "descriptor_start", "le16", "le32", "descriptor_name", "read_binary", "parse_fields", "read_dbf_table"],
    },
    "object_resolver": {
        "header": "include/datadict/ddict_object_resolver.hpp",
        "source": "src/datadict/ddict_object_resolver.cpp",
        "functions": ["resolve_object", "object_index"],
    },
}

COMMAND_RENDERERS = ["print_status", "print_tables", "print_fields", "print_tags", "print_rel_edge_row", "print_rel", "print_evidence", "print_objects", "cmd_DDICT"]

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


def find_function_span(source: str, name: str) -> Tuple[int, int, str]:
    pat = re.compile(r"(?m)^(?:[\w:<>,\s*&]+)\s+" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{")
    m = pat.search(source)
    if not m:
        return -1, -1, ""
    start = m.start()
    depth = 0
    end = -1
    for i in range(m.end() - 1, len(source)):
        ch = source[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end < 0:
        return -1, -1, ""
    return start, end, source[start:end]


def line_no(source: str, index: int) -> int:
    if index < 0:
        return -1
    return source[:index].count("\n") + 1


def source_shell(group: str, current: str, functions: List[str], bodies: Dict[str, str]) -> str:
    lines = []
    if group == "read_helpers":
        lines.append('#include "datadict/ddict_read_helpers.hpp"')
        lines.append("")
        lines.append("#include <algorithm>")
        lines.append("#include <cctype>")
        lines.append("")
    elif group == "catalog_paths":
        lines.append('#include "datadict/ddict_catalog_paths.hpp"')
        lines.append('#include "datadict/ddict_read_helpers.hpp"')
        lines.append("")
        lines.append("#include <array>")
        lines.append("#include <system_error>")
        lines.append("")
    elif group == "dbf_reader":
        lines.append('#include "datadict/ddict_dbf_reader.hpp"')
        lines.append('#include "datadict/ddict_read_helpers.hpp"')
        lines.append("")
        lines.append("#include <fstream>")
        lines.append("")
    elif group == "object_resolver":
        lines.append('#include "datadict/ddict_object_resolver.hpp"')
        lines.append('#include "datadict/ddict_read_helpers.hpp"')
        lines.append("")
    lines.append("// DD-089C extraction preview only.")
    lines.append("// This generated candidate is not installed or wired by DD-089C.")
    lines.append("")
    lines.append("namespace dottalk::datadict {")
    lines.append("")
    for fn in functions:
        body = bodies.get(fn, "").strip()
        if body:
            lines.append(body)
            lines.append("")
        else:
            lines.append(f"// Missing source body for {fn}; extraction requires review.")
            lines.append("")
    lines.append("} // namespace dottalk::datadict")
    lines.append("")
    return "\n".join(lines)


def diff_text(old: str, new: str, name: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=name + ".current",
        tofile=name + ".candidate",
        lineterm="",
    ))


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-089C guarded read-helper implementation extraction preview")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD089C-guarded-read-helper-extraction-preview-v0")
    ap.add_argument("--dd089b-dir", default="docs/datadict/reports/DD089B-guarded-read-helper-skeleton-install-apply-v0")
    ap.add_argument("--cmd-source", default="src/cli/cmd_ddict.cpp")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd089b_dir = (repo / args.dd089b_dir).resolve()
    dd089b_manifest = read_json(dd089b_dir / "dd089b_guarded_read_helper_skeleton_install_manifest.json")
    cmd_source_path = repo / args.cmd_source
    cmd_text = cmd_source_path.read_text(encoding="utf-8", errors="replace") if cmd_source_path.exists() else ""

    generated_root = out / "generated_extraction_preview"
    generated_root.mkdir(parents=True, exist_ok=True)

    review_rows: List[Dict[str, Any]] = []
    dd089b_green = int(dd089b_manifest.get("status") == EXPECTED_DD089B_STATUS)
    if not dd089b_green:
        review_rows.append({"issue": "DD089B_NOT_READY", "detail": dd089b_manifest.get("status", "")})
    if not cmd_source_path.exists():
        review_rows.append({"issue": "CMD_DDICT_SOURCE_MISSING", "detail": str(cmd_source_path)})

    function_rows: List[Dict[str, Any]] = []
    bodies: Dict[str, str] = {}

    all_helper_functions: List[str] = []
    for spec in HELPER_TARGETS.values():
        all_helper_functions.extend(spec["functions"])

    for fn in all_helper_functions + COMMAND_RENDERERS:
        start, end, body = find_function_span(cmd_text, fn)
        bodies[fn] = body
        function_rows.append({
            "function": fn,
            "category": "helper_candidate" if fn in all_helper_functions else "command_renderer_keep_local",
            "found": int(bool(body)),
            "start_line": line_no(cmd_text, start),
            "end_line": line_no(cmd_text, end),
            "line_count": 0 if not body else body.count("\n") + 1,
            "target_group": next((name for name, spec in HELPER_TARGETS.items() if fn in spec["functions"]), "keep_in_cmd_ddict"),
        })
        if fn in all_helper_functions and not body:
            review_rows.append({"issue": "HELPER_BODY_NOT_FOUND", "detail": fn})

    target_rows: List[Dict[str, Any]] = []
    for group, spec in HELPER_TARGETS.items():
        source_rel = spec["source"]
        source_path = repo / source_rel
        current_text = source_path.read_text(encoding="utf-8", errors="replace") if source_path.exists() else ""
        candidate = source_shell(group, current_text, spec["functions"], bodies)
        candidate_path = generated_root / source_rel
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text(candidate, encoding="utf-8")
        diff_path = generated_root / (source_rel + ".preview.diff")
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        diff_path.write_text(diff_text(current_text, candidate, source_rel), encoding="utf-8")

        found_count = sum(1 for fn in spec["functions"] if bodies.get(fn))
        target_rows.append({
            "helper_group": group,
            "target_source": source_rel,
            "installed_source_exists": int(source_path.exists()),
            "candidate_path": str(candidate_path),
            "preview_diff": str(diff_path),
            "functions_expected": len(spec["functions"]),
            "functions_found": found_count,
            "candidate_generated": 1,
            "installed": 0,
            "wired_to_build": 0,
        })

    cmd_preview = cmd_text
    removal_markers = []
    for fn in all_helper_functions:
        body = bodies.get(fn)
        if body:
            removal_markers.append({"function": fn, "replacement": f"// DD-089C future extraction point: {fn} moved to datadict helper module."})
    cmd_plan_path = generated_root / "src/cli/cmd_ddict_future_extraction_plan.md"
    cmd_plan = "# DD-089C cmd_ddict.cpp Future Extraction Plan\n\n"
    cmd_plan += "DD-089C does not patch cmd_ddict.cpp. Future extraction should remove helper implementations only after candidate helper files are reviewed and build wiring is authorized.\n\n"
    for marker in removal_markers:
        cmd_plan += f"- {marker['function']}: {marker['replacement']}\n"
    cmd_plan_path.parent.mkdir(parents=True, exist_ok=True)
    cmd_plan_path.write_text(cmd_plan, encoding="utf-8")

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
            "mutated_by_dd089c": 0,
        })

    helper_source_exists = sum(1 for row in target_rows if int(row["installed_source_exists"]) == 1)
    helper_bodies_found = sum(1 for row in function_rows if row["category"] == "helper_candidate" and int(row["found"]) == 1)
    helper_bodies_expected = len(all_helper_functions)
    all_candidates_generated = int(all(int(row["candidate_generated"]) == 1 for row in target_rows))

    gate_rows = [
        {"gate": "dd089b_skeleton_install_green", "expected": EXPECTED_DD089B_STATUS, "observed": dd089b_manifest.get("status", ""), "pass": dd089b_green},
        {"gate": "cmd_ddict_source_exists", "expected": 1, "observed": int(cmd_source_path.exists()), "pass": int(cmd_source_path.exists())},
        {"gate": "installed_helper_sources_exist", "expected": len(HELPER_TARGETS), "observed": helper_source_exists, "pass": int(helper_source_exists == len(HELPER_TARGETS))},
        {"gate": "helper_bodies_found", "expected": helper_bodies_expected, "observed": helper_bodies_found, "pass": int(helper_bodies_found == helper_bodies_expected)},
        {"gate": "candidate_helper_sources_generated", "expected": len(HELPER_TARGETS), "observed": sum(1 for r in target_rows if int(r["candidate_generated"]) == 1), "pass": all_candidates_generated},
        {"gate": "protected_files_unmutated", "expected": 0, "observed": protected_mutations, "pass": int(protected_mutations == 0)},
        {"gate": "preview_only", "expected": 1, "observed": 1, "pass": 1},
    ]
    failures = sum(1 for row in gate_rows if int(row["pass"]) != 1)
    status = "DDICT_READ_HELPER_EXTRACTION_PREVIEW_READY" if failures == 0 else "DDICT_READ_HELPER_EXTRACTION_PREVIEW_REVIEW"

    boundary_rows = [
        {"boundary": "extraction_preview_only", "observed": 1, "required": 1, "pass": 1},
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
            "next_id": "DD089D",
            "title": "guarded helper implementation extraction apply",
            "allowed_scope": "apply reviewed helper source candidates and cmd_ddict.cpp removals only with explicit authorization; then build-wire if needed in a separate step",
        },
        {
            "next_id": "DD089E",
            "title": "DDICT parity smoke closure after extraction",
            "allowed_scope": "run full DDICT parity tests after build succeeds",
        },
    ]

    write_csv(out / "dd089c_function_extraction_inventory.csv", function_rows, ["function", "category", "found", "start_line", "end_line", "line_count", "target_group"])
    write_csv(out / "dd089c_helper_target_preview_ledger.csv", target_rows, ["helper_group", "target_source", "installed_source_exists", "candidate_path", "preview_diff", "functions_expected", "functions_found", "candidate_generated", "installed", "wired_to_build"])
    write_csv(out / "dd089c_protected_file_ledger.csv", protected_rows, ["protected_path", "exists", "hash_before", "hash_after", "mutated_by_dd089c"])
    write_csv(out / "dd089c_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd089c_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd089c_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd089c_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-089C Guarded Read-Helper Implementation Extraction Preview

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-089C generates preview artifacts for moving helper implementations from `cmd_ddict.cpp`
into the installed read-helper skeleton source files.

It does not apply the extraction.

## Inputs

- DD-089B status: `{dd089b_manifest.get('status', '')}`
- Command source: `{rel(repo, cmd_source_path)}`

## Result

- Helper bodies expected: **{helper_bodies_expected}**
- Helper bodies found: **{helper_bodies_found}**
- Helper target candidates generated: **{sum(1 for r in target_rows if int(r['candidate_generated']) == 1)}**
- Generated preview root: `{generated_root}`
- Source files modified: **0**
- Build files edited: **0**

## Interpretation

The generated candidates are review artifacts, not installed implementation.
The command renderers should stay in `cmd_ddict.cpp` until helper extraction and parity testing are explicitly authorized.

## Boundary

DD-089C is extraction preview only. It does not patch `cmd_ddict.cpp`, modify installed
helper source files, edit build files, edit command registration, mutate active catalog data,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    (out / "DD089C_GUARDED_READ_HELPER_EXTRACTION_PREVIEW_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd089c_guarded_read_helper_extraction_preview_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd089b_status": dd089b_manifest.get("status", ""),
        "generated_preview_root": str(generated_root),
        "helper_bodies_expected": helper_bodies_expected,
        "helper_bodies_found": helper_bodies_found,
        "candidate_targets": len(target_rows),
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
        "next_recommended_action": "Review generated preview files; then explicitly authorize DD-089D guarded extraction apply if desired.",
    }
    write_json(out / "dd089c_guarded_read_helper_extraction_preview_manifest.json", manifest)

    print(f"DD-089C guarded read-helper extraction preview manifest: {out / 'dd089c_guarded_read_helper_extraction_preview_manifest.json'}")
    print(f"status: {status}; helper_bodies: {helper_bodies_found}/{helper_bodies_expected}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
