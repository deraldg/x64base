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
#include <filesystem>

namespace xbase { class DbArea; class XBaseEngine; }

// Non-owning engine binding for a prompt or a serialized embedded host.
// The host must unbind before destroying its engine; commands share this engine.
void shell_bind_engine(xbase::XBaseEngine* engine) noexcept;

// Dispatch a single command line through the registered CLI.
// Returns true if a command handler was found and executed, false otherwise.
bool shell_dispatch(xbase::DbArea& area, const std::string& line);

// Public API expected by dispatch_shim + tests.
// This must be a real (linkable) symbol, not just an inline wrapper.
bool shell_dispatch_line(xbase::DbArea& area, const std::string& line);

// Canonical shell execution entry: preprocesses one raw line and dispatches it.
// This is the shared path for prompt, DOTSCRIPT, TEST, and helper replays.
bool shell_execute_line(xbase::DbArea& area, const std::string& rawLine);

// Legacy compatibility for older callers that used a void helper.
// Kept as a different name to avoid return-type conflicts.
inline void shell_dispatch_line_void(xbase::DbArea& area, const std::string& line) {
    (void)shell_dispatch_line(area, line);
}

// DotScript/Test script execution context helpers.
// These support one-level subscript composition with relative path resolution.
bool shell_script_push(const std::filesystem::path& scriptFile, bool as_subscript, std::string* err = nullptr);
void shell_script_pop();
bool shell_script_active();
bool shell_script_in_subscript();
std::filesystem::path shell_script_current_dir();
// Absolute paths are exact. Outside a script, bare names use SCRIPTS and
// qualified relative paths use DATA. Inside a script, relatives use its
// directory. A missing extension means .dts; there is no directory fallback.
std::filesystem::path shell_resolve_script_path(const std::string& token);
