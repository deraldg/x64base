// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported
//
// AIF-078. REPOINTED 2026-08-24 BY RULING R123 -- ITS SUBJECT WAS DELETED.
//
// WHAT IT USED TO ASSERT. Session::workspace_model() carried a
// count_relation_matches lambda that counted DELETED ROWS as matches and
// scanned without a bound. Those were fixed by reading, and this fixture was
// written to hold the fix -- the discriminator being one integer, over a child
// table of four rows keyed S1, S1, S2 and S1-DELETED, where a counter honouring
// the deletion says 2 and the shipped one said 3.
//
// WHAT R123 DID. It deleted the counter. The GUI's number disagreed with
// relations_api::match_count_for_child in FOUR ways, not one -- deleted rows,
// scan bound, join arity, and index order versus physical order -- and under
// R122 it cannot be fixed in place, because a match count is a computation over
// this process's open areas and the engine's counter lives behind a process
// boundary. A number that disagrees with the engine is worse than no number.
//
// SO THIS FIXTURE IS REPOINTED, NOT DELETED, AND NOT LEFT TO RETUNE ITSELF --
// the IDXSTALE precedent. Its subject is now the ABSENCE: the GUI reports no
// count, and the relation edge survives intact anyway. That second half is the
// arm that matters, because "no count" is also what a blanked model produces.
//
// The fixture below is UNCHANGED and still earns its keep. It links
// dottalk_gui_core, builds its own two tables, and does NOT skip when data is
// missing -- everything here is created by the test, so absent data is a
// FAILURE rather than a silent pass. It is now the only place that proves a
// relation edge survives a real posture load against real open tables.
//
// THE FILENAME IS KEPT. It is still about the match count; what changed is that
// the answer is now absence. Renaming it would cost a CMake edit and lose the
// thread from R123 back to the defect it closed.
//
// WHEN A COUNT RETURNS -- and R122 says one will, emitted by the producer from
// the engine's own state -- T1 GOES RED. That is correct and it is the point.
// Repoint it then to assert the ENGINE's number, which for this fixture is 2:
// four child rows keyed S1, S1, S2 and S1-DELETED, with the engine skipping the
// deleted one. That arrangement is preserved below for exactly that day.

#include "gui/core/session.hpp"
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {

bool require(bool condition, const std::string& message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        return false;
    }
    return true;
}

// One character field, SID. Both tables share it so the relation has a key.
bool make_table(const std::filesystem::path& path, std::string& err) {
    std::vector<xbase::dbf_create::FieldSpec> fields;
    xbase::dbf_create::FieldSpec sid;
    sid.name = "SID";
    sid.type = 'C';
    sid.len = 4;
    sid.dec = 0;
    fields.push_back(sid);
    return xbase::dbf_create::create_dbf(path.string(), fields,
                                         xbase::dbf_create::Flavor::X64, err);
}

// Append one row and, when asked, delete it in place. A deleted row that never
// held the matching key would prove nothing, so the caller passes the SAME key
// for the deleted row as for the live ones.
bool add_row(xbase::DbArea& area, const std::string& sid, bool deleted) {
    if (!area.appendBlank()) return false;
    if (!area.set(1, sid)) return false;
    if (!area.writeCurrent()) return false;
    if (!deleted) return true;
    if (!area.readCurrent()) return false;
    return area.deleteCurrent();
}

} // namespace

