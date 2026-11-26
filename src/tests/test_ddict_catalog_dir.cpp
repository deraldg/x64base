// @dottalk.file v1
// subsystem: tests
// layer: test
// owns: 
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

// THE DDict PANEL MUST NOT PICK ITS CATALOG BY WORKING DIRECTORY.
//
// Measured 2026-09-18. catalog_candidates() named four directory shapes per
// root and the canonical one -- dottalkpp/data/datadict, which holds
// DDOBJECT.dbf and its ten siblings -- was not among them. It resolved only
// because base_roots() includes cwd/.. and the launcher pushes the working
// directory to dottalkpp\data before starting the Workbench. From the repo
// root the winner was instead dottalkpp/data/datadict/datadict, a nested
// mirror byte-identical to its own parent today and a fork the day either
// side is regenerated. The panel printed the directory it chose and no one
// read it as a choice.
//
// A2 IS THE ARM THAT FAILS ON THE OLD CODE. The others are the controls: the
// launcher's own cwd, two other plausible ones, the staging shape, and the
// miss. A fix that only satisfied A2 would break at least one of them.
//
// This test builds its own tree under temp_directory_path() and touches
// nothing in the repo. EACH ARM RETURNS ITS OWN CODE so a failure names
// itself in ctest output.

#include "datadict/ddict_catalog_paths.hpp"

#include <filesystem>
#include <string>
#include <system_error>

namespace fs = std::filesystem;

namespace {

// Compare by identity, not by spelling. On Windows a temp path can come back
// with different case or an 8.3 component, and a string compare would fail an
// arm that is actually correct.
bool same_dir(const fs::path& a, const fs::path& b) {
    std::error_code ec;
    if (!fs::exists(a, ec) || !fs::exists(b, ec)) {
        return false;
    }
    bool eq = fs::equivalent(a, b, ec);
    return !ec && eq;
}

struct CwdGuard {
    fs::path saved;
    explicit CwdGuard(const fs::path& to) {
        std::error_code ec;
        saved = fs::current_path(ec);
        fs::current_path(to, ec);
    }
    ~CwdGuard() {
        std::error_code ec;
        if (!saved.empty()) {
            fs::current_path(saved, ec);
        }
    }
};

} // namespace

int main()
{
    std::error_code ec;
    fs::path base = fs::temp_directory_path(ec) /
                    ("dottalk_ddict_catalog_dir_test_" + std::to_string(
                        static_cast<unsigned long long>(
                            fs::file_time_type::clock::now().time_since_epoch().count())));
    if (ec) {
        return 1;
    }

    const fs::path repo      = base / "repo";
    const fs::path canonical = repo / "dottalkpp" / "data" / "datadict";
    const fs::path mirror    = canonical / "datadict";
    const fs::path deep      = repo / "build" / "src" / "Release";
    const fs::path staging   = base / "staging";          // the C:\x64base shape
    const fs::path staged    = staging / "data" / "datadict";
    const fs::path bare      = base / "bare";             // no catalog anywhere

    fs::create_directories(mirror, ec);                   // makes canonical too
    if (ec) { return 2; }
    fs::create_directories(deep, ec);
    if (ec) { return 3; }
    fs::create_directories(staged, ec);
    if (ec) { return 4; }
    fs::create_directories(bare, ec);
    if (ec) { return 5; }

    int failure = 0;

    {
        // A2. THE FIX. From the repo root the canonical directory wins over the
        //     mirror nested inside it. This arm returns the mirror on the code
        //     as it stood before 2026-09-18.
        CwdGuard cwd(repo);
        if (!same_dir(dottalk::datadict::find_catalog_dir(), canonical)) { failure = 10; }
    }

    if (!failure) {
        // A3. THE CONTROL THAT MATTERS MOST. This is the launcher's own working
        //     directory (Invoke-DotTalkWbRuntime pushes dottalkpp\data), the one
        //     path that worked before. It must still resolve the same way.
        CwdGuard cwd(repo / "dottalkpp" / "data");
        if (!same_dir(dottalk::datadict::find_catalog_dir(), canonical)) { failure = 11; }
    }

    if (!failure) {
        // A4. One level up from that.
        CwdGuard cwd(repo / "dottalkpp");
        if (!same_dir(dottalk::datadict::find_catalog_dir(), canonical)) { failure = 12; }
    }

    if (!failure) {
        // A5. A built exe run where it was produced: three parents reach the
        //     repo root, which is the deepest base_roots() goes.
        CwdGuard cwd(deep);
        if (!same_dir(dottalk::datadict::find_catalog_dir(), canonical)) { failure = 13; }
    }

    if (!failure) {
        // A6. THE STAGING SHAPE. A tree with data/datadict and no dottalkpp/
        //     above it must still resolve -- this is why the older candidate
        //     stays in the list rather than being replaced.
        CwdGuard cwd(staging);
        if (!same_dir(dottalk::datadict::find_catalog_dir(), staged)) { failure = 14; }
    }

    if (!failure) {
        // A7. THE MISS NAMES A REAL PLACE. With no catalog anywhere the answer
        //     is the canonical RELATIVE path, not the metadata directory that
        //     does not exist in this tree and never has.
        CwdGuard cwd(bare);
        const fs::path miss = dottalk::datadict::find_catalog_dir();
        const std::string text = miss.generic_string();
        if (text.find("dottalkpp/data/datadict") == std::string::npos) { failure = 15; }
        if (!failure && text.find("metadata") != std::string::npos)    { failure = 16; }
    }

    fs::remove_all(base, ec);
    return failure;
}
