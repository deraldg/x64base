// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/append_support.cpp
//
// Shared APPEND / APPEND BLANK implementation.
// Generates numeric unique keys and updates indexes.
//
// Raw append policy:
//   - RAW append still populates autokey / unique fields.
//   - RAW append does NOT update attached indexes inline.
//   - Rebuild is expected after RAW MANY bulk operations.
//
// Incremental indexing policy:
//   - Smart append uses the same snapshot-based multi-tag insert model as
//     DELETE/REPLACE/RECALL.
//   - Canonical key construction lives in IndexManager, not here.
//   - APPEND no longer uses the older active-tag/simple inline update path.

#include "cli/append_support.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <iostream>
#include <cstdlib>
#include <iomanip>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xbase_locks.hpp"
#include "cli/command_output.hpp"
#include "cli/settings.hpp"
#include "cli/table_state.hpp"
#include "cli/unique_registry.hpp"
#include "xindex/index_manager.hpp"
#include "xindex/attach.hpp"

extern "C" xbase::XBaseEngine* shell_engine(void);

using cli::Settings;

namespace
{
    static std::string up_copy(std::string s)
    {
        for (char& ch : s)
            ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
        return s;
    }

    static std::string trim_copy(std::string s)
    {
        auto is_space = [](unsigned char ch){ return std::isspace(ch) != 0; };

        while (!s.empty() && is_space(static_cast<unsigned char>(s.front())))
            s.erase(s.begin());

        while (!s.empty() && is_space(static_cast<unsigned char>(s.back())))
            s.pop_back();

        return s;
    }

    static bool append_trace_enabled()
    {
        // Diagnostic drop-in: enabled by default so APPEND lifecycle evidence is visible.
        // Set DOTTALK_APPEND_TRACE=0 to silence after diagnosis.
        const char* v = std::getenv("DOTTALK_APPEND_TRACE");
        if (!v) return true;
        const std::string s = up_copy(trim_copy(v));
        return !(s == "0" || s == "OFF" || s == "FALSE" || s == "NO");
    }

    static std::string key_preview(const xindex::Key& key)
    {
        std::ostringstream os;
        os << "len=" << key.size() << " text=\"";
        for (std::uint8_t b : key) {
            const unsigned char c = static_cast<unsigned char>(b);
            if (c >= 32 && c <= 126) {
                os << static_cast<char>(c);
            } else {
                os << "\\x"
                   << std::hex << std::uppercase << std::setw(2) << std::setfill('0')
                   << static_cast<int>(c)
                   << std::dec << std::nouppercase << std::setfill(' ');
            }
        }
        os << "\"";
        return os.str();
    }

    static void append_trace_field_values(xbase::DbArea& A, std::uint32_t rn)
    {
        if (!append_trace_enabled()) return;

        std::cout << "[APPEND TRACE] recno=" << rn << " current=" << A.recno() << " values";
        const auto defs = A.fields();
        const int limit = static_cast<int>(std::min<std::size_t>(defs.size(), 6));
        for (int f1 = 1; f1 <= limit; ++f1) {
            std::string name;
            try { name = defs[static_cast<std::size_t>(f1 - 1)].name; } catch (...) { name = "?"; }
            std::string val;
            try { val = A.get(f1); } catch (...) { val = "<get-error>"; }
            std::cout << " #" << f1 << "(" << name << ")=\"" << val << "\"";
        }
        std::cout << "\n";
    }

    static void append_trace_snapshot(const xindex::IndexManager::DeleteSnapshot& snap)
    {
        if (!append_trace_enabled()) return;

        std::cout << "[APPEND TRACE] snapshot entries=" << snap.size() << "\n";
        for (const auto& e : snap) {
            std::cout << "[APPEND TRACE]   tag=" << e.tag_upper
                      << " key " << key_preview(e.key) << "\n";
        }
    }

    static int field_index_by_name_ci(xbase::DbArea& A, const std::string& name)
    {
        const std::string want = up_copy(name);
        const auto defs = A.fields();

        for (size_t i = 0; i < defs.size(); ++i) {
            if (up_copy(defs[i].name) == want)
                return static_cast<int>(i) + 1;
        }

        return 0;
    }

