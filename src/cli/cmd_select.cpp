// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_select.cpp ? SELECT <area#|name>
// Supports selecting by numeric slot (0..N-1) or by name/label (case-insensitive).
// Name matching checks workareas::name(i) and the DBF base name from DbArea::filename().
//
// Output style (matches your UX):
//   Selected area 9.
//   Current area: 9
//     File: <path>  Recs: <count>  Recno: <current>
//
// Deps: workareas.hpp, xbase.hpp

// @dottalk.usage v1
// owner: DOT|SELECT
// command: SELECT
// category: workspace
// status: supported
// noargs: usage
// effect: select
// mutates: current-area
// usage-access: SELECT USAGE
// summary:
//   Select the current work area by numeric slot or by work-area/table name.
//
// usage:
//   SELECT USAGE
//   SELECT <n>
//   SELECT <name>
//   SELECT <table.dbf>
//   SELECT <workspace>:<name>
//
// notes:
//   SELECT with no arguments prints usage with the current valid slot range.
//   SELECT USAGE prints usage and does not change the current area.
//   Numeric selection uses the current workarea slot count and is ABSOLUTE --
//   a slot number names an engine area in any workspace.
//   An UNQUALIFIED name resolves inside the CURRENT workspace only (Q8, closed
//   2026-08-27). A name open only in another workspace is REFUSED, and the
//   refusal names the workspace and area it is actually in.
//   The QUALIFIED form is <workspace>:<name> (R134, 2026-08-31). The colon
//   separates the workspace from the table; a field would follow on a dot,
//   WS:TABLE.FIELD, which SELECT does not take because it selects areas.
//   Name selection matches workarea labels and open DBF base names case-insensitively.
//   SELECT mutates current-area/session state but does not mutate table data.
//
// risk:
//   mutates_current_area: yes
//   mutates_table_data: no
//
// related:
//   AREA
//   DBAREA
//   WORKSPACE
//

#include <string>
#include <sstream>
#include <iostream>
#include <algorithm>
#include <cctype>
#include <cstdint>
#include <limits>
#include <vector>

#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
#include "xbase.hpp"
#include "xbase/workspace_membership.hpp"
#include "workareas.hpp"

// Provided by the shell (C linkage there)
extern "C" xbase::XBaseEngine* shell_engine();

// ----------------- helpers -----------------

static std::string to_upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return (char)std::toupper(c); });
    return s;
}

static std::string base_name_upper_from_cstr(const char* pathLike) {
    if (!pathLike) return {};
    std::string s(pathLike);
    for (char& c : s) if (c == '\\') c = '/';
    if (auto pos = s.find_last_of('/'); pos != std::string::npos) s.erase(0, pos + 1);
    std::string S = to_upper(s);
    const std::string ext = ".DBF";
    if (S.size() >= ext.size() && S.substr(S.size() - ext.size()) == ext) {
        S.erase(S.size() - ext.size());
    }
    return S;
}

static std::string base_name_upper_from_str(const std::string& pathLike) {
    return base_name_upper_from_cstr(pathLike.c_str());
}

// ---------------------------------------------------------------------------
// WHICH WORKSPACE OWNS ENGINE SLOT i.
//
// 0 means NO WORKSPACE CLAIMS IT, which for an OPEN area is invariant I1
// violated. Reported by WORKDESK; not this verb's business to repair, and a
// slot in that state is deliberately not matched here -- selecting an area
// nobody owns would make the violation harder to see, not easier.
static std::uint64_t owner_of(std::size_t i) {
    return xbase::workspace::owner_of_slot(static_cast<std::int32_t>(i));
}

// THE THREE WAYS A NAME CAN NAME AN AREA, unchanged from the original loop and
// deliberately kept HERE rather than delegated to
// cli::find_open_area_in_workspace_ci(). That resolver matches the LOGICAL NAME
// only; this verb has always also matched the DBF basename and tolerated a
// trailing .DBF, and dropping either would be a silent narrowing of SELECT
// wearing a scoping fix's clothes.
static bool area_answers_to(std::size_t i,
                            const std::string& wantU,
                            const std::string& wantBase) {
    const char* label   = workareas::name(i);
    const std::string labU    = to_upper(label ? std::string(label) : std::string());
    const std::string labBase = base_name_upper_from_cstr(label);

    if (!labU.empty()    && labU    == wantU)    return true;
    if (!labBase.empty() && labBase == wantBase) return true;

    const xbase::DbArea* a = workareas::db(i);
    if (a && a->isOpen()) {
        const std::string fileBase = base_name_upper_from_str(a->filename());
        if (!fileBase.empty() && fileBase == wantBase) return true;
    }
    return false;
}

