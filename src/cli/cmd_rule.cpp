// cmd_rule.cpp
// DotTalk++ RULE diagnostics command.
//
// Public surface:
//   RULE
//   RULE STATUS
//   RULE SHOW <field|ALL>
//   RULE LIST
//   RULE PATHS
//
// Notes:
//   - SHOW / STATUS / LIST / PATHS are internal subcommands of RULE.
//   - This file is diagnostic/read-only. It does not create, edit, or bind rules.
//   - Validation still flows through field_constraints.cpp and rule_catalog.cpp.

#include "cli/field_constraints.hpp"
#include "cli/rule_catalog.hpp"
#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

struct RuleBindingInfo {
    std::string field_upper;
    std::string rule_upper;
};

using BindingMap = std::map<std::string, std::string>;

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

static bool iequals(const std::string& a, const std::string& b)
{
    return up_copy(trim_copy(a)) == up_copy(trim_copy(b));
}

static bool file_exists(const std::string& p)
{
    std::error_code ec;
    const fs::path path(p);
    return fs::exists(path, ec) && fs::is_regular_file(path, ec);
}

static std::string strip_inline_comment(std::string s)
{
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

static std::string table_name_upper(const xbase::DbArea& A)
{
    std::string name = A.logicalName();
    if (name.empty()) name = A.dbfBasename();
    return up_copy(name);
}

static std::string field_name_upper(const xbase::DbArea& A, int field1)
{
    const auto& f = A.fields().at(static_cast<std::size_t>(field1 - 1));
    return up_copy(f.name);
}

static int find_field1(const xbase::DbArea& A, const std::string& name)
{
    const std::string wanted = up_copy(trim_copy(name));
    const auto& fields = A.fields();

    for (int i = 0; i < static_cast<int>(fields.size()); ++i) {
        if (up_copy(fields[static_cast<std::size_t>(i)].name) == wanted) {
            return i + 1;
        }
    }

    return -1;
}

static BindingMap load_table_bindings_for_rule_command(const xbase::DbArea& A)
{
    BindingMap bindings;

    const std::string path = dottalk::constraints::rules::table_rules_path_for_area(A);
    std::ifstream in(path);
    if (!in) return bindings;

    const std::string expected_table = table_name_upper(A);
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
            in_target_table = (iequals(word, "TABLE") && up_copy(table) == expected_table);
            continue;
        }

        if (!in_target_table) continue;

        const std::size_t eq = line.find('=');
        if (eq == std::string::npos) continue;

        const std::string field = up_copy(trim_copy(line.substr(0, eq)));
        const std::string rule  = up_copy(trim_copy(line.substr(eq + 1)));

        if (!field.empty() && !rule.empty()) {
            bindings[field] = rule;
        }
    }

    return bindings;
}

static std::vector<std::string> load_rule_names_for_rule_command(const xbase::DbArea& A)
{
    std::vector<std::string> names;

    const std::string path = dottalk::constraints::rules::rules_catalog_path_for_area(A);
    std::ifstream in(path);
    if (!in) return names;

    std::string line;
    while (std::getline(in, line)) {
        line = strip_inline_comment(line);
        if (line.empty()) continue;

        if (line.front() == '[' && line.back() == ']') {
            std::string section = trim_copy(line.substr(1, line.size() - 2));
            std::istringstream ss(section);
            std::string word;
            std::string name;
            ss >> word >> name;

            if (iequals(word, "RULE") && !name.empty()) {
                names.push_back(up_copy(name));
            }
        }
    }

    std::sort(names.begin(), names.end());
    names.erase(std::unique(names.begin(), names.end()), names.end());
    return names;
}

