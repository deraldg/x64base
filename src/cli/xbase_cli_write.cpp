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

#include <cctype>
#include <cstdint>
#include <exception>
#include <string>
#include <unordered_set>

#include "cli/field_constraints.hpp"
#include "xbase_field_getters.hpp"
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


namespace {

// A BLANK IS NOT A VALUE A KEY CAN HOLD, and ONE blank is enough to block. A
// stamped column with a blank row is precisely the state
// FINDING_A_FRESH_PROCESS_ENFORCES_A_KEY_IT_WILL_NOT_MINT measured: the row
// cannot be completed by the engine, which will not mint it, nor by the
// operator, whom the funnel refuses. Refusing the stamp leaves a plain table,
// which is recoverable; allowing it leaves rows that are not.
bool blank_key_value(const std::string& v)
{
    for (const char c : v) {
        if (!std::isspace(static_cast<unsigned char>(c))) return false;
    }
    return true;
}

} // namespace

KeyTravelResult carryPrimaryKey(const DbArea& src, DbArea& dst, KeyTravel choice)
{
    KeyTravelResult r;

    int sf1 = 0;
    try { sf1 = src.primaryFieldIndex(); } catch (...) { sf1 = 0; }
    if (sf1 < 1 || sf1 > static_cast<int>(src.fields().size())) {
        // The source designates nothing. There is nothing to carry and nothing
        // to report; a message here would be noise on every unkeyed COPY.
        r.proceed = true;
        return r;
    }

    const std::string key_name = src.fields()[static_cast<std::size_t>(sf1) - 1].name;

    if (choice == KeyTravel::Drop) {
        r.proceed = true;
        r.detail  = "primary key " + key_name + " not carried (dropped by request)";
        return r;
    }

    // BY NAME, NOT BY INDEX. SORT emits a caller-chosen column subset in a
    // caller-chosen order, so the source's field number means nothing at the
    // destination. Routed through the resolver AIF-157 consolidated ADDTAG and
    // SET UNIQUE ... PRIMARY onto, because a 10-byte descriptor token is not a
    // long logical name.
    int df0 = -1;
    try { df0 = xfg::resolve_field_index_std(dst, key_name); } catch (...) { df0 = -1; }
    if (df0 < 0) {
        r.detail = "primary key " + key_name +
                   " cannot travel: the destination has no field of that name";
        return r;
    }
    const int df1 = df0 + 1;

    // THE SCAN WALKS ALL PHYSICAL RECORDS INCLUDING DELETED ONES, on the same
    // argument compute_next_numeric already stands on: a deleted row can be
    // RECALLed and its key stays reserved until PACK, so a duplicate hiding
    // under a deletion flag is still a duplicate.
    //
    // 64-bit throughout. recCount()/gotoRec() are 32-bit compatibility
    // adapters and this tree's build vector allows more rows than they can
    // address; a truncating scan would report a clean column it never finished
    // reading.
    std::uint64_t saved = 0;
    try { saved = dst.recno64(); } catch (...) { saved = 0; }

    std::uint64_t n = 0;
    try { n = dst.recCount64(); } catch (...) { n = 0; }

    std::unordered_set<std::string> seen;

    for (std::uint64_t rn = 1; rn <= n; ++rn) {
        if (!dst.gotoRec64(rn) || !dst.readCurrent()) {
            r.detail = "primary key " + key_name +
                       " cannot travel: destination record " +
                       std::to_string(rn) + " could not be read";
            break;
        }

        const std::string v = dst.get(df1);

        if (blank_key_value(v)) {
            r.detail = "primary key " + key_name +
                       " cannot travel: destination record " +
                       std::to_string(rn) +
                       " has a blank key, and a stamped blank can never be filled";
            break;
        }

        if (!seen.insert(v).second) {
            r.detail = "primary key " + key_name +
                       " cannot travel: destination record " +
                       std::to_string(rn) + " duplicates an earlier value";
            break;
        }
    }

    if (r.detail.empty()) {
        // setFieldPrimaryDurable() is the metadata block's only writer and it
        // already refuses a destination that cannot record the flag -- a VFP or
        // classic header has nowhere to put one. Its wording is reused rather
        // than duplicated, so one refusal keeps one explanation.
        std::string stamp_err;
        if (dst.setFieldPrimaryDurable(df1, true, &stamp_err)) {
            r.proceed = true;
            r.stamped = true;
            r.detail  = "primary key " + key_name + " carried";
        } else {
            r.detail = "primary key " + key_name + " cannot travel: " + stamp_err;
        }
    }

    // The scan moved the cursor. Put it back: this function is a disposition,
    // not a navigation, and a caller that reads dst afterwards must not have to
    // know that.
    if (saved != 0) {
        try {
            (void)dst.gotoRec64(saved);
            (void)dst.readCurrent();
        } catch (...) { }
    }

    return r;
}

} // namespace xbase::cli
