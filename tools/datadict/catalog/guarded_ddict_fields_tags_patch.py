#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, re, shutil
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZJ", "docs/datadict/reports/DD096ZD2ZJ-ddict-callsite-integration-guard-v0/dd096zd2zj_ddict_callsite_integration_guard_manifest.json", ["DD096ZD2ZJ_DDICT_CALLSITE_INTEGRATION_GUARD_READY"]),
    ("DD096ZD2ZI", "docs/datadict/reports/DD096ZD2ZI-guarded-resolver-source-patch-v0/dd096zd2zi_guarded_resolver_source_patch_manifest.json", ["DD096ZD2ZI_GUARDED_RESOLVER_SOURCE_PATCH_APPLIED"]),
]

ALIASES = [
    ("DDRUN", "DATA_DICTIONARY_RUNS"),
    ("DDOBJECT", "DATA_DICTIONARY_OBJECTS"),
    ("DDATTR", "DATA_DICTIONARY_OBJECT_ATTRIBUTES"),
    ("DDEDGE", "DATA_DICTIONARY_RELATION_EDGES"),
    ("DDEVID", "DATA_DICTIONARY_EVIDENCE_RECORDS"),
    ("DDGATE", "DATA_DICTIONARY_GATE_RECORDS"),
]

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")

