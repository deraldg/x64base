// dli/browse_edit.cpp - PATCHED
#include "xbase.hpp"
#include "dli/browse_edit.hpp"
#include "dli/replace_api.hpp"
#include <sstream>
#include <stdexcept>

namespace dli {

static Hooks g_hooks{};

void set_hooks(const Hooks& h) { g_hooks = h; }

EditSession begin_edit(xbase::DbArea& db) {
    EditSession es;
    es.db = &db;
    es.active = true;
    // Do NOT capture recno here - it can become stale
    return es;
}

bool stage(EditSession& es, const std::string& field, const std::string& raw) {
    if (!es.active || !es.db) return false;
    es.staged[field] = raw;
    return true;
}

static bool is_memo(xbase::DbArea& db, const std::string& field) {
    if (g_hooks.field_type) {
        char t = g_hooks.field_type(db, field);
        return t == 'M' || t == 'm';
    }
    return false;
}

bool commit(EditSession& es, std::string& err) {
    if (!es.active || !es.db) {
        err = "No active edit session.";
        return false;
    }

    auto& db = *es.db;
    long long original_recno = db.recno();   // capture right before changes

    for (const auto& kv : es.staged) {
        bool ok = false;
        if (is_memo(db, kv.first)) {
            ok = do_replace_memo_text(db, kv.first, kv.second, &err);
        } else {
            ok = do_replace_text(db, kv.first, kv.second, &err);
        }
        if (!ok) return false;
    }

    es.active = false;
    es.staged.clear();

    if (g_hooks.after_commit_reposition) {
        g_hooks.after_commit_reposition(db, original_recno, es.staged);  // note: staged is now empty
    }
    if (g_hooks.refresh_row) {
        g_hooks.refresh_row(db);
    }

    return true;
}

void cancel(EditSession& es) {
    es.active = false;
    es.staged.clear();
}

} // namespace dli