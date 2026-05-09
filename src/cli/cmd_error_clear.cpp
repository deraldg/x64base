// src/cli/cmd_ERROR_CLEAR.cpp
// Clear the last xBase_64 error and report success.

// @dottalk.usage v1
// owner: DOT|ERROR_CLEAR
// command: ERROR_CLEAR
// category: diagnostics
// status: supported
// noargs: mutate
// effect: clear
// mutates: error-state
// usage-access: ERROR_CLEAR USAGE
// summary:
//   Clear the last xBase_64 error context.
//
// usage:
//   ERROR_CLEAR
//   ERROR_CLEAR USAGE
//
// notes:
//   ERROR_CLEAR with no arguments clears the last error.
//   ERROR_CLEAR USAGE prints usage and does not clear the error state.
//   ERROR_CLEAR mutates diagnostic error state only, not table data.
//
// risk:
//   clears_error_state: yes
//   mutates_table_data: no
//
// related:
//   ERROR_STATUS
//   ERROR_TEST
//

#include <iostream>
#include <sstream>

#include "xbase.hpp"
#include "xbase_error_codes.hpp"
#include "xbase_error_context.hpp"

using namespace xbase::error;

void cmd_ERROR_CLEAR(xbase::DbArea& A, std::istringstream& in)
{
    (void)A;
    (void)in;

    clear_last_error();

    std::cout << "Last error cleared.\n";
}