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

// CORRECTED 2026-09-25: this said "Phase 0: these return true unconditionally.
// Later phases will consult TABLE state and prompt when needed." Both later
// phases landed -- these DO consult dottalk::table state and DO prompt.
//
// Returns TRUE to mean PROCEED and false to mean the caller must abandon the
// operation. True is also what a suppressed prompt returns (cli::prompt), and
// that path proceeds WITHOUT committing -- the outcome a person at the keyboard
// cannot currently choose. OI-041, and the owner's four-button ruling.

bool maybe_prompt_area(xbase::DbArea& area, const char* context);
bool maybe_prompt_all(xbase::XBaseEngine& eng, const char* context);

} // namespace dottalk::dirty
