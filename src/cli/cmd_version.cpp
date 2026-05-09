// @dottalk.usage v1
// owner: DOT|VERSION
// command: VERSION
// category: report
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: VERSION USAGE
// summary:
//   Report the DotTalk++ version label and build date/time.
//
// usage:
//   VERSION
//   VERSION USAGE
//
// notes:
//   VERSION with no arguments reports version and build information.
//   VERSION USAGE prints usage.
//   VERSION is read-only and does not mutate table data or session state.
//
// risk:
//   mutates_table_data: no
//   mutates_session: no
//
// related:
//   ABOUT
//   SQLVER
//

#include "cmd_version.hpp"
#include <iostream>
#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>

#ifndef DOTTALKPP_VERSION
// #define DOTTALKPP_VERSION "alpha-v15.0"
#define DOTTALKPP_VERSION "beta-0"
#endif


namespace {
static std::string version_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string version_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_version_usage_request(const std::string& raw)
{
    std::string t = version_upper(version_trim(raw));
    if (t.rfind("VERSION ", 0) == 0) {
        t = version_upper(version_trim(t.substr(8)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_version_usage()
{
    std::cout << "Usage:\n"
              << "  VERSION\n"
              << "  VERSION USAGE\n";
}
} // namespace

void cmd_VERSION(xbase::DbArea& area, std::istringstream& args) {
    (void)area;
    if (is_version_usage_request(args.str())) {
        print_version_usage();
        return;
    }

    std::cout << "dottalk++ " << DOTTALKPP_VERSION
              << "  (" << __DATE__ << " " << __TIME__ << ")\n";
    // cmd_version.cpp
    std::cout << "DotTalk++ build " << __DATE__ << " " << __TIME__ << "\n";

}
 


