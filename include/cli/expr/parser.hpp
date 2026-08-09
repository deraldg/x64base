// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <memory>
#include <string>
#include "cli/expr/ast.hpp"
#include "cli/expr/lexer.hpp"
#include "cli/expr/token.hpp"

namespace dottalk { namespace expr {

struct ParseError { std::string message; };

class Parser {
public:
  explicit Parser(std::string src): m_lex(std::move(src)) {}
  std::unique_ptr<Expr> parse_expr();

  // ED-01b (AIF-074, 2026-07-30): a caller must be able to verify the parser consumed
  // the WHOLE input. Without this, `NVAL = 12.5 GARBAGE` parses the valid prefix,
  // silently discards the suffix, and returns a confident wrong answer. Runtime-proven
  // the same day: `8.MAJOR = "CSCI"` reported 200/0/0 where the truth was 21/179/0,
  // because the parser accepted `8` as a complete numeric-truthy predicate and threw
  // `.MAJOR = "CSCI"` away. Returns TokKind::End when nothing is left.
  const Token& peek_unconsumed() { return m_lex.peek(); }

private:
  Lexer m_lex;
  int lbp(const Token& t) const;
  std::unique_ptr<Expr> nud(Token t);
  std::unique_ptr<Expr> led(std::unique_ptr<Expr> left, Token op);
  std::unique_ptr<Expr> expression(int min_bp);
  Token expect(TokKind k, const char* msg);
};

}} // namespace



