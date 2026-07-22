// src/cli/cmd_table_buffer.cpp
// @dottalk.usage v1
// owner: DOT|TABLE_BUFFER
// command: TABLE_BUFFER
// category: table-buffer
// status: supported
// noargs: report
// effect: mixed
// mutates: session-buffer-state
// usage-access: TABLE_BUFFER USAGE
// summary:
//   Inspect or change per-area table-buffer state.
// usage:
//   TABLE_BUFFER
//   TABLE_BUFFER USAGE
//   TABLE_BUFFER STATUS [ALL]
//   TABLE_BUFFER BUFFER ON|OFF|DIRTY|CLEAN|STALE|FRESH|STATUS|DUMP|TESTADD|RESET
// notes:
//   No arguments reports current buffer state. State-changing subcommands mutate session buffer metadata.
// related:
//   COMMIT, ROLLBACK, TABLE
//
#include "cli/table_buffer.hpp"

#include <algorithm>
#include <cctype>
#include <climits>
#include <cstdlib>
#include <iostream>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "cli/command_output.hpp"
#include "cli/table_state.hpp"
#include "help/helpdata_messages.hpp"
#include "xbase.hpp"

extern "C" xbase::XBaseEngine* shell_engine();

using namespace dottalk::table;

namespace {

// ---- Helpers ---------------------------------------------------------------

static inline std::string trim_copy(std::string s) {
    auto is_space = [](unsigned char ch) { return std::isspace(ch) != 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(),
                                    [&](unsigned char c) { return !is_space(c); }));
    s.erase(std::find_if(s.rbegin(), s.rend(),
                         [&](unsigned char c) { return !is_space(c); }).base(),
            s.end());
    return s;
}

static inline std::string to_lower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return (char)std::tolower(c); });
    return s;
}

static inline bool try_parse_int(const std::string& s, int& out) {
    if (s.empty()) return false;
    char* end = nullptr;
    long v = std::strtol(s.c_str(), &end, 10);
    if (end == s.c_str() || *end != '\0') return false;
    if (v < INT_MIN || v > INT_MAX) return false;
    out = (int)v;
    return true;
}

static std::vector<std::string> split_tokens(const std::string& s) {
    std::vector<std::string> out;
    std::string cur;
    for (char c : s) {
        if (c == ',' || std::isspace((unsigned char)c)) {
            if (!cur.empty()) {
                out.push_back(trim_copy(cur));
                cur.clear();
            }
        } else {
            cur.push_back(c);
        }
    }
    if (!cur.empty()) out.push_back(trim_copy(cur));
    out.erase(std::remove_if(out.begin(), out.end(),
                             [](const std::string& t) { return t.empty(); }),
              out.end());
    return out;
}

static inline std::string basename(const std::string& path) {
    size_t p1 = path.find_last_of('\\');
    size_t p2 = path.find_last_of('/');
    size_t p = std::string::npos;
    if (p1 != std::string::npos) p = p1;
    if (p2 != std::string::npos) p = (p == std::string::npos) ? p2 : std::max(p, p2);
    if (p == std::string::npos) return path;
    return path.substr(p + 1);
}

static std::vector<int> parse_area_targets(const std::string& rest) {
    std::vector<int> out;
    std::string r = trim_copy(rest);
    if (r.empty()) return out;

    if (to_lower(r) == "all") {
        out.reserve(xbase::MAX_AREA);
        for (int i = 0; i < xbase::MAX_AREA; ++i) out.push_back(i);
        return out;
    }

    for (const auto& tok : split_tokens(r)) {
        int n = -1;
        if (try_parse_int(tok, n)) out.push_back(n);
    }
    return out;
}

static size_t unique_recnos_in_tb(const TableBuffer& tb) {
    std::set<std::uint64_t> recnos;
    for (const auto& pair : tb.changes) {
        recnos.insert(pair.first);
    }
    return recnos.size();
}

