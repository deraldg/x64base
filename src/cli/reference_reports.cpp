#include "help/reference_collection.hpp"

#include <algorithm>
#include <iomanip>
#include <ostream>
#include <sstream>
#include <vector>

namespace refsys {
namespace {

const char* yn(const bool v)
{
    return v ? "Y" : "N";
}

std::string join_or_dash(const std::vector<std::string>& values)
{
    if (values.empty()) {
        return "-";
    }

    std::ostringstream oss;
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i != 0U) {
            oss << ", ";
        }
        oss << values[i];
    }
    return oss.str();
}

std::size_t subcommand_count_for(const ReferenceCollection& rc,
                                 const std::string& canonical_name)
{
    std::size_t count = 0;
    for (const auto& sc : rc.subcommands) {
        if (sc.parent_command == canonical_name) {
            ++count;
        }
    }
    return count;
}

} // anonymous namespace

void report_subcommands(const ReferenceCollection& rc, std::ostream& os)
{
    std::vector<SubcommandInfo> rows = rc.subcommands;

    std::sort(rows.begin(), rows.end(),
              [](const SubcommandInfo& a, const SubcommandInfo& b) {
                  if (a.parent_command != b.parent_command) {
                      return a.parent_command < b.parent_command;
                  }
                  if (a.public_surface != b.public_surface) {
                      return a.public_surface > b.public_surface;
                  }
                  if (a.name != b.name) {
                      return a.name < b.name;
                  }
                  return a.qualified_name < b.qualified_name;
              });

    os << "Subcommand Inventory\n";
    os << "====================\n\n";

    os << std::left
       << std::setw(10) << "PARENT"
       << std::setw(18) << "NAME"
       << std::setw(24) << "QUALIFIED_NAME"
       << std::setw(22) << "DISPATCH"
       << std::setw(8)  << "PUBLIC"
       << std::setw(20) << "HANDLER"
       << std::setw(18) << "AUTHORITY"
       << std::setw(10) << "STATUS"
       << std::setw(8)  << "SYNTAX"
       << '\n';

    os << std::setw(10) << "------"
       << std::setw(18) << "------------"
       << std::setw(24) << "-------------------"
       << std::setw(22) << "-------------------"
       << std::setw(8)  << "------"
       << std::setw(20) << "--------------"
       << std::setw(18) << "----------------"
       << std::setw(10) << "-------"
       << std::setw(8)  << "------"
       << '\n';

    for (const auto& sc : rows) {
        os << std::setw(10) << sc.parent_command
           << std::setw(18) << sc.name
           << std::setw(24) << sc.qualified_name
           << std::setw(22) << sc.dispatch_style
           << std::setw(8)  << yn(sc.public_surface)
           << std::setw(20) << sc.handler_name
           << std::setw(18) << sc.authority
           << std::setw(10) << sc.status
           << std::setw(8)  << yn(!sc.syntax.empty())
           << '\n';
    }

    os << '\n';
}

void report_commands(const ReferenceCollection& rc, std::ostream& os)
{
    std::vector<CommandInfo> rows = rc.commands;

    std::sort(rows.begin(), rows.end(),
              [](const CommandInfo& a, const CommandInfo& b) {
                  return a.canonical_name < b.canonical_name;
              });

    os << "Command Inventory\n";
    os << "=================\n\n";

    os << std::left
       << std::setw(16) << "COMMAND"
       << std::setw(10) << "FAMILY"
       << std::setw(18) << "AUTHORITY"
       << std::setw(10) << "STATUS"
       << std::setw(18) << "ALIASES"
       << std::setw(18) << "SHORTCUTS"
       << std::setw(20) << "REEXPRESSIONS"
       << std::setw(6)  << "SUBS"
       << std::setw(8)  << "DIRECT"
       << std::setw(11) << "OUTROUTER"
       << std::setw(8)  << "MSGCAT"
       << std::setw(20) << "HANDLER"
       << "SOURCE"
       << '\n';

    os << std::setw(16) << "-----------"
       << std::setw(10) << "-------"
       << std::setw(18) << "----------------"
       << std::setw(10) << "-------"
       << std::setw(18) << "-------"
       << std::setw(18) << "---------"
       << std::setw(20) << "-------------"
       << std::setw(6)  << "----"
       << std::setw(8)  << "------"
       << std::setw(11) << "---------"
       << std::setw(8)  << "------"
       << std::setw(20) << "--------------"
       << "-----------------\n";

    for (const auto& cmd : rows) {
        os << std::setw(16) << cmd.canonical_name
           << std::setw(10) << cmd.family
           << std::setw(18) << cmd.authority
           << std::setw(10) << cmd.status
           << std::setw(18) << join_or_dash(cmd.aliases)
           << std::setw(18) << join_or_dash(cmd.shortcuts)
           << std::setw(20) << join_or_dash(cmd.reexpressions)
           << std::setw(6)  << subcommand_count_for(rc, cmd.canonical_name)
           << std::setw(8)  << yn(cmd.writes_console_direct)
           << std::setw(11) << yn(cmd.uses_output_router)
           << std::setw(8)  << yn(cmd.uses_message_catalog)
           << std::setw(20) << cmd.handler_name
           << cmd.source_file
           << '\n';
    }

    os << '\n';
}

void report_functions(const ReferenceCollection& rc, std::ostream& os)
{
    std::vector<FunctionInfo> rows = rc.functions;

    std::sort(rows.begin(), rows.end(),
              [](const FunctionInfo& a, const FunctionInfo& b) {
                  return a.canonical_name < b.canonical_name;
              });

    os << "Function Inventory\n";
    os << "==================\n\n";

    os << std::left
       << std::setw(16) << "NAME"
       << std::setw(12) << "CATEGORY"
       << std::setw(6)  << "MIN"
       << std::setw(6)  << "MAX"
       << std::setw(18) << "AUTHORITY"
       << std::setw(10) << "STATUS"
       << "SOURCE"
       << '\n';

    os << std::setw(16) << "-----------"
       << std::setw(12) << "---------"
       << std::setw(6)  << "---"
       << std::setw(6)  << "---"
       << std::setw(18) << "----------------"
       << std::setw(10) << "-------"
       << "-------------\n";

    for (const auto& fn : rows) {
        os << std::setw(16) << fn.canonical_name
           << std::setw(12) << fn.category
           << std::setw(6)  << fn.min_args
           << std::setw(6)  << fn.max_args
           << std::setw(18) << fn.authority
           << std::setw(10) << fn.status
           << fn.source_file
           << '\n';
    }

    os << '\n';
}

} // namespace refsys