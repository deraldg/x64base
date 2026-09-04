// @dottalk.file v1
// subsystem: cli
// layer: header
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: supported

#pragma once

#include <string>

namespace xbase { class DbArea; }

namespace dottalk::fieldstore {

// Validate and canonicalize a textual expression result for one physical field.
// This is the same type gate used by REPLACE; SQLsel DML calls it before a
// value can enter the house table buffer. On success `stored_value` is in the
// field codec's canonical textual form.
bool validate_and_normalize(const xbase::DbArea& area,
                            int field1,
                            std::string& stored_value,
                            std::string& error);

} // namespace dottalk::fieldstore
