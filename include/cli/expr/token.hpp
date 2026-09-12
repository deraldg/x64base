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

namespace dottalk { namespace expr {

enum class TokKind {
  End, Ident, Number, String,
  Eq, EqEq, Ne, Lt, Le, Gt, Ge,
  LParen, RParen, Comma,
  KW_NOT, KW_AND, KW_OR,
  Plus, Minus, Star, Slash        // <-- arithmetic
};

struct Token {
  TokKind kind{TokKind::End};
  std::string lexeme;
  double number{0.0};
};

}} // namespace


