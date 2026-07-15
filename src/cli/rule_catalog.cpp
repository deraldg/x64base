// rule_catalog.cpp
// DotTalk++ RULE catalog resolver.

#include "cli/rule_catalog.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <map>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace dottalk::constraints::rules {
namespace {

static std::string trim_copy(std::string s)
{
    std::size_t a = 0;
    while (a < s.size() && std::isspace(static_cast<unsigned char>(s[a]))) ++a;

    std::size_t b = s.size();
    while (b > a && std::isspace(static_cast<unsigned char>(s[b - 1]))) --b;

    return s.substr(a, b - a);
}

static std::string up_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool file_exists(const fs::path& p)
{
    std::error_code ec;
    return fs::exists(p, ec) && fs::is_regular_file(p, ec);
}

static bool dir_exists(const fs::path& p)
{
    std::error_code ec;
    return fs::exists(p, ec) && fs::is_directory(p, ec);
}

static std::vector<std::string> split_csv(const std::string& raw)
{
    std::vector<std::string> out;
    std::string cur;
    std::istringstream in(raw);
    while (std::getline(in, cur, ',')) {
        cur = trim_copy(cur);
        if (!cur.empty()) out.push_back(cur);
    }
    return out;
}

static std::string strip_inline_comment(std::string s)
{
    // Simple first-pass INI comments. Do not treat # or ; inside regex specially.
    // For now, put complex regexes on a clean PATTERN= line with no trailing comment.
    bool in_quote = false;
    for (std::size_t i = 0; i < s.size(); ++i) {
        const char ch = s[i];
        if (ch == '"') in_quote = !in_quote;
        if (!in_quote && (ch == '#' || ch == ';')) {
            return trim_copy(s.substr(0, i));
        }
    }
    return trim_copy(s);
}

static fs::path find_schemas_dir_for_area(const xbase::DbArea& A)
{
    fs::path start;
    if (!A.dbfDir().empty()) {
        start = fs::path(A.dbfDir());
    } else if (!A.filename().empty()) {
        start = fs::path(A.filename()).parent_path();
    } else {
        start = fs::current_path();
    }

    std::error_code ec;
    fs::path p = fs::weakly_canonical(start, ec);
    if (ec) p = fs::absolute(start, ec);
    if (ec) p = start;

    // Walk upward looking for an existing SCHEMAS directory.
    for (fs::path cur = p; !cur.empty(); cur = cur.parent_path()) {
        fs::path candidate = cur / "SCHEMAS";
        if (dir_exists(candidate)) return candidate;

        // Also tolerate lowercase on case-sensitive test hosts.
        candidate = cur / "schemas";
        if (dir_exists(candidate)) return candidate;

        if (cur == cur.parent_path()) break;
    }

    // Fallback for the expected DotTalk++ layout:
    //   data/DBF/x64  -> data/SCHEMAS
    //   data/dbf      -> data/SCHEMAS
    fs::path cur = p;
    for (int i = 0; i < 3 && !cur.empty(); ++i) {
        fs::path candidate = cur / "SCHEMAS";
        if (dir_exists(candidate)) return candidate;
        cur = cur.parent_path();
    }

    // Last-resort deterministic path. Caller will simply fail to load if absent.
    return p / "SCHEMAS";
}

static std::string field_name_upper(const xbase::DbArea& A, int field1)
{
    const auto& f = A.fields().at(static_cast<std::size_t>(field1 - 1));
    return up_copy(f.name);
}

static std::string table_name_upper(const xbase::DbArea& A)
{
    std::string name = A.logicalName();
    if (name.empty()) name = A.dbfBasename();
    return up_copy(name);
}

static std::string normalize_pattern_token(const std::string& raw)
{
    const std::string s = trim_copy(raw);
    if (up_copy(s) == "BASIC-EMAIL" || up_copy(s) == "EMAIL") {
        return R"(^[^@\s]+@[^@\s]+\.[^@\s]+$)";
    }
    return s;
}

using RuleMap = std::map<std::string, FieldConstraint>;
using BindingMap = std::map<std::string, std::string>;

static void apply_rule_property(FieldConstraint& c,
                                const std::string& key_raw,
                                const std::string& value_raw)
{
    const std::string key = up_copy(trim_copy(key_raw));
    const std::string value = trim_copy(value_raw);

    if (key == "REQUIRED" || key == "NOTNULL" || key == "NOT_NULL") {
        const std::string v = up_copy(value);
        c.required = (v == "1" || v == "TRUE" || v == "YES" || v == "ON");
    } else if (key == "MIN") {
        c.min_value = value;
    } else if (key == "MAX") {
        c.max_value = value;
    } else if (key == "ENUM" || key == "IN") {
        c.enum_values = split_csv(value);
    } else if (key == "PATTERN") {
        c.pattern = normalize_pattern_token(value);
    } else if (key == "MESSAGE") {
        c.message = value;
    } else if (key == "DEFAULT") {
        c.default_value = value;
    } else if (key == "UNIQUE") {
        const std::string v = up_copy(value);
        c.unique = (v == "1" || v == "TRUE" || v == "YES" || v == "ON");
    } else if (key == "PRIMARY") {
        const std::string v = up_copy(value);
        c.primary = (v == "1" || v == "TRUE" || v == "YES" || v == "ON");
    }
    // TYPE is accepted in rule files for documentation / future compatibility,
    // but field storage type still comes from DbArea::fields().
}

static RuleMap load_rule_catalog(const fs::path& path)
{
    RuleMap rules;
    std::ifstream in(path);
    if (!in) return rules;

    std::string active_rule;
    std::string line;

    while (std::getline(in, line)) {
        line = strip_inline_comment(line);
        if (line.empty()) continue;

        if (line.front() == '[' && line.back() == ']') {
            std::string section = trim_copy(line.substr(1, line.size() - 2));
            std::istringstream ss(section);
            std::string word;
            ss >> word;
            if (up_copy(word) == "RULE") {
                std::string name;
                ss >> name;
                active_rule = up_copy(trim_copy(name));
                if (!active_rule.empty() && rules.find(active_rule) == rules.end()) {
                    rules[active_rule] = FieldConstraint{};
                }
            } else {
                active_rule.clear();
            }
            continue;
        }

        if (active_rule.empty()) continue;

        const std::size_t eq = line.find('=');
        if (eq == std::string::npos) continue;

        const std::string key = line.substr(0, eq);
        const std::string value = line.substr(eq + 1);
        apply_rule_property(rules[active_rule], key, value);
    }

    return rules;
}

static BindingMap load_table_bindings(const fs::path& path,
                                      const std::string& expected_table_upper)
{
    BindingMap bindings;
    std::ifstream in(path);
    if (!in) return bindings;

    bool in_target_table = false;
    std::string line;

    while (std::getline(in, line)) {
        line = strip_inline_comment(line);
        if (line.empty()) continue;

        if (line.front() == '[' && line.back() == ']') {
            std::string section = trim_copy(line.substr(1, line.size() - 2));
            std::istringstream ss(section);
            std::string word;
            std::string table;
            ss >> word >> table;
            in_target_table = (up_copy(word) == "TABLE" && up_copy(table) == expected_table_upper);
            continue;
        }

        if (!in_target_table) continue;

        const std::size_t eq = line.find('=');
        if (eq == std::string::npos) continue;

        const std::string field = up_copy(trim_copy(line.substr(0, eq)));
        const std::string rule = up_copy(trim_copy(line.substr(eq + 1)));
        if (!field.empty() && !rule.empty()) bindings[field] = rule;
    }

    return bindings;
}

} // namespace

