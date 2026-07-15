// ============================================================================
// File: src/cli/command_registry.cpp
// Project: DotTalk++
// ----------------------------------------------------------------------------
#include "cli/command_registry.hpp"

#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
#include "textio.hpp"

#include <cctype>
#include <iostream>
#include <optional>
#include <string>
#include <vector>

using xbase::DbArea;

namespace dli {

static thread_local std::vector<std::string> tl_argv;
static thread_local std::string tl_raw_args;

const std::vector<std::string>& current_argv() noexcept { return tl_argv; }
const std::string& current_raw_args() noexcept { return tl_raw_args; }

static inline void ltrim_stream(std::istringstream& iss) {
    while (iss && std::isspace(static_cast<unsigned char>(iss.peek())))
        iss.get();
}

static std::string normalize_key(std::string name)
{
    return textio::up(textio::trim(std::move(name)));
}

const char* to_string(CommandOrigin origin) noexcept
{
    switch (origin) {
        case CommandOrigin::Core: return "core";
        case CommandOrigin::Extension: return "extension";
        case CommandOrigin::Function: return "function";
    }
    return "unknown";
}

bool CommandRegistry::add(const std::string& name, Handler h)
{
    return add_builtin(name, std::move(h));
}

bool CommandRegistry::add_builtin(const std::string& name,
                                  Handler h,
                                  std::string source)
{
    return add_with_origin(name, std::move(h), CommandOrigin::Core, true, std::move(source));
}

bool CommandRegistry::add_extension(const std::string& name,
                                    Handler h,
                                    std::string source)
{
    return add_with_origin(name, std::move(h), CommandOrigin::Extension, false, std::move(source));
}

bool CommandRegistry::add_function(const std::string& name,
                                   Handler h,
                                   std::string source)
{
    return add_with_origin(name, std::move(h), CommandOrigin::Function, true, std::move(source));
}

bool CommandRegistry::add_with_origin(const std::string& name,
                                      Handler h,
                                      CommandOrigin origin,
                                      bool protect_name,
                                      std::string source)
{
    const std::string key = normalize_key(name);
    if (key.empty()) return false;

    const auto existing = registrations_.find(key);
    if (existing != registrations_.end() && existing->second.protected_name) {
        if (origin == CommandOrigin::Extension) return false;
        if (origin == CommandOrigin::Function &&
            existing->second.origin == CommandOrigin::Core) {
            return false;
        }
    }

    // Core registration is allowed to reclaim a name that an extension may have
    // registered during static initialization. This keeps built-ins protected
    // even if extension objects initialize before shell bootstrap.
    map_[key] = std::move(h);
    registrations_[key] = CommandRegistration{
        origin,
        protect_name || origin == CommandOrigin::Core,
        std::move(source)
    };
    return true;
}

bool CommandRegistry::is_protected(const std::string& name) const
{
    const auto it = registrations_.find(normalize_key(name));
    return it != registrations_.end() && it->second.protected_name;
}

std::optional<CommandRegistration>
CommandRegistry::registration_info(const std::string& name) const
{
    const auto it = registrations_.find(normalize_key(name));
    if (it == registrations_.end()) return std::nullopt;
    return it->second;
}

RunResult CommandRegistry::try_run(DbArea& area,
                                   const std::string& normalized_key,
                                   std::istringstream& args)
{
    auto it = map_.find(normalize_key(normalized_key));
    if (it == map_.end()) {
        return {
            RunStatus::UnknownCommand,
            false,
            cli::cmdout::message_text(
                dottalk::helpdata::MessageId::UnknownCommand,
                {{"command", normalized_key}})
        };
    }

    // Snapshot remaining args without consuming the stream (handlers may still parse args).
    std::string raw;
    if (auto pos = args.tellg(); pos != std::istringstream::pos_type(-1)) {
        const std::string& whole = args.str();
        const auto upos = static_cast<size_t>(pos);
        if (upos < whole.size())
            raw = whole.substr(upos);
    }

    struct Scope {
        explicit Scope(std::string raw_in) {
            tl_raw_args = std::move(raw_in);
            tl_argv = textio::tokenize(tl_raw_args);
        }
        ~Scope() noexcept {
            tl_argv.clear();
            tl_raw_args.clear();
        }
    } scope{raw};

    try {
        ltrim_stream(args);
        it->second(area, args);
        return {RunStatus::Ok, false, {}};
    } catch (const ExitRequested&) {
        return {RunStatus::Ok, true, {}};
    } catch (const std::exception& e) {
        return {RunStatus::HandlerError, false, std::string("Command error: ") + e.what()};
    } catch (...) {
        return {RunStatus::HandlerError, false, "Command error: unknown exception"};
    }
}

bool CommandRegistry::run(DbArea& area,
                          const std::string& normalized_key,
                          std::istringstream& args)
{
    const RunResult r = try_run(area, normalized_key, args);

    if (r.exit_requested)
        return false; // stop shell

    switch (r.status) {
        case RunStatus::Ok:
            return true;
        case RunStatus::UnknownCommand:
            cli::cmdout::print_line(r.message);
            return true;
        case RunStatus::HandlerError:
            std::cerr << r.message << "\n";
            return true;
    }
    return true;
}

// Singleton instance
static CommandRegistry& instance() {
    static CommandRegistry reg;
    return reg;
}

CommandRegistry& registry() { return instance(); }

void register_command(const std::string& name, dli::Handler h) {
    registry().add(name, std::move(h));
}

bool register_extension_command(const std::string& name, dli::Handler h, std::string source) {
    return registry().add_extension(name, std::move(h), std::move(source));
}

bool register_function_command(const std::string& name, dli::Handler h, std::string source) {
    return registry().add_function(name, std::move(h), std::move(source));
}

const std::unordered_map<std::string, dli::Handler>& map() {
    return registry().map();
}

const std::unordered_map<std::string, CommandRegistration>& registrations() {
    return registry().registrations();
}

} // namespace dli
