// cmd_sftp.cpp
//
// DotTalk++ SFTP command module.
//
// Phase 1 design:
//   - Wrap the operating system's OpenSSH sftp client.
//   - Do file transfer only: LS, GET, PUT.
//   - Do not store passwords.
//   - Do not execute arbitrary remote shell commands.
//   - Expect key-based auth, ssh-agent, or normal OpenSSH prompting.
//
// Supported forms:
//   SFTP LS user@host:/remote/path
//   SFTP GET user@host:/remote/file TO local-file
//   SFTP PUT local-file TO user@host:/remote/file
//
// Also accepted:
//   SFTP LS sftp://user@host/remote/path
//   SFTP GET sftp://user@host/remote/file TO local-file
//   SFTP PUT local-file TO sftp://user@host/remote/file
//
// Notes:
//   - Port selection is deliberately deferred.
//   - Password embedding in URLs is deliberately not supported.
//   - This module stages a temporary sftp batch file and invokes:
//       sftp -b <batch-file> <user@host>

// @dottalk.usage v1
// owner: DOT|SFTP
// command: SFTP
// category: network
// status: supported
// noargs: usage
// effect: network-or-file
// mutates: optional-filesystem remote-filesystem
// usage-access: SFTP USAGE
// summary:
//   Wrap the system OpenSSH sftp client for LS, GET, and PUT file transfer.
//
// usage:
//   SFTP USAGE
//   SFTP LS <user@host:/remote/path>
//   SFTP GET <user@host:/remote/file> TO <local-file>
//   SFTP PUT <local-file> TO <user@host:/remote/file>
//
// examples:
//   SFTP LS derald@example.com:/home/derald/data
//   SFTP GET derald@example.com:/home/derald/data/students.dbf TO students.dbf
//   SFTP PUT students.dbf TO derald@example.com:/home/derald/data/students.dbf
//
// notes:
//   SFTP USAGE prints usage and does not start the sftp client.
//   This command stages a temporary sftp batch file and invokes the system sftp client.
//   Password embedding in URLs is deliberately not supported.
//
// risk:
//   network_access: LS/GET/PUT
//   launches_external_process: system sftp client
//   writes_local_filesystem: GET temporary batch file and local output
//   mutates_remote_filesystem: PUT
//   mutates_table_data: no
//
// related:
//   WEB
//   PSHELL
//

#include <chrono>
#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"

using xbase::DbArea;
namespace fs = std::filesystem;

namespace {

struct RemoteSpec {
    std::string target;      // user@host or host
    std::string remotePath;  // /path/file
};

static std::string trim_copy(const std::string& s)
{
    const auto first = s.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) {
        return std::string();
    }

    const auto last = s.find_last_not_of(" \t\r\n");
    return s.substr(first, last - first + 1);
}

