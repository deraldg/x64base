// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "cli/expr/ast.hpp"
#include "cli/expr/eval.hpp"
#include "cli/expr/text_compare.hpp"
#include "predicate_eval.hpp"
#include "cli/expr/fn_string.hpp"
#include "cli/expr/fn_date.hpp"
#include "cli/expr/fn_numeric.hpp"
#include "cli/expr/fn_custom.hpp"

#include <cctype>
#include <optional>
#include <string>
#include <stdexcept>
#include <vector>

using namespace dottalk::expr;

bool FieldRef::eval(const RecordView& rv) const {
  if (!rv.get_field_str) return false;
  auto s = rv.get_field_str(name);
  for (char ch: s) {
    if (!std::isspace(static_cast<unsigned char>(ch))) return true;
  }
  return false;
}

std::string FieldRef::evalString(const RecordView& rv) const {
  if (!rv.get_field_str) throw std::runtime_error("field accessor unavailable");
  return rv.get_field_str(name);
}

namespace {

std::string upper_name(std::string s) {
  for (char& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
  return s;
}

const BuiltinFnSpec* find_builtin(const std::string& name) {
  const auto find = [&](const BuiltinFnSpec* specs, std::size_t count) -> const BuiltinFnSpec* {
    for (std::size_t i = 0; i < count; ++i) if (name == specs[i].name) return &specs[i];
    return nullptr;
  };
  if (const auto* p = find(string_fn_specs(), string_fn_specs_count())) return p;
  if (const auto* p = find(date_fn_specs(), date_fn_specs_count())) return p;
  return find(numeric_fn_specs(), numeric_fn_specs_count());
}

bool logical_text(const std::string& raw, bool& out) {
  std::string s = upper_name(raw);
  while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
  while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
  if (s == ".T." || s == "T" || s == "TRUE" || s == "1") { out = true; return true; }
  if (s == ".F." || s == "F" || s == "FALSE" || s == "0" || s.empty()) { out = false; return true; }
  return false;
}

} // namespace

std::string FunctionCall::evalString(const RecordView& rv) const {
  const std::string fn = upper_name(name);
  if (fn == "DELETED" || fn == "RECNO" || fn == "RECCOUNT") {
    if (!args.empty()) throw std::runtime_error(fn + "() takes no arguments");
    if (!rv.get_field_str) throw std::runtime_error(fn + "() is unavailable");
    return rv.get_field_str(fn);
  }

  std::vector<std::string> argv;
  argv.reserve(args.size());
  for (const auto& arg : args) argv.push_back(arg->evalString(rv));

  if (const auto* spec = find_builtin(fn)) {
    const int argc = static_cast<int>(argv.size());
    if (argc < spec->minArgs || argc > spec->maxArgs) {
      throw std::runtime_error(fn + "() received the wrong number of arguments");
    }
    return spec->eval(argv);
  }
  if (const auto* custom = find_custom_fn(fn)) {
    const int argc = static_cast<int>(argv.size());
    if (argc < custom->minArgs || argc > custom->maxArgs) {
      throw std::runtime_error(fn + "() received the wrong number of arguments");
    }
    return custom->eval(argv);
  }
  throw std::runtime_error("unknown function '" + name + "'");
}

bool FunctionCall::eval(const RecordView& rv) const {
  const std::string result = evalString(rv);
  bool logical = false;
  if (logical_text(result, logical)) return logical;
  if (const auto number = to_number(result)) return *number != 0.0;
  return !result.empty();
}

static std::string value_as_string(const RecordView& rv, const Expr* e) {
  if (auto fr = dynamic_cast<const FieldRef*>(e)) {
    if (rv.get_field_str) return rv.get_field_str(fr->name);
    return {};
  }
  if (auto ls = dynamic_cast<const LitString*>(e)) return ls->v;
  if (auto ln = dynamic_cast<const LitNumber*>(e)) return std::to_string(ln->v);
  if (auto lb = dynamic_cast<const LitBool*>(e)) return lb->v ? ".T." : ".F.";
  return e->evalString(rv);
}

static std::optional<double> value_as_number(const RecordView& rv, const Expr* e) {
  if (auto ln = dynamic_cast<const LitNumber*>(e)) return ln->v;
  if (auto lb = dynamic_cast<const LitBool*>(e)) return lb->v ? 1.0 : 0.0;
  if (auto fr = dynamic_cast<const FieldRef*>(e)) {
    if (rv.get_field_num) return rv.get_field_num(fr->name);
    if (rv.get_field_str) return to_number(rv.get_field_str(fr->name));
    return std::nullopt;
  }
  if (auto ls = dynamic_cast<const LitString*>(e)) return to_number(ls->v);
  if (auto ar = dynamic_cast<const Arith*>(e))  return ar->evalNumber(rv);
  if (auto fn = dynamic_cast<const FunctionCall*>(e)) return to_number(fn->evalString(rv));
  return std::nullopt;
}

static std::optional<char> field_type(const RecordView& rv, const Expr* e) {
  const auto* fr = dynamic_cast<const FieldRef*>(e);
  if (!fr || !rv.get_field_type) return std::nullopt;
  return rv.get_field_type(fr->name);
}

bool Cmp::eval(const RecordView& rv) const {
  // A numeric/date/logical field compared with a non-coercible string is a
  // type error, not a confident FALSE. This closes the shared wrong-answer
  // class recorded by AIF-074 before SQLsel adopts this evaluator.
  const auto lt = field_type(rv, lhs.get());
  const auto rt = field_type(rv, rhs.get());
  const auto incompatible_literal = [](std::optional<char> type, const Expr* other) {
    const auto* text = dynamic_cast<const LitString*>(other);
    if (!type || !text) return false;
    const char t = static_cast<char>(std::toupper(static_cast<unsigned char>(*type)));
    return t == 'N' && !to_number(text->v).has_value();
  };
  if (incompatible_literal(lt, rhs.get()) || incompatible_literal(rt, lhs.get())) {
    throw std::runtime_error("incompatible field/literal types in comparison");
  }

  auto ln = value_as_number(rv, lhs.get());
  auto rn = value_as_number(rv, rhs.get());
  if (ln && rn) {
    double a = *ln, b = *rn;
    switch (op) {
      case CmpOp::EQ: return a == b;
      case CmpOp::NE: return a != b;
      case CmpOp::LT: return a <  b;
      case CmpOp::LE: return a <= b;
      case CmpOp::GT: return a >  b;
      case CmpOp::GE: return a >= b;
    }
  }

  std::string as = value_as_string(rv, lhs.get());
  std::string bs = value_as_string(rv, rhs.get());

  const bool case_on = predx::get_case_sensitive();
  const auto match = dottalk::expr::compare_text_values(as, bs);

  switch (op) {
    case CmpOp::EQ:
      return dottalk::expr::text_match_is_true(match, case_on);

    case CmpOp::NE:
      return !dottalk::expr::text_match_is_true(match, case_on);

    case CmpOp::LT:
    case CmpOp::LE:
    case CmpOp::GT:
    case CmpOp::GE: {
      const std::string lhs_exact = dottalk::expr::normalize_text_exact(as);
      const std::string rhs_exact = dottalk::expr::normalize_text_exact(bs);

      if (case_on) {
        if (op == CmpOp::LT) return lhs_exact <  rhs_exact;
        if (op == CmpOp::LE) return lhs_exact <= rhs_exact;
        if (op == CmpOp::GT) return lhs_exact >  rhs_exact;
        if (op == CmpOp::GE) return lhs_exact >= rhs_exact;
      } else {
        const std::string lhs_fold = dottalk::expr::normalize_text_folded(as);
        const std::string rhs_fold = dottalk::expr::normalize_text_folded(bs);

        if (op == CmpOp::LT) return lhs_fold <  rhs_fold;
        if (op == CmpOp::LE) return lhs_fold <= rhs_fold;
        if (op == CmpOp::GT) return lhs_fold >  rhs_fold;
        if (op == CmpOp::GE) return lhs_fold >= rhs_fold;
      }
    }
  }

  return false;
}

bool BoolBin::eval(const RecordView& rv) const {
  if (op==BoolOp::AND) {
    if (!lhs->eval(rv)) return false;
    return rhs->eval(rv);
  } else {
    if (lhs->eval(rv)) return true;
    return rhs->eval(rv);
  }
}

bool Not::eval(const RecordView& rv) const { return !inner->eval(rv); }

double Arith::evalNumber(const RecordView& rv) const {
  auto L = value_as_number(rv, lhs.get()).value_or(0.0);
  auto R = value_as_number(rv, rhs.get()).value_or(0.0);
  switch (op) {
    case ArithOp::Add: return L + R;
    case ArithOp::Sub: return L - R;
    case ArithOp::Mul: return L * R;
    case ArithOp::Div: return (R==0.0 ? 0.0 : L / R);
  }
  return 0.0;
}

bool Arith::eval(const RecordView& rv) const {
  return evalNumber(rv) != 0.0;
}
