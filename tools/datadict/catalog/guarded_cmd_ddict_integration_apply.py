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


EXPECTED_DD089F_STATUS = "DDICT_CMD_DDICT_APPLY_BUILD_WIRING_PLAN_READY"

CMD_SOURCE = "src/cli/cmd_ddict.cpp"
PROTECTED_UNTOUCHED = [
    "src/CMakeLists.txt",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
]

HELPER_ARTIFACTS = [
    "include/datadict/ddict_read_helpers.hpp",
    "include/datadict/ddict_catalog_paths.hpp",
    "include/datadict/ddict_dbf_reader.hpp",
    "include/datadict/ddict_object_resolver.hpp",
    "src/datadict/ddict_read_helpers.cpp",
    "src/datadict/ddict_catalog_paths.cpp",
    "src/datadict/ddict_dbf_reader.cpp",
    "src/datadict/ddict_object_resolver.cpp",
]

REQUIRED_CANDIDATE_MARKERS = [
    '#include "datadict/ddict_read_helpers.hpp"',
    '#include "datadict/ddict_catalog_paths.hpp"',
    '#include "datadict/ddict_dbf_reader.hpp"',
    '#include "datadict/ddict_object_resolver.hpp"',
    "dottalk::datadict",
    "print_status",
    "print_tables",
    "print_fields",
    "print_tags",
    "print_rel",
    "print_evidence",
    "print_objects",
    "cmd_DDICT",
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-089G guarded cmd_ddict integration apply")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD089G-guarded-cmd-ddict-integration-apply-v0")
    ap.add_argument("--dd089f-dir", default="docs/datadict/reports/DD089F-cmd-ddict-integration-apply-build-wiring-plan-v0")
    ap.add_argument("--apply-cmd-ddict", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd089f_dir = (repo / args.dd089f_dir).resolve()
    dd089f_manifest = read_json(dd089f_dir / "dd089f_cmd_ddict_integration_apply_build_wiring_plan_manifest.json")
    backup_root = (repo / args.backup_root).resolve()
    backup_dir = backup_root / f"{args.run_id}_{stamp()}"

    cmd_target = repo / CMD_SOURCE
    candidate_rel = dd089f_manifest.get("candidate_source", "")
    candidate_path = repo / candidate_rel if candidate_rel else Path("")
    candidate_text = read_text(candidate_path)
    current_text = read_text(cmd_target)

    review_rows: List[Dict[str, Any]] = []
    dd089f_green = int(dd089f_manifest.get("status") == EXPECTED_DD089F_STATUS)
    if not dd089f_green:
        review_rows.append({"issue": "DD089F_NOT_READY", "detail": dd089f_manifest.get("status", "")})
    if not cmd_target.exists():
        review_rows.append({"issue": "CMD_TARGET_MISSING", "detail": str(cmd_target)})
    if not candidate_path.exists():
        review_rows.append({"issue": "CANDIDATE_SOURCE_MISSING", "detail": str(candidate_path)})

    marker_rows = []
    for marker in REQUIRED_CANDIDATE_MARKERS:
        present = int(marker in candidate_text)
        marker_rows.append({"marker": marker, "present_in_candidate": present})
        if not present:
            review_rows.append({"issue": "CANDIDATE_MARKER_MISSING", "detail": marker})

    helper_rows = []
    for art in HELPER_ARTIFACTS:
        path = repo / art
        helper_rows.append({
            "artifact": art,
            "exists": int(path.exists()),
            "bytes": path.stat().st_size if path.exists() else 0,
            "hash": sha256(path),
        })
        if not path.exists():
            review_rows.append({"issue": "HELPER_ARTIFACT_MISSING", "detail": art})

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
            "mutated_by_dd089g": "",
        })

    target_same_before = int(candidate_path.exists() and cmd_target.exists() and filecmp.cmp(candidate_path, cmd_target, shallow=False))
    needs_apply = int(candidate_path.exists() and cmd_target.exists() and not target_same_before)
    applied = 0
    backup_path = ""

    review_before_apply = len(review_rows)

    if args.apply_cmd_ddict and review_before_apply == 0 and needs_apply:
        backup_target = backup_dir / CMD_SOURCE
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cmd_target, backup_target)
        backup_path = str(backup_target)
        shutil.copy2(candidate_path, cmd_target)
        applied = 1

    protected_mutations = 0
    for row in protected_rows:
        path = repo / row["protected_path"]
        after = sha256(path)
        row["hash_after"] = after
        row["mutated_by_dd089g"] = int(after != row["hash_before"])
        protected_mutations += int(row["mutated_by_dd089g"])

    target_hash_before = sha256(candidate_path) if target_same_before else sha256(backup_dir / CMD_SOURCE) if applied else sha256(cmd_target)
    target_hash_after = sha256(cmd_target)
    target_matches_candidate_after = int(candidate_path.exists() and cmd_target.exists() and filecmp.cmp(candidate_path, cmd_target, shallow=False))

    command_row = [{
        "target": CMD_SOURCE,
        "candidate_path": str(candidate_path),
        "target_exists_before": int(cmd_target.exists()),
        "candidate_exists": int(candidate_path.exists()),
        "target_same_before": target_same_before,
        "needs_apply": needs_apply,
        "apply_requested": int(args.apply_cmd_ddict),
        "applied": applied,
        "backup_path": backup_path,
        "target_hash_after": target_hash_after,
        "matches_candidate_after": target_matches_candidate_after,
    }]

    helper_count = sum(1 for r in helper_rows if int(r["exists"]) == 1)
    marker_count = sum(1 for r in marker_rows if int(r["present_in_candidate"]) == 1)

    gate_rows = [
        {"gate": "dd089f_plan_ready", "expected": EXPECTED_DD089F_STATUS, "observed": dd089f_manifest.get("status", ""), "pass": dd089f_green},
        {"gate": "cmd_target_exists", "expected": 1, "observed": int(cmd_target.exists()), "pass": int(cmd_target.exists())},
        {"gate": "candidate_source_exists", "expected": 1, "observed": int(candidate_path.exists()), "pass": int(candidate_path.exists())},
        {"gate": "candidate_required_markers_present", "expected": len(REQUIRED_CANDIDATE_MARKERS), "observed": marker_count, "pass": int(marker_count == len(REQUIRED_CANDIDATE_MARKERS))},
        {"gate": "helper_artifacts_present", "expected": len(HELPER_ARTIFACTS), "observed": helper_count, "pass": int(helper_count == len(HELPER_ARTIFACTS))},
        {"gate": "protected_files_unmutated", "expected": 0, "observed": protected_mutations, "pass": int(protected_mutations == 0)},
        {"gate": "cmd_ddict_applied_when_requested", "expected": int(args.apply_cmd_ddict), "observed": int(applied or (args.apply_cmd_ddict and target_matches_candidate_after)), "pass": int((not args.apply_cmd_ddict) or applied or target_matches_candidate_after)},
        {"gate": "build_wiring_deferred", "expected": 0, "observed": 0, "pass": 1},
    ]

    failures = sum(1 for row in gate_rows if int(row["pass"]) != 1)

    if args.apply_cmd_ddict and failures == 0:
        status = "DDICT_CMD_DDICT_INTEGRATION_APPLIED_BUILD_WIRING_PENDING"
    elif failures == 0:
        status = "DDICT_CMD_DDICT_INTEGRATION_APPLY_READY"
    else:
        status = "DDICT_CMD_DDICT_INTEGRATION_APPLY_REVIEW"

    boundary_rows = [
        {"boundary": "guarded_cmd_ddict_integration_apply", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cmd_ddict_cpp_patched", "observed": applied, "required": int(args.apply_cmd_ddict), "pass": int((not args.apply_cmd_ddict) or applied or target_matches_candidate_after)},
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
            "next_id": "DD089H",
            "title": "guarded build wiring package",
            "allowed_scope": "wire helper cpp files into build only if CMake does not already include them; then build",
        },
        {
            "next_id": "DD089I",
            "title": "DDICT parity closure",
            "allowed_scope": "run full DDICT smoke suite and close refactor parity after build succeeds",
        },
    ]

    write_csv(out / "dd089g_cmd_ddict_apply_ledger.csv", command_row, ["target", "candidate_path", "target_exists_before", "candidate_exists", "target_same_before", "needs_apply", "apply_requested", "applied", "backup_path", "target_hash_after", "matches_candidate_after"])
    write_csv(out / "dd089g_candidate_marker_ledger.csv", marker_rows, ["marker", "present_in_candidate"])
    write_csv(out / "dd089g_helper_artifact_ledger.csv", helper_rows, ["artifact", "exists", "bytes", "hash"])
    write_csv(out / "dd089g_protected_file_ledger.csv", protected_rows, ["protected_path", "exists_before", "hash_before", "hash_after", "mutated_by_dd089g"])
    write_csv(out / "dd089g_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd089g_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd089g_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd089g_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-089G Guarded cmd_ddict Integration Apply

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-089G applies the DD-089E/089F reviewed `cmd_ddict.cpp` integration candidate when `--apply-cmd-ddict` is supplied.

It does not wire CMake/build files.

## Inputs

- DD-089F status: `{dd089f_manifest.get('status', '')}`
- Target: `{CMD_SOURCE}`
- Candidate: `{candidate_path}`

## Result

- Apply requested: **{int(args.apply_cmd_ddict)}**
- Candidate exists: **{int(candidate_path.exists())}**
- Target same before: **{target_same_before}**
- Applied: **{applied}**
- Matches candidate after: **{target_matches_candidate_after}**
- Backup path: `{backup_path}`
- Protected file mutations: **{protected_mutations}**

## Important interpretation

After DD-089G apply, `cmd_ddict.cpp` may reference datadict helper modules, but CMake/build wiring is still pending.
Do not treat the refactor as runtime-green until DD-089H build wiring and DD-089I parity closure are green.

## Boundary

DD-089G may patch only `src/cli/cmd_ddict.cpp` when explicitly requested.
It does not modify helper source files, edit build files, edit command registration, mutate active catalog data,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    (out / "DD089G_GUARDED_CMD_DDICT_INTEGRATION_APPLY_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd089g_guarded_cmd_ddict_integration_apply_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd089f_status": dd089f_manifest.get("status", ""),
        "target": CMD_SOURCE,
        "candidate_source": str(candidate_path),
        "apply_cmd_ddict": int(args.apply_cmd_ddict),
        "applied": applied,
        "matches_candidate_after": target_matches_candidate_after,
        "backup_path": backup_path,
        "protected_file_mutations": protected_mutations,
        "failures": failures,
        "helper_source_files_modified": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-089H guarded build wiring package, then DD-089I parity closure.",
    }
    write_json(out / "dd089g_guarded_cmd_ddict_integration_apply_manifest.json", manifest)

    print(f"DD-089G guarded cmd_ddict integration apply manifest: {out / 'dd089g_guarded_cmd_ddict_integration_apply_manifest.json'}")
    print(f"status: {status}; applied: {applied}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
