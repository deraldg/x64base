// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <string>

namespace xbase { class DbArea; }

namespace dottalk::browse::format {

// Pretty printer with fixed-width columns by field type.
std::string tuple_pretty(::xbase::DbArea& db);

// Raw concatenation (legacy behavior).
std::string tuple_raw(::xbase::DbArea& db);

} // namespace dottalk::browse::format
