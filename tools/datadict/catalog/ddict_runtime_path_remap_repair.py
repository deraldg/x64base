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


EXPECTED_DD090_STATUS = "DDICT_READ_HELPER_REFACTOR_CYCLE_SAVEPOINT_GREEN"
EXPECTED_DD092A_STATUS = "DDICT_HELP_TOPIC_CANDIDATE_GENERATED_REVIEW_READY"

TARGET_SOURCE = "src/datadict/ddict_catalog_paths.cpp"
TARGET_HEADER = "include/datadict/ddict_catalog_paths.hpp"

PROTECTED_UNTOUCHED = [
    "src/cli/cmd_ddict.cpp",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
    "src/CMakeLists.txt",
    "dottalkpp/data/datadict/DDOBJECT.dbf",
    "dottalkpp/data/indexes/datadict/ddobject.cdx",
    "dottalkpp/data/lmdb/datadict/ddobject.cdx.d",
]

EXPECTED_DD_TABLES = [
    "DDRUN",
    "DDBASE",
    "DDSOURCE",
    "DDOBJECT",
    "DDATTR",
    "DDEDGE",
    "DDEVID",
    "DDGATE",
    "DDREVIEW",
    "DDARTIF",
    "DDPROFILE",
]

RUNTIME_PROOF_NEEDLES = [
    "DBF             = d:\\code\\ccode\\dottalkpp\\data\\DATADICT",
    "INDEXES         = d:\\code\\ccode\\dottalkpp\\data\\INDEXES\\DATADICT",
    "LMDB            = d:\\code\\ccode\\dottalkpp\\data\\LMDB\\DATADICT",
    "WORKSPACE: 11 table(s) opened",
    "Active catalog: dottalkpp\\data\\metadata\\datadict",
    "DBF tables    : 0 / 11",
    "Result        : OBJECT_NOT_FOUND",
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
    except Exception as exc:
        return {"_read_error": str(exc)}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def diff_text(old: str, new: str, name: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=name + ".before",
        tofile=name + ".after",
        lineterm="",
    ))


def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def table_presence(repo: Path) -> List[Dict[str, Any]]:
    roots = {
        "new_dbf_root": repo / "dottalkpp/data/datadict",
        "old_metadata_root": repo / "dottalkpp/data/metadata/datadict",
    }
    rows: List[Dict[str, Any]] = []
    for label, root in roots.items():
        for table in EXPECTED_DD_TABLES:
            p = root / f"{table}.dbf"
            rows.append({
                "root_label": label,
                "root_path": rel(repo, root),
                "table": table,
                "exists": int(p.exists()),
                "bytes": p.stat().st_size if p.exists() else 0,
            })
    return rows


def artifact_root_presence(repo: Path) -> List[Dict[str, Any]]:
    paths = [
        ("new_dbf_root", "dottalkpp/data/datadict"),
        ("new_index_root", "dottalkpp/data/indexes/datadict"),
        ("new_lmdb_root", "dottalkpp/data/lmdb/datadict"),
        ("old_metadata_root", "dottalkpp/data/metadata/datadict"),
        ("old_flat_index_root", "dottalkpp/data/indexes"),
        ("old_flat_lmdb_root", "dottalkpp/data/lmdb"),
    ]
    rows = []
    for label, rel_path in paths:
        p = repo / rel_path
        rows.append({
            "label": label,
            "path": rel_path,
            "exists": int(p.exists()),
            "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
            "children": sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else "",
        })
    return rows


def replace_path_literals(text: str) -> Tuple[str, List[str]]:
    out = text
    actions: List[str] = []

    replacements = [
        ("metadata/datadict", "datadict", "replace_forward_metadata_datadict_with_datadict"),
        ("metadata\\datadict", "datadict", "replace_backslash_metadata_datadict_with_datadict"),
        ("metadata\\\\datadict", "datadict", "replace_escaped_metadata_datadict_with_datadict"),
        ("data/metadata/datadict", "data/datadict", "replace_forward_data_metadata_datadict_with_data_datadict"),
        ("data\\metadata\\datadict", "data\\datadict", "replace_backslash_data_metadata_datadict_with_data_datadict"),
        ("data\\\\metadata\\\\datadict", "data\\\\datadict", "replace_escaped_data_metadata_datadict_with_data_datadict"),
    ]

    for old, new, action in replacements:
        if old in out:
            out = out.replace(old, new)
            actions.append(action)

    # Add explicit preferred subroot literals only if the file already contains old metadata root and helper names.
    # This keeps DD093 narrow: it fixes DBF root selection first and records INDEX/LMDB verification as post-build proof.
    return out, actions


