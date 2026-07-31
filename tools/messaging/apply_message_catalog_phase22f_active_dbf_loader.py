#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22F_ACTIVE_DBF_ROW_LOAD_PROVIDER_SOURCE_PATCH_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22F_ACTIVE_DBF_ROW_LOAD_PROVIDER_SOURCE_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_SET_MESSAGE_CATALOG_CHECK_THEN_VALIDATE_PHASE22F"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

MESSAGE_CATALOG_CPP = r'''// ============================================================================
// File: src/help/message_catalog.cpp
// Purpose: Runtime Messaging catalog provider boundary.
// Phase: MSG-022F active DBF row-load provider.
// ============================================================================

#include "message_catalog.hpp"

#include "helpdata_messages.hpp"

#include "memo/memo_auto.hpp"
#include "memo/memostore.hpp"
#include "xbase.hpp"
#include "xbase_64.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace dottalk::helpdata {
namespace {

namespace fs = std::filesystem;

struct ActiveCatalogPaths {
    fs::path dbf_dir;
    fs::path indexes_dir;
    fs::path lmdb_dir;
    bool present = false;
};

struct ActiveMessageRow {
    std::string msgid;
    std::string symbol;
    std::string enumname;
    std::string facility;
    std::string owner;
    std::string category;
    std::string severity;
    std::string status;
    std::string src;
};

struct ActiveTextRow {
    std::string msgid;
    std::string symbol;
    std::string enumname;
    std::string locale;
    std::string msglocale;
    std::string symbolloc;
    std::string text;
    std::string txthash;
    std::string status;
    std::string src;
};

struct ActiveCatalogLoad {
    ActiveCatalogPaths paths;
    bool loaded = false;
    std::string detail;
    std::vector<ActiveMessageRow> messages;
    std::vector<ActiveTextRow> texts;
    std::unordered_map<std::string, std::string> text_by_symbol_locale;
};

std::string generic_string(const fs::path& p)
{
    return p.lexically_normal().generic_string();
}

std::string trim_copy(std::string s)
{
    auto not_space = [](unsigned char ch) { return !std::isspace(ch); };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
}

std::string upper_copy(std::string s)
{
    for (auto& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

std::string text_key(const std::string& symbol, const std::string& locale)
{
    return upper_copy(trim_copy(symbol)) + "\x1f" + upper_copy(trim_copy(locale));
}

std::vector<fs::path> data_root_candidates()
{
    std::vector<fs::path> roots;

    fs::path cur = fs::current_path();
    for (fs::path p = cur; !p.empty(); p = p.parent_path()) {
        roots.push_back(p / "dottalkpp" / "data");
        roots.push_back(p / "data");

        if (p == p.parent_path()) {
            break;
        }
    }

    roots.push_back(fs::path("dottalkpp") / "data");
    return roots;
}

bool messaging_artifacts_present(const fs::path& dbf_dir)
{
    return fs::exists(dbf_dir / "SYSTEM_MESSAGES.dbf")
        && fs::exists(dbf_dir / "SYSTEM_MESSAGE_TEXT.dbf")
        && fs::exists(dbf_dir / "SYSTEM_MESSAGE_TEXT.dtx");
}

ActiveCatalogPaths find_active_catalog_paths()
{
    for (const auto& data_root : data_root_candidates()) {
        ActiveCatalogPaths current{
            data_root / "messaging",
            data_root / "indexes" / "messaging",
            data_root / "lmdb" / "messaging",
            false
        };
        if (messaging_artifacts_present(current.dbf_dir)) {
            current.present = true;
            return current;
        }

        ActiveCatalogPaths dbf_subdir{
            data_root / "dbf" / "messaging",
            data_root / "indexes" / "messaging",
            data_root / "lmdb" / "messaging",
            false
        };
        if (messaging_artifacts_present(dbf_subdir.dbf_dir)) {
            dbf_subdir.present = true;
            return dbf_subdir;
        }
    }

    ActiveCatalogPaths fallback{
        fs::path("dottalkpp") / "data" / "messaging",
        fs::path("dottalkpp") / "data" / "indexes" / "messaging",
        fs::path("dottalkpp") / "data" / "lmdb" / "messaging",
        false
    };
    return fallback;
}

int field_index_ci(const xbase::DbArea& area, const std::string& wanted)
{
    const std::string w = upper_copy(wanted);
    const auto& fields = area.fields();
    for (std::size_t i = 0; i < fields.size(); ++i) {
        if (upper_copy(fields[i].name) == w) {
            return static_cast<int>(i + 1);
        }
    }
    return 0;
}

bool has_memo_fields(const xbase::DbArea& area)
{
    for (const auto& f : area.fields()) {
        if (f.type == 'M' || f.type == 'm') {
            return true;
        }
    }
    return false;
}

bool is_x64_memo_field(const xbase::DbArea& area, int field1)
{
    if (field1 < 1 || field1 > area.fieldCount()) return false;
    if (area.versionByte() != xbase::DBF_VERSION_64) return false;

    const auto& f = area.fields()[static_cast<std::size_t>(field1 - 1)];
    return (f.type == 'M' || f.type == 'm') &&
           f.length == xbase::X64_MEMO_FIELD_LEN;
}

std::uint64_t parse_u64_or_zero(const std::string& s)
{
    const std::string t = trim_copy(s);
    if (t.empty()) return 0;
    try {
        std::size_t used = 0;
        const auto v = std::stoull(t, &used, 10);
        if (used != t.size()) return 0;
        return static_cast<std::uint64_t>(v);
    } catch (...) {
        return 0;
    }
}

dottalk::memo::MemoStore* memo_store_for_area(xbase::DbArea& area) noexcept
{
    auto* backend = cli_memo::memo_backend_for(area);
    if (!backend) return nullptr;
    return dynamic_cast<dottalk::memo::MemoStore*>(backend);
}

std::string field_value(xbase::DbArea& area, int field1)
{
    if (field1 <= 0) return {};
    const std::string raw = trim_copy(area.get(field1));

    if (!is_x64_memo_field(area, field1)) {
        return raw;
    }

    const std::uint64_t object_id = parse_u64_or_zero(raw);
    if (object_id == 0) {
        return {};
    }

    auto* store = memo_store_for_area(area);
    if (!store) {
        return raw;
    }

    std::string text;
    if (!store->get_text_id(object_id, text, nullptr)) {
        return raw;
    }
    return text;
}

void open_readonly_area(xbase::DbArea& area, const fs::path& path)
{
    area.open(path.string());

    std::string memo_err;
    if (!cli_memo::memo_auto_on_use(area, path.string(), has_memo_fields(area), memo_err)) {
        throw std::runtime_error(memo_err.empty() ? "memo attach failed" : memo_err);
    }
}

std::vector<ActiveMessageRow> load_messages(const fs::path& dbf_dir)
{
    xbase::DbArea area;
    open_readonly_area(area, dbf_dir / "SYSTEM_MESSAGES.dbf");

    const int f_msgid = field_index_ci(area, "MSGID");
    const int f_symbol = field_index_ci(area, "SYMBOL");
    const int f_enumname = field_index_ci(area, "ENUMNAME");
    const int f_facility = field_index_ci(area, "FACILITY");
    const int f_owner = field_index_ci(area, "OWNER");
    const int f_category = field_index_ci(area, "CATEGORY");
    const int f_severity = field_index_ci(area, "SEVERITY");
    const int f_status = field_index_ci(area, "STATUS");
    const int f_src = field_index_ci(area, "SRC");

    if (!f_msgid || !f_symbol || !f_enumname) {
        throw std::runtime_error("SYSTEM_MESSAGES required fields missing");
    }

    std::vector<ActiveMessageRow> rows;
    const std::uint64_t count = area.recCount64();
    rows.reserve(static_cast<std::size_t>(count));

    for (std::uint64_t rec = 1; rec <= count; ++rec) {
        if (!area.gotoRec(static_cast<int32_t>(rec)) || !area.readCurrent()) {
            continue;
        }
        if (area.isDeleted()) {
            continue;
        }

        rows.push_back(ActiveMessageRow{
            field_value(area, f_msgid),
            field_value(area, f_symbol),
            field_value(area, f_enumname),
            field_value(area, f_facility),
            field_value(area, f_owner),
            field_value(area, f_category),
            field_value(area, f_severity),
            field_value(area, f_status),
            field_value(area, f_src),
        });
    }

    cli_memo::memo_auto_on_close(area);
    area.close();
    return rows;
}

std::vector<ActiveTextRow> load_texts(const fs::path& dbf_dir)
{
    xbase::DbArea area;
    open_readonly_area(area, dbf_dir / "SYSTEM_MESSAGE_TEXT.dbf");

    const int f_msgid = field_index_ci(area, "MSGID");
    const int f_symbol = field_index_ci(area, "SYMBOL");
    const int f_enumname = field_index_ci(area, "ENUMNAME");
    const int f_locale = field_index_ci(area, "LOCALE");
    const int f_msglocale = field_index_ci(area, "MSGLOCALE");
    const int f_symbolloc = field_index_ci(area, "SYMBOLLOC");
    const int f_text = field_index_ci(area, "TEXT");
    const int f_txthash = field_index_ci(area, "TXTHASH");
    const int f_status = field_index_ci(area, "STATUS");
    const int f_src = field_index_ci(area, "SRC");

    if (!f_msgid || !f_symbol || !f_locale || !f_text) {
        throw std::runtime_error("SYSTEM_MESSAGE_TEXT required fields missing");
    }

    std::vector<ActiveTextRow> rows;
    const std::uint64_t count = area.recCount64();
    rows.reserve(static_cast<std::size_t>(count));

    for (std::uint64_t rec = 1; rec <= count; ++rec) {
        if (!area.gotoRec(static_cast<int32_t>(rec)) || !area.readCurrent()) {
            continue;
        }
        if (area.isDeleted()) {
            continue;
        }

        rows.push_back(ActiveTextRow{
            field_value(area, f_msgid),
            field_value(area, f_symbol),
            field_value(area, f_enumname),
            field_value(area, f_locale),
            field_value(area, f_msglocale),
            field_value(area, f_symbolloc),
            field_value(area, f_text),
            field_value(area, f_txthash),
            field_value(area, f_status),
            field_value(area, f_src),
        });
    }

    cli_memo::memo_auto_on_close(area);
    area.close();
    return rows;
}

ActiveCatalogLoad load_active_catalog()
{
    ActiveCatalogLoad load;
    load.paths = find_active_catalog_paths();

    if (!load.paths.present) {
        load.detail = "active Messaging DBF artifacts not found; compiled fallback active";
        return load;
    }

    try {
        load.messages = load_messages(load.paths.dbf_dir);
        load.texts = load_texts(load.paths.dbf_dir);

        for (const auto& row : load.texts) {
            if (!row.symbol.empty() && !row.locale.empty()) {
                load.text_by_symbol_locale[text_key(row.symbol, row.locale)] = row.text;
            }
        }

        load.loaded = true;
        load.detail = "active Messaging DBF rows loaded; compiled fallback available";
        return load;
    }
    catch (const std::exception& ex) {
        load.loaded = false;
        load.detail = std::string("active Messaging DBF row load failed; compiled fallback active: ") + ex.what();
        return load;
    }
}

std::string apply_vars(std::string out,
                       const std::unordered_map<std::string, std::string>& vars)
{
    for (const auto& kv : vars) {
        const std::string needle = "{" + kv.first + "}";
        std::string::size_type pos = 0;
        while ((pos = out.find(needle, pos)) != std::string::npos) {
            out.replace(pos, needle.size(), kv.second);
            pos += kv.second.size();
        }
    }
    return out;
}

const char* fallback_locale()
{
    return "en-US";
}

} // namespace

MessageCatalogStatus active_message_catalog_status()
{
    const auto active = load_active_catalog();

    MessageCatalogStatus status;
    status.mode = active.loaded ? MessageCatalogMode::ActiveDbf
                                : MessageCatalogMode::CompiledFallback;

    status.active_dbf_dir = generic_string(active.paths.dbf_dir);
    status.active_indexes_dir = generic_string(active.paths.indexes_dir);
    status.active_lmdb_dir = generic_string(active.paths.lmdb_dir);

    status.active_catalog_present = active.paths.present;
    status.active_catalog_loaded = active.loaded;
    status.message_count = active.loaded
        ? static_cast<int>(active.messages.size())
        : static_cast<int>(all_messages().size());
    status.text_row_count = active.loaded
        ? static_cast<int>(active.texts.size())
        : 0;
    status.detail = active.detail;
    return status;
}

std::string format_message_catalog(const std::string& locale,
                                   const std::string& symbol,
                                   const std::unordered_map<std::string, std::string>& vars)
{
    const auto active = load_active_catalog();
    if (active.loaded) {
        const std::string wanted_locale = trim_copy(locale).empty()
            ? fallback_locale()
            : trim_copy(locale);

        auto it = active.text_by_symbol_locale.find(text_key(symbol, wanted_locale));
        if (it != active.text_by_symbol_locale.end()) {
            return apply_vars(it->second, vars);
        }

        it = active.text_by_symbol_locale.find(text_key(symbol, fallback_locale()));
        if (it != active.text_by_symbol_locale.end()) {
            return apply_vars(it->second, vars);
        }
    }

    const MessageDef* message = find_message_by_key(symbol);
    if (!message || !message->text) {
        return {};
    }
    return apply_vars(message->text, vars);
}

} // namespace dottalk::helpdata
'''

