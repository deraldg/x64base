#pragma once

#include <cstdint>
#include <string>

namespace xexpr {

enum class ValueKind {
    None,
    Bool,
    Number,
    String,
    Date,
    Error
};

class Value {
public:
    Value() = default;

    static Value none();
    static Value logical(bool v);
    static Value number(double v);
    static Value string(std::string v);
    static Value date(std::int32_t yyyymmdd);
    static Value error(std::string message);

    ValueKind kind() const noexcept { return kind_; }

    bool is_none() const noexcept { return kind_ == ValueKind::None; }
    bool is_bool() const noexcept { return kind_ == ValueKind::Bool; }
    bool is_number() const noexcept { return kind_ == ValueKind::Number; }
    bool is_string() const noexcept { return kind_ == ValueKind::String; }
    bool is_date() const noexcept { return kind_ == ValueKind::Date; }
    bool is_error() const noexcept { return kind_ == ValueKind::Error; }

    bool as_bool() const noexcept { return tf_; }
    double as_number() const noexcept { return number_; }
    const std::string& as_string() const noexcept { return text_; }
    std::int32_t as_date8() const noexcept { return date8_; }
    const std::string& error_message() const noexcept { return text_; }

    bool truthy() const noexcept;
    std::string display() const;

private:
    ValueKind kind_{ValueKind::None};
    bool tf_{false};
    double number_{0.0};
    std::string text_{};
    std::int32_t date8_{0};
};

} // namespace xexpr
