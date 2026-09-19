// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: native path/default workflow proof
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
void require(bool ok, const std::string& reason) { if (!ok) throw std::runtime_error(reason); }
std::string bytes(const fs::path& p) {
    std::ifstream in(p, std::ios::binary); return {std::istreambuf_iterator<char>(in), {}};
}
fs::path slot(const SessionSnapshot& s, const std::string& name) {
    for (const auto& p : s.paths) if (p.slot == name) return p.value;
    throw std::runtime_error("Missing slot: " + name);
}
int main(int argc, char** argv) {
    try {
        if (argc == 5 && std::string(argv[1]) == "--load-definition") {
            WorkbenchSession session;
            const auto before = session.submit().get(); require(before.ok(), before.error);
            Request load; load.action = Action::LoadWorkspace; load.path = fs::absolute(argv[2]);
            load.table_root = fs::absolute(argv[3]); load.index_root = fs::absolute(argv[4]);
            const auto check = session.check_workspace(load.path, load.table_root).get();
            require(check.ready() && check.declared > 0, check.error + " missing=" + std::to_string(check.missing.size()));
            auto result = session.submit(load).get();
            require(result.ok() && result.areas.size() == static_cast<std::size_t>(check.declared), result.error + result.transcript);
            require(slot(result, "DBF") == slot(before, "DBF") && slot(result, "INDEXES") == slot(before, "INDEXES"), "Per-load roots restored");
            std::size_t rows_read = 0;
            for (const auto& area : result.areas) {
                require(fs::path(area.path).parent_path() == load.table_root, "Every declared table uses the chosen family");
                Request select; select.action = Action::SelectArea; select.slot = area.slot; select.area_handle = area.handle;
                require(session.submit(select).get().ok(), "Select real schema table");
                Request browse; browse.action = Action::Browse; browse.area_handle = area.handle;
                const auto view = session.submit(browse).get();
                require(view.ok() && view.table.open && view.table.error.empty(), view.error + view.table.error);
                if (area.records) { require(!view.table.rows.empty(), "Read real schema table rows"); ++rows_read; }
            }
            std::ostringstream proof;
            proof << result.transcript << "PASS actual schema: " << load.path.filename().string() << " declared=" << check.declared
                      << " loaded=" << result.areas.size() << " tables_with_rows_read=" << rows_read
                      << " source=" << load.table_root.string() << "\n";
            session.shutdown(); std::cout << proof.str(); return 0;
        }
        const auto root = fs::temp_directory_path() / ("workbench paths " +
            std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
        const auto data = root / "dottalkpp/data", bin = root / "dottalkpp/bin";
        for (const auto* dir : {"dbf", "dbf/system", "dbf/lesson space", "dbf/peer", "workspaces",
                                "alternate workspaces", "indexes", "lmdb", "sys", "tmp"}) fs::create_directories(data / dir);
        fs::create_directories(bin);
        std::ofstream(bin / "dottalkpp.ini") << "SET PATH DBF dbf/system\n";
        std::ofstream(bin / "init.ini") << "SET PATH DBF dbf/lesson space\n";
        const auto source = data / "dbf/STUDENTS.dbf";
        std::string error;
        require(xbase::dbf_create::create_dbf(source.string(), {{"NAME", 'C', 20}},
            xbase::dbf_create::Flavor::X64, error), error);
        { xbase::DbArea a; a.open(source.string()); require(a.appendBlank() && a.set(1, "Ada") && a.writeCurrent(), "fixture row"); }
        for (const auto* dir : {"system", "lesson space", "peer", "button open", "button load"}) {
            fs::create_directories(data / "dbf" / dir);
            fs::copy_file(source, data / "dbf" / dir / "STUDENTS.dbf");
        }
        const auto original = bytes(source);
        const auto schema_file = data / "workspaces/Button load & sample.dtschema";
        std::ofstream(schema_file) << "DTSHEMA 3\nDBFROOT " << (data / "dbf/button load").string()
            << "\nAREA 4 | dbf=STUDENTS.dbf | index=none | alias=FROM_SCHEMA\nCURRENT 4\n";
        const auto schema_bytes = bytes(schema_file);
        const auto legacy_file = data / "workspaces/Legacy load.dtschema";
        std::ofstream(legacy_file) << "DTSHEMA 2\nAREA 7 | dbf=STUDENTS.dbf | index=none | alias=LEGACY_FOLDER\nCURRENT 7\n";
        require(find_workbench_data_root(root / "build/Release/arctictalk_workbench.exe", fs::temp_directory_path()) == data,
                "Executable ancestry discovers development DATA from unrelated cwd");
        require(find_workbench_data_root(bin / "arctictalk_workbench.exe", fs::temp_directory_path()) == data,
                "Installed executable finds sibling DATA");
        require(find_workbench_data_root({}, data) == data, "DATA cwd fallback");
        WorkbenchSession session({false, data});
        auto s = session.submit().get(); require(s.ok(), s.error);
        require(slot(s, "DATA") == data && slot(s, "DBF") == data / "dbf/lesson space" && slot(s, "BIN") == bin,
                "Native initialization with system then user override");
        require(s.transcript.find("dottalkpp.ini") < s.transcript.find("init.ini") &&
                s.transcript.find("init.ini") != std::string::npos, "INIT transcript names both sources in order");
        require(s.default_catalog == data / "workspaces/WORKSPACES.dbf" && !fs::exists(s.default_catalog),
                "Default plural catalog follows WORKSPACES; startup does not create it");
        const auto home = s.home;
        auto run = [&](Request r) { auto result = session.submit(r).get(); require(result.ok(), result.error + result.transcript); return result; };
        auto command = [&](std::string line) { Request r; r.action = Action::Command; r.name = std::move(line); return run(r); };
        auto path = [&](std::string name, fs::path value) { Request r; r.action = Action::SetPath; r.name = std::move(name); r.path = std::move(value); return run(r); };
        // Competing filenames must never choose a different script just because
        // SCRIPTS has no match. Cwd and all fixtures are private to this process.
        {
            struct RestoreCwd { fs::path prior{fs::current_path()}; ~RestoreCwd() { fs::current_path(prior); } } restore;
            for (const auto* dir : {"scripts", "scripts/package", "tests", "user/scripts", "public/scripts", "alternate scripts", "cwd/scripts", "cwd/tests"})
                fs::create_directories(data / dir);
            fs::current_path(data / "cwd");
            auto script = [&](const fs::path& file, const char* dbf) { std::ofstream(file) << "SET PATH DBF dbf/" << dbf << '\n'; };
            for (const auto* dir : {"scripts", "tests", "user/scripts", "public/scripts", "cwd", "cwd/scripts", "cwd/tests"})
                script(data / dir / "choice.dts", "peer");
            script(data / "scripts/choice.dts", "system");
            s = command("DO choice");
            require(slot(s, "DBF") == data / "dbf/system" && s.transcript.find(fs::weakly_canonical(data / "scripts/choice.dts").string()) != std::string::npos,
                    "DO uses SCRIPTS only and reports exact running file: " + slot(s, "DBF").string() + "\n" + s.transcript);
            fs::rename(data / "scripts/choice.dts", data / "scripts/selected.dts");
            s = command("DO choice");
            require(slot(s, "DBF") == data / "dbf/system" && s.transcript.find("script not found") != std::string::npos &&
                    s.transcript.find((data / "scripts/choice.dts").lexically_normal().string()) != std::string::npos, "No cwd, tests or user/public fallback: " + s.transcript);
            s = command("DO tests/choice");
            require(slot(s, "DBF") == data / "dbf/peer", "Qualified DO is DATA-relative");
            script(data / "alternate scripts/choice.dts", "button open");
            path("SCRIPTS", data / "alternate scripts"); s = command("DO choice");
            require(slot(s, "DBF") == data / "dbf/button open", "DO honors SET PATH SCRIPTS override with spaces");
            path("SCRIPTS", data / "scripts");
            script(data / "scripts/package/child.dts", "button load");
            script(data / "scripts/child.dts", "peer");
            std::ofstream(data / "scripts/package/main.dts") << "DO child\n";
            s = command("DO scripts/package/main");
            require(slot(s, "DBF") == data / "dbf/button load", "Subscript uses caller's directory");
            fs::rename(data / "scripts/package/child.dts", data / "scripts/package/selected.dts");
            s = command("DO scripts/package/main");
            require(slot(s, "DBF") == data / "dbf/button load" && s.transcript.find("script not found") != std::string::npos,
                    "Missing sibling cannot fall back to SCRIPTS");
            const auto exact = data / "scripts/modal & script.dts";
            script(exact, "peer");
            Request run_script; run_script.action = Action::RunScript; run_script.path = exact;
            run_script.expected_workspace = s.desk.current_handle; s = run(run_script);
            require(slot(s, "DBF") == data / "dbf/peer", "Run script accepts exact path containing spaces and ampersand");
            run_script.path = data / "scripts/exact OUT name.dts"; script(run_script.path, "system"); s = run(run_script);
            require(slot(s, "DBF") == data / "dbf/system" && s.transcript.find("DOTSCRIPT OUT:") == std::string::npos,
                    "Quoted exact filename is never parsed as an OUT clause");
            run_script.path = data / "scripts/missing.dts";
            require(!session.submit(run_script).get().ok(), "Missing selected script refuses before dispatch");
            run_script.path = schema_file;
            require(!session.submit(run_script).get().ok(), "Run script refuses a workspace definition");
            // Keep transcript syntax working while tightening filename parsing.
            const auto transcript = data / "tmp/script transcript.txt";
            s = command("DO selected OUT \"" + transcript.string() + "\"");
            require(fs::is_regular_file(transcript) && bytes(transcript).find("selected.dts") != std::string::npos,
                    "OUT still writes the actual execution transcript");
            path("DBF", data / "dbf/lesson space");
        }
        s = command("WORKSPACE OPEN dbf NOINDEX");
        require(s.areas.size() == 1 && fs::path(s.areas.front().path) == data / "dbf/lesson space/STUDENTS.dbf",
                "WORKSPACE OPEN dbf uses initialized DBF slot, including spaces");
        command("WORKSPACE NEW PathParent"); command("SWITCH PathParent");
        s = path("DBF", "dbf/system");
        require(slot(s, "DBF") == data / "dbf/system", "UI assignment resolves relative to DATA");
        command("SELECT 4");
        s = command("WORKSPACE OPEN students NOINDEX");
        require(s.areas.size() == 2, "Bare table name opens through native DBF resolution: " + s.transcript);
        command("WORKSPACE NEW PathPeer"); command("SWITCH PathPeer"); path("DBF", "dbf/peer");
        s = command("SWITCH PathParent"); require(slot(s, "DBF") == data / "dbf/system", "SWITCH restores workspace roots");
        s = command("SET PATH RESET"); require(slot(s, "DBF") == data / "dbf", "RESET restores DATA defaults");
        command("SWITCH PathPeer"); s = command("SWITCH PathParent");
        require(slot(s, "DBF") == data / "dbf", "RESET persists on workspace switch away and back");
        s = command("SET PATH DBF dbf/lesson space IN PathPeer");
        require(slot(s, "DBF") == data / "dbf", "IN does not retarget current workspace");
        s = command("SWITCH PathPeer"); require(slot(s, "DBF") == data / "dbf/lesson space", "IN updates named workspace");
        s = command("INIT"); require(slot(s, "DBF") == data / "dbf/lesson space" && s.transcript.find("dottalkpp.ini") != std::string::npos,
                "Typed INIT uses installation config, not Workbench executable directory");
        Request bad; bad.action = Action::SetPath; bad.name = "DBF"; bad.path = "directory IN PathParent";
        require(!session.submit(bad).get().ok(), "Directory editor refuses accidental IN target");
        bad.path = "dbf\nQUIT"; require(!session.submit(bad).get().ok(), "Directory editor refuses newline");
        bad.name = "NOT_A_SLOT"; bad.path = "dbf"; require(!session.submit(bad).get().ok(), "Invalid slot refused");
        require(slot(session.submit().get(), "DBF") == data / "dbf/lesson space", "Refused edits leave paths unchanged");
        const auto posture = std::string("DTSHEMA 3\nAREA 4 | dbf=STUDENTS.dbf | index=none | alias=\nCURRENT 4\n");
        Request load; load.action = Action::Hydrate; load.name = "PathImage";
        load.payload = "MINIDB 1\nPOSTURE " + std::to_string(posture.size()) + "\n" + posture +
            "FILE " + std::to_string(original.size()) + " STUDENTS.dbf\n" + original + "END\n";
        s = run(load); require(s.images.size() == 1 && s.areas.size() == 3 && slot(s, "BIN") == bin,
                "Configured catalog image imports preserve installation BIN and mount privately");
        auto catalog = session.inspect(data / "workspaces/WORKSPACES.dbf").get();
        require(catalog.ok() && catalog.entries.size() == 3, "Births and imported image use configured workspace catalog");
        bool found = false;
        for (const auto& row : catalog.entries) if (row.value("WS_NAME") == "PathImage") found = row.payload == load.payload;
        require(found, "Imported image bytes attached to the configured catalog birth row");
        // Reproduce the maintainer's command-box workflow using actual native
        // script dispatch and directory enumeration, without GUI load helpers.
        fs::create_directories(data / "dbf/x64"); fs::create_directories(data / "scripts");
        fs::create_directories(data / "ram");
        fs::copy_file(source, data / "dbf/x64/STUDENTS.dbf");
        std::ofstream(data / "scripts/x64.dts") << "SET PATH DBF DBF/x64\nSET PATH INDEXES INDEXES/x64\nSET PATH LMDB LMDB/x64\n";
        command("SWITCH PathParent");
        command("DO x64"); s = command("WORKSPACE OPEN dbf");
        require(s.command_opened_tables == 1 && s.command_images.empty(), "Directory load reports new tables, not a MINIDB image");
        path("RAM", home / "command-ram");
        s = command("WORKSPACE LOAD PathImage MEMO RAM");
        require(s.command_images.empty() && s.command_opened_tables == 0, "Unmounted load publishes no image");
        path("BIN", home / "bin"); command("VDISK MOUNT");
        s = command("WORKSPACE LOAD PathImage MEMO RAM");
        require(s.command_images.size() == 1 && s.command_opened_tables == 1, "Native command load reports image and actual new table: " + s.transcript);
        const auto& event = s.command_images.front();
        require(event.tree.error.empty() && event.tree.nodes.size() == 1 && event.tree.nodes[0].payload == load.payload &&
                event.workspace == s.desk.current_handle && event.opened_areas.size() == 1, "Native event preserves payload, owner and opened identity");
        require(std::any_of(s.areas.begin(), s.areas.end(), [&](const auto& a) { return a.handle == event.opened_areas[0] && a.ram && a.records == 1; }),
                "Reported image area is actually open in RAM with its record");
        require(session.submit().get().command_images.empty(), "Observe never replays a stale hydration event");
        s = command("WORKSPACE LOAD DoesNotExist MEMO RAM");
        require(s.command_images.empty() && s.command_opened_tables == 0, "Missing image publishes no success event");
        // Native script dispatch must carry the same event as a typed LOAD.
        std::ofstream(data / "scripts/loadimage.dts") << "WORKSPACE LOAD PathImage MEMO RAM\n";
        s = command("DO loadimage");
        require(s.command_images.size() == 1, "Script hydration reaches the observer too");
        path("BIN", bin);
        s = path("WORKSPACES", "alternate workspaces");
        require(s.default_catalog == data / "alternate workspaces/WORKSPACES.dbf", "Catalog follows SET PATH WORKSPACES");
        require(!fs::exists(s.default_catalog), "Path changes never invent a catalog");
        command("SWITCH PathParent"); s = command("SET PATH RESET");
        require(s.default_catalog == data / "workspaces/WORKSPACES.dbf", "RESET restores catalog default");
        s = command("WORKSPACE NEW ButtonTarget");
        require(std::none_of(s.areas.begin(), s.areas.end(), [&](const auto& a) { return a.slot == s.desk.current_engine_area; }),
                "NEW moves off the previous table to an unused area");
        s = path("DBF", "dbf/button open"); const auto before_buttons = s;
        Request button; button.action = Action::OpenWorkspace; s = run(button);
        require(s.desk.current_handle == before_buttons.desk.current_handle && s.command_opened_tables == 1 &&
                s.areas.size() == before_buttons.areas.size() + 1 && slot(s, "DBF") == slot(before_buttons, "DBF") && s.command_images.empty(),
                "Open button runs native OPEN dbf in current workspace and keeps path settings: " + s.transcript);
        require(s.desk.current_engine_area == before_buttons.desk.current_engine_area &&
                std::any_of(s.areas.begin(), s.areas.end(), [&](const auto& a) {
                    return a.slot == s.desk.current_engine_area && a.workspace == s.desk.current_handle;
                }), "NEW then OPEN dbf selects the first table in the new workspace");
        button.action = Action::LoadWorkspace; button.path = schema_file;
        button.table_root = data / "workspaces"; // saved v3 root must outrank this
        s = run(button);
        require(s.desk.current_handle == before_buttons.desk.current_handle && s.command_opened_tables == 1 &&
                s.areas.size() == before_buttons.areas.size() + 2 && slot(s, "DBF") == slot(before_buttons, "DBF"),
                "Load button preserves current workspace and SET PATH while using schema roots: current=" + std::to_string(s.desk.current_handle) +
                " expected=" + std::to_string(before_buttons.desk.current_handle) + " new=" + std::to_string(s.command_opened_tables) +
                " total=" + std::to_string(s.areas.size()) + " before=" + std::to_string(before_buttons.areas.size()) +
                " DBF=" + slot(s, "DBF").string() + "\n" + s.transcript);
        const auto loaded_count = s.areas.size();
        for (const auto& prior : before_buttons.areas)
            require(std::any_of(s.areas.begin(), s.areas.end(), [&](const auto& area) { return area.handle == prior.handle && area.workspace == prior.workspace; }),
                    "Open/Load preserve existing peer area identities");
        const auto loaded = std::find_if(s.areas.begin(), s.areas.end(), [&](const auto& a) {
            return a.workspace == s.desk.current_handle && fs::path(a.path) == data / "dbf/button load/STUDENTS.dbf";
        });
        require(loaded != s.areas.end(), "Schema table is open in chosen workspace");
        require(s.desk.current_engine_area == loaded->slot, "Saved CURRENT key maps to the allocated zero-based area");
        const auto readback = session.inspect_field(loaded->slot, loaded->handle, 1, 1, "NAME").get();
        require(readback.error.empty() && readback.text == "Ada", "Load button reads actual schema table data");
        button.path = data / "workspaces/missing.dtschema";
        auto refused_load = session.submit(button).get();
        require(!refused_load.ok() && refused_load.areas.size() == loaded_count, "Missing schema leaves live tables intact");
        button.path = data / "workspaces/incomplete.dtschema";
        std::ofstream(button.path) << "DTSHEMA 3\nDBFROOT " << (data / "dbf/peer").string()
            << "\nAREA 1 | dbf=MISSING.dbf | index=none | alias=\n";
        s = session.submit(button).get();
        require(!s.ok() && s.command_opened_tables == 0 && s.areas.size() == loaded_count && s.error.find("missing") != std::string::npos,
                "Native incomplete-posture refusal is visible without changing tables");
        require(bytes(schema_file) == schema_bytes, "Schema file bytes unchanged by button loading");
        const auto before_modal = s;
        Request modal; modal.action = Action::OpenWorkspace;
        modal.expected_workspace = s.desk.current_handle;
        modal.path = data / "dbf/system";
        s = run(modal);
        require(s.desk.current_handle == before_modal.desk.current_handle && slot(s, "DBF") == slot(before_modal, "DBF"),
                "Modal directory open keeps explicit target and restores native DBF default");
        require(std::any_of(s.areas.begin(), s.areas.end(), [&](const auto& a) {
            return fs::path(a.path) == modal.path / "STUDENTS.dbf";
        }), "Modal directory containing spaces reaches native OPEN through DBF slot");
        const auto before_stale = s;
        modal.expected_workspace = 999999;
        for (const auto action : {Action::OpenWorkspace, Action::LoadWorkspace, Action::SaveImage, Action::NewWorkspace, Action::RunScript}) {
            modal.action = action; modal.name = "M1_WRONG_TARGET";
            const auto refused = session.submit(modal).get();
            require(!refused.ok() && refused.error.find("Workspace changed") != std::string::npos &&
                    refused.desk.current_handle == before_stale.desk.current_handle &&
                    refused.areas.size() == before_stale.areas.size() && refused.desk.workspace_count == before_stale.desk.workspace_count &&
                    slot(refused, "DBF") == slot(before_stale, "DBF"), "Stale modal target refuses before mutation");
        }
        modal = {}; modal.action = Action::NewWorkspace; modal.name = "M1_CHILD"; modal.workspace = 999999;
        const auto bad_parent = session.submit(modal).get();
        require(!bad_parent.ok() && bad_parent.desk.workspace_count == before_stale.desk.workspace_count, "Stale parent refuses before birth");
        modal.workspace = s.desk.current_handle; s = run(modal);
        require(s.desk.current_handle != before_stale.desk.current_handle && s.areas.size() == before_stale.areas.size(), "Modal child creation enters empty child");
        const auto duplicate = session.submit(modal).get();
        require(!duplicate.ok() && duplicate.desk.workspace_count == s.desk.workspace_count && duplicate.desk.current_handle == s.desk.current_handle,
                "Duplicate submit cannot create a second workspace");
        {
            const auto before = s;
            const auto bad = session.check_workspace(legacy_file, data / "workspaces").get();
            require(!bad.ready() && bad.version == 2 && bad.declared == 1 && bad.missing.size() == 1,
                    "V2 preflight reports exact missing member with wrong table directory");
            const auto untouched = session.submit().get();
            require(untouched.areas.size() == before.areas.size() && untouched.desk.current_engine_area == before.desk.current_engine_area &&
                    slot(untouched, "DBF") == slot(before, "DBF"), "Preflight never mutates area or path state");
            const auto good = session.check_workspace(legacy_file, data / "dbf/button load").get();
            require(good.ready() && good.declared == 1, "V2 preflight accepts explicit table directory");
            Request legacy; legacy.action = Action::LoadWorkspace; legacy.path = legacy_file;
            legacy.table_root = data / "dbf/button load"; legacy.index_root = data / "indexes";
            s = run(legacy);
            require(s.areas.size() == before.areas.size() + 1 && slot(s, "DBF") == slot(before, "DBF") &&
                    slot(s, "INDEXES") == slot(before, "INDEXES"), "Explicit V2 load restores both native defaults");
            const auto loaded = std::find_if(s.areas.begin(), s.areas.end(), [](const auto& area) { return area.name == "LEGACY_FOLDER"; });
            require(loaded != s.areas.end() && fs::path(loaded->path) == data / "dbf/button load/STUDENTS.dbf", "V2 opened exact selected family");
            const auto value = session.inspect_field(loaded->slot, loaded->handle, 1, 1, "NAME").get();
            require(value.error.empty() && value.text == "Ada", "V2 exact table readback");
            legacy.table_root = data / "workspaces";
            const auto refused = session.submit(legacy).get();
            require(!refused.ok() && refused.areas.size() == s.areas.size() && slot(refused, "DBF") == slot(s, "DBF"),
                    "Worker rechecks missing members without changing defaults or open areas");
        }
        {
            struct RestoreCwd { fs::path prior{fs::current_path()}; ~RestoreCwd() { fs::current_path(prior); } } restore;
            fs::current_path(data / "cwd");
            fs::copy_file(schema_file, data / "cwd/OnlyElsewhere.dtschema");
            const auto before = s.areas.size();
            s = command("WORKSPACE LOAD OnlyElsewhere.dtschema");
            require(s.areas.size() == before && s.transcript.find("cannot read file") != std::string::npos &&
                    s.transcript.find(fs::weakly_canonical(data / "workspaces/OnlyElsewhere.dtschema").string()) != std::string::npos,
                    "Workspace missing file never substitutes cwd duplicate: " + s.transcript);
            fs::copy_file(schema_file, data / "workspaces/Named.dtschemas");
            s = command("WORKSPACE LOAD Named");
            require(s.areas.size() == before + 1, "Legacy plural extension stays in WORKSPACES");
            const auto added = std::find_if(s.areas.begin(), s.areas.end(), [&](const auto& a) { return a.workspace == s.desk.current_handle; });
            require(added != s.areas.end(), "Named workspace has a real table");
            const auto field = session.inspect_field(added->slot, added->handle, 1, 1, "NAME").get();
            require(field.error.empty() && field.text == "Ada", "Named schema loaded actual table data");
            s = command("WORKSPACE LOAD workspaces/Named.dtschemas");
            require(s.transcript.find("cannot read file") == std::string::npos, "Qualified workspace path resolves under DATA");
        }
        // Saved versions with reused names must load the selected bytes, not
        // whatever the live catalog currently resolves for that name.
        const auto flow_dir = data / "catalogflow";
        fs::create_directory(flow_dir);
        const auto flow_catalog = flow_dir / "WORKSPACES.dbf";
        const auto old_definition = std::string("DTSHEMA 2\nAREA 0 | dbf=STUDENTS.dbf | index=none | alias=HISTORICAL\nCURRENT 0\n");
        const auto new_definition = std::string("DTSHEMA 3\nDBFROOT ") + (data / "dbf/button load").string() +
            "\nAREA 0 | dbf=STUDENTS.dbf | index=none | alias=CURRENT_VERSION\nCURRENT 0\n";
        const auto old_image = "MINIDB 1\nPOSTURE " + std::to_string(old_definition.size()) + "\n" + old_definition +
            "FILE " + std::to_string(original.size()) + " STUDENTS.dbf\n" + original + "END\n";
        require(xbase::dbf_create::create_dbf(flow_catalog.string(), {{"WS_ID", 'N', 10}, {"WS_NAME", 'C', 32},
            {"FMT", 'C', 12}, {"SNAPSHOT", 'M', 16}, {"SUPERSEDED", 'C', 1}}, xbase::dbf_create::Flavor::X64, error), error);
        {
            dottalk::memo::MemoStore memo;
            require(memo.open((flow_dir / "WORKSPACES.dtx").string(), dottalk::memo::OpenMode::CreateIfMissing).ok, "Flow catalog memo");
            xbase::DbArea catalog; catalog.open(flow_catalog.string());
            auto add = [&](int id, const char* name, const char* format, const std::string& payload, bool historical) {
                const auto put = memo.put_text(payload); require(put.ok, put.error);
                require(catalog.appendBlank() && catalog.set(1, std::to_string(id)) && catalog.set(2, name) &&
                    catalog.set(3, format) && catalog.set(4, put.ref.token) && catalog.set(5, historical ? "1" : "0") && catalog.writeCurrent(), "Flow catalog row");
            };
            add(11, "Repeated", "DTSHEMA 2", old_definition, true);
            add(12, "Repeated", "DTSHEMA 3", new_definition, false);
            add(21, "RepeatedImage", "MINIDB 1", old_image, true);
            add(22, "RepeatedImage", "MINIDB 1", "MINIDB 1\nPOSTURE " + std::to_string(new_definition.size()) + "\n" + new_definition +
                "FILE " + std::to_string(original.size()) + " STUDENTS.dbf\n" + original + "END\n", false);
            add(31, "BirthOnly", "BIRTH 1", "BIRTH 1\n", false);
            add(32, "Broken", "MINIDB 1", "MINIDB 1\nPOSTURE 100\nshort", false);
        }
        const auto flow_dbf = bytes(flow_catalog), flow_dtx = bytes(flow_dir / "WORKSPACES.dtx");
        const auto saved = session.inspect(flow_catalog).get(); require(saved.ok() && saved.entries.size() == 6, saved.error);
        require(saved.entries[0].action() == CatalogAction::LoadDefinition && saved.entries[2].action() == CatalogAction::Hydrate &&
            saved.entries[4].action() == CatalogAction::None && saved.entries[5].action() == CatalogAction::None,
            "Catalog actions follow actual payload and refuse birth/corrupt rows");
        command("WORKSPACE NEW ExactCatalog");
        Request exact; exact.action = Action::LoadWorkspace; exact.payload = saved.entries[0].payload;
        exact.provenance = "catalogflow / saved ID 11 / Repeated (historical version)";
        exact.table_root = data / "dbf/button load"; exact.index_root = data / "indexes";
        const auto preflight = session.check_workspace({}, exact.table_root, exact.payload).get();
        require(preflight.ready() && preflight.declared == 1, "Exact payload preflight");
        s = run(exact);
        auto last_table = [&] { for (const auto& area : s.areas) if (area.workspace == s.desk.current_handle) return area;
            throw std::runtime_error("Exact catalog target missing"); };
        auto selected = last_table();
        require(selected.name == "HISTORICAL" && !selected.ram &&
            session.inspect_field(selected.slot, selected.handle, 1, 1, "NAME").get().text == "Ada", "Historical definition exact alias and Ada readback");
        exact.expected_workspace = s.desk.current_handle + 999;
        const auto stale = session.submit(exact).get();
        require(!stale.ok() && stale.areas.size() == s.areas.size(), "Stale catalog destination refuses");
        exact.expected_workspace = s.desk.current_handle;
        exact.table_root = flow_dir;
        const auto missing = session.submit(exact).get();
        require(!missing.ok() && missing.areas.size() == s.areas.size(), "Missing catalog member refuses without closing areas");
        exact.table_root = data / "dbf/button load";
        exact.payload = saved.entries[4].payload;
        require(!session.submit(exact).get().ok(), "Birth payload cannot bypass disabled control");
        exact.payload = saved.entries[0].payload;
        Request select; select.action = Action::SelectArea; select.slot = selected.slot; select.area_handle = selected.handle; run(select);
        command("TABLE ON"); command("REPLACE NAME WITH 'Buffered'");
        const auto dirty = session.submit(exact).get();
        require(!dirty.ok() && dirty.dirty_areas == 1 && session.inspect_field(selected.slot, selected.handle, 1, 1, "NAME").get().text == "Buffered",
            "Load refusal preserves buffered field value");
        Request hydrate; hydrate.action = Action::Hydrate; hydrate.name = "ExactRam"; hydrate.payload = saved.entries[2].payload;
        hydrate.provenance = "catalogflow / saved ID 21 / RepeatedImage (historical version)";
        require(!session.submit(hydrate).get().ok(), "Hydration refuses buffered edits before creating a workspace");
        command("ROLLBACK"); command("TABLE OFF");
        const auto parent = s.desk.current_handle;
        hydrate.workspace = parent + 999;
        require(!session.submit(hydrate).get().ok(), "Hydration rechecks missing parent");
        hydrate.workspace = parent; s = run(hydrate); selected = last_table();
        require(selected.ram && selected.name == "HISTORICAL" && s.desk.current_engine_area == selected.slot &&
            s.images.back().provenance == hydrate.provenance &&
            session.inspect_field(selected.slot, selected.handle, 1, 1, "NAME").get().text == "Ada", "Exact historical RAM table, selection, provenance and Ada readback");
        bool child = false; for (const auto& ws : s.desk.workspaces) if (ws.handle == s.desk.current_handle) child = ws.parent == parent;
        require(child, "Hydration creates under selected current parent");
        require(bytes(flow_catalog) == flow_dbf && bytes(flow_dir / "WORKSPACES.dtx") == flow_dtx, "Selected catalog preserved byte for byte");
        command("WORKSPACE CLOSE ALL"); command("VDISK UNMOUNT"); session.shutdown();
        require(bytes(source) == original && bytes(data / "dbf/lesson space/STUDENTS.dbf") == original, "Opening table fixtures did not change bytes");
        for (const auto* ext : {".dbf", ".dtx"}) fs::copy_file(data / (std::string("workspaces/WORKSPACES") + ext),
            data / (std::string("alternate workspaces/WORKSPACES") + ext));
        std::cout << "PASS paths: installation discovery, native INIT order, default catalog, SET PATH spaces, OPEN dbf, bare names, SWITCH, RESET, IN, refusals, configured-catalog image import\n"
                  << "PASS command load: DO x64 / WORKSPACE OPEN dbf, MINIDB command and script notifications, actual RAM table readback, no stale or refused-load events\n"
                  << "PASS Open/Load buttons: native OPEN dbf, schema path spaces/ampersand, current workspace and peers retained, Ada readback, missing/incomplete schema refusal\n"
                  << "PASS M1 modal targets: explicit directory with spaces, native default restored, stale target/parent refusal, child activation, duplicate refusal\n"
                  << "PASS file locations: duplicate names, missing-file refusal, SCRIPTS overrides, DATA-qualified paths, caller-relative subscripts, exact modal paths, OUT transcript, workspace file roots and actual Ada readback\n"
                  << "PASS schema locations: V2 chosen roots, no-mutation preflight, missing-member refusal, V3 saved-root priority, per-load default restoration and exact Ada readback\n"
                  << "PASS catalog flow: historical exact bytes, duplicate names, V2 roots, Ada disk/RAM readback, active selection, child parent, stale/missing/birth/buffer refusal, unchanged catalog\n"
                  << "catalog_flow=" << flow_catalog.string() << '\n'
                  << "data_root=" << data.string() << '\n' << "session_home=" << home.string() << '\n';
    } catch (const std::exception& e) { std::cerr << "FAIL paths: " << e.what() << '\n'; return 1; }
}
