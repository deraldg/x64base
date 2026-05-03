#include "cli/help_warnings.hpp"

#include "cli/output_router.hpp"

#include <algorithm>
#include <cctype>
#include <ostream>
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

void print_warning_catalog()
{
    out() << "WARNING TOPICS\n\n"
          << "  W_FOR_CLAUSE_IGNORED\n"
          << "  W_ORDER_FALLBACK_PHYSICAL\n\n"
          << "Use HELP WARNING <symbol> for details.\n";
}

} // anonymous namespace

void print_warning_help(xbase::error::code ec)
{
    out() << xbase::error::symbol(ec) << "\n"
          << "  " << xbase::error::to_string(ec) << "\n";
}

bool show_warning_topic(const std::string& term)
{
    const std::string up = upper_copy(term);

    if (up.empty() || up == "WARNING" || up == "WARNINGS" || up == "OVERVIEW") {
        out() << "WARNING HELP\n\n"
              << "Warnings describe degraded-but-usable behavior.\n"
              << "Execution continues, but the requested behavior was altered,\n"
              << "ignored, or downgraded.\n\n";
        print_warning_catalog();
        return true;
    }

    if (up == "W_FOR_CLAUSE_IGNORED" || up == "FOR" || up == "FOR_CLAUSE") {
        print_warning_help(xbase::error::w_for_clause_ignored());
        out() << "\nExplanation:\n"
              << "  A FOR clause was rejected or ignored after parsing/compile failure.\n";
        return true;
    }

    if (up == "W_ORDER_FALLBACK_PHYSICAL" || up == "ORDER" || up == "FALLBACK") {
        print_warning_help(xbase::error::w_order_fallback_physical());
        out() << "\nExplanation:\n"
              << "  Ordered traversal was unavailable, so the command fell back to physical order.\n";
        return true;
    }

    print_warning_catalog();
    return true;
}

} // namespace dottalk::help
