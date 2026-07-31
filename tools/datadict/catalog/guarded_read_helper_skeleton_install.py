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


EXPECTED_DD089A_STATUS = "DDICT_READ_HELPER_SKELETON_PACKAGE_READY"

INSTALL_ARTIFACTS = [
    "include/datadict/ddict_read_helpers.hpp",
    "src/datadict/ddict_read_helpers.cpp",
    "include/datadict/ddict_catalog_paths.hpp",
    "src/datadict/ddict_catalog_paths.cpp",
    "include/datadict/ddict_dbf_reader.hpp",
    "src/datadict/ddict_dbf_reader.cpp",
    "include/datadict/ddict_object_resolver.hpp",
    "src/datadict/ddict_object_resolver.cpp",
    "docs/datadict/fragments/DD089A_candidate_cmake_fragment.txt",
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
    ap = argparse.ArgumentParser(description="DD-089B guarded read-helper skeleton install package")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD089B-guarded-read-helper-skeleton-install-v0")
    ap.add_argument("--dd089a-dir", default="docs/datadict/reports/DD089A-read-helper-skeleton-interface-package-v0")
    ap.add_argument("--apply-install", action="store_true")
    ap.add_argument("--replace-existing", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd089a_dir = (repo / args.dd089a_dir).resolve()
    dd089a_manifest = read_json(dd089a_dir / "dd089a_read_helper_skeleton_interface_package_manifest.json")
    generated_root = Path(dd089a_manifest.get("generated_skeleton_root", ""))

    if not generated_root.is_absolute():
        generated_root = (dd089a_dir / "generated_skeleton").resolve()

    backup_root = (repo / args.backup_root).resolve()
    backup_dir = backup_root / f"{args.run_id}_{stamp()}"

    artifact_rows: List[Dict[str, Any]] = []
    review_rows: List[Dict[str, Any]] = []

    dd089a_green = int(dd089a_manifest.get("status") == EXPECTED_DD089A_STATUS)
    if not dd089a_green:
        review_rows.append({"issue": "DD089A_NOT_READY", "detail": dd089a_manifest.get("status", "")})

    if not generated_root.exists():
        review_rows.append({"issue": "GENERATED_SKELETON_ROOT_MISSING", "detail": str(generated_root)})

    for rel_art in INSTALL_ARTIFACTS:
        src = generated_root / rel_art
        dest = repo / rel_art
        exists_src = int(src.exists())
        exists_dest = int(dest.exists())
        dest_same = int(exists_src and exists_dest and filecmp.cmp(src, dest, shallow=False))
        needs_install = int(exists_src and (not exists_dest or not dest_same))
        blocked_existing = int(exists_src and exists_dest and not dest_same and not args.replace_existing)

        if not exists_src:
            review_rows.append({"issue": "SKELETON_ARTIFACT_MISSING", "detail": rel_art})
        if blocked_existing:
            review_rows.append({"issue": "TARGET_EXISTS_REPLACE_NOT_ALLOWED", "detail": rel_art})

        artifact_rows.append({
            "artifact": rel_art,
            "generated_path": str(src),
            "target_path": rel(repo, dest),
            "generated_exists": exists_src,
            "target_exists_before": exists_dest,
            "target_same_before": dest_same,
            "needs_install": needs_install,
            "blocked_existing": blocked_existing,
            "installed": 0,
            "backup_path": "",
            "target_hash_after": "",
        })

    protected_rows: List[Dict[str, Any]] = []
    protected_before = {}
    for rel_path in PROTECTED_UNTOUCHED:
        p = repo / rel_path
        protected_before[rel_path] = sha256(p)
        protected_rows.append({
            "protected_path": rel_path,
            "exists_before": int(p.exists()),
            "hash_before": protected_before[rel_path],
            "hash_after": "",
            "mutated": "",
        })

    failures_pre_apply = len(review_rows)
    installed_count = 0
    backup_count = 0

    if args.apply_install and failures_pre_apply == 0:
        for row in artifact_rows:
            if int(row["needs_install"]) != 1:
                continue
            src = Path(row["generated_path"])
            dest = repo / row["target_path"]
            if dest.exists():
                backup_target = backup_dir / row["target_path"]
                backup_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dest, backup_target)
                row["backup_path"] = str(backup_target)
                backup_count += 1
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            row["installed"] = 1
            row["target_hash_after"] = sha256(dest)
            installed_count += 1

    for row in protected_rows:
        p = repo / row["protected_path"]
        after = sha256(p)
        row["hash_after"] = after
        row["mutated"] = int(after != row["hash_before"])

    protected_mutations = sum(1 for row in protected_rows if int(row["mutated"]) == 1)

    apply_ok = int((not args.apply_install) or (installed_count >= 1 and protected_mutations == 0))
    gate_rows = [
        {"gate": "dd089a_skeleton_package_ready", "expected": EXPECTED_DD089A_STATUS, "observed": dd089a_manifest.get("status", ""), "pass": dd089a_green},
        {"gate": "generated_skeleton_root_exists", "expected": 1, "observed": int(generated_root.exists()), "pass": int(generated_root.exists())},
        {"gate": "all_install_artifacts_present", "expected": len(INSTALL_ARTIFACTS), "observed": sum(1 for r in artifact_rows if int(r["generated_exists"]) == 1), "pass": int(sum(1 for r in artifact_rows if int(r["generated_exists"]) == 1) == len(INSTALL_ARTIFACTS))},
        {"gate": "replace_policy_clean", "expected": 0, "observed": sum(1 for r in artifact_rows if int(r["blocked_existing"]) == 1), "pass": int(sum(1 for r in artifact_rows if int(r["blocked_existing"]) == 1) == 0)},
        {"gate": "protected_files_unmutated", "expected": 0, "observed": protected_mutations, "pass": int(protected_mutations == 0)},
        {"gate": "install_applied_when_requested", "expected": int(args.apply_install), "observed": int(installed_count > 0), "pass": apply_ok},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    if args.apply_install and failures == 0:
        status = "DDICT_READ_HELPER_SKELETON_FILES_INSTALLED_BUILD_UNWIRED"
    elif failures == 0:
        status = "DDICT_READ_HELPER_SKELETON_INSTALL_READY"
    else:
        status = "DDICT_READ_HELPER_SKELETON_INSTALL_REVIEW"

    boundary_rows = [
        {"boundary": "guarded_skeleton_install", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "repo_cxx_files_installed", "observed": installed_count, "required": int(args.apply_install) * 8, "pass": int((not args.apply_install) or installed_count >= 8)},
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
            "next_id": "DD089C",
            "title": "guarded implementation extraction preview",
            "allowed_scope": "prepare diff to move helper implementation from cmd_ddict.cpp into installed helper files; do not apply without explicit authorization",
        },
        {
            "next_id": "DD089D",
            "title": "build wiring and parity closure",
            "allowed_scope": "wire helper cpp files only after implementation extraction is accepted and previewed",
        },
    ]

    write_csv(out / "dd089b_skeleton_install_ledger.csv", artifact_rows, ["artifact", "generated_path", "target_path", "generated_exists", "target_exists_before", "target_same_before", "needs_install", "blocked_existing", "installed", "backup_path", "target_hash_after"])
    write_csv(out / "dd089b_protected_file_ledger.csv", protected_rows, ["protected_path", "exists_before", "hash_before", "hash_after", "mutated"])
    write_csv(out / "dd089b_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd089b_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd089b_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd089b_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-089B Guarded Read-Helper Skeleton Install

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-089B installs the DD-089A generated read-helper skeleton/interface files into the repository source tree when `--apply-install` is supplied.

It still does not patch `cmd_ddict.cpp`, edit CMake/build files, or migrate implementation code.

## Inputs

- DD-089A status: `{dd089a_manifest.get('status', '')}`
- Generated skeleton root: `{generated_root}`

## Result

- Apply requested: **{int(args.apply_install)}**
- Replace existing allowed: **{int(args.replace_existing)}**
- Install artifacts expected: **{len(INSTALL_ARTIFACTS)}**
- Installed artifacts: **{installed_count}**
- Backups written: **{backup_count}**
- Protected file mutations: **{protected_mutations}**

## Installed target groups

```text
include/datadict/ddict_read_helpers.hpp
src/datadict/ddict_read_helpers.cpp
include/datadict/ddict_catalog_paths.hpp
src/datadict/ddict_catalog_paths.cpp
include/datadict/ddict_dbf_reader.hpp
src/datadict/ddict_dbf_reader.cpp
include/datadict/ddict_object_resolver.hpp
src/datadict/ddict_object_resolver.cpp
docs/datadict/fragments/DD089A_candidate_cmake_fragment.txt
```

## Boundary

DD-089B is guarded skeleton install only. It does not patch `cmd_ddict.cpp`, edit build files,
edit command registration, wire CMake, migrate implementation logic, mutate active catalog data,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    (out / "DD089B_GUARDED_READ_HELPER_SKELETON_INSTALL_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd089b_guarded_read_helper_skeleton_install_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd089a_status": dd089a_manifest.get("status", ""),
        "generated_skeleton_root": str(generated_root),
        "apply_install": int(args.apply_install),
        "replace_existing": int(args.replace_existing),
        "install_artifacts_expected": len(INSTALL_ARTIFACTS),
        "installed_count": installed_count,
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
        "next_recommended_action": "DD-089C guarded implementation extraction preview, explicitly authorized.",
    }
    write_json(out / "dd089b_guarded_read_helper_skeleton_install_manifest.json", manifest)

    print(f"DD-089B guarded read-helper skeleton install manifest: {out / 'dd089b_guarded_read_helper_skeleton_install_manifest.json'}")
    print(f"status: {status}; installed: {installed_count}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