static std::string summarize_constraint(const dottalk::constraints::FieldConstraint& c)
{
    std::ostringstream out;
    bool any = false;

    if (c.required) {
        out << "REQUIRED";
        any = true;
    }

    if (c.min_value) {
        if (any) out << "; ";
        out << "MIN " << *c.min_value;
        any = true;
    }

    if (c.max_value) {
        if (any) out << "; ";
        out << "MAX " << *c.max_value;
        any = true;
    }

    if (!c.enum_values.empty()) {
        if (any) out << "; ";
        out << "ENUM ";
        for (std::size_t i = 0; i < c.enum_values.size(); ++i) {
            if (i) out << ',';
            out << c.enum_values[i];
        }
        any = true;
    }

    if (c.pattern) {
        if (any) out << "; ";
        out << "PATTERN " << *c.pattern;
        any = true;
    }

    if (c.primary) {
        if (any) out << "; ";
        out << "PRIMARY";
        any = true;
    }

    if (c.unique) {
        if (any) out << "; ";
        out << "UNIQUE";
        any = true;
    }

    if (c.default_value) {
        if (any) out << "; ";
        out << "DEFAULT " << *c.default_value;
        any = true;
    }

    if (!any) return "(constraint has no active checks)";
    return out.str();
}

static void print_constraint_detail(const dottalk::constraints::FieldConstraint& c)
{
    if (c.required) {
        std::cout << "  REQUIRED: yes\n";
    }

    if (c.min_value) {
        std::cout << "  MIN     : " << *c.min_value << "\n";
    }

    if (c.max_value) {
        std::cout << "  MAX     : " << *c.max_value << "\n";
    }

    if (!c.enum_values.empty()) {
        std::cout << "  ENUM    : ";
        for (std::size_t i = 0; i < c.enum_values.size(); ++i) {
            if (i) std::cout << ",";
            std::cout << c.enum_values[i];
        }
        std::cout << "\n";
    }

    if (c.pattern) {
        std::cout << "  PATTERN : " << *c.pattern << "\n";
    }

    if (c.primary) {
        std::cout << "  PRIMARY : yes\n";
    }

    if (c.unique) {
        std::cout << "  UNIQUE  : yes\n";
    }

    if (c.default_value) {
        std::cout << "  DEFAULT : " << *c.default_value << "\n";
    }

    if (!c.message.empty()) {
        std::cout << "  MESSAGE : " << c.message << "\n";
    }
}

static void print_usage()
{
    std::cout << "RULE usage:\n";
    std::cout << "  RULE STATUS\n";
    std::cout << "  RULE SHOW <field|ALL>\n";
    std::cout << "  RULE LIST\n";
    std::cout << "  RULE PATHS\n";
}

static void rule_paths(xbase::DbArea& A, std::istringstream&)
{
    if (!A.isOpen()) {
        std::cout << "RULE PATHS: no file open\n";
        return;
    }

    const std::string catalog = dottalk::constraints::rules::rules_catalog_path_for_area(A);
    const std::string table   = dottalk::constraints::rules::table_rules_path_for_area(A);

    std::cout << "RULE paths for " << table_name_upper(A) << ":\n";
    std::cout << "  Catalog : " << catalog << (file_exists(catalog) ? "  [found]" : "  [missing]") << "\n";
    std::cout << "  Table   : " << table   << (file_exists(table)   ? "  [found]" : "  [missing]") << "\n";
}

static void rule_list(xbase::DbArea& A, std::istringstream&)
{
    if (!A.isOpen()) {
        std::cout << "RULE LIST: no file open\n";
        return;
    }

    const std::string catalog = dottalk::constraints::rules::rules_catalog_path_for_area(A);
    if (!file_exists(catalog)) {
        std::cout << "RULE LIST: catalog not found: " << catalog << "\n";
        return;
    }

    const auto names = load_rule_names_for_rule_command(A);
    if (names.empty()) {
        std::cout << "RULE LIST: no rules found in catalog\n";
        return;
    }

    std::cout << "RULE catalog: " << catalog << "\n";
    for (const auto& name : names) {
        std::cout << "  " << name << "\n";
    }
}

