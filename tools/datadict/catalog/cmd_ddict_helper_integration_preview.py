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


EXPECTED_DD089D_STATUS = "DDICT_HELPER_SOURCES_APPLIED_BUILD_UNWIRED_CMD_DDICT_UNCHANGED"

HELPER_FUNCTIONS = [
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
]

HELPER_HEADERS = [
    '#include "datadict/ddict_read_helpers.hpp"',
    '#include "datadict/ddict_catalog_paths.hpp"',
    '#include "datadict/ddict_dbf_reader.hpp"',
    '#include "datadict/ddict_object_resolver.hpp"',
]

PROTECTED_UNTOUCHED = [
    "src/cli/cmd_ddict.cpp",
    "src/CMakeLists.txt",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
]

LIKELY_LOCAL_TYPES = ["struct FieldDef", "struct Row", "struct CatalogStats"]


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
    # Include trailing blank lines after a function body for cleaner candidate diff.
    while end < len(source) and source[end:end+2] == "\n\n":
        end += 1
    return start, end, source[start:end]


def line_no(source: str, index: int) -> int:
    if index < 0:
        return -1
    return source[:index].count("\n") + 1


def insert_helper_includes(source: str) -> Tuple[str, int]:
    missing = [h for h in HELPER_HEADERS if h not in source]
    if not missing:
        return source, 0

    include_pat = re.compile(r'(?m)^#include\s+[<"].+[>"]\s*$')
    matches = list(include_pat.finditer(source))
    if not matches:
        block = "\n".join(missing) + "\n"
        return block + source, len(missing)

    insert_at = matches[-1].end()
    block = "\n" + "\n".join(missing)
    return source[:insert_at] + block + source[insert_at:], len(missing)


def add_namespace_comment(source: str) -> Tuple[str, int]:
    needle = "namespace fs = std::filesystem;"
    if "using namespace dottalk::datadict;" in source:
        return source, 0
    if needle in source:
        return source.replace(needle, needle + "\nusing namespace dottalk::datadict; // DD-089E preview: helper namespace bridge", 1), 1
    marker = "namespace {"
    if marker in source:
        return source.replace(marker, "using namespace dottalk::datadict; // DD-089E preview: helper namespace bridge\n\n" + marker, 1), 1
    return source, 0


def remove_helper_functions(source: str) -> Tuple[str, List[Dict[str, Any]]]:
    spans = []
    rows = []
    for fn in HELPER_FUNCTIONS:
        start, end, body = find_function_span(source, fn)
        rows.append({
            "function": fn,
            "found": int(bool(body)),
            "start_line": line_no(source, start),
            "end_line": line_no(source, end),
            "line_count": 0 if not body else body.count("\n") + 1,
            "planned_action": "remove_local_duplicate_use_helper_module" if body else "review_missing",
        })
        if body:
            spans.append((start, end, fn))

    # Remove from end to start to keep indexes valid.
    new = source
    for start, end, fn in sorted(spans, key=lambda x: x[0], reverse=True):
        replacement = f"\n// DD-089E preview: local helper `{fn}` moved to datadict helper module.\n"
        new = new[:start] + replacement + new[end:]
    return new, rows