// Every OPEN area answering to this name, ascending by slot, regardless of
// workspace. Used ONLY to write a refusal that says where the table actually
// is -- never to select one.
static std::vector<std::size_t> all_slots_answering(const std::string& wantU,
                                                    const std::string& wantBase) {
    std::vector<std::size_t> hits;
    for (std::size_t i = 0; i < workareas::count(); ++i) {
        const xbase::DbArea* a = workareas::db(i);
        if (!a || !a->isOpen()) continue;
        if (area_answers_to(i, wantU, wantBase)) hits.push_back(i);
    }
    return hits;
}

static bool try_parse_int(const std::string& s, int& out) {
    if (s.empty()) return false;
    size_t i = 0;
    if (s[0] == '+' || s[0] == '-') i = 1;
    for (; i < s.size(); ++i)
        if (!std::isdigit(static_cast<unsigned char>(s[i]))) return false;
    try {
        long long v = std::stoll(s);
        if (v < std::numeric_limits<int>::min() || v > std::numeric_limits<int>::max()) return false;
        out = static_cast<int>(v);
        return true;
    } catch (...) { return false; }
}

// ----------------- command -----------------

static void print_select_usage()
{
    const size_t cnt = workareas::count();
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SelectUsageText,
        {{"max_slot", std::to_string(cnt ? static_cast<int>(cnt - 1) : 0)}});

    // THE QUALIFIED FORM IS PRINTED HERE AND NOT IN THE CATALOG, because the
    // catalog entry is messaging-lane property and this verb should not be the
    // thing that edits it. A reader who has just been refused an unqualified
    // name needs the spelling in front of them, not in another lane's backlog.
    cli::cmdout::print_line(
        "  SELECT <workspace>:<name>   -- a table in another workspace");
    cli::cmdout::print_line(
        "  An unqualified name resolves in the CURRENT workspace only.");
    cli::cmdout::print_line(
        "  A slot number is absolute. WORKDESK lists workspaces and their areas.");
}

