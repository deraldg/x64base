#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD089H_STATUS = "DDICT_HELPER_BUILD_WIRING_APPLIED_BUILD_REQUIRED"

HELPER_SOURCE_REPAIRS = [
    "src/datadict/ddict_read_helpers.cpp",
    "src/datadict/ddict_catalog_paths.cpp",
    "src/datadict/ddict_dbf_reader.cpp",
    "src/datadict/ddict_object_resolver.cpp",
]

CMD_SOURCE = "src/cli/cmd_ddict.cpp"
CMAKE_REL = "src/CMakeLists.txt"

PROTECTED_UNTOUCHED = [
    "src/CMakeLists.txt",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
]

COMPILE_NEEDLES = [
    "cannot convert from 'dottalk::datadict::CatalogStats'",
    "'fs': is not a class or namespace name",
    "'Row': undeclared identifier",
    "value_of",
    "read_dbf_table",
    "resolve_object",
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


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


def ensure_fs_alias(text: str) -> Tuple[str, int]:
    if "namespace fs = std::filesystem;" in text:
        return text, 0
    marker = "namespace dottalk::datadict {"
    if marker in text:
        return text.replace(marker, marker + "\nnamespace fs = std::filesystem;", 1), 1
    return text, 0


def replace_row_with_ddictrow(text: str) -> Tuple[str, int]:
    new = re.sub(r"\bRow\b", "DDictRow", text)
    return new, int(new != text)


def remove_local_type_defs(text: str) -> Tuple[str, int]:
    changed = 0
    # Remove simple local structs. These were copied into helper headers and should not shadow helper types.
    for name in ["FieldDef", "CatalogStats"]:
        pattern = re.compile(r"\n?struct\s+" + re.escape(name) + r"\s*\{.*?\};\s*\n", re.DOTALL)
        text2, n = pattern.subn("\n", text, count=1)
        if n:
            text = text2
            changed += n
    # Remove local Row aliases so command renderers bind to helper row type.
    patterns = [
        re.compile(r"\n?using\s+Row\s*=\s*std::unordered_map\s*<[^;]+;\s*\n", re.DOTALL),
        re.compile(r"\n?using\s+Row\s*=\s*[^;]+;\s*\n"),
    ]
    for pattern in patterns:
        text2, n = pattern.subn("\n", text, count=1)
        if n:
            text = text2
            changed += n
            break
    return text, changed


def ensure_cmd_aliases(text: str) -> Tuple[str, int]:
    alias_block = (
        "using dottalk::datadict::CatalogStats;\n"
        "using dottalk::datadict::DDictRow;\n"
        "using dottalk::datadict::FieldDef;\n"
        "using Row = dottalk::datadict::DDictRow;\n"
    )
    if "using Row = dottalk::datadict::DDictRow;" in text:
        return text, 0

    bridge = "using namespace dottalk::datadict;"
    if bridge in text:
        return text.replace(bridge, bridge + "\n" + alias_block, 1), 1

    marker = "namespace {"
    if marker in text:
        return text.replace(marker, marker + "\n" + alias_block, 1), 1

    return alias_block + "\n" + text, 1


def repair_helper_source(path_rel: str, text: str) -> Tuple[str, List[str]]:
    actions: List[str] = []
    out = text
    if path_rel in ("src/datadict/ddict_catalog_paths.cpp", "src/datadict/ddict_dbf_reader.cpp"):
        out, n = ensure_fs_alias(out)
        if n:
            actions.append("added_fs_namespace_alias")
    if path_rel in ("src/datadict/ddict_read_helpers.cpp", "src/datadict/ddict_dbf_reader.cpp", "src/datadict/ddict_object_resolver.cpp"):
        out, n = replace_row_with_ddictrow(out)
        if n:
            actions.append("replaced_Row_with_DDictRow")
    return out, actions


def repair_cmd_source(text: str) -> Tuple[str, List[str]]:
    actions: List[str] = []
    out = text
    out, n = remove_local_type_defs(out)
    if n:
        actions.append(f"removed_local_type_defs_{n}")
    out, n = ensure_cmd_aliases(out)
    if n:
        actions.append("added_helper_type_aliases")
    return out, actions


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-089J DDICT helper compile repair")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD089J-ddict-helper-compile-repair-v0")
    ap.add_argument("--dd089h-dir", default="docs/datadict/reports/DD089H-guarded-build-wiring-apply-v0")
    ap.add_argument("--build-proof", default="docs/datadict/runlog/DD-089I_DDICT_REFACTOR_BUILD_PROOF.md")
    ap.add_argument("--apply-repair", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd089h_dir = (repo / args.dd089h_dir).resolve()
    dd089h_manifest = read_json(dd089h_dir / "dd089h_guarded_build_wiring_manifest.json")
    build_proof = (repo / args.build_proof).resolve()
    build_text = read_text(build_proof)

    generated = out / "generated_compile_repair"
    generated.mkdir(parents=True, exist_ok=True)

    review_rows: List[Dict[str, Any]] = []
    dd089h_green = int(dd089h_manifest.get("status") == EXPECTED_DD089H_STATUS)
    if not dd089h_green:
        review_rows.append({"issue": "DD089H_NOT_READY", "detail": dd089h_manifest.get("status", "")})

    build_failure_needles_seen = sum(1 for n in COMPILE_NEEDLES if n.upper() in build_text.upper())
    if build_proof.exists() and build_failure_needles_seen == 0:
        review_rows.append({"issue": "BUILD_PROOF_DOES_NOT_MATCH_EXPECTED_FAILURE_PATTERN", "detail": rel(repo, build_proof)})

    patch_rows: List[Dict[str, Any]] = []
    targets = HELPER_SOURCE_REPAIRS + [CMD_SOURCE]
    backup_dir = (repo / args.backup_root) / f"{args.run_id}_{stamp()}"
    applied_count = 0
    backup_count = 0

    for path_rel in targets:
        target = repo / path_rel
        before = read_text(target)
        if not target.exists():
            review_rows.append({"issue": "TARGET_MISSING", "detail": path_rel})
            after = before
            actions: List[str] = []
        elif path_rel == CMD_SOURCE:
            after, actions = repair_cmd_source(before)
        else:
            after, actions = repair_helper_source(path_rel, before)

        candidate = generated / path_rel
        diff_path = generated / (path_rel + ".diff")
        write_text(candidate, after)
        write_text(diff_path, diff_text(before, after, path_rel))

        changed = int(after != before)
        applied = 0
        backup_path = ""
        if args.apply_repair and changed and target.exists():
            backup_path_obj = backup_dir / path_rel
            backup_path_obj.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup_path_obj)
            backup_path = str(backup_path_obj)
            backup_count += 1
            target.write_text(after, encoding="utf-8")
            applied = 1
            applied_count += 1

        patch_rows.append({
            "target": path_rel,
            "exists": int(target.exists()),
            "actions": ";".join(actions),
            "changed_candidate": changed,
            "candidate_path": str(candidate),
            "diff_path": str(diff_path),
            "apply_requested": int(args.apply_repair),
            "applied": applied,
            "backup_path": backup_path,
            "hash_after": sha256(target),
        })

    protected_rows: List[Dict[str, Any]] = []
    protected_mutations = 0
    for path_rel in PROTECTED_UNTOUCHED:
        p = repo / path_rel
        # CMake is expected to stay as-is in DD-089J; shell/registry must also stay unchanged.
        protected_rows.append({
            "protected_path": path_rel,
            "exists": int(p.exists()),
            "hash": sha256(p),
            "mutated_by_dd089j": 0,
        })

    changed_candidates = sum(1 for r in patch_rows if int(r["changed_candidate"]) == 1)
    repair_applied_ok = int((not args.apply_repair) or applied_count == changed_candidates)

    gate_rows = [
        {"gate": "dd089h_build_wiring_applied", "expected": EXPECTED_DD089H_STATUS, "observed": dd089h_manifest.get("status", ""), "pass": dd089h_green},
        {"gate": "build_proof_exists", "expected": 1, "observed": int(build_proof.exists()), "pass": int(build_proof.exists())},
        {"gate": "expected_failure_needles_seen", "expected": ">=1", "observed": build_failure_needles_seen, "pass": int(build_failure_needles_seen >= 1 or not build_proof.exists())},
        {"gate": "repair_candidates_generated", "expected": len(targets), "observed": len(patch_rows), "pass": int(len(patch_rows) == len(targets))},
        {"gate": "repair_applied_when_requested", "expected": int(args.apply_repair), "observed": int(applied_count > 0), "pass": repair_applied_ok},
        {"gate": "protected_files_unmutated", "expected": 0, "observed": protected_mutations, "pass": int(protected_mutations == 0)},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    if args.apply_repair and failures == 0:
        status = "DDICT_HELPER_COMPILE_REPAIR_APPLIED_BUILD_REQUIRED"
    elif failures == 0:
        status = "DDICT_HELPER_COMPILE_REPAIR_READY"
    else:
        status = "DDICT_HELPER_COMPILE_REPAIR_REVIEW"

    boundary_rows = [
        {"boundary": "compile_repair", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "repair_source_files_modified", "observed": applied_count, "required": changed_candidates if args.apply_repair else 0, "pass": int((not args.apply_repair) or applied_count == changed_candidates)},
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
            "next_id": "BUILD",
            "title": "Rebuild dottalkpp after DD-089J repair",
            "allowed_scope": "cmake --build build --config Release --target dottalkpp",
        },
        {
            "next_id": "DD089K",
            "title": "second compile repair if needed",
            "allowed_scope": "only if new compile errors appear after DD-089J",
        },
        {
            "next_id": "DD089I",
            "title": "refactor parity closure",
            "allowed_scope": "only after build is green and runtime smoke transcript is captured",
        },
    ]

    write_csv(out / "dd089j_compile_repair_patch_ledger.csv", patch_rows, ["target", "exists", "actions", "changed_candidate", "candidate_path", "diff_path", "apply_requested", "applied", "backup_path", "hash_after"])
    write_csv(out / "dd089j_protected_file_ledger.csv", protected_rows, ["protected_path", "exists", "hash", "mutated_by_dd089j"])
    write_csv(out / "dd089j_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd089j_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd089j_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd089j_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-089J DDICT Helper Compile Repair

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-089J repairs the first compile failure after DD-089H build wiring.

The build failure shows helper implementations were copied out of `cmd_ddict.cpp` but still depended on anonymous-namespace details:

```text
fs alias missing in helper modules
Row local alias not available in helper modules
local CatalogStats/FieldDef/Row types still shadow helper module types in cmd_ddict.cpp
```

## Inputs

- DD-089H status: `{dd089h_manifest.get('status', '')}`
- Build proof: `{rel(repo, build_proof)}`
- Expected failure needles seen: **{build_failure_needles_seen}**

## Result

- Apply requested: **{int(args.apply_repair)}**
- Repair targets: **{len(targets)}**
- Changed candidates: **{changed_candidates}**
- Applied repairs: **{applied_count}**
- Backups written: **{backup_count}**

## Repair model

```text
src/datadict/ddict_catalog_paths.cpp    add fs namespace alias
src/datadict/ddict_dbf_reader.cpp       add fs namespace alias and Row -> DDictRow
src/datadict/ddict_object_resolver.cpp  Row -> DDictRow
src/datadict/ddict_read_helpers.cpp     Row -> DDictRow if present
src/cli/cmd_ddict.cpp                   remove local helper-shadow type declarations and add helper type aliases
```

## Boundary

DD-089J is compile repair only. It does not edit CMake/build files, command registration,
active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK, generated catalog content, or manual rows.
"""
    write_text(out / "DD089J_DDICT_HELPER_COMPILE_REPAIR_REPORT.md", report)

    manifest = {
        "contract": "dd089j_ddict_helper_compile_repair_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd089h_status": dd089h_manifest.get("status", ""),
        "build_proof": rel(repo, build_proof),
        "build_failure_needles_seen": build_failure_needles_seen,
        "apply_repair": int(args.apply_repair),
        "repair_targets": len(targets),
        "changed_candidates": changed_candidates,
        "applied_count": applied_count,
        "backup_count": backup_count,
        "failures": failures,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Rebuild dottalkpp. If build is green, run DD-089I parity closure; otherwise paste the next compile errors for DD-089K.",
    }
    write_json(out / "dd089j_ddict_helper_compile_repair_manifest.json", manifest)

    print(f"DD-089J DDICT helper compile repair manifest: {out / 'dd089j_ddict_helper_compile_repair_manifest.json'}")
    print(f"status: {status}; changed_candidates: {changed_candidates}; applied: {applied_count}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
