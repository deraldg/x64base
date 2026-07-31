#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import difflib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple


SHARED_HEADER_MARKER = "// DD-050 shared x64 memo field helper"
IMPORT_LOCAL_BEGIN = "// DD-048 IMPORT x64 memo assignment repair"
IMPORT_LOCAL_END_ANCHOR = "static void print_import_usage()"
IMPORT_CALL_NEW = "dottalk::cli::memo_field_store::store_user_value"


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


def unified_diff(before: str, after: str, before_name: str, after_name: str) -> str:
    return "".join(difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=before_name,
        tofile=after_name,
    ))


def shared_header_text() -> str:
    return """#pragma once

// DD-050 shared x64 memo field helper
//
// Shared CLI helper for storing user text into x64 M fields.
// This centralizes the memo object-id conversion that REPLACE already proved
// and DD-048 temporarily duplicated inside IMPORT.
//
// This header is inline-only to avoid CMake/source-list changes in the cleanup pass.

#include <cstdint>
#include <string>
#include <string_view>

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "memo/memo_auto.hpp"
#include "memo/memostore.hpp"

namespace dottalk::cli::memo_field_store {

inline bool is_x64_memo_field(const DbArea& area, int field1)
{
    if (field1 < 1 || field1 > area.fieldCount()) return false;
    if (area.versionByte() != xbase::DBF_VERSION_64) return false;

    const auto& f = area.fields()[static_cast<std::size_t>(field1 - 1)];
    return (f.type == 'M' || f.type == 'm') &&
           f.length == xbase::X64_MEMO_FIELD_LEN;
}

inline std::uint64_t parse_u64_or_zero(const std::string& s)
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

inline dottalk::memo::MemoStore* memo_store_for_area(DbArea& area) noexcept
{
    auto* backend = cli_memo::memo_backend_for(area);
    if (!backend) return nullptr;
    return dynamic_cast<dottalk::memo::MemoStore*>(backend);
}

inline bool build_x64_memo_stored_value(DbArea& area,
                                         int field1,
                                         const std::string& user_value,
                                         std::string& stored_value_out,
                                         std::string& err_out)
{
    stored_value_out.clear();
    err_out.clear();

    if (!is_x64_memo_field(area, field1)) {
        stored_value_out = user_value;
        return true;
    }

    auto* store = memo_store_for_area(area);
    if (!store) {
        err_out = "memo backend not attached";
        return false;
    }

    std::uint64_t old_object_id = 0;
    try {
        old_object_id = parse_u64_or_zero(area.get(field1));
    } catch (...) {
        old_object_id = 0;
    }

    if (user_value.empty()) {
        stored_value_out.clear();
        return true;
    }

    std::uint64_t new_object_id = 0;
    if (!store->update_text_id(old_object_id,
                               std::string_view(user_value),
                               new_object_id,
                               nullptr))
    {
        err_out = "memo store update failed";
        return false;
    }

    stored_value_out = (new_object_id == 0) ? std::string() : std::to_string(new_object_id);
    return true;
}

inline bool store_user_value(DbArea& area,
                             int field1,
                             const std::string& user_value,
                             std::string& err_out)
{
    std::string stored_value;
    if (!build_x64_memo_stored_value(area, field1, user_value, stored_value, err_out)) {
        return false;
    }

    area.set(field1, stored_value);
    return true;
}

} // namespace dottalk::cli::memo_field_store
"""


def ensure_include(src: str, anchor: str, include_line: str) -> str:
    if include_line in src:
        return src
    if anchor not in src:
        raise RuntimeError(f"include anchor not found: {anchor.strip()}")
    return src.replace(anchor, anchor + include_line, 1)


def remove_dd048_import_local_helper(src: str) -> Tuple[str, bool]:
    if IMPORT_LOCAL_BEGIN not in src:
        return src, False
    start = src.index(IMPORT_LOCAL_BEGIN)
    end = src.find(IMPORT_LOCAL_END_ANCHOR, start)
    if end < 0:
        raise RuntimeError("could not find print_import_usage after DD-048 helper")
    return src[:start] + src[end:], True


def patch_import(src: str) -> Tuple[str, List[Dict[str, Any]]]:
    checks: List[Dict[str, Any]] = []
    before = src

    src = ensure_include(src, '#include "xbase.hpp"\n', '#include "cli/memo_field_store.hpp"\n')
    checks.append({"check": "import_shared_header_include_present", "observed": 1, "pass": 1})

    src, removed = remove_dd048_import_local_helper(src)
    checks.append({"check": "import_dd048_local_helper_removed", "observed": int(removed), "pass": 1})

    old = """                if (!import_store_csv_value(a, fi, cols[c], import_err)) {
                    std::cout << "IMPORT: " << import_err
                              << " at rec " << a.recno()
                              << ", column " << (c + 1) << ".\\n";
                    break;
                }
"""
    new = """                if (!dottalk::cli::memo_field_store::store_user_value(a, fi, cols[c], import_err)) {
                    std::cout << "IMPORT: " << import_err
                              << " at rec " << a.recno()
                              << ", column " << (c + 1) << ".\\n";
                    break;
                }
"""
    if old in src:
        src = src.replace(old, new, 1)
        checks.append({"check": "import_call_repointed_to_shared_helper", "observed": 1, "pass": 1})
    elif IMPORT_CALL_NEW in src:
        checks.append({"check": "import_call_already_shared_helper", "observed": 1, "pass": 1})
    else:
        raise RuntimeError("could not find DD-048 import_store_csv_value call to repoint")

    checks.append({"check": "import_changed", "observed": int(src != before), "pass": 1})
    return src, checks


