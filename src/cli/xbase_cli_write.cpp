// @dottalk.file v1
// subsystem: cli
// layer: source
// owns: xbase::cli field-write funnel
// project: project.x64base.runtime
// lane: AIF-156
// owner: member.derald
// status: supported

// xbase_cli_write.cpp
//
// THE FIRST DEFINITION OF A CONTRACT THAT WAS DECLARED ON 2026-07-30 AND NEVER
// BUILT. include/xbase_cli.hpp described the buffered/direct field-write
// wrapper and no translation unit ever defined it, included it, or called it.
// It was flagged the day it was written ("a link error waiting for its first
// caller") and again six weeks later by the header reachability gate, which
// listed it as unreachable and baselined it. Neither detection reached the
// write path, because an unreachable header looks like dead weight rather than
// like a missing floor.
//
// WHAT THE MISSING FLOOR COST. cmd_replace.cpp and cmd_calcwrite.cpp each
// hand-rolled the same TABLE ON / TABLE OFF fork, so one logical operation --
// "write a value into a field" -- became several separate doors. AIF-156 then
// needed a place to refuse a write to a PRIMARY key and found no such place:
// the SQL side had evaluate_store_expression and got both its arms green off
// one wiring, while the native side had a fork per command and would have
// needed an arm per command to prove anything.
//
// WHAT THIS FILE DOES NOT DO. It does not print. Message text and its prefix
// belong to the command -- REPLACE and CALCWRITE say different things about
// the same write -- so every outcome here is returned, never rendered.

#include "xbase_cli.hpp"

#include <cstdint>
#include <exception>
#include <string>

#include "cli/field_constraints.hpp"
#include "cli/table_state.hpp"
#include "workarea_util.hpp"

