#include "cli/list_messaging.hpp"

#include "workareas.hpp"
#include "cursor_status.hpp"
#include "../xbase/cursor_hook.hpp"

#include <iostream>
#include <string>
#include <vector>
#include <cstdint>

namespace cli::listmsg {

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

const char* backend_name(const cli::OrderIterSpec& spec) {
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

void print_order_banner(const cli::OrderIterSpec& spec) {
    if (spec.backend == cli::OrderBackend::Natural) return;

    std::cout << "; ORDER: file '" << spec.container_path << "'";
    if (!spec.tag.empty()) {
        std::cout << "  TAG '" << spec.tag << "'";
    }
    if (spec.backend == cli::OrderBackend::Cdx) {
        std::cout << "  MODE " << ((spec.cdx_mode == cli::CdxExecMode::Lmdb) ? "LMDB" : "FALLBACK");
    }
    std::cout << "  " << (spec.ascending ? "ASC" : "DESC") << "\n";
}

void print_cursor_line(xbase::DbArea& a, const char* reason) {
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

void print_list_summary(xbase::DbArea& a,
                        int printed,
                        bool all,
                        int limit,
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

    (void)logical; // cursor_status reports using area state

    if (spec.backend == cli::OrderBackend::Natural) {
        if (!all) {
            std::cout << printed << " record(s) listed (limit " << limit
                      << "). Use LIST ALL to show more.\n";
        } else {
            std::cout << printed << " record(s) listed.\n";
        }
        print_cursor_line(a, "LIST");
        return;
    }

    std::cout << printed << " " << backend_name(spec) << " indexed record(s)";
    if (!spec.tag.empty()) {
        std::cout << " (tag=" << spec.tag << ")";
    }
    if (!all) {
        std::cout << " listed (limit " << limit << "). Use LIST ALL to show more.\n";
    } else {
        std::cout << " listed.\n";
    }
    print_cursor_line(a, "LIST");
}

void print_browser_summary(xbase::DbArea& a,
                           long total,
                           const cli::OrderIterSpec& spec,
                           const cli::smartlist::QuerySpec& qspec,
                           const char* reason)
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

    (void)logical;

    if (spec.backend == cli::OrderBackend::Natural) {
        std::cout << total << " record(s) listed.\n";
        print_cursor_line(a, reason);
        return;
    }

    std::cout << total << " " << backend_name(spec) << " indexed record(s)";
    if (!spec.tag.empty()) {
        std::cout << " (tag=" << spec.tag << ")";
    }
    std::cout << " listed.\n";
    print_cursor_line(a, reason);
}

} // namespace cli::listmsg