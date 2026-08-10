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
#include <cstdint>
#include <sstream>

#include "xbase.hpp"

bool dottalk_append_blank_raw(xbase::DbArea& A, std::uint32_t& rn);
bool dottalk_append_blank_raw_locked(xbase::DbArea& A, std::uint32_t& rn);

bool dottalk_append_many_raw(xbase::DbArea& A, std::size_t count);
bool dottalk_append_many_core(xbase::DbArea& A, std::size_t count);

bool dottalk_append_blank_core(xbase::DbArea& A, std::istringstream& iss);