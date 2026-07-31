#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple


TARGET_SOURCE = "src/datadict/ddict_catalog_paths.cpp"
TARGET_HEADER = "include/datadict/ddict_catalog_paths.hpp"
DD093_MANIFEST = "docs/datadict/reports/DD093-ddict-runtime-path-remap-repair-v0/dd093_ddict_runtime_path_remap_repair_manifest.json"

EXPECTED_DD_TABLES = [
    "DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE",
    "DDEVID", "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE",
]

PROTECTED_UNTOUCHED = [
    "src/cli/cmd_ddict.cpp",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
    "src/CMakeLists.txt",
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
]

SEARCH_TERMS = [
    "metadata", "datadict", "catalog_candidates", "catalog_candidates",
    "base_roots", "find_catalog", "active catalog", "indexes", "lmdb",
    "find_cdx_file", "find_lmdb_dir", "collect_stats",
]

SMOKE = """SETPATH
DO ddbase
DDICT STATUS
DDICT TABLES
DDICT TAGS DDATTR
DDICT REL DDOBJECT OUT
DDICT EVIDENCE DDOBJECT

"""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except Exception as exc:
        return {"_read_error": str(exc)}


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


def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def table_presence(repo: Path) -> Tuple[int, List[Dict[str, Any]]]:
    root = repo / "dottalkpp/data/datadict"
    rows: List[Dict[str, Any]] = []
    count = 0
    for table in EXPECTED_DD_TABLES:
        p = root / f"{table}.dbf"
        exists = int(p.exists())
        count += exists
        rows.append({
            "root": rel(repo, root),
            "table": table,
            "exists": exists,
            "bytes": p.stat().st_size if p.exists() else 0,
        })
    return count, rows


def context_rows(text: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    lines = text.splitlines()
    seen = set()
    for i, line in enumerate(lines, start=1):
        lower = line.lower()
        terms = [t for t in SEARCH_TERMS if t.lower() in lower]
        if not terms:
            continue
        start = max(1, i - 2)
        end = min(len(lines), i + 2)
        key = (start, end)
        if key in seen:
            continue
        seen.add(key)
        snippet = "\\n".join(f"{j}: {lines[j-1]}" for j in range(start, end + 1))
        rows.append({
            "start_line": start,
            "end_line": end,
            "terms": ";".join(sorted(set(terms))),
            "snippet": snippet,
        })
    return rows


def line_count(text: str) -> int:
    return len(text.splitlines())


def file_inventory(repo: Path) -> List[Dict[str, Any]]:
    rels = [TARGET_SOURCE, TARGET_HEADER, DD093_MANIFEST] + PROTECTED_UNTOUCHED
    rows: List[Dict[str, Any]] = []
    for rp in rels:
        p = repo / rp
        txt = read_text(p) if p.exists() and p.is_file() else ""
        rows.append({
            "path": rp,
            "exists": int(p.exists()),
            "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
            "bytes_or_children": p.stat().st_size if p.exists() and p.is_file() else sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else 0,
            "lines": line_count(txt) if txt else "",
            "mentions_metadata": int("metadata" in txt.lower()),
            "mentions_datadict": int("datadict" in txt.lower()),
            "mentions_indexes": int("indexes" in txt.lower()),
            "mentions_lmdb": int("lmdb" in txt.lower()),
            "sha256": sha256(p),
        })
    return rows


def diff_text(old: str, new: str, name: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=name + ".before",
        tofile=name + ".after",
        lineterm="",
    ))


