// @dottalk.file v1
// subsystem: tests
// layer: test
// owns:
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: experimental

// SQLSEL's two-table read transaction depends on the cooperative xbase lock
// protocol, not on a private mutex. This fixture drives real DbArea instances
// and real lock sidecars. It manufactures a second LIVE owner using this
// process's pid so contention cannot be mistaken for a stale lock.

#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase_locks.hpp"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

namespace {

unsigned long process_id() {
#ifdef _WIN32
    return static_cast<unsigned long>(::GetCurrentProcessId());
#else
    return static_cast<unsigned long>(::getpid());
#endif
}

bool require(bool condition, const std::string& message) {
    if (!condition) std::cerr << "FAIL: " << message << "\n";
    return condition;
}

bool make_table(const std::filesystem::path& path, std::string& error) {
    xbase::dbf_create::FieldSpec id;
    id.name = "ID";
    id.type = 'N';
    id.len = 6;
    id.dec = 0;
    return xbase::dbf_create::create_dbf(
        path.string(), std::vector<xbase::dbf_create::FieldSpec>{id},
        xbase::dbf_create::Flavor::X64, error);
}

bool write_live_foreign_lock(const std::filesystem::path& path) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    out << "DotTalk++ lock\n"
        << "owner=foreign:" << process_id() << ":1\n"
        << "member=member.test.foreign\n"
        << "pid=" << process_id() << "\n"
        << "ms=1\n";
    out.flush();
    return static_cast<bool>(out);
}

} // namespace

int main() {
    namespace fs = std::filesystem;
    std::error_code ec;
    const fs::path dir = fs::temp_directory_path() /
                         ("dottalkpp_lock_protocol_" + std::to_string(process_id()));
    fs::remove_all(dir, ec);
    ec.clear();
    fs::create_directories(dir, ec);
    if (!require(!ec && fs::is_directory(dir), "could not create scratch directory")) {
        return EXIT_FAILURE;
    }

    const fs::path dbf = dir / "LOCKTX.dbf";
    const fs::path table_lock = fs::path(dbf.string() + ".lock");
    const fs::path record_lock = fs::path(dbf.string() + ".lock.1");
    std::string error;
    if (!require(make_table(dbf, error), "could not create table: " + error)) {
        fs::remove_all(dir, ec);
        return EXIT_FAILURE;
    }

    bool ok = true;
    {
        xbase::DbArea area;
        area.open(dbf.string());
        const auto& me = xbase::locks::current_owner();

        // G1: ordinary table fencing is represented by a readable owner file.
        error.clear();
        ok &= require(xbase::locks::try_lock_table(area, me, &error),
                      "clean table lock refused: " + error);
        xbase::locks::LockHolder holder;
        ok &= require(xbase::locks::table_lock_holder(area, &holder) &&
                      holder.owner_id == me.id,
                      "table lock did not record the current owner");
        error.clear();
        ok &= require(xbase::locks::unlock_table(area, me, &error),
                      "clean table unlock failed: " + error);

        // G2: a live foreign record writer that arrived first defeats the table
        // fence. The failed acquisition must roll back its table sidecar.
        ok &= require(write_live_foreign_lock(record_lock),
                      "could not manufacture live foreign record lock");
        error.clear();
        ok &= require(!xbase::locks::try_lock_table(area, me, &error),
                      "table fence ignored live foreign record lock");
        ok &= require(error == "record locked",
                      "unexpected foreign-record refusal: " + error);
        ok &= require(!fs::exists(table_lock),
                      "failed table fence left its sidecar behind");
        fs::remove(record_lock, ec);

        // G3: an unreadable record owner is UNKNOWN, never stale. Fail closed
        // and preserve the evidence for an operator.
        {
            std::ofstream malformed(record_lock, std::ios::binary | std::ios::trunc);
            malformed << "not a lock owner\n";
        }
        error.clear();
        ok &= require(!xbase::locks::try_lock_table(area, me, &error),
                      "table fence ignored unreadable record lock");
        ok &= require(error == "record locked (owner unreadable)",
                      "unexpected unreadable-record refusal: " + error);
        ok &= require(fs::exists(record_lock) && !fs::exists(table_lock),
                      "fail-closed path removed evidence or leaked table lock");
        fs::remove(record_lock, ec);

        // G4: the reverse order is protected too. A record writer cannot enter
        // beneath a live foreign table fence and must leave no record sidecar.
        ok &= require(write_live_foreign_lock(table_lock),
                      "could not manufacture live foreign table lock");
        xbase::locks::Owner writer{"writer:" + std::to_string(process_id()) + ":2",
                                   "member.test.writer"};
        error.clear();
        ok &= require(!xbase::locks::try_lock_record(area, 1, writer, &error),
                      "record writer entered beneath foreign table fence");
        ok &= require(error == "table locked",
                      "unexpected foreign-table refusal: " + error);
        ok &= require(!fs::exists(record_lock),
                      "refused record writer left its sidecar behind");
        fs::remove(table_lock, ec);

        // G5: locks held by this process are re-entrant. This is required for a
        // SQLSEL statement to borrow a caller-owned FLOCK without deadlocking.
        error.clear();
        ok &= require(xbase::locks::try_lock_record(area, 1, me, &error),
                      "own record lock refused: " + error);
        error.clear();
        ok &= require(xbase::locks::try_lock_table(area, me, &error),
                      "own record lock prevented own table fence: " + error);
        error.clear();
        ok &= require(xbase::locks::unlock_table(area, me, &error),
                      "own table unlock failed: " + error);
        error.clear();
        ok &= require(xbase::locks::unlock_record(area, 1, me, &error),
                      "own record unlock failed: " + error);

        area.close();
    }

    fs::remove_all(dir, ec);
    ok &= require(!fs::exists(dir), "scratch directory did not self-erase");
    if (ok) std::cout << "lock_protocol: PASS -- table/record handshake 5/5\n";
    return ok ? EXIT_SUCCESS : EXIT_FAILURE;
}
