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

EXPECTED_DD074_STATUS = "DDICT_TAGS_REPRESENTATION_PLAN_READY"
DDICT_CPP = '#include "cli/cmd_ddict.hpp"\n\n#include <algorithm>\n#include <array>\n#include <cctype>\n#include <cstdint>\n#include <filesystem>\n#include <fstream>\n#include <iomanip>\n#include <iostream>\n#include <sstream>\n#include <string>\n#include <unordered_map>\n#include <vector>\n\nnamespace {\n\nnamespace fs = std::filesystem;\n\nstruct TableInfo {\n    const char* name;\n};\n\nconstexpr std::array<TableInfo, 11> kTables{{\n    TableInfo{"DDRUN"},\n    TableInfo{"DDBASE"},\n    TableInfo{"DDSOURCE"},\n    TableInfo{"DDOBJECT"},\n    TableInfo{"DDATTR"},\n    TableInfo{"DDEDGE"},\n    TableInfo{"DDEVID"},\n    TableInfo{"DDGATE"},\n    TableInfo{"DDREVIEW"},\n    TableInfo{"DDARTIF"},\n    TableInfo{"DDPROFILE"},\n}};\n\nstruct FieldDef {\n    std::string name;\n    char type = \'C\';\n    std::size_t width = 0;\n};\n\nusing Row = std::unordered_map<std::string, std::string>;\n\nstd::string lower_copy(std::string s) {\n    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) {\n        return static_cast<char>(std::tolower(ch));\n    });\n    return s;\n}\n\nstd::string trim_copy(std::string s) {\n    auto not_space = [](unsigned char ch) {\n        return !std::isspace(ch) && ch != \'\\0\';\n    };\n    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));\n    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());\n    return s;\n}\n\nstd::string upper_copy(std::string s) {\n    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) {\n        return static_cast<char>(std::toupper(ch));\n    });\n    return s;\n}\n\nstd::string value_of(const Row& row, const std::string& key) {\n    auto it = row.find(key);\n    return it == row.end() ? std::string{} : it->second;\n}\n\nbool exists_quiet(const fs::path& p) {\n    std::error_code ec;\n    return fs::exists(p, ec);\n}\n\nstd::uintmax_t size_quiet(const fs::path& p) {\n    std::error_code ec;\n    if (!fs::exists(p, ec) || !fs::is_regular_file(p, ec)) {\n        return 0;\n    }\n    auto n = fs::file_size(p, ec);\n    return ec ? 0 : n;\n}\n\nfs::path normalize_quiet(const fs::path& p) {\n    std::error_code ec;\n    auto c = fs::weakly_canonical(p, ec);\n    return ec ? p : c;\n}\n\nstd::vector<fs::path> base_roots() {\n    std::vector<fs::path> roots;\n    std::error_code ec;\n    fs::path cwd = fs::current_path(ec);\n    if (ec) {\n        cwd = fs::path(".");\n    }\n\n    roots.push_back(cwd);\n    roots.push_back(cwd / "..");\n    roots.push_back(cwd / "../..");\n    roots.push_back(cwd / "../../..");\n    return roots;\n}\n\nstd::vector<fs::path> catalog_candidates() {\n    std::vector<fs::path> candidates;\n    for (const auto& root : base_roots()) {\n        candidates.push_back(root / "data" / "metadata" / "datadict");\n        candidates.push_back(root / "dottalkpp" / "data" / "metadata" / "datadict");\n    }\n    candidates.push_back(fs::path("data") / "metadata" / "datadict");\n    candidates.push_back(fs::path("dottalkpp") / "data" / "metadata" / "datadict");\n    return candidates;\n}\n\nfs::path find_catalog_dir() {\n    for (const auto& c : catalog_candidates()) {\n        if (exists_quiet(c)) {\n            return normalize_quiet(c);\n        }\n    }\n    return normalize_quiet(fs::path("dottalkpp") / "data" / "metadata" / "datadict");\n}\n\nfs::path find_cdx_file(const std::string& table_name) {\n    std::string lower = lower_copy(table_name);\n    std::string upper = upper_copy(table_name);\n    for (const auto& root : base_roots()) {\n        std::vector<fs::path> candidates{\n            root / "data" / "indexes" / (lower + ".cdx"),\n            root / "data" / "indexes" / (upper + ".cdx"),\n            root / "dottalkpp" / "data" / "indexes" / (lower + ".cdx"),\n            root / "dottalkpp" / "data" / "indexes" / (upper + ".cdx"),\n            root / "indexes" / (lower + ".cdx"),\n            root / "indexes" / (upper + ".cdx"),\n        };\n        for (const auto& p : candidates) {\n            if (exists_quiet(p)) {\n                return normalize_quiet(p);\n            }\n        }\n    }\n    return {};\n}\n\nfs::path find_lmdb_dir(const std::string& table_name) {\n    std::string lower = lower_copy(table_name);\n    std::string upper = upper_copy(table_name);\n    for (const auto& root : base_roots()) {\n        std::vector<fs::path> candidates{\n            root / "data" / "lmdb" / (lower + ".cdx.d"),\n            root / "data" / "lmdb" / (upper + ".cdx.d"),\n            root / "dottalkpp" / "data" / "lmdb" / (lower + ".cdx.d"),\n            root / "dottalkpp" / "data" / "lmdb" / (upper + ".cdx.d"),\n            root / "lmdb" / (lower + ".cdx.d"),\n            root / "lmdb" / (upper + ".cdx.d"),\n        };\n        for (const auto& p : candidates) {\n            if (exists_quiet(p)) {\n                return normalize_quiet(p);\n            }\n        }\n    }\n    return {};\n}\n\nstruct CatalogStats {\n    fs::path dir;\n    int dbf_present = 0;\n    int dtx_present = 0;\n    std::uintmax_t total_dbf_bytes = 0;\n};\n\nCatalogStats collect_stats() {\n    CatalogStats stats;\n    stats.dir = find_catalog_dir();\n    for (const auto& t : kTables) {\n        fs::path dbf = stats.dir / (std::string(t.name) + ".dbf");\n        fs::path dtx = stats.dir / (std::string(t.name) + ".dtx");\n        if (exists_quiet(dbf)) {\n            ++stats.dbf_present;\n            stats.total_dbf_bytes += size_quiet(dbf);\n        }\n        if (exists_quiet(dtx)) {\n            ++stats.dtx_present;\n        }\n    }\n    return stats;\n}\n\nbool plausible_name(const std::vector<unsigned char>& data, std::size_t off) {\n    if (off + 11 > data.size()) {\n        return false;\n    }\n    unsigned char first = data[off];\n    if (!(std::isalpha(first) || first == \'_\')) {\n        return false;\n    }\n    for (std::size_t i = off; i < off + 11 && data[i] != 0; ++i) {\n        unsigned char ch = data[i];\n        if (!(std::isalnum(ch) || ch == \'_\')) {\n            return false;\n        }\n    }\n    return true;\n}\n\nbool plausible_descriptor(const std::vector<unsigned char>& data, std::size_t off) {\n    if (off + 32 > data.size() || data[off] == 0x0D || data[off] == 0x1A) {\n        return false;\n    }\n    if (!plausible_name(data, off)) {\n        return false;\n    }\n    char t = static_cast<char>(data[off + 11]);\n    std::string allowed = "CDNLFIMBYT@GOVQ";\n    return allowed.find(t) != std::string::npos;\n}\n\nstd::size_t descriptor_start(const std::vector<unsigned char>& data) {\n    if (plausible_descriptor(data, 96)) {\n        return 96;\n    }\n    if (plausible_descriptor(data, 32)) {\n        return 32;\n    }\n    const std::size_t limit = std::min<std::size_t>(data.size(), 512);\n    for (std::size_t off = 0; off + 64 < limit; ++off) {\n        if (plausible_descriptor(data, off) && plausible_descriptor(data, off + 32)) {\n            return off;\n        }\n    }\n    return static_cast<std::size_t>(-1);\n}\n\nstd::uint16_t le16(const std::vector<unsigned char>& data, std::size_t off) {\n    if (off + 2 > data.size()) {\n        return 0;\n    }\n    return static_cast<std::uint16_t>(data[off] | (data[off + 1] << 8));\n}\n\nstd::uint32_t le32(const std::vector<unsigned char>& data, std::size_t off) {\n    if (off + 4 > data.size()) {\n        return 0;\n    }\n    return static_cast<std::uint32_t>(data[off] | (data[off + 1] << 8) |\n        (data[off + 2] << 16) | (data[off + 3] << 24));\n}\n\nstd::string descriptor_name(const std::vector<unsigned char>& data, std::size_t off) {\n    std::string s;\n    for (std::size_t i = off; i < off + 11 && i < data.size() && data[i] != 0; ++i) {\n        s.push_back(static_cast<char>(data[i]));\n    }\n    return upper_copy(trim_copy(s));\n}\n\nstd::vector<unsigned char> read_binary(const fs::path& path) {\n    std::ifstream in(path, std::ios::binary);\n    if (!in) {\n        return {};\n    }\n    return std::vector<unsigned char>(std::istreambuf_iterator<char>(in), {});\n}\n\nstd::vector<FieldDef> parse_fields(const std::vector<unsigned char>& data) {\n    std::vector<FieldDef> fields;\n    std::size_t start = descriptor_start(data);\n    if (start == static_cast<std::size_t>(-1)) {\n        return fields;\n    }\n    for (std::size_t off = start; off + 32 <= data.size(); off += 32) {\n        if (data[off] == 0x0D || !plausible_descriptor(data, off)) {\n            break;\n        }\n        FieldDef f;\n        f.name = descriptor_name(data, off);\n        f.type = static_cast<char>(data[off + 11]);\n        f.width = data[off + 16];\n        if (f.width == 0) {\n            f.width = le16(data, off + 16);\n        }\n        if (!f.name.empty() && f.width > 0 && f.width < 4096) {\n            fields.push_back(f);\n        }\n    }\n    return fields;\n}\n\nstd::vector<Row> read_dbf_table(const fs::path& catalog_dir, const std::string& table_name) {\n    fs::path path = catalog_dir / (upper_copy(table_name) + ".dbf");\n    std::vector<unsigned char> data = read_binary(path);\n    if (data.size() < 32) {\n        return {};\n    }\n\n    std::uint32_t records = le32(data, 4);\n    std::uint16_t header_len = le16(data, 8);\n    std::uint16_t record_len = le16(data, 10);\n    std::vector<FieldDef> fields = parse_fields(data);\n    if (header_len == 0 || record_len == 0 || fields.empty()) {\n        return {};\n    }\n\n    std::vector<Row> rows;\n    for (std::uint32_t rec = 0; rec < records; ++rec) {\n        std::size_t base = static_cast<std::size_t>(header_len) + static_cast<std::size_t>(rec) * record_len;\n        if (base + record_len > data.size()) {\n            break;\n        }\n        if (data[base] == \'*\') {\n            continue;\n        }\n        Row row;\n        std::size_t pos = base + 1;\n        for (const auto& f : fields) {\n            if (pos + f.width > data.size()) {\n                break;\n            }\n            std::string raw(reinterpret_cast<const char*>(&data[pos]), f.width);\n            row[f.name] = trim_copy(raw);\n            pos += f.width;\n        }\n        rows.push_back(std::move(row));\n    }\n    return rows;\n}\n\nvoid print_ddict_usage() {\n    std::cout\n        << "Usage:\\n"\n        << "  DDICT HELP\\n"\n        << "  DDICT STATUS\\n"\n        << "  DDICT TABLES\\n"\n        << "  DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]\\n"\n        << "  DDICT FIELDS <table>\\n"\n        << "  DDICT TAGS <table>\\n"\n        << "  DDICT REL <object-id-or-name> [IN|OUT|BOTH]\\n"\n        << "  DDICT EVIDENCE <object-id-or-name>\\n"\n        << "Notes:\\n"\n        << "  DDICT is read-only over the active Data Dictionary catalog.\\n";\n}\n\nvoid print_pending(const std::string& sub) {\n    std::cout\n        << "DDICT " << sub\n        << " is accepted by contract but runtime read implementation is pending.\\n";\n}\n\nvoid print_status() {\n    CatalogStats stats = collect_stats();\n    std::cout\n        << "DDICT STATUS\\n"\n        << "  Active catalog: " << stats.dir.string() << "\\n"\n        << "  Read mode     : READ-ONLY\\n"\n        << "  DBF tables    : " << stats.dbf_present << " / " << kTables.size() << "\\n"\n        << "  DTX sidecars  : " << stats.dtx_present << " / " << kTables.size() << "\\n"\n        << "  DBF bytes     : " << stats.total_dbf_bytes << "\\n";\n    if (stats.dbf_present == static_cast<int>(kTables.size())) {\n        std::cout << "  Catalog state : ACTIVE_CATALOG_PRESENT\\n";\n    } else {\n        std::cout << "  Catalog state : ACTIVE_CATALOG_REVIEW\\n";\n    }\n}\n\nvoid print_tables() {\n    fs::path dir = find_catalog_dir();\n    std::cout\n        << "DDICT TABLES\\n"\n        << "  Active catalog: " << dir.string() << "\\n"\n        << "  Read mode     : READ-ONLY\\n"\n        << "  Table       DBF  DTX  DBF_BYTES\\n"\n        << "  ----------  ---  ---  ---------\\n";\n    for (const auto& t : kTables) {\n        fs::path dbf = dir / (std::string(t.name) + ".dbf");\n        fs::path dtx = dir / (std::string(t.name) + ".dtx");\n        bool has_dbf = exists_quiet(dbf);\n        bool has_dtx = exists_quiet(dtx);\n        std::cout\n            << "  " << std::left << std::setw(10) << t.name\n            << "  " << (has_dbf ? "YES" : "NO ")\n            << "  " << (has_dtx ? "YES" : "NO ")\n            << "  " << size_quiet(dbf)\n            << "\\n";\n    }\n}\n\nvoid print_fields(std::istringstream& args) {\n    std::string table_token;\n    args >> table_token;\n    table_token = upper_copy(trim_copy(table_token));\n\n    if (table_token.empty()) {\n        std::cout << "DDICT FIELDS requires a table name.\\n";\n        return;\n    }\n\n    fs::path dir = find_catalog_dir();\n    std::vector<Row> objects = read_dbf_table(dir, "DDOBJECT");\n    std::vector<Row> attrs = read_dbf_table(dir, "DDATTR");\n    std::vector<Row> fields;\n\n    for (const auto& row : objects) {\n        std::string objtype = upper_copy(value_of(row, "OBJTYPE"));\n        std::string owner = upper_copy(value_of(row, "OWNER"));\n        if (objtype == "CATALOG_FIELD" && owner == table_token) {\n            fields.push_back(row);\n        }\n    }\n\n    std::cout\n        << "DDICT FIELDS " << table_token << "\\n"\n        << "  Active catalog: " << dir.string() << "\\n"\n        << "  Read mode     : READ-ONLY\\n"\n        << "  Field rows    : " << fields.size() << "\\n";\n\n    if (fields.empty()) {\n        std::cout\n            << "  Result        : NO_FIELDS_FOUND\\n"\n            << "  Note          : expected DDOBJECT rows where OBJTYPE=CATALOG_FIELD and OWNER="\n            << table_token << "\\n";\n        return;\n    }\n\n    std::unordered_map<std::string, int> attr_counts;\n    for (const auto& attr : attrs) {\n        std::string objid = value_of(attr, "OBJID");\n        if (!objid.empty()) {\n            ++attr_counts[objid];\n        }\n    }\n\n    std::cout\n        << "  Field       OBJID                     STATUS                    PROFILE       ATTRS\\n"\n        << "  ----------  ------------------------  ------------------------  ------------  -----\\n";\n\n    for (const auto& field : fields) {\n        std::string objid = value_of(field, "OBJID");\n        std::string name = value_of(field, "NAME");\n        std::string status = value_of(field, "STATUS");\n        std::string profile = value_of(field, "PROFILE");\n        int acount = objid.empty() ? 0 : attr_counts[objid];\n\n        std::cout\n            << "  " << std::left << std::setw(10) << name.substr(0, 10)\n            << "  " << std::setw(24) << objid.substr(0, 24)\n            << "  " << std::setw(24) << status.substr(0, 24)\n            << "  " << std::setw(12) << profile.substr(0, 12)\n            << "  " << acount\n            << "\\n";\n    }\n}\n\nvoid print_tags(std::istringstream& args) {\n    std::string table_token;\n    args >> table_token;\n    table_token = upper_copy(trim_copy(table_token));\n\n    if (table_token.empty()) {\n        std::cout << "DDICT TAGS requires a table name.\\n";\n        return;\n    }\n\n    fs::path dir = find_catalog_dir();\n    fs::path dbf = dir / (table_token + ".dbf");\n    fs::path cdx = find_cdx_file(table_token);\n    fs::path lmdb = find_lmdb_dir(table_token);\n    std::vector<Row> objects = read_dbf_table(dir, "DDOBJECT");\n    std::vector<Row> attrs = read_dbf_table(dir, "DDATTR");\n    std::vector<Row> tags;\n\n    for (const auto& row : objects) {\n        std::string objtype = upper_copy(value_of(row, "OBJTYPE"));\n        std::string owner = upper_copy(value_of(row, "OWNER"));\n        if (objtype == "CATALOG_TAG" && owner == table_token) {\n            tags.push_back(row);\n        }\n    }\n\n    std::unordered_map<std::string, int> attr_counts;\n    for (const auto& attr : attrs) {\n        std::string objid = value_of(attr, "OBJID");\n        if (!objid.empty()) {\n            ++attr_counts[objid];\n        }\n    }\n\n    std::cout\n        << "DDICT TAGS " << table_token << "\\n"\n        << "  Active catalog: " << dir.string() << "\\n"\n        << "  Read mode     : READ-ONLY\\n"\n        << "  Table DBF     : " << (exists_quiet(dbf) ? "YES" : "NO") << "\\n"\n        << "  CDX artifact  : " << (cdx.empty() ? "NO" : cdx.string()) << "\\n"\n        << "  LMDB mirror   : " << (lmdb.empty() ? "NO" : lmdb.string()) << "\\n"\n        << "  Catalog tags  : " << tags.size() << "\\n";\n\n    if (tags.empty()) {\n        std::cout\n            << "  Result        : NO_CATALOG_TAGS_FOUND\\n"\n            << "  Note          : expected DDOBJECT rows where OBJTYPE=CATALOG_TAG and OWNER="\n            << table_token << "\\n";\n        return;\n    }\n\n    std::cout\n        << "  Tag         OBJID                     STATUS                    PROFILE       ATTRS\\n"\n        << "  ----------  ------------------------  ------------------------  ------------  -----\\n";\n\n    for (const auto& tag : tags) {\n        std::string objid = value_of(tag, "OBJID");\n        std::string name = value_of(tag, "NAME");\n        std::string status = value_of(tag, "STATUS");\n        std::string profile = value_of(tag, "PROFILE");\n        int acount = objid.empty() ? 0 : attr_counts[objid];\n\n        std::cout\n            << "  " << std::left << std::setw(10) << name.substr(0, 10)\n            << "  " << std::setw(24) << objid.substr(0, 24)\n            << "  " << std::setw(24) << status.substr(0, 24)\n            << "  " << std::setw(12) << profile.substr(0, 12)\n            << "  " << acount\n            << "\\n";\n    }\n}\n\n} // anonymous namespace\n\nvoid cmd_DDICT(xbase::DbArea& area, std::istringstream& args) {\n    (void)area;\n\n    std::string sub;\n    args >> sub;\n    sub = upper_copy(trim_copy(sub));\n\n    if (sub.empty() || sub == "HELP" || sub == "?" || sub == "USAGE") {\n        print_ddict_usage();\n        return;\n    }\n\n    if (sub == "STATUS") {\n        print_status();\n        return;\n    }\n\n    if (sub == "TABLES") {\n        print_tables();\n        return;\n    }\n\n    if (sub == "FIELDS") {\n        print_fields(args);\n        return;\n    }\n\n    if (sub == "TAGS") {\n        print_tags(args);\n        return;\n    }\n\n    if (sub == "OBJECTS" || sub == "REL" || sub == "EVIDENCE") {\n        print_pending(sub);\n        return;\n    }\n\n    std::cout << "DDICT: unknown subcommand \'" << sub << "\'.\\n";\n    print_ddict_usage();\n}\n'

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