namespace xbase::cli {

int resolve_current_index(DbArea& area)
{
    try {
        return ::cli::slot_of_area(&area);
    } catch (...) {
        return -1;
    }
}

void mark_all_fields_stale_best_effort(DbArea& area, int area0)
{
    if (!dottalk::table::in_range(area0)) return;
    int n = 0;
    try { n = area.fieldCount(); } catch (...) { return; }
    for (int f = 1; f <= n; ++f) {
        try { dottalk::table::mark_stale_field(area0, f); } catch (...) { }
    }
}

namespace {

// The one gate. Both entry points below ask it before anything is staged or
// written, so a refusal costs nothing and leaves no partial state.
//
// A NULL IS PRESENTED TO THE GATE AS AN EMPTY STORED VALUE. That is honest for
// the question actually being asked: today the only constraint enforced here
// is PRIMARY, which refuses a write to the field REGARDLESS of the value, so
// the value is not consulted. If a future constraint does consult it, this is
// the line that has to grow a real null representation rather than pretending
// a null is a blank -- noted here because the next person will read the empty
// string as an oversight.
bool gate(const DbArea& area, int field1, const std::string& stored_value,
          std::string* err)
{
    std::string constraint_error;
    if (dottalk::constraints::validate_field_constraint_for_store(
            area, field1, stored_value, constraint_error)) {
        return true;
    }
    if (err) *err = constraint_error;
    return false;
}

} // namespace

bool gateFieldWrites(const DbArea& area,
                     const std::vector<std::pair<int, std::string>>& writes,
                     std::string* err,
                     int* refused_field1)
{
    if (err) err->clear();
    if (refused_field1) *refused_field1 = 0;

    // Ask about EVERY field before the caller writes ANY of them. The loop
    // stops at the first refusal because that is already the whole answer:
    // the caller must abandon the entire edit, so enumerating the rest would
    // cost work to produce a message nobody acts on differently.
    for (const auto& w : writes) {
        if (gate(area, w.first, w.second, err)) continue;
        if (refused_field1) *refused_field1 = w.first;
        return false;
    }
    return true;
}

bool replaceFieldStored(DbArea& area, int field1, const std::string& stored_value,
                        std::string* err)
{
    if (err) err->clear();

    if (!gate(area, field1, stored_value, err)) return false;

    const int area0 = resolve_current_index(area);

    // TABLE ON -- stage into the buffer. No lock, no physical write.
    if (area0 >= 0 && dottalk::table::is_enabled(area0)) {
        std::uint64_t recno = 0;
        try { recno = area.recno64(); } catch (...) { recno = 0; }
        if (recno == 0) {
            if (err) *err = "no current record";
            return false;
        }

        auto& tb = dottalk::table::get_tb(area0);

        std::uint64_t field_mask[dottalk::table::kWords]{};
        const int fldIndex0 = field1 - 1;
        const int word = fldIndex0 / 64;
        const int bit  = fldIndex0 % 64;
        if (word < 0 || word >= dottalk::table::kWords) {
            if (err) *err = "field index out of range for the change mask";
            return false;
        }
        field_mask[word] |= (std::uint64_t{1} << bit);

        const int je_priority = tb.add_change(
            recno, dottalk::table::CHANGE_UPDATE, field_mask, field1, stored_value);

        // Write-ahead redo log, only under TABLE BUFFER PERSISTENT. Journal the
        // exact buffered edit -- recno, the priority add_change assigned, and
        // the value -- so history mode keeps every retained edit per field
        // rather than a last-write-wins snapshot.
        if (dottalk::table::is_persistent_enabled(area0)) {
            dottalk::table::ChangeEntry je;
            je.recno = recno;
            je.dirty_flags = dottalk::table::CHANGE_UPDATE;
            je.priority = je_priority;
            je.new_values[field1] = stored_value;
            (void)dottalk::table::journal_note_change(area0, je);
        }

        if (!dottalk::table::is_dirty(area0)) dottalk::table::set_dirty(area0, true);
        dottalk::table::mark_stale_field(area0, field1);
        return true;
    }

    // TABLE OFF -- the engine mutation funnel owns the record lock, the
    // physical write, and the CDX/LMDB replace-snapshot update.
    std::string before;
    std::string after;
    try { before = area.get(field1); } catch (...) { before.clear(); }

    std::string write_err;
    bool ok = false;
    try {
        ok = area.replaceFieldStored(field1, stored_value, &write_err);
    } catch (const std::exception& e) {
        if (err) *err = e.what();
        return false;
    } catch (...) {
        if (err) *err = "write failed";
        return false;
    }

    if (!ok) {
        if (err) *err = write_err.empty() ? std::string("write failed") : write_err;
        return false;
    }

    try { after = area.get(field1); } catch (...) { after.clear(); }
    if (area0 >= 0 && before != after) dottalk::table::mark_stale_field(area0, field1);

    // True with a non-empty err means the record IS on disk but index
    // maintenance afterwards failed. Pass it up unflattened and mark the field
    // stale, so the divergence is recorded rather than printed over.
    if (!write_err.empty()) {
        if (area0 >= 0) dottalk::table::mark_stale_field(area0, field1);
        if (err) *err = write_err;
    }
    return true;
}

bool replaceFieldNull(DbArea& area, int field1, bool make_null, std::string* err)
{
    if (err) err->clear();

    if (!gate(area, field1, std::string(), err)) return false;

    bool nullable = false;
    try { nullable = area.fieldIsNullable(field1); } catch (...) { nullable = false; }
    if (!nullable) {
        if (err) {
            *err = "field is not nullable; its descriptor carries no null flag, "
                   "so there is no bit to record NULL in. Nothing was written";
        }
        return false;
    }

    const int area0 = resolve_current_index(area);

    // See the header: the buffer stages one string per field and cannot say
    // NULL, so buffering one would commit a blank that reads back as not-null.
    if (area0 >= 0 && dottalk::table::is_enabled(area0)) {
        if (err) {
            *err = "NULL cannot be buffered -- the table buffer stores a value "
                   "per field and has no way to say NULL, so buffering one "
                   "would commit a blank instead. COMMIT or ROLLBACK, then "
                   "retry with TABLE BUFFER off. Nothing was written";
        }
        return false;
    }

    std::string write_err;
    bool ok = false;
    try {
        ok = area.replaceFieldNull(field1, make_null, &write_err);
    } catch (const std::exception& e) {
        if (err) *err = e.what();
        return false;
    } catch (...) {
        if (err) *err = "write failed";
        return false;
    }

    if (!ok) {
        if (err) *err = write_err.empty() ? std::string("write failed") : write_err;
        return false;
    }

    if (area0 >= 0) dottalk::table::mark_stale_field(area0, field1);

    // Same three-state return as the value path: written, but index not
    // maintained.
    if (!write_err.empty() && err) *err = write_err;
    return true;
}

} // namespace xbase::cli