def candidate_patches(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Try narrow local insertions: add data/datadict before metadata/datadict candidates."""
    patches: List[Dict[str, Any]] = []
    out = text

    # Case 1: push/emplace of base / "metadata" / "datadict".
    pattern = re.compile(
        r'(?P<indent>^[ \t]*)(?P<call>(?:[A-Za-z_][A-Za-z0-9_\.]*\.)?(?:push_back|emplace_back)\s*\(\s*)(?P<base>[^;\n]*?)\s*/\s*"metadata"\s*/\s*"datadict"\s*\)\s*;',
        re.MULTILINE,
    )

    def repl_push(m: re.Match) -> str:
        indent = m.group("indent")
        call = m.group("call")
        base = m.group("base").rstrip()
        old_line = m.group(0)
        new_line = f'{indent}{call}{base} / "datadict");'
        patches.append({
            "pattern_id": "P1_PUSH_EMPLACE_BASE_METADATA_DATADICT",
            "line_preview": old_line.strip(),
            "insertion_preview": new_line.strip(),
            "safe": 1,
        })
        return new_line + "\n" + old_line

    out2, n = pattern.subn(repl_push, out, count=1)
    if n:
        out = out2
        return out, patches

    # Case 2: vector initializer entry base / "metadata" / "datadict",
    # insert sibling base / "datadict" immediately before it.
    pattern2 = re.compile(
        r'(?P<indent>^[ \t]*)(?P<entry>[^,\n;{}]+?\s*/\s*"metadata"\s*/\s*"datadict"\s*,?)',
        re.MULTILINE,
    )

    def repl_init(m: re.Match) -> str:
        indent = m.group("indent")
        entry = m.group("entry")
        base = re.sub(r'\s*/\s*"metadata"\s*/\s*"datadict"\s*,?\s*$', "", entry).rstrip()
        comma = "," if entry.rstrip().endswith(",") else ""
        new_entry = f'{indent}{base} / "datadict"{comma}'
        patches.append({
            "pattern_id": "P2_INITIALIZER_BASE_METADATA_DATADICT",
            "line_preview": entry.strip(),
            "insertion_preview": new_entry.strip(),
            "safe": 1,
        })
        return new_entry + "\n" + indent + entry

    out2, n = pattern2.subn(repl_init, out, count=1)
    if n:
        out = out2
        return out, patches

    # Case 3: literal pieces "metadata", "datadict" in a candidate list.
    # Do not apply, only report because semantics are not safe to infer.
    if '"metadata"' in text and '"datadict"' in text:
        patches.append({
            "pattern_id": "P3_SPLIT_LITERALS_PRESENT_REVIEW_ONLY",
            "line_preview": '"metadata" and "datadict" both present',
            "insertion_preview": "manual/local patch needed: add data/datadict candidate before metadata/datadict fallback",
            "safe": 0,
        })

    return out, patches


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-093R DDICT path resolver local-pattern discovery")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD093R-ddict-path-resolver-local-pattern-discovery-v0")
    ap.add_argument("--apply-source-patch", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    target = repo / TARGET_SOURCE
    source = read_text(target)

    new_table_count, table_rows = table_presence(repo)
    inv_rows = file_inventory(repo)
    ctx_rows = context_rows(source)

    candidate, patch_rows = candidate_patches(source)
    changed = int(candidate != source)
    safe_patch = int(any(int(p.get("safe", 0)) == 1 for p in patch_rows))

    generated = out / "generated_local_pattern"
    candidate_path = generated / TARGET_SOURCE
    diff_path = generated / (TARGET_SOURCE + ".diff")
    smoke_path = generated / "dd093r_ddict_path_remap_smoke.dts"
    write_text(candidate_path, candidate)
    write_text(diff_path, diff_text(source, candidate, TARGET_SOURCE))
    write_text(smoke_path, SMOKE)

    review_rows: List[Dict[str, Any]] = []
    if not target.exists():
        review_rows.append({"issue": "TARGET_SOURCE_MISSING", "detail": TARGET_SOURCE})
    if new_table_count != 11:
        review_rows.append({"issue": "NEW_DATADICT_TABLE_COUNT_NOT_11", "detail": str(new_table_count)})
    if not patch_rows:
        review_rows.append({"issue": "NO_LOCAL_PATCH_PATTERN_FOUND", "detail": TARGET_SOURCE})
    elif not safe_patch:
        review_rows.append({"issue": "PATCH_PATTERN_REVIEW_ONLY", "detail": ";".join(p["pattern_id"] for p in patch_rows)})

    applied = 0
    backup_path = ""
    if args.apply_source_patch and changed and safe_patch and target.exists():
        backup_dir = (repo / args.backup_root) / f"{args.run_id}_{stamp()}"
        backup = backup_dir / TARGET_SOURCE
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        backup_path = str(backup)
        target.write_text(candidate, encoding="utf-8")
        applied = 1

    gate_rows = [
        {"gate": "target_source_exists", "expected": 1, "observed": int(target.exists()), "pass": int(target.exists())},
        {"gate": "new_datadict_tables_present", "expected": 11, "observed": new_table_count, "pass": int(new_table_count == 11)},
        {"gate": "context_rows_generated", "expected": ">=1", "observed": len(ctx_rows), "pass": int(len(ctx_rows) >= 1)},
        {"gate": "candidate_diff_generated", "expected": 1, "observed": int(diff_path.exists()), "pass": int(diff_path.exists())},
        {"gate": "safe_patch_available", "expected": "0 or 1", "observed": safe_patch, "pass": 1},
        {"gate": "apply_when_requested", "expected": int(args.apply_source_patch), "observed": applied, "pass": int((not args.apply_source_patch) or applied == 1)},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    if args.apply_source_patch and failures == 0 and applied:
        status = "DDICT_PATH_RESOLVER_LOCAL_PATTERN_PATCH_APPLIED_BUILD_REQUIRED"
    elif failures == 0 and safe_patch:
        status = "DDICT_PATH_RESOLVER_LOCAL_PATTERN_PATCH_READY"
    elif failures == 0:
        status = "DDICT_PATH_RESOLVER_LOCAL_PATTERN_DISCOVERY_REVIEW"
    else:
        status = "DDICT_PATH_RESOLVER_LOCAL_PATTERN_DISCOVERY_BLOCKED"

    boundary_rows = [
        {"boundary": "local_pattern_discovery", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "target_source_modified", "observed": applied, "required": int(args.apply_source_patch), "pass": int((not args.apply_source_patch) or applied == 1)},
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
        {"next_id": "DD093R_APPLY", "title": "Apply safe local pattern patch if READY", "allowed_scope": "src/datadict/ddict_catalog_paths.cpp only"},
        {"next_id": "MANUAL_PATCH", "title": "manual local patch from context report if REVIEW", "allowed_scope": "add data/datadict candidate before metadata/datadict fallback"},
        {"next_id": "DD093A", "title": "runtime path remap closure", "allowed_scope": "after build green and DDICT uses data/datadict"},
        {"next_id": "DD093B", "title": "index/lmdb subroot repair", "allowed_scope": "only if DBF root fixed but TAGS still uses flat index/lmdb roots"},
    ]

    write_csv(out / "dd093r_file_inventory.csv", inv_rows, ["path", "exists", "kind", "bytes_or_children", "lines", "mentions_metadata", "mentions_datadict", "mentions_indexes", "mentions_lmdb", "sha256"])
    write_csv(out / "dd093r_source_contexts.csv", ctx_rows, ["start_line", "end_line", "terms", "snippet"])
    write_csv(out / "dd093r_catalog_table_presence.csv", table_rows, ["root", "table", "exists", "bytes"])
    write_csv(out / "dd093r_patch_candidate_ledger.csv", patch_rows, ["pattern_id", "line_preview", "insertion_preview", "safe"])
    write_csv(out / "dd093r_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd093r_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd093r_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd093r_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-093R DDICT Path Resolver Local-Pattern Discovery

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-093R follows DD-093 review. DD-093 confirmed the new Data Dictionary DBF root contains 11 / 11 tables,
but the first patcher could not find a simple `metadata/datadict` literal.

DD-093R inspects the actual local structure of `{TARGET_SOURCE}`, captures context rows, and attempts a narrow candidate insertion:
add `data/datadict` as the preferred candidate before the legacy `metadata/datadict` fallback.

## Findings

- Target source exists: **{int(target.exists())}**
- New Data Dictionary tables present: **{new_table_count} / 11**
- Source context rows: **{len(ctx_rows)}**
- Patch candidates: **{len(patch_rows)}**
- Safe patch available: **{safe_patch}**
- Apply requested: **{int(args.apply_source_patch)}**
- Applied: **{applied}**

## Candidate patch

- Candidate file: `{candidate_path}`
- Diff file: `{diff_path}`
- Runtime smoke file: `{smoke_path}`

## Boundary

DD-093R does not edit build files, command registration, active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK,
generated catalog content, or manual rows. It may patch only `{TARGET_SOURCE}` when `--apply-source-patch`
is supplied and a safe local pattern is found.
"""
    write_text(out / "DD093R_DDICT_PATH_RESOLVER_LOCAL_PATTERN_DISCOVERY_REPORT.md", report)

    manifest = {
        "contract": "dd093r_ddict_path_resolver_local_pattern_discovery_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "target_source": TARGET_SOURCE,
        "new_datadict_tables_present": new_table_count,
        "source_context_rows": len(ctx_rows),
        "patch_candidates": len(patch_rows),
        "safe_patch_available": safe_patch,
        "changed_candidate": changed,
        "apply_source_patch": int(args.apply_source_patch),
        "applied": applied,
        "backup_path": backup_path,
        "failures": failures,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Inspect dd093r_source_contexts.csv and patch candidate ledger; apply if READY, otherwise patch locally from context.",
    }
    write_json(out / "dd093r_ddict_path_resolver_local_pattern_discovery_manifest.json", manifest)

    print(f"DD-093R DDICT path resolver local-pattern discovery manifest: {out / 'dd093r_ddict_path_resolver_local_pattern_discovery_manifest.json'}")
    print(f"status: {status}; contexts: {len(ctx_rows)}; patch_candidates: {len(patch_rows)}; safe_patch: {safe_patch}; applied: {applied}; new_tables: {new_table_count}/11; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
