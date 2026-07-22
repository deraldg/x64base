// src/commands/cmd_dotscript.cpp
// DOTSCRIPT runner with TRACE banner + scripts/tests resolver + @file support + one-level subscript limit.

// @dottalk.usage v1
// owner: DOT|DOTSCRIPT
// command: DOTSCRIPT
// category: script
// status: supported
// noargs: usage
// effect: execute
// mutates: delegates script commands session
// usage-access: DOTSCRIPT USAGE
// summary:
//   Run a DotTalk++ script file, resolving bare names through script/test
//   search locations, supporting @file notation, TRACE mode, and one-level
//   subscript nesting.
//
// usage:
//   DOTSCRIPT USAGE
//   DOTSCRIPT <file>
//   DOTSCRIPT @<file>
//   DOTSCRIPT TRACE
//   DOTSCRIPT TRACE ON
//   DOTSCRIPT TRACE OFF
//   DOTSCRIPT TRACE <file>
//   DOTSCRIPT TRACE @<file>
//   DOTSCRIPT TRACE ON <file>
//   DOTSCRIPT TRACE OFF <file>
//   DOTSCRIPT TRACE ON @<file>
//   DOTSCRIPT TRACE OFF @<file>
//
// notes:
//   DOTSCRIPT with no arguments shows usage.
//   DOTSCRIPT reads an external script file and executes each nonblank,
//   noncomment line through the shell command executor.
//   Script comments/blank lines are ignored when they begin with *, //, &&, or ; after trimming.
//   Bare script names try the typed name, .dts extension, scripts/, and tests/ candidates.
//   @file notation is accepted and unquoted before path resolution.
//   TRACE without a file reports the current trace state and usage.
//   TRACE ON/OFF changes global DOTSCRIPT trace state.
//   TRACE <file> runs a single script with trace enabled without changing global trace state.
//   Nesting is limited to main script plus one subscript.
//   DOTSCRIPT itself delegates side effects to the commands inside the script; it is not read-only.
//
// risk:
//   reads_files: yes
//   executes_commands: yes
//   mutates_data: depends on script contents
//   mutates_session: depends on script contents
//   writes_files: depends on script contents
//   trace_state_mutation: DOTSCRIPT TRACE ON/OFF
//   nesting_limit: main plus one subscript
//   no_transaction_or_rollback: yes
//
// related:
//   TEST
//   CMDHELP
//   WORKSPACE
//   CREATE
//   USE
//

#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

#include "shell_api.hpp"
#include "xbase.hpp"
#include "shell_transcript.hpp"
#include "script_reader.hpp"   // read_script_command: shared ';'-continuation reader
#include "xbase_error_context.hpp"  // stop_on_error[severity] threshold + trip check
#include "cli/dotscript_lexing.hpp" // canonical comment/line lexing (AIF-037)

using xbase::DbArea;

extern "C" xbase::XBaseEngine* shell_engine();

