// @dottalk.usage v1
// owner: EDU|CASE
// command: CASE
// category: education-reference
// status: supported
// noargs: usage
// effect: report
// mutates: none
// usage-access: CASE USAGE
// summary:
//   List and show educational case-study catalog entries.
//
// usage:
//   CASE USAGE
//   CASE HELP
//   CASE LIST
//   CASE SHOW <id>
//
// examples:
//   CASE
//   CASE LIST
//   CASE SHOW normalization
//
// notes:
//   CASE USAGE/HELP/? prints usage before catalog lookup.
//   CASE is read-only catalog/reference output.
//
// risk:
//   mutates_table_data: no
//

#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/command_registry.hpp"
#include "edu/case_catalog.hpp"

namespace {

using dottalk::cases::CaseStudy;
using dottalk::cases::catalog;
using dottalk::cases::trim_copy;
using dottalk::cases::up_copy;

static std::vector<std::string> split_ws(const std::string& s) {
    std::vector<std::string> out;
    std::istringstream iss(s);
    for (std::string t; iss >> t; ) out.push_back(t);
    return out;
}

static void print_usage() {
    std::cout
        << "Usage:\n"
        << "  CASE USAGE\n"
        << "  CASE HELP\n"
        << "  CASE LIST\n"
        << "  CASE SHOW <id>\n"
        << "Examples:\n"
        << "  CASE\n"
        << "  CASE LIST\n"
        << "  CASE SHOW normalization\n"
        << "Notes:\n"
        << "  - CASE USAGE does not load the case catalog.\n";
}

static void print_case_block(const char* heading, const std::string& body) {
    if (body.empty()) return;
    std::cout << "\n" << heading << "\n";
    std::cout << body << "\n";
}

static void cmd_help() {
    print_usage();
}

static void cmd_list() {
    std::string err;
    if (!catalog().load(&err)) {
        std::cout << "CASE LIST: " << err << "\n";
        return;
    }

    const auto items = catalog().list();
    if (items.empty()) {
        std::cout << "CASE LIST: no case studies found.\n";
        return;
    }

    std::cout << "CASE LIST (" << items.size() << ")\n";
    for (const CaseStudy* cs : items) {
        std::cout
            << std::left
            << std::setw(22) << cs->id
            << std::setw(52) << cs->title
            << std::setw(10) << cs->type
            << cs->era
            << "\n";
    }
}

static void cmd_show(const std::string& arg) {
    const std::string id = trim_copy(arg);
    if (id.empty()) {
        std::cout << "Usage: CASE SHOW <id>\n";
        return;
    }

    std::string err;
    if (!catalog().load(&err)) {
        std::cout << "CASE SHOW: " << err << "\n";
        return;
    }

    const CaseStudy* cs = catalog().find(id);
    if (!cs) {
        std::cout << "CASE SHOW: unknown case '" << id << "'.\n";
        return;
    }

    std::cout << "CASE: " << cs->title << "\n";
    std::cout << "ID   : " << cs->id << "\n";
    std::cout << "TYPE : " << cs->type << "\n";
    std::cout << "ERA  : " << cs->era << "\n";
    if (!cs->level.empty()) std::cout << "LEVEL: " << cs->level << "\n";
    if (!cs->lab.empty())   std::cout << "LAB  : " << cs->lab << "\n";

    if (!cs->domains.empty()) {
        std::cout << "DOMAINS: ";
        for (std::size_t i = 0; i < cs->domains.size(); ++i) {
            std::cout << cs->domains[i];
            if (i + 1 < cs->domains.size()) std::cout << ", ";
        }
        std::cout << "\n";
    }

    print_case_block("SUMMARY",  cs->summary);
    print_case_block("PROBLEM",  cs->problem);
    print_case_block("WORKFLOW", cs->workflow);
    print_case_block("MODEL",    cs->model);
    print_case_block("TAKEAWAY", cs->takeaway);
}

} // namespace

void edu_CASESTUDY(xbase::DbArea& area, std::istringstream& iss)
{
    (void)area;

    std::string raw;
    std::getline(iss >> std::ws, raw);
    raw = trim_copy(raw);

    const std::vector<std::string> parts = split_ws(raw);

    std::string sub;
    if (!parts.empty()) {
        sub = parts.front();
    }

    const std::string SUB = up_copy(sub);

    std::string rest;
    if (raw.size() > sub.size()) {
        rest = trim_copy(raw.substr(sub.size()));
    }

    if (SUB.empty() || SUB == "USAGE" || SUB == "HELP" || SUB == "?" || SUB == "/?" || SUB == "-H" || SUB == "--HELP") {
        cmd_help();
        return;
    }

    if (SUB == "LIST") {
        cmd_list();
        return;
    }

    if (SUB == "SHOW") {
        cmd_show(rest);
        return;
    }

    std::cout << "CASE: unknown subcommand '" << sub << "'.\n";
    print_usage();
}

static bool s_registered = []() {
    dli::registry().add("CASE", &edu_CASESTUDY);
    return true;
}();