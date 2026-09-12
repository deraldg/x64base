// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// ============================================================================
// path: src/cli/cmd_loop.cpp
// purpose: LOOP implementation with numeric repetition (N TIMES)
// notes  :
//   - LOOP
//       buffer + replay once
//   - LOOP <n>   | LOOP <n> TIMES
//       buffer + replay n times
//   - LOOP FOR <n> [TIMES]
//       same as above (compat with "FOR" phrasing)
//   - LOOP FOR <expr>
//       currently acts as a label only if not numeric
//   - the requested iteration count is CLAMPED. The ceiling is declared
//     ONCE, at kDefaultMaxLoopIterations, and is deliberately NOT repeated
//     here -- this line said 1000 while the code said 100000000, five
//     orders of magnitude apart, for as long as both existed.
// ============================================================================
// @dottalk.usage v1
// owner: DOT|LOOP
// command: LOOP
// category: script
// status: supported
// noargs: execute
// effect: buffer
// mutates: loop-buffer loop-state
// usage-access: LOOP USAGE
// summary:
//   Start buffering commands for later replay by ENDLOOP, with optional quiet
//   mode and numeric repetition labels.
//
// usage:
//   LOOP
//   LOOP USAGE
//   LOOP QUIET
//   LOOP <n>
//   LOOP <n> TIMES
//   LOOP FOR <n>
//   LOOP FOR <n> TIMES
//   LOOP FOR <label>
//   LOOP OVERRIDE <label>
//
// notes:
//   LOOP with no arguments starts command buffering and replays once at ENDLOOP.
//   LOOP <n>, LOOP <n> TIMES, and LOOP FOR <n> replay buffered commands n times.
//   LOOP QUIET suppresses buffering and ENDLOOP status messages.
//   LOOP FOR <label> stores a nonnumeric label and currently replays once.
//   ENDLOOP executes buffered commands through the pluggable shell executor.
//   The loop implementation skips buffered ENDLOOP lines during replay.
//   Iteration count is clamped to the hard maximum when necessary.
//   LOOP mutates script execution state and may indirectly mutate anything its buffered commands mutate.
//
// risk:
//   mutates_loop_state: yes
//   buffers_commands: yes
//   executes_commands: through ENDLOOP
//   mutates_table_data: depends on buffered commands
//   max_iterations: clamped
//
// related:
//   ENDLOOP
//   WHILE
//   ENDWHILE
//   UNTIL
//   ENDUNTIL
//

// @dottalk.usage v1
// owner: DOT|ENDLOOP
// command: ENDLOOP
// category: script
// status: supported
// noargs: execute
// effect: execute
// mutates: loop-buffer loop-state delegates-command-effects
// usage-access: ENDLOOP USAGE
// summary:
//   End the active LOOP block and replay buffered commands through the shell
//   executor.
//
// usage:
//   ENDLOOP
//   ENDLOOP USAGE
//
// notes:
//   ENDLOOP with no arguments executes the active LOOP buffer.
//   ENDLOOP requires an active LOOP block except for ENDLOOP USAGE.
//   ENDLOOP clears active loop state before replay.
//   ENDLOOP replays buffered commands through the registered loop executor.
//   ENDLOOP reports when no LOOP is active.
//   ENDLOOP may indirectly mutate data, session state, or files depending on buffered commands.
//
// risk:
//   executes_commands: yes
//   mutates_loop_state: yes
//   mutates_table_data: depends on buffered commands
//   mutates_session: depends on buffered commands
//
// related:
//   LOOP
//   WHILE
//   ENDWHILE
//   UNTIL
//   ENDUNTIL
//

#include "loop_state.hpp"
#include "cmd_loop.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <limits>
#include <optional>
#include <sstream>
#include <string>

#include "xbase_error_context.hpp"   // STOP_ON_ERROR: generation + trip check

