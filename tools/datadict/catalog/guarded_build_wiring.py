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


EXPECTED_DD089G_STATUS = "DDICT_CMD_DDICT_INTEGRATION_APPLIED_BUILD_WIRING_PENDING"

CMAKE_REL = "src/CMakeLists.txt"
HELPER_SOURCES = [
    "src/datadict/ddict_read_helpers.cpp",
    "src/datadict/ddict_catalog_paths.cpp",
    "src/datadict/ddict_dbf_reader.cpp",
    "src/datadict/ddict_object_resolver.cpp",
]

HELPER_CMAKE_SOURCES = [
    "datadict/ddict_read_helpers.cpp",
    "datadict/ddict_catalog_paths.cpp",
    "datadict/ddict_dbf_reader.cpp",
    "datadict/ddict_object_resolver.cpp",
]

PROTECTED_UNTOUCHED = [
    "src/cli/cmd_ddict.cpp",
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


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


def diff_text(old: str, new: str, name: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=name + ".before",
        tofile=name + ".after",
        lineterm="",
    ))


def already_wired(cmake_text: str) -> bool:
    lower = cmake_text.lower()
    return all(src.lower() in lower for src in HELPER_CMAKE_SOURCES)


def make_candidate(cmake_text: str) -> tuple[str, int]:
    if already_wired(cmake_text):
        return cmake_text, 0

    block = """
# DD-089H guarded Data Dictionary helper source wiring.
# These files support the refactored DDICT read-only catalog command surface.
if(TARGET dottalkpp)
  target_sources(dottalkpp PRIVATE
    datadict/ddict_read_helpers.cpp
    datadict/ddict_catalog_paths.cpp
    datadict/ddict_dbf_reader.cpp
    datadict/ddict_object_resolver.cpp
  )
endif()
"""
    if "DD-089H guarded Data Dictionary helper source wiring" in cmake_text:
        return cmake_text, 0
    return cmake_text.rstrip() + "\n" + block + "\n", 1


