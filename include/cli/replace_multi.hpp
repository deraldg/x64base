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

namespace xbase { class DbArea; }

struct FieldUpdate {
    std::string name;
    std::string value; // raw or normalized text; validation happens in the command
};

// Returns true on success; on failure fills *error (if not null)
bool cmd_REPLACE_MULTI(xbase::DbArea&, const std::vector<FieldUpdate>& updates, std::string* error = nullptr);



