#pragma once

#include <string>

#include "xexpr/array_value.hpp"   // dottalk::array::Value (arrays survive here)

namespace xbase { class DbArea; }

namespace dottalk::expr {

struct EvalValue;

// Canonical RHS evaluator entry point.
// areaOrNull == nullptr => scalar/no-table mode
// areaOrNull != nullptr => field-aware mode
EvalValue eval_rhs(xbase::DbArea* areaOrNull,
                   const std::string& exprText,
                   std::string* errOut = nullptr);

// Array-preserving RHS evaluator (AIF-038). Same expression grammar as eval_rhs,
// but returns the array-lane Value so an array result keeps its ArrayRef instead of
// being flattened to the "{array:N}" placeholder that EvalValue forces. Used by the
// VAR command so `VAR a = {1,2,3}` stores a real array, not a string. Returns false
// (and sets *errOut) on evaluation failure.
bool eval_rhs_avalue(xbase::DbArea* areaOrNull,
                     const std::string& exprText,
                     dottalk::array::Value& out,
                     std::string* errOut = nullptr);

} // namespace dottalk::expr