def diff_text(old: str, new: str, path: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=path + ".before",
        tofile=path + ".after",
        lineterm="",
    ))

def main() -> int:
    ap = argparse.ArgumentParser(description="DD-075 guarded DDICT TAGS implementation")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD075-guarded-ddict-tags-implementation-v0")
    ap.add_argument("--dd074-dir", default="docs/datadict/reports/DD074-ddict-tags-representation-plan-v0")
    ap.add_argument("--source-path", default="src/cli/cmd_ddict.cpp")
    ap.add_argument("--apply-source-patch", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd074_dir = (repo / args.dd074_dir).resolve()
    dd074_manifest = read_json(dd074_dir / "dd074_ddict_tags_representation_plan_manifest.json")
    source = (repo / args.source_path).resolve()
    backup_root = (repo / args.backup_root).resolve()

    generated_dir = out / "generated_source"
    generated_dir.mkdir(parents=True, exist_ok=True)
    generated_source = generated_dir / "cmd_ddict.cpp"
    generated_source.write_text(DDICT_CPP, encoding="utf-8")

    old = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""
    preview = diff_text(old, DDICT_CPP, rel(repo, source))
    (out / "dd075_cmd_ddict_tags_patch_preview.diff").write_text(preview, encoding="utf-8")

    dd074_green = int(dd074_manifest.get("status") == EXPECTED_DD074_STATUS)
    source_exists = int(source.exists())
    existing_has_fields = int("print_fields" in old and 'sub == "FIELDS"' in old)
    generated_has_tags = int("void print_tags" in DDICT_CPP and 'sub == "TAGS"' in DDICT_CPP)
    generated_preserves_fields = int("void print_fields" in DDICT_CPP and 'sub == "FIELDS"' in DDICT_CPP)
    generated_readonly = int("READ-ONLY" in DDICT_CPP and "BUILDLMDB" not in DDICT_CPP and "CDX ADDTAG" not in DDICT_CPP)

    review_rows: List[Dict[str, Any]] = []
    if not dd074_green:
        review_rows.append({"issue": "DD074_NOT_READY", "detail": dd074_manifest.get("status", "")})
    if not source_exists:
        review_rows.append({"issue": "SOURCE_MISSING", "detail": str(source)})
    if not existing_has_fields:
        review_rows.append({"issue": "FIELDS_BASELINE_NOT_DETECTED", "detail": "existing cmd_ddict.cpp does not appear to contain DD-073 FIELDS baseline"})

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
        status = "DDICT_TAGS_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"
    elif failures == 0:
        status = "DDICT_TAGS_SOURCE_PATCH_READY"
    else:
        status = "DDICT_TAGS_SOURCE_PATCH_REVIEW"

    gate_rows = [
        {"gate": "dd074_representation_plan_ready", "expected": EXPECTED_DD074_STATUS, "observed": dd074_manifest.get("status", ""), "pass": dd074_green},
        {"gate": "cmd_ddict_source_exists", "expected": 1, "observed": source_exists, "pass": source_exists},
        {"gate": "fields_baseline_detected", "expected": 1, "observed": existing_has_fields, "pass": existing_has_fields},
        {"gate": "generated_tags_surface", "expected": 1, "observed": generated_has_tags, "pass": generated_has_tags},
        {"gate": "generated_fields_preserved", "expected": 1, "observed": generated_preserves_fields, "pass": generated_preserves_fields},
        {"gate": "generated_readonly_surface", "expected": 1, "observed": generated_readonly, "pass": generated_readonly},
        {"gate": "source_patch_applied_when_requested", "expected": int(args.apply_source_patch), "observed": patched, "pass": int((not args.apply_source_patch) or patched == 1)},
    ]

    boundary_rows = [
        {"boundary": "guarded_tags_source_patch", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cmd_ddict_cpp_edit", "observed": patched, "required": int(args.apply_source_patch), "pass": int((not args.apply_source_patch) or patched == 1)},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd075_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd075_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd075_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-075 Guarded DDICT TAGS Implementation

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-075 implements:

```text
DDICT TAGS <table>
```

The implementation is read-only. It reports active catalog path, table DBF presence,
CDX artifact presence, LMDB mirror presence, and CATALOG_TAG rows from DDOBJECT.

## Target

- Source: `{rel(repo, source)}`
- Generated candidate: `{rel(repo, generated_source)}`
- Patch preview: `{rel(repo, out / 'dd075_cmd_ddict_tags_patch_preview.diff')}`

## Result

- Apply requested: **{int(args.apply_source_patch)}**
- Source patched: **{patched}**
- Backup path: `{backup_path}`

## Boundary

DD-075 edits only `cmd_ddict.cpp` when `--apply-source-patch` is supplied.
It does not edit registry/build files, mutate active catalog data, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair rows.
"""
    (out / "DD075_GUARDED_DDICT_TAGS_IMPLEMENTATION_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd075_guarded_ddict_tags_impl_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd074_status": dd074_manifest.get("status", ""),
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
        "next_recommended_action": "Build DotTalk++ and run DDICT TAGS DDATTR/DDOBJECT/DDEDGE smoke; then DD-076 closure.",
    }
    write_json(out / "dd075_guarded_ddict_tags_impl_manifest.json", manifest)

    print(f"DD-075 guarded DDICT TAGS manifest: {out / 'dd075_guarded_ddict_tags_impl_manifest.json'}")
    print(f"status: {status}; patched: {patched}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
