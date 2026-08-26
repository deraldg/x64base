// @dottalk.file v1
// subsystem: gui
// layer: test
// owns:
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: supported
//
// AIF-078 step 2/4. THE FIXTURE THAT PROVES MEMBERSHIP BECAME TRUE.
//
// Step 2b moved a session-owned area out of Session::Impl::Area (which held an
// xbase::DbArea BY VALUE) and into an XBaseEngine's array, at a slot claimed
// from the same allocator the CLI's USE ... IN FREE uses. The commit that did
// it said in its own text that a green async smoke proves nothing broke and
// does NOT prove the new thing works. This is the fixture that was owed.
//
// WHY THE OLD CODE FAILS THIS, which is what makes it a discriminator and not
// a demonstration:
//
// setEngineSlot() has exactly ONE caller in the tree -- XBaseEngine's
// constructor in dbf_file.cpp, over the engine's own array. An area outside that
// array could never have an engine slot and carried -1 for life. DbArea::open()
// then called workspace::join(_ws_handle, _engine_slot) with -1, and join's
// first loop is `if (m[i] == engine_slot) return i;` -- an idempotence check
// that returns WITHOUT claiming. -1 is ALSO the member array's own free-slot
// sentinel, so every GUI area matched the first FREE slot, was handed that
// index, and claimed nothing.
//
// So against the code as it stood on 2026-08-24 morning, T1 reads 0 and T2
// reads two IDENTICAL local slots. Against the engine-array areas, T1 reads 2
// and the slots differ. One integer and one comparison separate them.
//
// T3 IS THE HALF THAT COSTS MOST IF IT IS WRONG. Before step 2b, closing a GUI
// area released it implicitly: destroying an Area destroyed its by-value
// DbArea, and ~DbArea() calls close(), which calls workspace::leave(). The
// DbArea is no longer the Area's to destroy, so ~Area() closes the borrowed
// engine area explicitly. If that destructor were ever removed or reordered
// after the engine, the slots would stay claimed with NO compile error and no
// other failing test. T3 destroys the Session and reads membership back.
//
// Everything here is created by the test. It does NOT skip when data is
// absent -- the async smoke guards its table work with is_regular_file and
// passes green when the file is missing, which is a spec that reports success
// for having done nothing.

#include "gui/core/session.hpp"
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase/workspace_membership.hpp"

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

bool make_table(const std::filesystem::path& path, std::string& err) {
    std::vector<xbase::dbf_create::FieldSpec> fields;
    xbase::dbf_create::FieldSpec sid;
    sid.name = "SID";
    sid.type = 'C';
    sid.len  = 4;
    sid.dec  = 0;
    fields.push_back(sid);
    return xbase::dbf_create::create_dbf(path.string(), fields,
                                         xbase::dbf_create::Flavor::X64, err);
}

bool add_row(xbase::DbArea& area, const std::string& sid) {
    if (!area.appendBlank()) return false;
    if (!area.set(1, sid))   return false;
    return area.writeCurrent();
}

} // namespace

