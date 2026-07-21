// src/cli/expr/fn_custom.cpp
//
// Runtime custom-function registry (RUNTIME_DEF_FAMILY lane).
// A live, session-scoped map of name -> CustomFnEntry, consulted by the expression
// evaluators (value_eval.cpp, rhs_eval.cpp) as a fourth function group after the three
// static builtin tables. See include/cli/expr/fn_custom.hpp.

#include "cli/expr/fn_custom.hpp"

#include "cli/expr/fn_string.hpp"
#include "cli/expr/fn_date.hpp"
#include "cli/expr/fn_numeric.hpp"

#include <cctype>
#include <map>

namespace dottalk::expr {

namespace {

std::string to_upper(std::string s)
{
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

// Live registry singleton. std::map keeps names sorted (for custom_fn_names) and keeps
// element pointers/references stable across insert/erase of other keys.
std::map<std::string, CustomFnEntry>& store()
{
    static std::map<std::string, CustomFnEntry> s;
    return s;
}

} // namespace

bool register_custom_fn(const std::string& name,
                        int minArgs,
                        int maxArgs,
                        std::function<std::string(const std::vector<std::string>&)> eval)
{
    const std::string key = to_upper(name);
    if (key.empty() || !eval) return false;
    if (maxArgs < minArgs) maxArgs = minArgs;

    CustomFnEntry entry;
    entry.name = key;
    entry.minArgs = minArgs;
    entry.maxArgs = maxArgs;
    entry.eval = std::move(eval);

    store()[key] = std::move(entry);
    return true;
}

bool unregister_custom_fn(const std::string& name)
{
    return store().erase(to_upper(name)) != 0;
}

const CustomFnEntry* find_custom_fn(const std::string& nameUpper)
{
    auto& s = store();
    const auto it = s.find(to_upper(nameUpper));
    return it == s.end() ? nullptr : &it->second;
}

std::vector<std::string> custom_fn_names()
{
    std::vector<std::string> names;
    for (const auto& kv : store()) names.push_back(kv.first);
    return names;
}

bool is_builtin_fn(const std::string& nameUpper)
{
    const std::string key = to_upper(nameUpper);

    const auto* s = string_fn_specs();
    for (std::size_t i = 0; i < string_fn_specs_count(); ++i) {
        if (key == s[i].name) return true;
    }
    const auto* d = date_fn_specs();
    for (std::size_t i = 0; i < date_fn_specs_count(); ++i) {
        if (key == d[i].name) return true;
    }
    const auto* n = numeric_fn_specs();
    for (std::size_t i = 0; i < numeric_fn_specs_count(); ++i) {
        if (key == n[i].name) return true;
    }
    return false;
}

} // namespace dottalk::expr
