// cmd_manstar_candidate.h
// MDO-274E candidate only - no source-tree apply and no command registration.
#pragma once

#include <iosfwd>
#include <string>

namespace dottalk::manstar_candidate {
int print_usage(std::ostream& out);
int print_status(std::ostream& out);
int print_tables(std::ostream& out);
int dispatch_candidate(const std::string& subcommand, std::ostream& out);
}