int main() {
    namespace fs = std::filesystem;
    namespace ws = xbase::workspace;
    std::error_code ec;

    const auto dir = fs::temp_directory_path() / "dottalkpp_gui_area_membership";
    fs::remove_all(dir, ec);
    fs::create_directories(dir, ec);
    if (!require(fs::is_directory(dir, ec) && !ec, "could not create the scratch directory")) {
        return EXIT_FAILURE;
    }

    const auto a_path = dir / "GMEMA.dbf";
    const auto b_path = dir / "GMEMB.dbf";

    // ---- G0: the fixture, asserted before anything is claimed about it ----
    {
        std::string err;
        if (!require(make_table(a_path, err), "could not create GMEMA.dbf: " + err)) return EXIT_FAILURE;
        if (!require(make_table(b_path, err), "could not create GMEMB.dbf: " + err)) return EXIT_FAILURE;

        xbase::DbArea a;
        a.open(a_path.string());
        if (!require(a.isOpen(), "GMEMA.dbf did not open for population")) return EXIT_FAILURE;
        if (!require(add_row(a, "A1"), "could not write the GMEMA row")) return EXIT_FAILURE;
        a.close();

        xbase::DbArea b;
        b.open(b_path.string());
        if (!require(b.isOpen(), "GMEMB.dbf did not open for population")) return EXIT_FAILURE;
        if (!require(add_row(b, "B1"), "could not write the GMEMB row")) return EXIT_FAILURE;
        b.close();
    }

    // The two DbAreas above were LOCAL and are now closed, so whatever they did
    // to membership is undone. Read the baseline AFTER them, never before: a
    // baseline taken earlier would not account for the fixture's own opens.
    const std::uint64_t handle = ws::current_handle();
    const std::size_t   before = ws::member_count(handle);

    const auto posture = dir / "area_membership.dtschema";
    {
        std::ofstream out(posture);
        out << "AREA 0 | dbf=" << a_path.string() << "\n";
        out << "AREA 1 | dbf=" << b_path.string() << "\n";
    }
    if (!require(fs::is_regular_file(posture, ec) && !ec, "the posture file was not written")) {
        return EXIT_FAILURE;
    }

    std::size_t during = 0;
    std::vector<std::int32_t> slots;

    // R128 (owner, 2026-08-26). THE HANDLE THIS TEST MEASURES HAD TO MOVE, and
    // the move is the ruling rather than a concession to it. WORKSPACE LOAD is
    // now ADDITIVE and NAMES the workspace it loads into, so the areas no
    // longer join whichever workspace happened to be current when this file
    // started -- they join the one the load created. Reading `handle` after the
    // load would count DEFAULT's members and find none.
    //
    // WHAT THIS DOES NOT COST: the discriminator. Against the pre-2b code the
    // areas carried engine slot -1, join() matched the free-slot sentinel and
    // claimed nothing, and this reads ZERO on WHICHEVER handle it is pointed
    // at. Moving the pointer does not soften the arm.
    //
    // THE HANDLE IS READ OFF THE MODEL, NOT ASSUMED. AreaInfo::workspace is
    // written from the area's REAL wsHandle (gui_workspace_of_area, O(1), no
    // lookup), so this asks the areas where they went instead of predicting it
    // from the posture's filename -- which would make the arm pass on a
    // coincidence of naming.
    std::uint64_t joined = 0;

    {
        dottalk::gui::Session session;
        const auto loaded = session.run_command(dottalk::gui::CommandRequest{
            "workspace load " + posture.string()
        });
        if (!require(loaded.ok, "workspace load did not return success")) return EXIT_FAILURE;

        const auto model = session.workspace_model();
        // G1 GUARDS THE INPUT THE ARMS READ. If the posture restored no tables,
        // T1 would compare 0 against 0 and go RED while the membership code was
        // behaving perfectly -- a fixture failure wearing a verb failure's
        // clothes, which is the omission WSMULTI's WSM_G4 was added to close.
        if (!require(model.tables.size() == 2,
                     "the posture did not restore both tables")) {
            return EXIT_FAILURE;
        }

        joined = ws::find_by_name_ci(model.tables.front().workspace);
        // G2 GUARDS THE HANDLE THE ARMS READ, for the reason G1 guards the
        // tables: a lookup that answered 0 would send every count below to the
        // reserved not-a-workspace bucket and read as a membership failure.
        if (!require(joined != 0,
                     "the areas report a workspace the registry does not know: " +
                     model.tables.front().workspace)) {
            return EXIT_FAILURE;
        }
        during = ws::member_count(joined);
        slots  = ws::members(joined);
    }
    // The Session is destroyed HERE. ~Area() runs, and with it the close()
    // that performs workspace::leave().

    const std::size_t after = ws::member_count(joined);

    // AN ARM THAT ASSERTED THE LOAD DID NOT DISTURB THE PREVIOUSLY-CURRENT
    // WORKSPACE STOOD HERE AND WAS DELETED, 2026-08-26. It ran after the
    // Session was destroyed, where both sides are zero under every
    // implementation -- it could not go red, which is the shape this house
    // keeps naming. Moving it INSIDE the block would make it real, and would
    // also make this AIF-078 fixture fail for an R128 reason; the additive
    // property wants its own fixture rather than a lodger in this one. It does
    // not have one yet, and that is recorded rather than papered over.

    // ---- T1: THE DISCRIMINATOR -- the workspace can see the GUI's areas ---
    // Old code: join(h, -1) claimed nothing and this reads `before`.
    // The joined workspace is created BY the load, so its baseline is 0 by
    // construction -- `before` is the OTHER workspace's count and is asserted
    // separately above. Stated rather than left as arithmetic that happens to
    // agree while both numbers are zero.
    if (!require(during == 2,
                 "workspace membership did not grow by two when the GUI opened two "
                 "tables (before=" + std::to_string(before) +
                 ", during=" + std::to_string(during) + ")")) {
        return EXIT_FAILURE;
    }

    // ---- T2: the two areas hold DISTINCT engine slots ---------------------
    // Old code: every area was handed the SAME index -- the first free one --
    // because -1 matched the free-slot sentinel. Distinctness is the property
    // that a shared sentinel cannot fake.
    if (!require(slots.size() >= 2, "membership listed fewer than two slots")) {
        return EXIT_FAILURE;
    }
    std::vector<std::int32_t> claimed;
    for (const auto s : slots) {
        if (s >= 0) claimed.push_back(s);
    }
    if (!require(claimed.size() == during,
                 "the member list and the member count disagree")) {
        return EXIT_FAILURE;
    }
    for (std::size_t i = 0; i < claimed.size(); ++i) {
        for (std::size_t j = i + 1; j < claimed.size(); ++j) {
            if (!require(claimed[i] != claimed[j],
                         "two areas share engine slot " + std::to_string(claimed[i]) +
                         " -- the -1 sentinel collision is back")) {
                return EXIT_FAILURE;
            }
        }
    }

    // ---- T3: destroying the Session RELEASES the slots --------------------
    if (!require(after == 0,
                 "membership did not return to its baseline after the Session was "
                 "destroyed (before=" + std::to_string(before) +
                 ", after=" + std::to_string(after) +
                 ") -- ~Area() is not releasing the borrowed engine area")) {
        return EXIT_FAILURE;
    }

    fs::remove_all(dir, ec);
    std::cout << "PASS: dottalkpp gui area membership (before=" << before
              << " during=" << during << " after=" << after << ")\n";
    return EXIT_SUCCESS;
}
