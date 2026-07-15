#include "xexpr/eval.hpp"
#include "xexpr/compiled_expression.hpp"

#include <string>

#include "cli/expr/rhs_eval.hpp"
#include "cli/expr/value_eval.hpp"
#include "xbase.hpp"

namespace {

static xexpr::Value from_legacy_eval_value(const dottalk::expr::EvalValue& ev,
                                           const std::string& err) {
    switch (ev.kind) {
        case dottalk::expr::EvalValue::K_Bool:
            return xexpr::Value::logical(ev.tf);

        case dottalk::expr::EvalValue::K_Number:
            return xexpr::Value::number(ev.number);

        case dottalk::expr::EvalValue::K_String:
            return xexpr::Value::string(ev.text);

        case dottalk::expr::EvalValue::K_Date:
            return xexpr::Value::date(ev.date8);

        case dottalk::expr::EvalValue::K_None:
        default:
            if (!err.empty()) return xexpr::Value::error(err);
            return xexpr::Value::none();
    }
}

static std::string to_string_copy(std::string_view sv) {
    return std::string(sv.data(), sv.size());
}

} // namespace

namespace xexpr {

Value evaluate_expression(std::string_view expression, const EvalContext& ctx) {
    std::string err;
    const auto ev = dottalk::expr::eval_rhs(ctx.area, to_string_copy(expression), &err);
    return from_legacy_eval_value(ev, err);
}

Value evaluate_expression(std::string_view expression, xbase::DbArea* area) {
    EvalContext ctx;
    ctx.area = area;
    return evaluate_expression(expression, ctx);
}

bool evaluate_predicate(std::string_view expression,
                        const EvalContext& ctx,
                        bool& out,
                        std::string* err_out) {
    out = false;

    if (ctx.area && ctx.area->isOpen()) {
        std::string err;
        if (dottalk::expr::eval_bool(*ctx.area, to_string_copy(expression), out, &err)) {
            if (err_out) err_out->clear();
            return true;
        }
        if (err_out) *err_out = err.empty() ? "predicate evaluation failed" : err;
        return false;
    }

    const Value v = evaluate_expression(expression, ctx);
    if (v.is_error()) {
        if (err_out) *err_out = v.error_message();
        return false;
    }

    out = v.truthy();
    if (err_out) err_out->clear();
    return true;
}

Value CompiledExpression::evaluate(const EvalContext& ctx) const {
    return evaluate_expression(source_, ctx);
}

bool CompiledExpression::evaluate_predicate(const EvalContext& ctx,
                                            bool& out,
                                            std::string* err_out) const {
    return xexpr::evaluate_predicate(source_, ctx, out, err_out);
}

CompileResult compile(std::string_view expression) {
    CompileResult out;
    out.ok = true;
    out.expression = CompiledExpression(to_string_copy(expression));
    return out;
}

} // namespace xexpr
