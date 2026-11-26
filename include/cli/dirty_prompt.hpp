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

// S4 (OI-041): the commit-before-index gate. cmd_rebuild.cpp and cmd_reindex.cpp
// each carried a private copy of this -- 621 normalized characters apiece,
// identical except for the two MessageId names they printed. The MECHANISM is
// here; the MESSAGES stay with the caller, so this header does not have to pull
// a help header into cli.
enum class CleanOrCommit {
    AlreadyClean,          // nothing was dirty -- proceed
    Committed,             // the user agreed, COMMIT ran, the area came clean -- proceed
    DeclinedByUser,        // the user said no -- abandon
    StillDirtyAfterCommit  // COMMIT ran and left the area dirty -- abandon
};

CleanOrCommit ensure_clean_or_commit(xbase::DbArea& area, int area0, const char* verb);

} // namespace dottalk::dirty