static const char* persistence_label(int area0) {
    return is_persistent_enabled(area0) ? "RAM+JOURNAL" : "RAM";
}

static bool has_token_ci(const std::vector<std::string>& toks, const std::string& needle_lower) {
    for (const auto& t : toks) {
        if (to_lower(t) == needle_lower) return true;
    }
    return false;
}

static std::string remove_persistence_tokens(const std::vector<std::string>& toks) {
    std::string out;
    bool first = true;
    for (const auto& t : toks) {
        const std::string lt = to_lower(t);
        if (lt == "persistent" || lt == "persist" || lt == "journal" || lt == "ram") {
            continue;
        }
        if (!first) out += " ";
        out += t;
        first = false;
    }
    return out;
}

static std::string stale_fields_string_for_area(xbase::DbArea& A, int area0) {
    std::vector<int> fields1;
    if (!get_stale_fields(area0, fields1)) return {};
    if (fields1.empty()) return {};

    std::string out;
    try {
        const auto defs = A.fields();
        bool first = true;
        for (int f1 : fields1) {
            const std::size_t idx0 = static_cast<std::size_t>(f1 - 1);
            if (idx0 >= defs.size()) continue;

            if (!first) out += ",";
            out += defs[idx0].name;
            first = false;

            if (out.size() > 120) {
                out += ",...";
                break;
            }
        }
    } catch (...) {
        out = "(fields?)";
    }

    if (out.empty()) return {};
    return std::string(" [") + out + "]";
}

static int resolve_current_index(xbase::DbArea& A) {
    xbase::XBaseEngine* eng = shell_engine();
    if (!eng) return -1;

    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (&eng->area(i) == &A) return i;
    }
    return -1;
}

static std::vector<int> default_current_target(xbase::DbArea& current) {
    auto* eng = shell_engine();
    if (!eng) return {};

    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (&eng->area(i) == &current) return {i};
    }
    return {};
}

// ---- Display Functions -----------------------------------------------------

static void table_show(bool show_all_slots) {
    auto* eng = shell_engine();
    if (!eng) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::SetTableBufferEngineUnavailableText);
        return;
    }

    const int enabled = count_enabled();
    const int dirty = count_dirty();
    const int stale = count_stale();

    if (show_all_slots) {
        cli::cmdout::print_prefixed_message(
            "TABLE BUFFER",
            dottalk::helpdata::MessageId::TableBufferAreasAllTitleText,
            {{"last", std::to_string(xbase::MAX_AREA - 1)}});
    } else {
        cli::cmdout::print_prefixed_message(
            "TABLE BUFFER",
            dottalk::helpdata::MessageId::TableBufferOccupiedAreasTitleText);
    }
    std::cout << "  enabled=" << enabled << " dirty=" << dirty << " stale=" << stale << "\n";

    int shown = 0;

    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        xbase::DbArea& A = eng->area(i);
        const std::string dbf = A.filename();
        const bool open = !dbf.empty();

        if (!show_all_slots && !open) continue;

        const bool en = is_enabled(i);
        const bool di = is_dirty(i);
        const bool st = is_stale(i);

        std::string staleFields;
        if (open && st) staleFields = stale_fields_string_for_area(A, i);

        std::cout << "  Area " << i << ": "
                  << (open ? ("DBF=" + basename(dbf)) : std::string("(no file)"))
                  << " | buffer=" << (en ? "ON" : "OFF")
                  << " | mode=" << persistence_label(i)
                  << " | " << (di ? "DIRTY" : "clean")
                  << " | " << (st ? "STALE" : "fresh")
                  << staleFields;

        const auto& tb = get_tb_const(i);
        if (!tb.empty()) {
            std::cout << " | rows: " << tb.changes.size()
                      << " changes (" << unique_recnos_in_tb(tb) << " recnos)";
        }

        std::cout << "\n";
        ++shown;
    }

    if (!show_all_slots && shown == 0) {
        std::cout << "  (no open tables)\n";
    }
}

