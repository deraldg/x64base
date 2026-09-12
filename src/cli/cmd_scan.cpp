// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_scan.cpp
// SCAN / ENDSCAN with per-record command execution.
//
// Supports:
//   SCAN [FOR <expr>]
//   ENDSCAN
//
// Notes:
//   - Lines between SCAN..ENDSCAN are buffered via the internal __SCAN_BUFFER command.
//   - Default gate: skips deleted records.
//   - FOR <expr> is evaluated by the DotTalk++ expression engine.
//   - Native DotTalk++ predicates are NOT routed through SQL normalization.
//   - If evaluation fails, FOR matches no records (safe default).
//   - Honors active SET FILTER via filter::visible(&A, nullptr).
//
// Ordered traversal policy:
//   - No active order: physical recno 1..recCount traversal.
//   - Active order: use shared order_iterator (INX/CNX/CDX).
//   - If ordered traversal fails, fall back to physical order.
//
// Re-entrancy / nesting policy:
//   - Only one SCAN block may be buffered at a time.
//   - Nested SCAN during ENDSCAN execution is not allowed.
//   - Recursive ENDSCAN is not allowed.
//   - Buffering lines during ENDSCAN execution is not allowed.
//
// Execution policy:
//   - SCAN control verbs inside the SCAN body are ignored.
//   - ENDSCAN preserves the user's current cursor position on exit.
//   - Buffered body lines replay through the canonical loop executor so
//     shell shortcuts (e.g. TUP -> TUPLE) work the same as at the prompt.

// @dottalk.usage v1
// owner: DOT|SCAN
// command: SCAN
// category: script
// status: supported
// noargs: block-start
// effect: loop
// mutates: scan-state cursor delegates-command-effects
// usage-access: SCAN USAGE
// summary:
//   Buffer and execute a SCAN...ENDSCAN record loop over the current logical rowset.
//
// usage:
//   SCAN
//   SCAN USAGE
//   SCAN FOR <expr>
//   ENDSCAN
//   ENDSCAN USAGE
//
// notes:
//   SCAN with no arguments starts buffering a scan block on the current area.
//   SCAN FOR <expr> adds a predicate to the scan loop.
//   ENDSCAN executes buffered body lines through the canonical command executor.
//   Deleted records and active SET FILTER visibility are honored by the scan gate.
//   Active order traversal uses shared order_iterator when available, with physical fallback.
//   ENDSCAN restores the user's cursor best-effort after execution.
//
// risk:
//   buffers_commands: yes
//   executes_commands: ENDSCAN
//   delegates_command_effects: yes
//   mutates_cursor: during scan, restored best-effort
//   mutates_table_data: depends on buffered command body
//   requires_open_table: SCAN except usage
//
// related:
//   WHILE
//   UNTIL
//   FOR
//   LOOP
//

#include "cmd_scan.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/command_registry.hpp"
#include "scan_state.hpp"
#include "set_relations.hpp"
#include "filters/filter_registry.hpp"

#include "cli/order_state.hpp"
#include "cli/order_nav.hpp"
#include "cli/order_iterator.hpp"

#include "xbase_error_context.hpp"   // STOP_ON_ERROR: generation + trip check
#include "cli/table_state.hpp"       // TABLE buffering state: is a bail recoverable?
#include "workarea_util.hpp"          // cli::slot_of_area
#include "cli/expr/line_parse_utils.hpp"
#include "cli/expr/normalize_where.hpp"
#include "cli/expr/value_eval.hpp"

#include "cmd_loop.hpp"   // loop_get_executor()

using xbase::DbArea;

