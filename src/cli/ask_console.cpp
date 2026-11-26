// @dottalk.file v1
// subsystem: cli
// layer: support
// owns: the single console renderer for ASK
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: experimental

#include "cli/ask.hpp"
#include "cli/prompt_policy.hpp"

#include <cctype>
#include <cstdio>
#include <iostream>
#include <string>

#if defined(_WIN32)
  #include <io.h>
  #define DOTTALK_ISATTY _isatty
  #define DOTTALK_FILENO _fileno
#else
  #include <unistd.h>
  #define DOTTALK_ISATTY isatty
  #define DOTTALK_FILENO fileno
#endif

namespace cli::ask {

namespace {

std::string trim_copy(std::string s) {
    auto sp = [](unsigned char c) { return std::isspace(c) != 0; };
    while (!s.empty() && sp(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && sp(static_cast<unsigned char>(s.back())))  s.pop_back();
    return s;
}

std::string upper_copy(std::string s) {
    for (auto& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

bool is_yes_no(const Ask& a) {
    if (a.options.size() != 2) return false;
    const std::string first  = upper_copy(a.options[0].token ? a.options[0].token : "");
    const std::string second = upper_copy(a.options[1].token ? a.options[1].token : "");
    return (first == "YES" && second == "NO");
}

// THE DECORATION IS DERIVED, AND THAT DERIVATION IS THE UNIFICATION.
// Every call site used to hand-write its own suffix. For a two-option YES/NO
// ask this reproduces the existing text BYTE FOR BYTE -- " (y/N) " when a bare
// Enter means NO, " (Y/n) " when it means YES -- so routing REBUILD, REINDEX
// and the dirty confirm through here changes no console output at all.
void render(const Ask& a) {
    std::cout << a.prompt;
    if (is_yes_no(a)) {
        const bool default_no = (upper_copy(a.on_empty) != "YES");
        std::cout << (default_no ? " (y/N) " : " (Y/n) ");
        return;
    }
    // "[C] COMMIT  [R] ROLLBACK  [P] PROCEED  [X] CANCEL "
    // The key is shown in brackets beside the whole token rather than spliced
    // into it: "[C]ommit" reads well for COMMIT and badly for CANCEL, and the
    // two are the pair that must not be confused.
    for (std::size_t i = 0; i < a.options.size(); ++i) {
        const Option& o = a.options[i];
        std::cout << (i ? "  [" : " [") << o.key << "] "
                  << (o.label ? o.label : (o.token ? o.token : ""));
    }
    std::cout << ' ';
}

// Declared keys first, then the whole token. Nothing is inferred from a prefix:
// COMMIT and CANCEL share a first letter, which is why the keys are declared.
const Option* match(const Ask& a, const std::string& raw) {
    const std::string t = upper_copy(trim_copy(raw));
    if (t.empty()) return nullptr;
    if (t.size() == 1) {
        for (const auto& o : a.options) {
            if (std::toupper(static_cast<unsigned char>(o.key)) == static_cast<unsigned char>(t[0])) return &o;
        }
    }
    for (const auto& o : a.options) {
        if (o.token && upper_copy(o.token) == t) return &o;
    }
    return nullptr;
}

void say_accepted(const Ask& a) {
    std::cout << "Please answer with ";
    for (std::size_t i = 0; i < a.options.size(); ++i) {
        if (i) std::cout << ", ";
        std::cout << a.options[i].key;
        if (a.options[i].token) std::cout << " (" << a.options[i].token << ")";
    }
    if (!a.on_empty.empty()) std::cout << ", or Enter for " << a.on_empty;
    std::cout << ".\n";
}

} // namespace

bool console_available() {
    return DOTTALK_ISATTY(DOTTALK_FILENO(stdin)) != 0;
}

Answer ask(const Ask& a) {
    Answer out;

    // NOBODY TO ASK. Resolve to the declared unattended token WITHOUT reading.
    // This is deliberately stronger than what it replaces: `--script` is stdin
    // redirection rather than an interpreter, so the old prompt's getline
    // consumed THE NEXT LINE OF THE SCRIPT as its answer. Reading nothing is
    // strictly safer than reading one line, and it is what makes the re-ask
    // loop below safe to have at all.
    if (cli::prompt::suppressed() || !console_available()) {
        out.token = a.when_unattended;
        out.from_console = false;
        return out;
    }

    for (;;) {
        render(a);
        std::cout.flush();

        std::string line;
        if (!std::getline(std::cin, line)) {
            // EOF is not an answer. Resolve as unattended rather than looping.
            out.token = a.when_unattended;
            out.from_console = false;
            return out;
        }

        if (a.kind == Kind::Entry) {
            out.value = line;
            out.from_console = true;
            return out;
        }

        if (trim_copy(line).empty()) {
            out.token = a.on_empty;
            out.from_console = true;
            return out;
        }

        if (const Option* hit = match(a, line)) {
            out.token = hit->token ? hit->token : "";
            out.from_console = true;
            return out;
        }

        // UNRECOGNISED IS NOT AN ANSWER -- owner ruling, 2026-09-25. The three
        // parsers this replaces both guessed: `yellow` consented to an index
        // rebuild, and a leading space consented to a commit.
        say_accepted(a);
    }
}

} // namespace cli::ask
