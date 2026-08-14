// @dottalk.file v1
// subsystem: tests
// layer: test
// owns:
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: supported

// tests/test_dot_talk_m365_integration_e2e.cpp
//
// End-to-end stdlib-only tests:
//   create inbound files -> poll_inbound() -> import -> archive/quarantine -> verify moves.
//
// Build idea (MSVC):
//   cl /std:c++20 /W4 /EHsc tests\test_dot_talk_m365_integration_e2e.cpp dot_talk_m365_integration.cpp

#include "dot_talk_m365_integration.hpp"

#include <cassert>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

static void write_file(const fs::path& p, const std::string& contents)
{
    fs::create_directories(p.parent_path());
    std::ofstream ofs(p, std::ios::binary);
    assert(ofs && "failed to create test file");
    ofs << contents;
}

static std::string ext_lower(std::string s)
{
    for (auto& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return s;
}

static bool import_dispatch(const dottalk::m365::FileDescriptor& fd)
{
    using namespace dottalk::m365;

    const std::string ext = ext_lower(fd.extension);
    if (ext == ".csv")  return import_table_from_csv(fd);
    if (ext == ".json") return import_record_from_json(fd);
    if (ext == ".txt")  return import_notes_from_txt(fd);
    return false;
}

int main()
{
    using namespace dottalk::m365;

    // Isolated temp sandbox.
    const fs::path root = fs::temp_directory_path() / "dot_talk_m365_integration_tests_e2e";
    fs::remove_all(root);
    fs::create_directories(root);

    IntegrationConfig cfg{};
    cfg.base_folder          = root.string();
    cfg.inbound_subfolder    = "in";
    cfg.outbound_subfolder   = "out";
    cfg.archive_subfolder    = "arc";
    cfg.quarantine_subfolder = "q";

    cfg.import_prefix_csv  = "csv_";
    cfg.import_prefix_json = "json_";
    cfg.import_prefix_txt  = "txt_";

    assert(configure(cfg));

    const fs::path inbound = root / cfg.inbound_subfolder;
    const fs::path archive = root / cfg.archive_subfolder;
    const fs::path quarantine = root / cfg.quarantine_subfolder;

    // ---- Create inbound files (3 valid, 3 invalid)
    const fs::path p_csv_ok   = inbound / "csv_customers_20260101.csv";
    const fs::path p_csv_bad  = inbound / "customers_20260101.csv"; // missing prefix

    const fs::path p_json_ok  = inbound / "json_orders_42.json";
    const fs::path p_json_bad = inbound / "json_orders_0.json";     // id==0 treated invalid by current code

    const fs::path p_txt_ok   = inbound / "txt_support_20260101.txt";
    const fs::path p_txt_bad  = inbound / "txt_.txt";               // missing topic

    write_file(p_csv_ok,  "id,name\n1,Alice\n");
    write_file(p_csv_bad, "id,name\n1,Alice\n");

    write_file(p_json_ok,  "{ \"dummy\": true }\n");
    write_file(p_json_bad, "{ \"dummy\": true }\n");

    write_file(p_txt_ok,  "hello\n");
    write_file(p_txt_bad, "x\n");

    // ---- Poll inbound
    std::vector<FileDescriptor> files;
    assert(poll_inbound(files));
    assert(files.size() == 6);

    // ---- Process: import -> archive on success, quarantine on failure
    size_t ok_count = 0;
    size_t bad_count = 0;

    for (const auto& fd : files)
    {
        const bool ok = import_dispatch(fd);
        if (ok)
        {
            ++ok_count;
            assert(archive_file(fd));
            assert(!fs::exists(fd.full_path));
            assert(fs::exists(archive / fd.name));
        }
        else
        {
            ++bad_count;
            assert(quarantine_file(fd));
            assert(!fs::exists(fd.full_path));
            assert(fs::exists(quarantine / fd.name));
        }
    }

    assert(ok_count == 3);
    assert(bad_count == 3);

    // ---- Inbound should now be empty
    files.clear();
    assert(poll_inbound(files));
    assert(files.empty());

    // ---- Verify archive/quarantine contain expected filenames
    assert(fs::exists(archive / p_csv_ok.filename()));
    assert(fs::exists(archive / p_json_ok.filename()));
    assert(fs::exists(archive / p_txt_ok.filename()));

    assert(fs::exists(quarantine / p_csv_bad.filename()));
    assert(fs::exists(quarantine / p_json_bad.filename()));
    assert(fs::exists(quarantine / p_txt_bad.filename()));

    fs::remove_all(root);
    return 0;
}
