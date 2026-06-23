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

void show_command_syntax(const std::string& cmd);
void show_command_help(const std::string& cmd);

} // namespace cli::cmdout