namespace {

static inline std::string up(std::string s) {
    for (auto& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static inline std::string trim_copy(std::string s) {
    return textio::trim(std::move(s));
}

static inline bool ends_with_iex(const std::string& s, const char* EXT3) {
    const size_t n = s.size();
    return n >= 4 && s[n - 4] == '.'
        && static_cast<char>(std::toupper(static_cast<unsigned char>(s[n - 3]))) == EXT3[0]
        && static_cast<char>(std::toupper(static_cast<unsigned char>(s[n - 2]))) == EXT3[1]
        && static_cast<char>(std::toupper(static_cast<unsigned char>(s[n - 1]))) == EXT3[2];
}

static inline std::string upper_copy(std::string s) {
    for (char& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

static void print_scan_usage()
{
    std::cout
        << "Usage:\n"
        << "  SCAN\n"
        << "  SCAN USAGE\n"
        << "  SCAN FOR <expr>\n"
        << "  ENDSCAN\n"
        << "  ENDSCAN USAGE\n";
}

static bool scan_usage_request(const std::string& raw, const char* command_name)
{
    std::string s = upper_copy(trim_copy(raw));
    if (s.empty()) return false;

    const std::string cmd = upper_copy(command_name ? std::string(command_name) : std::string{});
    if (!cmd.empty() && s.rfind(cmd + " ", 0) == 0) {
        s = upper_copy(trim_copy(s.substr(cmd.size() + 1)));
    }

    return s == "USAGE" || s == "HELP" || s == "?";
}

static inline bool is_comment_or_blank(const std::string& raw) {
    std::string s = textio::trim(raw);
    if (s.empty()) return true;
    if (s[0] == '#') return true;
    if (s.size() >= 2 && s[0] == '/' && s[1] == '/') return true;
    return false;
}

static bool expression_has_function_call(const std::string& expr) {
    const auto lp = expr.find('(');
    if (lp == std::string::npos) return false;

    const auto rp = expr.find(')', lp + 1);
    if (rp == std::string::npos) return false;

    // A conservative test is enough here. Native function predicates such as
    // LEFT(LNAME,1), UPPER(LNAME), and SOUNDEX(LNAME) must pass through to
    // eval_bool() without RHS literal repair or SQL normalization.
    return true;
}

enum class DelGate {
    OnlyAlive,
    OnlyDeleted,
    Any
};

struct EvalProg {
    bool enabled{false};
    std::string expr;

    bool eval(xbase::DbArea& A) const {
        if (!enabled) return true;

        bool result = false;
        std::string err;

        try {
            return dottalk::expr::eval_bool(A, expr, result, &err) && result;
        } catch (...) {
            return false;
        }
    }
};

static EvalProg build_evaluator_from(xbase::DbArea& A, const std::string& userExpr) {
    EvalProg E{};

    std::string expr = strip_line_comments(userExpr);
    expr = trim_copy(expr);

    if (expr.empty()) {
        E.enabled = true;
        E.expr.clear();
        return E;
    }

    // SCAN is a native DotTalk++ command. Do not route its FOR clause through
    // SQL normalization. SQL-style normalization belongs at SQL/import surfaces,
    // not in the core xBase command loop.
    //
    // Keep unquoted RHS literal repair only for simple non-function predicates:
    //     LNAME = WHITE
    //
    // Function predicates must pass through unchanged:
    //     LEFT(LNAME,1) = "W"
    //     SOUNDEX(LNAME) = SOUNDEX("WHITE")
    //     UPPER(LNAME) = "WHITE"
    if (!expression_has_function_call(expr)) {
        expr = normalize_unquoted_rhs_literals(A, expr);
        expr = trim_copy(expr);
    }

    E.enabled = true;
    E.expr = std::move(expr);
    return E;
}

struct ScanFilter {
    DelGate del{DelGate::OnlyAlive};
    bool haveExpr{false};
    EvalProg E{};

    bool pass_deleted_gate(const xbase::DbArea& a) const {
        bool isDel = false;
        try { isDel = a.isDeleted(); } catch (...) { isDel = false; }

        switch (del) {
            case DelGate::OnlyDeleted: return isDel;
            case DelGate::Any:         return true;
            case DelGate::OnlyAlive:
            default:                   return !isDel;
        }
    }

    bool matches(xbase::DbArea& a) const {
        if (!pass_deleted_gate(a)) return false;
        if (!haveExpr) return true;
        return E.eval(a);
    }
};

struct CursorRestore {
    xbase::DbArea* a{nullptr};
    int32_t saved{0};
    bool active{false};

    explicit CursorRestore(xbase::DbArea& area) : a(&area) {
        try {
            saved = area.recno();
            active = (saved >= 1 && saved <= area.recCount());
        } catch (...) {
            active = false;
        }
    }

    ~CursorRestore() {
        if (!active || !a) return;
        try {
            if (a->gotoRec(saved)) {
                (void)a->readCurrent();
            }
        } catch (...) {
            // best-effort restore only
        }
    }

    CursorRestore(const CursorRestore&) = delete;
    CursorRestore& operator=(const CursorRestore&) = delete;
};

// File-local filter state for the active SCAN.
static ScanFilter g_scan_filter;

// Explicit execution guard for nested/re-entrant SCAN behavior.
static bool g_scan_executing = false;

struct ScanExecGuard {
    ScanExecGuard()  { g_scan_executing = true;  }
    ~ScanExecGuard() { g_scan_executing = false; }

    ScanExecGuard(const ScanExecGuard&) = delete;
    ScanExecGuard& operator=(const ScanExecGuard&) = delete;
};

static ScanFilter compile_filter(DbArea& A, std::istringstream& iss, bool& hadFor) {
    ScanFilter f{};
    hadFor = false;

    std::streampos save = iss.tellg();
    std::string tok;
    if (!(iss >> tok)) {
        return f;
    }

    if (!textio::ieq(tok, "FOR")) {
        iss.clear();
        iss.seekg(save);
        return f;
    }

    hadFor = true;

    std::string rest;
    std::getline(iss, rest);
    rest = trim_copy(rest);

    if (rest.empty()) {
        return f;
    }

    {
        const std::string U = up(rest);
        if (U == "DELETED") {
            f.del = DelGate::OnlyDeleted;
            f.haveExpr = false;
            return f;
        }
        if (U == "!DELETED" || U == "~DELETED") {
            f.del = DelGate::OnlyAlive;
            f.haveExpr = false;
            return f;
        }
    }

    f.haveExpr = true;
    f.E = build_evaluator_from(A, rest);
    return f;
}

static bool is_scan_control_verb(const std::string& cmdU) {
    return cmdU == "SCAN" || cmdU == "ENDSCAN" || cmdU == "__SCAN_BUFFER";
}

static std::vector<std::string> sanitize_body_lines(const std::vector<std::string>& lines, int& skipped_controls) {
    std::vector<std::string> out;
    skipped_controls = 0;

    out.reserve(lines.size());
    for (const auto& raw : lines) {
        const std::string trimmed = textio::trim(raw);
        if (trimmed.empty()) continue;

        std::istringstream li(trimmed);
        std::string cmd;
        li >> cmd;
        if (cmd.empty()) continue;

        const std::string U = up(cmd);
        if (is_scan_control_verb(U)) {
            ++skipped_controls;
            continue;
        }

        out.push_back(raw);
    }

    return out;
}

// STOP_ON_ERROR MEANS BAIL OUT -- steward ruling 2026-09-01.
//
// Returns FALSE when the run must stop. The check is at the LINE, not merely at
// the record, because a body of three REPLACEs that fails on the first has no
// business running the other two against the same row.
//
// gen_before is captured ONCE for the whole scan rather than per line. Once the
// generation moves past it the trip stays tripped, which is what is wanted --
// the first failure ends the run and no later check can un-see it.
static bool exec_lines(DbArea& A,
                       const std::vector<std::string>& lines,
                       std::uint64_t gen_before) {
    auto* exec = loop_get_executor();

    for (const auto& raw : lines) {
        const std::string trimmed = textio::trim(raw);
        if (trimmed.empty()) continue;

        std::istringstream li(trimmed);
        std::string cmd;
        li >> cmd;
        if (cmd.empty()) continue;

        const std::string U = up(cmd);
        if (is_scan_control_verb(U)) {
            continue;
        }

        if (exec) {
            (*exec)(A, trimmed);
        } else if (!dli::registry().run(A, U, li)) {
            std::cout << "Unknown command in SCAN: " << cmd << "\n";
        }

        if (xbase::error::errorstop_tripped(gen_before)) {
            return false;
        }
    }

    return true;
}

// Where a bailed-out scan stopped. Carried out by reference rather than
// returned, because both runners need to report it and the iterator's callback
// contract already owns the bool.
struct ScanStop {
    bool     stopped{false};
    uint64_t recno{0};
};

// Returns FALSE when the scan must stop. A record that is SKIPPED (unreadable,
// filtered out, not visible) returns TRUE -- skipping is not stopping.
static bool run_scan_on_recno(DbArea& A,
                              uint64_t rn,
                              const std::vector<std::string>& lines,
                              const ScanFilter& filter,
                              int& matched,
                              int& iterations,
                              std::uint64_t gen_before,
                              ScanStop& stop) {
    try {
        if (!A.gotoRec(static_cast<int32_t>(rn)) || !A.readCurrent()) return true;
    } catch (...) {
        return true;
    }

    relations_api::refresh_if_enabled();

    bool ok = false;
    try { ok = filter.matches(A) && filter::visible(&A, nullptr); } catch (...) { ok = false; }
    if (!ok) return true;

    ++matched;

    if (!exec_lines(A, lines, gen_before)) {
        // ITERATIONS IS NOT INCREMENTED, and that is the point: it counts
        // records that COMPLETED. This one did not, so the summary can say
        // truthfully that N completed and record rn was left part-done.
        stop.stopped = true;
        stop.recno   = rn;
        std::cout.flush();
        return false;
    }

    ++iterations;
    std::cout.flush();
    return true;
}

static void run_scan_physical(DbArea& A,
                              const std::vector<std::string>& lines,
                              const ScanFilter& filter,
                              int nrecs,
                              int& matched,
                              int& iterations,
                              std::uint64_t gen_before,
                              ScanStop& stop) {
    if (nrecs <= 0) return;

    for (int32_t rn = 1; rn <= nrecs; ++rn) {
        if (!run_scan_on_recno(A, static_cast<uint64_t>(rn), lines, filter,
                               matched, iterations, gen_before, stop)) {
            break;
        }
    }
}

static bool run_scan_via_iterator(DbArea& A,
                                  const std::vector<std::string>& lines,
                                  const ScanFilter& filter,
                                  int& matched,
                                  int& iterations,
                                  std::uint64_t gen_before,
                                  ScanStop& stop) {
    cli::OrderIterSpec spec{};
    std::string err;

    // The callback's bool ALREADY meant continue-or-stop; it was simply always
    // true. The bail-out needed no new plumbing here, only an honest answer.
    const bool ok = cli::order_iterate_recnos(
        A,
        [&](uint64_t rn) -> bool {
            return run_scan_on_recno(A, rn, lines, filter, matched, iterations,
                                     gen_before, stop);
        },
        &spec,
        &err
    );

    (void)spec;
    (void)err;
    return ok;
}

} // namespace

void cmd_SCAN(DbArea& A, std::istringstream& S)
{
    if (scan_usage_request(S.str(), "SCAN")) {
        print_scan_usage();
        return;
    }

    auto& st = scanblock::state();

    if (g_scan_executing) {
        std::cout << "SCAN: nested SCAN not allowed during ENDSCAN.\n";
        return;
    }

    if (st.active) {
        std::cout << "SCAN: already buffering lines. Type ENDSCAN to execute.\n";
        return;
    }

    if (!A.isOpen()) {
        st.active = false;
        st.lines.clear();
        std::cout << "SCAN: no table open in current area.\n";
        return;
    }

    st.active = true;
    st.lines.clear();

    bool hadFor = false;
    g_scan_filter = compile_filter(A, S, hadFor);

    std::cout << "SCAN: buffering lines. Type ENDSCAN to execute"
              << (hadFor ? " (FOR present)." : ".") << "\n";
}

// @dottalk.usage v1
// owner: INTERNAL|SCAN_BUFFER
// command: SCAN_BUFFER
// category: control-buffer-internal
// status: developer
// noargs: internal-capture
// effect: capture
// mutates: scan-capture-state
// usage-access: none
// summary:
//   Internal shell target that captures one SCAN body line.
// usage:
//   SCAN_BUFFER <captured-line>
// notes:
//   The shell routes lines here while SCAN capture is active. It is not a public direct command.
// related:
//   SCAN, ENDSCAN
//
void cmd_SCAN_BUFFER(DbArea& /*A*/, std::istringstream& S)
{
    auto& st = scanblock::state();

    if (g_scan_executing) {
        std::cout << "SCAN: cannot buffer lines during ENDSCAN.\n";
        return;
    }

    if (!st.active) return;

    std::string raw;
    std::getline(S >> std::ws, raw);
    if (raw.empty()) return;
    if (is_comment_or_blank(raw)) return;

    st.lines.push_back(raw);
}

void cmd_ENDSCAN(DbArea& A, std::istringstream& S)
{
    if (scan_usage_request(S.str(), "ENDSCAN")) {
        print_scan_usage();
        return;
    }

    auto& st = scanblock::state();

    if (g_scan_executing) {
        std::cout << "ENDSCAN: already executing.\n";
        return;
    }

    if (!st.active) {
        std::cout << "No active SCAN.\n";
        return;
    }

    CursorRestore restore(A);

    std::vector<std::string> raw_lines = st.lines;
    ScanFilter filter = std::move(g_scan_filter);

    st.active = false;
    st.lines.clear();
    g_scan_filter = ScanFilter{};

    int skipped_controls = 0;
    std::vector<std::string> lines = sanitize_body_lines(raw_lines, skipped_controls);
    const int buffered = static_cast<int>(lines.size());

    if (skipped_controls > 0) {
        std::cout << "SCAN: ignored " << skipped_controls
                  << " control line(s) inside SCAN body.\n";
    }

    int nrecs = 0;
    try { nrecs = A.recCount(); } catch (...) { nrecs = 0; }

    int matched = 0;
    int iterations = 0;

    // STOP_ON_ERROR is captured ONCE, here, for the whole scan.
    const std::uint64_t gen0 = xbase::error::error_generation();
    ScanStop stop;

    {
        ScanExecGuard exec_guard;

        if (orderstate::hasOrder(A)) {
            if (!run_scan_via_iterator(A, lines, filter, matched, iterations,
                                       gen0, stop)) {
                // THE FALLBACK MUST NOT RE-RUN A SCAN THAT ALREADY STOPPED.
                // run_scan_via_iterator returns false BOTH when the iterator
                // could not be used at all AND when our callback stopped it,
                // and those are opposite situations: the first wants the
                // physical pass, the second has already done the work and
                // deliberately quit part-way. Without this guard a bailed-out
                // scan would silently restart from record 1 and run the body
                // again over rows it had just failed on.
                if (!stop.stopped) {
                    run_scan_physical(A, lines, filter, nrecs, matched,
                                      iterations, gen0, stop);
                }
            }
        } else {
            run_scan_physical(A, lines, filter, nrecs, matched, iterations,
                              gen0, stop);
        }
    }

    if (stop.stopped) {
        // A BAILED SCAN LEAVES WORK HALF DONE, so the message has to say where
        // it stopped AND WHAT CAN BE DONE ABOUT IT. Without the first the
        // ruling buys "stop means stop" at the price of a silent partial
        // state; without the second it talks the operator out of the recovery
        // they actually have.
        //
        // THE RECOVERY DEPENDS ON TABLE BUFFERING AND THIS MESSAGE ASKS RATHER
        // THAN ASSUMES. An earlier draft of this block said flatly "nothing is
        // rolled back -- SCAN is not a transaction". That is true with
        // buffering OFF and FALSE with it ON: REPLACE is buffered per area and
        // cmd_ROLLBACK drops the change map, so a bailed scan's writes are
        // discardable. Printing the pessimistic line unconditionally would
        // have steered someone away from the one command that fixes their
        // table.
        //
        // NOT COVERED BY ROLLBACK EVEN WHEN BUFFERING IS ON: DELETE is
        // write-through (TABLE_BUFFER_WAL_DESIGN_2026-07-19, "Only REPLACE is
        // buffered"), so a body that deletes has already deleted. The message
        // does not claim otherwise -- it speaks of buffered CHANGES, which is
        // what the buffer holds.
        // NAMED table_buffering_on, NOT `buffered`. `buffered` is already taken
        // in this function for lines.size() -- how many BODY LINES were
        // buffered -- and the two mean entirely different things. The compiler
        // caught the collision (C4456); the rename is the fix rather than a
        // scope trick, because a reader should not have to work out which
        // `buffered` a line is talking about.
        const int  area0 = cli::slot_of_area(&A);
        const bool table_buffering_on =
            (area0 >= 0) && dottalk::table::is_enabled(area0);

        std::cout << "ENDSCAN: STOPPED at record " << stop.recno
                  << " (STOP_ON_ERROR "
                  << xbase::error::errorstop_level_name(xbase::error::get_errorstop())
                  << ").\n";
        std::cout << "  " << iterations << " record(s) completed; record "
                  << stop.recno << " was partially processed.\n";

        if (table_buffering_on) {
            std::cout << "  TABLE buffering is ON: the changes are held, not"
                         " written. ROLLBACK discards them; COMMIT applies"
                         " them. DELETEs are write-through and are NOT held.\n";
        } else {
            std::cout << "  TABLE buffering is OFF, so those writes went"
                         " straight to the table and there is nothing to roll"
                         " back.\n";
        }
        return;
    }

    std::cout << "ENDSCAN: " << matched
              << " match(es), " << iterations
              << " iteration(s) over " << buffered
              << " line(s).\n";
}
