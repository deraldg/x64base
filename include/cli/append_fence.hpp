#pragma once
// @dottalk.file v1
// subsystem: cli
// layer: support
// owns: the table fence taken around a record append
// project: project.x64base.runtime
// lane: OI-043
// owner: member.derald
// status: supported
//
// THE APPEND FENCE -- one guard, and the first brick of the gatekeeper.
//
// WHY (owner, 2026-09-19): "there should only be one common function called for
// increasing the record count and one for decreasing the record count."
//
// The increment is ALREADY one function: ++_rec_count64 occurs exactly once in
// this tree, inside DbArea::appendBlank() (src/xbase/dbf_file.cpp). What was
// missing is a gatekeeper. appendBlank is a raw byte-level operation -- seek to
// the end, write a blank row, patch the count -- and it TAKES NO LOCK. 37 call
// sites in 17 files reach it directly (tools/staging/check_append_callers.py).
//
// MEASURED 2026-09-19, not argued. A foreign LIVE table lock was planted beside
// a table and five doors were tried against it:
//   APPEND BLANK      REFUSED  "table locked (lock exists)"   append_support.cpp
//   SQLSEL INSERT     REFUSED  "refused -- lock exists"       enlist takes it
//   REPLACE           REFUSED  "record is locked (table locked)"
//   bare INSERT       *** GOT THROUGH ***                     cmd_sql_insert.cpp
//   IMPORT            *** GOT THROUGH ***                     cmd_import.cpp
// Two doors let a second engine grow a table this one had fenced. That is the
// "five doors across three files" shape AIF-156 already met for FIELD writes,
// and its recorded answer is the one being followed here: consolidate the
// route, then keep a static gate proving nobody goes around it.
//
// BORROWED-AWARE, AND THAT IS THE WHOLE SUBTLETY. try_lock_table is re-entrant
// for its own process by design -- COMMIT has to write while holding the fence
// it took. So a guard that unconditionally unlocks would TEAR DOWN AN ENCLOSING
// HOLDER'S FENCE on the way out, which is worse than never taking one. The
// guard therefore asks who holds the lock BEFORE taking it and releases only
// what it actually acquired.
//
// That re-entrancy is also what makes a LOOP correct with no second API: hold
// one TableFence around the whole import and let each append inside borrow it.
//
// PRIOR ART, AND IT WAS ALREADY IN THIS TREE. This is cmd_commit.cpp's
// InsertTableLockGuard, moved here rather than copied. A third hand-written
// copy of a lock protocol is how two of them start disagreeing.

#include "xbase.hpp"
#include "xbase_locks.hpp"

#include <cstdint>
#include <string>

namespace cli::fence {

// RAII table fence. `ready` false means the lock was refused and NOTHING may be
// written; `error` says why, in the lock layer's own words.
struct TableFence {
    xbase::DbArea* area   = nullptr;
    bool  acquired_here   = false;
    bool  ready           = true;
    std::string error;

    explicit TableFence(xbase::DbArea& value, bool required = true) : area(&value) {
        if (!required) return;
        xbase::locks::LockHolder holder;
        const bool borrowed = xbase::locks::table_lock_holder(value, &holder) &&
                              holder.owner_id == xbase::locks::current_owner().id;
        if (!xbase::locks::try_lock_table(value, &error)) {
            ready = false;
            return;
        }
        acquired_here = !borrowed;
    }

    ~TableFence() {
        if (!acquired_here || !area) return;
        std::string ignored;
        (void)xbase::locks::unlock_table(
            *area, xbase::locks::current_owner(), &ignored);
    }

    TableFence(const TableFence&)            = delete;
    TableFence& operator=(const TableFence&) = delete;
};

// THE GATEKEEPER. Fence, append, and return the record number the FILE gave the
// row -- never a number decided beforehand (OI-043 option A, owner ruling
// 2026-09-19: a DBF record's identity IS its physical position, so a number
// reserved ahead of the write is a promise about a gap, and a gap cannot exist
// in the file).
//
// Returns 0 on refusal and leaves the table untouched; `err` carries the reason.
// Safe to call inside an enclosing TableFence: the lock is borrowed, not retaken.
inline std::uint64_t append_fenced(xbase::DbArea& A, std::string* err = nullptr) {
    if (!A.isOpen()) {
        if (err) *err = "no open table";
        return 0;
    }
    TableFence fence(A);
    if (!fence.ready) {
        if (err) *err = fence.error.empty() ? std::string("table locked") : fence.error;
        return 0;
    }
    if (!A.appendBlank()) {
        if (err) *err = "append failed";
        return 0;
    }
    // appendBlank ends in gotoRec64(_rec_count64), so the cursor IS the new row.
    const std::uint64_t rn = A.recno64();
    if (rn == 0 && err) *err = "append produced no record number";
    return rn;
}

} // namespace cli::fence
