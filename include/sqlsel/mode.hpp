// @dottalk.file v1
// subsystem: sqlsel
// layer: public-api
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: supported

#pragma once

#include <string_view>

namespace sqlsel {

// Session-only language mode. It deliberately owns command aliases, not value
// meaning: TupleRow types and blank/absence semantics remain mode-invariant.
enum class SessionMode {
    Native,
    Sql,
    Other
};

SessionMode session_mode() noexcept;
void set_session_mode(SessionMode mode) noexcept;
bool sql_mode() noexcept;
std::string_view session_mode_name() noexcept;

} // namespace sqlsel
