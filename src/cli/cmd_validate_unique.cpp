// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]
//
// Scans current work area and reports duplicates for the given field.
// REPAIR is intended for numeric unique/autokey-style fields:
//   - blank values are assigned new numbers
//   - duplicate values keep the first occurrence
//   - later duplicates are assigned new numbers

// @dottalk.usage.voluntary v1
// NOT UNDER CONTRACT -- voluntary description, offered not promised.
// Nothing verifies this block and nothing may fail because of it.
// The binding identity for this surface is the @dottalk.subusage
// contract on its ladder arm in src/cli/cmd_set.cpp.
// owner: DOT|VALIDATE_UNIQUE
// documents: VALIDATE UNIQUE
// category: validation
// status: supported
// noargs: usage
// effect: validate
// mutates: optional-table-data
// usage-access: VALIDATE UNIQUE USAGE
// summary:
//   Scan the current work area for duplicate/blank values in a field, optionally
//   repairing numeric/autokey-style duplicate values.
//
// usage:
//   VALIDATE UNIQUE USAGE
//   VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]
//
// examples:
//   VALIDATE UNIQUE FIELD SID
//   VALIDATE UNIQUE FIELD EMAIL IGNORE DELETED
//   VALIDATE UNIQUE FIELD SID REPAIR
//   VALIDATE UNIQUE FIELD SID REPORT TO tmp\sid_dupes.txt
//
// notes:
//   VALIDATE UNIQUE USAGE prints usage before open-table checks.
//   REPAIR currently supports numeric/autokey-style fields only.
//   REPORT TO writes a duplicate report file.
//   Without REPAIR this command scans and reports only.
//
// risk:
//   requires_open_table: yes except usage
//   scans_records: yes
//   writes_files: REPORT TO <path>
//   mutates_table_data: REPAIR
//
// related:
//   VALIDATE
//   RULE
//

#include <sstream>
#include <string>
#include <iostream>
#include <fstream>
#include <unordered_map>
#include <vector>
#include <cctype>
#include <algorithm>
#include <limits>

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/unique_registry.hpp"

using namespace textio;


static void print_validate_unique_usage()
{
    std::cout
        << "Usage:\n"
        << "  VALIDATE UNIQUE USAGE\n"
        << "  VALIDATE UNIQUE                (all fields declared via SET UNIQUE)\n"
        << "  VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]\n"
        << "Examples:\n"
        << "  VALIDATE UNIQUE FIELD SID\n"
        << "  VALIDATE UNIQUE FIELD EMAIL IGNORE DELETED\n"
        << "  VALIDATE UNIQUE FIELD SID REPAIR\n"
        << "  VALIDATE UNIQUE FIELD SID REPORT TO tmp\\sid_dupes.txt\n"
        << "Notes:\n"
        << "  - REPAIR may mutate numeric/autokey-style field values.\n"
        << "  - REPORT TO writes a duplicate report file.\n";
}

static inline std::string upcopy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

static int field_index_by_name(xbase::DbArea& A, const std::string& nameU) {
    auto defs = A.fields();
    int idx = 1;
    for (const auto& f : defs) {
        std::string U = f.name;
        for (auto& c : U) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        if (U == nameU) return idx;
        ++idx;
    }
    return 0;
}

static inline void rtrim_spaces(std::string& s) {
    while (!s.empty() && (unsigned char)s.back() == ' ') s.pop_back();
}

static inline bool is_blank_value(const std::string& s) {
    return s.empty();
}

static bool parse_long_long_strict(const std::string& s, long long& out) {
    if (s.empty()) return false;

    size_t start = 0;
    if (s[0] == '+' || s[0] == '-') start = 1;
    if (start >= s.size()) return false;

    for (size_t i = start; i < s.size(); ++i) {
        if (!std::isdigit(static_cast<unsigned char>(s[i])))
            return false;
    }

    try {
        out = std::stoll(s);
        return true;
    } catch (...) {
        return false;
    }
}

static bool field_is_numericish(xbase::DbArea& A, int idx) {
    const auto defs = A.fields();
    if (idx < 1 || idx > (int)defs.size()) return false;

    const char t = (char)std::toupper((unsigned char)defs[(size_t)(idx - 1)].type);
    return t == 'N' || t == 'I' || t == 'Y' || t == 'F' || t == 'B';
}

