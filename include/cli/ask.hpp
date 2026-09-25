// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: the ASK value type and the one console renderer that answers it
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: experimental

#pragma once

#include <string>
#include <vector>

// AN ASK IS A QUESTION THE ENGINE NEEDS A PERSON TO ANSWER.
//
// R147 ruled the mechanism: the engine emits a structured prompt event and a
// driver answers with a TOKEN. Owner ruling (3) of 2026-09-25 -- "as much as
// possible code is unified" -- puts the CONSOLE behind the same door, so
// keystroke parsing lives in exactly one place instead of the three that
// disagreed (OI-041: `yellow` consented to an index rebuild, a leading space
// consented to a commit).
//
// TRANSPORT IS DEFERRED BY RULING (4) AND NOTHING HERE DECIDES IT. This header
// is the in-process shape only: one installed renderer, called directly. When
// the wire format is ruled, a second driver implements the same Answer.
//
// KEYS ARE DECLARED, NEVER INFERRED -- owner ruling, 2026-09-25. The four-token
// dirty ask made this necessary: COMMIT and CANCEL both begin with C, so no
// prefix rule can resolve `c`. Declaring the key also means the bridge's modal
// and the console agree BY CONSTRUCTION rather than by separately implementing
// the same inference.

namespace cli::ask {

enum class Kind { Choice, Entry };

struct Option {
    const char* token = nullptr;  // the reply, e.g. "COMMIT". ASCII, uppercase.
    char        key   = '\0';     // the declared accelerator, e.g. 'C'.
    const char* label = nullptr;  // display text; falls back to token.
};

struct Ask {
    Kind kind = Kind::Choice;

    // The question, WITHOUT decoration. The renderer derives "(y/N)" or the
    // key list from `options` and `on_empty`, which is the whole point: every
    // call site used to hand-write its own suffix.
    std::string prompt;

    std::vector<Option> options;   // Kind::Choice

    // TWO DEFAULTS, BECAUSE THE TREE ALREADY HAS TWO AND THEY DIFFER.
    // Measured in dirty_prompt.cpp before the unification: a bare Enter meant
    // NO (cancel the operation), while the suppressed/unattended path returned
    // true -- PROCEED WITHOUT COMMITTING. Owner ruling (2) of 2026-09-25 keeps
    // that unattended outcome as its own token, so one field cannot carry both.
    std::string on_empty;         // bare Enter at a live console
    std::string when_unattended;  // no console, or prompts suppressed

    // Kind::Entry. These three are not a wish list: app_simple_browser.cpp:857
    // already prints all three, so a modal can only render that prompt
    // faithfully if the ask carries them.
    std::string field;
    std::string type;
    std::string current;
};

struct Answer {
    std::string token;         // Kind::Choice
    std::string value;         // Kind::Entry
    bool from_console = false; // false => resolved by when_unattended
};

// Is there a person who could answer? This is the capability R147 recorded as
// absent -- "nothing can ask whether it has a console". It is answered here at
// its smallest useful size: a terminal check on stdin.
bool console_available();

// Ask, or resolve to `when_unattended` when nobody can answer. An unrecognised
// reply RE-ASKS (owner ruling, 2026-09-25): neither of the behaviours it
// replaces is defensible at a prompt that may commit or discard data. The loop
// ends on EOF, which resolves to `when_unattended` -- so a redirected stream
// cannot be consumed indefinitely.
Answer ask(const Ask& a);

} // namespace cli::ask
