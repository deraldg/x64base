// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported
//
// AIF-078 decision-owed #6 (plan sec 11i): settle merge_relation.
//
// Every arm compares a VALUE the parser or the merge reports. Nothing here
// touches the filesystem and nothing links the engine -- relation_parse.cpp
// is text in, rows out, which is the whole reason it was lifted out of
// session.cpp's anonymous namespace.
//
// TWO ARMS PIN DEFECTS RATHER THAN CONTRACTS, and they say so in their own
// failure text. They exist so that FIXING the defect turns them red on
// purpose, which is the only way a fixture can hold a known-wrong behaviour
// without quietly blessing it. Neither is a claim that the behaviour is right.

#include "gui/core/relation_parse.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace {

using dottalk::gui::WorkspaceRelationInfo;
using dottalk::gui::merge_relation;
using dottalk::gui::parse_relation_edges_from_output;

bool require(bool condition, const std::string& message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        return false;
    }
    return true;
}

// What the posture reader in session.cpp builds: keys, no count. Modelled
// rather than invoked -- that parser also constructs areas, so it stayed in
// session.cpp. This mirrors its three assignments exactly.
WorkspaceRelationInfo from_posture(const std::string& ws,
                                   const std::string& parent,
                                   const std::string& child,
                                   const std::string& key) {
    WorkspaceRelationInfo r;
    r.workspace = ws;
    r.parent = parent;
    r.child = child;
    r.parent_key = key;
    r.child_key = key;
    r.source = "DTSchema";
    return r;
}

// A real REL LIST ALL transcript. Header line, the root repeated as a row
// (cmd_rel.cpp prints rows[0] twice, once as the header), then depth 1 at two
// spaces and depth 2 at four -- set_relations.cpp builds the indent as
// depth * 2.
const char* kTree =
    "Relations (tree) rooted at: STUDENTS\n"
    "STUDENTS\n"
    "  -> ENROLL ON SID  (matches: 12)\n"
    "    -> COURSES ON CID  (matches: n/a)\n";

} // namespace

