// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_rel.cpp
// REL command dispatcher. Keeps REL subcommand parsing in one place and forwards
// to the underlying RELATIONS / SET RELATIONS / JOIN / ENUM handlers.

// @dottalk.usage v1
// owner: DOT|REL
// command: REL
// category: relations
// status: supported
// noargs: usage
// effect: dispatch
// mutates: depends-on-subcommand
// usage-access: REL; REL USAGE
// summary:
//   Dispatch relation list, refresh, join, enumeration, persistence, add, and clear operations.
// usage:
//   REL
//   REL USAGE
//   REL LIST [ALL]
//   REL REFRESH
//   REL JOIN [ONE] [DISTINCT|ALL] [LIMIT <n>] [<child1> <child2> ...] TUPLE <alias>.<field>[, ...]
//   REL ENUM [DISTINCT|ALL] [LIMIT <n>] [<child1> <child2> ...] TUPLE <alias>.<field>[, ...]
//   REL SAVE [path] | REL SAVE AS <dataset>
//   REL LOAD [path] | REL LOAD AS <dataset>
//   REL ADD <parent> <child> ON <field>[,<field>...]
//   REL ADD <parent> <child> ON <parent_field> TO <child_field>
//   REL CLEAR <parent>|ALL
//   REL SCANLIMIT [<n>]
// notes:
//   REL forwards each subcommand to the owning relation handler.
//   REL ADD and REL CLEAR mutate relation definitions; REL REFRESH refreshes relation state.
//   REL SCANLIMIT reports or sets the relation engine's PER-HOP record budget.
//   It caps what a traversal FINDS, not what is displayed: lowering it changes
//   match counts and drops join rows. ERSATZ LIMIT is the display cap.
//   Shipped since AIF-074 P1.3 and absent from this contract until 2026-08-28.
//   ONE is REL JOIN ONLY and REL ENUM DOES NOT ACCEPT IT -- the two lines are
//   deliberately not identical. ONE emits a single row from the CURRENT relation
//   pointers; given a child chain it REFUSES rather than discarding it (AIF-147),
//   because reporting success for a traversal that never happened is the shape
//   this codebase hunts.
//   DISTINCT de-duplicates tuples (FIELD LISTS ONLY); ALL allows duplicates and
//   is the default, overriding DISTINCT. Both are real on both verbs -- DISTINCT
//   is backed by a seen-set, not parsed and ignored. Wording here is taken from
//   MessageId::RelJoinUsageText rather than restated, because that catalog entry
//   is the authority and had all three flags documented correctly the whole time.
//   TUPLE takes a COMMA-SEPARATED <alias>.<field> list, not an expression. The
//   proven spelling is in data/scripts/main/rel_join_enum_regression.dts.
//   CONTRACT SWEEP, 2026-09-03. REL JOIN's usage had THREE HOMES and only the
//   newest was right:
//     1. this comment block            -- LIMIT and TUPLE only        (was stale)
//     2. rel_usage() below, printed by REL USAGE  -- same omission     (was stale)
//     3. MessageId::RelJoinUsageText, printed by a bare REL JOIN
//        -- ONE, DISTINCT and ALL, each with a description            (CORRECT)
//   So the answer a user got depended on HOW THEY ASKED: `REL USAGE` returned an
//   incomplete list and `REL JOIN` with no arguments returned the complete one.
//   Same question, two answers, decided by route. Homes 1 and 2 now quote home 3.
//   The SCANLIMIT note above records this same defect closed for ONE keyword on
//   2026-08-28; that fix corrected its line and did not sweep the block it was
//   standing in, which is how the rest survived.
//   WHEN A KEYWORD IS ADDED TO A PARSER HERE: update the catalog entry, then make
//   BOTH copies in this file quote it. Do not restate it in a third voice.
// related:
//   SET RELATION, SET RELATIONS, RELATIONS, TUPLE, WORKSPACE
//

#include "cmd_rel.hpp"

#include "cmd_relations.hpp"   // cmd_RELATIONS_LIST/REFRESH/SAVE/LOAD, cmd_REL_JOIN, cmd_REL_ENUM
#include "set_relations.hpp"   // cmd_SET_RELATIONS + relations_api helpers
#include "textio.hpp"

#include <cstddef>
#include <iostream>
#include <sstream>
#include <string>

namespace {

static void rel_usage() {
    std::cout
        << "REL syntax\n"
        << "  REL LIST [ALL]\n"
        << "  REL REFRESH\n"
        << "  REL JOIN [ONE] [DISTINCT|ALL] [LIMIT <n>] [<child> ...] TUPLE <alias>.<field>[, ...]\n"
        << "  REL ENUM [DISTINCT|ALL] [LIMIT <n>] [<child> ...] TUPLE <alias>.<field>[, ...]\n"
        << "      ONE       emit exactly one row using the current relation context (REL JOIN only;\n"
        << "                refuses a child chain rather than discarding it)\n"
        << "      DISTINCT  de-duplicate tuples (field lists only)\n"
        << "      ALL       allow duplicates (default; overrides DISTINCT)\n"
        << "  REL SAVE [path] | REL SAVE AS <dataset>\n"
        << "  REL LOAD [path] | REL LOAD AS <dataset>\n"
        << "  REL ADD <parent> <child> ON <field>[,<field>...]      # same-field relation\n"
        << "  REL ADD <parent> <child> ON <parent_field> TO <child_field>  # asymmetric relation\n"
        << "  REL CLEAR <parent>|ALL                   # alias of SET RELATIONS CLEAR\n"
        << "  REL SCANLIMIT [<n>]                      # records scanned PER HOP -- caps what is FOUND\n"
        << "                                           # (for a shorter SCREEN, use ERSATZ LIMIT)\n";
}

static std::string up(std::string s) { return textio::up(std::move(s)); }

} // namespace

