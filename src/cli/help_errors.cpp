#include "cli/help_errors.hpp"

#include "cli/output_router.hpp"

#include <algorithm>
#include <cctype>
#include <iomanip>
#include <ostream>
#include <sstream>
#include <string>

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

std::string hex32(std::uint32_t v)
{
    std::ostringstream oss;
    oss << "0x" << std::uppercase << std::hex << std::setw(8) << std::setfill('0') << v;
    return oss.str();
}

void print_error_catalog()
{
    out() << "ERROR TOPICS\n\n"
          << "  E_NO_TABLE_OPEN\n"
          << "  E_INVALID_RECORD_NUMBER\n"
          << "  E_INVALID_CURRENT_RECORD\n"
          << "  E_CLI_PARSE_ERROR\n"
          << "  E_ORDER_UNAVAILABLE\n\n"
          << "Use HELP ERROR <symbol> for details.\n";
}

} // anonymous namespace

void print_error_help(xbase::error::code ec)
{
    out() << xbase::error::symbol(ec) << "\n"
          << "  " << xbase::error::to_string(ec) << "\n"
          << "  packed: " << hex32(ec.value) << "\n";
}

bool show_error_topic(const std::string& term)
{
    const std::string up = upper_copy(term);

    if (up.empty() || up == "ERROR" || up == "ERRORS" || up == "OVERVIEW") {
        out() << "ERROR HELP\n\n"
              << "Errors describe failed actions or invalid runtime state.\n"
              << "The canonical identity for these is xbase::error::code.\n\n";
        print_error_catalog();
        return true;
    }

    if (up == "E_NO_TABLE_OPEN" || up == "NO_TABLE_OPEN") {
        print_error_help(xbase::error::e_no_table_open());
        return true;
    }

    if (up == "E_INVALID_RECORD_NUMBER" || up == "INVALID_RECORD_NUMBER") {
        print_error_help(xbase::error::e_invalid_record_number());
        return true;
    }

    if (up == "E_INVALID_CURRENT_RECORD" || up == "INVALID_CURRENT_RECORD") {
        print_error_help(xbase::error::e_invalid_current_record());
        return true;
    }

    if (up == "E_CLI_PARSE_ERROR" || up == "CLI_PARSE_ERROR") {
        print_error_help(xbase::error::e_cli_parse_error());
        return true;
    }

    if (up == "E_ORDER_UNAVAILABLE" || up == "ORDER_UNAVAILABLE") {
        print_error_help(xbase::error::e_order_unavailable());
        return true;
    }

    print_error_catalog();
    return true;
}

} // namespace dottalk::help
