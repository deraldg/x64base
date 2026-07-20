#pragma once

#include <string>
#include <unordered_map>

#include "xbase_error_codes.hpp"
#include "help/helpdata_messages.hpp"

namespace cli::cmdout {

void print_line(const std::string& s);

std::string message_text(
    dottalk::helpdata::MessageId id,
    const std::unordered_map<std::string, std::string>& vars = {});

void print_message(
    dottalk::helpdata::MessageId id,
    const std::unordered_map<std::string, std::string>& vars = {});

void print_prefixed_message(
    const char* cmd,
    dottalk::helpdata::MessageId id,
    const std::unordered_map<std::string, std::string>& vars = {});

void print_info(const char* cmd, const std::string& text);
void print_warning(const char* cmd, xbase::error::code ec);
void print_error(const char* cmd, xbase::error::code ec);
void print_note(const char* cmd, const std::string& text);

// Emit a localized diagnostic AND record the canonical error/warning code so
// ERROR_STATUS and (future) SET ERRORSTOP observe the failure. One visible
// localized line (the message catalog text); the English to_string(code) is
// never shown to the user — it only appears inside ERROR_STATUS's own Message
// field. Use these instead of print_message at fail/warn sites that must set
// error state.
void emit_error(
    dottalk::helpdata::MessageId id,
    xbase::error::code ec,
    const std::unordered_map<std::string, std::string>& vars = {});

void emit_warning(
    dottalk::helpdata::MessageId id,
    xbase::error::code ec,
    const std::unordered_map<std::string, std::string>& vars = {});

void show_command_syntax(const std::string& cmd);
void show_command_help(const std::string& cmd);

} // namespace cli::cmdout
