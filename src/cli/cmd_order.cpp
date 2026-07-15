// cmd_order.cpp ? consolidated ASCEND and DESCEND commands
// Safe to build even if indexing isn't wired yet.

// @dottalk.usage v1
// owner: DOT|ORDER_IMPL
// command: ASCEND/DESCEND
// category: order-helper
// status: implementation-helper
// noargs: n/a
// effect: order-support
// mutates: none-here
// usage-access: owned-by ASCEND/DESCEND command handlers
// summary:
//   Consolidated order helper/prototype translation unit for ASCEND/DESCEND.
//
// usage:
//   This file is not the SET ORDER or ORDER command owner.
//   User-visible ASCEND/DESCEND usage is owned by their command handlers.
//
// notes:
//   The file is intentionally low-behavior in this source drop.
//   Keep active-order mutation in the actual command handlers/order_state layer.
//
// risk:
//   mutates_table_data: no
//

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"

#include <sstream>
#include <iostream>
#include <string>

#include "cli/order_state.hpp"
#include "xbase.hpp"
#include <sstream>
#include <iostream>

// cmd_order.cpp  (top of file)
void cmd_ASCEND(xbase::DbArea&, std::istringstream&);
void cmd_DESCEND(xbase::DbArea&, std::istringstream&);



using xbase::DbArea;

// Internal helper: prints standard "no table" message and returns true if handled
static inline bool ensure_table_open(DbArea& A) {
    if (!A.isOpen()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::NoOpenTable);
        return true;
    }
    return false;
}
