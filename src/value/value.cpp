#include "value/value.hpp"

#include <algorithm>
#include <cctype>
#include <utility>

namespace dottalk::value {
namespace {

std::string trim_copy(const std::string& input) {
    std::size_t first = 0;
    while (first < input.size() &&
           std::isspace(static_cast<unsigned char>(input[first])) != 0) {
        ++first;
    }

    std::size_t last = input.size();
    while (last > first &&
           std::isspace(static_cast<unsigned char>(input[last - 1])) != 0) {
        --last;
    }

    return input.substr(first, last - first);
}

bool all_zero(const std::string& digits) {
    return std::all_of(digits.begin(), digits.end(),
                       [](char ch) { return ch == '0'; });
}

void normalized_parts(const ExactDecimal& value,
                      bool& negative,
                      std::string& digits,
                      std::uint32_t& scale) {
    negative = value.negative;
    digits = value.digits.empty() ? "0" : value.digits;
    scale = value.scale;

    const auto first_nonzero = digits.find_first_not_of('0');
    if (first_nonzero == std::string::npos) {
        negative = false;
        digits = "0";
        scale = 0;
        return;
    }
    digits.erase(0, first_nonzero);

    while (scale > 0 && digits.size() > 1 && digits.back() == '0') {
        digits.pop_back();
        --scale;
    }
}

} // namespace

bool ExactDecimal::parse(const std::string& text,
                         ExactDecimal& out,
                         std::string* error) {
    const std::string s = trim_copy(text);
    if (s.empty()) {
        if (error) *error = "decimal text is empty";
        return false;
    }

    std::size_t pos = 0;
    bool neg = false;
    if (s[pos] == '+' || s[pos] == '-') {
        neg = s[pos] == '-';
        ++pos;
    }

    if (pos >= s.size()) {
        if (error) *error = "decimal has sign but no digits";
        return false;
    }

    bool seen_dot = false;
    bool seen_digit = false;
    std::uint32_t scale = 0;
    std::string digits;
    digits.reserve(s.size());

    for (; pos < s.size(); ++pos) {
        const char ch = s[pos];
        if (ch >= '0' && ch <= '9') {
            seen_digit = true;
            digits.push_back(ch);
            if (seen_dot) ++scale;
            continue;
        }

        if (ch == '.' && !seen_dot) {
            seen_dot = true;
            continue;
        }

        if (error) *error = "invalid decimal character";
        return false;
    }

    if (!seen_digit) {
        if (error) *error = "decimal contains no digits";
        return false;
    }

    const auto first_nonzero = digits.find_first_not_of('0');
    if (first_nonzero == std::string::npos) {
        digits = "0";
        neg = false;
    } else {
        digits.erase(0, first_nonzero);
    }

    out.negative = neg;
    out.digits = std::move(digits);
    out.scale = scale;
    return true;
}

std::string ExactDecimal::canonical_text() const {
    std::string coefficient = digits.empty() ? "0" : digits;
    const bool is_zero = all_zero(coefficient);

    if (scale == 0) {
        return std::string((negative && !is_zero) ? "-" : "") + coefficient;
    }

    if (coefficient.size() <= scale) {
        coefficient.insert(0, static_cast<std::size_t>(scale) - coefficient.size() + 1, '0');
    }

    const std::size_t point = coefficient.size() - scale;
    coefficient.insert(point, 1, '.');

    if (negative && !is_zero) coefficient.insert(coefficient.begin(), '-');
    return coefficient;
}

bool ExactDecimal::equivalent(const ExactDecimal& other) const {
    bool lhs_negative = false;
    bool rhs_negative = false;
    std::string lhs_digits;
    std::string rhs_digits;
    std::uint32_t lhs_scale = 0;
    std::uint32_t rhs_scale = 0;

    normalized_parts(*this, lhs_negative, lhs_digits, lhs_scale);
    normalized_parts(other, rhs_negative, rhs_digits, rhs_scale);

    if (lhs_negative != rhs_negative) return false;

    if (lhs_scale < rhs_scale) {
        lhs_digits.append(rhs_scale - lhs_scale, '0');
    } else if (rhs_scale < lhs_scale) {
        rhs_digits.append(lhs_scale - rhs_scale, '0');
    }

    return lhs_digits == rhs_digits;
}

bool DateValue::valid() const noexcept {
    if (year < 1 || month < 1 || month > 12 || day < 1) return false;

    static constexpr std::uint8_t days_by_month[] = {
        0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
    };

    std::uint8_t max_day = days_by_month[month];
    const bool leap =
        (year % 400 == 0) || ((year % 4 == 0) && (year % 100 != 0));
    if (month == 2 && leap) max_day = 29;

    return day <= max_day;
}

bool DateTimeValue::valid() const noexcept {
    return date.valid() &&
           hour <= 23 &&
           minute <= 59 &&
           second <= 59 &&
           millisecond <= 999;
}

Value::Value(ValueState state,
             ValueKind kind,
             ValuePayload payload,
             std::string diagnostic)
    : state_(state),
      kind_(kind),
      payload_(std::move(payload)),
      diagnostic_(std::move(diagnostic)) {}

Value Value::logical(bool value) {
    return Value(ValueState::Present, ValueKind::Logical, value);
}

Value Value::integer(std::int64_t value) {
    return Value(ValueState::Present, ValueKind::Integer, value);
}

Value Value::unsigned_integer(std::uint64_t value) {
    return Value(ValueState::Present, ValueKind::UnsignedInteger, value);
}

Value Value::decimal(ExactDecimal value) {
    return Value(ValueState::Present, ValueKind::Decimal, std::move(value));
}

Value Value::floating(double value) {
    return Value(ValueState::Present, ValueKind::Floating, value);
}

Value Value::character(std::string value) {
    return Value(ValueState::Present, ValueKind::Character, std::move(value));
}

Value Value::date(DateValue value) {
    if (!value.valid()) return invalid(ValueKind::Date, "invalid date");
    return Value(ValueState::Present, ValueKind::Date, value);
}

Value Value::datetime(DateTimeValue value) {
    if (!value.valid()) return invalid(ValueKind::DateTime, "invalid datetime");
    return Value(ValueState::Present, ValueKind::DateTime, value);
}

Value Value::memo_reference(dottalk::memo::MemoRef value) {
    return Value(ValueState::Present, ValueKind::MemoReference, std::move(value));
}

Value Value::custom(CustomValue value) {
    return Value(ValueState::Present, ValueKind::Custom, std::move(value));
}

Value Value::array_reference(ArrayReference value) {
    return Value(ValueState::Present, ValueKind::ArrayReference, std::move(value));
}

Value Value::null(ValueKind expected) {
    return Value(ValueState::Null, expected, std::monostate{});
}

Value Value::blank(ValueKind expected) {
    return Value(ValueState::Blank, expected, std::monostate{});
}

Value Value::invalid(ValueKind expected, std::string diagnostic) {
    return Value(ValueState::Invalid, expected, std::monostate{}, std::move(diagnostic));
}

Value Value::unavailable(ValueKind expected, std::string diagnostic) {
    return Value(ValueState::Unavailable, expected, std::monostate{}, std::move(diagnostic));
}

Value Value::error(std::string diagnostic) {
    return Value(ValueState::Error,
                 ValueKind::Unspecified,
                 std::monostate{},
                 std::move(diagnostic));
}

} // namespace dottalk::value