def wt(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def wj(path: Path, obj):
    wt(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def wc(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def detect_include_style(text: str) -> str:
    # Match the style already used in cmd_ddict.cpp when possible.
    if '#include "../datadict/' in text:
        return '#include "../datadict/ddict_catalog_resolver.hpp"'
    if '#include "datadict/' in text:
        return '#include "datadict/ddict_catalog_resolver.hpp"'
    if '#include "ddict_' in text:
        return '#include "ddict_catalog_resolver.hpp"'
    return '#include "../datadict/ddict_catalog_resolver.hpp"'

def add_include_if_possible(text: str):
    include_line = detect_include_style(text)
    if "ddict_catalog_resolver.hpp" in text:
        return text, 0, "include_already_present", include_line
    lines = text.splitlines()
    last_include = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("#include"):
            last_include = i
    if last_include < 0:
        return text, 0, "no_include_anchor_found", include_line
    lines.insert(last_include + 1, include_line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), 1, "include_inserted", include_line

def make_bridge_helper_hpp() -> str:
    return """#pragma once
// DD096Z-D2ZK DDICT call-site bridge helpers.
// These helpers are intentionally small wrappers around the D2ZI resolver.

#include <string>

namespace dottalk::datadict {

std::string ddict_bridge_x64_owner_token(const std::string& token);
std::string ddict_bridge_legacy_owner_token(const std::string& token);
bool ddict_bridge_token_is_catalog_surface(const std::string& token);

} // namespace dottalk::datadict
"""

def make_bridge_helper_cpp() -> str:
    return """// DD096Z-D2ZK DDICT call-site bridge helpers.

#include "ddict_callsite_bridge.hpp"
#include "ddict_catalog_resolver.hpp"

namespace dottalk::datadict {

std::string ddict_bridge_x64_owner_token(const std::string& token) {
    return ddict_resolve_to_x64_catalog_name(token);
}

std::string ddict_bridge_legacy_owner_token(const std::string& token) {
    return ddict_resolve_to_legacy_catalog_name(token);
}

bool ddict_bridge_token_is_catalog_surface(const std::string& token) {
    return ddict_is_known_catalog_name(token);
}

} // namespace dottalk::datadict
"""

def make_smoke_dts() -> str:
    return "\n".join([
        "* DD096Z-D2ZK DDICT FIELDS/TAGS bridge smoke",
        "* Read-only smoke after call-site bridge patch/build.",
        "DDICT STATUS",
        "DDICT TABLES",
        "DDICT FIELDS DATA_DICTIONARY_OBJECTS",
        "DDICT FIELDS DDOBJECT",
        "DDICT TAGS DATA_DICTIONARY_OBJECTS",
        "DDICT TAGS DDOBJECT",
        "",
    ])

def source_metrics(text: str):
    up = text.upper()
    return {
        "has_resolver_include": int("DDICT_CATALOG_RESOLVER.HPP" in up),
        "has_callsite_bridge_include": int("DDICT_CALLSITE_BRIDGE.HPP" in up),
        "fields_mentions": up.count("FIELDS"),
        "tags_mentions": up.count("TAGS"),
        "no_fields_found_mentions": up.count("NO_FIELDS_FOUND"),
        "no_catalog_tags_found_mentions": up.count("NO_CATALOG_TAGS_FOUND"),
        "legacy_mentions": sum(up.count(a) for a, _ in ALIASES),
        "x64_mentions": sum(up.count(b) for _, b in ALIASES),
    }

def line_hits(text: str):
    patterns = ["FIELDS", "TAGS", "NO_FIELDS_FOUND", "NO_CATALOG_TAGS_FOUND", "DDOBJECT", "DDATTR", "DATA_DICTIONARY_OBJECTS"]
    rows = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        up = line.upper()
        for p in patterns:
            if p in up:
                rows.append({"line": lineno, "pattern": p, "text": line[:240]})
    return rows

def integration_plan_text() -> str:
    return """# DD096Z-D2ZK FIELDS/TAGS Source Patch Notes

This package intentionally keeps call-site mutation conservative.

## What is safe to apply automatically

- Add the resolver include to `src/cli/cmd_ddict.cpp` when an include anchor is found.
- Add bridge helper files:
  - `src/datadict/ddict_callsite_bridge.hpp`
  - `src/datadict/ddict_callsite_bridge.cpp`

## What is not automatically patched yet

The exact `FIELDS` and `TAGS` logic in `cmd_ddict.cpp` should be patched only after reviewing the generated line-hit report.

Reason: the current DDICT implementation may have local lambdas/helpers, field-owner lookup assumptions, and message text paths that should not be altered by blind text replacement.

## Manual/source-patch target

FIELDS should normalize requested owner/table token through the resolver before looking up metadata rows.

TAGS should distinguish physical artifact availability from catalog tag metadata rows. The desired honest result is:

```text
Table DBF     : YES
CDX artifact  : <path>
LMDB mirror   : <path>
Catalog tags  : 0
Physical tags : <n>
Result        : PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS
```

## Next lane

D2ZL should be the narrow patch that edits the actual `FIELDS` and `TAGS` code paths after reviewing D2ZK line hits.
"""

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZK guarded DDICT FIELDS/TAGS patch")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZK-guarded-ddict-fields-tags-patch-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--apply-safe-source-patch", action="store_true")
    ap.add_argument("--write-smoke-script", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_guarded_ddict_fields_tags_patch"
    gen.mkdir(parents=True, exist_ok=True)

    pre_rows = []
    blockers = 0
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        data = read_json(p)
        observed = data.get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zk_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    cmd_path = repo / "src/cli/cmd_ddict.cpp"
    cmd_text = read_text(cmd_path)
    metrics = source_metrics(cmd_text)
    wc(gen / "dd096zd2zk_cmd_ddict_metrics.csv", [{"metric": k, "value": v} for k, v in sorted(metrics.items())], ["metric", "value"])
    wc(gen / "dd096zd2zk_cmd_ddict_line_hits.csv", line_hits(cmd_text), ["line","pattern","text"])

    target_h = repo / "src/datadict/ddict_callsite_bridge.hpp"
    target_cpp = repo / "src/datadict/ddict_callsite_bridge.cpp"
    bridge_h = make_bridge_helper_hpp()
    bridge_cpp = make_bridge_helper_cpp()
    smoke = make_smoke_dts()

    wt(gen / "ddict_callsite_bridge.hpp", bridge_h)
    wt(gen / "ddict_callsite_bridge.cpp", bridge_cpp)
    wt(gen / "DD096ZD2ZK_DDICT_FIELDS_TAGS_BRIDGE_SMOKE.dts", smoke)
    wt(gen / "DD096ZD2ZK_FIELDS_TAGS_SOURCE_PATCH_NOTES.md", integration_plan_text())

    patched_cmd, include_changed, include_status, include_line = add_include_if_possible(cmd_text)
    wt(gen / "cmd_ddict.cpp.include_patch_preview", patched_cmd if patched_cmd else "")
    patch_rows = [{
        "target": "src/cli/cmd_ddict.cpp",
        "operation": "insert_resolver_include",
        "status": include_status,
        "include_line": include_line,
        "changed_if_applied": include_changed,
    },{
        "target": "src/datadict/ddict_callsite_bridge.hpp",
        "operation": "write_bridge_helper_header",
        "status": "ready",
        "include_line": "",
        "changed_if_applied": 1,
    },{
        "target": "src/datadict/ddict_callsite_bridge.cpp",
        "operation": "write_bridge_helper_cpp",
        "status": "ready",
        "include_line": "",
        "changed_if_applied": 1,
    }]
    wc(gen / "dd096zd2zk_safe_patch_plan.csv", patch_rows, ["target","operation","status","include_line","changed_if_applied"])

    source_files_written = 0
    backups_written = 0
    backup_root = repo / f"docs/datadict/backups/DD096ZD2ZK-source-backup-{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if args.apply_safe_source_patch:
        if blockers:
            raise SystemExit("Precondition blockers present; refusing --apply-safe-source-patch.")
        if not cmd_text:
            raise SystemExit("cmd_ddict.cpp not found or empty; refusing --apply-safe-source-patch.")
        # Backup existing targets.
        for target in [cmd_path, target_h, target_cpp]:
            if target.exists():
                backup = backup_root / target.relative_to(repo)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
                backups_written += 1
        if include_changed:
            wt(cmd_path, patched_cmd)
            source_files_written += 1
        wt(target_h, bridge_h)
        wt(target_cpp, bridge_cpp)
        source_files_written += 2

    smoke_written = 0
    if args.write_smoke_script:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZK_DDICT_FIELDS_TAGS_BRIDGE_SMOKE.dts", smoke)
        smoke_written = 1

    required_missing = int(not cmd_path.exists()) + int(not (repo / "src/datadict/ddict_catalog_resolver.hpp").exists()) + int(not (repo / "src/datadict/ddict_catalog_resolver.cpp").exists())
    failures = blockers + required_missing
    if failures:
        status = "DD096ZD2ZK_GUARDED_DDICT_FIELDS_TAGS_PATCH_REVIEW"
    elif args.apply_safe_source_patch:
        status = "DD096ZD2ZK_SAFE_SOURCE_PATCH_APPLIED_CALLSITE_REVIEW_PENDING"
    else:
        status = "DD096ZD2ZK_GUARDED_DDICT_FIELDS_TAGS_PATCH_READY"

    boundary = [
        {"boundary": "guarded_ddict_fields_tags_patch_package", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "safe_source_files_written", "observed": source_files_written, "required": 3 if args.apply_safe_source_patch and include_changed else (2 if args.apply_safe_source_patch else 0), "pass": int(source_files_written == (3 if args.apply_safe_source_patch and include_changed else (2 if args.apply_safe_source_patch else 0)))},
        {"boundary": "fields_tags_logic_rewritten", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zk_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZK Guarded DDICT FIELDS/TAGS Patch

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZK is the guarded transition from resolver source availability to DDICT FIELDS/TAGS integration.

This package applies only safe source scaffolding with `--apply-safe-source-patch`:

- include resolver header in `cmd_ddict.cpp` when anchor found
- write `ddict_callsite_bridge.hpp`
- write `ddict_callsite_bridge.cpp`

It does not blindly rewrite FIELDS/TAGS logic.

## Summary

- Precondition blockers: **{blockers}**
- Required files missing: **{required_missing}**
- Include patch status: **{include_status}**
- Source files written: **{source_files_written}**
- Backups written: **{backups_written}**
- Smoke script written: **{smoke_written}**
- Build file edits: **0**
- Active catalog mutation: **0**

## Next lane

D2ZL should patch the actual FIELDS/TAGS call-site logic after reviewing the generated line-hit report.
"""
    wt(out / "DD096ZD2ZK_GUARDED_DDICT_FIELDS_TAGS_PATCH_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zk_guarded_ddict_fields_tags_patch_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "required_files_missing": required_missing,
        "include_patch_status": include_status,
        "apply_safe_source_patch": int(args.apply_safe_source_patch),
        "source_files_written": source_files_written,
        "backups_written": backups_written,
        "smoke_script_written": smoke_written,
        "fields_tags_logic_rewritten": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Review line hits and authorize D2ZL actual FIELDS/TAGS logic patch.",
    }
    wj(out / "dd096zd2zk_guarded_ddict_fields_tags_patch_manifest.json", manifest)

    print(f"DD096Z-D2ZK guarded DDICT FIELDS/TAGS patch manifest: {out / 'dd096zd2zk_guarded_ddict_fields_tags_patch_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; include_patch_status: {include_status}; source_files_written: {source_files_written}; fields_tags_logic_rewritten: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
