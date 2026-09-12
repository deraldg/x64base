// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// cmd_order.cpp ? consolidated ASCEND and DESCEND commands
// Safe to build even if indexing isn't wired yet.

// NO USAGE CONTRACT HERE, DELIBERATELY. Removed 2026-07-27 (AIF-067).
//
// (The marker token is spelled out nowhere in this comment on purpose: the
// CONTRACT_QA/MENTION_ONLY check counts files that name the marker without
// carrying a parseable contract, and an explanation of an absence should not
// register as a malformed presence. Writing the token here made this file a
// finding within minutes of removing its real one.)
//
// This file OWNS NO COMMAND. It declares cmd_ASCEND and cmd_DESCEND (below);
// both are DEFINED in src/cli/cmd_ascend.cpp and registered from
// shell_commands.cpp. A usage contract means "I am this command", and this
// file is not one.
//
// The block that was here said so itself -- "This file is not the SET ORDER or
// ORDER command owner" -- while occupying the slot that asserts ownership, and
// named its identity `ASCEND/DESCEND`, which is not an identity at all. It was
// the largest remaining CONTRACT_QA/INVALID_IDENTITY finding.
//
// Its identity is carried by @dottalk.file above (layer: helper). The rule
// settled with member.derald, 2026-07-27: a file that owns no command gets
// @dottalk.file only.
//
// Consolidated order helper/prototype translation unit for ASCEND/DESCEND.
// Intentionally low-behaviour in this source drop; keep active-order mutation
// in the real command handlers / order_state layer. Does not mutate table data.

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
