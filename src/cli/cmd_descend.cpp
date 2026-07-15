// @dottalk.usage v1
// owner: DOT|DESCEND
// command: DESCEND
// category: index
// status: supported
// noargs: mutate
// effect: configure
// mutates: order-state
// usage-access: DESCEND USAGE
// summary:
//   Set the active order/tag direction to descending for the current work area.
//
// usage:
//   DESCEND
//   DESCEND USAGE
//
// notes:
//   DESCEND requires an active order except for DESCEND USAGE.
//   DESCEND with no arguments mutates order direction to descending.
//   DESCEND does not mutate table records or rebuild indexes.
//
// risk:
//   mutates_order_state: yes
//   mutates_table_data: no
//   requires_active_order: yes except usage
//
// related:
//   ASCEND
//   SET ORDER
//   ORDER
//

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "cli/order_state.hpp"
#include <algorithm>
#include <cctype>
#include <string>
#include <sstream>

namespace {
static std::string descend_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string descend_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_descend_usage_request(const std::string& raw)
{
    std::string t = descend_upper(descend_trim(raw));
    if (t.rfind("DESCEND ", 0) == 0) {
        t = descend_upper(descend_trim(t.substr(8)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_descend_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DescendUsageText);
}
} // namespace

void cmd_DESCEND(xbase::DbArea& A, std::istringstream& in) {
    const std::string raw_args = in.str();
    if (is_descend_usage_request(raw_args)) {
        print_descend_usage();
        return;
    }

    if (!orderstate::hasOrder(A)) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::NoActiveIndex);
        return;
    }
    orderstate::setAscending(A, false);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::OrderDescendingSet);
}



