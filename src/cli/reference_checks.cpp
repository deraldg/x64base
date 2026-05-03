#include "help/reference_collection.hpp"

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