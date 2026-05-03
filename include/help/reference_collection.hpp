#pragma once

#include <iosfwd>
#include <string>
#include <vector>

namespace refsys {

// -----------------------------
// Core reflected entities
// -----------------------------

struct CommandInfo {
    std::string canonical_name;

    std::vector<std::string> aliases;
    std::vector<std::string> shortcuts;
    std::vector<std::string> reexpressions;

    std::string handler_name;
    std::string source_file;

    std::string family;
    std::string authority;
    std::string status;

    bool implemented{false};
    bool public_surface{true};
    bool writes_console_direct{false};
    bool uses_output_router{false};
    bool uses_message_catalog{false};

    std::string summary;
    std::vector<std::string> syntax;
    std::vector<std::string> examples;
    std::vector<std::string> notes;
    std::vector<std::string> warnings;
};

struct SubcommandInfo {
    std::string parent_command;
    std::string name;
    std::string qualified_name;
    std::string dispatch_style;
    std::string handler_name;
    std::string source_file;

    std::string family;
    std::string authority;
    std::string status;

    bool implemented{false};
    bool public_surface{true};
    bool uses_output_router{false};
    bool uses_message_catalog{false};

    std::string summary;
    std::vector<std::string> syntax;
    std::vector<std::string> examples;
    std::vector<std::string> notes;
    std::vector<std::string> warnings;
};

struct EntryVariantInfo {
    std::string token;
    std::string canonical_command;
    std::string kind;
    std::string source_file;
    std::string notes;
};

struct FunctionInfo {
    std::string canonical_name;
    std::vector<std::string> aliases;

    std::string handler_name;
    std::string source_file;
    std::string category;
    std::string authority;
    std::string status;

    int min_args{0};
    int max_args{0};

    bool implemented{false};
    bool public_surface{true};
    bool callable_from_calc{true};
    bool uses_message_catalog{false};

    std::string summary;
    std::vector<std::string> syntax;
    std::vector<std::string> examples;
    std::vector<std::string> notes;
    std::vector<std::string> warnings;
};

struct MessageInfo {
    std::string symbol;
    std::string enum_name;
    std::string severity;
    std::string facility;
    std::string short_text;
    std::string suggested_action;
    std::string source_file;

    bool implemented{true};
    bool public_surface{true};
    bool used_by_runtime{false};

    std::vector<std::string> used_by_commands;
    std::vector<std::string> notes;
};

struct ArgInfo {
    std::string owner_kind;
    std::string owner_name;
    std::string arg_name;
    std::string kind;
    bool required{false};
    bool repeatable{false};

    std::string value_shape;
    std::string source_file;

    std::string summary;
    std::vector<std::string> syntax;
    std::vector<std::string> notes;
    std::vector<std::string> warnings;
};

struct ReferenceCollection {
    std::vector<CommandInfo>      commands;
    std::vector<SubcommandInfo>   subcommands;
    std::vector<ArgInfo>          args;
    std::vector<FunctionInfo>     functions;
    std::vector<EntryVariantInfo> entry_variants;
    std::vector<MessageInfo>      messages;
};

// -----------------------------
// Builder
// -----------------------------

ReferenceCollection build_reference_collection();

// -----------------------------
// Reports
// -----------------------------

void report_subcommands(const ReferenceCollection& rc, std::ostream& os);
void report_commands(const ReferenceCollection& rc, std::ostream& os);
void report_functions(const ReferenceCollection& rc, std::ostream& os);

// -----------------------------
// Checks
// -----------------------------

struct CheckIssue {
    std::string severity; // ERROR, WARNING, NOTE
    std::string message;
};

std::vector<CheckIssue> check_unresolved_variant_targets(const ReferenceCollection& rc);
std::vector<CheckIssue> check_duplicate_canonical_commands(const ReferenceCollection& rc);
std::vector<CheckIssue> check_duplicate_subcommands(const ReferenceCollection& rc);
std::vector<CheckIssue> check_missing_parent_commands(const ReferenceCollection& rc);

// Function checks
std::vector<CheckIssue> check_duplicate_functions(const ReferenceCollection& rc);
std::vector<CheckIssue> check_invalid_function_arg_ranges(const ReferenceCollection& rc);
std::vector<CheckIssue> check_missing_function_categories(const ReferenceCollection& rc);

void print_check_issues(const std::vector<CheckIssue>& issues, std::ostream& os);

} // namespace refsys