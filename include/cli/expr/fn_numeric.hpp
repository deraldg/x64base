#pragma once

#include <cstddef>

namespace dottalk::expr {

struct BuiltinFnSpec;

const BuiltinFnSpec* numeric_fn_specs();
std::size_t numeric_fn_specs_count();

} // namespace dottalk::expr