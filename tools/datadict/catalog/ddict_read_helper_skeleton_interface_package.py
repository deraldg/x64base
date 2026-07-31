#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json
from pathlib import Path

EXPECTED_DD088_STATUS = "DDICT_READ_HELPER_REFACTOR_PLAN_READY"

SKELETONS = {
"include/datadict/ddict_read_helpers.hpp": """#pragma once
#include <string>
#include <unordered_map>
namespace dottalk::datadict {
using DDictRow = std::unordered_map<std::string, std::string>;
std::string lower_copy(std::string value);
std::string trim_copy(std::string value);
std::string upper_copy(std::string value);
std::string short_text(const std::string& value, std::size_t limit);
std::string value_of(const DDictRow& row, const std::string& key);
} // namespace dottalk::datadict
""",
"src/datadict/ddict_read_helpers.cpp": """#include \"datadict/ddict_read_helpers.hpp\"
// DD-089A skeleton only. Implementation migration is deferred.
namespace dottalk::datadict {
std::string lower_copy(std::string value) { return value; }
std::string trim_copy(std::string value) { return value; }
std::string upper_copy(std::string value) { return value; }
std::string short_text(const std::string& value, std::size_t limit) { return value.size() <= limit ? value : value.substr(0, limit); }
std::string value_of(const DDictRow& row, const std::string& key) { auto it = row.find(key); return it == row.end() ? std::string{} : it->second; }
} // namespace dottalk::datadict
""",
"include/datadict/ddict_catalog_paths.hpp": """#pragma once
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>
namespace dottalk::datadict {
struct CatalogStats { std::filesystem::path dir; int dbf_present = 0; int dtx_present = 0; std::uintmax_t total_dbf_bytes = 0; };
bool exists_quiet(const std::filesystem::path& path);
std::uintmax_t size_quiet(const std::filesystem::path& path);
std::filesystem::path normalize_quiet(const std::filesystem::path& path);
std::vector<std::filesystem::path> base_roots();
std::vector<std::filesystem::path> catalog_candidates();
std::filesystem::path find_catalog_dir();
std::filesystem::path find_cdx_file(const std::string& table_name);
std::filesystem::path find_lmdb_dir(const std::string& table_name);
CatalogStats collect_stats();
} // namespace dottalk::datadict
""",
"src/datadict/ddict_catalog_paths.cpp": """#include \"datadict/ddict_catalog_paths.hpp\"
// DD-089A skeleton only. Implementation migration is deferred.
namespace dottalk::datadict {
bool exists_quiet(const std::filesystem::path& path) { return std::filesystem::exists(path); }
std::uintmax_t size_quiet(const std::filesystem::path& path) { return std::filesystem::exists(path) ? std::filesystem::file_size(path) : 0; }
std::filesystem::path normalize_quiet(const std::filesystem::path& path) { return path; }
std::vector<std::filesystem::path> base_roots() { return {}; }
std::vector<std::filesystem::path> catalog_candidates() { return {}; }
std::filesystem::path find_catalog_dir() { return {}; }
std::filesystem::path find_cdx_file(const std::string& table_name) { (void)table_name; return {}; }
std::filesystem::path find_lmdb_dir(const std::string& table_name) { (void)table_name; return {}; }
CatalogStats collect_stats() { return {}; }
} // namespace dottalk::datadict
""",
"include/datadict/ddict_dbf_reader.hpp": """#pragma once
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <string>
#include <unordered_map>
#include <vector>
namespace dottalk::datadict {
using DDictRow = std::unordered_map<std::string, std::string>;
struct FieldDef { std::string name; char type = 'C'; std::size_t width = 0; };
std::vector<unsigned char> read_binary(const std::filesystem::path& path);
std::vector<FieldDef> parse_fields(const std::vector<unsigned char>& data);
std::vector<DDictRow> read_dbf_table(const std::filesystem::path& catalog_dir, const std::string& table_name);
} // namespace dottalk::datadict
""",
"src/datadict/ddict_dbf_reader.cpp": """#include \"datadict/ddict_dbf_reader.hpp\"
// DD-089A skeleton only. Implementation migration is deferred.
namespace dottalk::datadict {
std::vector<unsigned char> read_binary(const std::filesystem::path& path) { (void)path; return {}; }
std::vector<FieldDef> parse_fields(const std::vector<unsigned char>& data) { (void)data; return {}; }
std::vector<DDictRow> read_dbf_table(const std::filesystem::path& catalog_dir, const std::string& table_name) { (void)catalog_dir; (void)table_name; return {}; }
} // namespace dottalk::datadict
""",
"include/datadict/ddict_object_resolver.hpp": """#pragma once
#include <string>
#include <unordered_map>
#include <vector>
#include \"datadict/ddict_dbf_reader.hpp\"
namespace dottalk::datadict {
const DDictRow* resolve_object(const std::vector<DDictRow>& objects, const std::string& token);
std::unordered_map<std::string, const DDictRow*> object_index(const std::vector<DDictRow>& objects);
} // namespace dottalk::datadict
""",
"src/datadict/ddict_object_resolver.cpp": """#include \"datadict/ddict_object_resolver.hpp\"
// DD-089A skeleton only. Implementation migration is deferred.
namespace dottalk::datadict {
const DDictRow* resolve_object(const std::vector<DDictRow>& objects, const std::string& token) { (void)objects; (void)token; return nullptr; }
std::unordered_map<std::string, const DDictRow*> object_index(const std::vector<DDictRow>& objects) { (void)objects; return {}; }
} // namespace dottalk::datadict
""",
"docs/datadict/fragments/DD089A_candidate_cmake_fragment.txt": """# DD-089A candidate CMake fragment only.
# Do not include this fragment until a guarded extraction/parity lane is authorized.
# Candidate source files:
#   src/datadict/ddict_read_helpers.cpp
#   src/datadict/ddict_catalog_paths.cpp
#   src/datadict/ddict_dbf_reader.cpp
#   src/datadict/ddict_object_resolver.cpp
"""
}