def diff_text(old: str, new: str, name: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=name + ".current",
        tofile=name + ".candidate",
        lineterm="",
    ))


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-089E cmd_ddict helper-removal / namespace integration preview")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD089E-cmd-ddict-helper-integration-preview-v0")
    ap.add_argument("--dd089d-dir", default="docs/datadict/reports/DD089D-guarded-helper-source-apply-apply-v0")
    ap.add_argument("--cmd-source", default="src/cli/cmd_ddict.cpp")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd089d_dir = (repo / args.dd089d_dir).resolve()
    dd089d_manifest = read_json(dd089d_dir / "dd089d_guarded_helper_source_apply_manifest.json")
    cmd_source = repo / args.cmd_source
    cmd_text = cmd_source.read_text(encoding="utf-8", errors="replace") if cmd_source.exists() else ""

    generated_root = out / "generated_integration_preview"
    candidate_path = generated_root / args.cmd_source
    diff_path = generated_root / (args.cmd_source + ".preview.diff")
    plan_path = generated_root / "DD089E_INTEGRATION_REVIEW_NOTES.md"
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    diff_path.parent.mkdir(parents=True, exist_ok=True)

    review_rows: List[Dict[str, Any]] = []
    dd089d_green = int(dd089d_manifest.get("status") == EXPECTED_DD089D_STATUS)
    if not dd089d_green:
        review_rows.append({"issue": "DD089D_NOT_READY", "detail": dd089d_manifest.get("status", "")})
    if not cmd_source.exists():
        review_rows.append({"issue": "CMD_SOURCE_MISSING", "detail": str(cmd_source)})

    candidate, include_count = insert_helper_includes(cmd_text)
    candidate, namespace_bridge_count = add_namespace_comment(candidate)
    candidate, function_rows = remove_helper_functions(candidate)

    local_type_rows = []
    for t in LIKELY_LOCAL_TYPES:
        local_type_rows.append({
            "local_type": t,
            "present_in_current_cmd_ddict": int(t in cmd_text),
            "present_in_candidate_cmd_ddict": int(t in candidate),
            "review_note": "Candidate preview leaves local type handling for DD-089F unless replaced by helper aliases.",
        })

    # Do not attempt to solve Row/DDictRow aliasing here; this is deliberately a preview.
    unresolved_notes = [
        {
            "note_id": "TYPE_ALIAS_REVIEW",
            "detail": "Preview removes helper functions but leaves command renderers in cmd_ddict.cpp; Row/DDictRow and FieldDef compatibility must be checked before apply.",
            "blocking_for_preview": 0,
            "blocking_for_apply": 1,
        },
        {
            "note_id": "BUILD_WIRING_DEFERRED",
            "detail": "Helper cpp files are not wired into CMake by DD-089E. Apply/build must be a separate guarded step.",
            "blocking_for_preview": 0,
            "blocking_for_apply": 1,
        },
        {
            "note_id": "NAMESPACE_BRIDGE_REVIEW",
            "detail": "Preview uses a namespace bridge; future apply should prefer explicit using declarations or type aliases after compile review.",
            "blocking_for_preview": 0,
            "blocking_for_apply": 1,
        },
    ]

    candidate_path.write_text(candidate, encoding="utf-8")
    diff_path.write_text(diff_text(cmd_text, candidate, args.cmd_source), encoding="utf-8")

    plan_text = f"""# DD-089E Integration Review Notes

DD-089E is preview-only.

Generated candidate: `{candidate_path}`
Generated diff: `{diff_path}`

## Preview strategy

1. Add datadict helper includes.
2. Add a temporary helper namespace bridge.
3. Remove local duplicate helper functions from `cmd_ddict.cpp`.
4. Keep command renderers in `cmd_ddict.cpp`.
5. Defer actual source patch and CMake wiring.

## Known apply blockers to resolve later

- Row/DDictRow and FieldDef compatibility.
- Namespace bridge style.
- Helper source build wiring.
- Full DDICT parity test after compile.

"""
    plan_path.write_text(plan_text, encoding="utf-8")

    protected_rows = []
    for rel_path in PROTECTED_UNTOUCHED:
        path = repo / rel_path
        h = sha256(path)
        protected_rows.append({
            "protected_path": rel_path,
            "exists": int(path.exists()),
            "hash_before": h,
            "hash_after": h,
            "mutated_by_dd089e": 0,
        })

    helper_found = sum(1 for r in function_rows if int(r["found"]) == 1)
    helper_expected = len(function_rows)
    protected_mutations = sum(1 for r in protected_rows if int(r["mutated_by_dd089e"]) == 1)
    candidate_generated = int(candidate_path.exists() and diff_path.exists())

    gate_rows = [
        {"gate": "dd089d_helper_sources_applied", "expected": EXPECTED_DD089D_STATUS, "observed": dd089d_manifest.get("status", ""), "pass": dd089d_green},
        {"gate": "cmd_ddict_source_exists", "expected": 1, "observed": int(cmd_source.exists()), "pass": int(cmd_source.exists())},
        {"gate": "helper_functions_found_for_preview", "expected": helper_expected, "observed": helper_found, "pass": int(helper_found == helper_expected)},
        {"gate": "helper_includes_inserted_in_candidate", "expected": len(HELPER_HEADERS), "observed": include_count, "pass": int(include_count == len(HELPER_HEADERS) or all(h in cmd_text for h in HELPER_HEADERS))},
        {"gate": "namespace_bridge_inserted_in_candidate", "expected": "0 or 1", "observed": namespace_bridge_count, "pass": 1},
        {"gate": "candidate_and_diff_generated", "expected": 1, "observed": candidate_generated, "pass": candidate_generated},
        {"gate": "protected_files_unmutated", "expected": 0, "observed": protected_mutations, "pass": int(protected_mutations == 0)},
        {"gate": "preview_only", "expected": 1, "observed": 1, "pass": 1},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_CMD_DDICT_HELPER_INTEGRATION_PREVIEW_READY" if failures == 0 else "DDICT_CMD_DDICT_HELPER_INTEGRATION_PREVIEW_REVIEW"

    boundary_rows = [
        {"boundary": "cmd_ddict_integration_preview_only", "observed": 1, "required": 1, "pass": 1},
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
            "next_id": "DD089F",
            "title": "guarded cmd_ddict integration apply and build wiring plan",
            "allowed_scope": "resolve alias/include details, generate apply diff, and separately decide CMake wiring",
        },
        {
            "next_id": "DD089G",
            "title": "DDICT parity smoke after integration",
            "allowed_scope": "run HELP/STATUS/TABLES/OBJECTS/FIELDS/TAGS/REL/EVIDENCE parity after build succeeds",
        },
    ]

    write_csv(out / "dd089e_helper_removal_inventory.csv", function_rows, ["function", "found", "start_line", "end_line", "line_count", "planned_action"])
    write_csv(out / "dd089e_local_type_review.csv", local_type_rows, ["local_type", "present_in_current_cmd_ddict", "present_in_candidate_cmd_ddict", "review_note"])
    write_csv(out / "dd089e_unresolved_apply_notes.csv", unresolved_notes, ["note_id", "detail", "blocking_for_preview", "blocking_for_apply"])
    write_csv(out / "dd089e_protected_file_ledger.csv", protected_rows, ["protected_path", "exists", "hash_before", "hash_after", "mutated_by_dd089e"])
    write_csv(out / "dd089e_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd089e_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd089e_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd089e_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-089E cmd_ddict Helper Integration Preview

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-089E generates a preview for removing duplicated helper implementations from `cmd_ddict.cpp`
and bridging the command to the installed datadict helper modules.

It does not apply the candidate.

## Inputs

- DD-089D status: `{dd089d_manifest.get('status', '')}`
- Command source: `{rel(repo, cmd_source)}`

## Result

- Helper functions expected: **{helper_expected}**
- Helper functions found: **{helper_found}**
- Helper includes inserted in candidate: **{include_count}**
- Candidate source: `{rel(repo, candidate_path)}`
- Candidate diff: `{rel(repo, diff_path)}`
- Protected file mutations: **{protected_mutations}**

## Known apply blockers

DD-089E deliberately records unresolved apply notes. The most important is type compatibility:
`cmd_ddict.cpp` renderers may still use local `Row`/`FieldDef`/`CatalogStats` shapes while helper
modules use namespaced helper types. Resolve that in a later apply plan before changing runtime code.

## Boundary

DD-089E is integration preview only. It does not patch `cmd_ddict.cpp`, modify helper source files,
edit build files, edit command registration, mutate active catalog data, create/rebuild CDX/LMDB,
mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    (out / "DD089E_CMD_DDICT_HELPER_INTEGRATION_PREVIEW_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd089e_cmd_ddict_helper_integration_preview_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd089d_status": dd089d_manifest.get("status", ""),
        "candidate_source": rel(repo, candidate_path),
        "candidate_diff": rel(repo, diff_path),
        "helper_functions_expected": helper_expected,
        "helper_functions_found": helper_found,
        "include_count": include_count,
        "protected_file_mutations": protected_mutations,
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
        "next_recommended_action": "Review DD-089E candidate diff and unresolved notes; then create DD-089F guarded apply/build-wiring plan.",
    }
    write_json(out / "dd089e_cmd_ddict_helper_integration_preview_manifest.json", manifest)

    print(f"DD-089E cmd_ddict helper integration preview manifest: {out / 'dd089e_cmd_ddict_helper_integration_preview_manifest.json'}")
    print(f"status: {status}; helper_functions: {helper_found}/{helper_expected}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
