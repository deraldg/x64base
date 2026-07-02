// @dottalk.usage v1
// owner: DOT|ASCEND
// command: ASCEND
// category: index
// status: supported
// noargs: mutate
// effect: configure
// mutates: order-state
// usage-access: ASCEND USAGE
// summary:
//   Set the active order/tag direction to ascending for the current work area.
//
// usage:
//   ASCEND
//   ASCEND USAGE
//
// notes:
//   ASCEND requires an active order except for ASCEND USAGE.
//   ASCEND with no arguments mutates order direction to ascending.
//   ASCEND does not mutate table records or rebuild indexes.
//
// risk:
//   mutates_order_state: yes
//   mutates_table_data: no
//   requires_active_order: yes except usage
//
// related:
//   DESCEND
//   SET ORDER
//   ORDER
//

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "cli/order_state.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>

namespace {
static std::string ascend_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string ascend_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_ascend_usage_request(const std::string& raw)
{
    std::string t = ascend_upper(ascend_trim(raw));
    if (t.rfind("ASCEND ", 0) == 0) {
        t = ascend_upper(ascend_trim(t.substr(7)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_ascend_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::AscendUsageText);
}
} // namespace

void cmd_ASCEND(xbase::DbArea& A, std::istringstream& in) {
    const std::string raw_args = in.str();
    if (is_ascend_usage_request(raw_args)) {
        print_ascend_usage();
        return;
    }

    if (!orderstate::hasOrder(A)) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::NoActiveIndex);
        return;
    }
    orderstate::setAscending(A, true);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::OrderAscendingSet);
}


/*#include "xbase.hpp"
#include "order_state.hpp"
#include <iostream>
#include <algorithm>
#include <cctype>
#include <string>
#include <sstream>

using namespace xbase;

void cmd_ASCEND(DbArea& area, std::istringstream& iss) {
    if (!order_state::hasOrder(area)) {
        std::cout << "No active order." << std::endl;
        return;
    }
    order_state::setAscending(area, true);
    std::cout << "Order set to ascending." << std::endl;
}

*/
