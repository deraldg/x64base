// src/cli/cmd_drawio.cpp
//
// DRAWIO command
//
// Launches the online diagrams.net / draw.io editor in the default browser.
//
// Usage:
//   DRAWIO
//   DRAWIO OPEN
//   DRAWIO OPEN <url>

#include <iostream>
#include <sstream>
#include <string>
#include <cstdlib>
#include <cctype>

#include "xbase.hpp"
#include "textio.hpp"

#if defined(_WIN32)
    #include <windows.h>
    #include <shellapi.h>
#endif

namespace {

static std::string trim_copy(std::string s) {
    return textio::trim(std::move(s));
}

static std::string up_copy(std::string s) {
    for (auto& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static void print_usage() {
    std::cout
        << "Usage:\n"
        << "  DRAWIO\n"
        << "  DRAWIO OPEN\n"
        << "  DRAWIO OPEN <url>\n"
        << "\n"
        << "Default:\n"
        << "  https://app.diagrams.net\n";
}

static bool launch_url(const std::string& url) {
#if defined(_WIN32)
    HINSTANCE rc = ShellExecuteA(
        nullptr,
        "open",
        url.c_str(),
        nullptr,
        nullptr,
        SW_SHOWNORMAL
    );
    return reinterpret_cast<intptr_t>(rc) > 32;
#elif defined(__APPLE__)
    std::string cmd = "open \"" + url + "\"";
    return std::system(cmd.c_str()) == 0;
#else
    std::string cmd = "xdg-open \"" + url + "\" >/dev/null 2>&1";
    return std::system(cmd.c_str()) == 0;
#endif
}

} // namespace

void cmd_DRAWIO(xbase::DbArea& area, std::istringstream& iss) {
    (void)area;

    std::string sub;
    iss >> sub;

    if (sub.empty()) {
        const std::string url = "https://app.diagrams.net";
        if (launch_url(url)) {
            std::cout << "DRAWIO: launched " << url << "\n";
        } else {
            std::cout << "DRAWIO: failed to launch browser.\n";
        }
        return;
    }

    const std::string SUB = up_copy(sub);

    if (SUB == "HELP" || SUB == "/?" || SUB == "-H" || SUB == "--HELP") {
        print_usage();
        return;
    }

    if (SUB == "OPEN") {
        std::string rest;
        std::getline(iss >> std::ws, rest);
        rest = trim_copy(rest);

        const std::string url = rest.empty()
            ? "https://app.diagrams.net"
            : rest;

        if (launch_url(url)) {
            std::cout << "DRAWIO: launched " << url << "\n";
        } else {
            std::cout << "DRAWIO: failed to launch browser.\n";
        }
        return;
    }

    print_usage();
}