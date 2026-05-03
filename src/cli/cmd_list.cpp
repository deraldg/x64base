// src/cli/cmd_list.cpp
#include "xbase.hpp"
#include "xindex/index_manager.hpp"
#include "textio.hpp"
#include "filters/filter_registry.hpp"
#include "cli/expr/api.hpp"
#include "cli/expr/ast.hpp"
#include "cli/expr/glue_xbase.hpp"
#include "cli/expr/parse_utils.hpp"
#include "cli/expr/line_parse_utils.hpp"
#include "value_normalize.hpp"
#include "cli/order_state.hpp"
#include "cli/order_iterator.hpp"
#include "cli/nav_move.hpp"
#include "cli/expr/normalize_where.hpp"
#include "workareas.hpp"
#include "workspace/workarea_utils.hpp"
#include "../xbase/cursor_hook.hpp"
#include "cursor_status.hpp"

// Shared SMARTLIST helpers reused here where appropriate.
// LIST keeps its own navigation / summary / cursor-report behavior.
#include "cli/smartlist_query.hpp"
#include "cli/smartlist_output.hpp"
#include "cli/table_object.hpp"
#include "cli/table_state.hpp"

#include <iostream>
#include <iomanip>
#include <string>
#include <cctype>
#include <algorithm>
#include <sstream>
#include <vector>
#include <cstdlib>
#include <cstdint>
#include <type_traits>
#include <utility>
#include <memory>

extern "C" xbase::XBaseEngine* shell_engine();

namespace {

struct CursorRestore {
    xbase::DbArea* a{nullptr};
    int32_t saved{0};
    bool active{false};

    explicit CursorRestore(xbase::DbArea& area) : a(&area) {
        saved = area.recno();
        active = (saved >= 1 && saved <= area.recCount());
    }

    void cancel() noexcept { active = false; }

    ~CursorRestore() {
        if (!active || !a) return;
        try {
            a->gotoRec(saved);
            a->readCurrent();
        } catch (...) {
            // best-effort
        }
    }
};

enum class DelFilter {
    Any,
    OnlyDeleted,
    OnlyAlive
};

enum class StartPos {
    Here,
    Top,
    Bottom
};

struct Options {
    bool all{false};
    int  limit{20};
    StartPos start{StartPos::Here};

    DelFilter del{DelFilter::Any};

