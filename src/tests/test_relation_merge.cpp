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
// T7 AND T8 WERE PINS, and are not any more. Each asserted a known-wrong
// behaviour and said in its own failure text that going red meant the defect
// had been fixed and the arm should be rewritten. Both went red on 2026-08-23
// when 4a and 4e landed, and both are now written the right way round. The
// mechanism is recorded because it worked: a fixture can hold a known-wrong
// behaviour without blessing it, and it tells you when to stop.

#include "gui/core/relation_parse.hpp"
#include "xbase/workspace_membership.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace {

using dottalk::gui::WorkspaceRelationInfo;
using dottalk::gui::merge_relation;
using dottalk::gui::parse_relation_edges_from_output;
using dottalk::gui::format_relation_posture_line;
using dottalk::gui::parse_relation_posture_line;

// R125, 2026-08-24. THE POSTURE PARSER TAKES A HANDLE NOW, NOT A NAME.
//
// These calls said "DEFAULT" and now say kDefaultHandle. That is not a
// cosmetic swap: the engine has keyed the relation store by HANDLE since I1.2
// while the GUI carried a NAME, and nothing converted. The conversion now
// happens in exactly one place, inside the parser, and what these arms verify
// on the way back out -- rows[0].workspace, the merge identity -- is the
// RENDERED name. Both spellings still meet, which is the point:
// xbase::workspace::kDefaultName and dottalk::gui::kDefaultWorkspace are both
// "DEFAULT", so the round trip closes.
//
// T10 IS THE ARM THAT WOULD CATCH A BREAK HERE. It merges an edge parsed from
// a posture line against one scraped from CLI text -- two producers, two
// paths, one of which now goes through the handle -- and requires them to
// FUSE into a single row. If the handle-to-name rendering ever stops agreeing
// with what the scraper stamps, that arm splits the edge in two and says so.

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

    // ---- T7: the ` TO ` clause IS parsed (finding 4a, fixed) -------------
    // set_relations.cpp:894 emits `ON <parent-csv> TO <child-csv>` whenever the
    // field lists differ, and gui_workspace_format.cpp measured how often that
    // is: 190 of 1,102 RELATION lines (17.2%) in the live catalog carry an
    // explicit TO. Its ` TO ` renderer fires only when child_key != parent_key,
    // so until this split existed the renderer could never fire -- the need was
    // measured, the renderer written, and the parser upstream never produced
    // its input.
    //
    // Each side stays a CSV. "SID,TERM" is ONE key made of two fields, and
    // splitting it further is the caller's business, not the parser's.
    {
        const auto rows = parse_relation_edges_from_output(
            "P\n  -> C ON SID,TERM TO STU_ID,TERM_CD  (matches: 3)\n", "DEFAULT");
        if (!require(rows.size() == 1, "T7: the TO-form line did not parse at all")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[0].parent_key == "SID,TERM",
                     "T7: the parent side of the TO clause is wrong")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[0].child_key == "STU_ID,TERM_CD",
                     "T7: the child side of the TO clause is wrong")) {
            return EXIT_FAILURE;
        }
        // THE DISCRIMINATOR for the renderer that could not fire.
        if (!require(rows[0].child_key != rows[0].parent_key,
                     "T7: the two sides compare equal, so ` TO ` still cannot render")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T7b: NO TO clause means the child side MIRRORS the parent --------
    // Not empty. An empty field name is not something a correct producer
    // emits, so nothing downstream should have to tell "no child key" apart
    // from a real one.
    {
        const auto rows = parse_relation_edges_from_output(
            "P\n  -> C ON SID  (matches: 1)\n", "DEFAULT");
        if (!require(rows.size() == 1 && rows[0].parent_key == "SID" &&
                     rows[0].child_key == "SID",
                     "T7b: a keyed line without TO did not mirror its key")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T8: the tree NESTS correctly (finding 4e, fixed) ----------------
    // The producer indents by depth * 2. The parser pops entries whose
    // recorded indent is >= the current one, so the push has to record the
    // indent the child was SEEN at. It recorded `indent + 2`, so a depth-1
    // child stored at 4 was popped by its own depth-2 child at indent 4, and
    // every descendant below depth 1 was attributed to the ROOT.
    {
        const auto rows = parse_relation_edges_from_output(kTree, "DEFAULT");
        if (!require(rows.size() == 2 && rows[1].child == "COURSES",
                     "T8: the depth-2 edge is missing")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[0].parent == "STUDENTS",
                     "T8: the depth-1 edge lost its root")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[1].parent == "ENROLL",
                     "T8: the depth-2 edge is still attributed to the ROOT")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T8b: SIBLINGS at one depth keep the same parent ------------------
    // The arrangement that a too-eager pop and a too-lazy pop disagree about,
    // so it discriminates the fix from an overcorrection to `>`.
    {
        const auto rows = parse_relation_edges_from_output(
            "R\n"
            "  -> A ON K1  (matches: 1)\n"
            "    -> A2 ON K2  (matches: 2)\n"
            "  -> B ON K3  (matches: 3)\n", "DEFAULT");
        if (!require(rows.size() == 3, "T8b: the three edges did not all parse")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[0].parent == "R" && rows[0].child == "A",
                     "T8b: the first depth-1 edge is wrong")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[1].parent == "A" && rows[1].child == "A2",
                     "T8b: the depth-2 edge did not nest under its sibling")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[2].parent == "R" && rows[2].child == "B",
                     "T8b: the second depth-1 edge did not pop back to the root")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T9: the POSTURE ROUND TRIP is lossless --------------------------
    // THE ARM THAT DID NOT EXIST WHEN THE LOSS DID. The writer emitted
    // `ON <parent_key>` and dropped the child side; the reader could not have
    // read one back. Two broken ends made the round trip look lossless, which
    // is why nothing caught it -- a save/load cycle returned exactly what it
    // was given, and what it was given had already been flattened.
    //
    // This is the FIELDMGR_APPEND shape stated the other way round: a
    // round-trip assertion proves nothing unless the value being carried can
    // tell the two ends apart. A relation whose sides are EQUAL cannot. So the
    // arm carries one whose sides differ.
    {
        WorkspaceRelationInfo original;
        original.workspace = "DEFAULT";
        original.parent = "STUDENTS";
        original.child = "ENROLL";
        original.parent_key = "SID,TERM";
        original.child_key = "STU_ID,TERM_CD";

        std::string line;
        if (!require(format_relation_posture_line(original, line),
                     "T9: a complete relation produced no posture line")) {
            return EXIT_FAILURE;
        }
        if (!require(line == "RELATION STUDENTS ENROLL ON SID,TERM TO STU_ID,TERM_CD",
                     "T9: the posture line is not the shape the reader expects")) {
            return EXIT_FAILURE;
        }

        WorkspaceRelationInfo back;
        if (!require(parse_relation_posture_line(line, xbase::workspace::kDefaultHandle, back),
                     "T9: the writer's own line did not parse")) {
            return EXIT_FAILURE;
        }
        if (!require(back.parent == original.parent && back.child == original.child &&
                     back.parent_key == original.parent_key &&
                     back.child_key == original.child_key,
                     "T9: a field did not survive the round trip")) {
            return EXIT_FAILURE;
        }
        // THE DISCRIMINATOR. Under the old writer this was the assertion that
        // would have failed, and it is the only one that could have.
        if (!require(back.child_key != back.parent_key,
                     "T9: the child side was flattened onto the parent's")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T9b: equal sides emit NO ` TO `, so ordinary files do not churn --
    {
        WorkspaceRelationInfo same;
        same.workspace = "DEFAULT";
        same.parent = "STUDENTS";
        same.child = "ENROLL";
        same.parent_key = "SID";
        same.child_key = "SID";

        std::string line;
        if (!require(format_relation_posture_line(same, line) &&
                     line == "RELATION STUDENTS ENROLL ON SID",
                     "T9b: a same-key relation grew a redundant TO clause")) {
            return EXIT_FAILURE;
        }
        WorkspaceRelationInfo back;
        if (!require(parse_relation_posture_line(line, xbase::workspace::kDefaultHandle, back) &&
                     back.parent_key == "SID" && back.child_key == "SID",
                     "T9b: a keyed line without TO did not round trip")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T9c: both ends REFUSE in the return value (R3) ------------------
    // Not by emitting an empty line, and not by half-filling the output.
    {
        WorkspaceRelationInfo incomplete;
        incomplete.workspace = "DEFAULT";
        incomplete.parent = "STUDENTS";
        incomplete.child = "ENROLL";
        // no key
        std::string line = "SENTINEL";
        if (!require(!format_relation_posture_line(incomplete, line),
                     "T9c: a keyless relation was given a posture line")) {
            return EXIT_FAILURE;
        }
        if (!require(line == "SENTINEL",
                     "T9c: the refused format still wrote to its output")) {
            return EXIT_FAILURE;
        }

        WorkspaceRelationInfo out;
        out.parent = "SENTINEL";
        if (!require(!parse_relation_posture_line("AREA 0 | students.dbf", xbase::workspace::kDefaultHandle, out),
                     "T9c: a non-RELATION posture line was parsed as a relation")) {
            return EXIT_FAILURE;
        }
        if (!require(!parse_relation_posture_line("RELATION STUDENTS ENROLL", xbase::workspace::kDefaultHandle, out),
                     "T9c: a RELATION line with no key was accepted")) {
            return EXIT_FAILURE;
        }
        if (!require(out.parent == "SENTINEL",
                     "T9c: a refused parse still wrote to its output")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T10: the posture and the shell agree on ONE grammar -------------
    // The same relation reached through the two different producers must land
    // on the same row rather than two. This is the arrangement that would have
    // caught 4a from either side: before the split, the tree's
    // `ON SID TO STU_ID` and the posture's `ON SID TO STU_ID` both collapsed
    // to one blob key, which agreed -- wrongly, and identically.
    {
        std::vector<WorkspaceRelationInfo> rows;
        for (auto r : parse_relation_edges_from_output(
                 "STUDENTS\n  -> ENROLL ON SID TO STU_ID  (matches: 7)\n", "DEFAULT")) {
            merge_relation(rows, std::move(r));
        }
        WorkspaceRelationInfo from_file;
        if (!require(parse_relation_posture_line(
                         "RELATION STUDENTS ENROLL ON SID TO STU_ID", xbase::workspace::kDefaultHandle, from_file),
                     "T10: the posture line did not parse")) {
            return EXIT_FAILURE;
        }
        merge_relation(rows, std::move(from_file));

        if (!require(rows.size() == 1,
                     "T10: the two producers disagreed and the edge split in two")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[0].parent_key == "SID" && rows[0].child_key == "STU_ID",
                     "T10: the agreed row does not carry both sides")) {
            return EXIT_FAILURE;
        }
        if (!require(rows[0].match_count.has_value() && *rows[0].match_count == 7,
                     "T10: the count from the shell did not survive the posture merge")) {
            return EXIT_FAILURE;
        }
    }

    std::cout << "R6: an uncomputed match count is absent, not zero; "
                 "a keyless line is not a relation\n";
    std::cout << "4a: `ON p TO c` splits both sides; 4e: the tree nests "
                 "instead of flattening onto the root\n";
    std::cout << "posture: writer and reader share one grammar, and the round "
                 "trip carries a relation whose two sides DIFFER\n";
    std::cout << "PASS: dottalkpp relation merge\n";
    return EXIT_SUCCESS;
}
