// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: MINIDB admission, nested DTX and native hydration proof
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_session.hpp"
#include "dottalk/minidb_hydrate.hpp"
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "memo/memostore.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
namespace fs = std::filesystem;
using namespace dottalk::workbench;
namespace minidb = dottalk::minidb;
void require(bool ok, const std::string& message) { if (!ok) throw std::runtime_error(message); }
std::string bytes(const fs::path& path) {
    std::ifstream in(path, std::ios::binary); return {std::istreambuf_iterator<char>(in), {}};
}
std::string image(const std::string& posture, const std::vector<std::pair<std::string, std::string>>& files) {
    auto result = "MINIDB 1\nPOSTURE " + std::to_string(posture.size()) + "\n" + posture;
    for (const auto& [name, body] : files) result += "FILE " + std::to_string(body.size()) + " " + name + "\n" + body;
    return result + "END\n";
}
std::string posture(const char* name) {
    return std::string("DTSHEMA 3\nAREA 4 | dbf=") + name + " | index=none | alias=\nCURRENT 4\n";
}
std::uint64_t handle(const SessionSnapshot& snapshot, const std::string& name) {
    for (const auto& ws : snapshot.desk.workspaces) if (ws.name == name) return ws.handle;
    throw std::runtime_error("Workspace missing: " + name);
}
int main(int argc, char** argv) {
    try {
        if (argc == 3 && std::string(argv[1]) == "--catalog") {
            WorkbenchSession session;
            const auto home = session.submit().get().home;
            const auto catalog = session.inspect(argv[2]).get(); require(catalog.ok(), catalog.error);
            std::size_t images = 0, nested = 0, tables = 0;
            for (const auto& saved : catalog.entries) if (saved.container.ok) {
                const auto tree = session.inspect_image(saved.payload).get(); require(tree.error.empty(), tree.error);
                nested += tree.nodes.size() - 1;
                for (const auto& node : tree.nodes) {
                    Request r; r.action = Action::Hydrate; r.name = "CatalogImage" + std::to_string(++images);
                    r.payload = node.payload; r.provenance = saved.value("WS_NAME") + "/" + node.location;
                    const auto loaded = session.submit(r).get(); require(loaded.ok(), r.provenance + ": " + loaded.error + "\n" + loaded.transcript);
                    require(loaded.desk.healthy(), "Catalog load orphaned an area");
                    Request browse; browse.action = Action::Browse;
                    const auto viewed = session.submit(browse).get();
                    require(viewed.ok() && viewed.table.error.empty(), "Hydrated table browsing: " + viewed.table.error);
                    tables = loaded.areas.size();
                }
            }
            require(images > 0 && tables > 0, "Actual catalog must exercise hydration");
            session.shutdown();
            std::cout << "PASS actual catalog: " << images << " images hydrated; " << nested << " nested; " << tables << " tables\n"
                      << "session_home=" << home.string() << '\n';
            return 0;
        }
        const auto root = fs::temp_directory_path() / ("workbench images " +
            std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
        require(fs::create_directory(root), "Create fixture root");
        const auto mount = root / "guard";
        xbase::ramfs::mount(mount.string());
        for (const auto* unsafe : {"../escape.dtx", "..\\escape.dtx", "C:/escape.dtx", "/escape.dtx",
                                  "a:stream.dtx", "a//b.dtx", "CON.dtx", "a./b.dbf", "a /b.dbf", "a/", "a/./b.dbf"}) {
            const auto payload = image("DTSHEMA 3\n", {{"first.dtx", "must not be written"}, {unsafe, "bad"}});
            const auto result = minidb::materialize(payload, minidb::scan(payload), mount, mount / "indexes");
            require(!result.ok && result.files == 0 && !fs::exists(mount / "first.dtx") && xbase::ramfs::list(mount.string()).empty(),
                    std::string("Reject entire manifest before first write: ") + unsafe);
        }
        auto duplicated = image("DTSHEMA 3\n", {{"same.dbf", "a"}, {"SAME.dbf", "b"}});
        require(!minidb::materialize(duplicated, minidb::scan(duplicated), mount, mount / "indexes").ok, "Case duplicate refused");
        for (const auto* length : {"-1", "1oops", "18446744073709551615", "18446744073709551616"}) {
            require(!minidb::scan(std::string("MINIDB 1\nPOSTURE ") + length + "\nxEND\n").ok, "Strict posture lengths");
            require(!minidb::scan(std::string("MINIDB 1\nPOSTURE 10\nDTSHEMA 3\nFILE ") + length + " x.dbf\nxEND\n").ok, "Strict member lengths");
        }
        xbase::ramfs::unmount(mount.string());
        std::string error;
        const auto table = root / "STUDENTS.dbf";
        require(xbase::dbf_create::create_dbf(table.string(), {{"NAME", 'C', 20}}, xbase::dbf_create::Flavor::X64, error), error);
        {
            xbase::DbArea area; area.open(table.string());
            for (const auto* name : {"Ada", "Grace"}) require(area.appendBlank() && area.set(1, name) && area.writeCurrent(), "Fixture rows");
        }
        const auto original = bytes(table);
        const auto leaf = image(posture("STUDENTS.dbf"), {{"STUDENTS.dbf", original}});
        const auto memo_path = root / "NEST.dtx";
        std::string live_token;
        {
            dottalk::memo::MemoStore memo; require(memo.open(memo_path.string(), dottalk::memo::OpenMode::CreateIfMissing).ok, "Create nested memo");
            const auto live = memo.put_text(leaf), dead = memo.put_text(leaf);
            require(live.ok && dead.ok && memo.erase(dead.ref).ok, "Live and tombstoned nested objects");
            require(memo.put_text("ordinary memo text").ok, "Non-image memo object"); live_token = live.ref.token;
        }
        const auto nest_table = root / "NEST.dbf";
        require(xbase::dbf_create::create_dbf(nest_table.string(), {{"IMAGE", 'M', 16}}, xbase::dbf_create::Flavor::X64, error), error);
        {
            xbase::DbArea area; area.open(nest_table.string());
            require(area.appendBlank() && area.set(1, live_token) && area.writeCurrent(), "DBF links live nested image");
        }
        const auto memo_before = bytes(memo_path), nest_before = bytes(nest_table);
        const auto outer = image(posture("NEST.dbf"), {{"NEST.dbf", nest_before}, {"NEST.dtx", memo_before}});
        require(admit_image(outer, mount).ok(), "Valid image admission");
        require(!admit_image(image(posture("../outside.dbf"), {{"STUDENTS.dbf", original}}), mount).ok(), "External posture paths refused");
        const auto tree = inspect_images(outer);
        require(tree.error.empty() && tree.nodes.size() == 2 && tree.nodes[1].depth == 1 && tree.nodes[1].payload == leaf,
                "Expand only live MINIDB objects, not tombstones or ordinary text");
        std::stop_source cancel; cancel.request_stop();
        require(!inspect_images(outer, cancel.get_token()).error.empty(), "Cancellation reported");
        SessionSnapshot loaded;
        fs::path leaf_file;
        {
        WorkbenchSession session;
        auto run = [&](Request r) { auto s = session.submit(std::move(r)).get(); require(s.ok(), s.error + "\n" + s.transcript); require(s.desk.healthy(), "No orphan areas"); return s; };
        Request r; r.action = Action::Hydrate; r.name = "ParentImage"; r.payload = outer; r.provenance = "private fixture / root";
        loaded = run(r); const auto parent = handle(loaded, r.name);
        require(loaded.areas.size() == 1 && loaded.areas.front().ram && loaded.areas.front().records == 1, "Outer DBF open in RAM");
        require(loaded.images.size() == 1 && loaded.images[0].disk_bytes == memo_before.size() && loaded.images[0].ram_bytes == nest_before.size(), "Measured RAM/disk split");
        const auto first_mount = loaded.images[0].root;
        require(!fs::exists(first_mount / "NEST.dbf") && fs::exists(first_mount / "NEST.dtx"), "Physical memo beside virtual DBF");
        const auto& ram_source = loaded.areas.front();
        const auto field_image = session.inspect_field_image(ram_source.slot, ram_source.handle, 1, 1, "IMAGE").get();
        require(field_image.error.empty() && field_image.nodes.size() == 1 && field_image.nodes[0].payload == leaf,
            "Inspect MINIDB from a RAM table with a disk DTX");
        r.name = "NestedImage"; r.payload = field_image.nodes[0].payload; r.workspace = parent;
        loaded = run(r); const auto child = handle(loaded, r.name);
        require(loaded.areas.size() == 2 && loaded.areas.back().records == 2, "Nested image table records");
        for (const auto& ws : loaded.desk.workspaces) if (ws.handle == child) require(ws.parent == parent, "Explicit nested workspace parent");
        r.name = "PeerImage"; r.workspace = 0; loaded = run(r);
        require(loaded.areas.size() == 3 && loaded.images.size() == 3, "Repeated image load is additive");
        // An inspected image is a value independent of the currently selected
        // table, including its cursor and uncommitted edits.
        for (const auto* command : {"GO BOTTOM", "TABLE ON", "REPLACE NAME WITH 'Buffered peer'", "BROWSE"}) {
            Request c; c.action = Action::Command; c.name = command; loaded = run(c);
        }
        require(loaded.table.current_record == 2 && loaded.table.pending_records == 1 &&
            loaded.table.rows[1].values[0] == "Buffered peer", "Export fixture has a real pending edit");
        const auto export_before = loaded;
        leaf_file = loaded.home / "Exported nested image.minidb";
        const auto root_file = loaded.home / "Exported outer image.minidb";
        Request export_request; export_request.action = Action::ExportImage;
        export_request.payload = field_image.nodes[0].payload; export_request.path = leaf_file;
        export_request.provenance = field_image.provenance;
        loaded = run(export_request);
        require(loaded.exported_image == leaf_file && bytes(leaf_file) == leaf && bytes(leaf_file) != outer,
            "Export the memo's exact nested payload, not its outer carrier or current workspace");
        require(loaded.desk.current_handle == export_before.desk.current_handle &&
            loaded.desk.workspace_count == export_before.desk.workspace_count && loaded.areas.size() == 3 &&
            loaded.table.area_handle == export_before.table.area_handle && loaded.table.current_record == 2 &&
            loaded.table.pending_records == 1 && loaded.table.rows[1].values[0] == "Buffered peer",
            "Export preserves workspace, area, cursor and native table buffer");
        export_request.payload = tree.nodes[0].payload; export_request.path = root_file;
        require(run(export_request).exported_image == root_file && bytes(root_file) == outer, "Root export retains exact nested DTX bytes");
        const auto root_back = session.inspect_image_file(root_file).get();
        require(root_back.error.empty() && root_back.nodes.size() == 2 && root_back.nodes[1].payload == leaf,
            "Exported root retains its nested database");
        export_request.path = leaf_file;
        auto refused = session.submit(export_request).get();
        require(!refused.ok() && refused.exported_image.empty() && bytes(leaf_file) == leaf,
            "Existing image is never overwritten by a different payload");
        for (const auto& invalid : {std::string(), std::string("plain text"), leaf.substr(0, leaf.size() - 2)}) {
            export_request.path = loaded.home / "Invalid export.minidb"; export_request.payload = invalid;
            refused = session.submit(export_request).get();
            require(!refused.ok() && refused.exported_image.empty() && !fs::exists(export_request.path),
                "Empty, non-image and truncated MINIDB exports fail before a destination is written");
        }
        export_request.payload = leaf; export_request.path.clear();
        require(!session.submit(export_request).get().ok(), "Missing export filename refused");
        export_request.path = loaded.home / "absent folder" / "image.minidb";
        refused = session.submit(export_request).get();
        require(!refused.ok() && refused.exported_image.empty() && !fs::exists(export_request.path.parent_path()),
            "Missing destination folder fails without making it");
        export_request.path = loaded.home;
        require(!session.submit(export_request).get().ok() && fs::is_directory(loaded.home), "Existing directory preserved");
        r = {}; r.action = Action::Command; r.name = "ROLLBACK"; loaded = run(r);
        const auto catalog = session.inspect(loaded.home / "workspaces/WORKSPACES.dbf").get();
        require(catalog.ok() && catalog.entries.size() == 3, "Private imported images have canonical identities");
        for (const auto& saved : catalog.entries) require(saved.container.ok, "Private catalog payload readback");
        r = {}; r.action = Action::OpenCopy; r.path = table; loaded = run(r);
        require(loaded.areas.size() == 4 && !loaded.areas.back().ram && loaded.areas.back().records == 2, "Disk copy still opens after hydration changes roots");
        const auto prior_current = loaded.desk.current_handle;
        r = {}; r.action = Action::Hydrate; r.name = "BrokenImage"; r.payload = image(posture("BROKEN.dbf"), {{"BROKEN.dbf", "bad"}});
        const auto failed = session.submit(r).get();
        require(!failed.ok() && failed.areas.size() == 4 && failed.desk.current_handle == prior_current, "Failed load restores prior desk and preserves peers");
        r = {}; r.action = Action::Command; r.name = "SWITCH ParentImage"; run(r);
        r = {}; r.action = Action::Recursion; r.enabled = false; run(r);
        r = {}; r.action = Action::SaveImage; r.workspace = parent; r.path = loaded.home / "Nested saved.minidb";
        const auto saved = run(r);
        const auto saved_tree = session.inspect_image_file(saved.saved_image).get();
        require(saved_tree.error.empty() && saved_tree.nodes.size() == 2 && saved_tree.nodes[1].payload == leaf,
            "RAM resave preserves the live nested MINIDB bytes in its carried DTX");
        r = {}; r.action = Action::Recursion; r.enabled = true; run(r);
        r.action = Action::CloseWorkspace; loaded = run(r);
        require(loaded.areas.size() == 2, "Recursive close excludes independent peer image");
        r = {}; r.action = Action::Command; r.name = "SWITCH PeerImage"; run(r);
        r.name = "WORKSPACE LOAD ParentImage MEMO RAM"; loaded = run(r);
        require(loaded.command_images.size() == 1 && loaded.command_images[0].tree.nodes.size() == 2 &&
                loaded.command_images[0].tree.nodes[1].payload == leaf && loaded.command_images[0].opened_areas.size() == 1,
                "Command hydration publishes nested image bytes and actual parent table identity");
        r.name = "WORKSPACE LOAD BrokenImage MEMO RAM"; loaded = run(r);
        require(loaded.command_images.size() == 1 && loaded.command_images[0].opened_areas.empty() && loaded.command_opened_tables == 0,
                "Materialized bytes with an invalid DBF report zero opened tables, never complete hydration");
        auto mounts = loaded.images;
        session.shutdown();
        for (const auto& resident : mounts)
            require(!xbase::ramfs::mounted(resident.root.string()) && xbase::ramfs::list(resident.root.string()).empty(), "Shutdown releases own RAM mounts");
        }
        {
            WorkbenchSession fresh;
            const auto reopened = fresh.inspect_image_file(leaf_file).get();
            require(reopened.error.empty() && reopened.nodes.size() == 1 && reopened.nodes[0].payload == leaf,
                "Fresh session reads exact exported child bytes");
            Request restore; restore.action = Action::Hydrate; restore.name = "ExportReopened";
            restore.payload = reopened.nodes[0].payload; restore.provenance = leaf_file.string();
            const auto restored = fresh.submit(restore).get();
            require(restored.ok() && restored.areas.size() == 1 && restored.areas[0].records == 2 && restored.areas[0].ram,
                "Exported child reopens as its own RAM workspace");
            const auto& area = restored.areas[0];
            for (std::uint64_t recno = 1; recno <= 2; ++recno) {
                const auto value = fresh.inspect_field(area.slot, area.handle, recno, 1, "NAME").get();
                require(value.error.empty() && value.text == (recno == 1 ? "Ada" : "Grace"),
                    "Restored exported data excludes unrelated buffered edits");
            }
            Request export_request; export_request.action = Action::ExportImage;
            export_request.path = restored.home / "Reexported file image.minidb";
            export_request.payload = reopened.nodes[0].payload;
            const auto reexported = fresh.submit(export_request).get();
            require(reexported.ok() && bytes(reexported.exported_image) == leaf, "File input also exports without rewriting");
            fresh.shutdown();
        }
        require(bytes(table) == original && bytes(nest_table) == nest_before && bytes(memo_path) == memo_before, "Source DBF/DTX bytes unchanged");
        for (const auto& path : {table, nest_table, memo_path}) fs::remove(path);
        fs::remove(root);
        std::cout << "PASS MINIDB: path/length admission, live nested DTX, nested image resave, real MEMO RAM load, additive identities, byte readback, RAM/disk split, failure recovery, copy after hydration, scoped close, mount teardown, unchanged sources\n";
        std::cout << "PASS image export: exact root/nested/memo/file bytes, existing destination preserved, malformed/missing destinations refused, workspace/area/cursor/buffer preserved, fresh session hydrates Ada and Grace\n";
        std::cout << "PASS command image: nested DTX payload observed; invalid materialized DBF reports zero opened tables\n";
        std::cout << "session_home=" << loaded.home.string() << '\n';
        return 0;
    } catch (const std::exception& e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}