    bool haveCompiledFor{false};
    std::string forExpr;
};

static inline std::string upper_copy(std::string s) {
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static int resolve_area_index(xbase::DbArea& a) {
    xbase::XBaseEngine* eng = shell_engine();
    if (!eng) return -1;

    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        try {
            if (&eng->area(i) == &a) return i;
        } catch (...) {
        }
    }

    return -1;
}

static void print_list_row(xbase::DbArea& area,
                           dottalk::table::Table* table_view,
                           int32_t rn,
                           int recw)
{
    if (table_view) {
        try {
            const bool physical_deleted = area.isDeleted();
            dottalk::table::Row row = table_view->snapshot_view(static_cast<int>(rn));
            cli::smartlist::print_row(area, row, recw, physical_deleted);
            return;
        } catch (...) {
            // LIST is a developer tool; if the overlay path is unavailable,
            // fall back to the physical DbArea row rather than abort output.
        }
    }

    cli::smartlist::print_row(area, recw);
}

static Options parse_opts(std::istringstream& iss) {
    Options o{};

    std::string tok;
    auto save = iss.tellg();
    if (iss >> tok) {
        if (textio::ieq(tok, "TOP")) {
            o.start = StartPos::Top;
        } else if (textio::ieq(tok, "BOTTOM")) {
            o.start = StartPos::Bottom;
        } else {
            iss.clear();
            iss.seekg(save);
        }
    }

    save = iss.tellg();
    if (iss >> tok) {
        if (textio::ieq(tok, "ALL")) {
            o.all = true;
        } else if (textio::ieq(tok, "DELETED")) {
            o.del = DelFilter::OnlyDeleted;
        } else if (is_uint(tok)) {
            o.limit = std::max(0, std::stoi(tok));
        } else {
            iss.clear();
            iss.seekg(save);
        }
    }

    save = iss.tellg();
    std::string w;
    if (iss >> w && textio::ieq(w, "FOR")) {
        std::string a;
        if (iss >> a) {
            const std::string ua = upper_copy(a);

            if (ua == "DELETED") {
                o.del = DelFilter::OnlyDeleted;
                return o;
            }
            if (ua == "!DELETED" || ua == "~DELETED") {
                o.del = DelFilter::OnlyAlive;
                return o;
            }

            std::string rest_of_line;
            std::getline(iss, rest_of_line);
            std::string expr = a;
            const std::string tail = textio::trim(rest_of_line);
            if (!tail.empty()) expr += " " + tail;

            const std::string cleaned = textio::trim(strip_line_comments(expr));
            if (!cleaned.empty()) {
                o.haveCompiledFor = true;
                o.forExpr = cleaned;
            }
            return o;
        } else {
            iss.clear();
            iss.seekg(save);
        }
    } else {
        iss.clear();
        iss.seekg(save);
    }

    return o;
}

static cli::smartlist::QuerySpec make_query_spec(
    const Options& opt,
    const std::shared_ptr<dottalk::expr::Expr>& prog)
{
    cli::smartlist::QuerySpec spec{};
    spec.all = opt.all;
    spec.limit = opt.limit;
    spec.debug = false;
    spec.expr_prog = prog;

    switch (opt.del) {
        case DelFilter::OnlyDeleted:
            spec.del = cli::smartlist::DelFilter::OnlyDeleted;
            break;
        case DelFilter::OnlyAlive:
            spec.del = cli::smartlist::DelFilter::OnlyAlive;
            break;
        case DelFilter::Any:
        default:
            spec.del = cli::smartlist::DelFilter::Any;
            break;
    }

    return spec;
}

static std::int64_t compute_physical_logical_row(xbase::DbArea& a,
                                                 int32_t physical_recno,
                                                 const cli::smartlist::QuerySpec& qspec)
{
    if (physical_recno < 1 || physical_recno > a.recCount()) return 0;

    xbase::cursor_hook::Guard suppress_cursor;
    std::int64_t logical_row = 0;

    for (int32_t rn = 1; rn <= physical_recno; ++rn) {
        if (!a.gotoRec(rn) || !a.readCurrent()) continue;
        if (!cli::smartlist::pass_all_filters(a, qspec)) continue;
        ++logical_row;
    }
    return logical_row;
}

static std::int64_t compute_ordered_logical_row(xbase::DbArea& a,
                                                const std::vector<uint64_t>& recnos_asc,
                                                const cli::OrderIterSpec& spec,
                                                int32_t physical_recno,
                                                const cli::smartlist::QuerySpec& qspec)
{
    if (physical_recno < 1 || physical_recno > a.recCount()) return 0;

    xbase::cursor_hook::Guard suppress_cursor;
    std::int64_t logical_row = 0;

    if (spec.ascending) {
        for (uint64_t rn64 : recnos_asc) {
            const int32_t rn = static_cast<int32_t>(rn64);
            if (!a.gotoRec(rn) || !a.readCurrent()) continue;
            if (!cli::smartlist::pass_all_filters(a, qspec)) continue;
            ++logical_row;
            if (rn == physical_recno) return logical_row;
        }
    } else {
        for (auto it = recnos_asc.rbegin(); it != recnos_asc.rend(); ++it) {
            const int32_t rn = static_cast<int32_t>(*it);
            if (!a.gotoRec(rn) || !a.readCurrent()) continue;
            if (!cli::smartlist::pass_all_filters(a, qspec)) continue;
            ++logical_row;
            if (rn == physical_recno) return logical_row;
        }
    }

    return 0;
}

static const char* backend_name(const cli::OrderIterSpec& spec) {
    switch (spec.backend) {
        case cli::OrderBackend::Natural: return "natural";
        case cli::OrderBackend::Inx:     return "inx";
        case cli::OrderBackend::Cnx:     return "cnx";
        case cli::OrderBackend::Cdx:
            return (spec.cdx_mode == cli::CdxExecMode::Lmdb) ? "cdx(lmdb)" : "cdx(fallback)";
        case cli::OrderBackend::Isx:     return "isx";
        case cli::OrderBackend::Csx:     return "csx";
        default:                         return "ordered";
    }
}

static void print_order_banner(const cli::OrderIterSpec& spec) {
    if (spec.backend == cli::OrderBackend::Natural) return;

    std::cout << "; ORDER: file '" << spec.container_path << "'";
    if (!spec.tag.empty()) {
        std::cout << "  TAG '" << upper_copy(spec.tag) << "'";
    }
    if (spec.backend == cli::OrderBackend::Cdx) {
        std::cout << "  MODE " << ((spec.cdx_mode == cli::CdxExecMode::Lmdb) ? "LMDB" : "FALLBACK");
    }
    std::cout << "  " << (spec.ascending ? "ASC" : "DESC") << "\n";
}

static void print_cursor_line(xbase::DbArea& a, const char* reason) {
    const std::size_t cur = workareas::current_slot();
    const int area_first = 0;
    const int area_last =
        workareas::count() > 0 ? static_cast<int>(workareas::count() - 1) : 0;

    auto snap = xbase::cursor_status::build_snapshot(
        a,
        reason,
        area_first,
        area_last
    );
    snap.area_index = static_cast<int>(cur);

    std::cout << xbase::cursor_status::format_cursor_line(snap) << "\n";
}

static void print_summary(xbase::DbArea& a,
                          int printed,
                          const Options& opt,
                          const cli::OrderIterSpec& spec,
                          const cli::smartlist::QuerySpec& qspec)
{
    const int32_t physical =
        (a.recno() >= 1 && a.recno() <= a.recCount()) ? a.recno() : 0;

    std::int64_t logical = 0;

    if (spec.backend == cli::OrderBackend::Natural) {
        logical = compute_physical_logical_row(a, physical, qspec);
    } else {
        std::vector<uint64_t> recnos_asc;
        cli::OrderIterSpec tmp_spec{};
        std::string err;

        if (cli::order_collect_recnos_asc(a, recnos_asc, &tmp_spec, &err) && !recnos_asc.empty()) {
            logical = compute_ordered_logical_row(a, recnos_asc, tmp_spec, physical, qspec);
        }
    }

    (void)logical; // cursor_status will compute/report using area state

    if (spec.backend == cli::OrderBackend::Natural) {
        if (!opt.all) {
            std::cout << printed << " record(s) listed (limit " << opt.limit
                      << "). Use LIST ALL to show more.\n";
        } else {
            std::cout << printed << " record(s) listed.\n";
        }
        print_cursor_line(a, "LIST");
        return;
    }

    std::cout << printed << " " << backend_name(spec) << " indexed record(s)";
    if (!spec.tag.empty()) {
        std::cout << " (tag=" << upper_copy(spec.tag) << ")";
    }
    if (!opt.all) {
        std::cout << " listed (limit " << opt.limit << "). Use LIST ALL to show more.\n";
    } else {
        std::cout << " listed.\n";
    }
    print_cursor_line(a, "LIST");
}

static bool list_from_recnos(xbase::DbArea& a,
                             const std::vector<uint64_t>& recnos_asc,
                             const cli::OrderIterSpec& spec,
                             const Options& opt,
                             const cli::smartlist::QuerySpec& qspec,
                             int recw,
                             int32_t start_rn,
                             dottalk::table::Table* table_view)
{
    xbase::cursor_hook::Guard suppress_cursor;

    int printed = 0;
    bool started = (start_rn == 0);

    if (spec.ascending) {
        for (uint64_t rn : recnos_asc) {
            if (!started) {
                if (static_cast<int32_t>(rn) != start_rn) continue;
                started = true;
            }
            if (!a.gotoRec(static_cast<int32_t>(rn)) || !a.readCurrent()) continue;
            if (!cli::smartlist::pass_all_filters(a, qspec)) continue;
            print_list_row(a, table_view, static_cast<int32_t>(rn), recw);
            ++printed;
            if (!opt.all && opt.limit > 0 && printed >= opt.limit) break;
        }
    } else {
        for (auto it = recnos_asc.rbegin(); it != recnos_asc.rend(); ++it) {
            const uint64_t rn = *it;
            if (!started) {
                if (static_cast<int32_t>(rn) != start_rn) continue;
                started = true;
            }
            if (!a.gotoRec(static_cast<int32_t>(rn)) || !a.readCurrent()) continue;
            if (!cli::smartlist::pass_all_filters(a, qspec)) continue;
            print_list_row(a, table_view, static_cast<int32_t>(rn), recw);
            ++printed;
            if (!opt.all && opt.limit > 0 && printed >= opt.limit) break;
        }
    }

    print_summary(a, printed, opt, spec, qspec);
    return true;
}

} // namespace

