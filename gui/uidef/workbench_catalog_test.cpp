// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: catalog inspection native proof
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_catalog.hpp"
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "memo/memostore.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <set>

namespace fs = std::filesystem;
using namespace dottalk::workbench;
void require(bool ok, const char* message) { if (!ok) throw std::runtime_error(message); }
std::string bytes(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(in), {});
}
struct Fixture {
    fs::path dir = fs::temp_directory_path() /
        ("arctictalk-test-" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    Fixture() { require(fs::create_directory(dir), "fixture directory collision"); }
    ~Fixture() {
        std::error_code ec;
        for (const auto* name : {"WORKSPACES.dbf", "WORKSPACES.dtx", "BAD.dbf"}) fs::remove(dir / name, ec);
        fs::remove(dir, ec);
    }
};
int main(int argc, char** argv) {
    try {
        if (argc == 3 && std::string(argv[1]) == "--catalog") {
            const auto s = inspect_catalog(fs::path(argv[2]));
            require(s.ok(), s.error.c_str());
            std::size_t images = 0, errors = 0;
            for (const auto& e : s.entries) { images += e.container.ok; errors += !e.error.empty(); }
            std::cout << "records=" << s.entries.size() << " deleted=" << s.deleted
                      << " minidb=" << images << " payload_errors=" << errors << '\n';
            return errors ? 1 : 0;
        }
        Fixture fixture;
        const auto dbf = fixture.dir / "WORKSPACES.dbf";
        const auto dtx = fixture.dir / "WORKSPACES.dtx";
        std::vector<xbase::dbf_create::FieldSpec> fields = {
            {"WS_ID", 'N', 10}, {"WS_NAME", 'C', 32}, {"FMT", 'C', 12},
            {"SNAPSHOT", 'M', 16}, {"SUPERSEDED", 'C', 1},
            {"PARENT_ID", 'N', 10}, {"PREV_ID", 'N', 10}};
        std::string err;
        require(xbase::dbf_create::create_dbf(dbf.string(), fields, xbase::dbf_create::Flavor::X64, err), err.c_str());
        {
            dottalk::memo::MemoStore memo;
            require(memo.open(dtx.string(), dottalk::memo::OpenMode::CreateIfMissing).ok, "create memo");
            const std::string posture = "DTSHEMA 3\n";
            const auto good = memo.put_text("MINIDB 1\nPOSTURE " + std::to_string(posture.size()) + "\n" + posture +
                "FILE 3 sample.dbf\nabcFILE 4 sample.dtx\ndefgEND\n");
            const auto bad = memo.put_text("MINIDB 1\nPOSTURE 10\nDTSHEMA 3\n");
            require(good.ok && bad.ok, "fixture memo payloads");
            memo.close();
            xbase::DbArea area;
            area.open(dbf.string());
            auto add = [&](int id, const char* name, int parent, int previous, bool super, const std::string& token) {
                require(area.appendBlank(), "append fixture row");
                area.set(1, std::to_string(id)); area.set(2, name);
                area.set(3, token.empty() ? "BIRTH 1" : "MINIDB 1"); area.set(4, token);
                area.set(5, super ? "1" : "0"); area.set(6, std::to_string(parent));
                area.set(7, std::to_string(previous)); require(area.writeCurrent(), "write fixture row");
            };
            add(10, "ROOT", 0, 0, false, "");
            add(20, "CHILD", 10, 0, false, good.ref.token);
            add(30, "VERSION", 0, 20, true, good.ref.token);
            add(40, "BROKEN", 0, 0, false, bad.ref.token);
            add(50, "DELETED", 0, 0, false, ""); require(area.deleteCurrent(), "delete fixture row");
            add(60, "CYCLE", 60, 0, false, "");
        }
        const auto before_dbf = bytes(dbf), before_dtx = bytes(dtx);
        const auto s = inspect_catalog(dbf);
        require(s.ok(), s.error.c_str());
        require(s.entries.size() == 5 && s.deleted == 1, "deleted rows excluded, historical rows retained");
        require(s.entries[1].id == 20 && s.entries[1].parent_id == 10, "durable parent identity");
        require(s.entries[2].superseded && s.entries[2].previous_id == 20 && s.entries[2].parent_id == 0,
                "version history must not become parentage");
        require(s.entries[1].container.ok && s.entries[1].container.files.size() == 2, "MINIDB member scan");
        require(s.entries[1].container.ram_file_bytes == 3 && s.entries[1].container.sidecar_file_bytes == 4,
                "RAM and disk memo byte split");
        require(!s.entries[3].error.empty() && !s.entries[3].container.ok, "truncated container reported");
        const auto ordered = catalog_order(s);
        require(ordered.size() == 5 && ordered[1].second == 1 && ordered[2].second == 0,
                "hierarchy uses parent, terminates on cycles, preserves rows");
        require(before_dbf == bytes(dbf) && before_dtx == bytes(dtx), "input catalog family byte preservation");
        std::stop_source cancel; cancel.request_stop();
        require(inspect_catalog(dbf, cancel.get_token()).code == "gui.catalog.cancelled", "cancellation");
        require(!inspect_catalog(fixture.dir / "ABSENT.dbf").ok(), "missing catalog refused");
        { std::ofstream bad(fixture.dir / "BAD.dbf"); bad << "not a DBF"; }
        require(!inspect_catalog(fixture.dir / "BAD.dbf").ok(), "malformed catalog refused");
        fs::remove(dtx);
        const auto missing = inspect_catalog(dbf);
        require(missing.ok() && !missing.entries[1].error.empty(), "missing sidecar visible per payload");
        std::cout << "PASS catalog: parent/version separation, history/deletion, MINIDB members, RAM/disk split,\n"
                     "corrupt payload, cycles, unchanged inputs, cancellation, missing/malformed files\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "FAIL: " << e.what() << '\n';
        return 1;
    }
}
