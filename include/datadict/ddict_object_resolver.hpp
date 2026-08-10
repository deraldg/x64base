// @dottalk.file v1
// subsystem: datadict
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <string>
#include <unordered_map>
#include <vector>
#include "datadict/ddict_dbf_reader.hpp"
namespace dottalk::datadict {
const DDictRow* resolve_object(const std::vector<DDictRow>& objects, const std::string& token);
std::unordered_map<std::string, const DDictRow*> object_index(const std::vector<DDictRow>& objects);
} // namespace dottalk::datadict
