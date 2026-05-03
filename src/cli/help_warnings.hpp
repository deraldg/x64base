#pragma once

#include <string>
#include "xbase_error_codes.hpp"

namespace dottalk::help {

bool show_warning_topic(const std::string& term);
void print_warning_help(xbase::error::code ec);

} // namespace dottalk::help
