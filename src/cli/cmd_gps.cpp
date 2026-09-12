// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// @dottalk.usage v1
// owner: DOT|GPS
// command: GPS
// category: report
// status: supported
// noargs: report
// effect: report
// mutates: cursor-temporary
// usage-access: GPS USAGE
// summary:
//   Report current work-area position, including area slot, table label,
//   physical record number, computed logical row, and the workspace that
//   OWNS the area beside the session's CURRENT workspace.
//
// usage:
//   GPS
//   GPS USAGE
//
// notes:
//   GPS with no arguments reports cursor position.
//   GPS with no open table reports the current area and no-table state.
//   GPS computes logical row by streaming the active order and counting
//   visible records up to the physical record the cursor is on.
//   GPS is an instrument. It restores the cursor and the record buffer it
//   moved, so the position it reports is the position that survives the call.
//   GPS reports WHY there is no logical row when there is none. It never
//   prints a row number that was not derived.
//   GPS rejects arguments it does not recognize rather than treating an
//   unrecognized argument as a request for a position report.
//   GPS reports BOTH the owning and the current workspace, always, including
//   when they agree -- "they agree" and "this build does not check" must not
//   look alike (the R112 ledger's rule). An area owned by nothing reads
//   "(none)", which is a real state rather than an error.
//
// risk:
//   reads_table_records: yes when table is open
//   reads_workspace_membership: yes -- owner of this slot, plus current handle
//   mutates_cursor: temporary during logical-row computation, restored before return
//   mutates_table_data: no
//
// related:
//   GOTO
//   SKIP
//   AREA
//   STATUS
//

// ============================================================================
// WHY THIS FILE IS SHAPED THIS WAY
//
// GPS answers one question -- "where am I" -- and that question is the whole
// engine model in miniature:
//
//   which AREA      addressing   (R121: addressing is absolute)
//   which TABLE     identity     (R130: identity is a key, not an address)
//   which RECORD    position     (RECNO64: the physical recno is the anchor)
//   which ROW       derivation   (R1: derivation downward only -- the logical
//                                 row is derived FROM the physical recno under
//                                 the active order and the visibility filter,
//                                 never stored, never the other way round)
//
// Three rules bind every line below.
//
// R3  -- failure travels in the return value. The order walk can fail. When it
//        does, GPS says so. It does not print the partial count it had reached.
//
// R6  -- absent must not be representable among present. "No logical row"
//        (empty table / off-table cursor / current record filtered out / record
//        not present in the active order / order unreadable) are five distinct
//        states and none of them is the number zero. The previous version
//        returned 0 for four of them and, for a deleted current record, ran the
//        walk to completion and returned the TOTAL VISIBLE COUNT -- a number in
//        the valid range that reads as "you are on the last row."
//
// THE COUNT DISCIPLINE -- a number is only reportable when the authority that
//        produced it holds one kind. compute_logical_row() below returns a kind
//        alongside the number, and the number is only read when the kind is
//        Derived.
//
// RECNO64: recno() and recCount() are the 32-bit compatibility accessors. On a
// table whose value exceeds INT32_MAX they return -1 by design, so that a
// 32-bit consumer sees "out of range" instead of acting on a clamped value.
// GPS was such a consumer: it read recno() into an int, so on the very table
// class this engine exists for it reported "Physical Recno -1, Logical Row 0"
// and called that a position. Everything here is recno64()/recCount64()/
// gotoRec64().
//
// GPS also streams the order rather than materializing it. order_iterate_recnos
// collects every recno into a vector first; asking "where am I" on a table with
// 2^31 records would have allocated ~17 GB to count up to the cursor.
// order_stream_display walks the backend cursor and yields in display order,
// which is what a logical row is counted in.
// ============================================================================

#include <cctype>
#include <cstdint>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "xbase/workspace_membership.hpp"
#include "workareas.hpp"
#include "cli/command_output.hpp"
#include "cli/order_iterator.hpp"
#include "help/helpdata_messages.hpp"


namespace {

const char* const GPS_CMD = "GPS";

std::string gps_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

std::string gps_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

// Strip the leading verb, if the dispatcher handed us the whole line, and
// return whatever the caller actually typed after it.
std::string gps_arg_tail(const std::string& raw)
{
    std::string t = gps_upper(gps_trim(raw));
    if (t == "GPS") return "";
    if (t.rfind("GPS ", 0) == 0) t = gps_upper(gps_trim(t.substr(4)));
    return t;
}

bool is_gps_usage_word(const std::string& tail)
{
    return tail == "USAGE" || tail == "HELP" || tail == "?";
}

void print_gps_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GpsUsageText);
}

// ---------- visibility ------------------------------------------------------
// Default reporting semantics: hide deleted rows from logical-row counting.
//
// OPEN ITEM -- this filter is hardcoded here rather than read from the session's
// SET DELETED state. When SET DELETED is OFF, LIST shows deleted rows and counts
// them, and GPS does not. That is two answers to one question about the same
// table (R5). It is left as-is deliberately: changing it changes the number GPS
// prints and is a ruling, not a repair. Recorded rather than silently altered.
bool pass_deleted_filter(const xbase::DbArea& a)
{
    return !a.isDeleted();
}

