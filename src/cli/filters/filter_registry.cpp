#include "filter_registry.hpp"

#include <cctype>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "xbase.hpp"

// real API
#include "cli/expr/api.hpp"
#include "cli/expr/ast.hpp"

// field lookup helpers
namespace filter_detail {

inline int find_field_ci(const std::vector<xbase::FieldDef>& fields,
                         const std::string& name)
{
    auto up = [](char c) { return static_cast<char>(std::toupper(static_cast<unsigned char>(c))); };

    for (size_t i = 0; i < fields.size(); ++i) {
        const auto& f = fields[i].name;
        if (f.size() != name.size()) continue;

        bool match = true;
        for (size_t j = 0; j < f.size(); ++j) {
            if (up(f[j]) != up(name[j])) {
                match = false;
                break;
            }
        }
        if (match) return static_cast<int>(i);
    }
    return -1;
}

inline std::string normalize_char(std::string s)
{
    // Trim right padding (classic DBF CHAR behavior).
    while (!s.empty() && (s.back() == ' ' || s.back() == '\t')) {
        s.pop_back();
    }

    // Trim left defensively.
    size_t i = 0;
    while (i < s.size() && (s[i] == ' ' || s[i] == '\t')) {
        ++i;
    }
    if (i > 0) {
        s.erase(0, i);
    }

    // Uppercase for case-insensitive comparisons.
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }

    return s;
}

inline std::string get_field_str(xbase::DbArea& area,
                                 const std::string& name)
{
    int idx = find_field_ci(area.fields(), name);
    if (idx < 0) return {};

    std::string s = area.get(idx + 1);
    return normalize_char(s);
}

inline std::optional<double> get_field_num(xbase::DbArea& area,
                                           const std::string& name)
{
    int idx = find_field_ci(area.fields(), name);
    if (idx < 0) return std::nullopt;

    std::string s = area.get(idx + 1);
    try {
        return std::stod(s);
    } catch (...) {
        return std::nullopt;
    }
}

inline bool is_ident_start(char c)
{
    return std::isalpha(static_cast<unsigned char>(c)) || c == '_';
}

inline bool is_ident_char(char c)
{
    return std::isalnum(static_cast<unsigned char>(c)) || c == '_';
}

inline std::string upper(std::string s)
{
    for (char& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

inline bool is_known_nonfield_identifier(const std::string& ident)
{
    static const std::unordered_set<std::string> k = {
        "AND", "OR", "NOT", "TRUE", "FALSE", "T", "F",
        "DATE", "TODAY", "TIME", "NOW", "DATETIME",
        "CTOD", "DTOC", "DATEADD", "DATEDIFF",
        "UPPER", "LOWER", "ALLTRIM", "LTRIM", "RTRIM", "TRIM",
        "LEN", "LEFT", "RIGHT", "SUBSTR", "VAL", "STR", "TRANSFORM"
    };
    return k.find(upper(ident)) != k.end();
}

inline bool has_comparison_at(const std::string& s, size_t i, size_t& width)
{
    width = 0;
    if (i >= s.size()) return false;
    const char c = s[i];
    if ((c == '<' || c == '>' || c == '!') && i + 1 < s.size() && s[i + 1] == '=') {
        width = 2;
        return true;
    }
    if (c == '<' && i + 1 < s.size() && s[i + 1] == '>') {
        width = 2;
        return true;
    }
    if (c == '=' || c == '<' || c == '>') {
        width = 1;
        return true;
    }
    return false;
}

inline bool last_identifier_before(const std::string& s, size_t pos, std::string& ident)
{
    ident.clear();
    if (pos == 0) return false;

    size_t i = pos;
    while (i > 0 && std::isspace(static_cast<unsigned char>(s[i - 1]))) --i;
    while (i > 0 && s[i - 1] == ')') {
        --i;
        while (i > 0 && std::isspace(static_cast<unsigned char>(s[i - 1]))) --i;
    }
    if (i == 0) return false;

    size_t end = i;
    while (i > 0 && is_ident_char(s[i - 1])) --i;
    if (i == end || !is_ident_start(s[i])) return false;

    ident = s.substr(i, end - i);
    return true;
}

inline bool validate_filter_field_refs(xbase::DbArea& area,
                                       const std::string& text,
                                       std::string& err)
{
    bool in_quote = false;
    char quote = '\0';

    for (size_t i = 0; i < text.size(); ++i) {
        const char c = text[i];
        if (in_quote) {
            if (c == quote) in_quote = false;
            continue;
        }
        if (c == '\'' || c == '"') {
            in_quote = true;
            quote = c;
            continue;
        }

        size_t width = 0;
        if (!has_comparison_at(text, i, width)) continue;

        std::string lhs;
        if (!last_identifier_before(text, i, lhs)) {
            i += width ? width - 1 : 0;
            continue;
        }

        if (is_known_nonfield_identifier(lhs)) {
            i += width ? width - 1 : 0;
            continue;
        }

        if (find_field_ci(area.fields(), lhs) < 0) {
            err = "unknown field '" + lhs + "' in filter expression";
            return false;
        }

        i += width ? width - 1 : 0;
    }

    return true;
}

} // namespace filter_detail

#define DOTTALK_GET_FIELD_STR(area, name) filter_detail::get_field_str(area, name)
#define DOTTALK_GET_FIELD_NUM(area, name) filter_detail::get_field_num(area, name)

#include "cli/expr/glue_xbase.hpp"

using dottalk::expr::Expr;

namespace {
struct State {
    std::shared_ptr<Expr> ast;
    std::string text;
};

std::unordered_map<xbase::DbArea*, State> g_map;
std::mutex g_mx;
} // namespace

namespace filter {

bool set(xbase::DbArea* area, const std::string& text, std::string& err)
{
    if (!area || !area->isOpen()) {
        err = "no table open";
        return false;
    }

    if (!filter_detail::validate_filter_field_refs(*area, text, err)) {
        return false;
    }

    auto cr = dottalk::expr::compile_where(text);
    if (!cr) {
        err = cr.error;
        return false;
    }

    std::lock_guard<std::mutex> lk(g_mx);
    g_map[area] = { std::shared_ptr<Expr>(std::move(cr.program)), text };
    return true;
}

void clear(xbase::DbArea* area)
{
    if (!area) return;

    std::lock_guard<std::mutex> lk(g_mx);
    g_map.erase(area);
}

bool has(xbase::DbArea* area)
{
    std::lock_guard<std::mutex> lk(g_mx);
    auto it = g_map.find(area);
    return it != g_map.end() && static_cast<bool>(it->second.ast);
}

bool has_active_filter(xbase::DbArea* area)
{
    if (!area) return false;

    std::lock_guard<std::mutex> lk(g_mx);
    auto it = g_map.find(area);
    if (it == g_map.end()) return false;

    return static_cast<bool>(it->second.ast) || !it->second.text.empty();
}

bool visible(xbase::DbArea* area,
             const std::shared_ptr<Expr>& for_ast)
{
    if (!area) return false;

    std::shared_ptr<Expr> fil_ast;
    {
        std::lock_guard<std::mutex> lk(g_mx);
        auto it = g_map.find(area);
        if (it != g_map.end())
            fil_ast = it->second.ast;
    }

    auto rv = dottalk::expr::glue::make_record_view(*area);

    if (fil_ast && !fil_ast->eval(rv)) return false;
    if (for_ast && !for_ast->eval(rv)) return false;
    return true;
}

} // namespace filter