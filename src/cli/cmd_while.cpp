// ============================================================================
// path: src/cli/cmd_while.cpp
// purpose: WHILE / ENDWHILE with private buffering (no loop_state deps)
// usage:
//   WHILE <bool-expr> [QUIET]  -> begin buffering; shell must route lines to WHILE_BUFFER
//   ENDWHILE                   -> execute buffered body while <expr> remains true
// notes:
//   - Boolean evaluator is provided by shell via while_set_condition_eval(...).
//   - Starts from the CURRENT record (does NOT force TOP).
//   - Advances with A.skip(1) and stops hard at EOF/BOF or empty tables.
//   - Buffer persists after ENDWHILE (mirrors ENDLOOP behavior).
// ============================================================================

// @dottalk.usage v1
// owner: DOT|WHILE
// command: WHILE
// category: script
// status: supported
// noargs: block-start
// effect: loop
// mutates: while-state cursor delegates-command-effects
// usage-access: WHILE USAGE
// summary:
//   Buffer and execute a WHILE...ENDWHILE loop from the current record while a
//   boolean expression remains true.
//
// usage:
//   WHILE USAGE
//   WHILE <bool-expr> [QUIET]
//   ENDWHILE
//   ENDWHILE USAGE
//
// examples:
//   WHILE GPA >= 3.0
//       TUPLE LNAME,FNAME,GPA
//   ENDWHILE
//
// notes:
//   WHILE USAGE and ENDWHILE USAGE do not start or execute a loop.
//   WHILE starts buffering; the shell must route body lines to WHILE_BUFFER.
//   ENDWHILE executes buffered body lines through the canonical loop executor.
//   Execution starts at the current record and advances one record per iteration.
//   Buffered body command effects are owned by those commands.
//
// risk:
//   buffers_commands: yes
//   executes_commands: ENDWHILE
//   mutates_cursor: yes during loop
//   mutates_table_data: depends on buffered command body
//
// related:
//   IF
//   UNTIL
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

extern "C" void while_set_condition_eval(bool_eval_t fn) { g_eval = fn; }

// ----------------------------- tiny state -----------------------------------
namespace whilestate {
struct State {
    bool active{false};
    bool quiet{false};
    std::string cond;
    std::vector<std::string> body;
};
static State& st() { static State S; return S; }
}

// Expose capture flag so shell can route lines into WHILE_BUFFER
extern "C" bool while_is_active() { return whilestate::st().active; }

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

// -------------------------------- WHILE -------------------------------------
static std::string trim_usage_copy_while(std::string s)
{
    while (!s.empty() && (s.front() == ' ' || s.front() == '\t' || s.front() == '\r' || s.front() == '\n')) {
        s.erase(s.begin());
    }
    while (!s.empty() && (s.back() == ' ' || s.back() == '\t' || s.back() == '\r' || s.back() == '\n')) {
        s.pop_back();
    }
    return s;
}

static std::string upper_usage_copy_while(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static bool while_usage_request(const std::string& raw)
{
    const std::string u = upper_usage_copy_while(trim_usage_copy_while(raw));
    return u == "USAGE" || u == "HELP" || u == "?";
}

static void print_while_usage()
{
    std::cout
        << "Usage:\n"
        << "  WHILE USAGE\n"
        << "  WHILE <bool-expr> [QUIET]\n"
        << "  ENDWHILE\n"
        << "  ENDWHILE USAGE\n"
        << "Examples:\n"
        << "  WHILE GPA >= 3.0\n"
        << "      TUPLE LNAME,FNAME,GPA\n"
        << "  ENDWHILE\n"
        << "Notes:\n"
        << "  - WHILE USAGE and ENDWHILE USAGE do not start or execute a loop.\n";
}
void cmd_WHILE(xbase::DbArea&, std::istringstream& S)
{
    auto& st = whilestate::st();

    std::string expr = slurp_rest(S);
    if (while_usage_request(expr)) {
        print_while_usage();
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
        std::cout << "WHILE: buffering body. Type ENDWHILE to execute loop.\n";
    }
}

// Lines are routed here by the shell while capture is active
// @dottalk.usage v1
// owner: INTERNAL|WHILE_BUFFER
// command: WHILE_BUFFER
// category: control-buffer-internal
// status: developer
// noargs: internal-capture
// effect: capture
// mutates: while-capture-state
// usage-access: none
// summary:
//   Internal shell target that captures one WHILE body line.
// usage:
//   WHILE_BUFFER <captured-line>
// notes:
//   The shell routes lines here while WHILE capture is active. It is not a public direct command.
// related:
//   WHILE, ENDWHILE
//
void cmd_WHILE_BUFFER(xbase::DbArea&, std::istringstream& S)
{
    auto& st = whilestate::st();
    std::string raw;
    std::getline(S, raw);
    if (!raw.empty() && (raw[0] == ' ' || raw[0] == '\t')) raw.erase(0, 1);
    if (!raw.empty()) st.body.push_back(std::move(raw));
}

// -------------------------------- ENDWHILE ----------------------------------
void cmd_ENDWHILE(xbase::DbArea& A, std::istringstream& S)
{
    if (while_usage_request(slurp_rest(S))) {
        print_while_usage();
        return;
    }
    auto& st = whilestate::st();

    // stop capturing before we run
    st.active = false;

    if (!g_eval) {
        if (!st.quiet) {
            std::cout << "ENDWHILE: no condition evaluator; nothing executed.\n";
        }
        return;
    }

    // Start from CURRENT record. Do not force TOP.

    // copy snapshot to avoid surprise mutations during execution
    const auto body = st.body;
    std::size_t iters = 0;

    while (g_eval(A, st.cond)) {
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
        std::cout << "ENDWHILE: executed " << iters
                  << " iteration(s) over " << body.size() << " line(s).\n";
    }
}
