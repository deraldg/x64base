// A TYPED lock provider: calls xbase::locks directly instead of speaking console
// text. AIF-120, R57.
//
// R47.2 built the provider on DotTalk++ command text -- SELECT <alias>; LOCK TABLE.
// R50 through R52 proved that path against the real binary, so it works. But the
// house GUI contract (docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md) lists
//
//     "parsing console text as the only contract for new native GUI features"
//
// as an anti-pattern, with a sunset clause: console parsing "is acceptable as a
// compatibility bridge while the shared runtime API is being extracted. It should
// be replaced by typed runtime APIs where the core already exposes stable state."
//
// For Tk and Python there is no alternative. For a generated wx C++ frontend there
// is: include/xbase_locks.hpp is stable, typed and owner-aware, and strictly richer
// than the LOCK/UNLOCK student commands -- it returns an error string, it can report
// the owner, and it can clean up after itself.
//
// This header is SEPARATE on purpose. Including it links the frontend against the
// engine; not including it leaves uidef_rt.h dependency-free for the text path. The
// choice belongs to the target, not to the generator (R57.1).
#pragma once
// Deliberately does NOT include uidef_rt.h. That header pulls in <wx/wx.h>, and
// nothing here needs a toolkit -- only the engine. Spelling the provider's type
// out instead of naming Runtime::LockProvider keeps this header compilable, and
// therefore TESTABLE, on any machine with the engine headers and no GUI stack.
// The type is identical; `rt.set_lock_provider(uidef::xbase_lock_provider(...))`
// still compiles because std::function is the same type either way.
#include "xbase.hpp"
#include "xbase_locks.hpp"

#include <algorithm>
#include <functional>
#include <string>
#include <vector>

// !! RECORD GRANULARITY IS UNSAFE FOR ANY HANDLER THAT WRITES !! (R57.2)
//
// src/xbase/dbarea.cpp already locks per write: the field-write path calls
// try_lock_record(*this, recno64()), performs the write, then unlock_record(...).
// And xbase::locks is re-entrant WITHOUT A DEPTH COUNT --
//
//     // Re-entrant lock in same process/session.
//     if (meta.owner == me.id) { return true; }
//
// -- so a handler that holds a record lock and then writes gets this:
//
//     handler   try_lock_record(R)      -> creates the lock file
//     DbArea    try_lock_record(R)      -> same owner, validates, returns true
//     DbArea    write
//     DbArea    unlock_record(R)        -> owner matches, DELETES the lock file
//     handler   ...still believes it holds R. It does not.
//
// The innermost unlock wins. Table granularity is unaffected: DbArea takes RECORD
// locks, and R54 ruled the two namespaces independent, so its unlock cannot reach
// a table lock. Until the engine counts nesting or exposes a scoped guard, pass
// record_granularity = false for any domain a handler writes to.

namespace uidef {

/// alias -> the open work area. The runtime NEVER opens areas: R53.4 rules that a
/// conforming frontend opens every SOURCE alias into its own work area before it
/// fires any handler. A resolver returning nullptr means that rule was broken, and
/// the acquisition is refused rather than silently skipped.
using AreaResolver = std::function<xbase::DbArea*(const std::string& alias)>;

/// Build a LockProvider that calls xbase::locks.
///
/// Ordering and all-or-nothing behaviour are identical to `uidef::lock_provider`'s,
/// because they are the same ruling (R48.4, R50.1): sorted on acquire, reversed on
/// release, and a partial acquisition is rolled back before returning false.
using LockProviderFn =
    std::function<bool(bool acquire, const std::vector<std::string>& aliases)>;

inline LockProviderFn xbase_lock_provider(
        AreaResolver resolve,
        bool record_granularity = false,
        std::function<void(const std::string&)> log = nullptr) {
    return [resolve, record_granularity, log](
               bool acquire, const std::vector<std::string>& aliases) -> bool {
        std::vector<std::string> in_order(aliases);
        std::sort(in_order.begin(), in_order.end());
        const xbase::locks::Owner& me = xbase::locks::current_owner();

        // R57.2, runtime-proven: at record granularity the caller's lock does not
        // survive its own write. Said at the call site, not only in a comment at
        // the top of a header -- R52's own complaint about where rules live.
        if (record_granularity && acquire && log) {
            log("WARNING record granularity: DbArea's write path unlocks this "
                "record when the write completes (R57.2). Safe only for a handler "
                "that does not write.");
        }

        auto note = [&log](const std::string& s) { if (log) log(s); };

        // recno64(), not recno(): the 32-bit adapter returns -1 rather than clamping
        // (include/xbase.hpp), and try_lock_record takes a uint64_t. Locking record
        // -1 would be a silent no-op on any table past 2^31 records.
        auto release_one = [&](const std::string& al) {
            xbase::DbArea* a = resolve(al);
            if (!a) return;
            std::string err;
            const bool ok = record_granularity
                ? xbase::locks::unlock_record(*a, a->recno64(), me, &err)
                : xbase::locks::unlock_table(*a, me, &err);
            if (!ok) note("unlock " + al + ": " + err);
        };

        if (!acquire) {
            for (auto it = in_order.rbegin(); it != in_order.rend(); ++it) release_one(*it);
            return true;
        }

        std::vector<std::string> taken;
        for (const std::string& al : in_order) {
            xbase::DbArea* a = resolve(al);
            std::string err;
            bool ok = false;
            if (!a) {
                err = "alias is not open -- R53.4 requires the frontend to open "
                      "every SOURCE alias before firing a handler";
            } else {
                ok = record_granularity
                    ? xbase::locks::try_lock_record(*a, a->recno64(), me, &err)
                    : xbase::locks::try_lock_table(*a, me, &err);
            }
            if (ok) { taken.push_back(al); continue; }
            note("lock " + al + ": " + err);
            for (auto it = taken.rbegin(); it != taken.rend(); ++it) release_one(*it);
            return false;
        }
        return true;
    };
}

/// Who holds this record, if anyone. The text path cannot answer this at all --
/// `LOCK WHO <n>` exists but the provider would have to render a record number into
/// a command, which R48.2 forbids. Typed, the question is just a call.
inline bool locked_by_other(xbase::DbArea& area, std::string* owner_out = nullptr) {
    std::string who;
    if (!xbase::locks::is_record_locked(area, area.recno64(), &who)) return false;
    if (owner_out) *owner_out = who;
    return who != xbase::locks::current_owner().id;
}

}  // namespace uidef
