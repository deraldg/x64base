// @dottalk.file v1
// subsystem: tools
// layer: probe
// owns:
// project: project.x64base.runtime
// lane: AIF-160
// owner: member.derald
// status: experimental
//
// AIF-160 DECISION 6.2 CALLED THIS "THE FIRST THING TO MEASURE" AND IT WAS NOT
// MEASURED. This is that number, and three others it is useless without.
//
// WHAT 6.2 ACTUALLY ASKED. It chose a DBF catalog for the group log over a flat
// append-only file, said the cost was "explicit and accepted", and named one
// open question: whether a DBF write can meet the fsync requirement, with a flat
// log as the fallback if it cannot. Section 8.2 later settled the CAPABILITY --
// xbase::durable_sync syncs a DBF by path and ships, doing exactly this on the
// workspaces catalog. What was never established is the COST.
//
// CORRECTED 2026-09-11, ON ITS FIRST RUN. The arithmetic block printed ratios
// up to 204x in the ruling's favour by carrying the per-record term in one
// column and not the other: `ruling = 4C + A` assumed a grouped commit takes no
// record locks, when apply_one_recno takes one per record either way. The
// design's own NOT CLAIMED had already said whether a held table lock makes the
// inner lock redundant was an OPEN QUESTION, and the probe was written as if it
// had been answered yes -- by the author who had just recommended the ruling, in
// the instrument built to check it. Arm B2 now measures the inner lock instead
// of assuming it away, and the shared term is printed rather than cancelled out
// of one side. The corrected advantage is a FLAT 4C against a LINEAR R*B, which
// is a better argument than the wrong one was.
//
// AND IT MEASURES A CLAIM OF THE AUTHOR'S OWN, WHICH IS THE REAL REASON IT
// EXISTS. The locking ruling in section 1.2 rests on an assertion derived by
// READING try_lock_record: that a record lock is a FILE, that taking one costs
// four to six syscalls, and that n rows is therefore O(n) file creates which no
// phase choice can make cheap. That argument moved a decision. It was never run.
// A ruling standing on unmeasured arithmetic is the shape this tree keeps
// cataloguing -- the ACID note's own one-fsync-per-commit figure is flagged NOT
// MEASURED for the same reason -- so arms B and C exist to confirm or refute it,
// and the report prints the arithmetic rather than asserting the conclusion.
//
// IT IS DELIBERATELY NOT AN add_test, following g0_slot_cost_probe: a timing
// measurement registered as a test is a test that can only pass, which is the
// defect class this tree has a name for.
//
// READ THE MINIMUM, NOT THE MEAN. These are syscall-bound operations on a shared
// machine; the mean carries every scheduler hiccup and every antivirus scan. The
// minimum is the closest this can get to the cost of the work itself, and the
// spread between min and max is the honest statement of how much that varies.

#include "cli/group_log.hpp"
#include "common/path_state.hpp"
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase/durable.hpp"
#include "xbase_locks.hpp"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <cstdint>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using clock_type = std::chrono::steady_clock;

namespace {

struct Stat {
    double min_us = 0, med_us = 0, mean_us = 0, max_us = 0;
    std::size_t n = 0;
};

Stat summarise(std::vector<double> us) {
    Stat s;
    if (us.empty()) return s;
    std::sort(us.begin(), us.end());
    s.n    = us.size();
    s.min_us = us.front();
    s.max_us = us.back();
    s.med_us = us[us.size() / 2];
    double total = 0;
    for (double v : us) total += v;
    s.mean_us = total / static_cast<double>(us.size());
    return s;
}

void row(const char* label, const Stat& s) {
    std::cout << "  " << std::left << std::setw(38) << label << std::right
              << std::fixed << std::setprecision(1)
              << std::setw(10) << s.min_us
              << std::setw(10) << s.med_us
              << std::setw(10) << s.mean_us
              << std::setw(10) << s.max_us
              << std::setw(8)  << s.n << "\n";
}

template <typename Fn>
double timed_us(Fn&& fn) {
    const auto t0 = clock_type::now();
    fn();
    const auto t1 = clock_type::now();
    return std::chrono::duration<double, std::micro>(t1 - t0).count();
}

bool make_table(const fs::path& path, std::string& err) {
    xbase::dbf_create::FieldSpec id;
    id.name = "ID"; id.type = 'N'; id.len = 6; id.dec = 0;
    xbase::dbf_create::FieldSpec mark;
    mark.name = "MARK"; mark.type = 'C'; mark.len = 8; mark.dec = 0;
    return xbase::dbf_create::create_dbf(
        path.string(), std::vector<xbase::dbf_create::FieldSpec>{id, mark},
        xbase::dbf_create::Flavor::X64, err);
}

} // namespace