std::string rules_catalog_path_for_area(const xbase::DbArea& A)
{
    return (find_schemas_dir_for_area(A) / "rules.meta").string();
}

std::string table_rules_path_for_area(const xbase::DbArea& A)
{
    return (find_schemas_dir_for_area(A) / "tables" / (table_name_upper(A) + ".rules")).string();
}

std::optional<FieldConstraint> constraint_for_field(const xbase::DbArea& A,
                                                    int field1)
{
    if (!A.isOpen()) return std::nullopt;
    if (field1 < 1 || field1 > static_cast<int>(A.fields().size())) return std::nullopt;

    const fs::path catalog_path = rules_catalog_path_for_area(A);
    const fs::path table_path = table_rules_path_for_area(A);

    if (!file_exists(catalog_path) || !file_exists(table_path)) return std::nullopt;

    const RuleMap rules = load_rule_catalog(catalog_path);
    if (rules.empty()) return std::nullopt;

    const BindingMap bindings = load_table_bindings(table_path, table_name_upper(A));
    if (bindings.empty()) return std::nullopt;

    const std::string field = field_name_upper(A, field1);
    const auto b = bindings.find(field);
    if (b == bindings.end()) return std::nullopt;

    const auto r = rules.find(b->second);
    if (r == rules.end()) return std::nullopt;

    return r->second;
}

} // namespace dottalk::constraints::rules
