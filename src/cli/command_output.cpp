#include "cli/command_output.hpp"

#include "cli/output_router.hpp"
#include "cli/command_catalog.hpp"

#include <ostream>

namespace cli::cmdout {

namespace {

inline std::ostream& out()
{
    return cli::OutputRouter::instance().out();
}

} // anonymous namespace

void print_line(const std::string& s)
{
    out() << s << '\n';
}

void print_info(const char* cmd, const std::string& text)
{
    if (cmd && *cmd) {
        out() << cmd << ": " << text << '\n';
    } else {
        out() << text << '\n';
    }
}

void print_error(const char* cmd, xbase::error::code ec)
{
    if (cmd && *cmd) {
        out() << cmd << ": " << xbase::error::to_string(ec) << '\n';
    } else {
        out() << xbase::error::to_string(ec) << '\n';
    }
}

void print_warning(const char* cmd, xbase::error::code ec)
{
    if (cmd && *cmd) {
        out() << cmd << ": warning: " << xbase::error::to_string(ec) << '\n';
    } else {
        out() << "warning: " << xbase::error::to_string(ec) << '\n';
    }
}

void print_note(const char* cmd, const std::string& text)
{
    if (cmd && *cmd) {
        out() << cmd << ": note: " << text << '\n';
    } else {
        out() << "note: " << text << '\n';
    }
}

void show_command_syntax(const std::string& cmd)
{
    const auto* doc = dottalk::doc::get(cmd);
    if (!doc || doc->syntax.empty()) return;

    out() << "Syntax:\n";
    for (const auto& line : doc->syntax) {
        out() << "  " << line << '\n';
    }
}

void show_command_help(const std::string& cmd)
{
    const auto* doc = dottalk::doc::get(cmd);
    if (!doc) return;

    out() << doc->name << " - " << doc->summary << '\n';

    if (!doc->syntax.empty()) {
        out() << "\nSyntax:\n";
        for (const auto& line : doc->syntax) {
            out() << "  " << line << '\n';
        }
    }

    if (!doc->samples.empty()) {
        out() << "\nExamples:\n";
        for (const auto& line : doc->samples) {
            out() << "  " << line << '\n';
        }
    }

    if (!doc->notes.empty()) {
        out() << "\nNotes:\n";
        for (const auto& line : doc->notes) {
            out() << "  " << line << '\n';
        }
    }

    if (!doc->warnings.empty()) {
        out() << "\nWarnings:\n";
        for (const auto& line : doc->warnings) {
            out() << "  " << line << '\n';
        }
    }
}

} // namespace cli::cmdout
