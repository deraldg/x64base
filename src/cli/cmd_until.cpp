// ============================================================================
// path: src/cli/cmd_until.cpp
// purpose: UNTIL / ENDUNTIL with private buffering (no loop_state deps)
// usage:
//   UNTIL <bool-expr> [QUIET]  -> begin buffering; shell routes lines to UNTIL_BUFFER
//   ENDUNTIL                   -> execute body until <expr> becomes true
// notes:
//   - Starts from the CURRENT record (does NOT force TOP).
//   - Advances with A.skip(1); stops hard at EOF/BOF or empty tables.
//   - Buffer persists after ENDUNTIL (mirrors ENDLOOP).
// ============================================================================

// @dottalk.usage v1
// owner: DOT|UNTIL
// command: UNTIL
// category: script
// status: supported
// noargs: block-start
// effect: loop
// mutates: until-state cursor delegates-command-effects
// usage-access: UNTIL USAGE
// summary:
//   Buffer and execute an UNTIL...ENDUNTIL loop from the current record until a
//   boolean expression becomes true.
//
// usage:
//   UNTIL USAGE
//   UNTIL <bool-expr> [QUIET]
//   ENDUNTIL
//   ENDUNTIL USAGE
//
// examples:
//   UNTIL EOF()
//       TUPLE LNAME,FNAME,GPA
//   ENDUNTIL
//
// notes:
//   UNTIL USAGE and ENDUNTIL USAGE do not start or execute a loop.
//   UNTIL starts buffering; the shell must route body lines to UNTIL_BUFFER.
//   ENDUNTIL executes buffered body lines through the canonical loop executor.
//   Execution starts at the current record and advances one record per iteration.
//   Buffered body command effects are owned by those commands.
//
// risk:
//   buffers_commands: yes
//   executes_commands: ENDUNTIL
//   mutates_cursor: yes during loop
//   mutates_table_data: depends on buffered command body
//
// related:
//   IF
//   WHILE
//   SCAN
//

#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <cctype>

#include "xbase.hpp"
#include "cmd_loop.hpp"  // for loop_get_executor() signature only

using bool_eval_t = bool(*)(xbase::DbArea&, const std::string&);
static bool_eval_t g_eval = nullptr;

extern "C" void until_set_condition_eval(bool_eval_t fn) { g_eval = fn; }

// ----------------------------- tiny state -----------------------------------
namespace untilstate {
struct State {
    bool active{false};
    bool quiet{false};
    std::string cond;
    std::vector<std::string> body;
};
static State& st() { static State S; return S; }
}

// Expose capture flag so shell can route lines into UNTIL_BUFFER
extern "C" bool until_is_active() { return untilstate::st().active; }

// ------------------------------ helpers -------------------------------------
static std::string slurp_rest(std::istringstream& S) {
    std::string rest;
    std::getline(S, rest);
    if (!rest.empty() && (rest[0] == ' ' || rest[0] == '\t')) rest.erase(0, 1);
    return rest;
}

static bool advance_one_record(xbase::DbArea& A) {
    try {
        if (!A.isOpen() || A.recCount() == 0) return false;
        return A.skip(1);
    } catch (...) {
        return false;
    }
}

static void trim_trailing(std::string& s) {
    while (!s.empty() && (s.back() == ' ' || s.back() == '\t' || s.back() == '\r')) {
        s.pop_back();
    }
}

// -------------------------------- UNTIL -------------------------------------
static std::string trim_usage_copy_until(std::string s)
{
    while (!s.empty() && (s.front() == ' ' || s.front() == '\t' || s.front() == '\r' || s.front() == '\n')) {
        s.erase(s.begin());
    }
    while (!s.empty() && (s.back() == ' ' || s.back() == '\t' || s.back() == '\r' || s.back() == '\n')) {
        s.pop_back();
    }
    return s;
}

static std::string upper_usage_copy_until(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static bool until_usage_request(const std::string& raw)
{
    const std::string u = upper_usage_copy_until(trim_usage_copy_until(raw));
    return u == "USAGE" || u == "HELP" || u == "?";
}

static void print_until_usage()
{
    std::cout
        << "Usage:\n"
        << "  UNTIL USAGE\n"
        << "  UNTIL <bool-expr> [QUIET]\n"
        << "  ENDUNTIL\n"
        << "  ENDUNTIL USAGE\n"
        << "Examples:\n"
        << "  UNTIL EOF()\n"
        << "      TUPLE LNAME,FNAME,GPA\n"
        << "  ENDUNTIL\n"
        << "Notes:\n"
        << "  - UNTIL USAGE and ENDUNTIL USAGE do not start or execute a loop.\n";
}
void cmd_UNTIL(xbase::DbArea&, std::istringstream& S)
{
    auto& st = untilstate::st();

    std::string expr = slurp_rest(S);
    if (until_usage_request(expr)) {
        print_until_usage();
        return;
    }
    bool quiet = false;

    // optional trailing QUIET
    {
        std::string up = expr;
        for (auto& c : up) c = char(std::toupper((unsigned char)c));
        const auto pos = up.rfind(" QUIET");
        if (pos != std::string::npos && pos + 6 == up.size()) {
            quiet = true;
            expr.erase(pos);
            trim_trailing(expr);
        }
    }

    st.body.clear();
    st.active = true;
    st.quiet  = quiet;
    st.cond   = std::move(expr);

    if (!st.quiet) {
        std::cout << "UNTIL: buffering body. Type ENDUNTIL to execute loop.\n";
    }
}

// Lines are routed here by the shell while capture is active
void cmd_UNTIL_BUFFER(xbase::DbArea&, std::istringstream& S)
{
    auto& st = untilstate::st();
    std::string raw;
    std::getline(S, raw);
    if (!raw.empty() && (raw[0] == ' ' || raw[0] == '\t')) raw.erase(0, 1);
    if (!raw.empty()) st.body.push_back(std::move(raw));
}

// -------------------------------- ENDUNTIL ----------------------------------
void cmd_ENDUNTIL(xbase::DbArea& A, std::istringstream& S)
{
    if (until_usage_request(slurp_rest(S))) {
        print_until_usage();
        return;
    }
    auto& st = untilstate::st();

    // stop capturing before we run
    st.active = false;

    if (!g_eval) {
        if (!st.quiet) {
            std::cout << "ENDUNTIL: no condition evaluator; nothing executed.\n";
        }
        return;
    }

    // Start from CURRENT record. Do not force TOP.

    const auto body = st.body;
    std::size_t iters = 0;

    while (true) {
        if (g_eval(A, st.cond)) break;  // stop when condition becomes true

        ++iters;

        if (!body.empty()) {
            auto* exec = loop_get_executor();
            if (exec) {
                for (const auto& line : body) {
                    (*exec)(A, line);
                }
            }
        }

        if (!advance_one_record(A)) break;
    }

    if (!st.quiet) {
        std::cout << "ENDUNTIL: executed " << iters
                  << " iteration(s) over " << body.size() << " line(s).\n";
    }
}