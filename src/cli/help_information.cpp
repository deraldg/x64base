#include "cli/help_information.hpp"

#include "cli/output_router.hpp"
#include "cli/command_catalog.hpp"

#include <algorithm>
#include <cctype>
#include <ostream>
#include <string>
#include <vector>

namespace dottalk::help {

namespace {

inline std::ostream& out()
{
    return cli::OutputRouter::instance().out();
}

std::string upper_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

void print_doc_note_topics()
{
    out() << "INFORMATION TOPICS\n\n"
          << "  HELP INFO OVERVIEW    - explain the runtime message split\n"
          << "  HELP INFO OUTPUT      - explain OutputRouter + command_output\n"
          << "  HELP INFO CATALOG     - explain command_catalog usage\n";
}

} // anonymous namespace

void show_information_overview()
{
    out() << "INFORMATION HELP\n\n"
          << "Information messages are runtime non-problem notices.\n"
          << "Use them for status, progress, successful routing, and behavioral notes.\n\n"
          << "Examples:\n"
          << "  LIST: using physical order\n"
          << "  SCHEMAS: 13 table(s) opened\n"
          << "  SET ORDER: tag LNAME active\n";
}

bool show_information_topic(const std::string& term)
{
    const std::string up = upper_copy(term);

    if (up.empty() || up == "INFO" || up == "INFORMATION" || up == "OVERVIEW") {
        show_information_overview();
        return true;
    }

    if (up == "OUTPUT") {
        out() << "INFORMATION: OUTPUT\n\n"
              << "Runtime informational text should go through cli::cmdout::print_info()\n"
              << "and ultimately through OutputRouter.\n";
        return true;
    }

    if (up == "CATALOG") {
        out() << "INFORMATION: COMMAND CATALOG\n\n"
              << "command_catalog owns static command documentation:\n"
              << "summary, syntax, examples, notes, and usage warnings.\n"
              << "It does not own runtime errors.\n";
        return true;
    }

    print_doc_note_topics();
    return true;
}

} // namespace dottalk::help
