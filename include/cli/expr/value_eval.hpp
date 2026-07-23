#pragma once
#include <cstdint>
#include <memory>
#include <string>

namespace xbase { class DbArea; }

namespace dottalk::expr {

// Forward declarations from your existing expr headers
struct Expr;
struct RecordView;

struct EvalValue {
    enum Kind { K_None, K_Number, K_String, K_Bool, K_Date } kind = K_None;

    double      number = 0.0;
    std::string text;
    bool        tf = false;
    std::int32_t date8 = 0;   // YYYYMMDD
};

// Evaluate a compiled program (no parsing/compiling here)
EvalValue eval_compiled_program(const Expr* prog, const RecordView& rv);

// Compile a WHERE-style expression to an AST program (moves out the program)
bool compile_where_program(const std::string& exprText,
                           std::unique_ptr<Expr>& programOut,
                           std::string* errOut = nullptr);

// Evaluate a “string value-expr” subset (field refs + string builtins + literals)
// This is the same fallback behavior CALC uses when the generic compiler can’t handle it.
bool eval_string_value_expr(xbase::DbArea& A,
                            const std::string& exprText,
                            std::string& out);

// Full pipeline (mirrors CALC):
// 1) predicate_chain fast path (boolean chains)
// 2) compile_where(...) + eval_compiled_program(...)
 // 3) eval_string_value_expr(...) fallback (string builtins/field refs)
// Returns typed value (bool/number/string/date) or K_None on failure.
EvalValue eval_any(xbase::DbArea& A,
                   const std::string& exprText,
                   std::string* errOut = nullptr);

// Boolean helper (FOR/WHILE):
// Accepts boolean results; also treats numeric as truthy (non-zero).
bool eval_bool(xbase::DbArea& A,
               const std::string& exprText,
               bool& out,
               std::string* errOut = nullptr);

// --- Compile-once predicate (scan-evaluator optimization lane, M1) -----------
// A boolean predicate compiled ONCE for repeated per-row evaluation across a
// scan, so the parse/compile pipeline (text expansion, date folding, AST build)
// is not re-run for every record — that per-row recompile was the dominant scan
// cost. For any predicate that cannot be safely hoisted — a DotScript/memvar
// predicate ($name / {..}), or any expression whose text preprocessing is not a
// record-independent no-op — it transparently falls back to per-row eval_bool,
// so results are identical to eval_bool for every input. Build once with
// compile_bool_predicate; evaluate per row with eval_bool_compiled against the
// area's CURRENT record (move the cursor between calls). CompiledPredicate is
// opaque; hold it by the returned shared_ptr.
struct CompiledPredicate;

// allow_raw: when true and the predicate is safely hoistable, the compiled
// predicate is bound to a selective-decode (readCurrentRaw) record view — the
// caller MUST then advance rows with DbArea::readCurrentRaw() instead of
// readCurrent(). Query compiled_predicate_uses_raw() to find out which view was
// bound (a fallback predicate always uses the normal full-decode path). Only
// pass allow_raw=true when no persistent SET FILTER is active (the filter needs
// the fully decoded record).
std::shared_ptr<CompiledPredicate>
compile_bool_predicate(xbase::DbArea& A, const std::string& exprText,
                       bool allow_raw = false);

// True when the compiled predicate was bound to the selective-decode raw view
// (so the caller must use readCurrentRaw()). False for the fallback/full path.
bool compiled_predicate_uses_raw(const CompiledPredicate& cp);

bool eval_bool_compiled(CompiledPredicate& cp,
                        xbase::DbArea& A,
                        bool& out,
                        std::string* errOut = nullptr);

} // namespace dottalk::expr
