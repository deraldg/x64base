// src/cli/cmd_ERROR_TEST.cpp
// Self-test for the xBase_64 error subsystem.

// @dottalk.usage v1
// owner: DOT|ERROR_TEST
// command: ERROR_TEST
// category: diagnostics
// status: supported
// noargs: execute
// effect: test
// mutates: error-state
// usage-access: ERROR_TEST USAGE
// summary:
//   Run the xBase_64 error subsystem self-test and update last-error state on failure.
//
// usage:
//   ERROR_TEST
//   ERROR_TEST USAGE
//
// notes:
//   ERROR_TEST with no arguments runs the error subsystem self-test.
//   ERROR_TEST USAGE prints usage and does not run tests.
//   Passing tests clear the last error.
//   Failing tests set a canonical unknown error.
//   ERROR_TEST mutates diagnostic error state only, not table data.
//
// risk:
//   runs_self_test: yes
//   clears_error_state: on success
//   sets_error_state: on failure
//   mutates_table_data: no
//
// related:
//   ERROR_STATUS
//   ERROR_CLEAR
//

#include <iostream>
#include <sstream>
#include <iomanip>

#include <algorithm>
#include <cctype>
#include <string>
#include "xbase.hpp"
#include "xbase_error_codes.hpp"
#include "xbase_error_runtime.hpp"
#include "xbase_error_context.hpp"

using namespace xbase::error;

namespace
{

    std::string trim_usage(std::string s)
    {
        while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
        while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
        return s;
    }

    std::string upper_usage(std::string s)
    {
        std::transform(s.begin(), s.end(), s.begin(),
                       [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
        return s;
    }

    bool is_usage_request(const std::string& raw)
    {
        std::string t = upper_usage(trim_usage(raw));
        if (t.rfind("ERROR_TEST ", 0) == 0) {
            t = upper_usage(trim_usage(t.substr(11)));
        }
        return t == "USAGE" || t == "HELP" || t == "?";
    }

    void print_usage()
    {
        std::cout << "Usage:\n"
                  << "  ERROR_TEST\n"
                  << "  ERROR_TEST USAGE\n";
    }

    bool test_ok()
    {
        code c = ok();
        if (!c.ok()) return false;
        if (c.get_severity() != severity::success) return false;
        if (c.get_facility() != facility::general) return false;
        if (c.get_number() != 0) return false;
        return true;
    }

    bool test_packing()
    {
        code c = make_code(severity::error, facility::dbf64, 0x0042);
        if (c.get_severity() != severity::error) return false;
        if (c.get_facility() != facility::dbf64) return false;
        if (c.get_number() != 0x0042) return false;
        return true;
    }

    bool test_known_codes()
    {
        if (e_invalid_argument().get_facility() != facility::general) return false;
        if (e_dbf_header_invalid().get_facility() != facility::dbf64) return false;
        if (e_fpt_block_invalid().get_facility() != facility::fpt64) return false;
        if (e_security_policy_violation().get_facility() != facility::security) return false;
        if (e_cli_parse_error().get_facility() != facility::cli) return false;
        return true;
    }

    bool test_hresult_bridge()
    {
        code c = e_dbf_header_invalid();
        std::uint32_t hr = to_hresult(c);
        code back = from_hresult(hr);
        return back.value == c.value;
    }

    void print_result(const char* name, bool ok_flag)
    {
        std::cout << "  " << std::left << std::setw(20) << name
                  << (ok_flag ? "OK" : "FAIL") << "\n";
    }
}

void cmd_ERROR_TEST(xbase::DbArea& A, std::istringstream& in)
{
    (void)A;
    (void)in;

    std::cout << "ERROR subsystem self-test:\n";

    bool ok1 = test_ok();
    bool ok2 = test_packing();
    bool ok3 = test_known_codes();
    bool ok4 = test_hresult_bridge();

    print_result("ok()", ok1);
    print_result("packing", ok2);
    print_result("known codes", ok3);
    print_result("HRESULT bridge", ok4);

    bool all_ok = ok1 && ok2 && ok3 && ok4;

    if (all_ok) {
        clear_last_error();
        std::cout << "All tests passed.\n";
    } else {
        // Set a canonical error to indicate failure of the test suite.
        set_last_error(e_unknown());
        std::cout << "One or more tests FAILED.\n";
    }
}