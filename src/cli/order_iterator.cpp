// src/cli/order_iterator.cpp
#include "cli/order_iterator.hpp"

#include "cli/order_state.hpp"
#include "textio.hpp"
#include "xbase.hpp"
#include "xindex/index_manager.hpp"

#include "cli/order_nav.hpp"
#include "cnx/cnx_backend.hpp"

#include <algorithm>
#include <cctype>
#include <functional>
#include <iostream>
#include <string>
#include <vector>

namespace {

static inline bool ends_with_ci(std::string s, const char* suf) {
    auto lower = [](unsigned char c){ return static_cast<char>(std::tolower(c)); };
    for (auto& c : s) c = lower(static_cast<unsigned char>(c));
    std::string t(suf);
    for (auto& c : t) c = lower(static_cast<unsigned char>(c));
    if (s.size() < t.size()) return false;
    return s.compare(s.size() - t.size(), t.size(), t) == 0;
}

} // namespace

namespace cli {

bool order_collect_recnos_asc(xbase::DbArea& area,
                              std::vector<uint64_t>& out,
                              OrderIterSpec* out_spec,
                              std::string* out_err)
{
    out.clear();

    OrderIterSpec spec{};
    spec.cdx_mode = CdxExecMode::Fallback;

    if (!orderstate::hasOrder(area)) {
        spec.backend = OrderBackend::Natural;
        spec.ascending = true;
        if (out_spec) *out_spec = spec;

        const uint64_t n = area.recCount64();
        out.reserve(static_cast<size_t>(n));
        for (uint64_t rn = 1; rn <= n; ++rn) out.push_back(rn);
        return true;
    }

    spec.container_path = orderstate::orderName(area);
    spec.tag            = orderstate::activeTag(area);
    spec.ascending      = orderstate::isAscending(area);

    const std::string& p = spec.container_path;

    // CNX
    if (orderstate::isCnx(area) || ends_with_ci(p, ".cnx")) {
        spec.backend = OrderBackend::Cnx;
        spec.cdx_mode = CdxExecMode::Fallback;
        if (out_spec) *out_spec = spec;

        if (spec.tag.empty()) {
            if (out_err) *out_err = "CNX active but no TAG selected";
            return false;
        }

        auto& im = area.indexManager();

        if (!im.hasBackend() || im.containerPath() != p || !im.isCnx()) {
            std::string err2;
            if (!im.openCnx(p, spec.tag, &err2)) {
                if (out_err) *out_err = err2.empty() ? ("CNX open failed: " + p) : err2;
                return false;
            }
        } else {
            std::string err2;
            (void)im.setTag(spec.tag, &err2);
        }

        auto* cnx = dynamic_cast<xindex::CnxBackend*>(im.backend());
        if (!cnx) {
            if (out_err) *out_err = "CNX backend not active";
            return false;
        }

        if (!cnx->selectTag(spec.tag)) {
            if (out_err) *out_err = "CNX tag not found: " + spec.tag;
            return false;
        }

        const xindex::CnxDocument& doc = cnx->document();
        const xindex::CnxTag* active = doc.activeTag();

        if (!active) {
            if (out_err) *out_err = "CNX has no active tag after selection";
            return false;
        }

        const auto& entries = active->payload().entries();
        if (entries.empty()) {
            if (out_err) *out_err = "CNX payload empty after backend extraction";
            return false;
        }

        out.reserve(entries.size());
        for (const auto& e : entries) {
            out.push_back(static_cast<uint64_t>(e.recno));
        }
        return true;
    }

    // CDX
    if (orderstate::isCdx(area) || ends_with_ci(p, ".cdx")) {
        spec.backend = OrderBackend::Cdx;
        spec.cdx_mode = CdxExecMode::Fallback;

        if (spec.tag.empty()) {
            if (out_spec) *out_spec = spec;
            if (out_err) *out_err = "CDX active but no TAG selected";
            return false;
        }

        auto& im = area.indexManager();

        if (!im.hasBackend() || !im.isCdx() || im.containerPath() != p) {
            std::string err2;
            if (!im.openCdx(p, spec.tag, &err2)) {
                if (out_spec) *out_spec = spec;
                if (out_err) *out_err = err2.empty() ? "openCdx failed" : err2;
                return false;
            }
        } else {
            std::string err2;
            (void)im.setTag(spec.tag, &err2);
        }

        auto cursor = im.scan(xindex::Key{}, xindex::Key{});
        if (!cursor) {
            if (out_spec) *out_spec = spec;
            if (out_err) *out_err = "Failed to create LMDB cursor";
            return false;
        }

        xindex::Key k;
        xindex::RecNo r;

        if (!cursor->first(k, r)) {
            spec.cdx_mode = CdxExecMode::Lmdb;
            if (out_spec) *out_spec = spec;
            return true;
        }

        do {
            out.push_back(static_cast<uint64_t>(r));
        } while (cursor->next(k, r));

        spec.cdx_mode = CdxExecMode::Lmdb;
        if (out_spec) *out_spec = spec;
        return true;
    }

    // ISX placeholder
    if (orderstate::isIsx(area) || ends_with_ci(p, ".isx")) {
        spec.backend = OrderBackend::Isx;
        spec.cdx_mode = CdxExecMode::Fallback;
        if (out_spec) *out_spec = spec;
        if (out_err) *out_err = "ISX order family recognized but not implemented";
        return false;
    }

    // CSX placeholder
    if (orderstate::isCsx(area) || ends_with_ci(p, ".csx")) {
        spec.backend = OrderBackend::Csx;
        spec.cdx_mode = CdxExecMode::Fallback;
        if (out_spec) *out_spec = spec;
        if (out_err) *out_err = "CSX order family recognized but not implemented";
        return false;
    }

    // INX
    spec.backend = OrderBackend::Inx;
    spec.cdx_mode = CdxExecMode::Fallback;
    if (out_spec) *out_spec = spec;

    std::vector<uint32_t> tmp;
    if (!order_nav_detail::load_inx_recnos(p, area.recCount(), tmp)) {
        if (out_err) *out_err = "INX read failed: " + p;
        return false;
    }

    out.reserve(tmp.size());
    for (uint32_t rn : tmp) out.push_back(static_cast<uint64_t>(rn));
    return true;
}

bool order_iterate_recnos(xbase::DbArea& area,
                          const std::function<bool(uint64_t recno)>& visitor,
                          OrderIterSpec* out_spec,
                          std::string* out_err)
{
    std::vector<uint64_t> recnos;
    if (!order_collect_recnos_asc(area, recnos, out_spec, out_err)) return false;

    const bool asc = out_spec ? out_spec->ascending : orderstate::isAscending(area);
    if (asc) {
        for (uint64_t rn : recnos) {
            if (!visitor(rn)) break;
        }
    } else {
        for (auto it = recnos.rbegin(); it != recnos.rend(); ++it) {
            if (!visitor(*it)) break;
        }
    }
    return true;
}

} // namespace cli