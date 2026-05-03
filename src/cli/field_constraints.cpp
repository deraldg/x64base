// field_constraints.cpp
// DotTalk++ first-pass field value constraint layer.

#include "cli/field_constraints.hpp"
#include "cli/rule_catalog.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <regex>
#include <sstream>
#include <string>

namespace dottalk::constraints {
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

static char field_type_upper(const xbase::DbArea& A, int field1)
{
    const auto& f = A.fields().at(static_cast<std::size_t>(field1 - 1));
    return static_cast<char>(std::toupper(static_cast<unsigned char>(f.type)));
}

static std::string field_name_upper(const xbase::DbArea& A, int field1)
{
    const auto& f = A.fields().at(static_cast<std::size_t>(field1 - 1));
    return up_copy(f.name);
}

static bool is_blank_store_value(const std::string& v)
{
    return trim_copy(v).empty();
}

static bool parse_long_double_strict(const std::string& raw, long double& out)
{
    const std::string s = trim_copy(raw);
    if (s.empty()) return false;

    char* end = nullptr;
    const long double v = std::strtold(s.c_str(), &end);
    if (end == s.c_str()) return false;
    while (end && *end) {
        if (!std::isspace(static_cast<unsigned char>(*end))) return false;
        ++end;
    }
    if (!std::isfinite(static_cast<double>(v))) return false;

    out = v;
    return true;
}

static bool parse_date8_strict(const std::string& raw, std::string& out)
{
    const std::string s = trim_copy(raw);
    if (s.size() != 8) return false;
    for (char c : s) {
        if (!std::isdigit(static_cast<unsigned char>(c))) return false;
    }
    out = s;
    return true;
}

static bool equals_ci(const std::string& a, const std::string& b)
{
    return up_copy(trim_copy(a)) == up_copy(trim_copy(b));
}

static std::string describe_field(const xbase::DbArea& A, int field1)
{
    try {
        const auto& f = A.fields().at(static_cast<std::size_t>(field1 - 1));
        return f.name;
    } catch (...) {
        return "field " + std::to_string(field1);
    }
}

// Bootstrap catalog.
// Later replacement seam: load this information from CDX/schema metadata.
static std::optional<FieldConstraint> bootstrap_constraint_for_name(const std::string& upper_name)
{
    if (upper_name == "GPA") {
        FieldConstraint c;
        c.min_value = "0.00";
        c.max_value = "4.00";
        c.message = "GPA must be between 0.00 and 4.00";
        return c;
    }

    if (upper_name == "AGE" || upper_name == "DRIVER_AGE") {
        FieldConstraint c;
        c.min_value = "16";
        c.message = upper_name == "DRIVER_AGE"
            ? "DRIVER_AGE must be 16 or greater"
            : "AGE must be 16 or greater";
        return c;
    }

    if (upper_name == "STATUS") {
        FieldConstraint c;
        c.enum_values = {"A", "I", "S"};
        c.message = "STATUS must be one of A, I, S";
        return c;
    }

    if (upper_name == "PRICE" || upper_name == "AMOUNT" || upper_name == "BALANCE") {
        FieldConstraint c;
        c.min_value = "0.00";
        c.message = upper_name + " must be 0.00 or greater";
        return c;
    }

    if (upper_name == "STATE") {
        FieldConstraint c;
        c.pattern = "^[A-Z][A-Z]$";
        c.message = "STATE must be two uppercase letters";
        return c;
    }

    return std::nullopt;
}

static bool validate_enum(const FieldConstraint& c,
                          const std::string& value,
                          std::string& err)
{
    if (c.enum_values.empty()) return true;

    for (const auto& allowed : c.enum_values) {
        if (equals_ci(value, allowed)) return true;
    }

    err = c.message.empty() ? "value is not in the allowed list" : c.message;
    return false;
}

static bool validate_numeric_range(const FieldConstraint& c,
                                   const std::string& value,
                                   std::string& err)
{
    long double actual = 0.0L;
    if (!parse_long_double_strict(value, actual)) {
        err = "constraint validation expected a numeric store value";
        return false;
    }

    if (c.min_value) {
        long double minv = 0.0L;
        if (parse_long_double_strict(*c.min_value, minv) && actual < minv) {
            err = c.message.empty() ? "value is below minimum" : c.message;
            return false;
        }
    }

    if (c.max_value) {
        long double maxv = 0.0L;
        if (parse_long_double_strict(*c.max_value, maxv) && actual > maxv) {
            err = c.message.empty() ? "value is above maximum" : c.message;
            return false;
        }
    }

    return true;
}

static bool validate_date_range(const FieldConstraint& c,
                                const std::string& value,
                                std::string& err)
{
    std::string actual;
    if (!parse_date8_strict(value, actual)) {
        err = "constraint validation expected YYYYMMDD date store value";
        return false;
    }

    if (c.min_value) {
        std::string minv;
        if (parse_date8_strict(*c.min_value, minv) && actual < minv) {
            err = c.message.empty() ? "date is before minimum" : c.message;
            return false;
        }
    }

    if (c.max_value) {
        std::string maxv;
        if (parse_date8_strict(*c.max_value, maxv) && actual > maxv) {
            err = c.message.empty() ? "date is after maximum" : c.message;
            return false;
        }
    }

    return true;
}

static bool validate_pattern(const FieldConstraint& c,
                             const std::string& value,
                             std::string& err)
{
    if (!c.pattern) return true;

    try {
        const std::regex rx(*c.pattern);
        if (std::regex_match(trim_copy(value), rx)) return true;
    } catch (...) {
        err = "invalid constraint pattern";
        return false;
    }

    err = c.message.empty() ? "value does not match required pattern" : c.message;
    return false;
}

} // namespace

