// src/cli/order_iterator.cpp
#include "cli/order_iterator.hpp"

#include "cli/order_state.hpp"
#include "textio.hpp"
#include "xbase.hpp"
#include "cli/order_nav.hpp"

#if DOTTALK_HAS_XINDEX
#include "xindex/index_manager.hpp"
#include "xindex/attach.hpp"
#include "cnx/cnx_backend.hpp"
#endif

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

#if !DOTTALK_HAS_XINDEX
    // A table-only composition always walks physical record order.  Persisted
    // workspace order metadata may still exist, but it cannot activate an
    // index backend that was not compiled into this product.
    spec.backend = OrderBackend::Natural;
    spec.ascending = true;
    if (out_spec) *out_spec = spec;
    if (out_err) out_err->clear();
    const uint64_t n = area.recCount64();
    out.reserve(static_cast<size_t>(n));
    for (uint64_t rn = 1; rn <= n; ++rn) out.push_back(rn);
    return true;
#else

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

        auto& im = xindex::ensure_manager(area);

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

        auto& im = xindex::ensure_manager(area);

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
#endif
}

bool order_stream_display(xbase::DbArea& area,
                          bool reverse,
                          const std::function<bool(uint64_t recno)>& visitor,
                          OrderIterSpec* out_spec,
                          std::string* out_err)
{
    OrderIterSpec spec{};
    spec.cdx_mode = CdxExecMode::Fallback;

    // Emit a natural (physical) range in the requested direction.
    auto emit_natural = [&](uint64_t n, bool forward) {
        if (forward) {
            for (uint64_t rn = 1; rn <= n; ++rn) {
                if (!visitor(rn)) return;
            }
        } else {
            for (uint64_t rn = n; rn >= 1; --rn) {
                if (!visitor(rn)) return;
                if (rn == 1) break;   // avoid unsigned wrap
            }
        }
    };

    if (!orderstate::hasOrder(area)) {
        spec.backend = OrderBackend::Natural;
        spec.ascending = true;
        if (out_spec) *out_spec = spec;
        if (out_err) out_err->clear();
        // Display order for natural is physical ascending; reverse flips it.
        emit_natural(area.recCount64(), /*forward=*/!reverse);
        return true;
    }

#if !DOTTALK_HAS_XINDEX
    spec.backend = OrderBackend::Natural;
    spec.ascending = true;
    if (out_spec) *out_spec = spec;
    if (out_err) out_err->clear();
    emit_natural(area.recCount64(), /*forward=*/!reverse);
    return true;
#else
    spec.container_path = orderstate::orderName(area);
    spec.tag            = orderstate::activeTag(area);
    spec.ascending      = orderstate::isAscending(area);

    const std::string& p = spec.container_path;

    // Walk the underlying index forward (ascending key) when the logical display
    // is ascending and we are NOT reversing, or when it is descending and we ARE
    // reversing. i.e. walkForward == (ascending != reverse).
    const bool walkForward = (spec.ascending != reverse);

    // CNX (32-bit flavors) -- iterate the materialized payload entries directly.
    if (orderstate::isCnx(area) || ends_with_ci(p, ".cnx")) {
        spec.backend = OrderBackend::Cnx;
        spec.cdx_mode = CdxExecMode::Fallback;
        if (out_spec) *out_spec = spec;

        if (spec.tag.empty()) {
            if (out_err) *out_err = "CNX active but no TAG selected";
            return false;
        }

        auto& im = xindex::ensure_manager(area);
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

        if (walkForward) {
            for (const auto& e : entries) {
                if (!visitor(static_cast<uint64_t>(e.recno))) break;
            }
        } else {
            for (auto it = entries.rbegin(); it != entries.rend(); ++it) {
                if (!visitor(static_cast<uint64_t>(it->recno))) break;
            }
        }
        return true;
    }

    // CDX (LMDB front end, 64-bit flavors) -- stream the backend cursor.
    if (orderstate::isCdx(area) || ends_with_ci(p, ".cdx")) {
        spec.backend = OrderBackend::Cdx;
        spec.cdx_mode = CdxExecMode::Fallback;

        if (spec.tag.empty()) {
            if (out_spec) *out_spec = spec;
            if (out_err) *out_err = "CDX active but no TAG selected";
            return false;
        }

        auto& im = xindex::ensure_manager(area);
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

        spec.cdx_mode = CdxExecMode::Lmdb;
        if (out_spec) *out_spec = spec;

        xindex::Key k;
        xindex::RecNo r;

        if (walkForward) {
            if (!cursor->first(k, r)) return true;   // empty index
            do {
                if (!visitor(static_cast<uint64_t>(r))) break;
            } while (cursor->next(k, r));
        } else {
            if (!cursor->last(k, r)) return true;    // empty index
            do {
                if (!visitor(static_cast<uint64_t>(r))) break;
            } while (cursor->prev(k, r));
        }
        return true;
    }

    // INX / ISX / CSX and anything else: no streaming backend available here.
    // Materialize the ascending order once and iterate it in display order.
    {
        std::vector<uint64_t> recnos;
        OrderIterSpec s2{};
        if (!order_collect_recnos_asc(area, recnos, &s2, out_err)) {
            if (out_spec) *out_spec = s2;
            return false;
        }
        if (out_spec) *out_spec = s2;

        // recnos are in ascending index order; forward display when ascending.
        const bool walkForwardVec = (s2.ascending != reverse);
        if (walkForwardVec) {
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
#endif
}

OrderStep order_step_cdx(xbase::DbArea& area, int index_delta, std::int64_t& out_recno)
{
    out_recno = 0;
#if !DOTTALK_HAS_XINDEX
    (void)area; (void)index_delta;
    return OrderStep::Unavailable;
#else
    if (!area.isOpen() || index_delta == 0) return OrderStep::Unavailable;
    if (!orderstate::hasOrder(area)) return OrderStep::Unavailable;

    const std::string p = orderstate::orderName(area);
    if (!(orderstate::isCdx(area) || ends_with_ci(p, ".cdx"))) return OrderStep::Unavailable;

    const std::string tag = orderstate::activeTag(area);
    if (tag.empty()) return OrderStep::Unavailable;

    auto& im = xindex::ensure_manager(area);
    if (!im.hasBackend() || !im.isCdx() || im.containerPath() != p) {
        std::string err2;
        if (!im.openCdx(p, tag, &err2)) return OrderStep::Unavailable;
    } else {
        std::string err2;
        (void)im.setTag(tag, &err2);
    }

    auto* cdx = dynamic_cast<xindex::CdxBackend*>(im.backend());
    if (!cdx) return OrderStep::Unavailable;

    // Base key of the CURRENT record (matches the stored index key exactly:
    // uppercased for char keys, padded/truncated to key length).
    const xindex::Key baseKey = im.buildActiveTagBaseKeyFromCurrentRecord();
    if (baseKey.empty()) return OrderStep::Unavailable; // tag field unresolved

    const std::int64_t cur = static_cast<std::int64_t>(area.recno64());
    if (cur < 1 || cur > static_cast<std::int64_t>(area.recCount64())) return OrderStep::Unavailable;

    const bool forward = index_delta > 0;
    const int steps = index_delta > 0 ? index_delta : -index_delta;

    xindex::RecNo landed = 0;
    bool located = false;
    if (cdx->stepOrdered(baseKey, static_cast<xindex::RecNo>(cur), forward, steps, landed, located)) {
        if (landed >= 1 && static_cast<std::int64_t>(landed) <= static_cast<std::int64_t>(area.recCount64())) {
            out_recno = static_cast<std::int64_t>(landed);
            return OrderStep::Moved;
        }
        return OrderStep::Unavailable;
    }
    // Located the current entry but could not step -> genuine order boundary.
    // Otherwise the current record is not in the index -> let the caller fall back.
    return located ? OrderStep::Boundary : OrderStep::Unavailable;
#endif
}

bool order_iterate_recnos(xbase::DbArea& area,
                          const std::function<bool(uint64_t recno)>& visitor,
                          OrderIterSpec* out_spec,
                          std::string* out_err)
{
    // NOTE: this path intentionally materializes first. Callers such as SCAN and
    // LIST may run command bodies that MUTATE the active index (e.g. REPLACE),
    // which must not happen while a read cursor is held open. order_stream_display
    // is used instead by the read-only navigation helpers (TOP/BOTTOM/SKIP/GO).
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
