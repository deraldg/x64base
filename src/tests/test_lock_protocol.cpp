// @dottalk.file v1
// subsystem: tests
// layer: test
// owns:
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: experimental

// SQLSEL's two-table read transaction depends on the cooperative xbase lock
// protocol, not on a private mutex. This fixture drives real DbArea instances,
// real lock sidecars, and (G6) two separately scheduled processes released by
// one start gate. The race arm proves atomic publication: exactly one process
// acquires the same table sidecar and the published owner is never overwritten.

#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase_locks.hpp"

#include <cstdlib>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/wait.h>
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

bool write_text(const std::filesystem::path& path, const std::string& text) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    out << text;
    out.flush();
    return static_cast<bool>(out);
}

bool wait_for_file(const std::filesystem::path& path,
                   std::chrono::milliseconds timeout) {
    const auto deadline = std::chrono::steady_clock::now() + timeout;
    std::error_code ec;
    while (std::chrono::steady_clock::now() < deadline) {
        if (std::filesystem::exists(path, ec)) return true;
        ec.clear();
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    return std::filesystem::exists(path, ec);
}

std::string read_text(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    std::ostringstream out;
    out << in.rdbuf();
    return out.str();
}

int race_child(const std::filesystem::path& dbf,
               const std::filesystem::path& ready,
               const std::filesystem::path& go,
               const std::filesystem::path& release,
               const std::filesystem::path& result,
               const std::string& owner_id) {
    xbase::DbArea area;
    try {
        area.open(dbf.string());
    } catch (...) {
        (void)write_text(result, "ERROR open");
        return EXIT_FAILURE;
    }
    if (!write_text(ready, "READY") ||
        !wait_for_file(go, std::chrono::seconds(10))) {
        (void)write_text(result, "ERROR gate");
        return EXIT_FAILURE;
    }

    const xbase::locks::Owner owner{owner_id, "member.test.race"};
    std::string error;
    const bool won = xbase::locks::try_lock_table(area, owner, &error);
    if (!write_text(result, won ? "WIN " + owner_id : "LOSE " + error)) {
        return EXIT_FAILURE;
    }
    if (won) {
        if (!wait_for_file(release, std::chrono::seconds(10))) return EXIT_FAILURE;
        error.clear();
        if (!xbase::locks::unlock_table(area, owner, &error)) return EXIT_FAILURE;
    }
    area.close();
    return EXIT_SUCCESS;
}

struct ChildProcess {
#ifdef _WIN32
    PROCESS_INFORMATION info{};
#else
    pid_t pid = -1;
#endif
};

std::string quoted_arg(const std::string& arg) {
    std::string out = "\"";
    for (const char ch : arg) {
        if (ch == '\"') out += '\\';
        out += ch;
    }
    out += '\"';
    return out;
}

bool launch_race_child(const std::filesystem::path& executable,
                       const std::filesystem::path& dbf,
                       const std::filesystem::path& ready,
                       const std::filesystem::path& go,
                       const std::filesystem::path& release,
                       const std::filesystem::path& result,
                       const std::string& owner_id,
                       ChildProcess& child) {
#ifdef _WIN32
    std::string command = quoted_arg(executable.string()) + " --race-child " +
                          quoted_arg(dbf.string()) + " " + quoted_arg(ready.string()) + " " +
                          quoted_arg(go.string()) + " " + quoted_arg(release.string()) + " " +
                          quoted_arg(result.string()) + " " + quoted_arg(owner_id);
    std::vector<char> mutable_command(command.begin(), command.end());
    mutable_command.push_back('\0');
    STARTUPINFOA startup{};
    startup.cb = sizeof(startup);
    return ::CreateProcessA(nullptr, mutable_command.data(), nullptr, nullptr, FALSE,
                            CREATE_NO_WINDOW, nullptr, nullptr, &startup, &child.info) != FALSE;
#else
    const pid_t pid = ::fork();
    if (pid < 0) return false;
    if (pid == 0) {
        ::execl(executable.c_str(), executable.c_str(), "--race-child",
                dbf.c_str(), ready.c_str(), go.c_str(), release.c_str(),
                result.c_str(), owner_id.c_str(), static_cast<char*>(nullptr));
        _exit(127);
    }
    child.pid = pid;
    return true;
#endif
}

bool wait_child(ChildProcess& child) {
#ifdef _WIN32
    const DWORD waited = ::WaitForSingleObject(child.info.hProcess, 10000);
    DWORD exit_code = 1;
    const bool ok = waited == WAIT_OBJECT_0 &&
                    ::GetExitCodeProcess(child.info.hProcess, &exit_code) != FALSE &&
                    exit_code == 0;
    ::CloseHandle(child.info.hThread);
    ::CloseHandle(child.info.hProcess);
    return ok;
#else
    int status = 0;
    return child.pid > 0 && ::waitpid(child.pid, &status, 0) == child.pid &&
           WIFEXITED(status) && WEXITSTATUS(status) == 0;
#endif
}

bool run_atomic_publication_race(const std::filesystem::path& executable,
                                 const std::filesystem::path& dbf,
                                 const std::filesystem::path& root) {
    namespace fs = std::filesystem;
    constexpr int rounds = 16;
    bool ok = true;
    for (int round = 0; round < rounds; ++round) {
        const fs::path round_dir = root / ("race_" + std::to_string(round));
        std::error_code ec;
        fs::create_directories(round_dir, ec);
        if (!require(!ec, "could not create race round directory")) return false;

        const fs::path ready_a = round_dir / "a.ready";
        const fs::path ready_b = round_dir / "b.ready";
        const fs::path go = round_dir / "go";
        const fs::path release = round_dir / "release";
        const fs::path result_a = round_dir / "a.result";
        const fs::path result_b = round_dir / "b.result";
        const std::string owner_a = "race-a-" + std::to_string(round);
        const std::string owner_b = "race-b-" + std::to_string(round);
        ChildProcess a;
        ChildProcess b;
        if (!require(launch_race_child(executable, dbf, ready_a, go, release,
                                       result_a, owner_a, a),
                     "could not launch race child A") ||
            !require(launch_race_child(executable, dbf, ready_b, go, release,
                                       result_b, owner_b, b),
                     "could not launch race child B")) {
            (void)write_text(release, "RELEASE");
            return false;
        }
        ok &= require(wait_for_file(ready_a, std::chrono::seconds(10)) &&
                      wait_for_file(ready_b, std::chrono::seconds(10)),
                      "race children did not reach the start gate");
        ok &= require(write_text(go, "GO"), "could not release race start gate");
        ok &= require(wait_for_file(result_a, std::chrono::seconds(10)) &&
                      wait_for_file(result_b, std::chrono::seconds(10)),
                      "race children did not publish results");

        const std::string a_result = read_text(result_a);
        const std::string b_result = read_text(result_b);
        const bool a_won = a_result.rfind("WIN ", 0) == 0;
        const bool b_won = b_result.rfind("WIN ", 0) == 0;
        ok &= require(a_won != b_won,
                      "atomic table-lock race did not produce exactly one winner: A='" +
                      a_result + "' B='" + b_result + "'");

        xbase::DbArea observer;
        observer.open(dbf.string());
        xbase::locks::LockHolder holder;
        const std::string winner = a_won ? owner_a : owner_b;
        ok &= require(xbase::locks::table_lock_holder(observer, &holder) &&
                      holder.owner_id == winner,
                      "published table-lock owner was missing or overwritten");
        observer.close();

        ok &= require(write_text(release, "RELEASE"), "could not release race winner");
        ok &= require(wait_child(a) && wait_child(b), "race child exited unsuccessfully");
        ok &= require(!fs::exists(fs::path(dbf.string() + ".lock")),
                      "race winner did not remove its table sidecar");
    }
    return ok;
}

} // namespace

int main(int argc, char** argv) {
    if (argc == 8 && std::string(argv[1]) == "--race-child") {
        return race_child(argv[2], argv[3], argv[4], argv[5], argv[6], argv[7]);
    }
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

    // G6: two real processes attempt the same absent sidecar after both have
    // announced readiness. Exactly one may acquire it, and its owner record
    // must remain intact until the parent releases it.
    ok &= run_atomic_publication_race(fs::absolute(argv[0]), dbf, dir);

    fs::remove_all(dir, ec);
    ok &= require(!fs::exists(dir), "scratch directory did not self-erase");
    if (ok) std::cout << "lock_protocol: PASS -- table/record handshake and atomic publication 6/6\n";
    return ok ? EXIT_SUCCESS : EXIT_FAILURE;
}