static std::string uppercase_copy(std::string s)
{
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static void sftp_usage()
{
    std::cout
        << "Usage:\n"
        << "  SFTP USAGE\n"
        << "  SFTP LS <user@host:/remote/path>\n"
        << "  SFTP GET <user@host:/remote/file> TO <local-file>\n"
        << "  SFTP PUT <local-file> TO <user@host:/remote/file>\n"
        << "\n"
        << "Examples:\n"
        << "  SFTP LS derald@example.com:/home/derald/data\n"
        << "  SFTP GET derald@example.com:/home/derald/data/students.dbf TO students.dbf\n"
        << "  SFTP PUT students.dbf TO derald@example.com:/home/derald/data/students.dbf\n"
        << "\n"
        << "Notes:\n"
        << "  - SFTP USAGE does not start the sftp client.\n"
        << "  - Uses the system OpenSSH sftp client.\n"
        << "  - Use key-based authentication or ssh-agent where possible.\n"
        << "  - Password embedding in URLs is deliberately not supported.\n";
}

static bool contains_forbidden_chars(const std::string& s)
{
    for (char c : s) {
        switch (c) {
        case '"':
        case '\r':
        case '\n':
            return true;
        default:
            break;
        }
    }

    return false;
}

static std::string quote_for_sftp_batch(const std::string& s)
{
    // We reject double quotes before this point, so simple quoting is enough
    // for paths containing spaces.
    return "\"" + s + "\"";
}

static std::string quote_for_shell(const std::string& s)
{
#ifdef _WIN32
    // Conservative Windows command-line quoting.
    // This is enough for normal temp paths and user@host targets after
    // forbidden quote/newline validation.
    return "\"" + s + "\"";
#else
    // Single-quote POSIX shell quoting.
    // Single quotes are handled by closing/reopening the quote.
    std::string out = "'";
    for (char c : s) {
        if (c == '\'') {
            out += "'\\''";
        } else {
            out += c;
        }
    }
    out += "'";
    return out;
#endif
}

static bool parse_remote_spec(const std::string& raw, RemoteSpec& out, std::string& err)
{
    const std::string spec = trim_copy(raw);

    if (spec.empty()) {
        err = "empty remote specification";
        return false;
    }

    if (contains_forbidden_chars(spec)) {
        err = "remote specification contains unsupported quote or newline";
        return false;
    }

    const std::string prefix = "sftp://";

    if (spec.rfind(prefix, 0) == 0) {
        const std::string rest = spec.substr(prefix.size());
        const auto slash = rest.find('/');

        if (slash == std::string::npos || slash == 0) {
            err = "expected sftp://user@host/path";
            return false;
        }

        out.target = rest.substr(0, slash);
        out.remotePath = rest.substr(slash);

        if (out.target.empty() || out.remotePath.empty()) {
            err = "invalid sftp URL";
            return false;
        }

        if (out.target.find(':') != std::string::npos) {
            err = "sftp URL ports are not supported in phase 1";
            return false;
        }

        return true;
    }

    const auto colon = spec.find(':');

    if (colon == std::string::npos || colon == 0 || colon + 1 >= spec.size()) {
        err = "expected user@host:/remote/path";
        return false;
    }

    out.target = spec.substr(0, colon);
    out.remotePath = spec.substr(colon + 1);

    if (out.remotePath.empty()) {
        err = "missing remote path";
        return false;
    }

    if (out.remotePath[0] != '/') {
        err = "remote path should start with /";
        return false;
    }

    return true;
}

static fs::path make_temp_batch_path()
{
    const auto now = std::chrono::high_resolution_clock::now()
                         .time_since_epoch()
                         .count();

    fs::path p = fs::temp_directory_path();
    p /= "dottalk_sftp_" + std::to_string(now) + ".batch";

    return p;
}

static bool write_batch_file(const fs::path& batchPath,
                             const std::vector<std::string>& lines,
                             std::string& err)
{
    std::ofstream out(batchPath, std::ios::binary | std::ios::trunc);

    if (!out) {
        err = "unable to create temporary sftp batch file";
        return false;
    }

    for (const std::string& line : lines) {
        out << line << "\n";
    }

    if (!out) {
        err = "unable to write temporary sftp batch file";
        return false;
    }

    return true;
}

static int run_sftp_batch(const std::string& target,
                          const std::vector<std::string>& lines,
                          std::string& err)
{
    if (target.empty()) {
        err = "missing sftp target";
        return -1;
    }

    if (contains_forbidden_chars(target)) {
        err = "sftp target contains unsupported quote or newline";
        return -1;
    }

    fs::path batchPath = make_temp_batch_path();

    if (!write_batch_file(batchPath, lines, err)) {
        return -1;
    }

    std::string command;

#ifdef _WIN32
    command = "sftp.exe -b " + quote_for_shell(batchPath.string()) + " " + quote_for_shell(target);
#else
    command = "sftp -b " + quote_for_shell(batchPath.string()) + " " + quote_for_shell(target);
#endif

    const int rc = std::system(command.c_str());

    std::error_code ec;
    fs::remove(batchPath, ec);

    return rc;
}

static bool local_path_ok(const std::string& path, std::string& err)
{
    if (path.empty()) {
        err = "missing local path";
        return false;
    }

    if (contains_forbidden_chars(path)) {
        err = "local path contains unsupported quote or newline";
        return false;
    }

    return true;
}

static void cmd_sftp_ls(std::istringstream& S)
{
    std::string remoteRaw;

    if (!(S >> remoteRaw)) {
        sftp_usage();
        return;
    }

    RemoteSpec remote;
    std::string err;

    if (!parse_remote_spec(remoteRaw, remote, err)) {
        std::cout << "SFTP LS: " << err << "\n";
        return;
    }

    std::vector<std::string> batch;
    batch.push_back("ls " + quote_for_sftp_batch(remote.remotePath));

    const int rc = run_sftp_batch(remote.target, batch, err);

    if (rc != 0) {
        std::cout << "SFTP LS: sftp returned " << rc << "\n";
        if (!err.empty()) {
            std::cout << "SFTP LS: " << err << "\n";
        }
        return;
    }
}

static void cmd_sftp_get(std::istringstream& S)
{
    std::string remoteRaw;

    if (!(S >> remoteRaw)) {
        sftp_usage();
        return;
    }

    std::string toKw;

    if (!(S >> toKw)) {
        std::cout << "SFTP GET: expected TO <local-file>\n";
        return;
    }

    toKw = uppercase_copy(toKw);

    if (toKw != "TO") {
        std::cout << "SFTP GET: expected TO <local-file>\n";
        return;
    }

    std::string localFile;

    if (!(S >> localFile)) {
        std::cout << "SFTP GET: expected local output file\n";
        return;
    }

    std::string err;

    if (!local_path_ok(localFile, err)) {
        std::cout << "SFTP GET: " << err << "\n";
        return;
    }

    RemoteSpec remote;

    if (!parse_remote_spec(remoteRaw, remote, err)) {
        std::cout << "SFTP GET: " << err << "\n";
        return;
    }

    std::vector<std::string> batch;
    batch.push_back("get " + quote_for_sftp_batch(remote.remotePath) + " " +
                    quote_for_sftp_batch(localFile));

    const int rc = run_sftp_batch(remote.target, batch, err);

    if (rc != 0) {
        std::cout << "SFTP GET: sftp returned " << rc << "\n";
        if (!err.empty()) {
            std::cout << "SFTP GET: " << err << "\n";
        }
        return;
    }

    std::cout << "SFTP GET: wrote " << localFile << "\n";
}

static void cmd_sftp_put(std::istringstream& S)
{
    std::string localFile;

    if (!(S >> localFile)) {
        sftp_usage();
        return;
    }

    std::string toKw;

    if (!(S >> toKw)) {
        std::cout << "SFTP PUT: expected TO <remote-file>\n";
        return;
    }

    toKw = uppercase_copy(toKw);

    if (toKw != "TO") {
        std::cout << "SFTP PUT: expected TO <remote-file>\n";
        return;
    }

    std::string remoteRaw;

    if (!(S >> remoteRaw)) {
        std::cout << "SFTP PUT: expected remote output file\n";
        return;
    }

    std::string err;

    if (!local_path_ok(localFile, err)) {
        std::cout << "SFTP PUT: " << err << "\n";
        return;
    }

    RemoteSpec remote;

    if (!parse_remote_spec(remoteRaw, remote, err)) {
        std::cout << "SFTP PUT: " << err << "\n";
        return;
    }

    std::vector<std::string> batch;
    batch.push_back("put " + quote_for_sftp_batch(localFile) + " " +
                    quote_for_sftp_batch(remote.remotePath));

    const int rc = run_sftp_batch(remote.target, batch, err);

    if (rc != 0) {
        std::cout << "SFTP PUT: sftp returned " << rc << "\n";
        if (!err.empty()) {
            std::cout << "SFTP PUT: " << err << "\n";
        }
        return;
    }

    std::cout << "SFTP PUT: uploaded " << localFile << "\n";
}

} // namespace

void cmd_SFTP(DbArea&, std::istringstream& S)
{
    std::string sub;

    if (!(S >> sub)) {
        sftp_usage();
        return;
    }

    sub = uppercase_copy(sub);

    if (sub == "LS" || sub == "DIR") {
        cmd_sftp_ls(S);
        return;
    }

    if (sub == "GET" || sub == "FETCH") {
        cmd_sftp_get(S);
        return;
    }

    if (sub == "PUT" || sub == "SEND") {
        cmd_sftp_put(S);
        return;
    }

    if (sub == "USAGE" || sub == "HELP" || sub == "?") {
        sftp_usage();
        return;
    }

    sftp_usage();
}