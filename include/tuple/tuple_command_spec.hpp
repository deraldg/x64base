#pragma once

#include <cstddef>
#include <iosfwd>
#include <string>

namespace dottalk::tupleaugment {

struct TupleCommandSpec {
    // TUPEXPORT-specific
    std::string format;      // CSV now; JSON/SQLITE later
    std::string path;        // destination/source path where applicable

    // Shared tuple command surface
    std::string tuple_spec{"*"};
    std::string for_expr;

    bool help{false};
    bool trace{false};
    bool all{false};
    bool include_deleted{false};
    bool only_deleted{false};

    std::size_t max_issues{50};
};

TupleCommandSpec parse_tuple_export_spec(std::istream& in);
TupleCommandSpec parse_tuple_validate_spec(std::istream& in);

std::string tuple_spec_trim(std::string s);
std::string tuple_spec_upper(std::string s);

} // namespace dottalk::tupleaugment
