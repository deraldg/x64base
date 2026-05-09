// @dottalk.usage v1
// owner: DOT|SECURITY
// command: SECURITY
// category: diagnostics
// status: supported
// noargs: usage
// effect: mixed
// mutates: none
// usage-access: SECURITY USAGE
// summary:
//   Display x64Base security policy/runtime diagnostics or run built-in security
//   self-tests.
//
// usage:
//   SECURITY USAGE
//   SECURITY SHOW
//   SECURITY SELFTEST
//   SECURITY RUNTIME
//
// notes:
//   SECURITY with no arguments prints usage.
//   SHOW displays the active policy and profile roots.
//   SELFTEST runs built-in security tests.
//   RUNTIME describes runtime enforcement rules.
//   SECURITY does not mutate table data.
//
// risk:
//   runs_self_tests: SECURITY SELFTEST
//   mutates_table_data: no
//
// related:
//   ERROR_TEST
//   VALIDATE
//

#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "xbase_security.hpp"
#include "xbase_security_policy.hpp"
#include "xbase_security_runtime.hpp"
#include "xbase_security_tests.hpp"

using namespace xbase::security;
using namespace xbase::security::policy;
using namespace xbase::security::runtime;

namespace
{
        static void print_security_usage()
    {
        std::cout
            << "Usage:\n"
            << "  SECURITY USAGE\n"
            << "  SECURITY SHOW\n"
            << "  SECURITY SELFTEST\n"
            << "  SECURITY RUNTIME\n";
    }

static std::string detect_profile_name()
    {
        return "default";
    }
}

void cmd_SECURITY(xbase::DbArea& A, std::istringstream& in)
{
    (void)A;

    std::string sub;
    if (!(in >> sub))
        sub = "USAGE";

    for (auto& c : sub)
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));


    if (sub == "USAGE" || sub == "HELP" || sub == "?")
    {
        print_security_usage();
        return;
    }

    if (sub == "SHOW")
    {
        config policy = strict_profile();
        context ctx(policy, detect_profile_name());

        std::cout << policy.describe();
        std::cout << "elevated: " << (ctx.is_elevated ? "yes" : "no") << "\n";
        std::cout << "profile: " << ctx.profile_name << "\n";
        std::cout << "app user root: " << ctx.app_user_root << "\n";
        std::cout << "app public root: " << ctx.app_public_root << "\n";
        std::cout << "app default root: " << ctx.app_default_root << "\n";
        std::cout << "os user root: " << ctx.os_user_root << "\n";
        std::cout << "os public root: " << ctx.os_public_root << "\n";
        std::cout << "os default root: " << ctx.os_default_root << "\n";
        return;
    }

    if (sub == "SELFTEST")
    {
        int failures = xbase::tests::run_xbase_security_tests();

        if (failures == 0)
            std::cout << "All xBase_64 security tests passed.\n";
        else
            std::cout << failures << " security tests failed.\n";

        return;
    }

    if (sub == "RUNTIME")
    {
        config policy = strict_profile();
        context ctx(policy, detect_profile_name());

        std::cout
            << "x64Base Runtime Security Enforcement:\n"
            << "  • Path canonicalization (no traversal)\n"
            << "  • Header validation required\n"
            << "  • Atomic writes required for structural updates\n"
            << "  • Elevated writes forbidden\n"
            << "  • Plaintext secrets forbidden\n"
            << "  • App-local profile roots supported\n"
            << "  • OS-local profile roots supported\n"
            << "  • Policy level: " << to_string(policy.security_level) << "\n"
            << "  • Active profile: " << ctx.profile_name << "\n"
            << "  • App user root: " << ctx.app_user_root << "\n"
            << "  • App public root: " << ctx.app_public_root << "\n"
            << "  • App default root: " << ctx.app_default_root << "\n"
            << "  • OS user root: " << ctx.os_user_root << "\n"
            << "  • OS public root: " << ctx.os_public_root << "\n"
            << "  • OS default root: " << ctx.os_default_root << "\n";

        return;
    }

    print_security_usage();
}