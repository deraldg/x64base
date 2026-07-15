#pragma once

#include <string>

#include "xbase.hpp"

namespace predicates {

int field_index_ci(const xbase::DbArea& a, const std::string& name);

// Backward-compatible predicate facade used by older command paths.
// Accepts both simple field comparisons:
//
//   predicates::eval(A, "LNAME", "=", "WHITE")
//
// and expression-side comparisons when the caller passes expression text:
//
//   predicates::eval(A, "SOUNDEX(LNAME)", "=", "SOUNDEX(\"WHITE\")")
//
// The implementation routes the final expression through the same expression
// evaluator used by CALC / value_eval so FOR predicates can use registered
// functions such as SOUNDEX(), UPPER(), LEFT(), DATE(), etc.
bool eval(const xbase::DbArea& a,
          const std::string& lhs,
          const std::string& op,
          const std::string& rhs);

// Direct full-expression predicate evaluation for newer call sites.
// Example:
//   predicates::eval_expr(A, "SOUNDEX(LNAME) = SOUNDEX(\"WHITE\")")
bool eval_expr(const xbase::DbArea& a,
               const std::string& expr_text,
               std::string* err_out = nullptr);

} // namespace predicates
