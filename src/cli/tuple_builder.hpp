// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/tuple_builder.hpp
#pragma once

#include <string>

#include "tuple_types.hpp"

namespace dottalk {

// Result wrapper so callers can handle errors without printing.
struct TupleBuildResult {
    bool ok = false;
    std::string error;            // if !ok
    TupleRow row;                 // if ok
};

TupleBuildResult build_tuple_from_spec(const std::string& spec, const TupleBuildOptions& opt);
TupleBuildResult build_tuple_default(const TupleBuildOptions& opt);

} // namespace dottalk
