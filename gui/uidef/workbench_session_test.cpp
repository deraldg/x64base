// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: serialized session native proof
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_session.hpp"
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include <fstream>
#include <iostream>
namespace fs = std::filesystem;
using namespace dottalk::workbench;
void require(bool ok, const std::string& reason) { if (!ok) throw std::runtime_error(reason); }
std::string bytes(const fs::path& p) {
    std::ifstream in(p, std::ios::binary); return {std::istreambuf_iterator<char>(in), {}};
}
int main() {
    try {
        // A source path with spaces exercises copy admission independently of
        // the engine command's whitespace-only tokenizer.
        const auto source_dir = fs::temp_directory_path() / ("workbench source " +
            std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
        require(fs::create_directory(source_dir), "create fixture directory");
        const auto source = source_dir / "SAMPLE.dbf";
        std::string error;
        require(xbase::dbf_create::create_dbf(source.string(), {{"VALUE", 'C', 20}},
            xbase::dbf_create::Flavor::X64, error), error);
        {
            xbase::DbArea area; area.open(source.string());
            for (const auto* value : {"first", "second"}) {
                require(area.appendBlank() && area.set(1, value) && area.writeCurrent(), "create fixture records");
            }
        }
        const auto original = bytes(source);
        WorkbenchSession session;
        bool second_refused = false;
        try { WorkbenchSession second; } catch (const std::exception&) { second_refused = true; }
        require(second_refused, "reject a concurrent second engine");
        auto snapshot = session.submit().get(); require(snapshot.ok(), snapshot.error);
        const auto home = snapshot.home;
        require(snapshot.desk.workspace_count == 1 && snapshot.desk.open_area_count == 0, "clean DEFAULT session");
        require(!fs::exists(home / "workspaces/WORKSPACES.dbf"), "observation does not create catalog");
        auto run = [&](Request request) {
            auto result = session.submit(std::move(request)).get();
            require(result.ok(), result.error + "\n" + result.transcript);
            require(result.desk.healthy(), "no orphan areas"); return result;
        };
        auto handle = [](const SessionSnapshot& s, const std::string& name) {
            for (const auto& ws : s.desk.workspaces) if (ws.name == name) return ws.handle;
            throw std::runtime_error("missing workspace " + name);
        };
        Request listing; listing.action = Action::Command; listing.name = "list";
        auto empty_list = run(listing);
        require(empty_list.transcript.find("No table open.") != std::string::npos, "LIST reaches engine in empty session");
        listing.name = "list usage";
        require(run(listing).transcript.find("LIST TOP") != std::string::npos, "LIST USAGE works without a table");
        Request r; r.action = Action::NewWorkspace; r.name = "BAD_CHILD"; r.workspace = 1;
        require(!session.submit(r).get().ok(), "undurable DEFAULT parent refused");
        r.workspace = 0; r.name = "PARENT"; snapshot = run(r); const auto parent = handle(snapshot, r.name);
        require(snapshot.desk.current_handle == parent && snapshot.desk.open_area_count == 0,
            "NEW enters an empty root workspace");
        r.workspace = parent; r.name = "CHILD"; snapshot = run(r); const auto child = handle(snapshot, r.name);
        require(snapshot.desk.current_handle == child, "NEW UNDER enters the new child");
        r.workspace = 0; r.name = "PEER"; snapshot = run(r); const auto peer = handle(snapshot, r.name);
        require(snapshot.desk.workspace_count == 4, "three workspaces are additive to DEFAULT");
        require(!session.submit(r).get().ok(), "duplicate workspace refused");
        const auto catalog = session.inspect(home / "workspaces/WORKSPACES.dbf").get();
        require(catalog.ok() && catalog.entries.size() == 3, "canonical birth rows in private catalog");
        std::uint64_t parent_id = 0, child_id = 0;
        for (const auto& ws : snapshot.desk.workspaces) {
            if (ws.handle != 1) require(ws.ws_id && ws.roots_stamped, "durable identity and roots at birth");
            if (ws.handle == parent) parent_id = ws.ws_id;
            if (ws.handle == child) { child_id = ws.ws_id; require(ws.parent == parent && ws.depth == 1, "runtime containment"); }
        }
        for (const auto& row : catalog.entries) if (row.id == child_id)
            require(row.parent_id == parent_id && row.previous_id == 0, "durable containment is not version lineage");
        auto switch_to = [&](std::uint64_t ws) { Request q; q.action = Action::SwitchWorkspace; q.workspace = ws; return run(q); };
        for (auto ws : {parent, child, peer}) {
            switch_to(ws); Request q; q.action = Action::OpenCopy; q.path = source; snapshot = run(q);
        }
        require(snapshot.areas.size() == 3 && snapshot.desk.name_fanout.size() == 1, "same table name in three workspaces");
        for (const auto& area : snapshot.areas) require(area.records == 2 && area.path != source.string(), "two records in private copies");
        const auto self = scope_areas(snapshot, parent, false, false);
        require(self.error.empty() && self.workspaces == 1 && self.indices.size() == 1 &&
            snapshot.areas[self.indices[0]].workspace == parent, "Parent-only browser scope");
        const auto nested = scope_areas(snapshot, parent, false, true);
        require(nested.error.empty() && nested.workspaces == 2 && nested.indices.size() == 2 &&
            snapshot.areas[nested.indices[1]].workspace == child, "Nested browser scope excludes peer");
        const auto child_view = scope_areas(snapshot, parent, false, true, "  cHiLd  ");
        require(child_view.indices.size() == 1 && snapshot.areas[child_view.indices[0]].workspace == child &&
            child_view.indices[0] != 0, "Filtered first row maps to its original area index");
        require(scope_areas(snapshot, parent, false, false, "CHILD").indices.empty(), "Search cannot escape scope");
        require(scope_areas(snapshot, parent, true, false, "sample").indices.size() == 3, "All-workspace table-name search includes duplicates");
        const auto peer_view = scope_areas(snapshot, child, true, true, "peer");
        require(peer_view.indices.size() == 1 && snapshot.areas[peer_view.indices[0]].workspace == peer, "All-workspace owner-name search");
        require(scope_areas(snapshot, 1, false, true).indices.empty(), "Empty workspace has no unrelated tables");
        require(!scope_areas(snapshot, 999999, false, true).error.empty(), "Missing workspace scope is explicit");
        auto projection = snapshot;
        projection.desk.recursion_enabled = !snapshot.desk.recursion_enabled;
        require(scope_areas(projection, parent, false, true).indices == nested.indices, "Browser nesting is independent of engine recursion");
        auto grandchild = projection.desk.workspaces.back();
        grandchild.handle = 9001; grandchild.parent = child; grandchild.name = "GRANDCHILD";
        projection.desk.workspaces.insert(projection.desk.workspaces.begin(), grandchild);
        auto nested_area = projection.areas.back(); nested_area.workspace = grandchild.handle; nested_area.handle = 9002;
        projection.areas.push_back(nested_area);
        require(scope_areas(projection, parent, false, true).indices.size() == 3,
            "Synthetic unordered grandchild snapshot exercises transitive traversal");
        const auto tree = navigator_view(projection);
        require(tree.workspaces.size() == 5 && tree.areas.size() == 4, "Navigator includes empty roots and unordered grandchild");
        const auto branch = navigator_view(projection, " pArEnT ");
        require(branch.workspaces.size() == 3 && branch.areas.size() == 3, "Workspace search includes descendants and own tables");
        const auto leaf = navigator_view(projection, "grandchild");
        require(leaf.workspaces.size() == 3 && leaf.areas.size() == 1 && leaf.areas[0] == projection.areas.size() - 1,
            "Deep workspace search retains ancestors without unrelated ancestor tables");
        require(navigator_view(projection, "SAMPLE").areas.size() == 4, "Same-name table search retains distinct identities");
        require(navigator_view(projection, "no match").workspaces.empty(), "Unmatched query has no false default workspace");
        projection.desk.workspaces.back().parent = projection.desk.workspaces.back().handle;
        require(navigator_view(projection, "peer").workspaces.size() == 1, "Cycle in snapshot is bounded");
        const auto after_view = session.submit().get();
        require(after_view.ok() && after_view.desk.current_handle == snapshot.desk.current_handle &&
            after_view.desk.current_engine_area == snapshot.desk.current_engine_area, "Browsing scope does not switch or select");
        const auto listed_area = snapshot.desk.current_engine_area;
        listing.name = "list all"; auto listed = run(listing);
        require(listed.transcript.find("first") != std::string::npos && listed.transcript.find("second") != std::string::npos,
            "LIST ALL prints actual row values");
        listing.name = "list top 1"; listed = run(listing);
        require(listed.transcript.find("first") != std::string::npos && listed.transcript.find("second") == std::string::npos,
            "LIST limit is honored");
        listing.name = "list all for VALUE = 'second'"; listed = run(listing);
        require(listed.transcript.find("first") == std::string::npos && listed.transcript.find("1 record") != std::string::npos,
            "LIST FOR filters actual rows");
        listing.name = "list for VALUE = 'first' GARBAGE"; listed = run(listing);
        require(listed.transcript.find("refusing") != std::string::npos && listed.transcript.find("record(s) listed") == std::string::npos,
            "Malformed LIST FOR refuses instead of showing all rows");
        require(listed.desk.current_handle == peer && listed.desk.current_engine_area == listed_area,
            "LIST preserves current workspace and selected area");
        const auto first = snapshot.areas.front();
        r = {}; r.action = Action::SelectArea; r.slot = first.slot; r.area_handle = first.handle; snapshot = run(r);
        require(snapshot.desk.current_handle == peer && snapshot.desk.current_engine_area == first.slot,
            "select area does not silently switch workspace");
        r = {}; r.action = Action::Command;
        for (const auto* line : {"SELECT", "SELECT wrong", "SELECT -1", "SELECT 512", "SELECT 999999999999999999999"}) {
            r.name = line; snapshot = run(r);
            require(snapshot.desk.current_engine_area == first.slot, "usage/invalid SELECT preserves current area");
            require(snapshot.transcript.size() > r.name.size() + 3, "SELECT produces an engine response, not just command echo");
        }
        r.name = "SELECT " + std::to_string(snapshot.areas.back().slot); snapshot = run(r);
        require(snapshot.desk.current_engine_area == snapshot.areas.back().slot, "typed SELECT n selects through real command");
        r.name = "SWITCH CHILD"; snapshot = run(r);
        require(snapshot.desk.current_handle == child, "typed SWITCH name resolves through shared shortcut");
        const auto child_area = std::find_if(snapshot.areas.begin(), snapshot.areas.end(),
            [child](const auto& area) { return area.workspace == child; });
        require(child_area != snapshot.areas.end() && snapshot.desk.current_engine_area == child_area->slot,
            "SWITCH selects the destination's first open area");
        const auto child_slot = child_area->slot;
        r.name = "SELECT SAMPLE"; snapshot = run(r);
        require(snapshot.desk.current_engine_area == child_slot,
            "SELECT table name resolves in current workspace");
        r.name = "SELECT PEER:SAMPLE"; snapshot = run(r);
        require(snapshot.desk.current_handle == child && snapshot.desk.current_engine_area == snapshot.areas.back().slot,
            "qualified SELECT reaches peer without switching workspace");
        r.name = "SWITCH missing_workspace"; snapshot = run(r);
        require(snapshot.desk.current_handle == child, "unknown SWITCH target preserves workspace");
        r.name = "WORKDESK"; snapshot = run(r);
        require(snapshot.transcript.find("PARENT") != std::string::npos, "WORKDESK uses engine observer");
        require(snapshot.registered_commands > 200, "full command registry attached");
        r.name = "BROWSER"; require(!session.submit(r).get().ok(), "terminal-only command explains its limitation");
        const auto registered = snapshot.registered_commands;
        auto execute = [&](const std::string& line) {
            Request cmd; cmd.action = Action::Command; cmd.name = line;
            return run(cmd);
        };
        auto contains = [&](const std::string& line, const std::string& expected) {
            auto value = execute(line);
            require(value.transcript.find(expected) != std::string::npos,
                line + " expected " + expected + "\n" + value.transcript);
            return value;
        };
        contains("? 6 * 7", "42");
        execute("SET VAR wb_number = 9"); contains("? &wb_number + 1", "10");
        contains("PSHELL USAGE", "PSHELL");
        contains("HIER USAGE", "HIER");
        contains("COUNT", "\n2\n");
        execute("GO TOP"); contains("DISPLAY", "first");
        execute("SKIP 1"); contains("DISPLAY", "second");
        execute("SET FILTER TO VALUE = 'first'"); contains("COUNT", "\n1\n");
        execute("SET FILTER TO"); contains("COUNT", "\n2\n");
        contains("SQLSEL SELECT VALUE FROM SAMPLE WHERE VALUE = 'second'", "second");
        execute("GO TOP"); execute("TABLE ON");
        auto buffered = execute("REPLACE VALUE WITH 'pending'");
        require(buffered.dirty_areas == 1, "buffered write visible to host");
        r.name = "QUIT"; require(!session.submit(r).get().ok(), "QUIT preserves buffered edits");
        require(execute("ROLLBACK").dirty_areas == 0, "rollback clears dirty state");
        execute("GO TOP"); contains("DISPLAY", "first");
        execute("REPLACE VALUE WITH 'committed'");
        require(execute("COMMIT").dirty_areas == 0, "commit applies buffered changes");
        execute("TABLE OFF"); execute("GO TOP"); contains("DISPLAY", "committed");
        execute("APPEND"); execute("REPLACE VALUE WITH 'third'");
        contains("COUNT", "\n3\n");
        execute("SET DELETED ON"); execute("DELETE ALL"); contains("COUNT", "\n0\n");
        execute("RECALL ALL"); contains("COUNT", "\n3\n");
        execute("SET DELETED OFF");
        const auto script = home / "commands.dts";
        { std::ofstream file(script); file << "GO TOP\n? 20 + 22\nLIST TOP 1\n"; }
        auto scripted = contains("DOTSCRIPT \"" + script.string() + "\"", "42");
        require(scripted.transcript.find("committed") != std::string::npos, "script uses the same selected table");
        { std::ofstream file(script); file << "BROWSER\n"; }
        r.name = "DOTSCRIPT \"" + script.string() + "\"";
        require(!session.submit(r).get().ok(), "script cannot bypass terminal admission");
        execute("SET VAR wb_browser = BROWSER"); r.name = "&wb_browser";
        require(!session.submit(r).get().ok(), "macro cannot bypass terminal admission");
        contains("not_a_real_workbench_command", "Unknown command");
        require(execute("QUIT").exit_requested, "QUIT requests orderly host close");
        switch_to(parent);
        r = {}; r.action = Action::Recursion; r.enabled = false; run(r);
        r.action = Action::CloseWorkspace; snapshot = run(r);
        require(snapshot.areas.size() == 2, "nonrecursive close leaves child and peer open");
        r.action = Action::Recursion; r.enabled = true; run(r);
        r.action = Action::CloseWorkspace; snapshot = run(r);
        require(snapshot.areas.size() == 1 && snapshot.areas.front().workspace == peer, "recursive close leaves peer open");
        require(snapshot.desk.workspace_count == 4, "close retains workspace identities");
        r.action = Action::OpenCopy; r.path = source; snapshot = run(r);
        r = {}; r.action = Action::SelectArea; r.slot = first.slot; r.area_handle = first.handle;
        require(!session.submit(r).get().ok(), "stale area handle refused after slot reuse");
        require(bytes(source) == original, "source table bytes unchanged");
        // Repeated opens/closes exercise ownership reuse, not just first boot.
        for (int cycle = 0; cycle < 12; ++cycle) {
            switch_to(parent); Request close; close.action = Action::CloseWorkspace; snapshot = run(close);
            require(snapshot.areas.size() == 1 && snapshot.areas.front().workspace == peer, "cycle preserves peer");
            Request open; open.action = Action::OpenCopy; open.path = source; snapshot = run(open);
            require(snapshot.areas.size() == 2 && snapshot.desk.healthy(), "cycle reopens a clean owned area");
        }
        // Exercise the transition with occupied global slots and more than one
        // table in the destination. Browsing and explicit SELECT stay separate.
        Request extra; extra.action = Action::OpenCopy; extra.path = source;
        snapshot = run(extra);
        int parent_first = xbase::MAX_AREA;
        for (const auto& area : snapshot.areas) if (area.workspace == parent)
            parent_first = std::min(parent_first, area.slot);
        switch_to(peer); snapshot = switch_to(parent);
        require(snapshot.desk.current_engine_area == parent_first,
            "SWITCH chooses lowest global area in a populated workspace");
        const auto before_empty = snapshot;
        snapshot = execute("WORKSPACE NEW EmptyFlow");
        const auto empty = handle(snapshot, "EmptyFlow");
        require(snapshot.desk.current_handle == empty && snapshot.areas.size() == before_empty.areas.size() &&
            std::none_of(snapshot.areas.begin(), snapshot.areas.end(), [&](const auto& a) {
                return a.slot == snapshot.desk.current_engine_area;
            }), "Typed NEW enters an unused area without selecting a foreign table or opening one");
        contains("GPS", "No table open");
        const auto empty_slot = snapshot.desk.current_engine_area;
        for (const auto* refused : {"WORKSPACE NEW EmptyFlow", "WORKSPACE NEW BadFlow UNDER Missing", "SWITCH Missing"}) {
            snapshot = execute(refused);
            require(snapshot.desk.current_handle == empty && snapshot.desk.current_engine_area == empty_slot &&
                snapshot.areas.size() == before_empty.areas.size(), "Refused transition preserves both cursors and tables");
        }
        switch_to(peer); snapshot = switch_to(empty);
        require(snapshot.desk.current_engine_area == empty_slot, "SWITCH to empty workspace selects an unused area");
        snapshot = run(extra);
        require(snapshot.desk.current_engine_area == empty_slot && std::any_of(snapshot.areas.begin(), snapshot.areas.end(),
            [&](const auto& a) { return a.slot == empty_slot && a.workspace == empty; }),
            "Opening after empty NEW/SWITCH uses the target area and workspace");
        // RAM reaches engine capacity without depending on the host CRT's
        // lower disk-file descriptor limit (Windows stopped at 508 disk DBFs).
        const auto capacity = xbase::MAX_AREA - snapshot.areas.size();
        std::string posture = "DTSHEMA 3\n", files;
        for (std::size_t i = 0; i < capacity; ++i) {
            const auto name = "CAP" + std::to_string(i) + ".dbf";
            posture += "AREA " + std::to_string(i) + " | dbf=" + name + " | index=none | alias=\n";
            files += "FILE " + std::to_string(original.size()) + " " + name + "\n" + original;
        }
        posture += "CURRENT 0\n";
        Request fill; fill.action = Action::Hydrate; fill.name = "CapacityFlow";
        fill.payload = "MINIDB 1\nPOSTURE " + std::to_string(posture.size()) + "\n" + posture + files + "END\n";
        const auto full = run(fill);
        require(full.areas.size() == xbase::MAX_AREA, "RAM image fills every engine area");
        for (const auto* refused : {"WORKSPACE NEW CapacityRefused", "SWITCH DEFAULT"}) {
            snapshot = execute(refused);
            require(snapshot.transcript.find("no unused area") != std::string::npos &&
                snapshot.desk.current_handle == full.desk.current_handle &&
                snapshot.desk.current_engine_area == full.desk.current_engine_area &&
                snapshot.desk.workspace_count == full.desk.workspace_count && snapshot.areas.size() == full.areas.size(),
                "Full capacity refuses empty entry without changing either cursor or workspace/table count");
            for (std::size_t i = 0; i < full.paths.size(); ++i)
                require(snapshot.paths[i].value == full.paths[i].value, "Full-capacity refusal preserves roots");
        }
        std::vector<std::future<SessionSnapshot>> queued;
        for (int i = 0; i < 8; ++i) queued.push_back(session.submit());
        auto read = session.inspect(home / "workspaces/WORKSPACES.dbf");
        session.shutdown();
        for (auto& future : queued) require(future.get().ok(), "queued work completed before shutdown");
        require(read.get().ok(), "catalog read serialized with engine and joined");
        bool closed_refused = false;
        try { session.submit(); } catch (const std::exception&) { closed_refused = true; }
        require(closed_refused, "closed session rejects new work");
        require(bytes(source) == original, "source remains unchanged after shutdown");
        fs::remove(source); fs::remove(source_dir);
        std::cout << "PASS live session: durable births, nesting, roots, same-name areas, independent selection, "
                     "SWITCH/SELECT number/name/qualified name, LIST empty/usage/rows/limit/filter/refusal, scoped/recursive close, stale handle refusal, "
                     "12 reuse cycles, serialized reads, queued shutdown, unchanged source\n"
                  << "PASS full command console: expressions, variables, navigation, filters, SQL, buffered writes, rollback, commit, "
                     "append, delete, recall, scripts, terminal admission, orderly exit\n"
                  << "PASS workspace navigation: parent/child/peer scopes, same-name tables, transitive snapshot, independent recursion, "
                     "case-insensitive names, visible-row mapping, missing workspace, unchanged engine selection; navigator empty roots, unordered grandchild, ancestor retention, duplicates and cycles\n"
                  << "PASS workspace flow: NEW and NEW UNDER activate; SWITCH selects first open global area; empty workspace selects unused area; failed transitions preserve state; GPS and later open agree\n"
                  << "PASS workspace capacity: all engine areas filled with RAM image; empty NEW/SWITCH refuse without birth, cursor, table or path changes\n"
                  << "registered_commands=" << registered << '\n'
                  << "session_home=" << home.string() << '\n';
        return 0;
    } catch (const std::exception& e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}
