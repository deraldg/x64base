// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <string>
#include <string_view>

namespace dottalk::dotscript {

enum class VarNameIssue {
    None = 0,
    Empty,
    QuotedIdentifierNotSupported,
    MustStartWithLetterOrUnderscore,
    ContainsInvalidCharacter,
    ReservedControlWord,
    ReservedExpressionWord,
    ReservedCommandWord,
    ReservedScopeQualifier,
};

struct VarNameCheck {
    bool ok = false;
    VarNameIssue issue = VarNameIssue::Empty;
    std::string normalized;
    std::string message;
};

std::string uppercase_ascii(std::string_view s);

bool is_hard_reserved(std::string_view token);
bool is_expression_reserved(std::string_view token);
bool is_command_head_reserved(std::string_view token);
bool is_soft_reserved(std::string_view token);

VarNameCheck validate_var_name(std::string_view token);

} // namespace dottalk::dotscript
