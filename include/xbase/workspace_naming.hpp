// @dottalk.file v1
// subsystem: xbase
// layer: header
// owns:
// project: project.x64base.runtime
// lane: application-ui-dsl
// owner: member.derald
// status: supported

#pragma once
// @dottalk.contract
// file: include/xbase/workspace_naming.hpp
// subsystem: xbase
// role: the workspace name a DIRECTORY implies
// authority: canonical-header-contract
// mutation: token-authorized
//
// TOKEN for the 2026-08-26 creation: R128, owner ruling of the same day --
// "open should be additive", "we can also open two dir into two workspaces
// too" -- plus his answer that the name is the directory LEAF with AS to
// override.

// WHY THIS IS A HEADER AND NOT A FUNCTION IN cmd_workspace.cpp.
//
// TWO SURFACES ASK THE SAME QUESTION. WORKSPACE OPEN <dir> in the CLI and the
// GUI's mirror of that command both have to turn a directory into a workspace
// name, and they cannot share code the ordinary way: R122 ruled that src/gui
// does not depend on src/cli, and the GUI reaches the engine by SPAWNING a
// dottalkpp and parsing its stdout. So a policy written once in the CLI would
// have to be written a second time in the GUI -- and two spellings of one rule
// is R5's defect, the shape where one question has two answers depending on
// which surface you asked.
//
// The placement follows R124 exactly: a neutral home both targets ALREADY
// link. src/xbase globs its sources and dottalk_gui_core links xbase PUBLIC,
// so neither consumer needs a build change, and the cherry-pick list the GUI
// maintains by hand does not grow by another entry.
//
// It depends on <filesystem> and <string> and nothing else -- no engine, no
// shell, no membership table. It is a naming rule, not a placement policy;
// the placement policy is area_alloc.hpp next door.

#include <filesystem>
#include <string>

namespace xbase::workspace {

// WS_NAME is C(32) in WORKSPACES.dbf. The limit lives here rather than at the
// call sites so that a widened field is one edit, and so a reader asking "why
// 32" finds the answer beside the number.
inline constexpr std::size_t kMaxWorkspaceNameChars = 32;

// The workspace name a directory implies, or empty with `err` set.
//
// THE LEAF, NOT A PATH SLUG. The leaf is what a person reads in a column, and
// a slug of any real path does not fit in 32 characters anyway. The cost is
// that two directories can imply one name; that collision is REFUSED by the
// caller rather than papered over with a suffix, because two workspaces on one
// name is the ambiguity a unique name exists to prevent.
//
// A LEAF THAT DOES NOT FIT IS REFUSED, NEVER TRUNCATED. A truncated name
// silently collides with every other name sharing its first 32 characters, and
// the name is the key -- so truncation converts a loud, fixable refusal into a
// quiet wrong answer.
inline std::string name_for_directory(const std::filesystem::path& dir,
                                      std::string& err) {
    err.clear();

    // A trailing separator makes filename() empty, which would otherwise
    // report "cannot derive a name" for a perfectly ordinary path typed with
    // a slash on the end.
    std::filesystem::path d = dir;
    std::string leaf = d.filename().string();
    if (leaf.empty()) leaf = d.parent_path().filename().string();

    if (leaf.empty()) {
        err = "cannot derive a workspace name from that path; name it with AS <name>.";
        return {};
    }
    if (leaf.size() > kMaxWorkspaceNameChars) {
        err = "'" + leaf + "' is longer than WS_NAME's "
            + std::to_string(kMaxWorkspaceNameChars)
            + " characters. Name it with AS <name> -- a truncated name is a "
              "collision waiting to happen, so it is refused rather than shortened.";
        return {};
    }
    return leaf;
}

}  // namespace xbase::workspace
