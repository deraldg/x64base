// src/cli/cmd_find.cpp
//
// FIND <text>
// FIND <field> <text>
//
// Dev-tool contract:
// - FIND <text> delegates to SEEK when an order is active.
// - FIND <field> <text> and FIND <text> IN <field> delegate to SEEK only
//   when <field> is the active tag.
// - Otherwise fall back to ordered or physical scan of the requested field.
// - Honors active SET FILTER via filter::visible(&A, nullptr).
// - Positions on the found record when successful; restores the prior cursor when not found.

// @dottalk.usage v1
// owner: DOT|FIND
// command: FIND
// category: navigation
// status: supported
// noargs: usage
// effect: locate
// mutates: cursor
// usage-access: FIND USAGE
// summary:
//   Find text in the current table, delegating to SEEK when the active order
//   can satisfy the request and otherwise scanning the selected field.
//
// usage:
//   FIND USAGE
//   FIND <text>
//   FIND <field> <text>
//   FIND <text> IN <field>
//
// notes:
//   FIND requires an open table except for FIND USAGE.
//   FIND with one text argument delegates to SEEK when an order is active.
//   FIND with a field delegates to SEEK only when that field is the active tag.
//   Otherwise FIND scans the requested field using ordered or physical traversal.
//   FIND honors active SET FILTER visibility.
//   FIND positions on the found record when successful.
//   FIND restores the prior cursor when not found.
//
// risk:
//   reads_table_records: yes
//   mutates_cursor: yes when found
//   restores_cursor_on_not_found: yes
//   mutates_table_data: no
//   delegates_to_seek: when active order satisfies the request
//
// related:
//   SEEK
//   LOCATE
//   GOTO
//   COUNT
//   SET ORDER
//

#include <cctype>
#include <cstdint>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#include "xbase.hpp"
#include "xindex/index_manager.hpp"
#include "xbase_field_getters.hpp"
#include "cli/order_state.hpp"
#include "cli/order_iterator.hpp"
#include "filters/filter_registry.hpp"
#include "predicate_eval.hpp"
#include "textio.hpp"

void cmd_SEEK(xbase::DbArea& A, std::istringstream& args);

namespace {

struct CursorRestore {
    xbase::DbArea* a{nullptr};
    int32_t saved{0};
    bool active{false};

    explicit CursorRestore(xbase::DbArea& area) : a(&area) {
        try {
            saved = area.recno();
            active = (saved >= 1 && saved <= area.recCount());
        } catch (...) {
            active = false;
        }
    }

    ~CursorRestore() {
        if (!active || !a) return;
        try {
            if (a->gotoRec(saved)) {
                (void)a->readCurrent();
            }
        } catch (...) {
        }
    }

    void dismiss() noexcept {
        active = false;
    }

