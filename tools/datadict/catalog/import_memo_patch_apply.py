#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List
import csv


PATCH_MARKER = "// DD-048 IMPORT x64 memo assignment repair"


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def patch_import_source(src: str) -> tuple[str, List[Dict[str, Any]]]:
    checks: List[Dict[str, Any]] = []

    if PATCH_MARKER in src:
        checks.append({"check": "already_patched_marker", "observed": 1, "pass": 1})
        return src, checks

    include_anchor = "#include <vector>\n"
    include_insert = "#include <cstdint>\n#include <string_view>\n"
    if include_insert not in src:
        if include_anchor not in src:
            raise RuntimeError("Could not find include anchor '#include <vector>'")
        src = src.replace(include_anchor, include_anchor + include_insert, 1)
    checks.append({"check": "standard_includes_inserted", "observed": 1, "pass": 1})

    xbase_anchor = '#include "xbase.hpp"\n'
    extra_includes = '#include "xbase_64.hpp"\n#include "memo/memo_auto.hpp"\n#include "memo/memostore.hpp"\n'
    if extra_includes not in src:
        if xbase_anchor not in src:
            raise RuntimeError('Could not find include anchor #include "xbase.hpp"')
        src = src.replace(xbase_anchor, xbase_anchor + extra_includes, 1)
    checks.append({"check": "memo_includes_inserted", "observed": 1, "pass": 1})

    helper_anchor = "static void print_import_usage()\n"
    helper_block = """
// DD-048 IMPORT x64 memo assignment repair
// Tactical local helper mirroring the proven REPLACE memo conversion path.
// Follow-up cleanup should extract this into a shared CLI helper used by both
// REPLACE and IMPORT.
static bool import_is_x64_memo_field(const DbArea& A, int field1)
{
    if (field1 < 1 || field1 > A.fieldCount()) return false;
    if (A.versionByte() != xbase::DBF_VERSION_64) return false;

    const auto& f = A.fields()[static_cast<std::size_t>(field1 - 1)];
    return (f.type == 'M' || f.type == 'm') &&
           f.length == xbase::X64_MEMO_FIELD_LEN;
}

static std::uint64_t import_parse_u64_or_zero(const std::string& s)
{
    if (s.empty()) return 0;
    try {
        std::size_t used = 0;
        const unsigned long long v = std::stoull(s, &used, 10);
        if (used != s.size()) return 0;
        return static_cast<std::uint64_t>(v);
    } catch (...) {
        return 0;
    }
}

static dottalk::memo::MemoStore* import_memo_store_for_area(DbArea& A) noexcept
{
    auto* backend = cli_memo::memo_backend_for(A);
    if (!backend) return nullptr;
    return dynamic_cast<dottalk::memo::MemoStore*>(backend);
}

static bool import_build_x64_memo_stored_value(DbArea& A,
                                               int field1,
                                               const std::string& csv_value,
                                               std::string& stored_value_out,
                                               std::string& err_out)
{
    stored_value_out.clear();
    err_out.clear();

    if (!import_is_x64_memo_field(A, field1)) {
        stored_value_out = csv_value;
        return true;
    }

    auto* store = import_memo_store_for_area(A);
    if (!store) {
        err_out = "memo backend not attached";
        return false;
    }

    std::uint64_t old_object_id = 0;
    try {
        old_object_id = import_parse_u64_or_zero(A.get(field1));
    } catch (...) {
        old_object_id = 0;
    }

    if (csv_value.empty()) {
        stored_value_out.clear();
        return true;
    }

    std::uint64_t new_object_id = 0;
    if (!store->update_text_id(old_object_id,
                               std::string_view(csv_value),
                               new_object_id,
                               nullptr))
    {
        err_out = "memo store update failed";
        return false;
    }

    stored_value_out = (new_object_id == 0) ? std::string() : std::to_string(new_object_id);
    return true;
}

static bool import_store_csv_value(DbArea& A,
                                   int field1,
                                   const std::string& csv_value,
                                   std::string& err_out)
{
    std::string stored_value;
    if (!import_build_x64_memo_stored_value(A, field1, csv_value, stored_value, err_out)) {
        return false;
    }

    A.set(field1, stored_value);
    return true;
}

"""
    if helper_anchor not in src:
        raise RuntimeError("Could not find helper anchor 'static void print_import_usage()'")
    src = src.replace(helper_anchor, helper_block + helper_anchor, 1)
    checks.append({"check": "memo_helper_block_inserted", "observed": 1, "pass": 1})

    old = "            if (fi > 0) a.set(fi, cols[c]);\n"
    new = """            if (fi > 0) {
                std::string import_err;
                if (!import_store_csv_value(a, fi, cols[c], import_err)) {
                    std::cout << "IMPORT: " << import_err
                              << " at rec " << a.recno()
                              << ", column " << (c + 1) << ".\\n";
                    break;
                }
            }
"""
    if old not in src:
        raise RuntimeError("Could not find plain IMPORT assignment line")
    src = src.replace(old, new, 1)
    checks.append({"check": "plain_set_replaced", "observed": 1, "pass": 1})

    return src, checks


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-048 guarded IMPORT x64 memo assignment patch")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD048-import-memo-field-assignment-repair-execution-v0")
    ap.add_argument("--cmd-import", default="src/cli/cmd_import.cpp")
    ap.add_argument("--apply-source-patch", action="store_true", help="Required to modify cmd_import.cpp")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    src_path = (repo / args.cmd_import).resolve()
    out.mkdir(parents=True, exist_ok=True)

    if not src_path.exists():
        raise SystemExit(f"cmd_import not found: {src_path}")

    original = src_path.read_text(encoding="utf-8", errors="replace")
    patched, checks = patch_import_source(original)

    backup_path = out / "backup" / "cmd_import.cpp.before_dd048"
    candidate_path = out / "candidate" / "cmd_import.cpp.after_dd048"
    diff_path = out / "dd048_cmd_import_patch.diff"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(original, encoding="utf-8")
    candidate_path.write_text(patched, encoding="utf-8")

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        patched.splitlines(keepends=True),
        fromfile=str(src_path) + ".before_dd048",
        tofile=str(src_path) + ".after_dd048",
    )
    diff_path.write_text("".join(diff), encoding="utf-8")

    source_modified = 0
    if args.apply_source_patch:
        if original != patched:
            shutil.copy2(src_path, src_path.with_suffix(src_path.suffix + ".dd048.bak"))
            src_path.write_text(patched, encoding="utf-8")
            source_modified = 1

    status = "IMPORT_MEMO_FIELD_PATCH_APPLIED" if source_modified else "IMPORT_MEMO_FIELD_PATCH_NOT_APPLIED"

    boundary_rows = [
        {"boundary": "source_patch_requires_flag", "observed": int(args.apply_source_patch), "required": "1 for source mutation", "pass": 1},
        {"boundary": "cmd_import_modified", "observed": source_modified, "required": int(args.apply_source_patch), "pass": 1},
        {"boundary": "cmd_replace_modified", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_run_by_dd048", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "datadict_sandbox_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "probe_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_build", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd048_source_patch_checks.csv", checks, ["check", "observed", "pass"])
    write_csv(out / "dd048_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    manifest = {
        "contract": "dd048_import_memo_field_assignment_repair_execution_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "cmd_import": str(src_path),
        "profiles": args.profile,
        "apply_source_patch": int(args.apply_source_patch),
        "source_modified": source_modified,
        "backup_path": str(backup_path),
        "repo_backup_path": str(src_path.with_suffix(src_path.suffix + ".dd048.bak")) if args.apply_source_patch else "",
        "candidate_path": str(candidate_path),
        "diff_path": str(diff_path),
        "build_run": 0,
        "active_catalog_mutation": 0,
        "datadict_sandbox_mutation": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "lmdb_build": 0,
        "next_recommended_action": "Build, then rerun DD-046 CREATE X64/IMPORT/memo probe.",
    }
    write_json(out / "dd048_import_memo_patch_manifest.json", manifest)

    report = f"""# DD-048 IMPORT Memo Field Assignment Repair Execution

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Patch

DD-048 patches only:

```text
{args.cmd_import}
```

It adds a narrow IMPORT-side x64 memo assignment helper and replaces the plain CSV assignment:

```text
a.set(fi, cols[c])
```

with memo-aware assignment for x64 M fields.

## Files

Candidate patched source:

```text
{candidate_path}
```

Unified diff:

```text
{diff_path}
```

Backup:

```text
{backup_path}
```

## Boundary

DD-048 does not run a build, does not mutate active/sandbox/probe catalog data,
does not mutate HELP/META/CMDHELPCHK, does not create CDX, and does not build LMDB.

## Next proof

Build, then rerun the DD-046 probe:

```text
setpath dbf metadata\\datadict_create_probe
create x64 ddprobe (probeid C(20), title C(80), notes M)
import D:\\code\\ccode\\dottalkpp\\data\\metadata\\datadict_create_probe\\ddprobe_import.csv
count
goto 1
tup
goto 2
tup
```

Expected: NOTES memo text should be imported, not blank.
"""
    (out / "DD048_IMPORT_MEMO_FIELD_ASSIGNMENT_REPAIR_EXECUTION_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-048 import memo patch manifest: {out / 'dd048_import_memo_patch_manifest.json'}")
    print(f"status: {status}; source_modified: {source_modified}; build_run: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
