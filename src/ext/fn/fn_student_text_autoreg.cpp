// src/ext/fn/fn_student_text_autoreg.cpp
//
// Student function extension (self-registering)
// Uses the SAME contract as fn_string_autoreg.cpp

#include "cli/expr/fn_string.hpp"
#include "cli/command_registry.hpp"
#include "../ext_policy.hpp"

#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

// ------------------------------------------------------------
// student functions (MUST match BuiltinFnEval signature)
// ------------------------------------------------------------

static std::string fn_STU_UPPER(const std::vector<std::string>& argv)
{
    if (argv.size() != 1)
        return "STU_UPPER: expects 1 argument";

    std::string s = argv[0];
    for (auto& c : s)
        c = (char)std::toupper((unsigned char)c);

    return s;
}

static std::string fn_STU_REPEAT(const std::vector<std::string>& argv)
{
    if (argv.size() != 2)
        return "STU_REPEAT: expects 2 arguments";

    const std::string& text = argv[0];
    int count = 0;

    try {
        count = std::stoi(argv[1]);
    } catch (...) {
        return "STU_REPEAT: invalid count";
    }

    if (count < 0)
        return "STU_REPEAT: count must be >= 0";

    std::string out;
    for (int i = 0; i < count; ++i)
        out += text;

    return out;
}

// ------------------------------------------------------------
// same registration helper pattern as fn_string_autoreg.cpp
// ------------------------------------------------------------

static void register_builtin_fn(const dottalk::expr::BuiltinFnSpec& spec)
{
    dli::registry().add(spec.name,
        [&spec](xbase::DbArea& A, std::istringstream& in)
    {
        // Student text functions deliberately do not resolve DBF field
        // values through the active work area. Keep the registry-compatible
        // signature, but mark the table context as intentionally unused.
        (void)A;

        std::string tail;
        std::getline(in, tail);

        // strip parentheses if present
        auto l = tail.find('(');
        auto r = tail.rfind(')');
        if (l != std::string::npos && r != std::string::npos && r > l)
            tail = tail.substr(l+1, r-l-1);

        // simple comma split (keep it minimal for student example)
        std::vector<std::string> argv;
        std::string cur;
        std::istringstream ss(tail);

        while (std::getline(ss, cur, ',')) {
            // trim
            size_t i = 0;
            while (i < cur.size() && std::isspace((unsigned char)cur[i])) ++i;
            size_t j = cur.size();
            while (j > i && std::isspace((unsigned char)cur[j-1])) --j;
            argv.push_back(cur.substr(i, j-i));
        }

        if ((int)argv.size() < spec.minArgs ||
            (int)argv.size() > spec.maxArgs)
        {
            std::cout << spec.name << " expects "
                      << spec.minArgs;
            if (spec.minArgs != spec.maxArgs)
                std::cout << ".." << spec.maxArgs;
            std::cout << " argument(s).\n";
            return;
        }

        try {
            std::cout << spec.eval(argv) << "\n";
        }
        catch (...) {
            std::cout << spec.name << ": evaluation error.\n";
        }
    });
}

// ------------------------------------------------------------
// self-registration
// ------------------------------------------------------------

struct AutoRegister {
    AutoRegister()
    {
        register_builtin_fn({
            "STU_UPPER",
            1, 1,
            &fn_STU_UPPER
        });

        register_builtin_fn({
            "STU_REPEAT",
            2, 2,
            &fn_STU_REPEAT
        });
    }
};

static AutoRegister g_autoreg;

} // namespace