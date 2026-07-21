// @dottalk.usage v1
// owner: DOT|WEB
// command: WEB
// category: network
// status: supported
// noargs: usage
// effect: network-or-file
// mutates: optional-filesystem
// usage-access: WEB USAGE
// summary:
//   Open, fetch, or inspect web URLs using the default handler or WinHTTP.
//
// usage:
//   WEB USAGE
//   WEB DEFAULT
//   WEB RETRO
//   WEB OPEN <url|DEFAULT|RETRO>
//   WEB LAUNCH <url|DEFAULT|RETRO>
//   WEB GET <url|DEFAULT|RETRO>
//   WEB HEAD <url|DEFAULT|RETRO>
//   WEB FETCH <url|DEFAULT|RETRO> TO <file>
//
// examples:
//   WEB DEFAULT
//   WEB RETRO
//   WEB OPEN https://example.com
//   WEB OPEN DEFAULT
//   WEB HEAD https://example.com
//   WEB GET https://example.com
//   WEB FETCH https://example.com/data.csv TO tmp\data.csv
//
// notes:
//   WEB USAGE prints usage and does not launch a browser, make a network request, or write files.
//   WEB DEFAULT opens x64base.com.
//   WEB RETRO opens the Flying Toasters page.
//   DEFAULT and RETRO are accepted anywhere a URL operand is accepted.
//   WEB OPEN/LAUNCH use the OS default URL handler.
//   WEB GET/HEAD use HTTP request support where implemented.
//   WEB FETCH writes the response body to the requested file.
//
// risk:
//   network_access: WEB GET/HEAD/FETCH
//   launches_external_app: WEB DEFAULT/RETRO/OPEN/LAUNCH
//   writes_filesystem: WEB FETCH
//   mutates_table_data: no
//
// related:
//   SFTP
//   PSHELL
//

#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"

#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#include <winhttp.h>
#pragma comment(lib, "winhttp.lib")
#else
#include <sys/wait.h>
#include <unistd.h>
#endif

using xbase::DbArea;
namespace fs = std::filesystem;

