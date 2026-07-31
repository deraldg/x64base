#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, shutil
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZK", "docs/datadict/reports/DD096ZD2ZK-guarded-ddict-fields-tags-patch-v0/dd096zd2zk_guarded_ddict_fields_tags_patch_manifest.json", ["DD096ZD2ZK_SAFE_SOURCE_PATCH_APPLIED_CALLSITE_REVIEW_PENDING"]),
    ("DD096ZD2ZN", "docs/datadict/reports/DD096ZD2ZN-surgical-fields-tags-patch-v0/dd096zd2zn_surgical_fields_tags_patch_manifest.json", ["DD096ZD2ZN_SURGICAL_FIELDS_TAGS_PATCH_READY"]),
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

def detect_bridge_include_line(text: str) -> str:
    if '#include "../datadict/' in text:
        return '#include "../datadict/ddict_callsite_bridge.hpp"'
    if '#include "datadict/' in text:
        return '#include "datadict/ddict_callsite_bridge.hpp"'
    if '#include "ddict_' in text:
        return '#include "ddict_callsite_bridge.hpp"'
    return '#include "../datadict/ddict_callsite_bridge.hpp"'

def insert_bridge_include(text: str):
    if "ddict_callsite_bridge.hpp" in text:
        return text, 0, "bridge_include_already_present", ""
    include_line = detect_bridge_include_line(text)
    lines = text.splitlines()
    # Prefer placement immediately after catalog resolver include, because D2K inserted it.
    for i, line in enumerate(lines):
        if "ddict_catalog_resolver.hpp" in line:
            lines.insert(i + 1, include_line)
            return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), 1, "bridge_include_inserted_after_catalog_resolver", include_line
    # Fallback to last include.
    last_include = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("#include"):
            last_include = i
    if last_include >= 0:
        lines.insert(last_include + 1, include_line)
        return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), 1, "bridge_include_inserted_after_last_include", include_line
    return text, 0, "no_include_anchor_found", include_line

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZKQ call-site bridge include repair")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZKQ-callsite-bridge-include-repair-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--apply-include-repair", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_callsite_bridge_include_repair"
    gen.mkdir(parents=True, exist_ok=True)

    blockers = 0
    pre_rows = []
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        observed = read_json(p).get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zkq_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    cmd_path = repo / "src/cli/cmd_ddict.cpp"
    bridge_h = repo / "src/datadict/ddict_callsite_bridge.hpp"
    bridge_cpp = repo / "src/datadict/ddict_callsite_bridge.cpp"
    cmd_text = read_text(cmd_path)

    patched, changed, status_detail, include_line = insert_bridge_include(cmd_text)
    wt(gen / "cmd_ddict.cpp.bridge_include_preview", patched if patched else "")

    inventory = [
        {"path": "src/cli/cmd_ddict.cpp", "exists": int(cmd_path.exists()), "bytes": cmd_path.stat().st_size if cmd_path.exists() else 0, "role": "patch target"},
        {"path": "src/datadict/ddict_callsite_bridge.hpp", "exists": int(bridge_h.exists()), "bytes": bridge_h.stat().st_size if bridge_h.exists() else 0, "role": "required bridge header"},
        {"path": "src/datadict/ddict_callsite_bridge.cpp", "exists": int(bridge_cpp.exists()), "bytes": bridge_cpp.stat().st_size if bridge_cpp.exists() else 0, "role": "required bridge implementation"},
    ]
    wc(gen / "dd096zd2zkq_source_inventory.csv", inventory, ["path","exists","bytes","role"])

    patch_plan = [{
        "target": "src/cli/cmd_ddict.cpp",
        "operation": "insert_ddict_callsite_bridge_include",
        "status": status_detail,
        "include_line": include_line,
        "changed_if_applied": changed,
    }]
    wc(gen / "dd096zd2zkq_include_repair_plan.csv", patch_plan, ["target","operation","status","include_line","changed_if_applied"])

    source_files_written = 0
    backups_written = 0
    backup_root = repo / f"docs/datadict/backups/DD096ZD2ZKQ-source-backup-{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    required_missing = int(not cmd_path.exists()) + int(not bridge_h.exists()) + int(not bridge_cpp.exists())

    if args.apply_include_repair:
        if blockers:
            raise SystemExit("Precondition blockers present; refusing --apply-include-repair.")
        if required_missing:
            raise SystemExit("Required source files missing; refusing --apply-include-repair.")
        if changed:
            backup = backup_root / cmd_path.relative_to(repo)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cmd_path, backup)
            backups_written = 1
            wt(cmd_path, patched)
            source_files_written = 1

    failures = blockers + required_missing
    if failures:
        status = "DD096ZD2ZKQ_CALLSITE_BRIDGE_INCLUDE_REPAIR_REVIEW"
    elif args.apply_include_repair:
        status = "DD096ZD2ZKQ_CALLSITE_BRIDGE_INCLUDE_REPAIR_APPLIED"
    else:
        status = "DD096ZD2ZKQ_CALLSITE_BRIDGE_INCLUDE_REPAIR_READY"

    boundary = [
        {"boundary": "callsite_bridge_include_repair_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "source_files_written", "observed": source_files_written, "required": 1 if args.apply_include_repair and changed else 0, "pass": int(source_files_written == (1 if args.apply_include_repair and changed else 0))},
        {"boundary": "fields_tags_logic_rewritten", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zkq_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f'''# DD096Z-D2ZKQ Call-Site Bridge Include Repair

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZKQ repairs a small chain inconsistency:

- D2ZK inserted the catalog resolver include and wrote bridge helper files.
- D2ZN expected `ddict_callsite_bridge.hpp` to be included in `cmd_ddict.cpp`.
- The D2ZN preview safely refused the marker with `bridge_include_missing_refuse_marker`.

This package inserts only the call-site bridge include. It does not rewrite FIELDS/TAGS logic.

## Summary

- Precondition blockers: **{blockers}**
- Required source files missing: **{required_missing}**
- Include repair status: **{status_detail}**
- Include line: `{include_line}`
- Source files written: **{source_files_written}**
- Backups written: **{backups_written}**
- FIELDS/TAGS logic rewritten: **0**

## Next

After D2ZKQ apply green, rerun D2ZN preview and then D2ZN `--apply-safe-marker --write-smoke-script`.
'''
    wt(out / "DD096ZD2ZKQ_CALLSITE_BRIDGE_INCLUDE_REPAIR_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zkq_callsite_bridge_include_repair_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "required_files_missing": required_missing,
        "include_repair_status": status_detail,
        "include_line": include_line,
        "apply_include_repair": int(args.apply_include_repair),
        "source_files_written": source_files_written,
        "backups_written": backups_written,
        "fields_tags_logic_rewritten": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Rerun D2ZN after include repair is applied.",
    }
    wj(out / "dd096zd2zkq_callsite_bridge_include_repair_manifest.json", manifest)

    print(f"DD096Z-D2ZKQ call-site bridge include repair manifest: {out / 'dd096zd2zkq_callsite_bridge_include_repair_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; required_files_missing: {required_missing}; include_repair_status: {status_detail}; source_files_written: {source_files_written}; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