    // Highest numeric value currently held in `field1`, plus one.
    //
    // THIS IS A FULL-TABLE SCAN AND THAT IS O(n) PER APPEND, so appending m rows
    // into a table of n costs O(m*(n+m)). Invisible on teaching data, quadratic
    // on anything real. THE FAST PATH IS NOT WRITTEN HERE ON PURPOSE and the
    // reason is a correctness trap rather than effort -- see the note below, so
    // the next person does not "optimise" this into a duplicate-key generator.
    //
    // WHY NOT ASK THE INDEX. cli/order_nav.hpp::order_last_recno() would give
    // the highest key in one seek instead of n reads, and index_manager carries
    // activeTagMatchesField(). Two things must be settled first, and neither is
    // settleable by reading:
    //   1. DELETED ROWS. The scan below walks them DELIBERATELY -- a deleted row
    //      can be RECALLed and its key stays reserved until PACK. An ordered
    //      container may omit deleted rows depending on SET DELETED. If the
    //      highest key sits on a deleted row the index does not show, the fast
    //      path issues a key that is already taken, and the collision only
    //      appears when somebody recalls the row. That is worse than slow.
    //   2. TAG IDENTITY. A tag can be built on an expression, not a bare field.
    //      Matching by tag NAME (tags are conventionally named for their field,
    //      as CDX ADDTAG SID does) is a guess, and a wrong guess here reads the
    //      wrong column's maximum.
    // Both are answerable with a runtime proof against a table with a deleted
    // high key and an expression tag. Until that proof exists, correct and slow
    // beats fast and occasionally wrong.
    //
    // RECNO64: this loop addresses records through the 64-bit accessors. It used
    // int32_t recno()/recCount()/gotoRec(), whose own declaration in xbase.hpp
    // says "use recno64()/recCount64() for the authoritative value" -- so the key
    // generator could not reach the record space X64_METRICS proves in the
    // default suite on every run. The engine's headline claim and its key
    // generator disagreed, and nothing in the suite could see it.
    static long long compute_next_numeric(xbase::DbArea& A, int field1)
    {
        long long mx = std::numeric_limits<long long>::min();

        const std::uint64_t save  = A.recno64();
        const std::uint64_t total = A.recCount64();

        // A value that is present but not parseable as an integer cannot be
        // compared, so it cannot raise the maximum. SILENCE WAS THE DEFECT: the
        // old catch(...) swallowed these, so an overflowing or corrupt key made
        // the maximum read LOW and the next APPEND could hand out a number that
        // is already in the table -- the one way uniqueness-by-construction
        // fails while everybody is doing everything right. Counted and reported.
        std::uint64_t unreadable = 0;
        std::uint64_t first_unreadable_rec = 0;
        std::string   first_unreadable_val;

        for (std::uint64_t r = 1; r <= total; ++r)
        {
            if (!A.gotoRec64(r)) continue;
            if (!A.readCurrent()) continue;

            // Autokey / unique generation must scan deleted physical records too.
            // Deleted rows can be recalled; their keys remain reserved until PACK.
            std::string v = A.get(field1);
            if (v.empty()) continue;

            try
            {
                long long n = std::stoll(v);
                if (n > mx) mx = n;
            }
            catch (...)
            {
                if (unreadable == 0) {
                    first_unreadable_rec = r;
                    first_unreadable_val = v;
                }
                ++unreadable;
            }
        }

        if (save > 0) {
            A.gotoRec64(save);
            A.readCurrent();
        }

        if (unreadable > 0) {
            std::cout << "APPEND: WARNING -- " << unreadable
                      << " value(s) in the key field could not be read as a number "
                      << "and were skipped when computing the next key (first at "
                      << "record " << first_unreadable_rec << ": \""
                      << first_unreadable_val << "\"). The generated key may "
                      << "collide with one of them.\n";
        }

        if (mx == std::numeric_limits<long long>::min())
            return 1;

        return mx + 1;
    }

