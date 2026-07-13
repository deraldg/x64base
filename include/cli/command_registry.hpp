// ============================================================================
// File: src/cli/command_registry.hpp
// Project: DotTalk++
// ----------------------------------------------------------------------------
#pragma once

#include <cstdint>
#include <exception>
#include <functional>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace xbase { class DbArea; }

namespace dli {

using Handler = std::function<void(xbase::DbArea& area, std::istringstream& args)>;

enum class CommandOrigin : std::uint8_t {
    Core = 0,
    Extension,
    Function,
};

const char* to_string(CommandOrigin origin) noexcept;

struct CommandRegistration {
    CommandOrigin origin{CommandOrigin::Core};
    bool protected_name{true};
    std::string source;
};

/**
 * Handlers may throw this to request a clean shutdown (EXIT/QUIT).
 * CommandRegistry::try_run catches it and reports exit_requested=true.
 */
struct ExitRequested final : std::exception {
    const char* what() const noexcept override { return "exit requested"; }
};

enum class RunStatus : std::uint8_t {
    Ok = 0,
    UnknownCommand,
    HandlerError,
};

struct RunResult {
    RunStatus status{RunStatus::Ok};
    bool exit_requested{false};
    std::string message; // for UnknownCommand / HandlerError
};

class CommandRegistry final {
public:
    /**
     * Historical registration path. It now means "core/built-in" and protects
     * the command name from later extension overwrite.
     */
    bool add(const std::string& name, Handler h);

    bool add_builtin(const std::string& name,
                     Handler h,
                     std::string source = {});

    bool add_extension(const std::string& name,
                       Handler h,
                       std::string source = {});

    bool add_function(const std::string& name,
                      Handler h,
                      std::string source = {});

    /**
     * Legacy contract: returns "keep shell alive".
     * Prints errors to stdout/stderr. Returns false if exit_requested.
     */
    bool run(xbase::DbArea& area,
             const std::string& normalized_key,
             std::istringstream& args);

    /**
     * UI-friendly contract: does not print.
     * - status==Ok: handler ran successfully
     * - status==UnknownCommand: no handler registered
     * - status==HandlerError: handler threw
     * - exit_requested==true: handler requested shutdown (status stays Ok)
     */
    RunResult try_run(xbase::DbArea& area,
                      const std::string& normalized_key,
                      std::istringstream& args);

    const std::unordered_map<std::string, Handler>& map() const noexcept { return map_; }
    const std::unordered_map<std::string, CommandRegistration>& registrations() const noexcept { return registrations_; }

    bool is_protected(const std::string& name) const;
    std::optional<CommandRegistration> registration_info(const std::string& name) const;

private:
    bool add_with_origin(const std::string& name,
                         Handler h,
                         CommandOrigin origin,
                         bool protect_name,
                         std::string source);

    std::unordered_map<std::string, Handler> map_;
    std::unordered_map<std::string, CommandRegistration> registrations_;
};

CommandRegistry& registry();
void register_command(const std::string& name, Handler h);
bool register_extension_command(const std::string& name, Handler h, std::string source = {});
bool register_function_command(const std::string& name, Handler h, std::string source = {});
const std::unordered_map<std::string, Handler>& map();
const std::unordered_map<std::string, CommandRegistration>& registrations();

/**
 * Quote-aware argv tokens for the currently executing command.
 * Valid only while a handler is running (inside try_run/run).
 */
const std::vector<std::string>& current_argv() noexcept;

/**
 * Raw args substring for the currently executing command (the remainder of args stream).
 * Valid only while a handler is running (inside try_run/run).
 */
const std::string& current_raw_args() noexcept;

} // namespace dli
