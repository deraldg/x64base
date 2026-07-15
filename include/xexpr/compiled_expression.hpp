#pragma once

#include <string>
#include <utility>

#include "xexpr/context.hpp"
#include "xexpr/diagnostic.hpp"
#include "xexpr/value.hpp"

namespace xexpr {

class CompiledExpression {
public:
    CompiledExpression() = default;
    explicit CompiledExpression(std::string source) : source_(std::move(source)) {}

    const std::string& source() const noexcept { return source_; }

    Value evaluate(const EvalContext& ctx = {}) const;
    bool evaluate_predicate(const EvalContext& ctx, bool& out, std::string* err_out = nullptr) const;

private:
    std::string source_;
};

struct CompileResult {
    bool ok = false;
    CompiledExpression expression{};
    Diagnostic diagnostic{};

    explicit operator bool() const noexcept { return ok; }
};

CompileResult compile(std::string_view expression);

} // namespace xexpr