// ---- State Mutation Helpers ------------------------------------------------

static int apply_one(int area0, const std::string& verb, bool value) {
    if (!in_range(area0)) return 0;

    int changed = 0;

    if (verb == "enabled") {
        const bool old = is_enabled(area0);
        if (old != value) {
            set_enabled(area0, value);
            changed = 1;
        }
    } else if (verb == "dirty") {
        const bool old = is_dirty(area0);
        if (old != value) {
            set_dirty(area0, value);
            changed = 1;
        }
    } else if (verb == "stale") {
        const bool old = is_stale(area0);
        if (old != value) {
            set_stale(area0, value);
            changed = 1;
        }
    } else if (verb == "history") {
        const bool old = is_history_enabled(area0);
        if (old != value) {
            set_history_enabled(area0, value);
            changed = 1;
        }
    }

    return changed;
}

static void apply_to_targets(const std::vector<int>& targets,
                             const std::string& verb, bool value) {
    int changed = 0;
    for (int a : targets) {
        changed += apply_one(a, verb, value);
    }
    cli::cmdout::print_prefixed_message(
        "TABLE BUFFER",
        dottalk::helpdata::MessageId::TableBufferAreasUpdatedText,
        {{"count", std::to_string(changed)}});
}

// The redo log is a sidecar of the DBF (`<dbf>.tbj`), so recovery-on-open can
// find it from the table's filename. Look it up from the engine's area slot.
static std::string area_dbf_filename(int area0) {
    auto* eng = shell_engine();
    if (!eng || !in_range(area0)) return {};
    try { return eng->area(area0).filename(); } catch (...) { return {}; }
}

static void apply_persistence_to_targets(const std::vector<int>& targets,
                                         BufferPersistenceMode mode) {
    int changed = 0;
    for (int a : targets) {
        if (!in_range(a)) continue;
        if (persistence_mode(a) != mode) {
            set_persistence_mode(a, mode);
            ++changed;
        }
        if (mode == BufferPersistenceMode::RamJournal) {
            (void)journal_note_buffer_on(a, area_dbf_filename(a));
        }
    }

    cli::cmdout::print_prefixed_message(
        "TABLE BUFFER",
        dottalk::helpdata::MessageId::TableBufferPersistenceUpdatedText,
        {{"count", std::to_string(changed)}});
}

static void apply_to_open_areas(const std::string& verb, bool value) {
    auto* eng = shell_engine();
    if (!eng) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::SetTableBufferEngineUnavailableText);
        return;
    }

    int changed = 0;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        xbase::DbArea& A = eng->area(i);
        if (A.filename().empty()) continue;
        changed += apply_one(i, verb, value);
    }
    cli::cmdout::print_prefixed_message(
        "TABLE BUFFER",
        dottalk::helpdata::MessageId::TableBufferAreasUpdatedText,
        {{"count", std::to_string(changed)}});
}

// ---- BUFFER STATUS / DUMP / TESTADD ----------------------------------------

static void table_buffer_status(int area0) {
    if (!in_range(area0)) {
        cli::cmdout::print_prefixed_message(
            "TABLE BUFFER",
            dottalk::helpdata::MessageId::TableBufferInvalidAreaText);
        return;
    }

    const auto& tb = get_tb_const(area0);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::TableBufferStatusHeaderText,
        {{"area", std::to_string(area0)}});
    std::cout << "  mode: " << persistence_label(area0) << "\n";
    if (is_persistent_enabled(area0)) {
        const std::string jp = journal_path(area0);
        std::cout << "  journal: " << (jp.empty() ? "(stub: not opened yet)" : jp) << "\n";
    }
    std::cout << "  empty: " << (tb.empty() ? "yes" : "no") << "\n";
    std::cout << "  changes: " << tb.changes.size() << "\n";
    std::cout << "  unique recnos: " << unique_recnos_in_tb(tb) << "\n";
    std::cout << "  next_seq: " << tb.next_priority << "\n";
}

