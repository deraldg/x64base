// src/cli/cmd_close.cpp
// @dottalk.usage v1
// owner: DOT|CLOSE
// command: CLOSE
// category: workspace
// status: supported
// noargs: mutate
// effect: close
// mutates: session area memo order table-buffer relations
// usage-access: CLOSE USAGE
// summary:
//   Close the current work area, honoring dirty table-buffer prompts,
//   clearing memo/order/table slot state, and clearing affected relation state.
//
// usage:
//   CLOSE USAGE
//   CLOSE
//   CLOSE ALL
//
// notes:
//   CLOSE with no arguments closes the current work area.
//   CLOSE ALL clears all relations and closes every open work area.
//   CLOSE prompts or cancels through dirty table-buffer protection when needed.
//   CLOSE runs memo sidecar lifecycle hooks before clearing area identity.
//   CLOSE clears active order/index state.
//   CLOSE resets table buffering state for the slot to off, clean, and fresh.
//   CLOSE is a session/area mutation command; it does not directly mutate table records.
//
// risk:
//   closes_area: yes
//   clears_order_state: yes
//   closes_memo_backend: yes
//   resets_table_buffer_state: yes
//   clears_relations_for_table: yes
//   clears_all_relations: CLOSE ALL
//   dirty_prompt_gate: yes
//   mutates_table_data: no
//
// related:
//   USE
//   WORKSPACE
//   TABLE
//   COMMIT
//   REL
//

#include <sstream>
#include <iostream>
#include <string>
#include <filesystem>
#include <cctype>
#include <vector>

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "cli/dirty_prompt.hpp"
#include "cli/order_state.hpp"   // orderstate::clearOrder
#include "memo/memo_manager.hpp"
#include "memo/memo_auto.hpp"   // cli_memo::memo_auto_on_close
#include "cli/table_state.hpp"   // dottalk::table::set_enabled/dirty/stale

#if __has_include("set_relations.hpp")
  #include "set_relations.hpp"   // relations_api::export_relations / import_relations / clear_all_relations
  #define HAVE_RELATIONS 1
#else
  #define HAVE_RELATIONS 0
#endif

namespace fs = std::filesystem;

// Provided by the interactive shell.
extern "C" xbase::XBaseEngine* shell_engine(void);

namespace {

static int area_index_from_ref(xbase::DbArea& areaRef) {
    xbase::XBaseEngine* eng = nullptr;
    try { eng = shell_engine(); } catch (...) { eng = nullptr; }
    if (!eng) return -1;

    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        try {
            if (&(eng->area(i)) == &areaRef) return i;
        } catch (...) {
            // ignore and keep scanning
        }
    }
    return -1;
}

static inline void clear_table_slot_state(xbase::DbArea& areaRef) {
    const int slot = area_index_from_ref(areaRef);
    if (slot < 0) return;

    dottalk::table::set_enabled(slot, false);
    dottalk::table::set_dirty(slot, false);
    dottalk::table::set_stale(slot, false);
}

} // namespace

