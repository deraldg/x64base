// ============================================================================
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


// MSG-022S1 BEGIN shared routing proof lane state
namespace {
bool& message_routing_proof_flag()
{
    static bool enabled = false;
    return enabled;
}
} // namespace

bool message_routing_proof_enabled()
{
    return message_routing_proof_flag();
}

void set_message_routing_proof_enabled(bool enabled)
{
    message_routing_proof_flag() = enabled;
}
// MSG-022S1 END shared routing proof lane state
} // namespace dottalk::helpdata