static void table_buffer_dump(int area0) {
    if (!in_range(area0)) {
        cli::cmdout::print_prefixed_message(
            "TABLE BUFFER",
            dottalk::helpdata::MessageId::TableBufferInvalidAreaText);
        return;
    }

    const auto& tb = get_tb_const(area0);
    if (tb.empty()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::TableBufferEmptyBufferText,
            {{"area", std::to_string(area0)}});
        return;
    }

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::TableBufferDumpHeaderText,
        {{"area", std::to_string(area0)}});
    for (const auto& pair : tb.changes) {
        const auto& entry = pair.second;
        std::cout << "  recno=" << entry.recno
                  << " seq=" << entry.priority
                  << " flags=0x" << std::hex << entry.dirty_flags << std::dec;

        bool any_field = false;
        for (int w = 0; w < kWords; ++w) {
            if (entry.field_bits[w] != 0) {
                any_field = true;
                break;
            }
        }
        if (any_field) std::cout << " (fields changed)";

        if (!entry.new_values.empty()) {
            std::cout << " values:";
            for (const auto& [f, v] : entry.new_values) {
                std::cout << " #" << f << "=\"" << v << "\"";
            }
        }
        std::cout << "\n";
    }
}

static void table_buffer_testadd(const std::string& arg, xbase::DbArea& current_area) {
    if (arg.empty()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::TableBufferTestAddUsageText);
        return;
    }

    std::string work = arg;
    const size_t comment_pos = work.find("//");
    if (comment_pos != std::string::npos) {
        work = work.substr(0, comment_pos);
    }
    work = trim_copy(work);

    std::istringstream iss(work);
    int recno = -1;
    iss >> recno;
    if (recno < 1) {
        cli::cmdout::print_prefixed_message(
            "TABLE BUFFER",
            dottalk::helpdata::MessageId::TableBufferInvalidRecnoText);
        return;
    }

    std::uint64_t flags = CHANGE_UPDATE;
    int field1 = 0;
    std::string value;
    std::string token;

    if (iss >> token) {
        int f = 0;
        if (try_parse_int(token, f)) {
            flags = static_cast<std::uint64_t>(f);
        } else {
            value = token;
        }
    }

    if (iss >> token) {
        int f = 0;
        if (try_parse_int(token, f)) {
            field1 = f;
        } else {
            value = token;
        }
    }

    std::getline(iss, token);
    if (!token.empty()) {
        value = trim_copy(token);
    }

    std::cout << "Parsed: recno=" << recno
              << ", flags=0x" << std::hex << flags << std::dec
              << ", field1=" << field1
              << ", value='" << value << "'\n";

    const int curr = resolve_current_index(current_area);
    if (curr < 0 || !is_enabled(curr)) {
        cli::cmdout::print_prefixed_message(
            "TABLE BUFFER",
            dottalk::helpdata::MessageId::TableBufferNoCurrentEnabledAreaText);
        return;
    }

    test_add_change(curr, recno, flags, field1, value);
}

