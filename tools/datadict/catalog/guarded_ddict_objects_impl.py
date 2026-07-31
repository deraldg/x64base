#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

EXPECTED_DD084_STATUS = "DDICT_OBJECTS_REPRESENTATION_PLAN_READY"
OBJECTS_FUNCTION = '\nvoid print_objects(std::istringstream& args) {\n    std::string word;\n    std::string type_filter;\n    std::string profile_filter;\n\n    while (args >> word) {\n        std::string key = upper_copy(trim_copy(word));\n        if (key == "TYPE") {\n            std::string value;\n            args >> value;\n            type_filter = upper_copy(trim_copy(value));\n        } else if (key == "PROFILE") {\n            std::string value;\n            args >> value;\n            profile_filter = upper_copy(trim_copy(value));\n        } else if (type_filter.empty()) {\n            type_filter = key;\n        }\n    }\n\n    fs::path dir = find_catalog_dir();\n    std::vector<Row> objects = read_dbf_table(dir, "DDOBJECT");\n    std::vector<Row> attrs = read_dbf_table(dir, "DDATTR");\n\n    std::unordered_map<std::string, int> attr_counts;\n    for (const auto& attr : attrs) {\n        std::string objid = value_of(attr, "OBJID");\n        if (!objid.empty()) {\n            ++attr_counts[objid];\n        }\n    }\n\n    std::vector<const Row*> selected;\n    for (const auto& obj : objects) {\n        std::string objtype = upper_copy(value_of(obj, "OBJTYPE"));\n        std::string profile = upper_copy(value_of(obj, "PROFILE"));\n\n        if (!type_filter.empty() && objtype != type_filter) {\n            continue;\n        }\n        if (!profile_filter.empty() && profile != profile_filter) {\n            continue;\n        }\n        selected.push_back(&obj);\n    }\n\n    std::cout\n        << "DDICT OBJECTS\\n"\n        << "  Active catalog: " << dir.string() << "\\n"\n        << "  Read mode     : READ-ONLY\\n"\n        << "  Type filter   : " << (type_filter.empty() ? "(none)" : type_filter) << "\\n"\n        << "  Profile filter: " << (profile_filter.empty() ? "(none)" : profile_filter) << "\\n"\n        << "  Object rows   : " << selected.size() << "\\n"\n        << "  Rows shown    : bounded to 80\\n"\n        << "  OBJTYPE             NAME              OWNER             STATUS                    PROFILE       ATTRS\\n"\n        << "  ------------------  ----------------  ----------------  ------------------------  ------------  -----\\n";\n\n    constexpr std::size_t kLimit = 80;\n    std::size_t shown = 0;\n    for (const Row* obj : selected) {\n        if (shown++ >= kLimit) {\n            break;\n        }\n        std::string objid = value_of(*obj, "OBJID");\n        int acount = objid.empty() ? 0 : attr_counts[objid];\n\n        std::cout\n            << "  " << std::left << std::setw(18) << short_text(value_of(*obj, "OBJTYPE"), 18)\n            << "  " << std::setw(16) << short_text(value_of(*obj, "NAME"), 16)\n            << "  " << std::setw(16) << short_text(value_of(*obj, "OWNER"), 16)\n            << "  " << std::setw(24) << short_text(value_of(*obj, "STATUS"), 24)\n            << "  " << std::setw(12) << short_text(value_of(*obj, "PROFILE"), 12)\n            << "  " << acount\n            << "\\n";\n    }\n\n    if (selected.empty()) {\n        std::cout << "  (none)\\n";\n    }\n}\n'

def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")

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

def diff_text(old: str, new: str, path: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=path + ".before",
        tofile=path + ".after",
        lineterm="",
    ))

def patch_source(old: str) -> tuple[str, List[Dict[str, Any]]]:
    review: List[Dict[str, Any]] = []

    if "void print_evidence(std::istringstream& args)" not in old:
        review.append({"issue": "EVIDENCE_BASELINE_NOT_FOUND", "detail": "print_evidence function not found; expected DD-081/DD-082 baseline"})
    if "void print_objects(std::istringstream& args)" in old:
        review.append({"issue": "OBJECTS_ALREADY_PRESENT", "detail": "print_objects already exists; no patch should be applied"})

    marker = "\n} // anonymous namespace\n\nvoid cmd_DDICT"
    if marker not in old:
        review.append({"issue": "NAMESPACE_MARKER_NOT_FOUND", "detail": "could not find anonymous namespace closing marker before cmd_DDICT"})
        return old, review

    new = old.replace(marker, "\n" + OBJECTS_FUNCTION + "\n} // anonymous namespace\n\nvoid cmd_DDICT", 1)

    old_block = (
        '    if (sub == "OBJECTS") {\n'
        '        print_pending(sub);\n'
        '        return;\n'
        '    }\n'
    )
    new_block = (
        '    if (sub == "OBJECTS") {\n'
        '        print_objects(args);\n'
        '        return;\n'
        '    }\n'
    )

    if old_block not in new:
        review.append({"issue": "OBJECTS_DISPATCH_BLOCK_NOT_FOUND", "detail": "could not find OBJECTS pending dispatch block"})
        return new, review

    new = new.replace(old_block, new_block, 1)
    return new, review

