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
//   SECURITY LOGIN <DEVELOPER|TEACHER|STUDENT> [AS <worker>]
//   SECURITY WHOAMI
//   SECURITY ASSIGNMENTS
//   SECURITY LOGOUT
//
// notes:
//   SECURITY with no arguments prints usage.
//   SHOW displays the active policy and profile roots.
//   SELFTEST runs built-in security tests.
//   RUNTIME describes runtime enforcement rules.
//   LOGIN establishes a role/session identity for the current shell session.
//   WHOAMI reports the active shell-session role identity.
//   ASSIGNMENTS reports the assignment lane bound to the active role.
//   LOGOUT clears the active shell-session role identity.
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
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>

#include "common/path_state.hpp"
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
    namespace fs = std::filesystem;

    struct session_identity
    {
        bool logged_in = false;
        std::string role;
        std::string worker;
    };

    session_identity& active_identity()
    {
        static session_identity id;
        return id;
    }

    static void print_security_usage()
    {
        std::cout
            << "Usage:\n"
            << "  SECURITY USAGE\n"
            << "  SECURITY SHOW\n"
            << "  SECURITY SELFTEST\n"
            << "  SECURITY RUNTIME\n"
            << "  SECURITY LOGIN <DEVELOPER|TEACHER|STUDENT> [AS <worker>]\n"
            << "  SECURITY WHOAMI\n"
            << "  SECURITY ASSIGNMENTS\n"
            << "  SECURITY LOGOUT\n";
    }

    static std::string detect_profile_name()
    {
        return "default";
    }

    static std::string trim_copy(std::string s)
    {
        while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front())))
            s.erase(s.begin());
        while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back())))
            s.pop_back();
        return s;
    }

    static std::string up_copy(std::string s)
    {
        for (auto& c : s)
            c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        return s;
    }

    static bool is_supported_role(const std::string& role)
    {
        const std::string u = up_copy(role);
        return u == "DEVELOPER" || u == "TEACHER" || u == "STUDENT";
    }

    static fs::path assignments_root_path()
    {
        const fs::path data_root = dottalk::paths::state().data_root;
        return data_root.parent_path().parent_path() / "docs" / "assignments";
    }

    static fs::path role_summary_path(const std::string& role)
    {
        const std::string u = up_copy(role);
        if (u == "DEVELOPER")
            return assignments_root_path() / "DEVELOPER_ASSIGNMENTS.md";
        if (u == "TEACHER")
            return assignments_root_path() / "TEACHER_ASSIGNMENTS.md";
        if (u == "STUDENT")
            return assignments_root_path() / "STUDENT_ASSIGNMENTS.md";
        return assignments_root_path() / "README.md";
    }

    static void print_role_assignments(const session_identity& id)
    {
        if (!id.logged_in)
        {
            std::cout << "SECURITY ASSIGNMENTS: no active role session.\n";
            return;
        }

        const fs::path summary = role_summary_path(id.role);
        std::cout << "Role   : " << id.role << "\n";
        std::cout << "Worker : " << id.worker << "\n";
        std::cout << "Summary: " << summary.string() << "\n";

        const std::string role = up_copy(id.role);
        if (role == "DEVELOPER")
        {
            std::cout << "Open assignments:\n";
            std::cout << "  1. MCC trinity mutation follow-up\n";
            std::cout << "     - VFP PACK header-warning canary (dev-only)\n";
            std::cout << "     - regression launcher integration\n";
            std::cout << "Packet : "
                      << (assignments_root_path() / "ASSIGNMENT_MCC_TRINITY_MUTATION_FOLLOWUP_2026-07-06.md").string()
                      << "\n";
            return;
        }

        std::cout << "Open assignments:\n";
        std::cout << "  none yet\n";
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
            << "  • Host shell execution forbidden unless explicitly enabled\n"
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

    if (sub == "LOGIN")
    {
        std::string role;
        if (!(in >> role))
        {
            std::cout << "SECURITY LOGIN: missing role\n";
            print_security_usage();
            return;
        }

        role = up_copy(role);
        if (!is_supported_role(role))
        {
            std::cout << "SECURITY LOGIN: unsupported role: " << role << "\n";
            std::cout << "Supported roles: DEVELOPER, TEACHER, STUDENT\n";
            return;
        }

        std::string rest;
        std::getline(in, rest);
        rest = trim_copy(rest);
        if (up_copy(rest).rfind("AS ", 0) == 0)
            rest = trim_copy(rest.substr(3));
        const std::string worker = rest.empty() ? "Derald" : rest;

        auto& id = active_identity();
        id.logged_in = true;
        id.role = role;
        id.worker = worker;

        std::cout << "SECURITY LOGIN: role=" << id.role
                  << " worker=" << id.worker << "\n";
        std::cout << "Role summary: " << role_summary_path(id.role).string() << "\n";
        return;
    }

    if (sub == "WHOAMI")
    {
        const auto& id = active_identity();
        if (!id.logged_in)
        {
            std::cout << "SECURITY WHOAMI: not logged in\n";
            return;
        }

        std::cout << "role=" << id.role << "\n";
        std::cout << "worker=" << id.worker << "\n";
        std::cout << "summary=" << role_summary_path(id.role).string() << "\n";
        return;
    }

    if (sub == "ASSIGNMENTS")
    {
        print_role_assignments(active_identity());
        return;
    }

    if (sub == "LOGOUT")
    {
        auto& id = active_identity();
        if (!id.logged_in)
        {
            std::cout << "SECURITY LOGOUT: no active role session.\n";
            return;
        }

        std::cout << "SECURITY LOGOUT: role=" << id.role
                  << " worker=" << id.worker << "\n";
        id = session_identity{};
        return;
    }

    print_security_usage();
}
