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
#include <vector>
#include <cstdlib>
#include <algorithm>
#include "xbase.hpp"

namespace predicates {

int field_index_ci(const xbase::DbArea& a, const std::string& name);
bool eval(const xbase::DbArea& a,
          const std::string& fld,
          const std::string& op,
          const std::string& val);

} // namespace predicates