void cmd_SELECT(xbase::DbArea& /*A*/, std::istringstream& iss) {
    xbase::XBaseEngine* eng = shell_engine();
    if (!eng) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::SelectEngineUnavailableText);
        return;
    }

    std::string arg;
    if (!(iss >> arg) || arg.empty()) {
        print_select_usage();
        return;
    }

    const std::string argU0 = to_upper(arg);
    if (argU0 == "USAGE" || argU0 == "HELP" || argU0 == "?") {
        print_select_usage();
        return;
    }

    // Allow quoted names
    if (arg.size() >= 2 && ((arg.front() == '"' && arg.back() == '"') ||
                            (arg.front() == '\'' && arg.back() == '\''))) {
        arg = arg.substr(1, arg.size() - 2);
    }

    int idx = -1;

    // numeric?
    int nParsed = -1;
    if (try_parse_int(arg, nParsed)) {
        const size_t cnt = workareas::count();
        if (nParsed < 0 || (size_t)nParsed >= cnt) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::SelectOutOfRangeText,
                {{"max_slot", std::to_string(cnt ? static_cast<int>(cnt - 1) : 0)}});
            return;
        }
        idx = nParsed;
    } else {
        // -------------------------------------------------------------------
        // BY NAME, AND THE NAME IS SCOPED (Q8, closed 2026-08-27; R134,
        // 2026-08-31).
        //
        // Q8: an UNQUALIFIED name resolves to the CURRENT workspace's member.
        // R134: the alias is the path, COMPOSED not stored -- the qualified
        // form is `WS:TABLE`, the alias namespace is global, and logicalName()
        // keeps returning the bare name.
        //
        // UNTIL 2026-09-11 THIS SWEPT EVERY ENGINE SLOT AND TOOK THE FIRST
        // MATCH. Measured live the same day: standing in ws3 holding its own
        // STUDENTS at area 34, `SELECT STUDENTS` selected area 8 -- DEFAULT's
        // -- and reported `Selected area 8.` as a clean success. Three
        // workspaces held twelve doubled names between them, so twelve tables
        // were unreachable by name and one was reachable by accident.
        //
        // A BRACKET SPELLING IS NOT ACCEPTED, deliberately: `ws[3]:students`
        // was considered and WITHDRAWN, and the dotted `WS.#n.TABLE` form that
        // src/reference/qualified_reference.cpp parses is the older R112/I4
        // surface that R134 supersedes. Wiring that parser in here would ship a
        // second address spelling beside the ruled one, which is the exact
        // thing the withdrawal was for.
        // -------------------------------------------------------------------

        std::string ws_token;                 // empty = unqualified
        std::string name_token = arg;

        if (const auto colon = arg.find(':'); colon != std::string::npos) {
            ws_token   = arg.substr(0, colon);
            name_token = arg.substr(colon + 1);

            if (ws_token.empty() || name_token.empty()) {
                cli::cmdout::print_line(
                    "SELECT: refused -- a qualified name is WS:TABLE, and both "
                    "halves are required. Nothing was selected.");
                return;
            }
        }

        std::string wantU = to_upper(name_token);
        std::string wantBase = wantU;
        if (wantBase.size() > 4 && wantBase.substr(wantBase.size() - 4) == ".DBF") {
            wantBase.erase(wantBase.size() - 4);
        }

        // WHICH WORKSPACE ARE WE ASKING? The current one, or the one named.
        std::uint64_t scope = xbase::workspace::current_handle();
        if (!ws_token.empty()) {
            scope = xbase::workspace::find_by_name_ci(ws_token);
            if (scope == 0) {
                // 0 is not a legal handle, which is what lets it mean "no such
                // workspace" without a second return channel.
                cli::cmdout::print_line(
                    "SELECT: no workspace named '" + ws_token +
                    "'. WORKDESK lists the open ones. Nothing was selected.");
                return;
            }
        }

        for (std::size_t i = 0; i < workareas::count(); ++i) {
            const xbase::DbArea* a = workareas::db(i);
            if (!a || !a->isOpen()) continue;
            if (owner_of(i) != scope) continue;
            if (!area_answers_to(i, wantU, wantBase)) continue;
            idx = static_cast<int>(i);
            break;
        }

        if (idx < 0) {
            // ABSENT HERE IS ABSENT -- the resolver contract, and this verb does
            // not fall back to another workspace. But a CLI verb HAS SOMEBODY TO
            // TELL, which an engine path does not, so the refusal says where the
            // table actually is instead of leaving the operator to run WORKDESK
            // and work it out. That sentence is the whole difference between a
            // scoping fix and a scoping regression.
            const std::vector<std::size_t> elsewhere =
                all_slots_answering(wantU, wantBase);

            std::string msg = "SELECT: '" + name_token + "' is not open in " +
                              xbase::workspace::name_of(scope);

            // The suggested spelling comes from the FIRST WORKSPACE ACTUALLY
            // NAMED in this message, not from elsewhere.front(). They are the
            // same slot today because the scoped loop above already consumed
            // every in-scope match -- but "the same by argument" is how a
            // message comes to suggest `<current-ws>:NAME`, which is the one
            // spelling guaranteed not to work.
            std::uint64_t suggest_ws = 0;
            for (const std::size_t i : elsewhere) {
                const std::uint64_t own = owner_of(i);
                if (own == scope) continue;
                if (suggest_ws == 0) { msg += ". It IS open in"; suggest_ws = own; }
                else                 { msg += ","; }
                msg += " " + xbase::workspace::name_of(own) +
                       " (area " + std::to_string(i) + ")";
            }

            if (suggest_ws != 0) {
                msg += " -- qualify it, e.g. " +
                       xbase::workspace::name_of(suggest_ws) +
                       ":" + wantBase + ". Nothing was selected.";
            } else {
                const std::size_t cnt = workareas::count();
                msg += ", and no open area anywhere answers to it. Use SELECT "
                       "<0.." +
                       std::to_string(cnt ? static_cast<int>(cnt - 1) : 0) +
                       "> or a known name. Nothing was selected.";
            }

            cli::cmdout::print_line(msg);
            return;
        }
    }

    // Perform selection & echo
    eng->selectArea((size_t)idx);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SelectSelectedAreaText,
        {{"slot", std::to_string(idx)}});

    const xbase::DbArea* cur = workareas::db((size_t)idx);
    if (cur && cur->isOpen()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SelectCurrentAreaText,
            {{"slot", std::to_string(idx)}});
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SelectCurrentAreaFileSummaryText,
            {
                {"path", cur->filename()},
                {"recs", std::to_string(cur->recCount())},
                {"recno", std::to_string(cur->recno())}
            });
    } else {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SelectCurrentAreaText,
            {{"slot", std::to_string(idx)}});
    }
}