// ---------- logical row derivation ------------------------------------------
enum class LogicalRowKind {
    Derived,      // walked the order, reached the physical record, counted to it
    NoRecords,    // the table holds no records
    OffTable,     // physical is outside 1..recCount64 (BOF / EOF / never positioned)
    NotVisible,   // the record is present but filtered out -- it HAS no logical row
    NotInOrder,   // the record is present and visible but the order never yielded it
    OrderFailed,  // the active order could not be read
};

struct LogicalRowResult {
    LogicalRowKind kind = LogicalRowKind::OffTable;
    std::uint64_t  row  = 0;  // read ONLY when kind == Derived
    std::string    err;       // read ONLY when kind == OrderFailed
};

LogicalRowResult compute_logical_row(xbase::DbArea& a, std::uint64_t physical)
{
    LogicalRowResult out;

    const std::uint64_t total = a.recCount64();
    if (total == 0)                        { out.kind = LogicalRowKind::NoRecords; return out; }
    if (physical < 1 || physical > total)  { out.kind = LogicalRowKind::OffTable;  return out; }

    // GPS is an instrument: it must not move the thing it is measuring. The
    // walk below repositions the cursor and refills the record buffer on every
    // step. Both are restored before this function returns.
    const std::uint64_t saved = a.recno64();

    std::uint64_t logical             = 0;
    bool          saw_physical        = false;
    bool          visible_at_physical = false;

    cli::OrderIterSpec spec{};
    std::string err;

    const bool walked = cli::order_stream_display(
        a,
        /*reverse=*/false,
        [&](std::uint64_t rn) -> bool
        {
            if (rn == 0 || rn > total) return true;

            const bool is_target = (rn == physical);

            if (!a.gotoRec64(rn) || !a.readCurrent()) {
                // Could not read the row. If it is the one we were asked about,
                // stop: we cannot say whether it is visible, and guessing is
                // what this file exists to stop doing.
                if (is_target) { saw_physical = true; visible_at_physical = false; return false; }
                return true;
            }

            const bool visible = pass_deleted_filter(a);
            if (visible) ++logical;

            if (is_target) {
                saw_physical        = true;
                visible_at_physical = visible;
                return false;   // stop AT the target, visible or not
            }
            return true;
        },
        &spec,
        &err);

    // Restore before classifying, so every exit below leaves the cursor where
    // the caller had it.
    if (saved >= 1 && saved <= total) {
        a.gotoRec64(saved);
        a.readCurrent();
    }

    if (!walked) {
        out.kind = LogicalRowKind::OrderFailed;
        out.err  = err.empty() ? std::string("active order could not be read") : err;
        return out;
    }
    if (!saw_physical)        { out.kind = LogicalRowKind::NotInOrder; return out; }
    if (!visible_at_physical) { out.kind = LogicalRowKind::NotVisible; return out; }

    out.kind = LogicalRowKind::Derived;
    out.row  = logical;
    return out;
}

// The logical-row cell of the report. A number ONLY when one was derived.
std::string logical_row_cell(const LogicalRowResult& r)
{
    switch (r.kind) {
        case LogicalRowKind::Derived:     return std::to_string(r.row);
        case LogicalRowKind::NoRecords:   return "none (table has no records)";
        case LogicalRowKind::OffTable:    return "none (cursor is not on a record)";
        case LogicalRowKind::NotVisible:  return "none (record is filtered out)";
        case LogicalRowKind::NotInOrder:  return "none (record not present in the active order)";
        case LogicalRowKind::OrderFailed: return "unknown (order walk failed)";
    }
    return "unknown";
}

// The physical-recno cell. recno64() is authoritative; the states that are not
// a record are named, not printed as 0.
std::string physical_recno_cell(const xbase::DbArea& a)
{
    const std::uint64_t rn    = a.recno64();
    const std::uint64_t total = a.recCount64();

    if (total == 0)          return "none (table has no records)";
    if (rn == 0)             return "none (BOF)";
    if (rn > total)          return "none (EOF)";
    return std::to_string(rn);
}


