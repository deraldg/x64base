#pragma once

namespace xbase { class DbArea; }

namespace xexpr {

struct EvalOptions {
    bool foxpro_compat = true;
    bool case_sensitive = false;
    bool allow_field_names = true;
    bool allow_functions = true;
};

struct EvalContext {
    // Non-const for Phase 1 because the existing dottalk::expr evaluator
    // uses DbArea through mutable record/memo glue. We can tighten this later.
    xbase::DbArea* area = nullptr;
    EvalOptions options{};
};

} // namespace xexpr