static void table_buffer_dispatch(const std::string& rest, xbase::DbArea& current_area) {
    const std::string r = trim_copy(rest);
    if (r.empty()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::TableBufferUsageText);
        return;
    }

    const auto toks = split_tokens(r);
    if (toks.empty()) return;

    const std::string sub = to_lower(toks[0]);
    const std::string arg = (toks.size() > 1) ? trim_copy(r.substr(toks[0].size())) : "";

    if (sub == "status") {
        if (to_lower(arg) == "all") {
            for (int i = 0; i < xbase::MAX_AREA; ++i) {
                if (!is_enabled(i)) continue;
                table_buffer_status(i);
            }
        } else if (arg.empty()) {
            const int curr = resolve_current_index(current_area);
            if (curr >= 0 && is_enabled(curr)) {
                table_buffer_status(curr);
            } else {
                cli::cmdout::print_prefixed_message(
                    "TABLE BUFFER",
                    dottalk::helpdata::MessageId::TableBufferNoCurrentAreaSelectedOrEnabledText);
            }
        } else {
            int a = -1;
            if (try_parse_int(arg, a)) table_buffer_status(a);
            else {
                cli::cmdout::print_prefixed_message(
                    "TABLE BUFFER",
                    dottalk::helpdata::MessageId::TableBufferInvalidAreaText);
            }
        }
        return;
    }

    if (sub == "dump") {
        if (to_lower(arg) == "all") {
            for (int i = 0; i < xbase::MAX_AREA; ++i) {
                if (!is_enabled(i)) continue;
                table_buffer_dump(i);
            }
        } else if (arg.empty()) {
            const int curr = resolve_current_index(current_area);
            if (curr >= 0 && is_enabled(curr)) {
                table_buffer_dump(curr);
            } else {
                cli::cmdout::print_prefixed_message(
                    "TABLE BUFFER",
                    dottalk::helpdata::MessageId::TableBufferNoCurrentAreaSelectedOrEnabledText);
            }
        } else {
            int a = -1;
            if (try_parse_int(arg, a)) table_buffer_dump(a);
            else {
                cli::cmdout::print_prefixed_message(
                    "TABLE BUFFER",
                    dottalk::helpdata::MessageId::TableBufferInvalidAreaText);
            }
        }
        return;
    }

    if (sub == "testadd") {
        table_buffer_testadd(arg, current_area);
        return;
    }

    if (sub == "persistent" || sub == "persist" || sub == "journal") {
        std::string mode_tok;
        std::string target_text;

        if (toks.size() >= 2) {
            mode_tok = to_lower(toks[1]);
        }

        std::size_t target_start = 1;
        BufferPersistenceMode mode = BufferPersistenceMode::RamJournal;

        if (mode_tok == "on" || mode_tok == "yes" || mode_tok == "true" || mode_tok == "journal") {
            mode = BufferPersistenceMode::RamJournal;
            target_start = 2;
        } else if (mode_tok == "off" || mode_tok == "no" || mode_tok == "false" || mode_tok == "ram") {
            mode = BufferPersistenceMode::RamOnly;
            target_start = 2;
        }

        for (std::size_t i = target_start; i < toks.size(); ++i) {
            if (!target_text.empty()) target_text += " ";
            target_text += toks[i];
        }

        auto targets = parse_area_targets(target_text);
        if (targets.empty() && to_lower(target_text) != "all") {
            targets = default_current_target(current_area);
            if (targets.empty()) {
                cli::cmdout::print_prefixed_message(
                    "TABLE BUFFER",
                    dottalk::helpdata::MessageId::TableBufferCannotDetermineCurrentAreaSpecifyText);
                return;
            }
        }

        apply_persistence_to_targets(targets, mode);
        return;
    }

    if (sub == "reset") {
        reset_all();
        cli::cmdout::print_prefixed_message(
            "TABLE BUFFER",
            dottalk::helpdata::MessageId::TableBufferResetAllText);
        return;
    }

    if (sub == "history") {
        // TABLE BUFFER HISTORY ON|OFF [<areas>] -- toggle multiple-retained-
        // edits-per-field (history) mode vs single last-write-wins.
        std::string mode_tok;
        if (toks.size() >= 2) mode_tok = to_lower(toks[1]);
        bool value = true;
        std::size_t target_start = 1;
        if (mode_tok == "off" || mode_tok == "no" || mode_tok == "false" ||
            mode_tok == "disable" || mode_tok == "disabled") {
            value = false; target_start = 2;
        } else if (mode_tok == "on" || mode_tok == "yes" || mode_tok == "true" ||
                   mode_tok == "enable" || mode_tok == "enabled") {
            value = true; target_start = 2;
        }

        std::string target_text;
        for (std::size_t i = target_start; i < toks.size(); ++i) {
            if (!target_text.empty()) target_text += " ";
            target_text += toks[i];
        }
        auto htargets = parse_area_targets(target_text);
        if (htargets.empty() && to_lower(target_text) != "all") {
            htargets = default_current_target(current_area);
        }
        apply_to_targets(htargets, "history", value);
        return;
    }

    auto targets = parse_area_targets(arg);
    if (targets.empty() && to_lower(arg) != "all") {
        targets = default_current_target(current_area);
        if (targets.empty()) {
            cli::cmdout::print_prefixed_message(
                "TABLE BUFFER",
                dottalk::helpdata::MessageId::TableBufferCannotDetermineCurrentAreaSpecifyText);
            return;
        }
    }

    if (sub == "on" || sub == "enable" || sub == "enabled") {
        const bool wants_persistent =
            has_token_ci(toks, "persistent") ||
            has_token_ci(toks, "persist") ||
            has_token_ci(toks, "journal");
        const bool wants_ram = has_token_ci(toks, "ram");

        if (wants_persistent || wants_ram) {
            const std::string target_text = remove_persistence_tokens(
                std::vector<std::string>(toks.begin() + 1, toks.end()));
            targets = parse_area_targets(target_text);
            if (targets.empty() && to_lower(target_text) != "all") {
                targets = default_current_target(current_area);
                if (targets.empty()) {
                    cli::cmdout::print_prefixed_message(
                        "TABLE BUFFER",
                        dottalk::helpdata::MessageId::TableBufferCannotDetermineCurrentAreaSpecifyText);
                    return;
                }
            }

            apply_persistence_to_targets(
                targets,
                wants_persistent ? BufferPersistenceMode::RamJournal
                                 : BufferPersistenceMode::RamOnly);
        }

        apply_to_targets(targets, "enabled", true);

        for (int a : targets) {
            if (is_persistent_enabled(a)) {
                (void)journal_note_buffer_on(a, area_dbf_filename(a));
            }
        }
        return;
    }
    if (sub == "off" || sub == "disable" || sub == "disabled") {
        apply_to_targets(targets, "enabled", false);
        return;
    }
    if (sub == "dirty") {
        apply_to_targets(targets, "dirty", true);
        return;
    }
    if (sub == "clean" || sub == "clear") {
        apply_to_targets(targets, "dirty", false);
        return;
    }
    if (sub == "stale") {
        apply_to_targets(targets, "stale", true);
        return;
    }
    if (sub == "fresh" || sub == "clearstale" || sub == "unstale") {
        apply_to_targets(targets, "stale", false);
        return;
    }

    cli::cmdout::print_prefixed_message(
        "TABLE BUFFER",
        dottalk::helpdata::MessageId::TableBufferUnknownSubcommandText,
        {{"subcommand", sub}});
}

