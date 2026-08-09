// tests/test_dot_talk_m365_integration.cpp
//
// Minimal stdlib-only tests for filename parsing + import entrypoints.
// Assumes these symbols exist in your project (from dot_talk_m365_integration.hpp):
// - dottalk::m365::IntegrationConfig
// - dottalk::m365::FileDescriptor
// - dottalk::m365::configure
// - dottalk::m365::import_table_from_csv
// - dottalk::m365::import_record_from_json
// - dottalk::m365::import_notes_from_txt
//
// Build idea (MSVC):
//   cl /std:c++20 /W4 /EHsc tests\test_dot_talk_m365_integration.cpp dot_talk_m365_integration.cpp

#include "dot_talk_m365_integration.hpp"

#include <cassert>
#include <filesystem>
#include <fstream>
#include <string>

namespace fs = std::filesystem;

static void write_file(const fs::path& p, const std::string& contents)
{
    fs::create_directories(p.parent_path());
    std::ofstream ofs(p, std::ios::binary);
    assert(ofs && "failed to create test file");
    ofs << contents;
    ofs.close();
}

static dottalk::m365::FileDescriptor make_fd(const fs::path& p)
{
    dottalk::m365::FileDescriptor fd{};
    fd.full_path = p.string();
    fd.name      = p.filename().string();
    fd.extension = p.extension().string();
    fd.stem      = p.stem().string();
    return fd;
}

int main()
{
    using namespace dottalk::m365;

    // Create an isolated temp sandbox.
    const fs::path root = fs::temp_directory_path() / "dot_talk_m365_integration_tests";
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

    // ---- Valid cases (should import true)
    {
        const fs::path p = inbound / "csv_customers_20260101.csv";
        write_file(p, "id,name\n1,Alice\n");
        assert(import_table_from_csv(make_fd(p)));
    }
    {
        const fs::path p = inbound / "json_orders_42.json";
        write_file(p, "{ \"dummy\": true }\n");
        assert(import_record_from_json(make_fd(p)));
    }
    {
        const fs::path p = inbound / "txt_support_20260101.txt";
        write_file(p, "hello\n");
        assert(import_notes_from_txt(make_fd(p)));
    }

    // ---- Invalid cases (should import false)
    {
        const fs::path p = inbound / "customers_20260101.csv"; // missing prefix
        write_file(p, "id,name\n1,Alice\n");
        assert(!import_table_from_csv(make_fd(p)));
    }
    {
        const fs::path p = inbound / "json_orders_.json"; // missing id
        write_file(p, "{ }\n");
        assert(!import_record_from_json(make_fd(p)));
    }
    {
        const fs::path p = inbound / "txt_.txt"; // missing topic
        write_file(p, "x\n");
        assert(!import_notes_from_txt(make_fd(p)));
    }
    {
        const fs::path p = inbound / "json_orders_0.json"; // id==0 treated invalid by current code
        write_file(p, "{ }\n");
        assert(!import_record_from_json(make_fd(p)));
    }

    fs::remove_all(root);
    return 0;
}
