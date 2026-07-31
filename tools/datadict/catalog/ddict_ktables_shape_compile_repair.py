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


EXPECTED_DD089K_STATUS = "DDICT_CATALOG_PATHS_KTABLES_REPAIR_APPLIED_BUILD_REQUIRED"

TARGET_SOURCE = "src/datadict/ddict_catalog_paths.cpp"
PROTECTED_UNTOUCHED = [
    "src/cli/cmd_ddict.cpp",
    "src/CMakeLists.txt",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
    "src/datadict/ddict_read_helpers.cpp",
    "src/datadict/ddict_dbf_reader.cpp",
    "src/datadict/ddict_object_resolver.cpp",
]

TABLEINFO_BLOCK = """
namespace {
struct TableInfo {
    const char* name;
};

constexpr TableInfo kTables[] = {
    {"DDRUN"},
    {"DDBASE"},
    {"DDSOURCE"},
    {"DDOBJECT"},
    {"DDATTR"},
    {"DDEDGE"},
    {"DDEVID"},
    {"DDGATE"},
    {"DDREVIEW"},
    {"DDARTIF"},
    {"DDPROFILE"},
};
} // namespace
"""


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


def has_tableinfo_shape(text: str) -> bool:
    return "struct TableInfo" in text and "const char* name" in text and re.search(r"\bTableInfo\s+kTables\s*\[\s*\]", text) is not None


def has_char_pointer_shape(text: str) -> bool:
    return re.search(r"constexpr\s+const\s+char\s*\*\s*kTables\s*\[\s*\]\s*=", text) is not None