static long long compute_max_numeric_value(xbase::DbArea& A, int idx, bool ignoreDeleted) {
    long long mx = std::numeric_limits<long long>::min();
    const std::int64_t total = static_cast<std::int64_t>(A.recCount64());
    const std::int64_t save = static_cast<std::int64_t>(A.recno64());

    for (std::int64_t r = 1; r <= total; ++r) {
        if (!A.gotoRec64(static_cast<std::uint64_t>(r))) continue;
        if (ignoreDeleted) {
            try { if (A.isDeleted()) continue; } catch (...) {}
        }

        std::string val;
        try {
            val = A.get(idx);
        } catch (...) {
            continue;
        }

        rtrim_spaces(val);

        long long n = 0;
        if (parse_long_long_strict(val, n)) {
            if (n > mx) mx = n;
        }
    }

    if (save > 0) {
        A.gotoRec64(static_cast<std::uint64_t>(save));
    }

    if (mx == std::numeric_limits<long long>::min())
        return 0;

    return mx;
}

// REPAIR routes through DbArea::replaceFieldStored(), which takes a per-record
// lock and maintains the active index. Two things can therefore go wrong for an
// individual record without invalidating the pass as a whole, and both must be
// visible rather than absorbed into a bare "updated N record(s)" count:
//
//   skipped   -- not written at all (record locked by another process, or the
//                write failed). The duplicate/blank value is still there.
//   unindexed -- written, but index maintenance afterwards failed. The value is
//                corrected on disk while an active tag still points at the old
//                one, so that record needs a REINDEX/REBUILD to be findable.
static void report_repair_exceptions(const std::vector<std::int64_t>& skipped,
                                     const std::vector<std::int64_t>& unindexed)
{
    auto print_recnos = [](const std::vector<std::int64_t>& v) {
        const std::size_t preview = std::min<std::size_t>(5, v.size());
        for (std::size_t i = 0; i < preview; ++i) {
            std::cout << (i ? ", " : " ") << v[i];
        }
        if (v.size() > preview) {
            std::cout << ", ... and " << (v.size() - preview) << " more";
        }
        std::cout << "\n";
    };

    if (!skipped.empty()) {
        std::cout << "VALIDATE: REPAIR skipped " << skipped.size()
                  << " record(s) (locked or write failed) at rec:";
        print_recnos(skipped);
    }

    if (!unindexed.empty()) {
        std::cout << "VALIDATE: REPAIR wrote " << unindexed.size()
                  << " record(s) whose index update failed; REINDEX/REBUILD needed. rec:";
        print_recnos(unindexed);
    }
}