static void show_usage() {
    cli::cmdout::print_message(dottalk::helpdata::MessageId::TableBufferUsageText);
}

} // namespace

void cmd_TABLE_BUFFER(xbase::DbArea& current, std::istringstream& in) {
    std::string arg_line;
    std::getline(in, arg_line);
    const std::string args = trim_copy(arg_line);

    if (!args.empty()) {
        const auto toks = split_tokens(args);
        if (!toks.empty() && to_lower(toks[0]) == "tables") {
            const bool show_all_slots = (toks.size() > 1 && to_lower(toks[1]) == "all");
            table_show(show_all_slots);
            return;
        }
    }

    if (args.empty()) {
        table_show(false);
        return;
    }

    std::string sub, rest;
    const auto sp = args.find_first_of(" \t");
    if (sp == std::string::npos) {
        sub = args;
        rest = "";
    } else {
        sub = args.substr(0, sp);
        rest = trim_copy(args.substr(sp));
    }
    sub = to_lower(sub);

    if (sub == "usage" || sub == "help" || sub == "?") {
        show_usage();
        return;
    }

    if (sub == "all") {
        table_show(true);
        return;
    }

    if (sub == "status" || sub == "show" || sub == "list" || sub == "s") {
        const bool show_all_slots = (to_lower(trim_copy(rest)) == "all");
        table_show(show_all_slots);
        return;
    }

    // Preferred explicit form:
    //   TABLE BUFFER ON|OFF|DIRTY|CLEAN|STALE|FRESH|STATUS|DUMP|TESTADD|RESET
    if (sub == "buffer") {
        table_buffer_dispatch(rest, current);
        return;
    }

    // Legacy compatibility path
    auto* eng = shell_engine();
    if (!eng) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::SetTableBufferEngineUnavailableText);
        return;
    }

    if (sub == "onall") {
        apply_to_open_areas("enabled", true);
        return;
    }
    if (sub == "offall") {
        apply_to_open_areas("enabled", false);
        return;
    }
    if (sub == "dirtyall") {
        apply_to_open_areas("dirty", true);
        return;
    }
    if (sub == "cleanall" || sub == "clearall") {
        apply_to_open_areas("dirty", false);
        return;
    }
    if (sub == "staleall") {
        apply_to_open_areas("stale", true);
        return;
    }
    if (sub == "freshall" || sub == "clearstaleall" || sub == "unstaleall") {
        apply_to_open_areas("stale", false);
        return;
    }

    if (sub == "history") {
        // TABLE BUFFER HISTORY ON|OFF [<areas>]  -- toggle multiple-retained-
        // edits-per-field (history) mode vs single last-write-wins.
        std::string tail = trim_copy(rest);
        std::string first_tok;
        const auto sp2 = tail.find_first_of(" \t");
        if (sp2 == std::string::npos) { first_tok = tail; tail.clear(); }
        else { first_tok = tail.substr(0, sp2); tail = trim_copy(tail.substr(sp2)); }

        const std::string lw = to_lower(first_tok);
        bool value = true;
        if (lw == "off" || lw == "no" || lw == "false" || lw == "disable" || lw == "disabled") {
            value = false;
        } else if (lw == "on" || lw == "yes" || lw == "true" || lw == "enable" || lw == "enabled") {
            value = true;
        } else {
            // No explicit ON/OFF token: treat the whole tail as the area spec and
            // default to enabling history mode.
            tail = trim_copy(rest);
            value = true;
        }

        auto htargets = parse_area_targets(tail);
        if (htargets.empty() && to_lower(tail) != "all") {
            htargets = default_current_target(current);
        }
        apply_to_targets(htargets, "history", value);
        return;
    }

    auto targets = parse_area_targets(rest);
    if (targets.empty() && to_lower(rest) != "all") {
        targets = default_current_target(current);
        if (targets.empty()) {
            cli::cmdout::print_prefixed_message(
                "TABLE BUFFER",
                dottalk::helpdata::MessageId::TableBufferCannotDetermineCurrentAreaSpecifyText);
            return;
        }
    }

    if (sub == "on" || sub == "enable" || sub == "enabled") {
        apply_to_targets(targets, "enabled", true);
    } else if (sub == "off" || sub == "disable" || sub == "disabled") {
        apply_to_targets(targets, "enabled", false);
    } else if (sub == "dirty") {
        apply_to_targets(targets, "dirty", true);
    } else if (sub == "clean" || sub == "clear") {
        apply_to_targets(targets, "dirty", false);
    } else if (sub == "stale") {
        apply_to_targets(targets, "stale", true);
    } else if (sub == "fresh" || sub == "clearstale" || sub == "unstale") {
        apply_to_targets(targets, "stale", false);
    } else if (sub == "reset") {
        reset_all();
        cli::cmdout::print_prefixed_message(
            "TABLE BUFFER",
            dottalk::helpdata::MessageId::TableBufferResetAllText);
    } else {
        cli::cmdout::print_prefixed_message(
            "TABLE BUFFER",
            dottalk::helpdata::MessageId::TableBufferUnknownSubcommandText,
            {{"subcommand", sub}});
        show_usage();
    }
}
