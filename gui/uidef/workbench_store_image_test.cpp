// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: buffered database image storage in memo fields
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_session.hpp"
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "memo/memostore.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
namespace fs = std::filesystem;
using namespace dottalk::workbench;
void require(bool ok, const std::string& why) { if (!ok) throw std::runtime_error(why); }
std::string bytes(const fs::path& path) {
    std::ifstream in(path, std::ios::binary); return {std::istreambuf_iterator<char>(in), {}};
}
void write(const fs::path& path, const std::string& value) {
    std::ofstream out(path, std::ios::binary); out.write(value.data(), static_cast<std::streamsize>(value.size()));
    out.close(); require(static_cast<bool>(out), "Write fixture");
}
std::string image(const fs::path& path) {
    const std::string posture = "DTSHEMA 3\nAREA 4 | dbf=ROWS.dbf | index=none | alias=ROWS\nCURRENT 4\n";
    const auto body = bytes(path);
    return "MINIDB 1\nPOSTURE " + std::to_string(posture.size()) + "\n" + posture +
        "FILE " + std::to_string(body.size()) + " ROWS.dbf\n" + body + "END\n";
}
int main() {
    try {
        const auto root = fs::temp_directory_path() / ("workbench store image " +
            std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
        require(fs::create_directory(root), "Create fixture root");
        const auto source = root / "SHELF.dbf", sidecar = root / "SHELF.dtx", rows = root / "ROWS.dbf";
        const auto image_file = root / "New database image.minidb";
        std::string error;
        require(xbase::dbf_create::create_dbf(rows.string(), {{"NAME", 'C', 24}}, xbase::dbf_create::Flavor::X64, error), error);
        { xbase::DbArea a; a.open(rows.string()); require(a.appendBlank() && a.set(1, "Original") && a.writeCurrent(), "Old image row"); }
        const auto old_image = image(rows);
        { xbase::DbArea a; a.open(rows.string()); a.gotoRec64(1);
          require(a.set(1, "Ada") && a.writeCurrent() && a.appendBlank() && a.set(1, "Grace") && a.writeCurrent(), "New image rows"); }
        const auto new_image = image(rows);
        write(image_file, new_image);
        const auto large_file = root / "Large database image.minidb";
        const auto large_image = new_image.substr(0, new_image.size() - 4) +
            "FILE 1100000 padding.bin\n" + std::string(1100000, '\0') + "END\n";
        write(large_file, large_image);
        require(xbase::dbf_create::create_dbf(source.string(), {{"IMAGE", 'M', 16}, {"FIXED", 'M', 8}, {"LABEL", 'C', 24}},
            xbase::dbf_create::Flavor::X64, error), error);
        {
            dottalk::memo::MemoStore store; require(store.open(sidecar.string(), dottalk::memo::OpenMode::CreateIfMissing).ok, "Memo fixture");
            const auto id = store.put_text_id(old_image, &error); require(id != 0, error);
            xbase::DbArea a; a.open(source.string());
            for (int row = 1; row <= 3; ++row)
                require(a.appendBlank() && a.set(1, row == 3 ? "" : store.ref_from_object_id(id).token) &&
                    a.set(2, row == 3 ? "0" : std::to_string(id)) && a.set(3, "original label") && a.writeCurrent(), "Shared old references");
        }
        const auto dbf_before = bytes(source), memo_before = bytes(sidecar);
        fs::path private_copy, carrier_file, home;
        {
            WorkbenchSession session;
            auto run = [&](Request r = {}) { auto s = session.submit(std::move(r)).get(); require(s.ok(), s.error + "\n" + s.transcript);
                require(s.desk.healthy(), "Desk remains healthy"); return s; };
            auto command = [&](const std::string& line) { Request r; r.action = Action::Command; r.name = line; return run(r); };
            Request open; open.action = Action::OpenCopy; open.path = source; auto s = run(open);
            private_copy = s.areas[0].path; home = s.home;
            command("GO 2"); s = command("BROWSE");
            FieldEdit e; e.slot = s.table.slot; e.handle = s.table.area_handle; e.record = 1; e.field1 = 1; e.field_name = "IMAGE";
            auto target = [&](FieldEdit field) { auto t = session.inspect_memo_target(field).get(); require(t.error.empty(), t.error); return t.edit; };
            auto read = [&](std::uint64_t rec, int field = 1) { return session.inspect_field_image(e.slot, e.handle, rec, field, field == 1 ? "IMAGE" : "FIXED").get(); };
            auto store_request = [&](const FieldEdit& field, const fs::path& file) { Request r; r.action = Action::StoreImage; r.edit = field; r.path = file; return r; };
            auto request = store_request(target(e), image_file);
            auto bad = request; bad.edit.handle += 1000;
            require(!session.submit(bad).get().ok(), "Stale area handle refused");
            bad = request; bad.edit.field_name = "WRONG";
            require(!session.submit(bad).get().ok(), "Stale field name refused");
            bad = request; bad.edit.record = 999;
            require(!session.submit(bad).get().ok(), "Missing record refused");
            bad = request; bad.edit.expected_value = "changed";
            require(!session.submit(bad).get().ok(), "Stale memo reference refused");
            bad = request; bad.edit.field1 = 3; bad.edit.field_name = "LABEL";
            require(!session.submit(bad).get().ok(), "Non-memo target refused");
            for (const auto& value : {std::string(), std::string("not an image"), new_image.substr(0, new_image.size() - 2)}) {
                const auto invalid_file = root / "Invalid.minidb"; write(invalid_file, value);
                require(!session.submit(store_request(request.edit, invalid_file)).get().ok(), "Bad payload refused");
            }
            for (const auto& path : {fs::path{}, root / "Missing.minidb", root})
                require(!session.submit(store_request(request.edit, path)).get().ok(), "Missing/directory source refused");
            require(run().dirty_areas == 0 && read(1).nodes[0].payload == old_image, "Refusals leave memo and buffer intact");
            command("TABLE ON"); command("REPLACE LABEL WITH 'pending scalar'");
            const auto before = run();
            s = run(request);
            require(s.table.current_record == 2 && s.table.pending_records == 2 && s.desk.current_handle == before.desk.current_handle &&
                s.desk.current_engine_area == before.desk.current_engine_area, "Store preserves cursor/selection and separate scalar buffer");
            require(!read(1).error.empty(), "Pending memo inspection requires resolution");
            require(read(2).nodes[0].payload == old_image && read(1, 2).nodes[0].payload == old_image, "Other references retain original bytes before commit");
            require(!session.submit(request).get().ok(), "Second memo edit refused until resolution");
            s = command("ROLLBACK"); require(s.dirty_areas == 0 && read(1).nodes[0].payload == old_image, "Rollback restores original memo reference");
            command("REPLACE LABEL WITH 'scalar survives'");
            request.edit = target(e); run(request); command("COMMIT");
            require(read(1).nodes[0].payload == new_image && read(2).nodes[0].payload == old_image &&
                read(1, 2).nodes[0].payload == old_image, "Committed token replacement preserves all old shared references");
            const auto label = session.inspect_field(e.slot, e.handle, 2, 3, "LABEL").get();
            require(label.error.empty() && label.text == "scalar survives", "Scalar buffer commits alongside image reference");
            auto fixed = e; fixed.field1 = 2; fixed.field_name = "FIXED";
            auto fixed_request = store_request(target(fixed), large_file); run(fixed_request); command("ROLLBACK");
            require(read(1, 2).nodes[0].payload == old_image, "Fixed reference rollback preserves old bytes");
            fixed_request.edit = target(fixed); run(fixed_request); command("COMMIT");
            require(read(1, 2).nodes[0].payload == large_image, "Fixed reference stores more than 1 MiB including embedded NUL bytes");
            auto empty = e; empty.record = 3; run(store_request(target(empty), image_file)); command("COMMIT");
            require(read(3).nodes[0].payload == new_image, "Empty token memo accepts an image");
            empty.field1 = 2; empty.field_name = "FIXED"; run(store_request(target(empty), image_file)); command("COMMIT");
            require(read(3, 2).nodes[0].payload == new_image, "Empty fixed memo accepts an image");
            // Capture a real target, change its reference, then try the stale request.
            auto stale = store_request(target(e), large_file);
            run(store_request(target(e), image_file)); command("COMMIT");
            require(!session.submit(stale).get().ok() && read(1).nodes[0].payload == new_image, "Actual intervening memo write refuses stale target");
            command("GO 1"); command("DELETE");
            require(!session.inspect_memo_target(e).get().error.empty(), "Pending deleted row refused"); command("ROLLBACK");
            command("SET MODE SQL"); command("BEGIN");
            require(!session.submit(store_request(e, image_file)).get().ok(), "Active SQL transaction refused");
            command("ROLLBACK"); command("SET MODE NATIVE");
            command("CLOSE"); s = command("USE " + private_copy.string()); s = command("BROWSE");
            e.slot = s.table.slot; e.handle = s.table.area_handle;
            require(read(1).nodes[0].payload == new_image && read(1, 2).nodes[0].payload == large_image &&
                read(2).nodes[0].payload == old_image, "Close/reopen preserves both reference formats and original shared object");
            Request save; save.action = Action::SaveImage; save.workspace = s.desk.current_handle;
            save.path = carrier_file = home / "Carrier with stored databases.minidb";
            run(save);
            session.shutdown();
        }
        {
            WorkbenchSession fresh;
            const auto tree = fresh.inspect_image_file(carrier_file).get(); require(tree.error.empty() && tree.nodes.size() > 1, "Stored databases are nested in saved carrier");
            Request r; r.action = Action::Hydrate; r.name = "Carrier"; r.payload = tree.nodes[0].payload;
            auto s = fresh.submit(r).get(); require(s.ok() && s.areas.size() == 1 && s.areas[0].ram, "Fresh carrier opens in RAM");
            const auto a = s.areas[0];
            auto stored = fresh.inspect_field_image(a.slot, a.handle, 1, 1, "IMAGE").get();
            require(stored.error.empty() && stored.nodes[0].payload == new_image, "New session reads exact stored image from RAM table");
            FieldEdit e; e.slot = a.slot; e.handle = a.handle; e.record = 2; e.field1 = 1; e.field_name = "IMAGE";
            const auto t = fresh.inspect_memo_target(e).get(); require(t.error.empty(), t.error);
            r = {}; r.action = Action::StoreImage; r.edit = t.edit; r.path = image_file;
            require(fresh.submit(r).get().ok(), "Store image into RAM table with disk DTX");
            r = {}; r.action = Action::CommitTable; r.slot = a.slot; r.area_handle = a.handle;
            require(fresh.submit(r).get().ok(), "Commit RAM table memo reference");
            require(fresh.inspect_field_image(a.slot, a.handle, 2, 1, "IMAGE").get().nodes[0].payload == new_image,
                "RAM reference readback");
            r = {}; r.action = Action::Hydrate; r.name = "FromStoredField"; r.payload = stored.nodes[0].payload;
            r.workspace = s.desk.current_handle; s = fresh.submit(r).get();
            require(s.ok() && s.areas.size() == 2 && s.areas.back().records == 2, "Stored field hydrates as a child workspace");
            const auto child = s.areas.back();
            const auto value = fresh.inspect_field(child.slot, child.handle, 2, 1, "NAME").get();
            require(value.error.empty() && value.text == "Grace", "Hydrated stored database contains the expected data");
            require(!fresh.inspect_memo_target(e).get().error.empty(), "Wrong selected area refuses a retained target");
            fresh.shutdown();
        }
        require(bytes(source) == dbf_before && bytes(sidecar) == memo_before && bytes(image_file) == new_image, "Source table, memo and image file unchanged");
        std::cout << "PASS store image: token/fixed/empty fields, exact binary bytes, rollback, commit/reopen, shared references preserved, "
                     "scalar buffer and cursor preservation, invalid/stale/deleted/SQL refusals, nested carrier, RAM table write and child hydration, unchanged sources\n"
                  << "memo_source=" << source.string() << "\nimage_source=" << image_file.string() << "\nsession_home=" << home.string() << '\n';
        return 0;
    } catch (const std::exception& e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}
