// @dottalk.file v1
// subsystem: sqlsel
// layer: engine
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: supported

#include "sqlsel/mode.hpp"

#include <atomic>

namespace sqlsel {
namespace {

std::atomic<SessionMode> current_mode{SessionMode::Native};

} // namespace

SessionMode session_mode() noexcept {
    return current_mode.load(std::memory_order_relaxed);
}

void set_session_mode(SessionMode mode) noexcept {
    current_mode.store(mode, std::memory_order_relaxed);
}

bool sql_mode() noexcept {
    return session_mode() == SessionMode::Sql;
}

std::string_view session_mode_name() noexcept {
    switch (session_mode()) {
        case SessionMode::Sql: return "SQL";
        case SessionMode::Other: return "OTHER";
        case SessionMode::Native: return "NATIVE";
    }
    return "NATIVE";
}

} // namespace sqlsel
