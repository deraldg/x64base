#include "message_catalog.hpp"

namespace dottalk::msg {

std::string text(Code code)
{
    switch (code) {
    case Code::UnknownCommand: return "Unknown command";
    case Code::MissingArgument: return "Missing required argument";
    case Code::InvalidSyntax: return "Invalid command syntax";
    case Code::NotFound: return "Not found";
    case Code::IndexNotSet: return "No active index";
    case Code::InternalError: return "Internal error";
    case Code::ExpectedPositiveRecordNumber:
        return "expected a positive record number";
    case Code::AreaQualifierNotSupportedYet:
        return "'IN <alias>' not supported yet (SELECT the area, then GO ...)";
    case Code::UnrecognizedCommandForm:
        return "unrecognized form";
    }
    return "Unknown message";
}

} // namespace dottalk::msg