    // A PLANNED WRITE AND NOT AN IMMEDIATE ONE, AND THE REASON IS MEASURED.
    //
    // compute_next_numeric() SCANS THE TABLE, and a scan MOVES THE RECORD
    // BUFFER: it ends with A.gotoRec64(save); A.readCurrent();, and
    // readCurrent() RELOADS THAT BUFFER FROM DISK. Anything an earlier
    // generator had set in the buffer and not yet written is gone.
    //
    // MEASURED 2026-09-08 on build Sep 07 2026 16:35:05. Table
    // (EMPNO N(6,0), SID N(6,0), LNAME C(12)), EMPNO declared PRIMARY: APPEND
    // produced SID=1 and EMPNO BLANK -- IN THE DECLARING PROCESS, on a build
    // where every PKPOLICY generation marker read green. The declared,
    // header-stamped primary key was computed, set in the buffer, and then
    // destroyed by the NEXT generator's scan; only the last generator's field
    // survived to writeCurrent(). The row came out with a blank primary key
    // that the write funnel then REFUSES to let anyone fill, because a primary
    // key is minted at creation and never edited.
    //
    // WHY NO SPEC SAW IT: every fixture in this tree that generates a key uses
    // a field named SID, which is both the registry's declared field and the
    // one the SID planner below mints by name. One generator, nothing to
    // destroy. A THROWAWAY PROBE separated the two candidate causes in one
    // process: a lone declared field NOT named SID minted correctly, so the
    // registry path works, and the same field beside a SID column did not. It
    // is described rather than cited -- it lived under the ignored tmp/, and a
    // path a reader of this tree cannot open is worse than no path at all.
    //
    // WHY THIS SHAPE rather than re-setting the value after the last scan: the
    // fix has to survive a THIRD generator being added by somebody who never
    // reads this comment. Planning first and applying once makes the invariant
    // STRUCTURAL -- no generator may write into a buffer another generator is
    // still going to disturb -- instead of a rule the next author has to know.
    struct PlannedKey { int field1; std::string value; };

    static void plan_registered_uniques(xbase::DbArea& A, std::vector<PlannedKey>& plan)
    {
        std::vector<std::string> uniq;

        try
        {
            uniq = unique_reg::list_unique_fields(A);
        }
        catch (...)
        {
            return;
        }

        for (const auto& f : uniq)
        {
            const int idx = field_index_by_name_ci(A, f);
            if (idx <= 0) continue;

            const std::string v = A.get(idx);
            if (!trim_copy(v).empty()) continue;

            const long long next = compute_next_numeric(A, idx);
            if (append_trace_enabled()) {
                std::cout << "[APPEND TRACE] unique field " << f
                          << " (#" << idx << ") next=" << next << "\n";
            }
            plan.push_back(PlannedKey{idx, std::to_string(next)});
        }
    }

    static void plan_sid_if_needed(xbase::DbArea& A, std::vector<PlannedKey>& plan)
    {
        const int sid = field_index_by_name_ci(A, "SID");
        if (sid <= 0) return;

        // ALREADY PLANNED BY THE REGISTRY, AND THE BLANK CHECK BELOW CANNOT SEE
        // THAT. A field can be declared PRIMARY and also be named SID -- the
        // PKPOLICY fixture is exactly that table -- and the plan has not been
        // applied to the buffer yet, so A.get() still reads blank. Without this
        // the same field is planned twice; the two values agree today because
        // both come from the same scan of the same column, and relying on that
        // agreement is how a duplicate-key generator gets written by accident.
        for (const PlannedKey& p : plan) {
            if (p.field1 == sid) return;
        }

        const std::string v = A.get(sid);
        if (!trim_copy(v).empty()) return;

        const long long next = compute_next_numeric(A, sid);
        if (append_trace_enabled()) {
            std::cout << "[APPEND TRACE] SID field #" << sid << " next=" << next << "\n";
        }
        plan.push_back(PlannedKey{sid, std::to_string(next)});
    }