void cmd_REL(xbase::DbArea& area, std::istringstream& in) {
    std::string sub;
    if (!(in >> sub)) {
        rel_usage();
        return;
    }
    sub = up(sub);

    // AIF-074 P1.3 (RDB-06): fresh truncation latch per REL command, so the
    // once-per-cycle warning fires again if this command hits the scan limit.
    relations_api::clear_scan_truncated();

    if (sub == "LIST") {
        // REL LIST           -> existing one-hop display (via cmd_RELATIONS_LIST)
        // REL LIST ALL       -> recursive tree display (engine-side, cursor-safe)
        const std::streampos pos = in.tellg();
        std::string maybe;

        if (in >> maybe) {
            const std::string flag = up(maybe);
            if (flag == "ALL") {
                auto rows = relations_api::list_tree_for_current_parent(/*recursive=*/true, /*max_depth=*/24);
                if (rows.empty()) {
                    std::cout << "(no relations)\n";
                    return;
                }

                std::cout << "Relations (tree) rooted at: " << rows[0].line << "\n";
                for (std::size_t i = 0; i < rows.size(); ++i) {
                    std::cout << rows[i].line << "\n";
                }
                return;
            }
        }

        // Restore stream position if we consumed a non-ALL token (or hit EOF).
        in.clear();
        if (pos != std::streampos(-1)) {
            in.seekg(pos);
        }

        cmd_RELATIONS_LIST(area, in);
        return;
    }
    if (sub == "REFRESH") {
        cmd_RELATIONS_REFRESH(area, in);
        return;
    }
    if (sub == "SAVE") {
        cmd_REL_SAVE(area, in);
        return;
    }
    if (sub == "LOAD") {
        cmd_REL_LOAD(area, in);
        return;
    }
    if (sub == "JOIN") {
        cmd_REL_JOIN(area, in);
        return;
    }
    if (sub == "ENUM") {
        cmd_REL_ENUM(area, in);
        return;
    }

    // Aliases to SET RELATIONS
    if (sub == "SCANLIMIT") {
        // AIF-074 P1.3: CLI reach for the relation scan limit (closes AIF-073
        // OQ-1). No argument reports; a positive integer sets.
        std::string nTok;
        if (!(in >> nTok)) {
            std::cout
                << "REL: scan limit is " << relations_api::scan_limit()
                << " record(s) per relation hop.\n"
                << "REL: this caps what the relation engine FINDS, not what is displayed --\n"
                << "REL: lowering it changes match counts and drops join rows. For a shorter\n"
                << "REL: screen without changing answers, use ERSATZ LIMIT <n>.\n";
            return;
        }
        char* end = nullptr;
        const unsigned long long v = std::strtoull(nTok.c_str(), &end, 10);
        if (!end || *end != '\0' || v == 0ULL) {
            std::cout << "REL: SCANLIMIT expects a positive integer.\n";
            return;
        }
        relations_api::set_scan_limit(static_cast<std::size_t>(v));
        std::cout
            << "REL: scan limit set to " << relations_api::scan_limit()
            << " record(s) per relation hop -- this changes ANSWERS, not just display.\n";
        return;
    }

    if (sub == "ADD" || sub == "CLEAR") {
        std::string rest;
        std::getline(in, rest);
        std::istringstream tmp(sub + rest);
        cmd_SET_RELATIONS(area, tmp);
        return;
    }

    // AIF-147 sec 3a: this fallthrough printed usage and NOTHING ELSE, so an
    // unknown subcommand was indistinguishable from a deliberate `REL USAGE`.
    // Someone who typed a form the command does not have concluded they had
    // mistyped their HELP request -- the one reading that guarantees they never
    // report it. That is the AIF-118 shape wearing good manners: printing usage
    // for an unknown subcommand is ordinarily courteous, and here it is what
    // hid the defect.
    //
    // Naming the rejected token does NOT decide AIF-147 R-e -- whether
    // `RELATIONS ALL` should reach cmd_RELATIONS_LIST at all. It is true under
    // every one of that ruling's three options, which is why it can land first.
    std::cout << "REL: unknown subcommand '" << sub << "'.\n";

    // ALL is called out by name because it is the token this defect was found
    // through. `RELATIONS ALL` is documented as a working form in three places
    // (cmd_relations.cpp usage block, its notes, and dotref.hpp) and is
    // rewritten to `REL ALL` before dispatch (shell_api_extras.cpp), so it
    // lands HERE and was answered with usage. Pointing at the spelling that
    // works is a HINT, not a routing change; the routing is R-e's to decide.
    if (sub == "ALL") {
        std::cout
            << "REL: did you mean REL LIST ALL?\n"
            << "REL: note -- RELATIONS ALL is rewritten to REL ALL before\n"
            << "REL:         dispatch, so it arrives here rather than at the\n"
            << "REL:         RELATIONS handler. See AIF-147.\n";
    }

    rel_usage();
}
