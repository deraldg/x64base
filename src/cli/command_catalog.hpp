#pragma once
#include "command_doc.hpp"
#include <string>

namespace dottalk::doc {

const CommandDoc* get(const std::string& command);

} // namespace dottalk::doc
