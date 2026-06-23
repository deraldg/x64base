#include "help/reference_collection.hpp"

#include <algorithm>
#include <cctype>
#include <map>
#include <set>
#include <sstream>
#include <unordered_set>

namespace refsys {
namespace {

static std::unordered_set<std::string> command_name_set(const ReferenceCollection& rc)
{
    std::unordered_set<std::string> names;
    for (const auto& cmd : rc.commands) {
        names.insert(cmd.canonical_name);
    }
    return names;
}

static std::unordered_set<std::string> qualified_subcommand_set(const ReferenceCollection& rc)
{
    std::unordered_set<std::string> names;
    for (const auto& sc : rc.subcommands) {
        names.insert(sc.qualified_name);
    }
    return names;
}

static std::string upper_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static std::string compact_token(std::string s)
{
    s = upper_copy(std::move(s));
    s.erase(std::remove_if(s.begin(), s.end(),
                           [](unsigned char ch) {
                               return std::isspace(ch) != 0 || ch == '_' || ch == '-';
                           }),
            s.end());
    return s;
}

static bool has_space(const std::string& s)
{
    return std::any_of(s.begin(), s.end(),
                       [](unsigned char ch) { return std::isspace(ch) != 0; });
}

static std::string compact_set_family_target(const std::string& token)
{
    // Only compact spellings are violations/aliases here.  Already-spaced
    // canonical topics such as SET ORDER and SET INDEX are valid and must not
    // be re-flagged just because compact_token() can reduce them to SETORDER.
    if (has_space(token)) {
        return {};
    }

    static const std::map<std::string, std::string> kMap = {
        {"SETORDER",  "SET ORDER"},
        {"SETINDEX",  "SET INDEX"},
        {"SETFILTER", "SET FILTER"},
        {"SETCASE",   "SET CASE"},
        {"SETPATH",   "SET PATH"},
        {"SETCNX",    "SET CNX"},
        {"SETCDX",    "SET CDX"},
        {"SETLMDB",   "SET LMDB"},
        {"SETNEAR",   "SET NEAR"},
        {"SETUNIQUE", "SET UNIQUE"}
    };

    const auto it = kMap.find(compact_token(token));
    return it == kMap.end() ? std::string{} : it->second;
}

} // namespace

std::vector<CheckIssue> check_unresolved_variant_targets(const ReferenceCollection& rc)
{
    std::vector<CheckIssue> issues;

    const auto command_names = command_name_set(rc);
    const auto subcommand_names = qualified_subcommand_set(rc);

    for (const auto& ev : rc.entry_variants) {
        const bool found_as_command = (command_names.find(ev.canonical_command) != command_names.end());
        const bool found_as_subcmd = (subcommand_names.find(ev.canonical_command) != subcommand_names.end());

        if (!found_as_command && !found_as_subcmd) {
            std::ostringstream oss;
            oss << "unresolved variant target: token=" << ev.token
                << " kind=" << ev.kind
                << " target=" << ev.canonical_command;
            issues.push_back({"ERROR", oss.str()});
        }
    }

    return issues;
}

std::vector<CheckIssue> check_duplicate_canonical_commands(const ReferenceCollection& rc)
{
    std::vector<CheckIssue> issues;
    std::set<std::string> seen;

    for (const auto& cmd : rc.commands) {
        const auto inserted = seen.insert(cmd.canonical_name);
        if (!inserted.second) {
            std::ostringstream oss;
            oss << "duplicate canonical command: " << cmd.canonical_name;
            issues.push_back({"ERROR", oss.str()});
        }
    }

    return issues;
}

std::vector<CheckIssue> check_duplicate_subcommands(const ReferenceCollection& rc)
{
    std::vector<CheckIssue> issues;
    std::set<std::pair<std::string, std::string>> seen;

    for (const auto& sc : rc.subcommands) {
        const auto key = std::make_pair(sc.parent_command, sc.name);
        const auto inserted = seen.insert(key);
        if (!inserted.second) {
            std::ostringstream oss;
            oss << "duplicate subcommand: parent=" << sc.parent_command
                << " name=" << sc.name;
            issues.push_back({"ERROR", oss.str()});
        }
    }

    return issues;
}

std::vector<CheckIssue> check_missing_parent_commands(const ReferenceCollection& rc)
{
    std::vector<CheckIssue> issues;
    const auto command_names = command_name_set(rc);

    for (const auto& sc : rc.subcommands) {
        if (command_names.find(sc.parent_command) == command_names.end()) {
            std::ostringstream oss;
            oss << "missing parent command: parent=" << sc.parent_command
                << " subcommand=" << sc.name;
            issues.push_back({"ERROR", oss.str()});
        }
    }

    return issues;
}

std::vector<CheckIssue> check_set_family_canonicalization(const ReferenceCollection& rc)
{
    std::vector<CheckIssue> issues;

    // CODEX convention: compact SET-family verbs are compatibility aliases.
    // The canonical reflected/help topic must be the spaced SET * form.
    for (const auto& cmd : rc.commands) {
        const std::string expected = compact_set_family_target(cmd.canonical_name);
        if (!expected.empty()) {
            std::ostringstream oss;
            oss << "SET-family canonical command must be spaced: "
                << cmd.canonical_name << " should be " << expected;
            issues.push_back({"ERROR", oss.str()});
        }
    }

    for (const auto& sc : rc.subcommands) {
        const std::string expected = compact_set_family_target(sc.qualified_name);
        if (!expected.empty()) {
            std::ostringstream oss;
            oss << "SET-family subcommand must be represented as parent SET + name: "
                << sc.qualified_name << " should be " << expected;
            issues.push_back({"ERROR", oss.str()});
        }
    }

    for (const auto& ev : rc.entry_variants) {
        const std::string token_expected = compact_set_family_target(ev.token);
        if (!token_expected.empty() && ev.canonical_command != token_expected) {
            std::ostringstream oss;
            oss << "SET-family variant target mismatch: token=" << ev.token
                << " target=" << ev.canonical_command
                << " expected=" << token_expected;
            issues.push_back({"ERROR", oss.str()});
        }

        const std::string target_expected = compact_set_family_target(ev.canonical_command);
        if (!target_expected.empty() && ev.canonical_command != target_expected) {
            std::ostringstream oss;
            oss << "SET-family variant target must be canonical spaced form: token="
                << ev.token << " target=" << ev.canonical_command
                << " should be " << target_expected;
            issues.push_back({"ERROR", oss.str()});
        }
    }

    return issues;
}

std::vector<CheckIssue> check_duplicate_functions(const ReferenceCollection& rc)
{
    std::vector<CheckIssue> issues;
    std::set<std::string> seen;

    for (const auto& fn : rc.functions) {
        const auto inserted = seen.insert(fn.canonical_name);
        if (!inserted.second) {
            std::ostringstream oss;
            oss << "duplicate function: " << fn.canonical_name;
            issues.push_back({"ERROR", oss.str()});
        }
    }

    return issues;
}

std::vector<CheckIssue> check_invalid_function_arg_ranges(const ReferenceCollection& rc)
{
    std::vector<CheckIssue> issues;

    for (const auto& fn : rc.functions) {
        if (fn.min_args > fn.max_args) {
            std::ostringstream oss;
            oss << "invalid function arg range: " << fn.canonical_name
                << " min=" << fn.min_args
                << " max=" << fn.max_args;
            issues.push_back({"ERROR", oss.str()});
        }
    }

    return issues;
}

std::vector<CheckIssue> check_missing_function_categories(const ReferenceCollection& rc)
{
    std::vector<CheckIssue> issues;

    for (const auto& fn : rc.functions) {
        if (fn.category.empty()) {
            std::ostringstream oss;
            oss << "missing function category: " << fn.canonical_name;
            issues.push_back({"WARNING", oss.str()});
        }
    }

    return issues;
}

void print_check_issues(const std::vector<CheckIssue>& issues, std::ostream& os)
{
    os << "Structural Checks\n";
    os << "=================\n";

    if (issues.empty()) {
        os << "OK no structural issues found\n\n";
        return;
    }

    std::size_t error_count = 0;
    std::size_t warning_count = 0;
    std::size_t note_count = 0;

    for (const auto& issue : issues) {
        os << issue.severity << ' ' << issue.message << '\n';

        if (issue.severity == "ERROR") {
            ++error_count;
        } else if (issue.severity == "WARNING") {
            ++warning_count;
        } else {
            ++note_count;
        }
    }

    os << "\nSummary: "
       << error_count << " errors, "
       << warning_count << " warnings, "
       << note_count << " notes\n\n";
}

} // namespace refsys