CMD_SET_HELPER_BEGIN = "// MSG-022E BEGIN message catalog provider status helper"
CMD_SET_HELPER_END = "// MSG-022E END message catalog provider status helper"

CMD_SET_HELPER_REPLACEMENT = r'''// MSG-022E BEGIN message catalog provider status helper
static const char* message_catalog_mode_name(dottalk::helpdata::MessageCatalogMode mode) {
    switch (mode) {
        case dottalk::helpdata::MessageCatalogMode::ActiveDbf:
            return "active_dbf";
        case dottalk::helpdata::MessageCatalogMode::Auto:
            return "auto";
        case dottalk::helpdata::MessageCatalogMode::CompiledFallback:
        default:
            return "compiled_fallback";
    }
}

static void print_message_catalog_provider_status() {
    auto& out = cli::OutputRouter::instance().out();
    const auto status = dottalk::helpdata::active_message_catalog_status();

    out << "Message catalog provider status:\n";
    out << "  mode: " << message_catalog_mode_name(status.mode) << "\n";
    out << "  active catalog present: " << (status.active_catalog_present ? "yes" : "no") << "\n";
    out << "  active catalog loaded: " << (status.active_catalog_loaded ? "yes" : "no") << "\n";
    out << "  message count: " << status.message_count << "\n";
    out << "  text row count: " << status.text_row_count << "\n";
    out << "  active dbf dir: " << status.active_dbf_dir << "\n";
    out << "  active indexes dir: " << status.active_indexes_dir << "\n";
    out << "  active lmdb dir: " << status.active_lmdb_dir << "\n";
    out << "  detail: " << status.detail << "\n";
    out << "  boundary: read-only status/load; no DBF/CDX/LMDB mutation; no runtime writeback\n";
}
// MSG-022E END message catalog provider status helper'''

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except ValueError:
        return str(path)