int main() {
    namespace fs = std::filesystem;
    std::error_code ec;

    const auto dir = fs::temp_directory_path() / "dottalkpp_gui_match_count";
    fs::remove_all(dir, ec);
    fs::create_directories(dir, ec);
    if (!require(fs::is_directory(dir, ec) && !ec, "could not create the scratch directory")) {
        return EXIT_FAILURE;
    }

    const auto parent_path = dir / "MCPAR.dbf";
    const auto child_path = dir / "MCCHD.dbf";

    // ---- G0: the fixture, asserted before anything is claimed about it ----
    {
        std::string err;
        if (!require(make_table(parent_path, err), "could not create MCPAR.dbf: " + err)) {
            return EXIT_FAILURE;
        }
        if (!require(make_table(child_path, err), "could not create MCCHD.dbf: " + err)) {
            return EXIT_FAILURE;
        }

        xbase::DbArea parent;
        parent.open(parent_path.string());
        if (!require(parent.isOpen(), "MCPAR.dbf did not open for population")) {
            return EXIT_FAILURE;
        }
        if (!require(add_row(parent, "S1", false), "could not write the parent row")) {
            return EXIT_FAILURE;
        }
        parent.close();

        xbase::DbArea child;
        child.open(child_path.string());
        if (!require(child.isOpen(), "MCCHD.dbf did not open for population")) {
            return EXIT_FAILURE;
        }
        if (!require(add_row(child, "S1", false) &&
                     add_row(child, "S1", false) &&
                     add_row(child, "S2", false) &&
                     add_row(child, "S1", true),
                     "could not write the child rows")) {
            return EXIT_FAILURE;
        }

        // G0 GUARDS THE DELETION ITSELF. WSMULTI's WSM_G4 and the workspace
        // ladder's WSL_G4/G5 exist because a fixture whose INPUT silently
        // failed to be written reported a VERB failure that had not happened.
        // If this deletion did not take, the discriminator below would compare
        // 3 against 3 and go red while the counter was behaving correctly --
        // or, worse, the arrangement would be 2 live rows either way and it
        // would pass green while proving nothing.
        if (!require(child.recCount64() == 4, "the child table does not hold four rows")) {
            return EXIT_FAILURE;
        }
        if (!require(child.gotoRec(4) && child.readCurrent(),
                     "could not re-read the row that was deleted")) {
            return EXIT_FAILURE;
        }
        if (!require(child.isDeleted(), "the fourth child row is NOT marked deleted")) {
            return EXIT_FAILURE;
        }
        if (!require(child.gotoRec(1) && child.readCurrent() && !child.isDeleted(),
                     "the first child row was marked deleted by mistake")) {
            return EXIT_FAILURE;
        }
        child.close();
    }

    // ---- The posture: two areas and one relation, no match count ----------
    // The count MUST come from the GUI's own counter, so the relation is
    // delivered by the posture reader, which supplies no "(matches: N)". A
    // relation scraped out of REL LIST ALL would carry the ENGINE's number and
    // this fixture would be testing the wrong counter.
    const auto posture = dir / "match_count.dtschema";
    {
        std::ofstream out(posture);
        out << "AREA 0 | dbf=" << parent_path.string() << "\n";
        out << "AREA 1 | dbf=" << child_path.string() << "\n";
        out << "RELATION MCPAR MCCHD ON SID\n";
    }
    if (!require(fs::is_regular_file(posture, ec) && !ec, "the posture file was not written")) {
        return EXIT_FAILURE;
    }

    dottalk::gui::Session session;
    const auto loaded = session.run_command(dottalk::gui::CommandRequest{
        "workspace load " + posture.string()
    });
    if (!require(loaded.ok, "workspace load did not return success")) {
        return EXIT_FAILURE;
    }

    const auto model = session.workspace_model();
    if (!require(model.tables.size() == 2,
                 "the posture did not restore both tables")) {
        return EXIT_FAILURE;
    }

    const dottalk::gui::WorkspaceRelationInfo* edge = nullptr;
    for (const auto& relation : model.relations) {
        if (relation.parent == "MCPAR" && relation.child == "MCCHD") {
            edge = &relation;
            break;
        }
    }
    if (!require(edge != nullptr, "the posture's relation is not in the model")) {
        return EXIT_FAILURE;
    }

    // ---- T1 (R123): THE GUI REPORTS NO COUNT -----------------------------
    // A single-field key over two open tables is squarely within what the old
    // counter could do -- which is the point. This is not a question the GUI
    // fails to answer; it is a question the GUI no longer ANSWERS AT ALL,
    // because its answer disagreed with the engine's and there is no third
    // state to put the disagreement in.
    //
    // This arm is a TRIPWIRE in the honest direction: it reds the day a count
    // comes back. See the header for what to repoint it to.
    if (!require(!edge->match_count.has_value(),
                 "the GUI produced a match count -- R123 deleted the GUI's "
                 "counter, so a number here means either the counter came back "
                 "or a second one was written")) {
        return EXIT_FAILURE;
    }

    // ---- T2: THE EDGE SURVIVES, AND THIS IS THE ARM THAT MATTERS ---------
    // FIELDMGR_APPEND. T1 alone is satisfied by a BLANKED MODEL: no relations
    // at all, no counts at all, green. So T1 is not evidence of anything until
    // something proves the edge is really there -- with its endpoints and its
    // key, as VALUES, not as a row that exists.
    //
    // It also guards the thing R123 could plausibly have broken. Deleting the
    // counter meant deleting the loop that walked model.relations, and a
    // careless cut takes the edge with it.
    if (!require(edge->parent == "MCPAR",
                 "the surviving edge lost its parent")) {
        return EXIT_FAILURE;
    }
    if (!require(edge->child == "MCCHD",
                 "the surviving edge lost its child")) {
        return EXIT_FAILURE;
    }
    if (!require(edge->parent_key == "SID",
                 "the surviving edge lost its key")) {
        return EXIT_FAILURE;
    }
    if (!require(edge->child_key == "SID",
                 "the surviving edge lost its mirrored child key -- with no TO "
                 "clause the parser mirrors the parent side, and an empty one "
                 "here would mean that mirroring stopped")) {
        return EXIT_FAILURE;
    }

    fs::remove_all(dir, ec);

    std::cout << "GUI relation edge: MCPAR -> MCCHD ON SID survives a posture "
                 "load with NO match count, which is R123\n";
    std::cout << "PASS: dottalkpp gui match count\n";
    return EXIT_SUCCESS;
}
