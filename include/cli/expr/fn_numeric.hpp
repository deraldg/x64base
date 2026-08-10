// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <cstddef>

namespace dottalk::expr {

struct BuiltinFnSpec;

const BuiltinFnSpec* numeric_fn_specs();
std::size_t numeric_fn_specs_count();

} // namespace dottalk::expr