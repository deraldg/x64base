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
#include "cli/settings.hpp"
#include "cli/table_state.hpp"
#include "cli/unique_registry.hpp"
#include "xindex/index_manager.hpp"

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

    static long long compute_next_numeric(xbase::DbArea& A, int field1)
    {
        long long mx = std::numeric_limits<long long>::min();

        const int32_t save = A.recno();
        const int32_t total = A.recCount();

        for (int32_t r = 1; r <= total; ++r)
        {
            if (!A.gotoRec(r)) continue;
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
            }
        }

        if (save > 0) {
            A.gotoRec(save);
            A.readCurrent();
        }

        if (mx == std::numeric_limits<long long>::min())
            return 1;

        return mx + 1;
    }

    static void generate_sid_if_needed(xbase::DbArea& A, bool& wrote)
    {
        const int sid = field_index_by_name_ci(A, "SID");
        if (sid <= 0) return;

        const std::string v = A.get(sid);
        if (!trim_copy(v).empty()) return;

        const long long next = compute_next_numeric(A, sid);
        if (append_trace_enabled()) {
            std::cout << "[APPEND TRACE] SID field #" << sid << " next=" << next << "\n";
        }
        A.set(sid, std::to_string(next));
        wrote = true;
    }

    static void generate_registered_uniques(xbase::DbArea& A, bool& wrote)
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
            A.set(idx, std::to_string(next));
            wrote = true;
        }
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

            generate_registered_uniques(A, wrote);
            generate_sid_if_needed(A, wrote);

            if (wrote) {
                if (!A.writeCurrent())
                    return false;
            }

            if (update_index_inline) {
                if (!A.gotoRec(static_cast<std::int32_t>(rn)))
                    return false;
                if (!A.readCurrent())
                    return false;

                append_trace_field_values(A, rn);

                try {
                    auto& im = A.indexManager();

                    if (append_trace_enabled()) {
                        std::cout << "[APPEND TRACE] index backend="
                                  << (im.hasBackend() ? "yes" : "no")
                                  << " type=" << (im.isCdx() ? "CDX" : (im.isCnx() ? "CNX" : "OTHER"))
                                  << " container="" << im.containerPath() << """
                                  << " activeTag="" << im.activeTag() << ""\n";
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
        std::cout << "APPEND: no file open\n";
        return false;
    }

    if (count == 0)
        return true;

    std::string err;
    if (!xbase::locks::try_lock_table(A, &err))
    {
        std::cout << "APPEND: table locked (" << err << ")\n";
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
        std::cout << "APPEND MANY: stopped after "
                  << done << " successful append(s)\n";
        return false;
    }

    if (Settings::instance().talk_on.load())
        std::cout << "Appended " << count << " blank record(s)\n";

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
        std::cout << "APPEND: no file open\n";
        return false;
    }

    std::string err;
    if (!xbase::locks::try_lock_table(A, &err))
    {
        std::cout << "APPEND: table locked (" << err << ")\n";
        return false;
    }

    const bool ok = dottalk_append_blank_raw_locked(A, rn);

    xbase::locks::unlock_table(A);

    if (!ok)
    {
        std::cout << "APPEND failed\n";
        return false;
    }

    return true;
}

bool dottalk_append_many_raw(xbase::DbArea& A, std::size_t count)
{
    if (!A.isOpen())
    {
        std::cout << "APPEND: no file open\n";
        return false;
    }

    if (count == 0)
        return true;

    std::string err;
    if (!xbase::locks::try_lock_table(A, &err))
    {
        std::cout << "APPEND: table locked (" << err << ")\n";
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
        std::cout << "APPEND RAW MANY: stopped after "
                  << done << " successful append(s)\n";
        return false;
    }

    if (Settings::instance().talk_on.load())
        std::cout << "Appended " << count << " raw blank record(s)\n";

    return true;
}

bool dottalk_append_blank_core(xbase::DbArea& A, std::istringstream&)
{
    if (!A.isOpen())
    {
        std::cout << "APPEND: no file open\n";
        return false;
    }

    std::string err;
    if (!xbase::locks::try_lock_table(A, &err))
    {
        std::cout << "APPEND: table locked (" << err << ")\n";
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
        std::cout << "APPEND failed\n";
        return false;
    }

    if (Settings::instance().talk_on.load())
        std::cout << "Appended blank record " << A.recno() << "\n";

    return true;
}