#include "cli/workarea_cursor_restore.hpp"

#include <exception>
#include <string>

#include "set_relations.hpp"
#include "workareas.hpp"
#include "xbase.hpp"

namespace dottalk::tupleaugment {

namespace {

static bool area_is_open(const xbase::DbArea* area) {
    if (!area) return false;
    try { return area->isOpen(); } catch (...) { return false; }
}

static std::int32_t safe_recno(const xbase::DbArea* area) {
    if (!area) return 0;
    try { return static_cast<std::int32_t>(area->recno()); } catch (...) { return 0; }
}

static std::int32_t safe_reccount(const xbase::DbArea* area) {
    if (!area) return 0;
    try { return static_cast<std::int32_t>(area->recCount()); } catch (...) { return 0; }
}

static std::string safe_area_name(std::size_t slot, const xbase::DbArea* area) {
    try {
        const std::string alias = std::string(workareas::name(slot));
        if (!alias.empty()) return alias;
    } catch (...) {}

    if (area) {
        try {
            const std::string logical = area->logicalName();
            if (!logical.empty()) return logical;
        } catch (...) {}
        try {
            const std::string base = area->dbfBasename();
            if (!base.empty()) return base;
        } catch (...) {}
        try { return area->name(); } catch (...) {}
    }
    return {};
}

} // namespace

WorkAreaCursorRestore::WorkAreaCursorRestore() {
    std::string ignored;
    (void)snapshot(ignored);
}

WorkAreaCursorRestore::~WorkAreaCursorRestore() {
    close();
}

bool WorkAreaCursorRestore::snapshot(std::string& error) {
    error.clear();
    slots_.clear();
    restored_ = false;

    try {
        const std::size_t n = workareas::count();
        slots_.reserve(n);
        for (std::size_t i = 0; i < n; ++i) {
            SlotState state;
            state.slot = i;

            xbase::DbArea* area = nullptr;
            try { area = workareas::db(i); } catch (...) { area = nullptr; }

            state.open = area_is_open(area);
            state.recno = state.open ? safe_recno(area) : 0;
            state.name = safe_area_name(i, area);
            slots_.push_back(std::move(state));
        }
        snapshotted_ = true;
        return true;
    } catch (const std::exception& ex) {
        error = ex.what();
    } catch (...) {
        error = "unable to snapshot workarea cursors";
    }

    snapshotted_ = false;
    return false;
}

bool WorkAreaCursorRestore::restore(std::string& error) noexcept {
    error.clear();
    if (!snapshotted_ || restored_) {
        restored_ = true;
        return true;
    }

    bool ok = true;

    for (const SlotState& state : slots_) {
        if (!state.open) continue;
        if (state.recno <= 0) continue;

        xbase::DbArea* area = nullptr;
        try { area = workareas::db(state.slot); } catch (...) { area = nullptr; }
        if (!area_is_open(area)) continue;

        try {
            const std::int32_t total = safe_reccount(area);
            if (state.recno >= 1 && state.recno <= total) {
                (void)area->gotoRec(state.recno);
                (void)area->readCurrent();
            }
        } catch (const std::exception& ex) {
            ok = false;
            if (error.empty()) error = ex.what();
        } catch (...) {
            ok = false;
            if (error.empty()) error = "unable to restore one or more workarea cursors";
        }
    }

    // Re-sync child workareas to the restored parent cursor state.  This mirrors
    // the Smart Browser safety pattern and is required after relation refreshes
    // have moved child cursors during tuple projection.
    try { relations_api::refresh_if_enabled(); } catch (...) {}

    restored_ = ok;
    if (!ok && error.empty()) error = "unable to restore one or more workarea cursors";
    return ok;
}

void WorkAreaCursorRestore::close() noexcept {
    std::string ignored;
    (void)restore(ignored);
}

} // namespace dottalk::tupleaugment
