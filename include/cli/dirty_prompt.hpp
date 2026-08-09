// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

namespace xbase { class DbArea; class XBaseEngine; }

namespace dottalk::dirty {

// Phase 0: these return true unconditionally.
// Later phases will consult TABLE state and prompt when needed.

bool maybe_prompt_area(xbase::DbArea& area, const char* context);
bool maybe_prompt_all(xbase::XBaseEngine& eng, const char* context);

} // namespace dottalk::dirty
