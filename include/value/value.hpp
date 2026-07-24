#pragma once

#include <cstdint>
#include <string>
#include <variant>
#include <vector>

#include "memo/memo_ref.hpp"

namespace dottalk::value {

enum class ValueState : std::uint8_t {
    Present,
    Null,
    Blank,
    Invalid,
    Unavailable,
    Error
};

enum class ValueKind : std::uint8_t {
    Unspecified,
    Logical,
    Integer,
    UnsignedInteger,
    Decimal,
    Floating,
    Character,
    Date,
    DateTime,
    MemoReference,
    Custom,
    ArrayReference
};

struct ExactDecimal final {
    bool negative{false};
    std::string digits{"0"};
    std::uint32_t scale{0};

    static bool parse(const std::string& text,
                      ExactDecimal& out,
                      std::string* error = nullptr);

    [[nodiscard]] std::string canonical_text() const;
    [[nodiscard]] bool equivalent(const ExactDecimal& other) const;
};

struct DateValue final {
    std::int32_t year{0};
    std::uint8_t month{0};
    std::uint8_t day{0};

    [[nodiscard]] bool valid() const noexcept;
};

struct DateTimeValue final {
    DateValue date;
    std::uint8_t hour{0};
    std::uint8_t minute{0};
    std::uint8_t second{0};
    std::uint16_t millisecond{0};

    [[nodiscard]] bool valid() const noexcept;
};

struct CustomValue final {
    char type_code{0};
    std::string registry_name;
    std::string canonical_text;
};

struct ArrayReference final {
    std::uint64_t object_id{0};
    std::uint64_t generation{0};
    std::vector<std::uint64_t> index_path;
};

using ValuePayload = std::variant<
    std::monostate,
    bool,
    std::int64_t,
    std::uint64_t,
    ExactDecimal,
    double,
    std::string,
    DateValue,
    DateTimeValue,
    dottalk::memo::MemoRef,
    CustomValue,
    ArrayReference
>;

class Value final {
public:
    Value() = default;

    [[nodiscard]] ValueState state() const noexcept { return state_; }
    [[nodiscard]] ValueKind kind() const noexcept { return kind_; }
    [[nodiscard]] const ValuePayload& payload() const noexcept { return payload_; }
    [[nodiscard]] const std::string& diagnostic() const noexcept { return diagnostic_; }

    static Value logical(bool value);
    static Value integer(std::int64_t value);
    static Value unsigned_integer(std::uint64_t value);
    static Value decimal(ExactDecimal value);
    static Value floating(double value);
    static Value character(std::string value);
    static Value date(DateValue value);
    static Value datetime(DateTimeValue value);
    static Value memo_reference(dottalk::memo::MemoRef value);
    static Value custom(CustomValue value);
    static Value array_reference(ArrayReference value);

    static Value null(ValueKind expected = ValueKind::Unspecified);
    static Value blank(ValueKind expected);
    static Value invalid(ValueKind expected, std::string diagnostic);
    static Value unavailable(ValueKind expected, std::string diagnostic);
    static Value error(std::string diagnostic);

private:
    Value(ValueState state,
          ValueKind kind,
          ValuePayload payload,
          std::string diagnostic = {});

    ValueState state_{ValueState::Unavailable};
    ValueKind kind_{ValueKind::Unspecified};
    ValuePayload payload_{};
    std::string diagnostic_;
};

} // namespace dottalk::value