def backup(path: Path, backup_root: Path, repo: Path, rows: list[dict[str, Any]]) -> None:
    if not path.exists():
        return
    dst = backup_root / rel(path, repo)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    rows.append({
        "TARGET_PATH": rel(path, repo),
        "BACKUP_PATH": rel(dst, repo),
        "BYTES": dst.stat().st_size,
        "SHA256": sha256_file(dst),
        "ROLE": "pre_patch_source_backup",
    })

def replace_between(text: str, begin: str, end: str, replacement: str) -> str:
    b = text.find(begin)
    e = text.find(end)
    if b < 0 or e < 0 or e < b:
        raise RuntimeError(f"marker block not found: {begin} ... {end}")
    e += len(end)
    return text[:b] + replacement + text[e:]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22e = first_row(reports / "message_catalog_phase22e_runtime_status_summary_v1.csv")
    messages = p22e.get("MESSAGES", "12")
    text_rows = p22e.get("TEXT_ROWS", "60")
    locales = p22e.get("LOCALES", "de;en-US;es;fr;it")

    provider_cpp = repo / "src/help/message_catalog.cpp"
    cmd_set = repo / "src/cli/cmd_set.cpp"

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22E_STATUS_SMOKE_GREEN",
         p22e.get("STATUS") == "MESSAGE_CATALOG_PHASE22E_RUNTIME_PROVIDER_STATUS_SMOKE_GREEN",
         p22e.get("STATUS", ""))
    gate("MESSAGE_CATALOG_CPP_PRESENT", provider_cpp.exists(), rel(provider_cpp, repo))
    gate("CMD_SET_CPP_PRESENT", cmd_set.exists(), rel(cmd_set, repo))
    gate("ACTIVE_MESSAGES_DBF_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
    gate("ACTIVE_MESSAGE_TEXT_DBF_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
    gate("ACTIVE_MESSAGE_TEXT_DTX_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dtx").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dtx")

    backup_rows: list[dict[str, Any]] = []
    mutation_rows: list[dict[str, Any]] = []
    status = STATUS_BLOCKED

    if failures == 0:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022F_ACTIVE_DBF_LOADER_BACKUP_{timestamp}"

        backup(provider_cpp, backup_root, repo, backup_rows)
        backup(cmd_set, backup_root, repo, backup_rows)

        provider_cpp.write_text(MESSAGE_CATALOG_CPP, encoding="utf-8")
        mutation_rows.append({
            "TARGET_PATH": rel(provider_cpp, repo),
            "ACTION": "REPLACE",
            "BYTES": provider_cpp.stat().st_size,
            "SHA256": sha256_file(provider_cpp),
            "DETAIL": "replaced provider with active DBF row-load implementation using xbase DbArea and memo_auto_on_use",
        })

        cmd_text = cmd_set.read_text(encoding="utf-8", errors="replace")
        cmd_text = replace_between(cmd_text, CMD_SET_HELPER_BEGIN, CMD_SET_HELPER_END, CMD_SET_HELPER_REPLACEMENT)
        cmd_set.write_text(cmd_text, encoding="utf-8")
        mutation_rows.append({
            "TARGET_PATH": rel(cmd_set, repo),
            "ACTION": "UPDATE",
            "BYTES": cmd_set.stat().st_size,
            "SHA256": sha256_file(cmd_set),
            "DETAIL": "updated SET MESSAGE CATALOG CHECK status output for active DBF load state and text row count",
        })

        status = STATUS_GREEN

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22f_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "ACTIVE_DBF_ROW_LOAD_PROVIDER_APPLIED": 1 if status == STATUS_GREEN else 0,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "ACTIVE_DBF_ROW_LOAD_PROVIDER_APPLIED", "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22f_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22f_source_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22f_source_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to message_catalog.cpp active DBF loader and cmd_set.cpp status output."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Provider reads active DBFs only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22f_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    smoke = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22F_ACTIVE_DBF_LOAD_SMOKE.dts"
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text("\n".join([
        "* MESSAGE_CATALOG_PHASE22F_ACTIVE_DBF_LOAD_SMOKE.dts",
        "* Runtime-visible active DBF row-load provider smoke.",
        "* Expected: active catalog loaded yes; message count 12; text row count 60.",
        "SET MESSAGE CATALOG CHECK",
        "",
    ]), encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len(mutation_rows)}")
    print(f"  source backup rows: {len(backup_rows)}")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