GROUPS = [
 {"group":"string_utils","headers":"include/datadict/ddict_read_helpers.hpp","sources":"src/datadict/ddict_read_helpers.cpp","functions":"lower_copy;trim_copy;upper_copy;short_text;value_of","migration_status":"SKELETON_ONLY_IMPLEMENTATION_DEFERRED"},
 {"group":"catalog_paths","headers":"include/datadict/ddict_catalog_paths.hpp","sources":"src/datadict/ddict_catalog_paths.cpp","functions":"exists_quiet;size_quiet;normalize_quiet;base_roots;catalog_candidates;find_catalog_dir;find_cdx_file;find_lmdb_dir;collect_stats","migration_status":"SKELETON_ONLY_IMPLEMENTATION_DEFERRED"},
 {"group":"dbf_reader","headers":"include/datadict/ddict_dbf_reader.hpp","sources":"src/datadict/ddict_dbf_reader.cpp","functions":"read_binary;parse_fields;read_dbf_table plus later descriptor helpers","migration_status":"SKELETON_ONLY_IMPLEMENTATION_DEFERRED"},
 {"group":"object_resolver","headers":"include/datadict/ddict_object_resolver.hpp","sources":"src/datadict/ddict_object_resolver.cpp","functions":"resolve_object;object_index","migration_status":"SKELETON_ONLY_IMPLEMENTATION_DEFERRED"},
]

TESTS = [
 ("DDICT_HELP_PRESERVED","DDICT HELP"),
 ("DDICT_STATUS_PRESERVED","DDICT STATUS"),
 ("DDICT_TABLES_PRESERVED","DDICT TABLES"),
 ("DDICT_OBJECTS_PRESERVED","DDICT OBJECTS TYPE CATALOG_TABLE"),
 ("DDICT_FIELDS_PRESERVED","DDICT FIELDS DDOBJECT"),
 ("DDICT_TAGS_PRESERVED","DDICT TAGS DDATTR"),
 ("DDICT_REL_PRESERVED","DDICT REL DDOBJECT OUT"),
 ("DDICT_EVIDENCE_PRESERVED","DDICT EVIDENCE DDOBJECT"),
]

