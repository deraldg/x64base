#pragma once

#include <string>
#include "xbase_error_codes.hpp"

namespace cli::cmdout {

void print_line(const std::string& s);

void print_info(const char* cmd, const std::string& text);
void print_warning(const char* cmd, xbase::error::code ec);
void print_error(const char* cmd, xbase::error::code ec);
void print_note(const char* cmd, const std::string& text);

void show_command_syntax(const std::string& cmd);
void show_command_help(const std::string& cmd);

} // namespace cli::cmdout
