#pragma once

#include "xbase.hpp"
#include "cli/order_iterator.hpp"
#include "cli/smartlist_query.hpp"

namespace cli::listmsg {

const char* backend_name(const cli::OrderIterSpec& spec);

void print_order_banner(const cli::OrderIterSpec& spec);

void print_cursor_line(xbase::DbArea& a, const char* reason);

void print_list_summary(xbase::DbArea& a,
                        int printed,
                        bool all,
                        int limit,
                        const cli::OrderIterSpec& spec,
                        const cli::smartlist::QuerySpec& qspec);

void print_browser_summary(xbase::DbArea& a,
                           long total,
                           const cli::OrderIterSpec& spec,
                           const cli::smartlist::QuerySpec& qspec,
                           const char* reason);

} // namespace cli::listmsg