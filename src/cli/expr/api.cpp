// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "cli/expr/api.hpp"
#include "cli/expr/parser.hpp"
#include "cli/expr/token.hpp"   // TokKind::End -- ED-01b end-of-input check

namespace dottalk { namespace expr {

// ED-01b repair (AIF-074, 2026-07-30). This is the ONE funnel both evaluator families
// reach: the tuple path enters here directly, and the classic path arrives via
// compile_where_program() in value_eval.cpp. Before this check, a predicate whose valid
// PREFIX parsed was accepted and its remainder discarded without a word -- the silent
// wrong-answer class this lane has now closed four times. Confirmed by EVALDIFF on
// 2026-07-30 (labtalk/proofs/runs/20260730_evaldiff_eof_probe.txt): both evaluators
// returned 200/0/0 for `8.MAJOR = "CSCI"` against a true 21/179/0, and both returned
// the bare `NVAL = 12.5` answer for `NVAL = 12.5 GARBAGE`.
//
// EXPECTED FALLOUT, and it is the point: any script carrying a sloppy trailing token
// now REPORTS instead of quietly evaluating something other than what it says. Treat a
// newly failing regression as a bug found, not a regression caused.
CompileResult compile_where(const std::string& text) {
  try {
    Parser p(text);
    auto e = p.parse_expr();

    const Token& rest = p.peek_unconsumed();
    if (rest.kind != TokKind::End) {
      return CompileResult{ nullptr,
        "unexpected input after the end of the expression: '" + rest.lexeme + "'" };
    }

    return CompileResult{ std::move(e), "" };
  } catch (const ParseError& pe) {
    return CompileResult{ nullptr, pe.message };
  } catch (...) {
    return CompileResult{ nullptr, "Unknown parse error" };
  }
}

}} // namespace dottalk::expr