static void rule_show_one(xbase::DbArea& A,
                          const BindingMap& bindings,
                          int field1)
{
    const auto& f = A.fields().at(static_cast<std::size_t>(field1 - 1));
    const std::string fname = f.name;
    const std::string fupper = field_name_upper(A, field1);

    const auto binding = bindings.find(fupper);
    const std::string rule_name = (binding == bindings.end()) ? "(none)" : binding->second;

    const auto c_opt = dottalk::constraints::constraint_for_field(A, field1);

    std::cout << fname << " :\n";
    std::cout << "  RULE    : " << rule_name << "\n";

    if (!c_opt) {
        std::cout << "  STATUS  : no resolved constraint\n";
        return;
    }

    std::cout << "  STATUS  : resolved\n";
    print_constraint_detail(*c_opt);
}

static void rule_show(xbase::DbArea& A, std::istringstream& S)
{
    if (!A.isOpen()) {
        std::cout << "RULE SHOW: no file open\n";
        return;
    }

    std::string target;
    S >> target;

    if (target.empty()) {
        std::cout << "Usage: RULE SHOW <field|ALL>\n";
        return;
    }

    const BindingMap bindings = load_table_bindings_for_rule_command(A);

    if (iequals(target, "ALL")) {
        const int n = static_cast<int>(A.fields().size());
        for (int field1 = 1; field1 <= n; ++field1) {
            rule_show_one(A, bindings, field1);
        }
        return;
    }

    const int field1 = find_field1(A, target);
    if (field1 < 1) {
        std::cout << "RULE SHOW: unknown field '" << target << "'\n";
        return;
    }

    rule_show_one(A, bindings, field1);
}

static void rule_status(xbase::DbArea& A, std::istringstream&)
{
    if (!A.isOpen()) {
        std::cout << "RULE STATUS: no file open\n";
        return;
    }

    const std::string catalog = dottalk::constraints::rules::rules_catalog_path_for_area(A);
    const std::string table   = dottalk::constraints::rules::table_rules_path_for_area(A);
    const BindingMap bindings = load_table_bindings_for_rule_command(A);

    std::cout << "RULE STATUS for " << table_name_upper(A) << "\n";
    std::cout << "Catalog : " << catalog << (file_exists(catalog) ? "  [found]" : "  [missing]") << "\n";
    std::cout << "Table   : " << table   << (file_exists(table)   ? "  [found]" : "  [missing]") << "\n";
    std::cout << "\n";

    std::cout << std::left
              << std::setw(14) << "Field"
              << std::setw(18) << "Rule"
              << "Constraint\n";
    std::cout << std::string(70, '-') << "\n";

    const int n = static_cast<int>(A.fields().size());
    for (int field1 = 1; field1 <= n; ++field1) {
        const auto& f = A.fields().at(static_cast<std::size_t>(field1 - 1));
        const std::string fupper = field_name_upper(A, field1);

        const auto b = bindings.find(fupper);
        const std::string rule_name = (b == bindings.end()) ? "(none)" : b->second;

        const auto c_opt = dottalk::constraints::constraint_for_field(A, field1);
        const std::string summary = c_opt ? summarize_constraint(*c_opt) : "(none)";

        std::cout << std::left
                  << std::setw(14) << f.name
                  << std::setw(18) << rule_name
                  << summary << "\n";
    }
}

} // namespace

void cmd_RULE(xbase::DbArea& A, std::istringstream& S)
{
    std::string sub;
    S >> sub;
    sub = up_copy(trim_copy(sub));

    if (sub.empty() || sub == "STATUS") {
        rule_status(A, S);
        return;
    }

    if (sub == "SHOW") {
        rule_show(A, S);
        return;
    }

    if (sub == "LIST") {
        rule_list(A, S);
        return;
    }

    if (sub == "PATHS") {
        rule_paths(A, S);
        return;
    }

    if (sub == "HELP" || sub == "?") {
        print_usage();
        return;
    }

    std::cout << "RULE: unknown option '" << sub << "'\n";
    print_usage();
}