#if HAVE_RELATIONS
static inline std::string up_copy(std::string s)
{
    for (auto& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

static std::string close_table_key(const xbase::DbArea& a)
{
    // Prefer logical name because REL commands use logical names.
    std::string ln = a.logicalName();
    if (!ln.empty()) return ln;

    // Fallback: legacy name() if present/used as alias in your build.
    try {
        std::string nm = a.name();
        if (!nm.empty()) return nm;
    } catch (...) {}

    // Final fallback: stem of filename
    try {
        fs::path p(a.filename());
        if (!p.empty()) return p.stem().string();
    } catch (...) {}

    return {};
}

static void clear_relations_involving_table(const xbase::DbArea& a)
{
    const std::string key = up_copy(close_table_key(a));
    if (key.empty()) return;

    const auto all = relations_api::export_relations();

    std::vector<relations_api::RelationSpec> keep;
    keep.reserve(all.size());

    for (const auto& r : all) {
        const std::string p = up_copy(r.parent);
        const std::string c = up_copy(r.child);

        if (p == key || c == key) continue;
        keep.push_back(r);
    }

    if (keep.size() == all.size()) return;

    relations_api::import_relations(keep, /*clear_existing=*/true);

    try {
        const std::string cur = up_copy(relations_api::current_parent_name());
        if (cur == key) relations_api::set_current_parent_name(std::string{});
    } catch (...) {}
}
#endif // HAVE_RELATIONS


static std::string close_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static bool is_close_usage_request(std::string raw)
{
    std::string t = close_trim(std::move(raw));
    for (char& ch : t) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    if (t.rfind("CLOSE ", 0) == 0) t = close_trim(t.substr(6));
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_close_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::CloseUsageText);
}

// Close a single work area: memo lifecycle hooks, order/index detach, the
// actual close, and slot-state reset. Relation clearing is handled by the
// caller because single-area CLOSE and CLOSE ALL differ there.
static void close_one_area(xbase::DbArea& area)
{
    // Memo sidecar lifecycle hook. The live DTX backend is owned by
    // memo_auto.cpp, not MemoManager. Close it before DbArea::close() clears
    // area identity so ERASE can delete the .dtx sidecar immediately after.
    try { cli_memo::memo_auto_on_close(area); } catch (...) {}

    if (auto* mm = area.memoManagerPtr()) {
        mm->close();
    }

    try { orderstate::clearOrder(area); } catch (...) {}
    try { area.close(); } catch (...) {}
    try { area.setFilename(""); } catch (...) {}

    // RULE: closing a DBF resets TABLE state for that slot (OFF + clean + fresh)
    clear_table_slot_state(area);
}

void cmd_CLOSE(xbase::DbArea& a, std::istringstream& iss)
{
    const std::string raw_args = iss.str();
    if (is_close_usage_request(raw_args)) {
        print_close_usage();
        return;
    }

    // Parse the optional argument first so CLOSE ALL can fan out over every
    // OPEN work area, not just the current one.
    std::string arg;
    iss >> arg;
    std::string argU = arg;
    for (char& ch : argU) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    const bool close_all = (argU == "ALL");

    if (close_all) {
#if HAVE_RELATIONS
        relations_api::clear_all_relations();
#endif
        xbase::XBaseEngine* eng = nullptr;
        try { eng = shell_engine(); } catch (...) { eng = nullptr; }

        if (eng) {
            for (int i = 0; i < xbase::MAX_AREA; ++i) {
                xbase::DbArea* areap = nullptr;
                try { areap = &eng->area(i); } catch (...) { areap = nullptr; }
                if (!areap) continue;

                // "Open truth" in this codebase is a non-empty filename() (the
                // same test WORKSPACE uses to enumerate open areas), so match it.
                bool is_open = false;
                try { is_open = !areap->filename().empty(); } catch (...) { is_open = false; }
                if (!is_open) continue;

                // Honor the dirty table-buffer gate per area; skip (leave open)
                // any area whose prompt the user cancels.
                if (!dottalk::dirty::maybe_prompt_area(*areap, "CLOSE")) continue;

                close_one_area(*areap);
            }
        } else {
            // No engine handle: fall back to closing just the current area.
            if (dottalk::dirty::maybe_prompt_area(a, "CLOSE")) {
                close_one_area(a);
            }
        }

        cli::cmdout::print_message(dottalk::helpdata::MessageId::CloseCompletedText);
        return;
    }

    // Single-area CLOSE.
    if (!dottalk::dirty::maybe_prompt_area(a, "CLOSE")) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CloseCanceledText);
        return;
    }

#if HAVE_RELATIONS
    clear_relations_involving_table(a);
#endif

    close_one_area(a);

    cli::cmdout::print_message(dottalk::helpdata::MessageId::CloseCompletedText);
}
