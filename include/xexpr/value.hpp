#pragma once

#include <cstdint>
#include <memory>
#include <string>

// The array runtime core (DOTSCRIPT-ARRAYS lane, AIF-038). Only the handle type is
// needed here; value.hpp forward-declares it so the widely-included value header
// stays lightweight. Consumers that actually inspect array contents include
// "xexpr/array_value.hpp". shared_ptr of an incomplete type is well-formed for
// copy/move/destroy (the deleter is type-erased at construction).
namespace dottalk::array {
struct ArrayValue;
using ArrayRef = std::shared_ptr<ArrayValue>;
} // namespace dottalk::array

namespace xexpr {

enum class ValueKind {
    None,
    Bool,
    Number,
    String,
    Date,
    Error,
    Array   // DOTSCRIPT-ARRAYS (AIF-038): payload is a shared ArrayRef
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
    static Value array(dottalk::array::ArrayRef a);

    ValueKind kind() const noexcept { return kind_; }

    bool is_none() const noexcept { return kind_ == ValueKind::None; }
    bool is_bool() const noexcept { return kind_ == ValueKind::Bool; }
    bool is_number() const noexcept { return kind_ == ValueKind::Number; }
    bool is_string() const noexcept { return kind_ == ValueKind::String; }
    bool is_date() const noexcept { return kind_ == ValueKind::Date; }
    bool is_error() const noexcept { return kind_ == ValueKind::Error; }
    bool is_array() const noexcept { return kind_ == ValueKind::Array; }

    bool as_bool() const noexcept { return tf_; }
    double as_number() const noexcept { return number_; }
    const std::string& as_string() const noexcept { return text_; }
    std::int32_t as_date8() const noexcept { return date8_; }
    const std::string& error_message() const noexcept { return text_; }
    const dottalk::array::ArrayRef& as_array() const noexcept { return arr_; }

    bool truthy() const noexcept;
    std::string display() const;

private:
    ValueKind kind_{ValueKind::None};
    bool tf_{false};
    double number_{0.0};
    std::string text_{};
    std::int32_t date8_{0};
    dottalk::array::ArrayRef arr_{};
};

} // namespace xexpr
