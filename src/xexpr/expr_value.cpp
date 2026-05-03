#include "xexpr/value.hpp"

#include <cmath>
#include <iomanip>
#include <sstream>
#include <utility>

namespace xexpr {

Value Value::none() {
    return Value{};
}

Value Value::logical(bool v) {
    Value out;
    out.kind_ = ValueKind::Bool;
    out.tf_ = v;
    return out;
}

Value Value::number(double v) {
    Value out;
    out.kind_ = ValueKind::Number;
    out.number_ = v;
    return out;
}

Value Value::string(std::string v) {
    Value out;
    out.kind_ = ValueKind::String;
    out.text_ = std::move(v);
    return out;
}

Value Value::date(std::int32_t yyyymmdd) {
    Value out;
    out.kind_ = ValueKind::Date;
    out.date8_ = yyyymmdd;
    return out;
}

Value Value::error(std::string message) {
    Value out;
    out.kind_ = ValueKind::Error;
    out.text_ = std::move(message);
    return out;
}

bool Value::truthy() const noexcept {
    switch (kind_) {
        case ValueKind::Bool:   return tf_;
        case ValueKind::Number: return number_ != 0.0;
        case ValueKind::String: return !text_.empty();
        case ValueKind::Date:   return date8_ != 0;
        default:                return false;
    }
}

std::string Value::display() const {
    switch (kind_) {
        case ValueKind::Bool:
            return tf_ ? ".T." : ".F.";

        case ValueKind::Number: {
            const double iv = std::floor(number_);
            if (std::fabs(number_ - iv) < 1e-9) {
                std::ostringstream o;
                o << static_cast<long long>(iv);
                return o.str();
            }

            std::ostringstream o;
            o << std::fixed << std::setprecision(10) << number_;
            std::string s = o.str();
            while (!s.empty() && s.find('.') != std::string::npos && s.back() == '0') s.pop_back();
            if (!s.empty() && s.back() == '.') s.pop_back();
            return s.empty() ? "0" : s;
        }

        case ValueKind::String:
            return text_;

        case ValueKind::Date:
            return std::to_string(date8_);

        case ValueKind::Error:
            return text_.empty() ? "expression error" : text_;

        case ValueKind::None:
        default:
            return ".F.";
    }
}

} // namespace xexpr