// AIF-078 / 2026-08-29, owner instruction. ONE writer for the workspace line,
// called from BOTH of GPS's exits -- the no-table one and the open-table one.
// It is a function rather than two copies because two copies of an output
// contract drift, which is the defect this file's own header warns about under
// "three declarations of a command surface".
//
// owner 0 renders "(none)": an area owned by no workspace is a REAL state that
// reconcile_unregistered_areas() calls a registration defect, and a zero
// printed as a name is how you find one.
void print_workspace_line(std::size_t cur_area)
{
    // x64: workareas::current_slot() answers std::size_t, while the membership
    // table keys engine slots as std::int32_t (Entry::members is
    // std::vector<std::int32_t>). NARROW ONCE, HERE, WITH THE BOUND STATED
    // RATHER THAN ASSUMED -- an `int` parameter took the size_t silently on
    // g++ and is C4267 on MSVC, which is how this was caught.
    //
    // xbase::MAX_AREA is the real domain bound, so a legal slot always fits.
    // A value outside it cannot be a member of any workspace, and 0 is the
    // "(none)" sentinel that says so rather than a value that pretends.
    const std::uint64_t owner_h =
        (cur_area < static_cast<std::size_t>(xbase::MAX_AREA))
            ? xbase::workspace::owner_of_slot(static_cast<std::int32_t>(cur_area))
            : 0;
    const std::uint64_t cur_h = xbase::workspace::current_handle();
    auto nm = [](std::uint64_t h) -> std::string {
        return h == 0 ? std::string("(none)") : xbase::workspace::name_of(h);
    };
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::GpsWorkspaceLineText,
        {
            {"owner",          nm(owner_h)},
            {"owner_handle",   std::to_string(owner_h)},
            {"current",        nm(cur_h)},
            {"current_handle", std::to_string(cur_h)}
        });
}

} // namespace

// ---------- main command ----------------------------------------------------
void cmd_GPS(xbase::DbArea& current, std::istringstream& iss)
{
    const std::string tail = gps_arg_tail(iss.str());

    if (is_gps_usage_word(tail)) {
        print_gps_usage();
        return;
    }
    if (!tail.empty()) {
        // An argument GPS does not understand is not a position request. The
        // previous version reported the cursor for ANY argument, so a typo
        // returned a plausible answer to a question that was not asked.
        cli::cmdout::print_note(GPS_CMD, "unrecognized argument: " + tail);
        print_gps_usage();
        return;
    }

    const std::size_t cur_area = workareas::current_slot();

    // R5 -- one tree, one ladder. The dispatcher hands GPS a DbArea reference;
    // workareas is asked for the slot number. Nothing else in this function
    // proves those are the same area. If they disagree, GPS must not print the
    // pair as though it had been verified.
    const xbase::DbArea* by_slot = workareas::current_db();
    if (by_slot != &current) {
        cli::cmdout::print_note(
            GPS_CMD,
            "engine current area (slot " + std::to_string(cur_area) +
            ") is not the area handed to GPS -- slot and table below may not "
            "describe the same area");
    }

    if (!current.isOpen()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::GpsNoTableCursorLineText,
            {
                {"area",     std::to_string(cur_area)},
                {"occupied", workareas::occupied_desc()}
            });
        // "Both, ALWAYS" has to mean here too. The first cut returned before
        // this line and GPS with no table open reported no workspace at all --
        // which is the state a reader is MOST likely to be lost in, and the
        // current workspace is perfectly well defined with nothing open.
        // Caught on the first run, 2026-08-29, because the run began with a
        // bare GPS and the new line simply was not there.
        print_workspace_line(cur_area);
        return;
    }

    // Identity. workareas::current() can be null (no engine bound, or the slot
    // is out of range); the previous version dereferenced it inside a try/catch,
    // which does not catch a null dereference. It also wrapped recno(), which is
    // noexcept and cannot throw -- a guard that could only ever guard nothing.
    std::string table_name;
    if (const workareas::WorkArea* wa = workareas::current_const()) {
        table_name = wa->label();
    } else {
        table_name = current.name();
    }
    if (table_name.empty()) {
        table_name = cli::cmdout::message_text(dottalk::helpdata::MessageId::GpsUnnamedTableText);
    }

    const std::string      recno_cell = physical_recno_cell(current);
    const LogicalRowResult logical    = compute_logical_row(current, current.recno64());

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::GpsCursorLineText,
        {
            {"area",        std::to_string(cur_area)},
            {"occupied",    workareas::occupied_desc()},
            {"table",       table_name},
            {"recno",       recno_cell},
            {"logical_row", logical_row_cell(logical)}
        });

    // 2026-08-29, owner instruction. BOTH workspaces, ALWAYS, even when they
    // agree. The R112 ambiguity ledger's rule applied to a second instrument:
    // it prints at zero so that "they agree" and "this build does not check"
    // cannot look alike. They diverge the moment SELECT reaches an area another
    // workspace owns -- the session is in one, the area belongs to the other --
    // and a report naming only the session would be a label describing
    // something other than the thing beneath it. AIF-148, written the same day,
    // is exactly that failure one layer down.
    //
    // owner 0 renders "(none)", which is a REAL state and not an error: an area
    // can be open and belong to no workspace, which reconcile_unregistered_areas
    // calls a defect in registration. This line is therefore an instrument for
    // that too, and it is the only place it would be visible on one area.
    print_workspace_line(cur_area);

    if (logical.kind == LogicalRowKind::OrderFailed) {
        cli::cmdout::print_note(GPS_CMD, "order walk failed: " + logical.err);
    }
}
