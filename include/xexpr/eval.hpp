#pragma once

#include <string>
#include <string_view>

#include "xexpr/context.hpp"
#include "xexpr/value.hpp"

namespace xexpr {

Value evaluate_expression(std::string_view expression,
                          const EvalContext& ctx = {});

Value evaluate_expression(std::string_view expression,
                          xbase::DbArea* area);

bool evaluate_predicate(std::string_view expression,
                        const EvalContext& ctx,
                        bool& out,
                        std::string* err_out = nullptr);

} // namespace xexpr