void cmd_VALIDATE_UNIQUE(xbase::DbArea& A, std::istringstream& in) {
    std::string tok1, tok2;
    if (!(in >> tok1)) {
        print_validate_unique_usage();
        return;
    }

    const std::string T1 = upcopy(tok1);
    if (T1 == "USAGE" || T1 == "HELP" || T1 == "?") {
        print_validate_unique_usage();
        return;
    }

    if (!(in >> tok2)) {
        if (T1 == "UNIQUE") {
            // AIF-074 P1.1 slice 2: no-FIELD form -- validate every field the
            // unique_reg registry declares for the current table (report-only;
            // the explicit FIELD form keeps REPAIR/REPORT options).
            if (!A.isOpen()) {
                std::cout << "VALIDATE: No file open.\n";
                return;
            }
            const auto declared = unique_reg::list_unique_fields(A);
            if (declared.empty()) {
                std::cout << "VALIDATE: no unique fields declared for this "
                             "table. Use SET UNIQUE FIELD <name> ON|PRIMARY, "
                             "or VALIDATE UNIQUE FIELD <name>.\n";
                return;
            }
            for (const auto& f : declared) {
                std::istringstream sub("UNIQUE FIELD " + f);
                cmd_VALIDATE_UNIQUE(A, sub);
            }
            return;
        }
        print_validate_unique_usage();
        return;
    }

    const std::string T2 = upcopy(tok2);
    if (T1 == "UNIQUE" && (T2 == "USAGE" || T2 == "HELP" || T2 == "?")) {
        print_validate_unique_usage();
        return;
    }

    if (T1 != "UNIQUE" || T2 != "FIELD") {
        print_validate_unique_usage();
        return;
    }

    std::string fieldName;
    if (!(in >> fieldName)) {
        std::cout << "VALIDATE: Expected field name.\n";
        print_validate_unique_usage();
        return;
    }

    if (!A.isOpen()) {
        std::cout << "VALIDATE: No file open.\n";
        return;
    }
const std::string fieldU = upcopy(fieldName);

    bool ignoreDeleted = false;
    bool doRepair = false;
    std::string reportPath;

    std::string w1, w2;
    while (in >> w1) {
        const std::string W = upcopy(w1);

        if (W == "IGNORE") {
            if (!(in >> w2) || upcopy(w2) != "DELETED") {
                std::cout << "VALIDATE: Use 'IGNORE DELETED' exactly.\n";
                return;
            }
            ignoreDeleted = true;
        } else if (W == "REPAIR") {
            doRepair = true;
        } else if (W == "REPORT") {
            if (!(in >> w2) || upcopy(w2) != "TO") {
                std::cout << "VALIDATE: Use 'REPORT TO <path>'.\n";
                return;
            }
            std::string path;
            if (!(in >> std::ws) || !std::getline(in, path) || path.empty()) {
                std::cout << "VALIDATE: Missing report path after 'REPORT TO'.\n";
                return;
            }
            size_t p = path.find_first_not_of(' ');
            reportPath = (p == std::string::npos) ? std::string() : path.substr(p);
        } else {
            std::cout << "VALIDATE: Unrecognized option '" << w1 << "'.\n";
            return;
        }
    }

    const int idx = field_index_by_name(A, fieldU);
    if (idx <= 0) {
        std::cout << "VALIDATE: Field not found: " << fieldName << "\n";
        return;
    }

    if (doRepair && !field_is_numericish(A, idx)) {
        std::cout << "VALIDATE: REPAIR currently supports numeric/autokey-style fields only.\n";
        return;
    }

    const std::int64_t startRec = static_cast<std::int64_t>(A.recno64());
    const std::int64_t total = static_cast<std::int64_t>(A.recCount64());
    if (total <= 0) {
        std::cout << "VALIDATE: Table is empty.\n";
        return;
    }

    std::unordered_map<std::string, std::int64_t> firstSeen;
    struct Dup { std::int64_t recno; std::string value; std::int64_t first; bool blank; };
    std::vector<Dup> dups;
    dups.reserve(16);

    int blankCount = 0;

    for (std::int64_t r = 1; r <= total; ++r) {
        if (!A.gotoRec64(static_cast<std::uint64_t>(r))) continue;

        if (ignoreDeleted) {
            try { if (A.isDeleted()) continue; } catch (...) {}
        }

        std::string val;
        try {
            val = A.get(idx);
        } catch (...) {
            continue;
        }

        rtrim_spaces(val);

        if (is_blank_value(val)) {
            ++blankCount;
            dups.push_back({r, val, 0, true});
            continue;
        }

        const auto it = firstSeen.find(val);
        if (it == firstSeen.end()) {
            firstSeen.emplace(val, r);
        } else {
            dups.push_back({r, val, it->second, false});
        }
    }

    int repaired = 0;
    std::vector<std::int64_t> repairSkipped;    // not written (locked / write failed)
    std::vector<std::int64_t> repairUnindexed;  // written, but index not maintained

    if (doRepair && !dups.empty()) {
        long long nextValue = compute_max_numeric_value(A, idx, ignoreDeleted) + 1;

        for (const auto& d : dups) {
            if (!A.gotoRec64(static_cast<std::uint64_t>(d.recno))) {
                repairSkipped.push_back(d.recno);
                continue;
            }

            if (ignoreDeleted) {
                try { if (A.isDeleted()) continue; } catch (...) {}
            }

            try {
                // Must succeed before the write: replaceFieldStored() captures
                // the index key set from the current record buffer, so writing
                // on a failed read could delete key entries belonging to a
                // different record.
                if (!A.readCurrent()) {
                    repairSkipped.push_back(d.recno);
                    continue;
                }

                // Use the engine mutation funnel, not set() + writeCurrent().
                // REPAIR rewrites a uniqueness-candidate field -- precisely the
                // kind of field likely to carry an index tag -- and the raw
                // write path carries no index hook, so the previous code left
                // active CDX/CNX tags pointing at the old value with nothing
                // recording the divergence. replaceFieldStored() owns the record
                // lock, the physical write, and the index replace snapshot.
                //
                // Consequence accepted deliberately: this now takes a per-record
                // lock the old loop did not. A record held by another process is
                // skipped and reported rather than silently rewritten or
                // aborting the whole pass -- REPAIR stays a reporting command.
                std::string write_err;
                if (A.replaceFieldStored(idx, std::to_string(nextValue), &write_err)) {
                    ++repaired;
                    ++nextValue;

                    // true + non-empty err means "written, index not maintained".
                    if (!write_err.empty()) repairUnindexed.push_back(d.recno);
                } else {
                    repairSkipped.push_back(d.recno);
                }
            } catch (...) {
                repairSkipped.push_back(d.recno);
            }
        }

        // Re-scan after repair so report/output reflects final state.
        firstSeen.clear();
        dups.clear();
        blankCount = 0;

        for (std::int64_t r = 1; r <= total; ++r) {
            if (!A.gotoRec64(static_cast<std::uint64_t>(r))) continue;

            if (ignoreDeleted) {
                try { if (A.isDeleted()) continue; } catch (...) {}
            }

            std::string val;
            try {
                val = A.get(idx);
            } catch (...) {
                continue;
            }

            rtrim_spaces(val);

            if (is_blank_value(val)) {
                ++blankCount;
                dups.push_back({r, val, 0, true});
                continue;
            }

            const auto it = firstSeen.find(val);
            if (it == firstSeen.end()) {
                firstSeen.emplace(val, r);
            } else {
                dups.push_back({r, val, it->second, false});
            }
        }
    }

    if (startRec > 0) {
        A.gotoRec64(static_cast<std::uint64_t>(startRec));
        try { A.readCurrent(); } catch (...) {}
    }

    if (dups.empty()) {
        std::cout << "VALIDATE: OK - field '" << fieldName << "' is unique across "
                  << total << " record(s)"
                  << (ignoreDeleted ? " (ignoring deleted)" : "")
                  << ".";
        if (doRepair) {
            std::cout << " REPAIR updated " << repaired << " record(s).";
        }
        std::cout << "\n";
        if (doRepair) report_repair_exceptions(repairSkipped, repairUnindexed);
        return;
    }

    std::cout << "VALIDATE: Found " << dups.size()
              << " problem record(s) on field '" << fieldName << "'"
              << (ignoreDeleted ? " (ignoring deleted)" : "") << ".\n";

    const int preview = std::min<int>(5, (int)dups.size());
    for (int i = 0; i < preview; ++i) {
        const auto& d = dups[i];
        if (d.blank) {
            std::cout << "  blank value at rec " << d.recno << "\n";
        } else {
            std::cout << "  dup value='" << d.value << "' at rec " << d.recno
                      << " (first seen at rec " << d.first << ")\n";
        }
    }
    if ((int)dups.size() > preview) {
        std::cout << "  ... and " << (dups.size() - preview) << " more.\n";
    }

    if (doRepair) {
        std::cout << "VALIDATE: REPAIR updated " << repaired
                  << " record(s), but " << dups.size()
                  << " problem record(s) remain.\n";
        report_repair_exceptions(repairSkipped, repairUnindexed);
    }

    if (!reportPath.empty()) {
        std::ofstream out(reportPath, std::ios::binary);
        if (!out) {
            std::cout << "VALIDATE: Could not write report: " << reportPath << "\n";
            return;
        }

        out << "recno,value,first_seen,kind\n";
        for (const auto& d : dups) {
            out << d.recno << ",\""
                << d.value << "\","
                << d.first << ","
                << (d.blank ? "blank" : "duplicate")
                << "\n";
        }
        std::cout << "Report written: " << reportPath << "\n";
    }
}