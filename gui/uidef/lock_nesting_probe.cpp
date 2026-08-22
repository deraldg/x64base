// @dottalk.file v1
// subsystem: gui
// layer: probe
// owns: standalone main(); no uidef_register
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: supported
// summary:
//   R57 -- lock nesting
//
// notes:
//   Contract added 2026-08-22. This directory was promoted from lane to
//   project in 898a37b62 without them, so 14 of its 15 C++ files were
//   INVISIBLE to the doc pass -- not undocumented, invisible: the pass
//   completed and reported success while covering less than it claimed.

// AIF-120 R57 -- lock nesting probe.
//
// Build and run in WSL (this needs libxbase.a, which is built by ./wslbuild.sh and
// cannot be linked from the Cowork VM -- its libstdc++ is older than the one the
// archive was compiled against):
//
//   cd /mnt/d/code/ccode
//   cp dottalkpp/data/dbf/vfp/STUDENTS.dbf /tmp/nest_STUDENTS.dbf
//   B=build/wsl-core-vcpkg
//   g++ -std=c++17 -Iinclude -I$B/generated gui/uidef/lock_nesting_probe.cpp \
//       $B/src/xbase/libxbase.a $B/src/memo/libmemo.a $B/src/xexpr/libxexpr.a \
//       $B/src/libdottalk_value.a $B/src/libdottalk_inx_payload.a \
//       -o /tmp/nest -pthread
//   /tmp/nest /tmp/nest_STUDENTS.dbf
//
// It WRITES to the table, so run it against a copy -- the command above makes one.
//
// The claim, read from src/xbase/dbarea.cpp and xbase_locks.cpp:
//   handler try_lock_record(R) -> creates the lock file
//   DbArea  try_lock_record(R) -> same owner, "re-entrant", returns true
//   DbArea  write
//   DbArea  unlock_record(R)   -> owner matches, DELETES the lock file
// leaving the handler holding nothing. This runs it.
#include "xbase.hpp"
#include "xbase_locks.hpp"
#include <cstdio>
#include <string>

int main(int argc, char** argv) {
    if (argc < 2) { std::printf("usage: nest <table.dbf>\n"); return 2; }
    xbase::DbArea a;
    a.open(argv[1]);
    if (!a.isOpen()) { std::printf("could not open %s\n", argv[1]); return 2; }
    a.gotoRec64(1);

    const xbase::locks::Owner& me = xbase::locks::current_owner();
    std::string err;
    // argv[2] == "table" runs the SAME experiment at table granularity. The claim
    // under test there is the opposite one: DbArea takes RECORD locks, and R54
    // ruled the namespaces independent, so its unlock must NOT reach a table lock.
    const bool table_mode = (argc > 2 && std::string(argv[2]) == "table");

    std::printf("owner            : %s\n", me.id.c_str());
    std::printf("granularity      : %s\n", table_mode ? "table" : "record");
    const bool got = table_mode
        ? xbase::locks::try_lock_table(a, me, &err)
        : xbase::locks::try_lock_record(a, a.recno64(), me, &err);
    if (!got) {
        std::printf("could not take the lock: %s\n", err.c_str());
        return 2;
    }
    // Sequenced deliberately. The first version of this probe called
    // is_record_locked(&who) and who.c_str() as two arguments of ONE printf --
    // argument evaluation order is unspecified, gcc evaluated who.c_str() first,
    // and the owner printed empty. That looked exactly like an engine defect
    // (owner_out not populated) and was a defect in the probe.
    std::string who;
    bool held = table_mode ? xbase::locks::is_table_locked(a, &who)
                           : xbase::locks::is_record_locked(a, a.recno64(), &who);
    std::printf("after handler LOCK   : record locked = %s (%s)\n",
                held ? "yes" : "NO", who.c_str());

    // The write the handler performs while believing it holds the lock.
    std::string werr;
    const bool wrote = a.replaceFieldStored(1, std::string("Z"), &werr);
    std::printf("write             : %s%s%s\n", wrote ? "ok" : "FAILED",
                werr.empty() ? "" : " -- ", werr.c_str());

    who.clear();
    const bool still = table_mode ? xbase::locks::is_table_locked(a, &who)
                                  : xbase::locks::is_record_locked(a, a.recno64(), &who);
    std::printf("after DbArea write   : %s locked = %s (%s)\n",
                table_mode ? "table " : "record", still ? "yes" : "NO", who.c_str());

    std::printf("\n  the caller's lock survived its own write : %s\n",
                still ? "YES" : "NO -- DbArea's unlock removed it");
    if (table_mode) xbase::locks::unlock_table(a, me, &err);
    else            xbase::locks::unlock_record(a, a.recno64(), me, &err);
    return 0;
}
