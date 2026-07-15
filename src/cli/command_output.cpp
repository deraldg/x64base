#include "cli/command_output.hpp"

#include "cli/output_router.hpp"
#include "cli/command_catalog.hpp"
#include "cli/settings.hpp"

#include <ostream>
#include <vector>

namespace cli::cmdout {

namespace {

inline std::ostream& out()
{
    return cli::OutputRouter::instance().out();
}

inline void print_heading(dottalk::helpdata::MessageId id)
{
    out() << "\n"
          << dottalk::helpdata::format_message(
                 id, {}, cli::Settings::instance().message_locale)
          << '\n';
}

inline void print_indented_lines(const std::vector<std::string>& lines)
{
    for (const auto& line : lines) {
        out() << "  " << line << '\n';
    }
}

} // anonymous namespace

void print_line(const std::string& s)
{
    out() << s << '\n';
}

std::string message_text(
    dottalk::helpdata::MessageId id,
    const std::unordered_map<std::string, std::string>& vars)
{
    return dottalk::helpdata::format_message(id, vars, cli::Settings::instance().message_locale);
}

void print_message(
    dottalk::helpdata::MessageId id,
    const std::unordered_map<std::string, std::string>& vars)
{
    print_line(message_text(id, vars));
}

void print_prefixed_message(
    const char* cmd,
    dottalk::helpdata::MessageId id,
    const std::unordered_map<std::string, std::string>& vars)
{
    const std::string text = message_text(id, vars);
    if (cmd && *cmd) {
        out() << cmd << ": " << text << '\n';
    } else {
        out() << text << '\n';
    }
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

    out() << message_text(dottalk::helpdata::MessageId::GlobalSyntaxTitle) << '\n';
    print_indented_lines(doc->syntax);
}

void show_command_help(const std::string& cmd)
{
    const auto* doc = dottalk::doc::get(cmd);
    if (!doc) return;

    out() << doc->name << " - " << doc->summary << '\n';

    if (!doc->syntax.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalSyntaxTitle);
        print_indented_lines(doc->syntax);
    }

    if (!doc->samples.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalExamplesTitle);
        print_indented_lines(doc->samples);
    }

    if (!doc->notes.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalNotesTitle);
        print_indented_lines(doc->notes);
    }

    if (!doc->warnings.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalWarningsTitle);
        print_indented_lines(doc->warnings);
    }
}

} // namespace cli::cmdout