namespace {

static DbArea& current_shell_area_or(DbArea& fallback)
{
    if (auto* eng = shell_engine()) {
        try {
            return eng->area(eng->currentArea());
        } catch (...) {
        }
    }
    return fallback;
}


struct ScopeExit {
    void (*fn)() = nullptr;
    ~ScopeExit() { if (fn) fn(); }
};

static inline std::string ltrim_copy(std::string s) {
    size_t i = 0;
    while (i < s.size() && (s[i] == ' ' || s[i] == '\t' || s[i] == '\r' || s[i] == '\n')) ++i;
    s.erase(0, i);
    return s;
}

static inline std::string rtrim_copy(std::string s) {
    while (!s.empty()) {
        const char c = s.back();
        if (c == ' ' || c == '\t' || c == '\r' || c == '\n') s.pop_back();
        else break;
    }
    return s;
}

static inline std::string trim_copy(std::string s) {
    return rtrim_copy(ltrim_copy(std::move(s)));
}

static inline std::string upper_copy(std::string s) {
    for (char& c : s) {
        if (c >= 'a' && c <= 'z') c = static_cast<char>(c - 'a' + 'A');
    }
    return s;
}

static inline std::string unquote_copy(std::string s) {
    s = trim_copy(std::move(s));
    if (s.size() >= 2) {
        const char a = s.front();
        const char b = s.back();
        if ((a == '"' && b == '"') || (a == '\'' && b == '\'')) {
            s = s.substr(1, s.size() - 2);
        }
    }
    return trim_copy(std::move(s));
}

static inline std::string strip_at_prefix(std::string s) {
    s = trim_copy(std::move(s));
    if (!s.empty() && s.front() == '@') {
        s.erase(0, 1);
        s = trim_copy(std::move(s));
        s = unquote_copy(std::move(s));
    }
    return s;
}

static inline bool looks_like_comment_or_blank(const std::string& line) {
    return dottalk::lexing::is_comment_or_blank(line);
}


static std::vector<std::string> split_dotscript_words(const std::string& text) {
    std::vector<std::string> out;
    std::string cur;
    bool in_single = false;
    bool in_double = false;
    char prev = '\0';

    for (char c : text) {
        if (c == '\'' && !in_double && prev != '\\') {
            in_single = !in_single;
            prev = c;
            continue;
        }
        if (c == '"' && !in_single && prev != '\\') {
            in_double = !in_double;
            prev = c;
            continue;
        }

        const bool space = (c == ' ' || c == '\t' || c == '\r' || c == '\n');
        if (space && !in_single && !in_double) {
            if (!cur.empty()) {
                out.push_back(cur);
                cur.clear();
            }
        } else {
            cur.push_back(c);
        }
        prev = c;
    }

    if (!cur.empty()) out.push_back(cur);
    return out;
}

static std::string join_dotscript_words(const std::vector<std::string>& words, size_t first, size_t last_exclusive) {
    std::string out;
    for (size_t i = first; i < last_exclusive && i < words.size(); ++i) {
        if (!out.empty()) out += " ";
        out += words[i];
    }
    return out;
}

static std::string strip_dotscript_at_prefix(std::string s) {
    if (!s.empty() && s.front() == '@') s.erase(s.begin());
    return s;
}

static std::string unquote_dotscript_token(std::string s) {
    if (s.size() >= 2) {
        const char a = s.front();
        const char b = s.back();
        if ((a == '"' && b == '"') || (a == '\'' && b == '\'')) {
            return s.substr(1, s.size() - 2);
        }
    }
    return s;
}

static bool extract_dotscript_output_clause(
    std::string& file_spec,
    std::string& transcript_spec,
    bool& transcript_append,
    std::string* error_out
) {
    transcript_spec.clear();
    transcript_append = false;

    std::vector<std::string> words = split_dotscript_words(file_spec);
    if (words.size() < 3) return true;

    auto upper_word = [](std::string s) {
        for (char& c : s) {
            if (c >= 'a' && c <= 'z') c = static_cast<char>(c - 'a' + 'A');
        }
        return s;
    };

    size_t out_pos = static_cast<size_t>(-1);
    size_t transcript_pos = static_cast<size_t>(-1);

    const std::string last = upper_word(words.back());
    if (last == "APPEND") {
        if (words.size() < 4) {
            if (error_out) *error_out = "APPEND requires OUT <file> APPEND";
            return false;
        }
        const std::string maybe_out = upper_word(words[words.size() - 3]);
        if (maybe_out == "OUT" || maybe_out == "OUTPUT") {
            out_pos = words.size() - 3;
            transcript_pos = words.size() - 2;
            transcript_append = true;
        }
    } else {
        const std::string maybe_out = upper_word(words[words.size() - 2]);
        if (maybe_out == "OUT" || maybe_out == "OUTPUT") {
            out_pos = words.size() - 2;
            transcript_pos = words.size() - 1;
            transcript_append = false;
        }
    }

    if (out_pos == static_cast<size_t>(-1)) return true;
    if (out_pos == 0) {
        if (error_out) *error_out = "missing script file before OUT";
        return false;
    }

    transcript_spec = unquote_dotscript_token(words[transcript_pos]);
    if (transcript_spec.empty()) {
        if (error_out) *error_out = "missing transcript file after OUT";
        return false;
    }

    file_spec = strip_dotscript_at_prefix(unquote_dotscript_token(join_dotscript_words(words, 0, out_pos)));
    return true;
}

static inline bool has_extension(const std::string& s) {
    return std::filesystem::path(s).has_extension();
}

static std::vector<std::string> build_candidate_specs(const std::string& spec) {
    std::vector<std::string> out;
    out.push_back(spec);

    if (!has_extension(spec)) {
        out.push_back(spec + ".dts");
    }

    const std::filesystem::path p(spec);
    const bool no_parent = !p.has_parent_path();

    if (no_parent) {
        // Priority requested: scripts/ first, then tests/
        out.push_back((std::filesystem::path("scripts") / spec).string());
        if (!has_extension(spec)) out.push_back((std::filesystem::path("scripts") / (spec + ".dts")).string());

        out.push_back((std::filesystem::path("tests") / spec).string());
        if (!has_extension(spec)) out.push_back((std::filesystem::path("tests") / (spec + ".dts")).string());
    }

    // Dedup preserving order
    std::vector<std::string> dedup;
    dedup.reserve(out.size());
    for (const auto& s : out) {
        bool seen = false;
        for (const auto& d : dedup) {
            if (d == s) { seen = true; break; }
        }
        if (!seen) dedup.push_back(s);
    }
    return dedup;
}

static std::optional<std::filesystem::path> resolve_existing_script_path(
    const std::string& spec,
    std::string* attempts_out
) {
    const auto candidates = build_candidate_specs(spec);
    std::ostringstream attempts;

    for (const auto& c : candidates) {
        const auto p = shell_resolve_script_path(c);
        attempts << "  - " << c << " -> " << p.string() << "\n";
        if (std::filesystem::exists(p)) {
            if (attempts_out) *attempts_out = attempts.str();
            return p;
        }
    }

    if (attempts_out) *attempts_out = attempts.str();
    return std::nullopt;
}

static thread_local int g_dotscript_depth = 0;
static bool g_dotscript_trace = false;
static bool g_trace_banner_printed = false;

static void print_usage() {
    std::cout
        << "Usage:\n"
        << "  DOTSCRIPT USAGE\n"
        << "  DOTSCRIPT <file>\n"
        << "  DOTSCRIPT @<file>\n"
        << "  DOTSCRIPT TRACE\n"
        << "  DOTSCRIPT TRACE ON|OFF\n"
        << "  DOTSCRIPT TRACE <file>\n"
        << "  DOTSCRIPT TRACE @<file>\n"
        << "  DOTSCRIPT TRACE ON|OFF <file>\n"
        << "  DOTSCRIPT TRACE ON|OFF @<file>\n"
        << "Notes:\n"
        << "  - Bare names resolve as typed, .dts, scripts/, then tests/.\n"
        << "  - Lines beginning with *, //, &&, or ; after trimming are skipped.\n"
        << "  - DOTSCRIPT executes commands; side effects depend on script contents.\n"
        << "  - OUT/OUTPUT tees full command output to a transcript file.\n"
        << "  - Nesting is limited to main script plus one subscript.\n";
}


static bool is_dotscript_usage_request(const std::string& raw)
{
    const std::string t = upper_copy(trim_copy(raw));
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void maybe_print_trace_banner() {
    if (g_trace_banner_printed) return;
    g_trace_banner_printed = true;

    std::cout
        << "DOTSCRIPT TRACE: resolver search order:\n"
        << "  1) <typed>\n"
        << "  2) <typed>.dts (if no extension)\n"
        << "  3) scripts/<typed>(.dts) (if no parent path)\n"
        << "  4) tests/<typed>(.dts)   (if no parent path)\n";
}

} // namespace

// @dottalk.contract DOTSCRIPT TRANSCRIPT v1
// command: DOTSCRIPT
// source: cmd_dotscript.cpp
// contract_update: MDO-377G v1.1
// purpose: DOTSCRIPT executes .dts command scripts and may tee full runtime output to a transcript.
// @dottalk.usage v1
// owner: DOT|DOTSCRIPT
// command: DOTSCRIPT
// category: transcript
// status: supplemental
// usage: DOTSCRIPT <file>
// usage: DOTSCRIPT @<file>
// usage: DOTSCRIPT <file> OUT <transcript-file>
// usage: DOTSCRIPT <file> OUTPUT <transcript-file>
// usage: DOTSCRIPT TRACE <file>
// usage: DOTSCRIPT TRACE <file> OUT <transcript-file>
// usage: DOTSCRIPT <file> OUT <transcript-file> APPEND
// behavior: OUT/OUTPUT captures full command output emitted through std::cout while preserving console visibility.
// behavior: APPEND appends to an existing transcript; default OUT/OUTPUT truncates/rewrites the transcript.
// behavior: transcript capture does not make script commands safe; side effects still depend on script contents.
// boundary: transcript capture itself does not mutate DBF/CDX/LMDB, MAN*/MANSTAR, reader pointers, HELP, or CMDHELPCHK.
// note: TEST is intentionally not refactored in this patch; TEST may become a later consumer of shell_transcript.
// provenance: MDO-377G v1.1 shell transcript service source patch with usage-contract update.
// @dottalk.contract.end

void cmd_DOTSCRIPT(DbArea& area, std::istringstream& args)
{
    std::string rest;
    std::getline(args, rest);
    rest = trim_copy(std::move(rest));

    if (rest.empty() || is_dotscript_usage_request(rest)) {
        print_usage();
        return;
    }

    bool trace_for_this_run = g_dotscript_trace;
    std::string file_spec;
    std::string transcript_spec;
    bool transcript_append = false;

    {
        std::istringstream ss(rest);
        std::string t1;
        ss >> t1;

        if (t1.empty()) {
            print_usage();
            return;
        }

        const std::string t1u = upper_copy(t1);

        if (t1u == "TRACE") {
            std::string t2;
            if (!(ss >> t2) || t2.empty()) {
                std::cout << "DOTSCRIPT TRACE is " << (g_dotscript_trace ? "ON" : "OFF") << "\n";
                print_usage();
                return;
            }

            const std::string t2u = upper_copy(t2);

            if (t2u == "ON" || t2u == "OFF") {
                g_dotscript_trace = (t2u == "ON");
                trace_for_this_run = g_dotscript_trace;

                std::string tail;
                std::getline(ss, tail);
                tail = strip_at_prefix(unquote_copy(std::move(tail)));
                if (tail.empty()) {
                    std::cout << "DOTSCRIPT TRACE is now " << (g_dotscript_trace ? "ON" : "OFF") << "\n";
                    return;
                }
                file_spec = tail;
            } else {
                // TRACE <file...> => run once with trace ON; global unchanged.
                trace_for_this_run = true;

                std::string tail;
                std::getline(ss, tail);
                tail = trim_copy(std::move(tail));

                std::string joined = t2;
                if (!tail.empty()) joined += " " + tail;

                file_spec = strip_at_prefix(unquote_copy(std::move(joined)));
            }
        } else {
            // DOTSCRIPT <file...> or DOTSCRIPT @<file...>
            file_spec = strip_at_prefix(unquote_copy(std::move(rest)));
        }
    }

    std::string transcript_error;
    if (!extract_dotscript_output_clause(file_spec, transcript_spec, transcript_append, &transcript_error)) {
        std::cout << "DOTSCRIPT: " << transcript_error << "\n";
        return;
    }

    if (file_spec.empty()) {
        print_usage();
        return;
    }

    // One-level controlled subscript: allow main + 1 subscript; block deeper.
    if (g_dotscript_depth >= 2) {
        std::cout << "DOTSCRIPT: nesting limit reached (max 1 subscript).\n";
        return;
    }

    if (trace_for_this_run) {
        maybe_print_trace_banner();
    }

    std::string attempts;
    const auto resolved = resolve_existing_script_path(file_spec, &attempts);
    if (!resolved) {
        std::cout << "DOTSCRIPT: script not found.\n" << attempts;
        return;
    }

    std::optional<shell_transcript::ScopedShellTranscript> transcript_guard;
    if (!transcript_spec.empty()) {
        std::string transcript_open_error;
        transcript_guard.emplace(
            std::filesystem::path(transcript_spec),
            transcript_append,
            true,
            false,
            &transcript_open_error
        );
        if (!transcript_guard->ok()) {
            std::cout << "DOTSCRIPT: transcript open failed: " << transcript_open_error << "\n";
            return;
        }
        std::cout << "DOTSCRIPT OUT: " << transcript_spec
                  << (transcript_append ? " (append)" : " (write)") << "\n";
    }

    if (trace_for_this_run) {
        std::cout << "DOTSCRIPT TRACE: resolved: " << resolved->string() << "\n";
    }

    const bool as_subscript = shell_script_active();

    std::string push_err;
    if (!shell_script_push(*resolved, as_subscript, &push_err)) {
        std::cout << "DOTSCRIPT: " << push_err << ": " << resolved->string() << "\n";
        return;
    }

    ScopeExit pop_guard{[] { shell_script_pop(); }};
    ++g_dotscript_depth;
    ScopeExit depth_guard{[] { --g_dotscript_depth; }};

    std::ifstream in(*resolved, std::ios::binary);
    if (!in) {
        std::cout << "DOTSCRIPT: unable to open '" << resolved->string() << "'\n";
        return;
    }

    std::string line;
    size_t lineno = 0;      // physical lines consumed so far
    int consumed = 0;

    // Read logical commands: read_script_command joins ';'-continued lines the
    // same way the interactive shell does, so multi-line CREATE (and any other
    // continued command) behaves identically under DOTSCRIPT. cmd_start is the
    // first physical line of the command, for accurate trace/error reporting.
    while (read_script_command(in, line, consumed)) {
        const size_t cmd_start = lineno + 1;
        lineno += static_cast<size_t>(consumed > 0 ? consumed : 1);

        const std::string trimmed = trim_copy(line);
        if (looks_like_comment_or_blank(trimmed)) continue;

        if (trace_for_this_run) {
            std::cout << resolved->string() << ":" << cmd_start << "> " << trimmed << "\n";
        }

        DbArea& cur = current_shell_area_or(area);
        const auto err_gen0 = xbase::error::error_generation();
        if (!shell_execute_line(cur, trimmed)) {
            std::cout << "DOTSCRIPT: " << resolved->string() << ":" << cmd_start
                      << ": Unknown command: " << trimmed << "\n";
        }

        // stop_on_error[severity]: abort the run if this line recorded a new
        // error at or above the configured threshold.
        if (xbase::error::errorstop_tripped(err_gen0)) {
            std::cout << "DOTSCRIPT: " << resolved->string() << ":" << cmd_start
                      << ": stopped (STOP_ON_ERROR "
                      << xbase::error::errorstop_level_name(xbase::error::get_errorstop())
                      << ")\n";
            break;
        }
    }
}