def replace_static_helper_block(src: str) -> Tuple[str, bool]:
    marker = "build_x64_memo_stored_value"
    pos = src.find(marker)
    if pos < 0:
        return src, False

    start = src.rfind("\nstatic ", 0, pos)
    if start < 0:
        start = src.rfind("\nbool ", 0, pos)
    if start < 0:
        return src, False
    start += 1

    brace = src.find("{", pos)
    if brace < 0:
        return src, False

    depth = 0
    end = -1
    for i in range(brace, len(src)):
        ch = src[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end < 0:
        return src, False

    while end < len(src) and src[end] in " \t\r\n":
        end += 1

    return src[:start] + src[end:], True


def patch_replace(src: str) -> Tuple[str, List[Dict[str, Any]], str]:
    checks: List[Dict[str, Any]] = []
    before = src
    review_reason = ""

    src = ensure_include(src, '#include "xbase.hpp"\n', '#include "cli/memo_field_store.hpp"\n')
    checks.append({"check": "replace_shared_header_include_present", "observed": 1, "pass": 1})

    if "build_x64_memo_stored_value(" not in src:
        checks.append({"check": "replace_private_helper_call_found", "observed": 0, "pass": 0})
        return before, checks, "cmd_replace.cpp private helper call not found"

    src = src.replace("build_x64_memo_stored_value(", "dottalk::cli::memo_field_store::build_x64_memo_stored_value(")
    checks.append({"check": "replace_calls_repointed_to_shared_helper", "observed": 1, "pass": 1})

    src, removed = replace_static_helper_block(src)
    checks.append({"check": "replace_private_helper_removed", "observed": int(removed), "pass": int(removed)})
    if not removed:
        review_reason = "Could not safely remove cmd_replace.cpp private helper definition; call was repointed only in candidate."

    checks.append({"check": "replace_changed", "observed": int(src != before), "pass": 1})
    return src, checks, review_reason


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-050 guarded shared memo helper cleanup")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD050-shared-memo-helper-cleanup-v0")
    ap.add_argument("--cmd-import", default="src/cli/cmd_import.cpp")
    ap.add_argument("--cmd-replace", default="src/cli/cmd_replace.cpp")
    ap.add_argument("--shared-header", default="include/cli/memo_field_store.hpp")
    ap.add_argument("--apply-cleanup", action="store_true", help="Required to write source cleanup")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    import_path = (repo / args.cmd_import).resolve()
    replace_path = (repo / args.cmd_replace).resolve()
    header_path = (repo / args.shared_header).resolve()

    for p, label in [(import_path, "cmd_import"), (replace_path, "cmd_replace")]:
        if not p.exists():
            raise SystemExit(f"{label} not found: {p}")

    import_src = import_path.read_text(encoding="utf-8", errors="replace")
    replace_src = replace_path.read_text(encoding="utf-8", errors="replace")

    checks: List[Dict[str, Any]] = []
    review_reasons: List[str] = []

    try:
        import_new, import_checks = patch_import(import_src)
        checks.extend({"file": args.cmd_import, **c} for c in import_checks)
    except Exception as exc:
        import_new = import_src
        review_reasons.append(f"cmd_import cleanup failed: {type(exc).__name__}: {exc}")
        checks.append({"file": args.cmd_import, "check": "import_cleanup_exception", "observed": str(exc), "pass": 0})

    try:
        replace_new, replace_checks, rr = patch_replace(replace_src)
        checks.extend({"file": args.cmd_replace, **c} for c in replace_checks)
        if rr:
            review_reasons.append(rr)
    except Exception as exc:
        replace_new = replace_src
        review_reasons.append(f"cmd_replace cleanup failed: {type(exc).__name__}: {exc}")
        checks.append({"file": args.cmd_replace, "check": "replace_cleanup_exception", "observed": str(exc), "pass": 0})

    header_new = shared_header_text()
    header_old = header_path.read_text(encoding="utf-8", errors="replace") if header_path.exists() else ""

    candidate_dir = out / "candidate"
    backup_dir = out / "backup"
    diff_dir = out / "diff"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)
    diff_dir.mkdir(parents=True, exist_ok=True)

    (backup_dir / "cmd_import.cpp.before_dd050").write_text(import_src, encoding="utf-8")
    (candidate_dir / "cmd_import.cpp.after_dd050").write_text(import_new, encoding="utf-8")
    (diff_dir / "cmd_import_dd050.diff").write_text(
        unified_diff(import_src, import_new, str(import_path) + ".before_dd050", str(import_path) + ".after_dd050"),
        encoding="utf-8",
    )

    (backup_dir / "cmd_replace.cpp.before_dd050").write_text(replace_src, encoding="utf-8")
    (candidate_dir / "cmd_replace.cpp.after_dd050").write_text(replace_new, encoding="utf-8")
    (diff_dir / "cmd_replace_dd050.diff").write_text(
        unified_diff(replace_src, replace_new, str(replace_path) + ".before_dd050", str(replace_path) + ".after_dd050"),
        encoding="utf-8",
    )

    (backup_dir / "memo_field_store.hpp.before_dd050").write_text(header_old, encoding="utf-8")
    (candidate_dir / "memo_field_store.hpp.after_dd050").write_text(header_new, encoding="utf-8")
    (diff_dir / "memo_field_store_hpp_dd050.diff").write_text(
        unified_diff(header_old, header_new, str(header_path) + ".before_dd050", str(header_path) + ".after_dd050"),
        encoding="utf-8",
    )

    source_modified = 0
    files_written: List[str] = []
    cleanup_review = bool(review_reasons)

    if args.apply_cleanup and not cleanup_review:
        shutil.copy2(import_path, import_path.with_suffix(import_path.suffix + ".dd050.bak"))
        shutil.copy2(replace_path, replace_path.with_suffix(replace_path.suffix + ".dd050.bak"))
        if header_path.exists():
            shutil.copy2(header_path, header_path.with_suffix(header_path.suffix + ".dd050.bak"))
        header_path.parent.mkdir(parents=True, exist_ok=True)

        if import_new != import_src:
            import_path.write_text(import_new, encoding="utf-8")
            files_written.append(args.cmd_import)
        if replace_new != replace_src:
            replace_path.write_text(replace_new, encoding="utf-8")
            files_written.append(args.cmd_replace)
        if header_new != header_old:
            header_path.write_text(header_new, encoding="utf-8")
            files_written.append(args.shared_header)
        source_modified = int(bool(files_written))

    if args.apply_cleanup and cleanup_review:
        status = "SHARED_MEMO_HELPER_CLEANUP_BLOCKED_REVIEW"
    elif args.apply_cleanup and source_modified:
        status = "SHARED_MEMO_HELPER_CLEANUP_APPLIED"
    elif cleanup_review:
        status = "SHARED_MEMO_HELPER_CLEANUP_CANDIDATE_REVIEW"
    else:
        status = "SHARED_MEMO_HELPER_CLEANUP_CANDIDATE_READY"

    boundary_rows = [
        {"boundary": "cleanup_requires_apply_flag", "observed": int(args.apply_cleanup), "required": "1 for source mutation", "pass": 1},
        {"boundary": "source_files_modified", "observed": source_modified, "required": int(args.apply_cleanup and not cleanup_review), "pass": 1},
        {"boundary": "build_run_by_dd050", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "datadict_sandbox_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "probe_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_build", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd050_cleanup_checks.csv", checks, ["file", "check", "observed", "pass"])
    write_csv(out / "dd050_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_json(out / "dd050_review_reasons.json", {"review_reasons": review_reasons})

    manifest = {
        "contract": "dd050_shared_memo_helper_cleanup_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "apply_cleanup": int(args.apply_cleanup),
        "source_modified": source_modified,
        "files_written": files_written,
        "review_reasons": review_reasons,
        "candidate_dir": str(candidate_dir),
        "diff_dir": str(diff_dir),
        "build_run": 0,
        "active_catalog_mutation": 0,
        "datadict_sandbox_mutation": 0,
        "probe_catalog_mutation": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "lmdb_build": 0,
        "next_recommended_action": "If cleanup is applied, build and rerun DD-046/DD-049 probe evidence.",
    }
    write_json(out / "dd050_shared_memo_helper_cleanup_manifest.json", manifest)

    report = f"""# DD-050 Shared Memo Helper Cleanup

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-050 centralizes the x64 memo field storage helper so IMPORT and REPLACE do not
carry separate memo conversion logic.

## Candidate files

```text
{args.shared_header}
{args.cmd_import}
{args.cmd_replace}
```

## Review reasons

```text
{chr(10).join(review_reasons) if review_reasons else 'none'}
```

## Boundary

DD-050 does not run a build, mutate active/sandbox/probe catalog data, build LMDB,
or mutate HELP/META/CMDHELPCHK.

## Next proof

If applied, build and rerun:

```text
DD-046 pydottalk/readback
DD-049 x64 header-aware evidence closure
```
"""
    (out / "DD050_SHARED_MEMO_HELPER_CLEANUP_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-050 shared memo helper cleanup manifest: {out / 'dd050_shared_memo_helper_cleanup_manifest.json'}")
    print(f"status: {status}; source_modified: {source_modified}; review_reasons: {len(review_reasons)}")
    return 2 if (args.fail_on_review and (cleanup_review or "REVIEW" in status)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