    // Shared post-append record initialization.
    // This keeps autokey generation in APPEND, not in rebuild.
    static bool finalize_appended_record(xbase::DbArea& A, bool update_index_inline, std::uint32_t rn)
    {
        bool wrote = false;

        try
        {
            if (!A.readCurrent())
                return false;

            // PLAN FIRST, APPLY ONCE. Every compute_next_numeric() call inside
            // these planners reloads the record buffer from disk, so nothing
            // may be SET until the last scan has finished.
            std::vector<PlannedKey> plan;
            plan_registered_uniques(A, plan);
            plan_sid_if_needed(A, plan);

            if (!plan.empty()) {
                // Re-read rather than trusting the buffer the last scan left
                // behind. A planner that returns early never scans at all, so
                // what the buffer holds here depends on which branch ran --
                // and depending on that is the defect this fix removes.
                if (!A.readCurrent())
                    return false;

                for (const PlannedKey& p : plan) {
                    A.set(p.field1, p.value);
                }
                wrote = true;
            }

            if (wrote) {
                if (!A.writeCurrent())
                    return false;
            }

#if DOTTALK_HAS_XINDEX
            if (update_index_inline) {
                if (!A.gotoRec(static_cast<std::int32_t>(rn)))
                    return false;
                if (!A.readCurrent())
                    return false;

                append_trace_field_values(A, rn);

                try {
                    auto& im = xindex::ensure_manager(A);

                    if (append_trace_enabled()) {
                        std::cout << "[APPEND TRACE] index backend="
                                  << (im.hasBackend() ? "yes" : "no")
                                  << " type=" << (im.isCdx() ? "CDX" : (im.isCnx() ? "CNX" : "OTHER"))
                                  << " container=\"" << im.containerPath() << "\""
                                  << " activeTag=\"" << im.activeTag() << "\"\n";
                    }

                    // Snapshot the completed current row across all relevant tags,
                    // then insert those keys into the active backend.
                    auto snap = im.capture_delete_snapshot_for_current_record();
                    append_trace_snapshot(snap);

                    bool insert_ok = false;
                    if (!snap.empty()) {
                        insert_ok = im.apply_insert_snapshot(
                            snap,
                            static_cast<xindex::RecNo>(rn)
                        );
                    }

                    if (append_trace_enabled()) {
                        std::cout << "[APPEND TRACE] apply_insert_snapshot result="
                                  << (insert_ok ? "true" : "false") << "\n";
                    }
                } catch (const std::exception& e) {
                    if (append_trace_enabled()) {
                        std::cout << "[APPEND TRACE] index insert exception: " << e.what() << "\n";
                    }
                    // Best effort only. Data append succeeds even if inline
                    // index maintenance does not complete.
                } catch (...) {
                    if (append_trace_enabled()) {
                        std::cout << "[APPEND TRACE] index insert exception: unknown\n";
                    }
                    // Best effort only. Data append succeeds even if inline
                    // index maintenance does not complete.
                }
            }
#else
            (void)update_index_inline;
            (void)rn;
#endif

            return true;
        }
        catch (...)
        {
            return false;
        }
    }

} // namespace

bool dottalk_append_many_core(xbase::DbArea& A, std::size_t count)
{
    if (!A.isOpen())
    {
        cli::cmdout::print_prefixed_message("APPEND", dottalk::helpdata::MessageId::NoOpenTable);
        return false;
    }

    if (count == 0)
        return true;

    std::string err;
    if (!xbase::locks::try_lock_table(A, &err))
    {
        cli::cmdout::print_prefixed_message(
            "APPEND",
            dottalk::helpdata::MessageId::AppendTableLocked,
            {{"detail", err}});
        return false;
    }

    bool ok = true;
    std::size_t done = 0;
    std::uint32_t rn = 0;

    for (; done < count; ++done)
    {
        try
        {
            if (!A.appendBlank())
            {
                ok = false;
                break;
            }

            rn = static_cast<std::uint32_t>(A.recno());

            if (!finalize_appended_record(A, /*update_index_inline=*/true, rn))
            {
                ok = false;
                break;
            }
        }
        catch (...)
        {
            ok = false;
            break;
        }
    }

    xbase::locks::unlock_table(A);

    if (!ok)
    {
        cli::cmdout::print_prefixed_message(
            "APPEND",
            dottalk::helpdata::MessageId::AppendManyStopped,
            {{"count", std::to_string(done)}});
        return false;
    }

    if (Settings::instance().talk_on.load())
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::AppendManySuccess,
            {{"count", std::to_string(count)}});

    return true;
}

