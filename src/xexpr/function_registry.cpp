#include "xexpr/function.hpp"

namespace xexpr {

const FunctionInfo* find_function(const std::string& /*name*/) {
    // Phase 1 intentionally does not duplicate the existing function catalog.
    // The executable evaluator still reaches the legacy dottalk::expr functions.
    return nullptr;
}

std::vector<FunctionInfo> list_functions() {
    // Phase 1 placeholder. Later this should bridge/move function_catalog.cpp.
    return {};
}

} // namespace xexpr