namespace {

struct NamedWebTarget final {
    const char* name;
    const char* url;
};

constexpr NamedWebTarget kNamedWebTargets[] = {
    {"DEFAULT", "https://x64base.com/"},
    {"RETRO", "https://www.bryanbraun.com/after-dark-css/all/flying-toasters.html"},
};

static void web_usage()
{
    std::cout
        << "Usage:\n"
        << "  WEB USAGE\n"
        << "  WEB DEFAULT\n"
        << "  WEB RETRO\n"
        << "  WEB OPEN <url|DEFAULT|RETRO>\n"
        << "  WEB LAUNCH <url|DEFAULT|RETRO>\n"
        << "  WEB GET <url|DEFAULT|RETRO>\n"
        << "  WEB HEAD <url|DEFAULT|RETRO>\n"
        << "  WEB FETCH <url|DEFAULT|RETRO> TO <file>\n"
        << "Examples:\n"
        << "  WEB DEFAULT\n"
        << "  WEB RETRO\n"
        << "  WEB OPEN https://example.com\n"
        << "  WEB OPEN DEFAULT\n"
        << "  WEB HEAD https://example.com\n"
        << "  WEB GET https://example.com\n"
        << "  WEB FETCH https://example.com/data.csv TO tmp\\data.csv\n"
        << "Notes:\n"
        << "  - WEB USAGE does not launch a browser, make a network request, or write files.\n"
        << "  - WEB FETCH writes/truncates the requested output file.\n";
}

static std::string uppercase_copy(std::string s)
{
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static std::string resolve_web_target(const std::string& operand)
{
    const std::string name = uppercase_copy(operand);

    for (const NamedWebTarget& target : kNamedWebTargets) {
        if (name == target.name) {
            return target.url;
        }
    }

    return operand;
}

#ifdef _WIN32

static std::wstring widen_utf8_or_ansi(const std::string& s)
{
    if (s.empty()) {
        return std::wstring();
    }

    int needed = MultiByteToWideChar(
        CP_UTF8,
        0,
        s.c_str(),
        -1,
        nullptr,
        0);

    if (needed <= 0) {
        needed = MultiByteToWideChar(
            CP_ACP,
            0,
            s.c_str(),
            -1,
            nullptr,
            0);

        if (needed <= 0) {
            return std::wstring(s.begin(), s.end());
        }

        std::wstring out(static_cast<size_t>(needed - 1), L'\0');

        MultiByteToWideChar(
            CP_ACP,
            0,
            s.c_str(),
            -1,
            out.data(),
            needed);

        return out;
    }

    std::wstring out(static_cast<size_t>(needed - 1), L'\0');

    MultiByteToWideChar(
        CP_UTF8,
        0,
        s.c_str(),
        -1,
        out.data(),
        needed);

    return out;
}

static bool launch_url_default_handler(const std::string& url, std::string& err)
{
    if (url.empty()) {
        err = "missing URL";
        return false;
    }

    const std::wstring wurl = widen_utf8_or_ansi(url);

    HINSTANCE rc = ShellExecuteW(
        nullptr,
        L"open",
        wurl.c_str(),
        nullptr,
        nullptr,
        SW_SHOWNORMAL);

    if (reinterpret_cast<INT_PTR>(rc) <= 32) {
        err = "ShellExecuteW failed";
        return false;
    }

    return true;
}

struct ParsedUrl {
    std::wstring host;
    std::wstring path;
    INTERNET_PORT port = 0;
    bool secure = false;
};

static bool parse_url(const std::string& url, ParsedUrl& out)
{
    std::wstring wurl = widen_utf8_or_ansi(url);

    URL_COMPONENTS uc{};
    wchar_t host[256]{};
    wchar_t path[2048]{};

    uc.dwStructSize = sizeof(uc);
    uc.lpszHostName = host;
    uc.dwHostNameLength = static_cast<DWORD>(std::size(host));
    uc.lpszUrlPath = path;
    uc.dwUrlPathLength = static_cast<DWORD>(std::size(path));

    if (!WinHttpCrackUrl(wurl.c_str(), 0, 0, &uc)) {
        return false;
    }

    out.host.assign(uc.lpszHostName, uc.dwHostNameLength);
    out.path.assign(uc.lpszUrlPath, uc.dwUrlPathLength);

    if (out.path.empty()) {
        out.path = L"/";
    }

    out.port = uc.nPort;
    out.secure = (uc.nScheme == INTERNET_SCHEME_HTTPS);

    return true;
}

static bool ensure_parent_dir(const std::string& path)
{
    std::error_code ec;

    fs::path p(path);
    fs::path parent = p.parent_path();

    if (parent.empty()) {
        return true;
    }

    fs::create_directories(parent, ec);

    return !ec;
}

static bool http_request_bytes(const std::string& method,
                               const std::string& url,
                               std::vector<char>& outBytes,
                               std::string& err)
{
    ParsedUrl pu;

    if (!parse_url(url, pu)) {
        err = "invalid URL";
        return false;
    }

    std::wstring methodW(method.begin(), method.end());

    HINTERNET session = WinHttpOpen(
        L"DotTalk++",
        WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
        WINHTTP_NO_PROXY_NAME,
        WINHTTP_NO_PROXY_BYPASS,
        0);

    if (!session) {
        err = "WinHttpOpen failed";
        return false;
    }

    HINTERNET connect = WinHttpConnect(session, pu.host.c_str(), pu.port, 0);

    if (!connect) {
        err = "WinHttpConnect failed";
        WinHttpCloseHandle(session);
        return false;
    }

    HINTERNET request = WinHttpOpenRequest(
        connect,
        methodW.c_str(),
        pu.path.c_str(),
        nullptr,
        WINHTTP_NO_REFERER,
        WINHTTP_DEFAULT_ACCEPT_TYPES,
        pu.secure ? WINHTTP_FLAG_SECURE : 0);

    if (!request) {
        err = "WinHttpOpenRequest failed";
        WinHttpCloseHandle(connect);
        WinHttpCloseHandle(session);
        return false;
    }

    BOOL ok = WinHttpSendRequest(
        request,
        WINHTTP_NO_ADDITIONAL_HEADERS,
        0,
        WINHTTP_NO_REQUEST_DATA,
        0,
        0,
        0);

    if (!ok) {
        err = "WinHttpSendRequest failed";
        WinHttpCloseHandle(request);
        WinHttpCloseHandle(connect);
        WinHttpCloseHandle(session);
        return false;
    }

    ok = WinHttpReceiveResponse(request, nullptr);

    if (!ok) {
        err = "WinHttpReceiveResponse failed";
        WinHttpCloseHandle(request);
        WinHttpCloseHandle(connect);
        WinHttpCloseHandle(session);
        return false;
    }

    DWORD statusCode = 0;
    DWORD statusSize = sizeof(statusCode);

    if (WinHttpQueryHeaders(
            request,
            WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
            WINHTTP_HEADER_NAME_BY_INDEX,
            &statusCode,
            &statusSize,
            WINHTTP_NO_HEADER_INDEX)) {
        if (statusCode >= 400) {
            err = "HTTP error " + std::to_string(statusCode);
            WinHttpCloseHandle(request);
            WinHttpCloseHandle(connect);
            WinHttpCloseHandle(session);
            return false;
        }
    }

    outBytes.clear();

    while (true) {
        DWORD avail = 0;

        if (!WinHttpQueryDataAvailable(request, &avail)) {
            err = "WinHttpQueryDataAvailable failed";
            WinHttpCloseHandle(request);
            WinHttpCloseHandle(connect);
            WinHttpCloseHandle(session);
            return false;
        }

        if (avail == 0) {
            break;
        }

        std::vector<char> buf(avail);
        DWORD read = 0;

        if (!WinHttpReadData(request, buf.data(), avail, &read)) {
            err = "WinHttpReadData failed";
            WinHttpCloseHandle(request);
            WinHttpCloseHandle(connect);
            WinHttpCloseHandle(session);
            return false;
        }

        outBytes.insert(outBytes.end(), buf.begin(), buf.begin() + read);
    }

    WinHttpCloseHandle(request);
    WinHttpCloseHandle(connect);
    WinHttpCloseHandle(session);

    return true;
}

static bool save_bytes(const std::string& path,
                       const std::vector<char>& bytes,
                       std::string& err)
{
    if (!ensure_parent_dir(path)) {
        err = "unable to create parent directory";
        return false;
    }

    std::ofstream out(path, std::ios::binary | std::ios::trunc);

    if (!out) {
        err = "unable to open output file";
        return false;
    }

    if (!bytes.empty()) {
        out.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
    }

    if (!out) {
        err = "write failed";
        return false;
    }

    return true;
}

#else

static bool run_url_launcher_1(const char* launcher, const std::string& url)
{
    pid_t pid = fork();

    if (pid < 0) {
        return false;
    }

    if (pid == 0) {
        execlp(launcher, launcher, url.c_str(), static_cast<char*>(nullptr));
        _exit(127);
    }

    int status = 0;

    if (waitpid(pid, &status, 0) < 0) {
        return false;
    }

    return WIFEXITED(status) && WEXITSTATUS(status) == 0;
}

static bool run_url_launcher_2(const char* launcher,
                               const char* arg1,
                               const std::string& url)
{
    pid_t pid = fork();

    if (pid < 0) {
        return false;
    }

    if (pid == 0) {
        execlp(launcher, launcher, arg1, url.c_str(), static_cast<char*>(nullptr));
        _exit(127);
    }

    int status = 0;

    if (waitpid(pid, &status, 0) < 0) {
        return false;
    }

    return WIFEXITED(status) && WEXITSTATUS(status) == 0;
}

static bool launch_url_default_handler(const std::string& url, std::string& err)
{
    if (url.empty()) {
        err = "missing URL";
        return false;
    }

#if defined(__APPLE__)
    if (run_url_launcher_1("open", url)) {
        return true;
    }

    err = "unable to launch URL with open";
    return false;
#else
    if (run_url_launcher_1("xdg-open", url)) {
        return true;
    }

    if (run_url_launcher_2("gio", "open", url)) {
        return true;
    }

    err = "unable to launch URL; tried xdg-open and gio open";
    return false;
#endif
}

#endif // _WIN32

} // namespace

void cmd_WEB(DbArea&, std::istringstream& S)
{
    std::string sub;

    if (!(S >> sub)) {
        web_usage();
        return;
    }

    sub = uppercase_copy(sub);


    if (sub == "USAGE" || sub == "HELP" || sub == "?") {
        web_usage();
        return;
    }

    if (sub == "DEFAULT" || sub == "RETRO") {
        const std::string url = resolve_web_target(sub);
        std::string err;

        if (!launch_url_default_handler(url, err)) {
            std::cout << "WEB " << sub << ": " << err << "\n";
            return;
        }

        std::cout << "WEB " << sub << ": launched " << url << "\n";
        return;
    }

    if (sub == "OPEN" || sub == "LAUNCH") {
        std::string url;

        if (!(S >> url) || url.empty()) {
            web_usage();
            return;
        }

        url = resolve_web_target(url);

        std::string err;

        if (!launch_url_default_handler(url, err)) {
            std::cout << "WEB " << sub << ": " << err << "\n";
            return;
        }

        std::cout << "WEB " << sub << ": launched " << url << "\n";
        return;
    }

    if (sub == "GET" || sub == "HEAD") {
        std::string url;

        if (!(S >> url) || url.empty()) {
            web_usage();
            return;
        }

        url = resolve_web_target(url);

#ifdef _WIN32
        std::vector<char> bytes;
        std::string err;

        if (!http_request_bytes(sub, url, bytes, err)) {
            std::cout << "WEB: " << err << "\n";
            return;
        }

        if (!bytes.empty()) {
            std::cout.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
        }

        std::cout << "\n";
#else
        std::cout << "WEB " << sub << ": not implemented on this platform\n";
#endif

        return;
    }

    if (sub == "FETCH") {
        std::string url;

        if (!(S >> url) || url.empty()) {
            web_usage();
            return;
        }

        url = resolve_web_target(url);

        std::string toKw;

        if (!(S >> toKw)) {
            std::cout << "WEB FETCH: expected TO <file>\n";
            return;
        }

        toKw = uppercase_copy(toKw);

        if (toKw != "TO") {
            std::cout << "WEB FETCH: expected TO <file>\n";
            return;
        }

        std::string outFile;

        if (!(S >> outFile) || outFile.empty()) {
            std::cout << "WEB FETCH: expected output file\n";
            return;
        }

#ifdef _WIN32
        std::vector<char> bytes;
        std::string err;

        if (!http_request_bytes("GET", url, bytes, err)) {
            std::cout << "WEB FETCH: " << err << "\n";
            return;
        }

        if (!save_bytes(outFile, bytes, err)) {
            std::cout << "WEB FETCH: " << err << "\n";
            return;
        }

        std::cout << "WEB FETCH: wrote " << bytes.size()
                  << " byte(s) to " << outFile << "\n";
#else
        std::cout << "WEB FETCH: not implemented on this platform\n";
#endif

        return;
    }

    web_usage();
}