
#include "generated_help_runtime_contract.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>

namespace dottalk::maintenance::generated_help {
namespace {

std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::toupper(c));
    });
    return s;
}

bool contains_case_insensitive(const std::string& haystack, const std::string& needle) {
    return upper_copy(haystack).find(upper_copy(needle)) != std::string::npos;
}

}  // namespace

RuntimeSmokeCommandSet make_help_runtime_smoke_setup(
    const std::string& help_dbf_root,
    const std::string& help_index_root) {
    RuntimeSmokeCommandSet set;
    set.lines.push_back("ECHO OFF");
    set.lines.push_back("SET PAGING OFF");
    set.lines.push_back("SETPATH DBF " + help_dbf_root);
    set.lines.push_back("SETPATH INDEXES " + help_index_root);
    set.lines.push_back("WORKSPACE CLOSE");
    set.lines.push_back("WORKSPACE OPEN DBF");
    set.lines.push_back("WORKSPACE");
    return set;
}

bool generated_help_smoke_contract_ok(const std::vector<std::string>& lines,
                                      std::string* reason_out) {
    bool saw_setpath_dbf = false;
    bool saw_setpath_indexes = false;
    for (const auto& line : lines) {
        if (contains_case_insensitive(line, "SETPATH DBF")) {
            saw_setpath_dbf = true;
        }
        if (contains_case_insensitive(line, "SETPATH INDEXES")) {
            saw_setpath_indexes = true;
        }
        if (contains_case_insensitive(line, "DO cmdhelp")) {
            if (reason_out) *reason_out = "generated HELP smoke must not call DO cmdhelp";
            return false;
        }
        if (contains_case_insensitive(line, "GOTO <n>")) {
            if (reason_out) *reason_out = "generated HELP smoke must not contain GOTO <n> placeholders";
            return false;
        }
    }
    if (!saw_setpath_dbf) {
        if (reason_out) *reason_out = "generated HELP smoke missing SETPATH DBF";
        return false;
    }
    if (!saw_setpath_indexes) {
        if (reason_out) *reason_out = "generated HELP smoke missing SETPATH INDEXES";
        return false;
    }
    if (reason_out) reason_out->clear();
    return true;
}

}  // namespace dottalk::maintenance::generated_help