def utc_now(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
def read_json(path):
    if not path.exists(): return {}
    try: return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception: return {}
def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows: w.writerow({k: row.get(k, "") for k in fields})

def main():
    ap = argparse.ArgumentParser(description="DD-089A DDICT read-helper skeleton/interface package")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD089A-read-helper-skeleton-interface-package-v0")
    ap.add_argument("--dd088-dir", default="docs/datadict/reports/DD088-ddict-read-helper-refactor-plan-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    dd088 = read_json(repo / args.dd088_dir / "dd088_ddict_read_helper_refactor_plan_manifest.json")
    generated_root = out / "generated_skeleton"

    file_rows = []
    for rel_path, text in SKELETONS.items():
        target = generated_root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        file_rows.append({"artifact":rel_path,"generated_path":str(target),"bytes":len(text.encode()),"installed_to_repo":0,"wired_to_build":0,"implementation_migrated":0})

    gate_rows = [
        {"gate":"dd088_refactor_plan_ready","expected":EXPECTED_DD088_STATUS,"observed":dd088.get("status",""),"pass":int(dd088.get("status") == EXPECTED_DD088_STATUS)},
        {"gate":"skeleton_files_generated","expected":len(SKELETONS),"observed":len(file_rows),"pass":int(len(file_rows)==len(SKELETONS))},
        {"gate":"candidate_headers_generated","expected":4,"observed":sum(1 for r in file_rows if r["artifact"].endswith(".hpp")),"pass":int(sum(1 for r in file_rows if r["artifact"].endswith(".hpp"))==4)},
        {"gate":"candidate_sources_generated","expected":4,"observed":sum(1 for r in file_rows if r["artifact"].endswith(".cpp")),"pass":int(sum(1 for r in file_rows if r["artifact"].endswith(".cpp"))==4)},
        {"gate":"implementation_migration_deferred","expected":0,"observed":0,"pass":1},
        {"gate":"build_wiring_deferred","expected":0,"observed":0,"pass":1},
    ]
    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_READ_HELPER_SKELETON_PACKAGE_READY" if failures == 0 else "DDICT_READ_HELPER_SKELETON_PACKAGE_REVIEW"

    boundary_rows = [
        {"boundary":"skeleton_package_only","observed":1,"required":1,"pass":1},
        {"boundary":"cxx_source_edits","observed":0,"required":0,"pass":1},
        {"boundary":"repo_cxx_files_installed","observed":0,"required":0,"pass":1},
        {"boundary":"cmd_ddict_cpp_patched","observed":0,"required":0,"pass":1},
        {"boundary":"build_file_edits","observed":0,"required":0,"pass":1},
        {"boundary":"registry_edits","observed":0,"required":0,"pass":1},
        {"boundary":"active_catalog_mutation","observed":0,"required":0,"pass":1},
        {"boundary":"dbf_append_replace_delete_pack_zap","observed":0,"required":0,"pass":1},
        {"boundary":"cdx_lmdb_create_rebuild","observed":0,"required":0,"pass":1},
        {"boundary":"help_meta_cmdhelpchk_mutation","observed":0,"required":0,"pass":1},
        {"boundary":"catalog_regeneration","observed":0,"required":0,"pass":1},
        {"boundary":"manual_row_repair","observed":0,"required":0,"pass":1},
    ]
    tests = [{"test_id":tid,"command":cmd,"required_after_future_extraction":1} for tid,cmd in TESTS]
    next_rows = [
        {"next_id":"DD089B","title":"guarded skeleton install package","allowed_scope":"copy candidate headers/sources into repo only; no cmd_ddict.cpp patch; no CMake wiring unless separately authorized"},
        {"next_id":"DD089C","title":"guarded helper implementation extraction","allowed_scope":"move implementation from cmd_ddict.cpp into helper files and rerun full DDICT parity tests"},
        {"next_id":"DD089D","title":"build wiring and parity closure","allowed_scope":"wire helper cpp files into build only after source extraction preview is accepted"},
    ]

    write_csv(out/"dd089a_skeleton_file_ledger.csv", file_rows, ["artifact","generated_path","bytes","installed_to_repo","wired_to_build","implementation_migrated"])
    write_csv(out/"dd089a_helper_group_ledger.csv", GROUPS, ["group","headers","sources","functions","migration_status"])
    write_csv(out/"dd089a_parity_test_carryforward.csv", tests, ["test_id","command","required_after_future_extraction"])
    write_csv(out/"dd089a_gate_ledger.csv", gate_rows, ["gate","expected","observed","pass"])
    write_csv(out/"dd089a_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary","observed","required","pass"])
    write_csv(out/"dd089a_next_lane_recommendations.csv", next_rows, ["next_id","title","allowed_scope"])

    report = f"""# DD-089A DDICT Read-Helper Skeleton / Interface Package

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-089A creates candidate read-helper skeleton/interface files as report artifacts only.

It does not install files into the repository source tree, patch `cmd_ddict.cpp`, wire CMake,
or migrate implementation code.

## Inputs

- DD-088 status: `{dd088.get('status','')}`
- Generated skeleton root: `{generated_root}`

## Result

- Generated files: **{len(file_rows)}**
- Candidate headers: **{sum(1 for r in file_rows if r['artifact'].endswith('.hpp'))}**
- Candidate sources: **{sum(1 for r in file_rows if r['artifact'].endswith('.cpp'))}**
- Installed into repo: **0**
- Wired to build: **0**
- Implementation migrated: **0**

## Boundary

DD-089A is skeleton/interface packaging only. It does not edit C++ source, install new
C++ files into the repo source tree, patch `cmd_ddict.cpp`, edit build files, mutate
active catalog data, create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate
catalog content, or repair manual rows.
"""
    (out/"DD089A_READ_HELPER_SKELETON_INTERFACE_PACKAGE_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract":"dd089a_read_helper_skeleton_interface_package_v0",
        "run_id":args.run_id,
        "created_utc":utc_now(),
        "status":status,
        "repo_root":str(repo),
        "profiles":args.profile,
        "dd088_status":dd088.get("status",""),
        "generated_skeleton_root":str(generated_root),
        "generated_files":len(file_rows),
        "candidate_headers":sum(1 for r in file_rows if r["artifact"].endswith(".hpp")),
        "candidate_sources":sum(1 for r in file_rows if r["artifact"].endswith(".cpp")),
        "installed_to_repo":0,
        "wired_to_build":0,
        "implementation_migrated":0,
        "failures":failures,
        "cxx_source_edits":0,
        "repo_cxx_files_installed":0,
        "cmd_ddict_cpp_patched":0,
        "build_file_edits":0,
        "registry_edits":0,
        "active_catalog_mutation":0,
        "help_meta_cmdhelpchk_mutation":0,
        "next_recommended_action":"DD-089B guarded skeleton install package or DD-089C implementation extraction plan, explicitly authorized.",
    }
    write_json(out/"dd089a_read_helper_skeleton_interface_package_manifest.json", manifest)
    print(f"DD-089A read-helper skeleton/interface manifest: {out/'dd089a_read_helper_skeleton_interface_package_manifest.json'}")
    print(f"status: {status}; generated_files: {len(file_rows)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