std::optional<FieldConstraint> constraint_for_field(const xbase::DbArea& A, int field1)
{
    if (!A.isOpen()) return std::nullopt;
    if (field1 < 1 || field1 > static_cast<int>(A.fields().size())) return std::nullopt;

    // Preferred source: file-backed RULE catalog.
    // Fallback source: bootstrap catalog retained for tests and migration.
    if (auto from_rules = rules::constraint_for_field(A, field1)) {
        return from_rules;
    }

    return bootstrap_constraint_for_name(field_name_upper(A, field1));
}

bool validate_field_constraint_for_store(const xbase::DbArea& A,
                                         int field1,
                                         const std::string& stored_value,
                                         std::string& err_out)
{
    err_out.clear();

    const auto c_opt = constraint_for_field(A, field1);
    if (!c_opt) return true;

    const FieldConstraint& c = *c_opt;
    const std::string field_name = describe_field(A, field1);
    const std::string value = trim_copy(stored_value);

    if (c.required && is_blank_store_value(value)) {
        err_out = field_name + ": required value is blank";
        return false;
    }

    // Blank optional values are allowed. REQUIRED is the separate rule.
    if (is_blank_store_value(value)) return true;

    std::string err;
    if (!validate_enum(c, value, err)) {
        err_out = field_name + ": " + err;
        return false;
    }

    const char t = field_type_upper(A, field1);

    switch (t) {
        case 'N': // Numeric ASCII
        case 'F': // Float ASCII
        case 'I': // Integer32
        case 'B': // Double
        case 'Y': // Currency
            if ((c.min_value || c.max_value) && !validate_numeric_range(c, value, err)) {
                err_out = field_name + ": " + err;
                return false;
            }
            break;

        case 'D': // YYYYMMDD
            if ((c.min_value || c.max_value) && !validate_date_range(c, value, err)) {
                err_out = field_name + ": " + err;
                return false;
            }
            break;

        case 'C':
            if (!validate_pattern(c, value, err)) {
                err_out = field_name + ": " + err;
                return false;
            }
            break;

        default:
            // First pass: constraints on unsupported storage families are ignored
            // unless ENUM/REQUIRED already caught them above.
            break;
    }

    return true;
}

bool validate_current_record_constraints(const xbase::DbArea& A, std::string& err_out)
{
    err_out.clear();

    if (!A.isOpen()) {
        err_out = "no file open";
        return false;
    }

    const int n = static_cast<int>(A.fields().size());
    for (int field1 = 1; field1 <= n; ++field1) {
        if (!constraint_for_field(A, field1)) continue;

        std::string value;
        try {
            value = A.get(field1);
        } catch (...) {
            err_out = "failed to read field " + std::to_string(field1) + " for constraint validation";
            return false;
        }

        if (!validate_field_constraint_for_store(A, field1, value, err_out)) {
            return false;
        }
    }

    return true;
}

} // namespace dottalk::constraints
