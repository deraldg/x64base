#pragma once

#include <string>
#include "xbase_error_codes.hpp"

namespace dottalk::help {

bool show_error_topic(const std::string& term);
void print_error_help(xbase::error::code ec);

} // namespace dottalk::help
