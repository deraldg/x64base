// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: live memo field to MINIDB inspection proof
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_session.hpp"
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "memo/memostore.hpp"
#include <fstream>
#include <iostream>
namespace fs = std::filesystem;
using namespace dottalk::workbench;
void require(bool ok, const std::string& why) { if (!ok) throw std::runtime_error(why); }
std::string bytes(const fs::path& path) {
    std::ifstream file(path, std::ios::binary); return {std::istreambuf_iterator<char>(file), {}};
}
int main() {
    try {
        const auto root = fs::temp_directory_path() / ("workbench memo image " +
            std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
        require(fs::create_directory(root), "create fixture root");
        const auto leaf_path = root / "STUDENTS.dbf", source = root / "LIBRARY.dbf", sidecar = root / "LIBRARY.dtx";
        std::string error;
        require(xbase::dbf_create::create_dbf(leaf_path.string(), {{"NAME", 'C', 20}}, xbase::dbf_create::Flavor::X64, error), error);
        { xbase::DbArea table; table.open(leaf_path.string());
          for (const auto* name : {"Ada", "Grace"}) require(table.appendBlank() && table.set(1, name) && table.writeCurrent(), "leaf records"); }
        const std::string posture = "DTSHEMA 3\nAREA 4 | dbf=STUDENTS.dbf | index=none | alias=STUDENTS\nCURRENT 4\n";
        const auto leaf_bytes = bytes(leaf_path);
        const auto prefix = "MINIDB 1\nPOSTURE " + std::to_string(posture.size()) + "\n" + posture +
            "FILE " + std::to_string(leaf_bytes.size()) + " STUDENTS.dbf\n" + leaf_bytes;
        const auto leaf = prefix + "END\n";
        const auto large = prefix + "FILE 1100000 padding.bin\n" + std::string(1100000, 'x') + "END\n";
        require(xbase::dbf_create::create_dbf(source.string(), {{"IMAGE", 'M', 16}, {"FIXED", 'M', 8}, {"LABEL", 'C', 16}},
            xbase::dbf_create::Flavor::X64, error), error);
        {
            dottalk::memo::MemoStore store; require(store.open(sidecar.string(), dottalk::memo::OpenMode::CreateIfMissing).ok, "memo store");
            xbase::DbArea table; table.open(source.string());
            const std::vector<std::string> payloads{leaf, "ordinary text", leaf, "", "MINIDB 1\nPOSTURE 99\nshort", large};
            for (std::size_t i = 0; i < payloads.size(); ++i) {
                std::uint64_t id = payloads[i].empty() ? 0 : store.put_text_id(payloads[i], &error);
                if (!payloads[i].empty()) require(id != 0, error);
                const auto ref = store.ref_from_object_id(id);
                require(table.appendBlank() && table.set(1, id ? ref.token : "") &&
                    table.set(2, id ? std::to_string(id) : "0") && table.set(3, "fixture") && table.writeCurrent(), "memo fixture row");
                if (i == 2) require(store.erase_id(id, &error), "deleted memo object");
            }
        }
        const auto original = bytes(source), original_memo = bytes(sidecar);
        WorkbenchSession session;
        auto run = [&](Request r = {}) { auto s = session.submit(std::move(r)).get(); require(s.ok(), s.error + "\n" + s.transcript); return s; };
        auto command = [&](const std::string& line) { Request r; r.action = Action::Command; r.name = line; return run(r); };
        Request open; open.action = Action::OpenCopy; open.path = source; auto s = run(open);
        command("GO 2"); s = command("BROWSE");
        const auto slot = s.table.slot; const auto handle = s.table.area_handle;
        auto inspect = [&](std::uint64_t record, int field = 1, const std::string& name = "IMAGE") {
            return session.inspect_field_image(slot, handle, record, field, name).get();
        };
        auto image = inspect(1);
        require(image.error.empty() && image.nodes.size() == 1 && image.nodes[0].payload == leaf, "legacy token resolves exact payload");
        require(image.provenance.find("/ record 1 / field IMAGE / committed memo") != std::string::npos, "record and field provenance");
        require(image.source_label == "LIBRARY / record 1 / field IMAGE / committed memo", "visible source field label");
        auto fixed = inspect(1, 2, "FIXED");
        require(fixed.error.empty() && fixed.nodes.size() == 1 && fixed.nodes[0].payload == leaf, "x64 fixed object id resolves exact payload");
        require(!inspect(1, 3, "LABEL").error.empty(), "non-memo refused");
        for (auto record : {2, 3, 4, 7}) require(!inspect(record).error.empty(), "plain/deleted/empty/missing memo refused");
        auto malformed = inspect(5); require(malformed.nodes.size() == 1 && !malformed.nodes[0].scan.ok, "malformed image refused by scanner");
        auto big = inspect(6);
        require(big.error.empty() && big.nodes.size() == 1 && big.nodes[0].payload == large, "image read exceeds text preview budget without truncation");
        require(!session.inspect_field(slot, handle, 6, 1, "IMAGE").get().error.empty(), "ordinary preview keeps 1 MiB limit");
        require(!inspect(1, 1, "WRONG").error.empty(), "stale field refused");
        require(!session.inspect_field_image(slot, handle + 1000, 1, 1, "IMAGE").get().error.empty(), "stale handle refused");
        std::stop_source stop; stop.request_stop();
        require(!session.inspect_field_image(slot, handle, 1, 1, "IMAGE", stop.get_token()).get().error.empty(), "cancelled read refused");
        require(run().table.current_record == 2, "all memo reads preserve record 2");
        command("GO 1"); command("TABLE ON");
        require(command("REPLACE IMAGE WITH 'pending memo'").dirty_areas == 1, "pending memo fixture");
        require(inspect(1).error.find("Commit or roll back") != std::string::npos, "pending memo explicitly refused");
        command("ROLLBACK"); require(inspect(1).nodes[0].payload == leaf, "rollback restores committed image");
        command("REPLACE FIXED WITH 'fixed pending'");
        require(inspect(1, 2, "FIXED").error.find("Commit or roll back") != std::string::npos, "fixed memo pending also refused");
        command("ROLLBACK");
        fixed = inspect(1, 2, "FIXED");
        require(fixed.error.empty() && fixed.nodes.size() == 1 && fixed.nodes[0].payload == leaf, "fixed memo rollback restores its original object");
        Request hydrate; hydrate.action = Action::Hydrate; hydrate.name = "FromMemo"; hydrate.payload = image.nodes[0].payload;
        hydrate.provenance = image.provenance; auto loaded = run(hydrate);
        require(loaded.areas.size() == 2 && loaded.areas.back().ram && loaded.areas.back().records == 2, "field image hydrates through engine");
        const auto selected = loaded.desk.current_engine_area;
        const auto workspace = loaded.desk.current_handle;
        require(inspect(1).nodes[0].payload == leaf, "inspect source while another workspace is selected");
        s = run(); require(s.desk.current_engine_area == selected && s.desk.current_handle == workspace, "inspection preserves peer selection");
        session.shutdown();
        require(bytes(source) == original && bytes(sidecar) == original_memo, "source family unchanged after shutdown");
        std::cout << "PASS memo image: token and fixed references, exact payload, provenance, cursor and peer selection, "
                     "plain/empty/deleted/malformed/stale/cancel refusal, >1 MiB image with unchanged text limit, "
                     "buffer refusal and rollback, native hydration, unchanged source\n"
                  << "session_home=" << s.home.string() << '\n';
        return 0;
    } catch (const std::exception& e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}
