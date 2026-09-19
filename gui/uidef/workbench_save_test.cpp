// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: portable MINIDB save and fresh-session restore proof
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
#include <set>
namespace fs = std::filesystem;
using namespace dottalk::workbench;
void require(bool ok, const std::string& why) { if (!ok) throw std::runtime_error(why); }
std::string bytes(const fs::path& path) {
    std::ifstream file(path, std::ios::binary); return {std::istreambuf_iterator<char>(file), {}};
}
SessionSnapshot run(WorkbenchSession& session, Request request = {}) {
    auto s = session.submit(std::move(request)).get();
    std::string diagnostic = s.error;
    for (const int slot : s.desk.orphan_open_slots) diagnostic += "\nOrphan open area " + std::to_string(slot);
    require(s.ok() && s.desk.healthy(), diagnostic + "\n" + s.transcript); return s;
}
SessionSnapshot command(WorkbenchSession& session, std::string line) {
    Request r; r.action = Action::Command; r.name = std::move(line); return run(session, r);
}
int main() {
    try {
        const auto root = fs::temp_directory_path() / ("workbench save " +
            std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
        require(fs::create_directory(root), "create fixture directory");
        const auto source = root / "SAMPLE.dbf", memo_path = root / "SAMPLE.dtx";
        const auto output = root / "Saved workspace.minidb", ram_output = root / "RAM saved.minidb";
        std::string error;
        require(xbase::dbf_create::create_dbf(source.string(), {{"NAME", 'C', 24}, {"NOTE", 'M', 16}},
            xbase::dbf_create::Flavor::X64, error), error);
        {
            dottalk::memo::MemoStore memo;
            require(memo.open(memo_path.string(), dottalk::memo::OpenMode::CreateIfMissing).ok, "fixture memo");
            const auto value = memo.put_text("Memo survives image save and reopen"); require(value.ok, value.error);
            xbase::DbArea table; table.open(source.string());
            require(table.appendBlank() && table.set(1, "original") && table.set(2, value.ref.token) && table.writeCurrent(), "fixture row");
        }
        const auto original_dbf = bytes(source), original_memo = bytes(memo_path);
        {
            WorkbenchSession session;
            auto create = [&](const char* name, std::uint64_t parent = 0) {
                Request r; r.action = Action::NewWorkspace; r.name = name; r.workspace = parent;
                const auto made = run(session, r);
                for (const auto& ws : made.desk.workspaces) if (ws.name == name) return ws.handle;
                throw std::runtime_error("create workspace");
            };
            auto select = [&](std::uint64_t handle) {
                Request r; r.action = Action::SwitchWorkspace; r.workspace = handle; return run(session, r);
            };
            auto copy = [&] { Request r; r.action = Action::OpenCopy; r.path = source; return run(session, r); };
            const auto parent = create("Parent"); select(parent); copy();
            command(session, "GO TOP"); command(session, "TABLE ON");
            require(command(session, "REPLACE NAME WITH 'committed parent'").dirty_areas == 1, "pending edit");
            Request save; save.action = Action::SaveImage; save.workspace = parent; save.path = output;
            require(!session.submit(save).get().ok() && !fs::exists(output), "pending edit refused without export");
            command(session, "COMMIT");
            command(session, "TABLE OFF"); command(session, "CDX CREATE");
            command(session, "CDX ADDTAG NAME"); command(session, "BUILDLMDB YES");
            command(session, "SET ORDER SAMPLE.cdx NAME");
            const auto child = create("Child", parent); select(child); copy();
            command(session, "GO TOP"); command(session, "REPLACE NAME WITH 'child value'"); command(session, "COMMIT");
            const auto peer = create("Peer"); select(peer); copy();
            command(session, "GO TOP"); command(session, "REPLACE NAME WITH 'PEER PRIVATE VALUE'"); command(session, "COMMIT");
            command(session, "TABLE ON");
            require(command(session, "REPLACE NAME WITH 'peer pending'").dirty_areas == 1, "peer remains pending");
            auto before = select(parent);
            // SELECT is independent of SWITCH: save must use workspace scope,
            // even with a peer's table selected.
            command(session, "SELECT Peer:SAMPLE"); before = run(session);
            Request recurse; recurse.action = Action::Recursion; recurse.enabled = false; run(session, recurse);
            save.path = root / "Parent only.minidb"; auto saved = run(session, save);
            auto tree = session.inspect_image_file(save.path).get();
            require(tree.error.empty() && tree.nodes.size() == 1 && tree.nodes[0].scan.files.size() == 3, "nonrecursive save contains only parent table, memo and index");
            require(saved.desk.current_engine_area == before.desk.current_engine_area && saved.desk.current_handle == parent && saved.dirty_areas == 1,
                "save preserves selected peer, current workspace and peer buffer");
            save.include_nested = true; save.expected_workspace = parent;
            save.path = root / "Modal nested option.minidb";
            auto modal_saved = run(session, save);
            auto modal_tree = session.inspect_image_file(save.path).get();
            require(modal_tree.error.empty() && modal_tree.nodes.size() == 1 && modal_tree.nodes[0].scan.files.size() == 5 &&
                    !modal_saved.desk.recursion_enabled && modal_saved.dirty_areas == 1,
                    "Modal include-nested option saves child, preserves peer buffer and restores recursion default");
            save.path = root / "Modal stale scope.minidb"; save.expected_workspace = peer;
            auto stale = session.submit(save).get();
            require(!stale.ok() && !fs::exists(save.path) && !stale.desk.recursion_enabled, "Stale modal save changes no output or recursion default");
            save.expected_workspace = 0; save.include_nested.reset();
            recurse.enabled = true; run(session, recurse);
            save.path = output; saved = run(session, save);
            require(saved.saved_image == output, "verified save path");
            tree = session.inspect_image_file(output).get();
            require(tree.error.empty() && tree.nodes.size() == 1 && tree.nodes[0].scan.files.size() == 5,
                "recursive save contains two duplicate-name table/memo families");
            require(bytes(output).find("PEER PRIVATE VALUE") == std::string::npos && bytes(output).find("peer pending") == std::string::npos,
                "peer bytes are absent from carrier");
            const auto saved_bytes = bytes(output);
            require(!session.submit(save).get().ok() && bytes(output) == saved_bytes, "existing destination preserved");
            save.path = root / "stale.minidb"; save.workspace = peer;
            require(!session.submit(save).get().ok() && !fs::exists(save.path), "stale workspace refused");
            save.workspace = parent; save.path = root / "transaction.minidb";
            command(session, "ROLLBACK"); command(session, "SET MODE SQL"); command(session, "BEGIN");
            require(!session.submit(save).get().ok() && !fs::exists(save.path), "SQL transaction refused");
            command(session, "ROLLBACK"); command(session, "SET MODE NATIVE");
            // Exercise the shared command's failure ordering, not just the GUI
            // export check: an unreadable active index must keep the old head.
            command(session, "WORKSPACE SAVE KeepPrevious MEMO MINIDB");
            const auto catalog_path = before.home / "workspaces/WORKSPACES.dbf";
            const auto prior = session.inspect(catalog_path).get(); require(prior.ok(), prior.error);
            const auto index = before.home / "indexes/SAMPLE.cdx", moved = before.home / "indexes/SAMPLE.missing";
            require(fs::is_regular_file(index), "active index fixture exists");
            fs::rename(index, moved);
            const auto failed = command(session, "WORKSPACE SAVE KeepPrevious MEMO MINIDB");
            fs::rename(moved, index);
            require(failed.transcript.find("WORKSPACE SAVE refused: MINIDB cannot read") != std::string::npos,
                "missing member refuses save: " + failed.transcript);
            const auto after = session.inspect(catalog_path).get();
            require(after.ok() && after.entries.size() == prior.entries.size(), "failed save did not append a row");
            for (std::size_t i = 0; i < prior.entries.size(); ++i)
                require(after.entries[i].id == prior.entries[i].id && after.entries[i].superseded == prior.entries[i].superseded &&
                    after.entries[i].payload == prior.entries[i].payload, "failed save preserves catalog heads and payloads");
        }
        auto restore = [&](const fs::path& file, bool resave) {
            WorkbenchSession session;
            const auto tree = session.inspect_image_file(file).get();
            require(tree.error.empty() && tree.nodes.size() == 1, "fresh session image inspection");
            Request r; r.action = Action::Hydrate; r.name = "Restored"; r.payload = tree.nodes[0].payload;
            r.provenance = file.string(); auto s = run(session, r);
            require(s.areas.size() == 2 && s.images.size() == 1, "fresh session restored both duplicate-name areas");
            std::set<std::string> values;
            for (const auto& area : s.areas) {
                require(area.ram && area.records == 1, "restored RAM table");
                const auto name = session.inspect_field(area.slot, area.handle, 1, 1, "NAME").get();
                const auto note = session.inspect_field(area.slot, area.handle, 1, 2, "NOTE").get();
                require(name.error.empty() && note.error.empty() && note.text == "Memo survives image save and reopen", "restored memo value");
                values.insert(name.text);
                if (name.text == "committed parent") {
                    Request select; select.action = Action::SelectArea; select.slot = area.slot; select.area_handle = area.handle;
                    run(session, select);
                    command(session, "GO BOTTOM"); command(session, "SKIP 1");
                    const auto seek = command(session, "SEEK 'committed parent'");
                    const auto browse = command(session, "BROWSE");
                    require(browse.table.current_record == 1 && browse.table.order != "natural" && !browse.table.order.empty(),
                        "restored active index finds known key: " + seek.transcript);
                }
            }
            require(values == std::set<std::string>{"committed parent", "child value"}, "committed values restored independently");
            if (resave) {
                Request save; save.action = Action::SaveImage; save.workspace = s.desk.current_handle; save.path = ram_output;
                require(run(session, save).saved_image == ram_output, "save RAM working set");
                const auto bad = session.inspect_image_file(source).get();
                require(!bad.error.empty() || (bad.nodes.size() == 1 && !bad.nodes[0].scan.ok), "non-image input refused");
            }
        };
        restore(output, true); restore(ram_output, false);
        require(bytes(source) == original_dbf && bytes(memo_path) == original_memo, "source family unchanged");
        std::cout << "PASS image save: recursion scope, peer byte exclusion, duplicate basenames, memo carriage, active index seek, pending/SQL/stale refusal, "
                     "no overwrite, independent selection, fresh-session restore, RAM resave, failed save preserves history, unchanged source\n"
                  << "saved_image=" << output.string() << '\n' << "ram_image=" << ram_output.string() << '\n';
        return 0;
    } catch (const std::exception& e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}
