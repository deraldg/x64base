#include "shell_bool_eval_adapter.hpp"

#include <mutex>
#include <unordered_map>
#include <memory>
#include <string>
#include <cctype>
#include <utility>

#include "xbase.hpp"
#include "cli/expr/api.hpp"          // compile_where, CompileResult
#include "cli/expr/glue_xbase.hpp"   // glue::make_record_view

// These are provided by the shell control-flow module.
// shell.cpp already declares them as extern "C"; we do the same here so the
// adapter can register the evaluator for WHILE/UNTIL without pulling in shell.cpp.
extern "C" void while_set_condition_eval(bool(*)(xbase::DbArea&, const std::string&));
extern "C" void until_set_condition_eval(bool(*)(xbase::DbArea&, const std::string&));

namespace {

using dottalk::expr::Expr;

struct CacheEntry { std::unique_ptr<Expr> expr; };
static std::mutex g_cache_mu;
static std::unordered_map<std::string, CacheEntry> g_cache;
static constexpr std::size_t kMaxCache = 256;

static ShellAstBoolEval g_injected_eval = nullptr;

static bool quick_literals_ci(const std::string& s, bool& out)
{
    auto up = [](char c){ return char(std::toupper(static_cast<unsigned char>(c))); };
    size_t i = 0, j = s.size();
    while (i < j && std::isspace(static_cast<unsigned char>(s[i]))) ++i;
    while (j > i && std::isspace(static_cast<unsigned char>(s[j - 1]))) --j;
    if (i >= j) return false;

    std::string U;
    U.reserve(j - i);
    for (size_t k = i; k < j; ++k) U.push_back(up(s[k]));

    if (U == ".T." || U == "T" || U == "TRUE" || U == "1" || U == "Y") { out = true;  return true; }
    if (U == ".F." || U == "F" || U == "FALSE"|| U == "0" || U == "N") { out = false; return true; }

    return false;
}

static bool cr_has_expr(const dottalk::expr::CompileResult& cr)
{
    return (cr.program != nullptr);
}

static std::unique_ptr<Expr> cr_take_expr(dottalk::expr::CompileResult& cr)
{
    return std::move(cr.program);
}

static bool ensure_compiled_in_cache(const std::string& text)
{
    std::lock_guard<std::mutex> lk(g_cache_mu);

    auto it = g_cache.find(text);
    if (it != g_cache.end() && it->second.expr) return true;

    auto cr = dottalk::expr::compile_where(text);
    if (!cr_has_expr(cr)) return false;

    auto up = cr_take_expr(cr);
    if (!up) return false;

    if (g_cache.size() >= kMaxCache) g_cache.clear(); // simple eviction

    g_cache.emplace(text, CacheEntry{ std::move(up) });
    return true;
}

static bool ast_boolean_eval(xbase::DbArea& A, const std::string& expr)
{
    bool lit = false;
    if (quick_literals_ci(expr, lit)) return lit;

    if (!ensure_compiled_in_cache(expr)) {
        return false;
    }

    std::unique_ptr<Expr>* pExpr = nullptr;
    {
        std::lock_guard<std::mutex> lk(g_cache_mu);
        auto it = g_cache.find(expr);
        if (it == g_cache.end()) return false;
        pExpr = &it->second.expr;
    }
    if (!pExpr || !(*pExpr)) return false;

    auto rv = dottalk::expr::glue::make_record_view(A);
    return (*pExpr)->eval(rv);
}

} // namespace

void shell_set_ast_boolean_evaluator(ShellAstBoolEval fn)
{
    g_injected_eval = fn;
}

bool shell_eval_bool_expr(const std::string& expr, xbase::DbArea& area, std::string* err)
{
    if (g_injected_eval) {
        return g_injected_eval(expr, area, err);
    }

    try {
        bool r = ast_boolean_eval(area, expr);
        if (err) err->clear();
        return r;
    } catch (const std::exception& e) {
        if (err) *err = e.what();
        return false;
    } catch (...) {
        if (err) *err = "evaluation failed";
        return false;
    }
}

static bool shell_boolean_eval_bridge(xbase::DbArea& A, const std::string& expr)
{
    return ast_boolean_eval(A, expr);
}

void shell_eval_register_for_loops()
{
    while_set_condition_eval(&shell_boolean_eval_bridge);
    until_set_condition_eval(&shell_boolean_eval_bridge);
}