int main() {
    // ---- G0: the fixture, asserted before anything is claimed about it ----
    {
        const auto rows = parse_relation_edges_from_output(kTree, "DEFAULT");
        if (!require(rows.size() == 2,
                     "G0: the sample transcript did not yield two edges")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T1: the OWNING WORKSPACE is part of a relation's identity --------
    // The I1.2 defect: two edges differing only by workspace fused into one.
    {
        std::vector<WorkspaceRelationInfo> rows;
        for (auto r : parse_relation_edges_from_output(kTree, "ALPHA")) {
            merge_relation(rows, std::move(r));
        }
        for (auto r : parse_relation_edges_from_output(kTree, "BETA")) {
            merge_relation(rows, std::move(r));
        }
        if (!require(rows.size() == 4,
                     "T1: same edges in two workspaces did not stay distinct")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T2: the same edge on the same key is ONE row ---------------------
    {
        std::vector<WorkspaceRelationInfo> rows;
        for (auto r : parse_relation_edges_from_output(kTree, "DEFAULT")) {
            merge_relation(rows, std::move(r));
        }
        merge_relation(rows, from_posture("DEFAULT", "STUDENTS", "ENROLL", "SID"));
        if (!require(rows.size() == 2, "T2: an exact key match did not fuse")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T3: two keys on one edge are TWO relations, not one -------------
    // P->C ON SID and P->C ON CLS_ID are different relations. This is what
    // deleting the keyless fallback had to leave standing.
    {
        std::vector<WorkspaceRelationInfo> rows;
        merge_relation(rows, from_posture("DEFAULT", "STUDENTS", "ENROLL", "SID"));
        merge_relation(rows, from_posture("DEFAULT", "STUDENTS", "ENROLL", "CLS_ID"));
        if (!require(rows.size() == 2,
                     "T3: two differently-keyed edges collapsed into one")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T4: R6.3 at the PRODUCER -- a keyless line is not a relation ----
    // No relation in this tree is keyless: add_relation refuses empty field
    // lists (set_relations.cpp:570), so format_on_fields never returns empty.
    // A `-> something` with no ` ON ` is arbitrary command output shaped like
    // a relation, and the parser drops it WHOLE -- no row, and no tree_stack
    // push, so nothing nests under a parent that was never a parent.
    {
        const char* noise =
            "Areas\n"
            "  -> SCRATCH\n"
            "    -> DEEPER ON X\n";
        const auto rows = parse_relation_edges_from_output(noise, "DEFAULT");
        if (!require(rows.size() == 1,
                     "T4: a keyless line was minted as a relation")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[0].parent == "Areas",
                     "T4: a dropped keyless line still nested its children")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T5: R6 -- an uncomputed count is ABSENT, a measured zero is 0 ----
    // THE DISCRIMINATOR. set_relations.cpp:1010 prints "(matches: n/a)" when
    // it could not compute one. That used to become 0 via value_or(0), and
    // main_frame.cpp showed the user "0". If these two ever compare equal
    // again, absence has been folded back into the space of present values.
    {
        const auto rows = parse_relation_edges_from_output(kTree, "DEFAULT");
        if (!require(rows[0].match_count.has_value() && *rows[0].match_count == 12,
                     "T5: a measured count of 12 did not survive")) {
            return EXIT_FAILURE;
        }
        if (!require(!rows[1].match_count.has_value(),
                     "T5: (matches: n/a) was recorded as a number")) {
            return EXIT_FAILURE;
        }

        const auto zero = parse_relation_edges_from_output(
            "P\n  -> C ON K  (matches: 0)\n", "DEFAULT");
        if (!require(zero.size() == 1 && zero[0].match_count.has_value() &&
                     *zero[0].match_count == 0,
                     "T5: a measured ZERO was not recorded as a zero")) {
            return EXIT_FAILURE;
        }
        if (!require(zero[0].match_count != rows[1].match_count,
                     "T5: a measured zero and an uncomputed count compare EQUAL")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T6: identity-bearing fields are ORDER-INDEPENDENT ---------------
    // ... and `source` is NOT, which is pinned rather than asserted away:
    // the fill-in is last-writer-wins.
    {
        std::vector<WorkspaceRelationInfo> tree_first;
        for (auto r : parse_relation_edges_from_output(kTree, "DEFAULT")) {
            merge_relation(tree_first, std::move(r));
        }
        merge_relation(tree_first, from_posture("DEFAULT", "STUDENTS", "ENROLL", "SID"));

        std::vector<WorkspaceRelationInfo> posture_first;
        merge_relation(posture_first, from_posture("DEFAULT", "STUDENTS", "ENROLL", "SID"));
        for (auto r : parse_relation_edges_from_output(kTree, "DEFAULT")) {
            merge_relation(posture_first, std::move(r));
        }

        if (!require(tree_first.size() == posture_first.size(),
                     "T6: the two orders produced different row counts")) {
            return EXIT_FAILURE;
        }
        for (std::size_t i = 0; i < tree_first.size(); ++i) {
            const auto& a = tree_first[i];
            const auto& b = posture_first[i];
            if (!require(a.workspace == b.workspace && a.parent == b.parent &&
                         a.child == b.child && a.parent_key == b.parent_key &&
                         a.match_count == b.match_count,
                         "T6: an identity-bearing field depended on merge order")) {
                return EXIT_FAILURE;
            }
        }
        if (!require(tree_first[0].source != posture_first[0].source,
                     "T6 PIN: `source` is last-writer-wins and this arm records "
                     "that. If it just went order-independent, the pin is stale "
                     "-- delete this assertion, do not weaken the one above")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T7 PIN: the ` TO ` clause is NOT parsed (finding 4a) -------------
    // set_relations.cpp:894 emits `ON <parent-csv> TO <child-csv>` whenever the
    // two field lists differ, and SET RELATIONS ADD ... ON a TO b is shipped
    // grammar (cmd_relations.cpp:418-455). The parser takes everything after
    // " ON " as ONE key and copies it to the child side. gui_workspace_format
    // .cpp measured the cost: 190 of 1,102 RELATION lines (17.2%) in the live
    // catalog carry an explicit TO, and its ` TO ` renderer -- which fires only
    // when child_key != parent_key -- can therefore never fire.
    //
    // PINNED, NOT BLESSED. When 4a lands, parent_key becomes "SID,TERM" and
    // child_key "STU_ID,TERM_CD", and this arm goes red on purpose.
    {
        const auto rows = parse_relation_edges_from_output(
            "P\n  -> C ON SID,TERM TO STU_ID,TERM_CD  (matches: 3)\n", "DEFAULT");
        if (!require(rows.size() == 1, "T7: the TO-form line did not parse at all")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[0].parent_key == "SID,TERM TO STU_ID,TERM_CD" &&
                     rows[0].child_key == rows[0].parent_key,
                     "T7 PIN: the TO clause is now split -- finding 4a has been "
                     "fixed, so DELETE this arm and assert the correct split")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T8 PIN: the tree FLATTENS below depth 1 (finding 4e, new) --------
    // The producer indents by depth * 2 (set_relations.cpp), so depth 1 is two
    // spaces and depth 2 is four. The parser pops while
    // `tree_stack.back().first >= indent` but pushes at `indent + 2`, so a
    // depth-2 line at indent 4 pops the depth-1 entry that was stored at 4 and
    // is attributed to the ROOT. COURSES is a child of ENROLL and is recorded
    // as a child of STUDENTS. Either the push should be `indent` or the pop
    // should be `>`; the two do not currently agree.
    //
    // PINNED, NOT BLESSED. Fixing it makes this arm red on purpose.
    {
        const auto rows = parse_relation_edges_from_output(kTree, "DEFAULT");
        if (!require(rows[1].child == "COURSES", "T8: the depth-2 edge is missing")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[1].parent == "STUDENTS",
                     "T8 PIN: the depth-2 edge now names its real parent -- "
                     "finding 4e has been fixed, so DELETE this arm and assert "
                     "parent == ENROLL")) {
            return EXIT_FAILURE;
        }
    }

    std::cout << "R6: an uncomputed match count is absent, not zero; "
                 "a keyless line is not a relation\n";
    std::cout << "PIN: 2 arms hold known defects (4a the TO clause, "
                 "4e the flattened tree) and go red when they are fixed\n";
    std::cout << "PASS: dottalkpp relation merge\n";
    return EXIT_SUCCESS;
}