def main() -> int:
    ap = argparse.ArgumentParser(description="DD-085 guarded DDICT OBJECTS implementation")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD085-guarded-ddict-objects-implementation-v0")
    ap.add_argument("--dd084-dir", default="docs/datadict/reports/DD084-ddict-objects-representation-plan-v0")
    ap.add_argument("--source-path", default="src/cli/cmd_ddict.cpp")
    ap.add_argument("--apply-source-patch", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd084_dir = (repo / args.dd084_dir).resolve()
    dd084_manifest = read_json(dd084_dir / "dd084_ddict_objects_representation_plan_manifest.json")
    source = (repo / args.source_path).resolve()
    backup_root = (repo / args.backup_root).resolve()

    old = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""
    generated, review_rows = patch_source(old)

    generated_dir = out / "generated_source"
    generated_dir.mkdir(parents=True, exist_ok=True)
    generated_source = generated_dir / "cmd_ddict.cpp"
    generated_source.write_text(generated, encoding="utf-8")

    preview = diff_text(old, generated, rel(repo, source))
    (out / "dd085_cmd_ddict_objects_patch_preview.diff").write_text(preview, encoding="utf-8")

    dd084_green = int(dd084_manifest.get("status") == EXPECTED_DD084_STATUS)
    source_exists = int(source.exists())
    existing_has_evidence = int("void print_evidence" in old and 'sub == "EVIDENCE"' in old)
    generated_has_objects = int("void print_objects" in generated and 'sub == "OBJECTS"' in generated)
    generated_preserves_evidence = int("void print_evidence" in generated and 'sub == "EVIDENCE"' in generated)
    generated_readonly = int("READ-ONLY" in generated and "BUILDLMDB" not in generated and "CDX ADDTAG" not in generated and "REPLACE" not in generated)

    if not dd084_green:
        review_rows.append({"issue": "DD084_NOT_READY", "detail": dd084_manifest.get("status", "")})
    if not source_exists:
        review_rows.append({"issue": "SOURCE_MISSING", "detail": str(source)})
    if not existing_has_evidence:
        review_rows.append({"issue": "EVIDENCE_BASELINE_NOT_DETECTED", "detail": "existing cmd_ddict.cpp does not appear to contain DD-081 EVIDENCE baseline"})

    failures = len(review_rows)
    patched = 0
    backup_path = ""
    if args.apply_source_patch and failures == 0:
        backup_dir = backup_root / f"{args.run_id}_{stamp()}"
        backup_target = backup_dir / rel(repo, source)
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, backup_target)
        backup_path = str(backup_target)
        source.write_text(generated, encoding="utf-8")
        patched = 1

    if args.apply_source_patch and patched and failures == 0:
        status = "DDICT_OBJECTS_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"
    elif failures == 0:
        status = "DDICT_OBJECTS_SOURCE_PATCH_READY"
    else:
        status = "DDICT_OBJECTS_SOURCE_PATCH_REVIEW"

    gate_rows = [
        {"gate": "dd084_representation_plan_ready", "expected": EXPECTED_DD084_STATUS, "observed": dd084_manifest.get("status", ""), "pass": dd084_green},
        {"gate": "cmd_ddict_source_exists", "expected": 1, "observed": source_exists, "pass": source_exists},
        {"gate": "evidence_baseline_detected", "expected": 1, "observed": existing_has_evidence, "pass": existing_has_evidence},
        {"gate": "generated_objects_surface", "expected": 1, "observed": generated_has_objects, "pass": generated_has_objects},
        {"gate": "generated_evidence_preserved", "expected": 1, "observed": generated_preserves_evidence, "pass": generated_preserves_evidence},
        {"gate": "generated_readonly_surface", "expected": 1, "observed": generated_readonly, "pass": generated_readonly},
        {"gate": "source_patch_applied_when_requested", "expected": int(args.apply_source_patch), "observed": patched, "pass": int((not args.apply_source_patch) or patched == 1)},
    ]

    boundary_rows = [
        {"boundary": "guarded_objects_source_patch", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cmd_ddict_cpp_edit", "observed": patched, "required": int(args.apply_source_patch), "pass": int((not args.apply_source_patch) or patched == 1)},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd085_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd085_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd085_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-085 Guarded DDICT OBJECTS Implementation

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-085 implements:

```text
DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]
```

The implementation is read-only. It lists bounded `DDOBJECT` rows, supports simple
TYPE and PROFILE filters, and decorates each row with a DDATTR count.

## Target

- Source: `{rel(repo, source)}`
- Generated candidate: `{rel(repo, generated_source)}`
- Patch preview: `{rel(repo, out / 'dd085_cmd_ddict_objects_patch_preview.diff')}`

## Result

- Apply requested: **{int(args.apply_source_patch)}**
- Source patched: **{patched}**
- Backup path: `{backup_path}`

## Boundary

DD-085 edits only `cmd_ddict.cpp` when `--apply-source-patch` is supplied.
It does not edit registry/build files, mutate active catalog data, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair rows.
"""
    (out / "DD085_GUARDED_DDICT_OBJECTS_IMPLEMENTATION_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd085_guarded_ddict_objects_impl_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd084_status": dd084_manifest.get("status", ""),
        "source_path": rel(repo, source),
        "apply_source_patch": int(args.apply_source_patch),
        "patched": patched,
        "backup_path": backup_path,
        "failures": failures,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Build DotTalk++ and run DDICT OBJECTS, TYPE, PROFILE smokes; then DD-086 closure.",
    }
    write_json(out / "dd085_guarded_ddict_objects_impl_manifest.json", manifest)

    print(f"DD-085 guarded DDICT OBJECTS manifest: {out / 'dd085_guarded_ddict_objects_impl_manifest.json'}")
    print(f"status: {status}; patched: {patched}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