def classify_cmake(cmake_text: str) -> Dict[str, Any]:
    lower = cmake_text.lower()
    upper = cmake_text.upper()
    return {
        "uses_glob": int("glob" in lower),
        "has_target_dottalkpp": int("dottalkpp" in lower),
        "has_target_sources": int("target_sources" in lower),
        "mentions_datadict": int("datadict" in lower),
        "already_wired": int(already_wired(cmake_text)),
        "has_dd089h_block": int("DD-089H guarded Data Dictionary helper source wiring" in cmake_text),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-089H guarded DDICT helper build wiring")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD089H-guarded-build-wiring-v0")
    ap.add_argument("--dd089g-dir", default="docs/datadict/reports/DD089G-guarded-cmd-ddict-integration-apply-apply-v0")
    ap.add_argument("--apply-build-wiring", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd089g_dir = (repo / args.dd089g_dir).resolve()
    dd089g_manifest = read_json(dd089g_dir / "dd089g_guarded_cmd_ddict_integration_apply_manifest.json")

    cmake_path = repo / CMAKE_REL
    cmake_before = read_text(cmake_path)
    cmake_candidate, block_added = make_candidate(cmake_before)
    classified_before = classify_cmake(cmake_before)
    classified_candidate = classify_cmake(cmake_candidate)

    generated_dir = out / "generated_build_wiring"
    generated_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = generated_dir / CMAKE_REL
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(cmake_candidate, encoding="utf-8")
    diff_path = generated_dir / (CMAKE_REL + ".diff")
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    diff_path.write_text(diff_text(cmake_before, cmake_candidate, CMAKE_REL), encoding="utf-8")

    review_rows: List[Dict[str, Any]] = []
    dd089g_green = int(dd089g_manifest.get("status") == EXPECTED_DD089G_STATUS)
    if not dd089g_green:
        review_rows.append({"issue": "DD089G_NOT_READY", "detail": dd089g_manifest.get("status", "")})
    if not cmake_path.exists():
        review_rows.append({"issue": "CMAKE_MISSING", "detail": str(cmake_path)})
    if not classified_candidate["has_target_dottalkpp"]:
        review_rows.append({"issue": "TARGET_DOTTALKPP_NOT_DETECTED", "detail": "CMake text does not mention dottalkpp; target_sources guard may not attach."})

    helper_rows = []
    for rel_src in HELPER_SOURCES:
        path = repo / rel_src
        helper_rows.append({
            "helper_source": rel_src,
            "exists": int(path.exists()),
            "bytes": path.stat().st_size if path.exists() else 0,
            "hash": sha256(path),
        })
        if not path.exists():
            review_rows.append({"issue": "HELPER_SOURCE_MISSING", "detail": rel_src})

    protected_rows = []
    protected_before = {}
    for rel_path in PROTECTED_UNTOUCHED:
        path = repo / rel_path
        protected_before[rel_path] = sha256(path)
        protected_rows.append({
            "protected_path": rel_path,
            "exists_before": int(path.exists()),
            "hash_before": protected_before[rel_path],
            "hash_after": "",
            "mutated_by_dd089h": "",
        })

    applied = 0
    backup_path = ""
    review_before_apply = len(review_rows)

    needs_apply = int(cmake_candidate != cmake_before)
    if args.apply_build_wiring and review_before_apply == 0 and needs_apply:
        backup_dir = (repo / args.backup_root) / f"{args.run_id}_{stamp()}"
        backup_target = backup_dir / CMAKE_REL
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cmake_path, backup_target)
        backup_path = str(backup_target)
        cmake_path.write_text(cmake_candidate, encoding="utf-8")
        applied = 1

    cmake_after = read_text(cmake_path)
    matches_candidate_after = int(cmake_path.exists() and cmake_after == cmake_candidate)
    classified_after = classify_cmake(cmake_after)

    protected_mutations = 0
    for row in protected_rows:
        path = repo / row["protected_path"]
        after = sha256(path)
        row["hash_after"] = after
        row["mutated_by_dd089h"] = int(after != row["hash_before"])
        protected_mutations += int(row["mutated_by_dd089h"])

    cmake_rows = [{
        "cmake_path": CMAKE_REL,
        "exists": int(cmake_path.exists()),
        "uses_glob_before": classified_before["uses_glob"],
        "mentions_datadict_before": classified_before["mentions_datadict"],
        "already_wired_before": classified_before["already_wired"],
        "block_added_to_candidate": block_added,
        "needs_apply": needs_apply,
        "apply_requested": int(args.apply_build_wiring),
        "applied": applied,
        "matches_candidate_after": matches_candidate_after,
        "already_wired_after": classified_after["already_wired"],
        "has_dd089h_block_after": classified_after["has_dd089h_block"],
        "backup_path": backup_path,
    }]

    helper_count = sum(1 for r in helper_rows if int(r["exists"]) == 1)
    apply_ok = int((not args.apply_build_wiring) or applied or matches_candidate_after or classified_after["already_wired"])

    gate_rows = [
        {"gate": "dd089g_cmd_ddict_applied", "expected": EXPECTED_DD089G_STATUS, "observed": dd089g_manifest.get("status", ""), "pass": dd089g_green},
        {"gate": "cmake_exists", "expected": 1, "observed": int(cmake_path.exists()), "pass": int(cmake_path.exists())},
        {"gate": "helper_sources_exist", "expected": len(HELPER_SOURCES), "observed": helper_count, "pass": int(helper_count == len(HELPER_SOURCES))},
        {"gate": "cmake_candidate_generated", "expected": 1, "observed": int(candidate_path.exists()), "pass": int(candidate_path.exists())},
        {"gate": "build_wiring_applied_when_requested", "expected": int(args.apply_build_wiring), "observed": int(applied or classified_after["already_wired"]), "pass": apply_ok},
        {"gate": "protected_files_unmutated", "expected": 0, "observed": protected_mutations, "pass": int(protected_mutations == 0)},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)

    if args.apply_build_wiring and failures == 0:
        status = "DDICT_HELPER_BUILD_WIRING_APPLIED_BUILD_REQUIRED"
    elif failures == 0:
        status = "DDICT_HELPER_BUILD_WIRING_READY"
    else:
        status = "DDICT_HELPER_BUILD_WIRING_REVIEW"

    boundary_rows = [
        {"boundary": "guarded_build_wiring", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cmake_build_file_edits", "observed": applied, "required": int(args.apply_build_wiring), "pass": int((not args.apply_build_wiring) or applied or classified_after["already_wired"])},
        {"boundary": "cmd_ddict_cpp_patched", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "helper_source_files_modified", "observed": 0, "required": 0, "pass": 1},
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
            "next_id": "BUILD",
            "title": "Build dottalkpp",
            "allowed_scope": "cmake --build build --config Release --target dottalkpp",
        },
        {
            "next_id": "DD089I",
            "title": "DDICT refactor parity closure",
            "allowed_scope": "close build/runtime parity after successful build and DDICT smoke transcript",
        },
    ]

    write_csv(out / "dd089h_cmake_wiring_ledger.csv", cmake_rows, ["cmake_path", "exists", "uses_glob_before", "mentions_datadict_before", "already_wired_before", "block_added_to_candidate", "needs_apply", "apply_requested", "applied", "matches_candidate_after", "already_wired_after", "has_dd089h_block_after", "backup_path"])
    write_csv(out / "dd089h_helper_source_ledger.csv", helper_rows, ["helper_source", "exists", "bytes", "hash"])
    write_csv(out / "dd089h_protected_file_ledger.csv", protected_rows, ["protected_path", "exists_before", "hash_before", "hash_after", "mutated_by_dd089h"])
    write_csv(out / "dd089h_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd089h_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd089h_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd089h_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-089H Guarded DDICT Helper Build Wiring

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-089H wires the extracted Data Dictionary helper source files into the `dottalkpp` build when
`--apply-build-wiring` is supplied.

## Inputs

- DD-089G status: `{dd089g_manifest.get('status', '')}`
- CMake file: `{CMAKE_REL}`
- Helper sources: `{len(HELPER_SOURCES)}`

## Result

- Apply requested: **{int(args.apply_build_wiring)}**
- CMake already wired before: **{classified_before['already_wired']}**
- Candidate block added: **{block_added}**
- Needs apply: **{needs_apply}**
- Applied: **{applied}**
- Matches candidate after: **{matches_candidate_after}**
- Helper sources present: **{helper_count} / {len(HELPER_SOURCES)}**
- Backup path: `{backup_path}`

## Boundary

DD-089H may edit only `src/CMakeLists.txt` when explicitly requested.
It does not patch `cmd_ddict.cpp`, modify helper source files, edit command registration,
mutate active catalog data, create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK,
regenerate catalog content, or repair manual rows.

## Next

After DD-089H apply is green, build `dottalkpp`, then run DD-089I parity closure.
"""
    (out / "DD089H_GUARDED_DDICT_HELPER_BUILD_WIRING_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd089h_guarded_build_wiring_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd089g_status": dd089g_manifest.get("status", ""),
        "cmake_path": CMAKE_REL,
        "apply_build_wiring": int(args.apply_build_wiring),
        "applied": applied,
        "matches_candidate_after": matches_candidate_after,
        "helper_sources_present": helper_count,
        "helper_sources_expected": len(HELPER_SOURCES),
        "backup_path": backup_path,
        "failures": failures,
        "cmd_ddict_cpp_patched": 0,
        "helper_source_files_modified": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Build dottalkpp; then DD-089I parity closure.",
    }
    write_json(out / "dd089h_guarded_build_wiring_manifest.json", manifest)

    print(f"DD-089H guarded build wiring manifest: {out / 'dd089h_guarded_build_wiring_manifest.json'}")
    print(f"status: {status}; applied: {applied}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
