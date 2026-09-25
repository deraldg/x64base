// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/dirty_prompt.cpp
#include "workarea_util.hpp"
#include "cli/dirty_prompt.hpp"

#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

#include "cli/ask.hpp"
#include "cli/prompt_policy.hpp"
#include "cli/table_state.hpp"
#include "xbase.hpp"

// Defined in src/cli/cmd_commit.cpp
extern void cmd_COMMIT(xbase::DbArea& A, std::istringstream& in);

namespace dottalk { namespace dirty {

// The suppression flag moved to cli::prompt on 2026-09-25 -- it answers a
// process-wide question and is not this file's property. See
// include/cli/prompt_policy.hpp.

extern "C" xbase::XBaseEngine* shell_engine();

// Defined in src/cli/cmd_commit.cpp (global function)
void cmd_COMMIT(xbase::DbArea& A, std::istringstream& in);

static inline std::string to_upper_copy(std::string s) {
    for (std::size_t i = 0; i < s.size(); ++i) {
        s[i] = (char)std::toupper((unsigned char)s[i]);
    }
    return s;
}

// ONE RENDERER, ONE PARSER (owner ruling (3), 2026-09-25). This used to be
// `parse_yes_default_no()` -- trim, lowercase, accept only "y" or "yes" --
// which disagreed with the two copies in cmd_rebuild.cpp and cmd_reindex.cpp:
// `yellow` consented there and not here, a leading space consented here and not
// there. Both are gone; cli::ask owns the keystrokes now.
//
// THE PRINTED TEXT IS UNCHANGED. cli::ask derives " (y/N) " from a two-option
// YES/NO ask whose bare-Enter answer is NO, which is byte-for-byte what this
// function printed.
static inline bool prompt_commit_yn(const std::string& scopeLabel) {
    cli::ask::Ask a;
    a.prompt = "TABLE: uncommitted changes detected (" + scopeLabel + "). COMMIT changes?";
    a.options = { {"YES", 'Y', "yes"}, {"NO", 'N', "no"} };
    a.on_empty = "NO";
    // NO, not PROCEED: the four-token ask of ruling (2) is a later step. What
    // changes here is that an unattended caller RESOLVES rather than reading --
    // `--script` is stdin redirection, so the old getline ate the next line of
    // the script as its answer. Cancelling deterministically is both safer and
    // what EOF already did.
    a.when_unattended = "NO";
    return cli::ask::ask(a).token == "YES";
}

static bool commit_area0(int area0) {
    xbase::XBaseEngine* eng = nullptr;
    try { eng = shell_engine(); } catch (...) { eng = nullptr; }
    if (!eng) {
        std::cout << "COMMIT: shell engine unavailable.\n";
        return false;
    }

    try {
        xbase::DbArea& A = eng->area(area0);
        std::istringstream empty;

        // RAII, not save/restore: the manual version restored on the NEXT LINE,
        // so a throwing cmd_COMMIT skipped it and left suppression on for the
        // life of the process -- silently, because the catch below reports only
        // "COMMIT failed (exception)".
        {
            cli::prompt::SuppressScope guard;
            ::cmd_COMMIT(A, empty);   // <-- global call
        }

        if (dottalk::table::is_enabled(area0) && dottalk::table::is_dirty(area0)) {
            std::cout << "COMMIT failed (area still dirty).\n";
            return false;
        }
        return true;
    } catch (...) {
        std::cout << "COMMIT failed (exception).\n";
        return false;
    }
}

static bool commit_all_dirty() {
    xbase::XBaseEngine* eng = nullptr;
    try { eng = shell_engine(); } catch (...) { eng = nullptr; }
    if (!eng) {
        std::cout << "COMMIT: shell engine unavailable.\n";
        return false;
    }

    bool ok = true;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (dottalk::table::is_enabled(i) && dottalk::table::is_dirty(i)) {
            ok = commit_area0(i) && ok;
        }
    }
    return ok;
}

static int area_index_from_ref(xbase::DbArea& areaRef) {
    // AIF-120 I1.1 sweep completed 2026-08-22 (AIF-078 GUI design sec 8, O5).
    // This was a MAX_AREA pointer-identity scan. The engine stamps the same
    // number into DbArea::_engine_slot once at construction, so the scan
    // recovered a value the area already carried. Body only -- the signature
    // and every call site are unchanged, which is how I1.1 did it.
    return cli::slot_of_area(&areaRef);
}

static bool is_quit_like(const std::string& opLabel) {
    const std::string u = to_upper_copy(opLabel);
    return (u == "QUIT" || u == "EXIT");
}

bool maybe_prompt_area(const int area0, const std::string& opLabel) {
    if (cli::prompt::suppressed()) return true;
    if (!dottalk::table::is_enabled(area0) || !dottalk::table::is_dirty(area0)) return true;

    if (!prompt_commit_yn(std::string("area ") + std::to_string(area0))) return false;

    const bool ok = commit_area0(area0);
    if (ok && is_quit_like(opLabel)) cli::prompt::set_suppressed(true);
    return ok;
}

bool maybe_prompt_area(xbase::DbArea& areaRef, const char* opLabel) {
    if (cli::prompt::suppressed()) return true;

    const std::string label = opLabel ? std::string(opLabel) : std::string();
    const int idx = area_index_from_ref(areaRef);
    if (idx >= 0) return maybe_prompt_area(idx, label);

    // Fallback: prompt once, commit all dirty.
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (dottalk::table::is_enabled(i) && dottalk::table::is_dirty(i)) {
            if (!prompt_commit_yn("unknown area (index unavailable)")) return false;
            const bool ok = commit_all_dirty();
            if (ok && is_quit_like(label)) cli::prompt::set_suppressed(true);
            return ok;
        }
    }
    return true;
}

bool maybe_prompt_all(xbase::XBaseEngine& eng, const std::string& opLabel) {
    (void)eng;

    if (cli::prompt::suppressed()) return true;

    int dirtyCount = 0;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (dottalk::table::is_enabled(i) && dottalk::table::is_dirty(i)) ++dirtyCount;
    }
    if (dirtyCount == 0) return true;

    if (!prompt_commit_yn(std::string("all areas (") + std::to_string(dirtyCount) + " dirty)")) return false;

    const bool ok = commit_all_dirty();
    if (ok && is_quit_like(opLabel)) cli::prompt::set_suppressed(true);
    return ok;
}

bool maybe_prompt_all(xbase::XBaseEngine& eng, const char* opLabel) {
    return maybe_prompt_all(eng, opLabel ? std::string(opLabel) : std::string());
}

}} // namespace dottalk::dirty