void cmd_LIST(xbase::DbArea& a, std::istringstream& iss) {
    CursorRestore _restore_(a);

    if (!a.isOpen()) {
        std::cout << "No table open.\n";
        return;
    }

    Options opt = parse_opts(iss);

    std::shared_ptr<dottalk::expr::Expr> _prog;
    if (opt.haveCompiledFor) {
        std::string norm = normalize_unquoted_rhs_literals(a, opt.forExpr);
        auto cr = dottalk::expr::compile_where(norm);
        if (cr) {
            _prog = std::shared_ptr<dottalk::expr::Expr>(std::move(cr.program));
        } else {
            std::cout << "; LIST FOR error: " << cr.error << " - ignoring FOR.\n";
            opt.haveCompiledFor = false;
        }
    }

    cli::smartlist::QuerySpec qspec = make_query_spec(opt, _prog);

    const int32_t total = a.recCount();
    if (total <= 0) {
        std::cout << "(empty)\n";
        return;
    }

    bool nav_ok = true;
    switch (opt.start) {
        case StartPos::Top:
            nav_ok = cli::nav::go_endpoint(a, cli::nav::Endpoint::Top, "LIST");
            break;
        case StartPos::Bottom:
            nav_ok = cli::nav::go_endpoint(a, cli::nav::Endpoint::Bottom, "LIST");
            break;
        case StartPos::Here:
        default:
            if (opt.all) nav_ok = a.top();
            else if (a.recno() <= 0) nav_ok = a.top();
            break;
    }
    if (!nav_ok) return;

    const int recw = cli::smartlist::recno_width(a);
    cli::smartlist::print_header(a, recw);

    xbase::XBaseEngine* eng = shell_engine();
    const int area0 = resolve_area_index(a);
    std::unique_ptr<dottalk::table::Table> table_view;

    if (eng && area0 >= 0) {
        try {
            table_view = std::make_unique<dottalk::table::Table>(*eng, area0);
        } catch (...) {
            table_view.reset();
        }
    }

    // Explicit LIST DELETED must use physical traversal.
    // Active order/index streams generally exclude deleted records, so an
    // ordered pass cannot be the source of truth for deleted-only inspection.
    if (orderstate::hasOrder(a) && opt.del != DelFilter::OnlyDeleted) {
        cli::OrderIterSpec spec{};
        std::vector<uint64_t> recnos_asc;
        std::string err;

        const bool ok = cli::order_collect_recnos_asc(a, recnos_asc, &spec, &err);

        int32_t start_rn = 0;
        if (!opt.all && a.recno() >= 1 && a.recno() <= a.recCount()) {
            // LIST without ALL is cursor-relative. However, when an active
            // SET FILTER or LIST FOR predicate is present, starting from a
            // current record that does not pass the predicate can produce a
            // false empty result under ordered traversal. In that case, start
            // from the top of the ordered stream and let pass_all_filters()
            // decide row visibility.
            const int32_t cur = a.recno();
            xbase::cursor_hook::Guard suppress_cursor_for_probe;
            if (a.gotoRec(cur) && a.readCurrent() && cli::smartlist::pass_all_filters(a, qspec)) {
                start_rn = cur;
            }
        }

        if (ok && !recnos_asc.empty()) {
            print_order_banner(spec);
            list_from_recnos(a, recnos_asc, spec, opt, qspec, recw, start_rn, table_view.get());
            return;
        }

        if (!err.empty()) {
            std::cout << "; LIST order note: " << err << " - falling back to physical order\n";
        } else {
            std::cout << "; LIST order note: ordered backend unavailable - falling back to physical order\n";
        }
    }

    {
        xbase::cursor_hook::Guard suppress_cursor;

        int printed = 0;
        const int32_t start = opt.all ? 1 : a.recno();

        for (int32_t rn = start; rn <= total; ++rn) {
            if (!a.gotoRec(rn) || !a.readCurrent()) continue;
            if (!cli::smartlist::pass_all_filters(a, qspec)) continue;
            print_list_row(a, table_view.get(), rn, recw);
            ++printed;
            if (!opt.all && opt.limit > 0 && printed >= opt.limit) break;
        }

        cli::OrderIterSpec natural_spec{};
        natural_spec.backend = cli::OrderBackend::Natural;
        natural_spec.cdx_mode = cli::CdxExecMode::Fallback;
        natural_spec.ascending = true;

        print_summary(a, printed, opt, natural_spec, qspec);
    }
}