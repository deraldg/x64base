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

EXPECTED_DD069_STATUS = "DDICT_READ_SURFACE_IMPLEMENTATION_PLAN_READY"
DDICT_CPP = '#include "cli/cmd_ddict.hpp"\n\n#include <algorithm>\n#include <array>\n#include <cctype>\n#include <cstdint>\n#include <filesystem>\n#include <iomanip>\n#include <iostream>\n#include <sstream>\n#include <string>\n#include <vector>\n\nnamespace {\n\nnamespace fs = std::filesystem;\n\nstruct TableInfo {\n    const char* name;\n};\n\nconstexpr std::array<TableInfo, 11> kTables{{\n    TableInfo{"DDRUN"},\n    TableInfo{"DDBASE"},\n    TableInfo{"DDSOURCE"},\n    TableInfo{"DDOBJECT"},\n    TableInfo{"DDATTR"},\n    TableInfo{"DDEDGE"},\n    TableInfo{"DDEVID"},\n    TableInfo{"DDGATE"},\n    TableInfo{"DDREVIEW"},\n    TableInfo{"DDARTIF"},\n    TableInfo{"DDPROFILE"},\n}};\n\nstd::string trim_copy(std::string s) {\n    auto not_space = [](unsigned char ch) { return !std::isspace(ch); };\n    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));\n    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());\n    return s;\n}\n\nstd::string upper_copy(std::string s) {\n    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) {\n        return static_cast<char>(std::toupper(ch));\n    });\n    return s;\n}\n\nbool exists_quiet(const fs::path& p) {\n    std::error_code ec;\n    return fs::exists(p, ec);\n}\n\nstd::uintmax_t size_quiet(const fs::path& p) {\n    std::error_code ec;\n    if (!fs::exists(p, ec) || !fs::is_regular_file(p, ec)) {\n        return 0;\n    }\n    auto n = fs::file_size(p, ec);\n    return ec ? 0 : n;\n}\n\nfs::path normalize_quiet(const fs::path& p) {\n    std::error_code ec;\n    auto c = fs::weakly_canonical(p, ec);\n    return ec ? p : c;\n}\n\nstd::vector<fs::path> catalog_candidates() {\n    std::vector<fs::path> roots;\n    std::error_code ec;\n    fs::path cwd = fs::current_path(ec);\n    if (ec) {\n        cwd = fs::path(".");\n    }\n\n    roots.push_back(cwd);\n    roots.push_back(cwd / "..");\n    roots.push_back(cwd / "../..");\n    roots.push_back(cwd / "../../..");\n\n    std::vector<fs::path> candidates;\n    for (const auto& root : roots) {\n        candidates.push_back(root / "data" / "metadata" / "datadict");\n        candidates.push_back(root / "dottalkpp" / "data" / "metadata" / "datadict");\n    }\n    candidates.push_back(fs::path("data") / "metadata" / "datadict");\n    candidates.push_back(fs::path("dottalkpp") / "data" / "metadata" / "datadict");\n    return candidates;\n}\n\nfs::path find_catalog_dir() {\n    for (const auto& c : catalog_candidates()) {\n        if (exists_quiet(c)) {\n            return normalize_quiet(c);\n        }\n    }\n    return normalize_quiet(fs::path("dottalkpp") / "data" / "metadata" / "datadict");\n}\n\nstruct CatalogStats {\n    fs::path dir;\n    int dbf_present = 0;\n    int dtx_present = 0;\n    std::uintmax_t total_dbf_bytes = 0;\n};\n\nCatalogStats collect_stats() {\n    CatalogStats stats;\n    stats.dir = find_catalog_dir();\n    for (const auto& t : kTables) {\n        fs::path dbf = stats.dir / (std::string(t.name) + ".dbf");\n        fs::path dtx = stats.dir / (std::string(t.name) + ".dtx");\n        if (exists_quiet(dbf)) {\n            ++stats.dbf_present;\n            stats.total_dbf_bytes += size_quiet(dbf);\n        }\n        if (exists_quiet(dtx)) {\n            ++stats.dtx_present;\n        }\n    }\n    return stats;\n}\n\nvoid print_ddict_usage() {\n    std::cout\n        << "Usage:\\n"\n        << "  DDICT HELP\\n"\n        << "  DDICT STATUS\\n"\n        << "  DDICT TABLES\\n"\n        << "  DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]\\n"\n        << "  DDICT FIELDS <table>\\n"\n        << "  DDICT TAGS <table>\\n"\n        << "  DDICT REL <object-id-or-name> [IN|OUT|BOTH]\\n"\n        << "  DDICT EVIDENCE <object-id-or-name>\\n"\n        << "Notes:\\n"\n        << "  DDICT is read-only over the active Data Dictionary catalog.\\n";\n}\n\nvoid print_pending(const std::string& sub) {\n    std::cout\n        << "DDICT " << sub\n        << " is accepted by contract but runtime read implementation is pending.\\n";\n}\n\nvoid print_status() {\n    CatalogStats stats = collect_stats();\n    std::cout\n        << "DDICT STATUS\\n"\n        << "  Active catalog: " << stats.dir.string() << "\\n"\n        << "  Read mode     : READ-ONLY\\n"\n        << "  DBF tables    : " << stats.dbf_present << " / " << kTables.size() << "\\n"\n        << "  DTX sidecars  : " << stats.dtx_present << " / " << kTables.size() << "\\n"\n        << "  DBF bytes     : " << stats.total_dbf_bytes << "\\n";\n    if (stats.dbf_present == static_cast<int>(kTables.size())) {\n        std::cout << "  Catalog state : ACTIVE_CATALOG_PRESENT\\n";\n    } else {\n        std::cout << "  Catalog state : ACTIVE_CATALOG_REVIEW\\n";\n    }\n}\n\nvoid print_tables() {\n    fs::path dir = find_catalog_dir();\n    std::cout\n        << "DDICT TABLES\\n"\n        << "  Active catalog: " << dir.string() << "\\n"\n        << "  Read mode     : READ-ONLY\\n"\n        << "  Table       DBF  DTX  DBF_BYTES\\n"\n        << "  ----------  ---  ---  ---------\\n";\n    for (const auto& t : kTables) {\n        fs::path dbf = dir / (std::string(t.name) + ".dbf");\n        fs::path dtx = dir / (std::string(t.name) + ".dtx");\n        bool has_dbf = exists_quiet(dbf);\n        bool has_dtx = exists_quiet(dtx);\n        std::cout\n            << "  " << std::left << std::setw(10) << t.name\n            << "  " << (has_dbf ? "YES" : "NO ")\n            << "  " << (has_dtx ? "YES" : "NO ")\n            << "  " << size_quiet(dbf)\n            << "\\n";\n    }\n}\n\n} // anonymous namespace\n\nvoid cmd_DDICT(xbase::DbArea& area, std::istringstream& args) {\n    (void)area;\n\n    std::string sub;\n    args >> sub;\n    sub = upper_copy(trim_copy(sub));\n\n    if (sub.empty() || sub == "HELP" || sub == "?" || sub == "USAGE") {\n        print_ddict_usage();\n        return;\n    }\n\n    if (sub == "STATUS") {\n        print_status();\n        return;\n    }\n\n    if (sub == "TABLES") {\n        print_tables();\n        return;\n    }\n\n    if (sub == "OBJECTS" || sub == "FIELDS" || sub == "TAGS" ||\n        sub == "REL" || sub == "EVIDENCE") {\n        print_pending(sub);\n        return;\n    }\n\n    std::cout << "DDICT: unknown subcommand \'" << sub << "\'.\\n";\n    print_ddict_usage();\n}\n'

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
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})

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

