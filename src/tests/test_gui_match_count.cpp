// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported
//
// AIF-078. THE FIXTURE THAT WAS OWED.
//
// Session::workspace_model()'s count_relation_matches counted DELETED ROWS as
// matches and scanned without a bound. Those were fixed by reading, and the
// commit that fixed them said in its own text that it had no fixture, because
// the counter needs a live Session with real open tables -- which is exactly
// why it drifted from the engine's counter unnoticed in the first place.
//
// This is that fixture. It links dottalk_gui_core, builds its own two tables,
// and does NOT skip when data is missing. That last part is deliberate: the
// existing async smoke guards its table work with is_regular_file and passes
// green when the file is absent, which is a spec that reports success for
// having done nothing. Everything here is created by the test, so absent data
// is a FAILURE rather than a silent pass.
//
// THE DISCRIMINATOR is one integer. The child table holds four rows keyed
// S1, S1, S2 and S1-DELETED. A counter that honours the deletion says 2. The
// counter as it shipped said 3. No other arrangement separates them.

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

    // ---- T1: the counter answered at all ---------------------------------
    // A single-field key over two open tables is squarely within what this
    // counter can do, so ABSENT here would mean it refused a question it can
    // answer -- the opposite failure from the one being guarded.
    if (!require(edge->match_count.has_value(),
                 "the GUI counter left a count it should have been able to compute")) {
        return EXIT_FAILURE;
    }

    // ---- T2: THE DISCRIMINATOR -- deleted rows are not matches -----------
    if (!require(*edge->match_count != 3,
                 "the count is 3: the DELETED child row is still being counted")) {
        return EXIT_FAILURE;
    }
    if (!require(*edge->match_count == 2,
                 "the count is neither 2 nor 3, so the arrangement is not what "
                 "this fixture assumes -- check G0 before trusting this arm")) {
        return EXIT_FAILURE;
    }

    fs::remove_all(dir, ec);

    std::cout << "GUI match counter: 4 child rows keyed S1,S1,S2,S1-DELETED "
                 "count as 2, not 3\n";
    std::cout << "PASS: dottalkpp gui match count\n";
    return EXIT_SUCCESS;
}