int main(int argc, char** argv) {
    const int reps = (argc > 1) ? std::max(1, std::atoi(argv[1])) : 200;

    std::error_code ec;
    const fs::path root = fs::temp_directory_path(ec) / "dottalkpp_costprobe";
    fs::remove_all(root, ec);
    fs::create_directories(root, ec);
    const fs::path sys_root = root / "sys";
    dottalk::paths::set_slot(dottalk::paths::Slot::SYS, sys_root);

    std::cout << "GROUP COMMIT COST PROBE (AIF-160 decision 6.2)\n"
              << "  scratch      : " << root.string() << "\n"
              << "  sys slot     : " << sys_root.string() << "\n"
              << "  group log    : " << dottalk::group::catalog_path() << "\n"
              << "  iterations   : " << reps << "\n"
              << "  owner token  : " << xbase::locks::current_owner().id << "\n\n";

    // ---- A. THE DECISION WRITE ----------------------------------------------
    // append a row + writeCurrent + durable_sync, which is the whole of what a
    // group commit adds over N independent single-table commits.
    double first_us = 0;
    {
        std::string err;
        const std::string k = dottalk::group::mint_group_key();
        first_us = timed_us([&] { (void)dottalk::group::decide_committed(k, 4, &err); });
    }

    std::vector<double> decide_us;
    decide_us.reserve(static_cast<std::size_t>(reps));
    for (int i = 0; i < reps; ++i) {
        std::string err;
        const std::string k = dottalk::group::mint_group_key();
        decide_us.push_back(
            timed_us([&] { (void)dottalk::group::decide_committed(k, 4, &err); }));
    }

    // ---- B / C. THE LOCKS ---------------------------------------------------
    const fs::path dbf = root / "LOCKED.dbf";
    std::string cerr_;
    if (!make_table(dbf, cerr_)) {
        std::cerr << "probe: could not build the lock fixture (" << cerr_ << ")\n";
        return 1;
    }

    std::vector<double> reclock_us, tablock_us, inner_us, sync_us;
    {
        xbase::DbArea a;
        try { a.open(dbf.string()); } catch (...) {}
        if (!a.isOpen()) { std::cerr << "probe: fixture would not open\n"; return 1; }
        (void)a.appendBlank();
        (void)a.writeCurrent();

        reclock_us.reserve(static_cast<std::size_t>(reps));
        for (int i = 0; i < reps; ++i) {
            std::string e;
            reclock_us.push_back(timed_us([&] {
                if (xbase::locks::try_lock_record(a, 1, &e))
                    xbase::locks::unlock_record(a, 1);
            }));
        }

        tablock_us.reserve(static_cast<std::size_t>(reps));
        for (int i = 0; i < reps; ++i) {
            std::string e, e2;
            tablock_us.push_back(timed_us([&] {
                if (xbase::locks::try_lock_table(a, &e))
                    (void)xbase::locks::unlock_table(a, xbase::locks::current_owner(), &e2);
            }));
        }

        // B2. THE INNER LOCK AS IT IS ACTUALLY PAID IN THE RULING'S WORLD.
        // apply_one_recno takes a record lock per record, and a held table lock
        // does NOT suppress it: try_lock_record calls table_lock_allows_owner,
        // finds the fence is ours, and creates the record lock file anyway. So
        // under the ruling every record still costs a lock -- this measures what
        // that costs with our own table lock in place, which is the extra read
        // of the table-lock file plus the same create.
        //
        // THE FIRST CUT OF THIS PROBE OMITTED THIS ARM AND ITS ARITHMETIC
        // ASSUMED THE INNER LOCK AWAY, which flattered the ruling its author had
        // just recommended, in the instrument built to check it. The design's
        // own NOT CLAIMED had already named the question as open.
        {
            std::string te, te2;
            const bool got_table = xbase::locks::try_lock_table(a, &te);
            inner_us.reserve(static_cast<std::size_t>(reps));
            for (int i = 0; i < reps; ++i) {
                std::string e;
                inner_us.push_back(timed_us([&] {
                    if (xbase::locks::try_lock_record(a, 1, &e))
                        xbase::locks::unlock_record(a, 1);
                }));
            }
            if (got_table)
                (void)xbase::locks::unlock_table(a, xbase::locks::current_owner(), &te2);
        }

        sync_us.reserve(static_cast<std::size_t>(reps));
        for (int i = 0; i < reps; ++i) {
            std::string e;
            sync_us.push_back(timed_us([&] { (void)xbase::durable_sync(dbf.string(), &e); }));
        }
        a.close();
    }

    const Stat A = summarise(decide_us);
    const Stat B = summarise(reclock_us);
    const Stat C = summarise(tablock_us);
    const Stat B2 = summarise(inner_us);
    const Stat D  = summarise(sync_us);

    std::cout << "  " << std::left << std::setw(38) << "operation" << std::right
              << std::setw(10) << "min us" << std::setw(10) << "med"
              << std::setw(10) << "mean"   << std::setw(10) << "max"
              << std::setw(8)  << "n" << "\n";
    std::cout << "  " << std::string(86, '-') << "\n";
    row("A  decide_committed (the decision)", A);
    row("B  record lock take+release", B);
    row("C  table  lock take+release", C);
    row("B2 record lock UNDER our table lock", B2);
    row("D  durable_sync, existing file", D);
    std::cout << "\n  first decide_committed (creates the catalog): "
              << std::fixed << std::setprecision(1) << first_us << " us\n";

    // ---- E. THE LINEAR SCAN, WHICH THE DESIGN SAYS IS OWED AN INDEX ---------
    // is_committed walks an append-only catalog that is never packed. The design
    // calls that the one place cost is unbounded; this prints the shape of it
    // rather than leaving it as an adjective.
    std::cout << "\n  E  is_committed() over a catalog that only grows:\n";
    const std::string probe_key = dottalk::group::mint_group_key();
    {
        std::string err;
        (void)dottalk::group::decide_committed(probe_key, 1, &err);
    }
    for (int target : {100, 500, 2000}) {
        while (dottalk::group::decision_count() < target) {
            std::string err;
            (void)dottalk::group::decide_committed(dottalk::group::mint_group_key(), 1, &err);
        }
        // The WORST case is the honest one: a key absent from the catalog, which
        // is PRESUMED ABORT and the answer recovery gets most often.
        const double miss = timed_us([&] { (void)dottalk::group::is_committed("absent#0"); });
        const double hit  = timed_us([&] { (void)dottalk::group::is_committed(probe_key); });
        std::cout << "       rows=" << std::setw(5) << dottalk::group::decision_count()
                  << "   miss (full scan) " << std::setw(9) << std::fixed
                  << std::setprecision(1) << miss << " us"
                  << "   hit (row 1) " << std::setw(9) << hit << " us\n";
    }

    // ---- THE ARITHMETIC, WITH THE TERM BOTH STRATEGIES SHARE ---------------
    // CORRECTED. The first cut printed `ruling = 4C + A` against
    // `rejected = 4C + R*B + A` and reported ratios up to 204x. That assumed a
    // grouped commit takes no record locks, which is false: apply_one_recno
    // takes one per record either way. Carrying a term in one column and not
    // the other is not a comparison.
    //
    // The two strategies differ ONLY in what they add on top of apply, so the
    // shared term cancels and the honest comparison is small.
    std::cout << "\n  THE TWO STRATEGIES DIFFER ONLY IN WHAT THEY ADD ON TOP OF APPLY.\n"
                 "  apply_one_recno takes a record lock per record in BOTH schemes, so\n"
                 "  that term is common and cancels here. It is priced separately below.\n\n"
              << "       ruling   adds 4 table locks       4C   = "
              << std::fixed << std::setprecision(1) << (4 * C.min_us)
              << " us, FLAT in R\n"
              << "       rejected adds R record locks      R*B  = R * "
              << B.min_us << " us\n\n";
    if (B.min_us > 0) {
        std::cout << "       crossover at R = 4C/B = "
                  << std::setprecision(2) << (4 * C.min_us / B.min_us) << " rows\n"
                  << "       Below it the two are a wash. Above it the ruling wins, and\n"
                  << "       it wins by a term that is FLAT while the other is linear.\n";
    }

    std::cout << "\n  AND THE TERM THEY SHARE, WHICH DOMINATES BOTH:\n"
                 "       apply's own record locks   R * B2 = R * "
              << std::setprecision(1) << B2.min_us << " us\n\n";
    for (int R : {1, 10, 100, 1000}) {
        const double shared   = R * B2.min_us;
        const double ruled    = 4 * C.min_us + A.min_us + shared;
        const double rejected = 4 * C.min_us + A.min_us + shared + R * B.min_us;
        std::cout << "       R=" << std::setw(5) << R
                  << "   shared " << std::setw(11) << std::fixed << std::setprecision(1) << shared
                  << "   ruling " << std::setw(11) << ruled
                  << "   per-record " << std::setw(11) << rejected
                  << "   x" << std::setprecision(2)
                  << (ruled > 0 ? rejected / ruled : 0.0) << "\n";
    }
    std::cout << "\n       THE SHARED COLUMN IS THE FINDING. At R=1000 it is about "
              << std::setprecision(0) << (1000 * B2.min_us / 1000.0) << " ms of\n"
                 "       lock files, paid by the SHIPPED single-table COMMIT path today,\n"
                 "       before any group commit exists and whichever strategy is chosen.\n";

    std::cout << "\n  READ THE MINIMUM. These are syscall-bound on a shared machine;\n"
                 "  the mean carries every scheduler hiccup. The min-to-max spread is\n"
                 "  the honest statement of variance.\n"
                 "\n  NOT CLAIMED: nothing here is a throughput number, nothing is\n"
                 "  concurrent, and one machine with one filesystem is one data point.\n"
                 "  A ruling that survives this has survived ONE measurement.\n";

    fs::remove_all(root, ec);
    return 0;
}