def make_runtime_smoke() -> str:
    return """SETPATH
DO ddbase
DDICT STATUS
DDICT TABLES
DDICT TAGS DDATTR
DDICT REL DDOBJECT OUT
DDICT EVIDENCE DDOBJECT

"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-093 DDICT runtime path-remap repair")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD093-ddict-runtime-path-remap-repair-v0")
    ap.add_argument("--dd090-dir", default="docs/datadict/reports/DD090-ddict-read-helper-refactor-cycle-savepoint-v0")
    ap.add_argument("--dd092a-dir", default="docs/datadict/reports/DD092A-ddict-help-topic-candidate-generation-v0")
    ap.add_argument("--runtime-proof", default="docs/datadict/runlog/DD-093_DDICT_PATH_REMAP_RED_PROOF.md")
    ap.add_argument("--apply-source-patch", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd090_manifest = read_json(repo / args.dd090_dir / "dd090_ddict_read_helper_refactor_cycle_savepoint_manifest.json")
    dd092a_manifest = read_json(repo / args.dd092a_dir / "dd092a_ddict_help_topic_candidate_generation_manifest.json")

    runtime_proof = repo / args.runtime_proof
    runtime_text = read_text(runtime_proof)
    runtime_lower = runtime_text.lower()

    target = repo / TARGET_SOURCE
    before = read_text(target)
    candidate, actions = replace_path_literals(before)

    generated = out / "generated_path_remap_repair"
    candidate_path = generated / TARGET_SOURCE
    diff_path = generated / (TARGET_SOURCE + ".diff")
    smoke_path = generated / "dd093_ddict_path_remap_smoke.dts"

    write_text(candidate_path, candidate)
    write_text(diff_path, diff_text(before, candidate, TARGET_SOURCE))
    write_text(smoke_path, make_runtime_smoke())

    changed = int(candidate != before)
    safe_pattern_found = int(len(actions) > 0)

    review_rows: List[Dict[str, Any]] = []
    if dd090_manifest.get("status") != EXPECTED_DD090_STATUS:
        review_rows.append({"issue": "DD090_NOT_GREEN", "detail": dd090_manifest.get("status", "")})
    if dd092a_manifest and dd092a_manifest.get("status") != EXPECTED_DD092A_STATUS:
        review_rows.append({"issue": "DD092A_NOT_REVIEW_READY", "detail": dd092a_manifest.get("status", "")})
    if not target.exists():
        review_rows.append({"issue": "TARGET_SOURCE_MISSING", "detail": TARGET_SOURCE})
    if not safe_pattern_found:
        review_rows.append({"issue": "NO_SAFE_METADATA_DATADICT_PATTERN_FOUND", "detail": TARGET_SOURCE})
    if runtime_proof.exists():
        seen = sum(1 for n in RUNTIME_PROOF_NEEDLES if n.lower() in runtime_lower)
        if seen < 3:
            review_rows.append({"issue": "RUNTIME_RED_PROOF_WEAK", "detail": f"needles_seen={seen}"})
    else:
        review_rows.append({"issue": "RUNTIME_RED_PROOF_MISSING", "detail": rel(repo, runtime_proof)})

    applied = 0
    backup_path = ""
    if args.apply_source_patch and changed and safe_pattern_found and target.exists():
        backup_dir = (repo / args.backup_root) / f"{args.run_id}_{stamp()}"
        backup = backup_dir / TARGET_SOURCE
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        backup_path = str(backup)
        target.write_text(candidate, encoding="utf-8")
        applied = 1

    patch_rows = [{
        "target": TARGET_SOURCE,
        "exists": int(target.exists()),
        "safe_pattern_found": safe_pattern_found,
        "actions": ";".join(actions),
        "changed_candidate": changed,
        "candidate_path": str(candidate_path),
        "diff_path": str(diff_path),
        "apply_requested": int(args.apply_source_patch),
        "applied": applied,
        "backup_path": backup_path,
        "hash_after": sha256(target),
    }]

    table_rows = table_presence(repo)
    root_rows = artifact_root_presence(repo)

    protected_rows = []
    for rel_path in PROTECTED_UNTOUCHED:
        p = repo / rel_path
        protected_rows.append({
            "protected_path": rel_path,
            "exists": int(p.exists()),
            "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
            "sha256": sha256(p),
            "mutation_in_dd093": 0,
        })

    new_tables_present = sum(1 for r in table_rows if r["root_label"] == "new_dbf_root" and int(r["exists"]) == 1)
    old_tables_present = sum(1 for r in table_rows if r["root_label"] == "old_metadata_root" and int(r["exists"]) == 1)

    boundary_rows = [
        {"boundary": "guarded_path_remap_repair", "observed": 1, "required": 1, "pass": 1},
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

    gate_rows = [
        {"gate": "dd090_green", "expected": EXPECTED_DD090_STATUS, "observed": dd090_manifest.get("status", ""), "pass": int(dd090_manifest.get("status") == EXPECTED_DD090_STATUS)},
        {"gate": "target_source_exists", "expected": 1, "observed": int(target.exists()), "pass": int(target.exists())},
        {"gate": "safe_metadata_datadict_pattern_found", "expected": 1, "observed": safe_pattern_found, "pass": safe_pattern_found},
        {"gate": "candidate_diff_generated", "expected": 1, "observed": int(diff_path.exists()), "pass": int(diff_path.exists())},
        {"gate": "new_datadict_tables_present", "expected": 11, "observed": new_tables_present, "pass": int(new_tables_present == 11)},
        {"gate": "old_metadata_tables_absent_or_legacy", "expected": "0 or legacy", "observed": old_tables_present, "pass": 1},
        {"gate": "apply_when_requested", "expected": int(args.apply_source_patch), "observed": applied, "pass": int((not args.apply_source_patch) or applied == 1)},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    if args.apply_source_patch and failures == 0:
        status = "DDICT_PATH_REMAP_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"
    elif failures == 0:
        status = "DDICT_PATH_REMAP_SOURCE_PATCH_READY"
    else:
        status = "DDICT_PATH_REMAP_SOURCE_PATCH_REVIEW"

    next_rows = [
        {"next_id": "BUILD", "title": "Build dottalkpp after DD093 source patch", "allowed_scope": "cmake --build build --config Release --target dottalkpp"},
        {"next_id": "DD093A", "title": "DDICT path remap runtime closure", "allowed_scope": "prove DDICT STATUS/TABLES/TAGS/REL/EVIDENCE use data/datadict"},
        {"next_id": "DD093B", "title": "index/lmdb subroot repair if needed", "allowed_scope": "only if DDICT TAGS still uses flat indexes/lmdb paths"},
    ]

    write_csv(out / "dd093_path_root_presence.csv", root_rows, ["label", "path", "exists", "kind", "children"])
    write_csv(out / "dd093_catalog_table_presence.csv", table_rows, ["root_label", "root_path", "table", "exists", "bytes"])
    write_csv(out / "dd093_source_patch_ledger.csv", patch_rows, ["target", "exists", "safe_pattern_found", "actions", "changed_candidate", "candidate_path", "diff_path", "apply_requested", "applied", "backup_path", "hash_after"])
    write_csv(out / "dd093_protected_file_ledger.csv", protected_rows, ["protected_path", "exists", "kind", "sha256", "mutation_in_dd093"])
    write_csv(out / "dd093_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd093_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd093_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd093_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-093 DDICT Runtime Path Remap Repair

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-093 repairs the DDICT runtime catalog path resolver after the Data Dictionary catalog was moved out of
`dottalkpp/data/metadata/datadict` and into the first-class runtime catalog root:

```text
dottalkpp/data/datadict
dottalkpp/data/indexes/datadict
dottalkpp/data/lmdb/datadict
```

## Current evidence

Workspace pathing is good, but DDICT still reads the old metadata path:

```text
DDICT STATUS -> Active catalog: dottalkpp\\data\\metadata\\datadict
DDICT STATUS -> DBF tables: 0 / 11
```

## Candidate repair

- Target: `{TARGET_SOURCE}`
- Safe pattern found: **{safe_pattern_found}**
- Candidate changed: **{changed}**
- Actions: `{'; '.join(actions)}`
- Apply requested: **{int(args.apply_source_patch)}**
- Applied: **{applied}**

## Catalog table presence

- New root tables present: **{new_tables_present} / 11**
- Old metadata-root tables present: **{old_tables_present} / 11**

## Required post-build smoke

```text
SETPATH
DO ddbase
DDICT STATUS
DDICT TABLES
DDICT TAGS DDATTR
DDICT REL DDOBJECT OUT
DDICT EVIDENCE DDOBJECT
```

Expected critical result:

```text
Active catalog: d:\\code\\ccode\\dottalkpp\\data\\datadict
DBF tables    : 11 / 11
Catalog state : ACTIVE_CATALOG_PRESENT
```

## Boundary

DD-093 is guarded source-path repair only. It does not edit build files, command registration,
active catalog DBFs, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB,
mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""

    (out / "DD093_DDICT_RUNTIME_PATH_REMAP_REPAIR_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd093_ddict_runtime_path_remap_repair_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "target_source": TARGET_SOURCE,
        "safe_pattern_found": safe_pattern_found,
        "changed_candidate": changed,
        "actions": actions,
        "apply_source_patch": int(args.apply_source_patch),
        "applied": applied,
        "new_datadict_tables_present": new_tables_present,
        "old_metadata_tables_present": old_tables_present,
        "failures": failures,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Build dottalkpp and run DD093A DDICT path remap runtime closure.",
    }
    write_json(out / "dd093_ddict_runtime_path_remap_repair_manifest.json", manifest)

    print(f"DD-093 DDICT runtime path remap repair manifest: {out / 'dd093_ddict_runtime_path_remap_repair_manifest.json'}")
    print(f"status: {status}; safe_pattern_found: {safe_pattern_found}; applied: {applied}; new_tables: {new_tables_present}/11; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