def main() -> int:
    ap = argparse.ArgumentParser(description="DD-070 guarded DDICT STATUS/TABLES implementation")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD070-guarded-ddict-status-tables-implementation-v0")
    ap.add_argument("--dd069-dir", default="docs/datadict/reports/DD069-ddict-read-surface-implementation-plan-v0")
    ap.add_argument("--source-path", default="src/cli/cmd_ddict.cpp")
    ap.add_argument("--apply-source-patch", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd069_dir = (repo / args.dd069_dir).resolve()
    dd069_manifest = read_json(dd069_dir / "dd069_ddict_read_surface_implementation_plan_manifest.json")
    source = (repo / args.source_path).resolve()
    backup_root = (repo / args.backup_root).resolve()

    generated_dir = out / "generated_source"
    generated_dir.mkdir(parents=True, exist_ok=True)
    generated_source = generated_dir / "cmd_ddict.cpp"
    generated_source.write_text(DDICT_CPP, encoding="utf-8")

    old = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""
    preview = diff_text(old, DDICT_CPP, rel(repo, source))
    (out / "dd070_cmd_ddict_patch_preview.diff").write_text(preview, encoding="utf-8")

    dd069_green = int(dd069_manifest.get("status") == EXPECTED_DD069_STATUS)
    source_exists = int(source.exists())
    source_has_house_shape = int("void cmd_DDICT" in old and "std::istringstream" in old)
    generated_has_status = int("void print_status" in DDICT_CPP and 'sub == "STATUS"' in DDICT_CPP)
    generated_has_tables = int("void print_tables" in DDICT_CPP and 'sub == "TABLES"' in DDICT_CPP)
    generated_readonly = int("READ-ONLY" in DDICT_CPP and "BUILDLMDB" not in DDICT_CPP)

    review_rows: List[Dict[str, Any]] = []
    if not dd069_green:
        review_rows.append({"issue": "DD069_NOT_READY", "detail": dd069_manifest.get("status", "")})
    if not source_exists:
        review_rows.append({"issue": "SOURCE_MISSING", "detail": str(source)})
    if not source_has_house_shape:
        review_rows.append({"issue": "SOURCE_SHAPE_REVIEW", "detail": "cmd_DDICT house handler shape not detected in existing source"})

    failures = len(review_rows)
    patched = 0
    backup_path = ""
    if args.apply_source_patch and failures == 0:
        backup_dir = backup_root / f"{args.run_id}_{stamp()}"
        backup_target = backup_dir / rel(repo, source)
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, backup_target)
        backup_path = str(backup_target)
        source.write_text(DDICT_CPP, encoding="utf-8")
        patched = 1

    if args.apply_source_patch and patched and failures == 0:
        status = "DDICT_STATUS_TABLES_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"
    elif failures == 0:
        status = "DDICT_STATUS_TABLES_SOURCE_PATCH_READY"
    else:
        status = "DDICT_STATUS_TABLES_SOURCE_PATCH_REVIEW"

    gate_rows = [
        {"gate": "dd069_plan_ready", "expected": EXPECTED_DD069_STATUS, "observed": dd069_manifest.get("status", ""), "pass": dd069_green},
        {"gate": "cmd_ddict_source_exists", "expected": 1, "observed": source_exists, "pass": source_exists},
        {"gate": "existing_source_house_shape", "expected": 1, "observed": source_has_house_shape, "pass": source_has_house_shape},
        {"gate": "generated_status_surface", "expected": 1, "observed": generated_has_status, "pass": generated_has_status},
        {"gate": "generated_tables_surface", "expected": 1, "observed": generated_has_tables, "pass": generated_has_tables},
        {"gate": "generated_readonly_surface", "expected": 1, "observed": generated_readonly, "pass": generated_readonly},
        {"gate": "source_patch_applied_when_requested", "expected": int(args.apply_source_patch), "observed": patched, "pass": int((not args.apply_source_patch) or patched == 1)},
    ]

    boundary_rows = [
        {"boundary": "guarded_status_tables_source_patch", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cmd_ddict_cpp_edit", "observed": patched, "required": int(args.apply_source_patch), "pass": int((not args.apply_source_patch) or patched == 1)},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd070_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd070_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd070_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-070 Guarded DDICT STATUS / TABLES Implementation

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-070 implements the first real read-only `DDICT` surfaces:

```text
DDICT STATUS
DDICT TABLES
```

## Target

- Source: `{rel(repo, source)}`
- Generated candidate: `{rel(repo, generated_source)}`
- Patch preview: `{rel(repo, out / 'dd070_cmd_ddict_patch_preview.diff')}`

## Result

- Apply requested: **{int(args.apply_source_patch)}**
- Source patched: **{patched}**
- Backup path: `{backup_path}`

## Boundary

DD-070 edits only `cmd_ddict.cpp` when `--apply-source-patch` is supplied.
It does not edit registry/build files, mutate active catalog data, append/replace/delete/pack/zap DBFs,
rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair rows.
"""
    (out / "DD070_GUARDED_DDICT_STATUS_TABLES_IMPLEMENTATION_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd070_guarded_ddict_status_tables_impl_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd069_status": dd069_manifest.get("status", ""),
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
        "next_recommended_action": "Build DotTalk++ and run DDICT STATUS/TABLES smoke; then DD-071 closure.",
    }
    write_json(out / "dd070_guarded_ddict_status_tables_impl_manifest.json", manifest)

    print(f"DD-070 guarded DDICT STATUS/TABLES manifest: {out / 'dd070_guarded_ddict_status_tables_impl_manifest.json'}")
    print(f"status: {status}; patched: {patched}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
