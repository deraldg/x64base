#include "tuple/root_recno_source.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <climits>
#include <exception>
#include <sstream>
#include <string>
#include <vector>

#include "cli/order_iterator.hpp"
#include "cli/order_state.hpp"

namespace dottalk::tupleaugment {

namespace {

constexpr std::size_t kMaxDiagRecnos = 256;

static void push_diag_recno(std::vector<int>& v, int rn) {
    if (v.size() < kMaxDiagRecnos) v.push_back(rn);
}

static std::string upcopy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static int safe_reccount(xbase::DbArea& area) {
    try { return static_cast<int>(area.recCount()); } catch (...) { return 0; }
}

static bool safe_goto_read(xbase::DbArea& area, int rn) {
    try {
        if (rn < 1 || rn > safe_reccount(area)) return false;
        if (!area.gotoRec(rn)) return false;
        return area.readCurrent();
    } catch (...) {
        return false;
    }
}

static bool safe_deleted(xbase::DbArea& area) {
    try { return area.isDeleted(); } catch (...) { return false; }
}

static const char* backend_name(const cli::OrderIterSpec& spec) {
    switch (spec.backend) {
        case cli::OrderBackend::Natural: return "NATURAL";
        case cli::OrderBackend::Inx:     return "INX";
        case cli::OrderBackend::Cnx:     return "CNX";
        case cli::OrderBackend::Cdx:
            return (spec.cdx_mode == cli::CdxExecMode::Lmdb) ? "CDX(LMDB)" : "CDX(FALLBACK)";
        case cli::OrderBackend::Isx:     return "ISX";
        case cli::OrderBackend::Csx:     return "CSX";
        default:                         return "ORDERED";
    }
}

static std::string order_status_from_spec(const cli::OrderIterSpec& spec) {
    if (spec.backend == cli::OrderBackend::Natural) return "NATURAL";

    std::ostringstream oss;
    oss << backend_name(spec);
    if (!spec.tag.empty()) oss << " TAG " << upcopy(spec.tag);
    oss << (spec.ascending ? " ASC" : " DESC");
    return oss.str();
}

} // namespace

RootRecnoSource::RootRecnoSource(xbase::DbArea& root, RootRecnoSourceOptions options)
    : root_(root), options_(options) {}

bool RootRecnoSource::include_current_root_record_() const {
    const bool deleted = safe_deleted(root_);
    if (options_.only_deleted) return deleted;
    if (!options_.include_deleted && deleted) return false;
    return true;
}

bool RootRecnoSource::collect(std::vector<int>& out, std::string& error) {
    out.clear();
    error.clear();
    stats_ = RootRecnoSourceStats{};

    const int total = safe_reccount(root_);
    stats_.table_rec_count = total;
    if (total <= 0) return true;

    auto push_if_visible = [&](int rn) {
        ++stats_.candidate_recnos;

        if (rn < 1 || rn > total) {
            ++stats_.skipped_out_of_range;
            push_diag_recno(stats_.skipped_out_of_range_recnos, rn);
            return;
        }

        if (!safe_goto_read(root_, rn)) {
            ++stats_.skipped_read;
            push_diag_recno(stats_.skipped_read_recnos, rn);
            return;
        }

        if (!include_current_root_record_()) {
            ++stats_.skipped_deleted;
            push_diag_recno(stats_.skipped_deleted_recnos, rn);
            return;
        }

        out.push_back(rn);
    };

    bool tried_order = false;
    if (options_.use_active_order) {
        bool has_order = false;
        try { has_order = orderstate::hasOrder(root_); } catch (...) { has_order = false; }

        if (has_order) {
            tried_order = true;
            cli::OrderIterSpec spec{};
            std::vector<uint64_t> recnos_asc;
            std::string order_error;

            const bool ok = cli::order_collect_recnos_asc(root_, recnos_asc, &spec, &order_error);
            if (ok && !recnos_asc.empty()) {
                stats_.ordered = true;
                stats_.order_status = order_status_from_spec(spec);

                if (spec.ascending) {
                    for (uint64_t rn64 : recnos_asc) {
                        if (rn64 > static_cast<uint64_t>(INT_MAX)) {
                            ++stats_.candidate_recnos;
                            ++stats_.skipped_out_of_range;
                            continue;
                        }
                        push_if_visible(static_cast<int>(rn64));
                    }
                } else {
                    for (auto it = recnos_asc.rbegin(); it != recnos_asc.rend(); ++it) {
                        if (*it > static_cast<uint64_t>(INT_MAX)) {
                            ++stats_.candidate_recnos;
                            ++stats_.skipped_out_of_range;
                            continue;
                        }
                        push_if_visible(static_cast<int>(*it));
                    }
                }
            } else {
                stats_.order_fallback = true;
                stats_.order_status = order_error.empty()
                    ? "NATURAL (order fallback)"
                    : "NATURAL (order fallback: " + order_error + ")";
            }
        }
    }

    if (out.empty() && (!tried_order || stats_.order_fallback)) {
        for (int rn = 1; rn <= total; ++rn) push_if_visible(rn);
        if (!stats_.order_fallback) stats_.order_status = "NATURAL";
    }

    stats_.recnos_collected = out.size();
    if (!out.empty()) {
        stats_.first_recno = out.front();
        stats_.last_recno = out.back();
    }

    return true;
}

} // namespace dottalk::tupleaugment
