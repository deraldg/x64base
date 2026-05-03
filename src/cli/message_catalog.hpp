#pragma once
#include <string>

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

std::string text(Code code);

} // namespace dottalk::msg
