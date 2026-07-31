#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import filecmp
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD089C_STATUS = "DDICT_READ_HELPER_EXTRACTION_PREVIEW_READY"

HELPER_SOURCE_TARGETS = [
    "src/datadict/ddict_read_helpers.cpp",
    "src/datadict/ddict_catalog_paths.cpp",
    "src/datadict/ddict_dbf_reader.cpp",
    "src/datadict/ddict_object_resolver.cpp",
]

PROTECTED_UNTOUCHED = [
    "src/cli/cmd_ddict.cpp",
    "src/CMakeLists.txt",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
]


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


def sha256(path: Path) -> str:
    import hashlib
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-089D guarded helper source apply")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD089D-guarded-helper-source-apply-v0")
    ap.add_argument("--dd089c-dir", default="docs/datadict/reports/DD089C-guarded-read-helper-extraction-preview-v0")
    ap.add_argument("--apply-helper-sources", action="store_true")
    ap.add_argument("--replace-existing", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd089c_dir = (repo / args.dd089c_dir).resolve()
    dd089c_manifest = read_json(dd089c_dir / "dd089c_guarded_read_helper_extraction_preview_manifest.json")
    preview_root = Path(dd089c_manifest.get("generated_preview_root", ""))
    if not preview_root.is_absolute():
        preview_root = dd089c_dir / "generated_extraction_preview"

    backup_root = (repo / args.backup_root).resolve()
    backup_dir = backup_root / f"{args.run_id}_{stamp()}"

    review_rows: List[Dict[str, Any]] = []
    dd089c_green = int(dd089c_manifest.get("status") == EXPECTED_DD089C_STATUS)
    if not dd089c_green:
        review_rows.append({"issue": "DD089C_NOT_READY", "detail": dd089c_manifest.get("status", "")})
    if not preview_root.exists():
        review_rows.append({"issue": "PREVIEW_ROOT_MISSING", "detail": str(preview_root)})

    source_rows: List[Dict[str, Any]] = []
    for rel_src in HELPER_SOURCE_TARGETS:
        preview = preview_root / rel_src
        target = repo / rel_src
        preview_exists = int(preview.exists())
        target_exists = int(target.exists())
        target_same = int(preview_exists and target_exists and filecmp.cmp(preview, target, shallow=False))
        needs_apply = int(preview_exists and (not target_exists or not target_same))
        blocked_existing = int(preview_exists and target_exists and not target_same and not args.replace_existing)

        if not preview_exists:
            review_rows.append({"issue": "PREVIEW_SOURCE_MISSING", "detail": rel_src})
        if blocked_existing and args.apply_helper_sources:
            review_rows.append({"issue": "TARGET_EXISTS_REPLACE_NOT_ALLOWED", "detail": rel_src})

        source_rows.append({
            "target_source": rel_src,
            "preview_path": str(preview),
            "target_path": rel(repo, target),
            "preview_exists": preview_exists,
            "target_exists_before": target_exists,
            "target_same_before": target_same,
            "needs_apply": needs_apply,
            "blocked_existing": blocked_existing,
            "applied": 0,
            "backup_path": "",
            "target_hash_before": sha256(target),
            "target_hash_after": "",
        })

    protected_rows: List[Dict[str, Any]] = []
    protected_before = {}
    for rel_path in PROTECTED_UNTOUCHED:
        path = repo / rel_path
        protected_before[rel_path] = sha256(path)
        protected_rows.append({
            "protected_path": rel_path,
            "exists_before": int(path.exists()),
            "hash_before": protected_before[rel_path],
            "hash_after": "",
            "mutated_by_dd089d": "",
        })

    review_before_apply = len(review_rows)
    applied_count = 0
    backup_count = 0

    if args.apply_helper_sources and review_before_apply == 0:
        for row in source_rows:
            if int(row["needs_apply"]) != 1:
                continue
            preview = Path(row["preview_path"])
            target = repo / row["target_path"]
            if target.exists():
                backup_target = backup_dir / row["target_path"]
                backup_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup_target)
                row["backup_path"] = str(backup_target)
                backup_count += 1
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(preview, target)
            row["applied"] = 1
            row["target_hash_after"] = sha256(target)
            applied_count += 1

    protected_mutations = 0
    for row in protected_rows:
        path = repo / row["protected_path"]
        after = sha256(path)
        row["hash_after"] = after
        row["mutated_by_dd089d"] = int(after != row["hash_before"])
        protected_mutations += int(row["mutated_by_dd089d"])

    helper_sources_present = sum(1 for r in source_rows if int(r["preview_exists"]) == 1)
    blocked_count = sum(1 for r in source_rows if int(r["blocked_existing"]) == 1)
    apply_gate = int((not args.apply_helper_sources) or (applied_count >= 1 and protected_mutations == 0))

    gate_rows = [
        {"gate": "dd089c_preview_ready", "expected": EXPECTED_DD089C_STATUS, "observed": dd089c_manifest.get("status", ""), "pass": dd089c_green},
        {"gate": "preview_root_exists", "expected": 1, "observed": int(preview_root.exists()), "pass": int(preview_root.exists())},
        {"gate": "preview_helper_sources_present", "expected": len(HELPER_SOURCE_TARGETS), "observed": helper_sources_present, "pass": int(helper_sources_present == len(HELPER_SOURCE_TARGETS))},
        {"gate": "replace_policy_clean_or_not_applying", "expected": 0, "observed": blocked_count if args.apply_helper_sources else 0, "pass": int((not args.apply_helper_sources) or blocked_count == 0)},
        {"gate": "protected_files_unmutated", "expected": 0, "observed": protected_mutations, "pass": int(protected_mutations == 0)},
        {"gate": "helper_sources_applied_when_requested", "expected": int(args.apply_helper_sources), "observed": int(applied_count > 0), "pass": apply_gate},
        {"gate": "cmd_ddict_left_in_place", "expected": 0, "observed": 0, "pass": 1},
        {"gate": "build_wiring_deferred", "expected": 0, "observed": 0, "pass": 1},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    if args.apply_helper_sources and failures == 0:
        status = "DDICT_HELPER_SOURCES_APPLIED_BUILD_UNWIRED_CMD_DDICT_UNCHANGED"
    elif failures == 0:
        status = "DDICT_HELPER_SOURCE_APPLY_READY"
    else:
        status = "DDICT_HELPER_SOURCE_APPLY_REVIEW"

    boundary_rows = [
        {"boundary": "guarded_helper_source_apply", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "helper_source_files_modified", "observed": applied_count, "required": int(args.apply_helper_sources) * len(HELPER_SOURCE_TARGETS), "pass": int((not args.apply_helper_sources) or applied_count == len(HELPER_SOURCE_TARGETS))},
        {"boundary": "cmd_ddict_cpp_patched", "observed": 0, "required": 0, "pass": 1},
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
            "next_id": "DD089E",
            "title": "cmd_ddict helper removal and namespace integration preview",
            "allowed_scope": "generate diff to remove duplicated helper functions from cmd_ddict.cpp and add helper includes/usings; no build wiring yet unless separately authorized",
        },
        {
            "next_id": "DD089F",
            "title": "build wiring and DDICT parity closure",
            "allowed_scope": "wire helper cpp files and run full DDICT parity tests after cmd_ddict integration is accepted",
        },
    ]

    write_csv(out / "dd089d_helper_source_apply_ledger.csv", source_rows, ["target_source", "preview_path", "target_path", "preview_exists", "target_exists_before", "target_same_before", "needs_apply", "blocked_existing", "applied", "backup_path", "target_hash_before", "target_hash_after"])
    write_csv(out / "dd089d_protected_file_ledger.csv", protected_rows, ["protected_path", "exists_before", "hash_before", "hash_after", "mutated_by_dd089d"])
    write_csv(out / "dd089d_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd089d_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd089d_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd089d_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-089D Guarded Helper Source Apply

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-089D applies the DD-089C generated helper implementation candidates into the installed
helper source files when `--apply-helper-sources` is supplied.

It intentionally leaves `cmd_ddict.cpp` unchanged and build wiring deferred.

## Inputs

- DD-089C status: `{dd089c_manifest.get('status', '')}`
- Preview root: `{preview_root}`

## Result

- Apply requested: **{int(args.apply_helper_sources)}**
- Replace existing allowed: **{int(args.replace_existing)}**
- Helper targets expected: **{len(HELPER_SOURCE_TARGETS)}**
- Helper targets applied: **{applied_count}**
- Backups written: **{backup_count}**
- Protected file mutations: **{protected_mutations}**

## Important interpretation

After DD-089D apply, helper source files may contain copied implementations, but the runtime
still uses `cmd_ddict.cpp` because command integration and build wiring are not performed here.

## Boundary

DD-089D is guarded helper-source apply only. It does not patch `cmd_ddict.cpp`, edit build files,
edit command registration, mutate active catalog data, create/rebuild CDX/LMDB, mutate
HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    (out / "DD089D_GUARDED_HELPER_SOURCE_APPLY_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd089d_guarded_helper_source_apply_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd089c_status": dd089c_manifest.get("status", ""),
        "preview_root": str(preview_root),
        "apply_helper_sources": int(args.apply_helper_sources),
        "replace_existing": int(args.replace_existing),
        "helper_targets_expected": len(HELPER_SOURCE_TARGETS),
        "helper_targets_applied": applied_count,
        "backup_count": backup_count,
        "protected_file_mutations": protected_mutations,
        "failures": failures,
        "cmd_ddict_cpp_patched": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-089E cmd_ddict helper-removal/namespace integration preview, explicitly authorized.",
    }
    write_json(out / "dd089d_guarded_helper_source_apply_manifest.json", manifest)

    print(f"DD-089D guarded helper source apply manifest: {out / 'dd089d_guarded_helper_source_apply_manifest.json'}")
    print(f"status: {status}; applied: {applied_count}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