namespace {

static LoopExecFn g_loop_exec = nullptr;
// THE CEILING IS A TEACHING GUARD, and 10,000 is the steward's value
// (2026-09-01). It is not a performance limit.
//
// It was 100,000,000, with the header comment above claiming 1000 -- two
// declarations of one number that disagreed by a factor of 100,000. Neither
// was reachable as a useful stop: a hundred million iterations of a body that
// touches a table is indistinguishable, from the operator's chair, from a
// hang, and LOOP/WHILE/UNTIL are student tools. A guard that fires in under a
// second and SAYS WHY teaches; a guard nobody lives to see does not.
//
// Bare LOOP still runs ONCE -- this clamps a count that was explicitly asked
// for (LOOP FOR <n>), which is the only way to reach it.
static constexpr size_t kDefaultMaxLoopIterations = 10000;

static inline void upcase_ascii(std::string& s)
{
    std::transform(
        s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
}

static inline std::string trim_ascii(std::string s)
{
    auto issp = [](unsigned char c) {
        return c == ' ' || c == '\t' || c == '\r' || c == '\n';
    };

    while (!s.empty() && issp(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && issp(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

static inline bool starts_with_ascii(const std::string& s, const std::string& prefix)
{
    if (prefix.size() > s.size()) return false;
    for (size_t i = 0; i < prefix.size(); ++i) {
        if (static_cast<unsigned char>(s[i]) != static_cast<unsigned char>(prefix[i])) {
            return false;
        }
    }
    return true;
}

// Try to parse "<n> [TIMES]" from free-form text.
// Returns {true, n} if a leading integer exists.
static std::pair<bool, size_t> parse_leading_count(const std::string& s0)
{
    std::string s = trim_ascii(s0);
    if (s.empty()) return {false, 0};

    size_t i = 0;
    if (s[i] == '+' || s[i] == '-') ++i;
    if (i >= s.size() || !std::isdigit(static_cast<unsigned char>(s[i]))) {
        return {false, 0};
    }

    long long val = 0;
    while (i < s.size() && std::isdigit(static_cast<unsigned char>(s[i]))) {
        int d = s[i] - '0';
        if (val > (std::numeric_limits<long long>::max() - d) / 10) {
            return {false, 0};
        }
        val = val * 10 + d;
        ++i;
    }

    while (i < s.size() && (s[i] == ' ' || s[i] == '\t')) ++i;

    if (val <= 0) return {true, 0};
    return {true, static_cast<size_t>(val)};
}

// Parse LOOP flags/args.
// Supports:
//   LOOP
//   LOOP QUIET
//   LOOP <n>
//   LOOP <n> TIMES
//   LOOP FOR <n>
//   LOOP FOR <n> TIMES OVERRIDE (Developer)
static void parse_loop_flags(std::istringstream& S, bool& quiet, std::string& label)
{
    quiet = false;
    label.clear();

    std::string tok;
    if (!(S >> tok)) return;

    std::string U = tok;
    upcase_ascii(U);

    if (U == "QUIET") {
        quiet = true;
        return;
    }

    if (U == "FOR") {
        std::string rest;
        std::getline(S, rest);
        label = trim_ascii(rest);
        return;
    }

    if (U == "OVERRIDE") {
        std::string rest;
        std::getline(S, rest);
        label = trim_ascii(rest);
        return;
    }

    std::string rest;
    std::getline(S, rest);
    label = trim_ascii(tok + rest);
}

static size_t iterations_from_label(const std::string& label)
{
    auto [ok, n] = parse_leading_count(label);
    if (!ok) return 1;
    return n;
}


static void print_loop_usage()
{
    std::cout
        << "Usage:\n"
        << "  LOOP\n"
        << "  LOOP USAGE\n"
        << "  LOOP QUIET\n"
        << "  LOOP <n>\n"
        << "  LOOP <n> TIMES\n"
        << "  LOOP FOR <n>\n"
        << "  LOOP FOR <n> TIMES\n"
        << "  LOOP FOR <label>\n"
        << "  LOOP OVERRIDE <label>\n"
        << "Notes:\n"
        << "  - LOOP starts buffering commands until ENDLOOP.\n"
        << "  - Numeric forms replay the buffer n times.\n";
}

static void print_endloop_usage()
{
    std::cout
        << "Usage:\n"
        << "  ENDLOOP\n"
        << "  ENDLOOP USAGE\n"
        << "Notes:\n"
        << "  - ENDLOOP executes the active LOOP buffer through the registered executor.\n";
}

static bool is_loop_usage_request(const std::string& raw)
{
    std::string t = trim_ascii(raw);
    upcase_ascii(t);
    if (starts_with_ascii(t, "LOOP ")) {
        t = trim_ascii(t.substr(5));
        upcase_ascii(t);
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static bool is_endloop_usage_request(const std::string& raw)
{
    std::string t = trim_ascii(raw);
    upcase_ascii(t);
    if (starts_with_ascii(t, "ENDLOOP ")) {
        t = trim_ascii(t.substr(8));
        upcase_ascii(t);
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

} // namespace

// ---- public API -------------------------------------------------------------

void loop_set_executor(LoopExecFn fn)
{
    g_loop_exec = fn;
}

LoopExecFn loop_get_executor()
{
    return g_loop_exec;
}

// ---- commands ---------------------------------------------------------------

void cmd_LOOP(xbase::DbArea&, std::istringstream& S)
{
    const std::string raw_args = S.str();
    if (is_loop_usage_request(raw_args)) {
        print_loop_usage();
        return;
    }

    auto& st = loopblock::state();
    st.lines.clear();

    bool quiet = false;
    std::string label;
    parse_loop_flags(S, quiet, label);

    st.active = true;
    st.quiet = quiet;
    st.for_expr = label.empty()
        ? std::optional<std::string>{}
        : std::optional<std::string>{label};

    if (!st.quiet) {
        std::cout << "LOOP: buffering commands";
        if (st.for_expr) {
            std::cout << " FOR " << *st.for_expr;
        }
        std::cout << ". Type ENDLOOP to execute.\n";
    }
}

// @dottalk.usage v1
// owner: INTERNAL|LOOP_BUFFER
// command: LOOP_BUFFER
// category: control-buffer-internal
// status: developer
// noargs: internal-capture
// effect: capture
// mutates: loop-capture-state
// usage-access: none
// summary:
//   Internal shell target that captures one LOOP body line.
// usage:
//   LOOP_BUFFER <captured-line>
// notes:
//   The shell routes lines here while LOOP capture is active. It is not a public direct command.
// related:
//   LOOP, ENDLOOP
//
void cmd_LOOP_BUFFER(xbase::DbArea&, std::istringstream& S)
{
    auto& st = loopblock::state();

    std::string raw;
    std::getline(S, raw);
    raw = trim_ascii(raw);

    if (!raw.empty()) {
        st.lines.push_back(raw);
    }
}

void cmd_ENDLOOP(xbase::DbArea& A, std::istringstream& S)
{
    const std::string raw_args = S.str();
    if (is_endloop_usage_request(raw_args)) {
        print_endloop_usage();
        return;
    }

    auto& st = loopblock::state();
    if (!st.active) {
        std::cout << "ENDLOOP: not in a LOOP.\n";
        return;
    }

    st.active = false;

    const size_t buffered = st.lines.size();

    size_t iters_requested = 1;
    if (st.for_expr && !st.for_expr->empty()) {
        iters_requested = iterations_from_label(*st.for_expr);
    }

    if (iters_requested > kDefaultMaxLoopIterations) {
        if (!st.quiet) {
            std::cout << "ENDLOOP: iteration count " << iters_requested
                      << " exceeds max " << kDefaultMaxLoopIterations
                      << "; clamping.\n";
        }
        iters_requested = kDefaultMaxLoopIterations;
    }

    size_t iters_executed = 0;

    // STOP_ON_ERROR MEANS BAIL OUT -- steward ruling 2026-09-01, the same rule
    // SCAN follows. Captured ONCE for the whole loop; once the generation moves
    // past it the trip stays tripped, which is what is wanted.
    const std::uint64_t gen0 = xbase::error::error_generation();
    bool stopped_on_error = false;

    if (g_loop_exec) {
        for (; iters_executed < iters_requested && !stopped_on_error; ++iters_executed) {
            for (const std::string& raw : st.lines) {
                std::string t = trim_ascii(raw);
                if (t.empty()) continue;

                std::string up = t;
                upcase_ascii(up);
                if (starts_with_ascii(up, "ENDLOOP")) continue;

                g_loop_exec(A, t);

                // At the LINE, not merely at the iteration: a body that fails
                // on its first command should not run the rest of itself.
                if (xbase::error::errorstop_tripped(gen0)) {
                    stopped_on_error = true;
                    break;
                }
            }
        }
    } else if (!st.quiet) {
        std::cout << "LOOP: no executor; buffered lines not executed\n";
    }

    if (stopped_on_error) {
        std::cout << "ENDLOOP: STOPPED after " << iters_executed
                  << " iteration(s) (STOP_ON_ERROR "
                  << xbase::error::errorstop_level_name(xbase::error::get_errorstop())
                  << ").\n";
        return;
    }

    if (!st.quiet) {
        std::cout << "ENDLOOP: " << buffered << " buffered line(s)";
        if (st.for_expr && !st.for_expr->empty()) {
            std::cout << ", FOR " << *st.for_expr;
        }
        if (iters_requested != 1) {
            std::cout << " -> " << iters_executed << " iteration(s)";
        }
        std::cout << "\n";
    }

    // Next LOOP clears st.lines.
}
