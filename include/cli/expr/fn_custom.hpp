#pragma once
// include/cli/expr/fn_custom.hpp
//
// DotTalk++ runtime custom-function seam (RUNTIME_DEF_FAMILY lane).
//
// Sibling to fn_string / fn_date / fn_numeric, but with two key differences:
//   - it is a LIVE, runtime-mutable registry (not a static BuiltinFnSpec[] table);
//   - its entry carries a real body via std::function (not a raw function pointer),
//     so a runtime-defined body (DEFFN / custom field-type accessor) can be captured.
//
// The expression evaluators (value_eval.cpp, rhs_eval.cpp) consult this registry as a
// fourth group, after the three static builtin tables. Registering a name here makes it
// resolvable inside ? / CALC / WHERE immediately, with no rebuild.

#include <functional>
#include <string>
#include <vector>

namespace dottalk::expr {

struct CustomFnEntry {
    std::string name;      // normalized UPPER
    int minArgs = 0;
    int maxArgs = 0;
    std::function<std::string(const std::vector<std::string>& argv)> eval;
};

// Register (or redefine) a runtime custom function. Name is normalized to UPPER.
// Returns false only if the name is empty or eval is null.
bool register_custom_fn(const std::string& name,
                        int minArgs,
                        int maxArgs,
                        std::function<std::string(const std::vector<std::string>&)> eval);

// Remove a runtime custom function. Returns true if one was erased.
bool unregister_custom_fn(const std::string& name);

// Lookup by (case-insensitive) name. Returns nullptr if not registered.
// The pointer is valid until the entry is unregistered/overwritten.
const CustomFnEntry* find_custom_fn(const std::string& nameUpper);

// Names of all registered custom functions (for DEFFN LIST), sorted.
std::vector<std::string> custom_fn_names();

// True if the name collides with a compiled-in builtin (string/date/numeric).
// Used by DEFFN to refuse shadowing a real builtin function.
bool is_builtin_fn(const std::string& nameUpper);

} // namespace dottalk::expr