bool dottalk_append_blank_raw_locked(xbase::DbArea& A, std::uint32_t& rn)
{
    rn = 0;

    try
    {
        if (!A.appendBlank())
            return false;

        rn = static_cast<std::uint32_t>(A.recno());

        // RAW append still initializes autokey / unique fields.
        // It simply skips inline index maintenance.
        return finalize_appended_record(A, /*update_index_inline=*/false, rn);
    }
    catch (...)
    {
        rn = 0;
        return false;
    }
}

bool dottalk_append_blank_raw(xbase::DbArea& A, std::uint32_t& rn)
{
    rn = 0;

    if (!A.isOpen())
    {
        cli::cmdout::print_prefixed_message("APPEND", dottalk::helpdata::MessageId::NoOpenTable);
        return false;
    }

    std::string err;
    if (!xbase::locks::try_lock_table(A, &err))
    {
        cli::cmdout::print_prefixed_message(
            "APPEND",
            dottalk::helpdata::MessageId::AppendTableLocked,
            {{"detail", err}});
        return false;
    }

    const bool ok = dottalk_append_blank_raw_locked(A, rn);

    xbase::locks::unlock_table(A);

    if (!ok)
    {
        cli::cmdout::print_prefixed_message("APPEND", dottalk::helpdata::MessageId::AppendFailed);
        return false;
    }

    return true;
}

bool dottalk_append_many_raw(xbase::DbArea& A, std::size_t count)
{
    if (!A.isOpen())
    {
        cli::cmdout::print_prefixed_message("APPEND", dottalk::helpdata::MessageId::NoOpenTable);
        return false;
    }

    if (count == 0)
        return true;

    std::string err;
    if (!xbase::locks::try_lock_table(A, &err))
    {
        cli::cmdout::print_prefixed_message(
            "APPEND",
            dottalk::helpdata::MessageId::AppendTableLocked,
            {{"detail", err}});
        return false;
    }

    bool ok = true;
    std::uint32_t rn = 0;
    std::size_t done = 0;

    for (; done < count; ++done)
    {
        if (!dottalk_append_blank_raw_locked(A, rn))
        {
            ok = false;
            break;
        }
    }

    xbase::locks::unlock_table(A);

    if (!ok)
    {
        cli::cmdout::print_prefixed_message(
            "APPEND",
            dottalk::helpdata::MessageId::AppendRawManyStopped,
            {{"count", std::to_string(done)}});
        return false;
    }

    if (Settings::instance().talk_on.load())
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::AppendRawManySuccess,
            {{"count", std::to_string(count)}});

    return true;
}

bool dottalk_append_blank_core(xbase::DbArea& A, std::istringstream&)
{
    if (!A.isOpen())
    {
        cli::cmdout::print_prefixed_message("APPEND", dottalk::helpdata::MessageId::NoOpenTable);
        return false;
    }

    std::string err;
    if (!xbase::locks::try_lock_table(A, &err))
    {
        cli::cmdout::print_prefixed_message(
            "APPEND",
            dottalk::helpdata::MessageId::AppendTableLocked,
            {{"detail", err}});
        return false;
    }

    bool ok = false;
    std::uint32_t rn = 0;

    try
    {
        if (A.appendBlank())
        {
            rn = static_cast<std::uint32_t>(A.recno());
            ok = finalize_appended_record(A, /*update_index_inline=*/true, rn);
        }
    }
    catch (...)
    {
        ok = false;
    }

    xbase::locks::unlock_table(A);

    if (!ok)
    {
        cli::cmdout::print_prefixed_message("APPEND", dottalk::helpdata::MessageId::AppendFailed);
        return false;
    }

    if (Settings::instance().talk_on.load())
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::AppendBlankSuccess,
            {{"recno", std::to_string(A.recno())}});

    return true;
}
