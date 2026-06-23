#pragma once
#include <string>
#include <vector>

namespace dottalk::msg {

enum class Code {
    UnknownCommand,
    MissingArgument,
    InvalidSyntax,
    NotFound,
    IndexNotSet,
    InternalError,
    ExpectedPositiveRecordNumber,
    AreaQualifierNotSupportedYet,
    UnrecognizedCommandForm
};

std::string normalize_locale(const std::string& locale);
std::vector<std::string> available_locales();
bool is_supported_locale(const std::string& locale);

// Returns text in the active SET LANGUAGE / SET LOCALE setting.
std::string text(Code code);

// Returns text in a specific locale, with fallback to en-US.
std::string text(Code code, const std::string& locale);

} // namespace dottalk::msg