    CursorRestore(const CursorRestore&) = delete;
    CursorRestore& operator=(const CursorRestore&) = delete;
};

static std::string trim_copy(std::string s) {
    return textio::trim(s);
}

static std::string upper_copy(std::string s) {
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static bool ieq_char(char a, char b) {
    return std::tolower(static_cast<unsigned char>(a)) ==
           std::tolower(static_cast<unsigned char>(b));
}

static bool ieq(const std::string& a, const char* b) {
    if (!b) return false;
    size_t m = 0;
    while (b[m] != '\0') ++m;
    if (a.size() != m) return false;
    for (size_t i = 0; i < a.size(); ++i) {
        if (!ieq_char(a[i], b[i])) return false;
    }
    return true;
}

static std::string strip_outer_quotes(std::string s) {
    s = trim_copy(std::move(s));
    if (s.size() >= 2) {
        const char a = s.front();
        const char b = s.back();
        if ((a == '"' && b == '"') || (a == '\'' && b == '\'')) {
            s = s.substr(1, s.size() - 2);
        }
    }
    return s;
}

static bool contains_for_find(const std::string& hay, const std::string& needle) {
    if (predx::get_case_sensitive()) {
        return hay.find(needle) != std::string::npos;
    }

    const std::string h = upper_copy(hay);
    const std::string n = upper_copy(needle);
    return h.find(n) != std::string::npos;
}

static int find_field_1based(const xbase::DbArea& a, const std::string& name_ci) {
    const auto& fds = a.fields();
    for (size_t i = 0; i < fds.size(); ++i) {
        if (ieq(fds[i].name, name_ci.c_str())) {
            return static_cast<int>(i) + 1;
        }
    }
    return 0;
}

struct FindArgs {
    std::string field;
    std::string needle;
    bool ok{false};
    bool simple{false};
};

// FIND <text>
// FIND <field> <text>
// FIND <text> IN <field>
//
// Notes:
// - Simple FIND <text> is allowed only when an active tag/order supplies
//   the target field. cmd_FIND delegates that simple ordered form to SEEK,
//   so SET NEAR behavior stays centralized in cmd_SEEK.
// - Field-qualified forms remain scan-based and do not consume SET NEAR
//   unless later intentionally promoted to ordered seek when field == tag.
static FindArgs parse_find_args(xbase::DbArea& A, const std::string& rest) {
    FindArgs out{};
    std::istringstream in(rest);

    std::string t1;
    if (!(in >> t1)) return out;

    std::string tail;
    std::getline(in, tail);
    tail = trim_copy(tail);

    if (tail.empty()) {
        const std::string activeTag = orderstate::activeTag(A);
        if (activeTag.empty()) return out;

        out.field = activeTag;
        out.needle = strip_outer_quotes(t1);
        out.ok = !out.field.empty() && !out.needle.empty();
        out.simple = true;
        return out;
    }

    // Support: FIND <text> IN <field>
    {
        std::istringstream tail_in(tail);
        std::string maybe_in;
        std::string field_after_in;
        std::string extra;

        if ((tail_in >> maybe_in >> field_after_in) &&
            !(tail_in >> extra) &&
            ieq(maybe_in, "IN")) {
            out.field = field_after_in;
            out.needle = strip_outer_quotes(t1);
            out.ok = !out.field.empty() && !out.needle.empty();
            out.simple = false;
            return out;
        }
    }

    // Default support: FIND <field> <text>
    out.field = t1;
    out.needle = strip_outer_quotes(tail);
    out.ok = !out.field.empty() && !out.needle.empty();
    out.simple = false;
    return out;
}

static bool match_find_current(xbase::DbArea& A,
                               int fld,
                               const std::string& needle)
{
    if (!A.readCurrent()) return false;
    if (A.isDeleted()) return false;
    if (!filter::visible(&A, nullptr)) return false;

    try {
        const std::string cur = A.get(fld);
        return contains_for_find(cur, needle);
    } catch (...) {
        return false;
    }
}

// Returns true when the CDX route was used, whether or not a match was found.
// found_recno > 0 means success; 0 means routed but not found.
static bool run_find_cdx_active_order(xbase::DbArea& A,
                                      const std::string& field,
                                      const std::string& needle,
                                      int& found_recno)
{
    found_recno = 0;

    if (!A.isOpen()) return false;
    if (!orderstate::hasOrder(A) || !orderstate::isCdx(A)) return false;

    const std::string tagU = upper_copy(orderstate::activeTag(A));
    const std::string fldU = upper_copy(field);
    if (tagU.empty() || tagU != fldU) return false;

    const int fld = find_field_1based(A, field);
    if (fld <= 0) return false;

    const std::string path = orderstate::orderName(A);
    if (path.empty()) return false;

    auto& im = A.indexManager();
    std::string err;

    if (!im.hasBackend() || !im.isCdx() || im.containerPath() != path) {
        if (!im.openCdx(path, tagU, &err)) {
            return false;
        }
    } else {
        if (!im.setTag(tagU, &err)) {
            return false;
        }
    }

    if (!im.hasBackend() || !im.isCdx() || im.activeTag().empty()) {
        return false;
    }

    auto cur = im.scan(xindex::Key{}, xindex::Key{});
    if (!cur) return false;

    const bool asc = orderstate::isAscending(A);

    xindex::Key k;
    xindex::RecNo r = 0;
    bool ok = asc ? cur->first(k, r) : cur->last(k, r);

    while (ok) {
        const int32_t rn = static_cast<int32_t>(r);
        if (rn > 0 && rn <= A.recCount()) {
            try {
                if (A.gotoRec(rn) && match_find_current(A, fld, needle)) {
                    found_recno = rn;
                    return true;
                }
            } catch (...) {
                // continue
            }
        }
        ok = asc ? cur->next(k, r) : cur->prev(k, r);
    }

    return true;
}

// Returns true when ordered route was used, whether or not a match was found.
static bool run_find_ordered_shared(xbase::DbArea& A,
                                    const std::string& field,
                                    const std::string& needle,
                                    int& found_recno)
{
    found_recno = 0;

    if (!A.isOpen()) return false;
    if (!orderstate::hasOrder(A)) return false;

    const int fld = find_field_1based(A, field);
    if (fld <= 0) return false;

    std::vector<uint64_t> recnos;
    cli::OrderIterSpec spec{};
    std::string err;

    if (!cli::order_collect_recnos_asc(A, recnos, &spec, &err)) {
        return false;
    }
    if (recnos.empty()) {
        return true;
    }

    if (spec.ascending) {
        for (uint64_t rn64 : recnos) {
            const int32_t rn = static_cast<int32_t>(rn64);
            if (rn < 1 || rn > A.recCount()) continue;
            if (!A.gotoRec(rn)) continue;
            if (match_find_current(A, fld, needle)) {
                found_recno = rn;
                return true;
            }
        }
    } else {
        for (size_t i = recnos.size(); i-- > 0;) {
            const int32_t rn = static_cast<int32_t>(recnos[i]);
            if (rn < 1 || rn > A.recCount()) continue;
            if (!A.gotoRec(rn)) continue;
            if (match_find_current(A, fld, needle)) {
                found_recno = rn;
                return true;
            }
        }
    }

    return true;
}

// Returns true when physical route was used, whether or not a match was found.
static bool run_find_physical(xbase::DbArea& A,
                              const std::string& field,
                              const std::string& needle,
                              int& found_recno)
{
    found_recno = 0;

    const int fld = find_field_1based(A, field);
    if (fld <= 0) return false;

    if (!A.top()) {
        return true;
    }

    do {
        if (match_find_current(A, fld, needle)) {
            found_recno = A.recno();
            return true;
        }
    } while (A.skip(1));

    return true;
}


static bool is_find_usage_request(std::string raw) {
    std::string t = upper_copy(trim_copy(std::move(raw)));
    if (t.rfind("FIND ", 0) == 0) {
        t = upper_copy(trim_copy(t.substr(5)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_find_usage() {
    std::cout
        << "Usage:\n"
        << "  FIND USAGE\n"
        << "  FIND <text>\n"
        << "  FIND <field> <text>\n"
        << "  FIND <text> IN <field>\n"
        << "Notes:\n"
        << "  - FIND requires an open table except for FIND USAGE.\n"
        << "  - FIND delegates to SEEK when the active order can satisfy the request.\n"
        << "  - Otherwise FIND scans the requested field and positions on the found record.\n";
}

} // namespace

void cmd_FIND(xbase::DbArea& A, std::istringstream& args) {
    std::string rest;
    std::getline(args, rest);
    rest = trim_copy(rest);

    if (is_find_usage_request(rest)) {
        print_find_usage();
        return;
    }

    if (!A.isOpen()) {
        std::cout << "No table open.\n";
        return;
    }

    const FindArgs fa = parse_find_args(A, rest);
    if (!fa.ok) {
        print_find_usage();
        return;
    }

    // Ordered FIND contract:
    //
    //   FIND <text>
    //       If an order is active, delegate to SEEK.
    //
    //   FIND <field> <text>
    //   FIND <text> IN <field>
    //       Delegate to SEEK only when <field> is the active tag.
    //       Otherwise remain scan-based and search the named field.
    //
    // This keeps exact / SET NEAR behavior centralized in cmd_SEEK and
    // avoids duplicating ordered-key logic here.
    if (orderstate::hasOrder(A)) {
        const std::string activeTagU = upper_copy(orderstate::activeTag(A));
        const std::string fieldU = upper_copy(fa.field);

        if (fa.simple || (!activeTagU.empty() && activeTagU == fieldU)) {
            std::istringstream seek_args(fa.needle);
            cmd_SEEK(A, seek_args);
            return;
        }
    }

    CursorRestore restore(A);

    // Preferred fast path: active CDX tag search.
    {
        int found_recno = 0;
        const bool routed = run_find_cdx_active_order(A, fa.field, fa.needle, found_recno);
        if (routed) {
            if (found_recno > 0) {
                restore.dismiss();
                std::cout << "Found.\n";
            } else {
                std::cout << "Not Found.\n";
            }
            return;
        }
    }

    // Ordered fallback whenever any active order exists.
    if (orderstate::hasOrder(A)) {
        int found_recno = 0;
        const bool routed = run_find_ordered_shared(A, fa.field, fa.needle, found_recno);
        if (routed) {
            if (found_recno > 0) {
                restore.dismiss();
                std::cout << "Found.\n";
            } else {
                std::cout << "Not Found.\n";
            }
            return;
        }
    }

    // Physical fallback.
    {
        int found_recno = 0;
        (void)run_find_physical(A, fa.field, fa.needle, found_recno);
        if (found_recno > 0) {
            restore.dismiss();
            std::cout << "Found.\n";
        } else {
            std::cout << "Not Found.\n";
        }
    }
}