def repair_ktables_shape(text: str) -> Tuple[str, str]:
    if has_tableinfo_shape(text):
        return text, "already_tableinfo_shape"

    # Replace the DD-089K char-pointer block including its wrapping anonymous namespace.
    pattern = re.compile(
        r"\n?namespace\s*\{\s*"
        r"constexpr\s+const\s+char\s*\*\s*kTables\s*\[\s*\]\s*=\s*\{.*?\};\s*"
        r"\}\s*//\s*namespace\s*\n?",
        re.DOTALL,
    )
    new, n = pattern.subn("\n" + TABLEINFO_BLOCK + "\n", text, count=1)
    if n:
        return new, "replaced_const_char_array_with_TableInfo_array"

    # Fallback: replace just the declaration block if namespace wrapper differs.
    pattern2 = re.compile(
        r"constexpr\s+const\s+char\s*\*\s*kTables\s*\[\s*\]\s*=\s*\{.*?\};",
        re.DOTALL,
    )
    new, n = pattern2.subn(TABLEINFO_BLOCK.strip(), text, count=1)
    if n:
        return new, "replaced_const_char_array_decl_with_TableInfo_block"

    # Last-resort insertion: only if no kTables definition exists.
    if "kTables" not in text:
        marker = "namespace fs = std::filesystem;"
        if marker in text:
            return text.replace(marker, marker + "\n" + TABLEINFO_BLOCK, 1), "inserted_TableInfo_after_fs_alias"
        return TABLEINFO_BLOCK + "\n" + text, "inserted_TableInfo_at_top"

    return text, "review_no_safe_replacement_found"


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-089L DDICT kTables shape compile repair")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD089L-ddict-ktables-shape-compile-repair-v0")
    ap.add_argument("--dd089k-dir", default="docs/datadict/reports/DD089K-ddict-catalog-paths-ktables-compile-repair-apply-v0")
    ap.add_argument("--build-proof", default="docs/datadict/runlog/DD-089K_DDICT_CATALOG_PATHS_KTABLES_BUILD_PROOF.md")
    ap.add_argument("--apply-repair", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd089k_dir = (repo / args.dd089k_dir).resolve()
    dd089k_manifest = read_json(dd089k_dir / "dd089k_ddict_catalog_paths_ktables_compile_repair_manifest.json")
    build_proof = (repo / args.build_proof).resolve()
    build_text = read_text(build_proof)
    target = repo / TARGET_SOURCE
    before = read_text(target)

    review_rows: List[Dict[str, Any]] = []
    dd089k_green = int(dd089k_manifest.get("status") == EXPECTED_DD089K_STATUS)
    if not dd089k_green:
        review_rows.append({"issue": "DD089K_NOT_READY", "detail": dd089k_manifest.get("status", "")})
    if not build_proof.exists():
        review_rows.append({"issue": "BUILD_PROOF_MISSING", "detail": rel(repo, build_proof)})
    if "left of '.name' must have class/struct/union" not in build_text and "const char *const" not in build_text:
        review_rows.append({"issue": "BUILD_PROOF_DOES_NOT_SHOW_KTABLES_SHAPE_FAILURE", "detail": rel(repo, build_proof)})
    if not target.exists():
        review_rows.append({"issue": "TARGET_SOURCE_MISSING", "detail": TARGET_SOURCE})
    if target.exists() and not has_char_pointer_shape(before) and not has_tableinfo_shape(before):
        review_rows.append({"issue": "TARGET_KTABLES_SHAPE_NOT_RECOGNIZED", "detail": TARGET_SOURCE})

    after, action = repair_ktables_shape(before)
    changed = int(after != before)

    generated = out / "generated_compile_repair"
    candidate_path = generated / TARGET_SOURCE
    diff_path = generated / (TARGET_SOURCE + ".diff")
    write_text(candidate_path, after)
    write_text(diff_path, diff_text(before, after, TARGET_SOURCE))

    applied = 0
    backup_path = ""
    review_before_apply = len(review_rows)
    if args.apply_repair and changed and review_before_apply == 0:
        backup_dir = (repo / args.backup_root) / f"{args.run_id}_{stamp()}"
        backup_target = backup_dir / TARGET_SOURCE
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup_target)
        backup_path = str(backup_target)
        target.write_text(after, encoding="utf-8")
        applied = 1

    protected_rows: List[Dict[str, Any]] = []
    protected_mutations = 0
    for rel_path in PROTECTED_UNTOUCHED:
        path = repo / rel_path
        protected_rows.append({
            "protected_path": rel_path,
            "exists": int(path.exists()),
            "hash": sha256(path),
            "mutated_by_dd089l": 0,
        })

    patch_rows = [{
        "target": TARGET_SOURCE,
        "exists": int(target.exists()),
        "action": action,
        "had_const_char_shape_before": int(has_char_pointer_shape(before)),
        "had_tableinfo_shape_before": int(has_tableinfo_shape(before)),
        "has_tableinfo_shape_candidate": int(has_tableinfo_shape(after)),
        "changed_candidate": changed,
        "candidate_path": str(candidate_path),
        "diff_path": str(diff_path),
        "apply_requested": int(args.apply_repair),
        "applied": applied,
        "backup_path": backup_path,
        "hash_after": sha256(target),
    }]

    gate_rows = [
        {"gate": "dd089k_repair_applied", "expected": EXPECTED_DD089K_STATUS, "observed": dd089k_manifest.get("status", ""), "pass": dd089k_green},
        {"gate": "build_proof_exists", "expected": 1, "observed": int(build_proof.exists()), "pass": int(build_proof.exists())},
        {"gate": "build_proof_shows_ktables_shape_failure", "expected": 1, "observed": int("left of '.name' must have class/struct/union" in build_text or "const char *const" in build_text), "pass": int("left of '.name' must have class/struct/union" in build_text or "const char *const" in build_text)},
        {"gate": "target_source_exists", "expected": 1, "observed": int(target.exists()), "pass": int(target.exists())},
        {"gate": "repair_candidate_generated", "expected": 1, "observed": int(candidate_path.exists()), "pass": int(candidate_path.exists())},
        {"gate": "candidate_has_tableinfo_shape", "expected": 1, "observed": int(has_tableinfo_shape(after)), "pass": int(has_tableinfo_shape(after))},
        {"gate": "repair_applied_when_requested", "expected": int(args.apply_repair), "observed": int(applied or not changed), "pass": int((not args.apply_repair) or applied or not changed)},
        {"gate": "protected_files_unmutated", "expected": 0, "observed": protected_mutations, "pass": int(protected_mutations == 0)},
    ]

    failures = sum(1 for row in gate_rows if int(row["pass"]) != 1)
    if args.apply_repair and failures == 0:
        status = "DDICT_KTABLES_SHAPE_REPAIR_APPLIED_BUILD_REQUIRED"
    elif failures == 0:
        status = "DDICT_KTABLES_SHAPE_REPAIR_READY"
    else:
        status = "DDICT_KTABLES_SHAPE_REPAIR_REVIEW"

    boundary_rows = [
        {"boundary": "ktables_shape_compile_repair", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "catalog_paths_source_modified", "observed": applied, "required": int(args.apply_repair), "pass": int((not args.apply_repair) or applied or not changed)},
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
            "next_id": "BUILD",
            "title": "Rebuild dottalkpp after DD-089L repair",
            "allowed_scope": "cmake --build build --config Release --target dottalkpp",
        },
        {
            "next_id": "DD089M",
            "title": "next compile repair if needed",
            "allowed_scope": "only if new compile errors appear after DD-089L",
        },
        {
            "next_id": "DD089I",
            "title": "refactor parity closure",
            "allowed_scope": "only after build is green and runtime smoke transcript is captured",
        },
    ]

    write_csv(out / "dd089l_compile_repair_patch_ledger.csv", patch_rows, ["target", "exists", "action", "had_const_char_shape_before", "had_tableinfo_shape_before", "has_tableinfo_shape_candidate", "changed_candidate", "candidate_path", "diff_path", "apply_requested", "applied", "backup_path", "hash_after"])
    write_csv(out / "dd089l_protected_file_ledger.csv", protected_rows, ["protected_path", "exists", "hash", "mutated_by_dd089l"])
    write_csv(out / "dd089l_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd089l_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd089l_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd089l_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-089L DDICT kTables Shape Compile Repair

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-089L repairs the next compile failure after DD-089K.

DD-089K correctly restored `kTables`, but used `const char* kTables[]`. The extracted code still expects
each table entry to expose `.name`:

```text
std::string(t.name)
```

So DD-089L restores the earlier table-info shape:

```text
struct TableInfo {{ const char* name; }};
constexpr TableInfo kTables[] = {{ ... }};
```

## Inputs

- DD-089K status: `{dd089k_manifest.get('status', '')}`
- Build proof: `{rel(repo, build_proof)}`
- Target source: `{TARGET_SOURCE}`

## Result

- Apply requested: **{int(args.apply_repair)}**
- Candidate changed: **{changed}**
- Action: `{action}`
- Applied: **{applied}**
- Backup path: `{backup_path}`

## Boundary

DD-089L is compile repair only. It may edit only `src/datadict/ddict_catalog_paths.cpp`.
It does not patch `cmd_ddict.cpp`, edit CMake/build files, command registration, active catalog DBFs,
CDX/LMDB, HELP/META/CMDHELPCHK, generated catalog content, or manual rows.
"""
    write_text(out / "DD089L_DDICT_KTABLES_SHAPE_COMPILE_REPAIR_REPORT.md", report)

    manifest = {
        "contract": "dd089l_ddict_ktables_shape_compile_repair_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd089k_status": dd089k_manifest.get("status", ""),
        "build_proof": rel(repo, build_proof),
        "target": TARGET_SOURCE,
        "apply_repair": int(args.apply_repair),
        "changed_candidate": changed,
        "applied": applied,
        "backup_path": backup_path,
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
        "next_recommended_action": "Rebuild dottalkpp. If build is green, run DDICT smoke and DD-089I closure; otherwise paste the next compile errors for DD-089M.",
    }
    write_json(out / "dd089l_ddict_ktables_shape_compile_repair_manifest.json", manifest)

    print(f"DD-089L kTables shape compile repair manifest: {out / 'dd089l_ddict_ktables_shape_compile_repair_manifest.json'}")
    print(f"status: {status}; changed_candidate: {changed}; applied: {applied}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
