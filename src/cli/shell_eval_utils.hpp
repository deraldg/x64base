// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <string>
#include "xbase.hpp"  // xbase::DbArea

namespace dottalk {

// Forward declarations from value_eval.hpp
namespace expr {
struct EvalValue;
}

// VarBangEval result types (same as before)
struct VarBangEval {
    enum Kind { K_None, K_Number, K_String, K_Bool, K_Date8 } kind = K_None;
    double number = 0.0;
    std::string text;
    bool tf = false;
};

// Evaluate expression for SET VAR! (clock fast paths, simple arith, full eval pipeline)
bool eval_for_varbang(xbase::DbArea& A, const std::string& expr, VarBangEval& out, std::string& err);

// Serialize VarBangEval to shell storage format
std::string serialize_varbang_value(const VarBangEval& v);

} // namespace dottalk