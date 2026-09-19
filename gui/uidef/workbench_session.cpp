// @dottalk.file v1
// subsystem: gui
// layer: service
// owns: single engine worker and private session data
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_session.hpp"
#include "xbase.hpp"
#include "xbase/workspace_membership.hpp"
#include "common/path_state.hpp"
#include "shortcut_resolver.hpp"
#include "cli/output_router.hpp"
#include "workarea_util.hpp"
#include "workareas.hpp"
#include "xbase/fields.hpp"
#include "xbase/ramfs.hpp"
#include "memo/memostore.hpp"
#include "dottalk/minidb_hydrate.hpp"
#include "shell_api.hpp"
#include "shell_commands.hpp"
#include "shell_bool_eval_adapter.hpp"
#include "cmd_loop.hpp"
#include "set_relations.hpp"
#include "cli/fn_autoreg.hpp"
#include "cli/command_registry.hpp"
#include "cli/shell_exit_request.hpp"
#include "cli/table_state.hpp"
#include "cli/table_object.hpp"
#include "cli/workspace_image_event.hpp"
#include "sqlsel_statement.hpp"
#include <set>
#include <atomic>
#include <condition_variable>
#include <deque>
#include <functional>
#include <fstream>
#include <cctype>
#include <iostream>
#include <mutex>
#include <sstream>
#include <thread>

void cmd_WORKSPACE(xbase::DbArea&, std::istringstream&);
void cmd_SELECT(xbase::DbArea&, std::istringstream&);
void cmd_LIST(xbase::DbArea&, std::istringstream&);
void cmd_VDISK(xbase::DbArea&, std::istringstream&);
void cmd_SETPATH(xbase::DbArea&, std::istringstream&);
void cmd_DOTSCRIPT(xbase::DbArea&, std::istringstream&);
void cmd_INIT_from(xbase::DbArea&, std::istringstream&, const std::filesystem::path&, const std::string&);
namespace {
xbase::XBaseEngine* engine = nullptr;
std::atomic_bool session_active{false};
// OutputRouter retains its console streambuf. Give it a process-lifetime sink,
// not a per-request ostringstream whose address would dangle after completion.
class CapturedOutput : public std::ostream {
    struct Buffer : std::streambuf {
        static constexpr std::size_t limit = 4 * 1024 * 1024;
        std::string bytes;
        bool truncated{};
        std::streamsize xsputn(const char* s, std::streamsize n) override {
            const auto kept = std::min(static_cast<std::size_t>(n), limit - bytes.size());
            bytes.append(s, kept); truncated |= kept < static_cast<std::size_t>(n);
            return n;
        }
        int_type overflow(int_type ch) override {
            if (!traits_type::eq_int_type(ch, traits_type::eof())) {
                const char c = traits_type::to_char_type(ch); xsputn(&c, 1);
            }
            return traits_type::not_eof(ch);
        }
    } buffer_;
public:
    CapturedOutput() : std::ostream(nullptr) { rdbuf(&buffer_); }
    void reset() { buffer_.bytes.clear(); buffer_.truncated = false; clear(); }
    std::string str() const {
        return buffer_.bytes + (buffer_.truncated ? "\n[Workbench output limited to 4 MiB; narrow the query or use SET ALTERNATE.]\n" : "");
    }
};
CapturedOutput host_output;
std::istringstream host_input;
}
namespace dottalk::workbench {
namespace fs = std::filesystem;
struct WorkbenchSession::Impl {
    std::mutex mutex;
    std::condition_variable wake;
    std::deque<std::function<void()>> queue;
    bool stopping{};
    std::thread worker;
    fs::path home;
    SessionOptions options;
    unsigned copies{};
    unsigned image_sequence{};
    unsigned save_sequence{};
    std::vector<ResidentImage> images;
    std::string startup_error;
    std::string command_refusal;
    bool browse_active{}, browse_requested{};
    std::uint64_t browse_offset{}, browse_handle{};
    dli::Handler previous_browse, previous_init;
    std::string startup_transcript;
    cli::WorkspaceImageObserver previous_image_observer;
    bool observe_command_images{};
    std::vector<cli::WorkspaceImageEvent> command_images;
    static unsigned dirty_areas() {
        unsigned count = 0;
        if (engine) for (int slot = 0; slot < xbase::MAX_AREA; ++slot)
            if (engine->area(slot).isOpen() && dottalk::table::is_enabled(slot) && dottalk::table::is_dirty(slot)) ++count;
        return count;
    }
    explicit Impl(SessionOptions initial) : options(std::move(initial)) {
        if (session_active.exchange(true)) throw std::runtime_error("Only one Workbench session is supported per process");
        try { worker = std::thread([this] { run(); }); }
        catch (...) { session_active = false; throw; }
    }
    ~Impl() { stop(); session_active = false; }
    void stop() {
        { std::lock_guard lock(mutex); stopping = true; }
        wake.notify_all();
        if (worker.joinable()) worker.join();
    }
    template<class T, class F> std::future<T> enqueue(F fn) {
        auto task = std::make_shared<std::packaged_task<T()>>(std::move(fn));
        auto future = task->get_future();
        { std::lock_guard lock(mutex);
          if (stopping) throw std::runtime_error("Workbench session is closed");
          queue.emplace_back([task] { (*task)(); }); }
        wake.notify_one(); return future;
    }
    void run() {
        // Construct and destroy the engine on its sole owning thread.
        std::unique_ptr<xbase::XBaseEngine> owned;
        const auto previous_paths = dottalk::paths::state();
        auto* previous_output = std::cout.rdbuf(host_output.rdbuf());
        auto* previous_errors = std::cerr.rdbuf(host_output.rdbuf());
        auto* previous_input = std::cin.rdbuf(host_input.rdbuf());
        cli::OutputRouter::instance().set_wrap(false);
        try {
            home = fs::temp_directory_path() / ("arctictalk-session-" +
                std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
            if (!fs::create_directory(home)) throw std::runtime_error("Session directory collision");
            for (const auto* dir : {"dbf", "workspaces", "indexes", "lmdb", "ram", "sys", "tmp", "bin"})
                fs::create_directory(home / dir);
            using dottalk::paths::Slot;
            dottalk::paths::reset();
            for (const auto [slot, dir] : std::initializer_list<std::pair<Slot, const char*>>{
                {Slot::DATA,""}, {Slot::DBF,"dbf"}, {Slot::WORKSPACES,"workspaces"},
                {Slot::INDEXES,"indexes"}, {Slot::LMDB,"lmdb"}, {Slot::RAM,"ram"},
                {Slot::SYS,"sys"}, {Slot::TMP,"tmp"}, {Slot::BIN,"bin"}})
                dottalk::paths::set_slot(slot, home / dir);
            std::ofstream config(home / "bin/vdisk.ini");
            config << "[vdisk]\nenabled=1\nmode=fixed\nsize_mb=128\nfloor_mb=1\nceil_mb=128\non_full=fail\n";
            config.close();
            if (!config) throw std::runtime_error("Cannot create private RAM budget configuration");
            if (!options.private_session) {
                if (options.data_root.empty() || !fs::is_directory(options.data_root))
                    throw std::runtime_error("Cannot find x64base data. Start with --data-root <directory>.");
                const auto data = fs::absolute(options.data_root).lexically_normal();
                dottalk::paths::initialize(data.parent_path() / "bin", data);
            }
            xbase::workspace::default_table() = xbase::workspace::WorkspaceTable{};
            owned = std::make_unique<xbase::XBaseEngine>(); engine = owned.get();
            engine->selectArea(0);
            cli::workspace_roots_bind_from_slots(xbase::workspace::current_handle());
            shell_bind_engine(engine);
            // This host can replace its engine in one process. The compatibility
            // cache keys on an engine address, which an allocator may reuse even
            // though all DbArea objects changed. Rebuild for every new session.
            workareas::global() = workareas::WorkAreaSet{};
            xbase::clear_shell_exit_request();
            relations_api::attach_engine(engine);
            relations_api::set_autorefresh(true);
            register_shell_commands(*engine, false);
            previous_image_observer = cli::set_workspace_image_observer([this](const cli::WorkspaceImageEvent& event) {
                if (observe_command_images) command_images.push_back(event);
            });
            previous_init = dli::registry().map().at("INIT");
            dli::registry().add_builtin("INIT", [](xbase::DbArea& area, std::istringstream& input) {
                cmd_INIT_from(area, input, dottalk::paths::get_slot(dottalk::paths::Slot::BIN), "dottalkpp");
            });
            previous_browse = dli::registry().map().at("BROWSE");
            dli::registry().add_builtin("BROWSE", [this](xbase::DbArea& area, std::istringstream& input) {
                std::string args; std::getline(input, args);
                const auto first = args.find_first_not_of(" \t\r\n");
                args = first == std::string::npos ? "" : args.substr(first, args.find_last_not_of(" \t\r\n") - first + 1);
                for (auto& c : args) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
                if (args == "USAGE" || args == "HELP" || args == "?") {
                    std::cout << "BROWSE opens the selected table in the Workbench. Inspect values read-only; edit with commands.\n"; return;
                }
                if (!args.empty()) { command_refusal = "Workbench BROWSE takes no arguments; edit through the command console."; throw std::runtime_error(command_refusal); }
                if (!area.isOpen()) { command_refusal = "No table open. Use SELECT or open a table first."; throw std::runtime_error(command_refusal); }
                browse_active = browse_requested = true; browse_offset = 0;
            }, "gui/uidef/workbench_session.cpp");
            dottalk::ensure_builtin_commands_registered();
            shell_eval_register_for_loops();
            loop_set_executor(+[](xbase::DbArea& area, const std::string& line) { (void)shell_execute_line(area, line); });
            dli::registry().set_execution_guard([this](const std::string& key, const std::string& raw) {
                static const std::set<std::string> terminal{
                    "SIMPLEBROWSER", "RBROWSE", "ERSATZ", "BROWSER", "BROWSETUI",
                    "SMARTBROWSER", "GUI", "APPGUI", "TVISION", "FOXPRO", "ARCTICTALK", "FOXTALK",
                    "GENERIC", "BROWSETV", "RECORD", "RECORDVIEW", "!", "CLEAR"};
                std::istringstream words(raw); std::string sub; words >> sub;
                for (auto& c : sub) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
                if (terminal.count(key) || (key == "BBS" && sub == "SERVE"))
                    command_refusal = key + " requires the terminal or a separate application; run it from the x64base prompt.";
                else if ((key == "QUIT" || key == "EXIT" || key == "SHUTDOWN") && dirty_areas())
                    command_refusal = "Commit or roll back buffered table edits before closing the session.";
                else if ((key == "APPEND" || key == "APPEND_BLANK" || key == "RECALL" || key == "UNDELETE") &&
                    dottalk::table::is_enabled(engine->currentArea()) && sub != "USAGE" && sub != "HELP" && sub != "?")
                    command_refusal = key + " has no native buffered implementation. TABLE ON prevents this write. Finish edits and explicitly use TABLE OFF first.";
                else return std::string{};
                return command_refusal;
            });
            if (!options.private_session) {
                host_output.reset();
                (void)shell_execute_line(engine->area(engine->currentArea()), "INIT");
                startup_transcript = host_output.str();
            }
        } catch (const std::exception& e) { startup_error = e.what(); }
        for (;;) {
            std::function<void()> task;
            { std::unique_lock lock(mutex);
              wake.wait(lock, [this] { return stopping || !queue.empty(); });
              if (queue.empty()) break;
              task = std::move(queue.front()); queue.pop_front(); }
            task();
        }
        if (engine) {
            // Reuse the command's memo, relation and membership teardown before
            // DbAreas disappear; worker shutdown must not leave dangling maps.
            try {
                std::istringstream close("CLOSE ALL");
                cmd_WORKSPACE(engine->area(engine->currentArea()), close);
            } catch (...) {}
        }
        dli::registry().set_execution_guard({});
        cli::set_workspace_image_observer(std::move(previous_image_observer));
        if (previous_init) dli::registry().add_builtin("INIT", std::move(previous_init));
        if (previous_browse) dli::registry().add_builtin("BROWSE", std::move(previous_browse));
        loop_set_executor(nullptr);
        relations_api::attach_engine(nullptr);
        shell_bind_engine(nullptr);
        workareas::global() = workareas::WorkAreaSet{};
        owned.reset(); engine = nullptr;
        for (const auto& image : images) release_mount(image.root);
        xbase::workspace::default_table() = xbase::workspace::WorkspaceTable{};
        dottalk::paths::state() = previous_paths;
        std::cout.rdbuf(previous_output);
        std::cerr.rdbuf(previous_errors);
        std::cin.rdbuf(previous_input); std::cin.clear();
        // Private data stays at the reported path for review. This service does
        // not recursively delete a directory in a shared development machine.
    }
    static void release_mount(const fs::path& root) {
        for (const auto& file : xbase::ramfs::list(root.string())) xbase::ramfs::erase(file);
        xbase::ramfs::unmount(root.string());
    }
    static void validate_name(const std::string& name) {
        if (name.empty() || name.size() > 32 || !std::isalpha(static_cast<unsigned char>(name.front())) ||
            name.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_") != std::string::npos)
            throw std::runtime_error("Use a workspace name starting with a letter, then letters, digits or underscore (up to 32).");
        if (xbase::workspace::find_by_name_ci(name)) throw std::runtime_error("Workspace name already exists");
    }
    void attach_image(const Request& request, std::uint64_t handle) {
        // NEW allocated the canonical birth identity in the active catalog. Attach bytes only
        // to that identity, never copy foreign catalog IDs into the live desk.
        memo::MemoStore store;
        const auto catalog_root = dottalk::paths::get_slot(dottalk::paths::Slot::WORKSPACES);
        auto opened = store.open((catalog_root / "WORKSPACES.dtx").string(), memo::OpenMode::CreateIfMissing);
        if (!opened.ok) throw std::runtime_error(opened.error);
        const auto put = store.put_text(request.payload);
        if (!put.ok) throw std::runtime_error(put.error);
        const auto readback = store.get_text(put.ref);
        if (!readback.ok || readback.text != request.payload) throw std::runtime_error("Image memo readback failed");
        store.close();
        xbase::DbArea catalog; catalog.open((catalog_root / "WORKSPACES.dbf").string());
        auto field = [&](const char* name) {
            const auto n = fields::findFieldCI(catalog, name);
            if (n < 0) throw std::runtime_error(std::string("Workspace catalog missing ") + name);
            return n + 1;
        };
        const auto id_field = field("WS_ID");
        for (std::uint64_t n = 1; n <= catalog.recCount64(); ++n) {
            catalog.gotoRec(static_cast<int32_t>(n)); catalog.readCurrent();
            if (minidb::detail::trim_ascii(catalog.get(id_field)) != std::to_string(xbase::workspace::ws_id_of(handle))) continue;
            if (!catalog.set(field("SNAPSHOT"), put.ref.token) || !catalog.set(field("FMT"), "MINIDB 1") ||
                !catalog.set(field("SIZE_B"), std::to_string(request.payload.size())) || !catalog.writeCurrent())
                throw std::runtime_error("Cannot attach image to workspace identity");
            catalog.readCurrent();
            if (minidb::detail::trim_ascii(catalog.get(field("SNAPSHOT"))) != put.ref.token)
                throw std::runtime_error("Private catalog token readback failed");
            return;
        }
        throw std::runtime_error("Workspace birth identity missing");
    }
    fs::path stage_definition(const std::string& payload) {
        if (!is_workspace_definition(payload)) throw std::runtime_error("Choose a saved DTSHEMA 2 or DTSHEMA 3 definition.");
        // Exact selected bytes, never a second lookup by a possibly reused name.
        const auto file = home / ("catalog-definition-" + std::to_string(++image_sequence) + ".dtschema");
        if (fs::exists(file)) throw std::runtime_error("Private definition filename already exists.");
        std::ofstream out(file, std::ios::binary); out.write(payload.data(), payload.size()); out.close();
        if (!out) throw std::runtime_error("Cannot stage the selected definition.");
        return file;
    }
    void require_load_ready() {
        if (sqlsel::transaction_active()) throw std::runtime_error("End the active SQL transaction before loading.");
        for (int slot = 0; slot < xbase::MAX_AREA; ++slot)
            if (engine->area(slot).isOpen() && (dottalk::table::is_dirty(slot) || !dottalk::table::get_tb_const(slot).empty()))
                throw std::runtime_error("Commit or roll back buffered table edits before loading.");
    }
    SessionSnapshot perform(const Request& request) {
        SessionSnapshot result; result.home = home;
        command_images.clear();
        const bool observe_load = request.action == Action::Command || request.action == Action::RunScript || request.action == Action::OpenWorkspace || request.action == Action::LoadWorkspace;
        observe_command_images = observe_load;
        std::set<std::uint64_t> previous_areas;
        if (observe_command_images && engine)
            for (int slot = 0; slot < xbase::MAX_AREA; ++slot)
                if (engine->area(slot).isOpen()) previous_areas.insert(engine->area(slot).areaHandle());
        host_output.reset();
        if (!startup_transcript.empty()) { host_output << startup_transcript; startup_transcript.clear(); }
        host_input.str({}); host_input.clear(); std::cin.clear();
        command_refusal.clear();
        browse_requested = false;
        auto& output = host_output;
        auto command = [&](const std::string& args) {
            std::istringstream input(args);
            cmd_WORKSPACE(engine->area(engine->currentArea()), input);
        };
        try {
            if (!startup_error.empty()) throw std::runtime_error(startup_error);
            if (!engine) throw std::runtime_error("Engine unavailable");
            if (request.expected_workspace && request.expected_workspace != xbase::workspace::current_handle())
                throw std::runtime_error("Workspace changed while the form was open. Reopen the form for the intended workspace.");
            switch (request.action) {
            case Action::Observe: break;
            case Action::StoreImage: {
                const auto target = read_memo_target(*engine, request.edit);
                if (!target.error.empty()) throw std::runtime_error(target.error);
                if (target.edit.expected_value != request.edit.expected_value)
                    throw std::runtime_error("The memo reference changed; select the field again.");
                const auto payload = read_image_file(request.path);
                const auto error = stage_memo_image(*engine, request.edit, payload);
                if (!error.empty()) throw std::runtime_error(error);
                output << "Image reference buffered: " << target.title << '\n'
                       << payload.size() << " bytes verified from " << request.path.string() << '\n'
                       << "Commit table saves it; Rollback table keeps the previous image.\n";
                browse_active = browse_requested = true; break;
            }
            case Action::ExportImage: {
                result.exported_image = export_image(request.payload, request.path, home);
                output << "Exported image verified: " << result.exported_image.string() << '\n'
                       << request.payload.size() << " bytes copied exactly from " << request.provenance << '\n';
                break;
            }
            case Action::SaveImage: {
                if (request.workspace != xbase::workspace::current_handle())
                    throw std::runtime_error("Workspace selection is stale; refresh before saving.");
                if (request.path.empty()) throw std::runtime_error("Choose a new image file.");
                const auto destination = fs::absolute(request.path);
                if (fs::exists(destination)) throw std::runtime_error("That file already exists. Choose a new image filename.");
                if (sqlsel::transaction_active()) throw std::runtime_error("End the active SQL transaction before saving an image.");
                struct RecursionRestore {
                    bool previous{xbase::workspace::recursion_enabled()};
                    ~RecursionRestore() { xbase::workspace::set_recursion_enabled(previous); }
                } recursion_restore;
                if (request.include_nested) xbase::workspace::set_recursion_enabled(*request.include_nested);
                std::set<std::uint64_t> scope;
                std::function<void(std::uint64_t)> collect = [&](std::uint64_t ws) {
                    if (!scope.insert(ws).second) return;
                    if (xbase::workspace::recursion_enabled()) for (auto child : xbase::workspace::children(ws)) collect(child);
                };
                collect(request.workspace);
                unsigned tables = 0;
                for (const auto ws : scope) for (const auto slot : xbase::workspace::members(ws)) {
                    if (slot < 0 || slot >= xbase::MAX_AREA || !engine->area(slot).isOpen()) continue;
                    ++tables;
                    if (dottalk::table::is_dirty(slot) || !dottalk::table::get_tb_const(slot).empty())
                        throw std::runtime_error("Commit or roll back buffered edits in the workspace being saved.");
                }
                if (!tables) throw std::runtime_error("The workspace has no open tables to save.");
                // Always write the native snapshot to our private catalog,
                // even when the console has selected another WORKSPACES root.
                const auto previous_paths = dottalk::paths::state();
                const auto name = "WB_IMAGE_" + std::to_string(++save_sequence);
                dottalk::paths::set_slot(dottalk::paths::Slot::WORKSPACES, home / "workspaces");
                try { command("SAVE " + name + " MEMO MINIDB"); }
                catch (...) { dottalk::paths::state() = previous_paths; throw; }
                dottalk::paths::state() = previous_paths;
                const auto catalog = inspect_catalog(home / "workspaces/WORKSPACES.dbf");
                if (!catalog.ok()) throw std::runtime_error(catalog.error);
                const SavedWorkspace* saved = nullptr;
                for (const auto& entry : catalog.entries)
                    if (entry.value("WS_NAME") == name && !entry.superseded) saved = &entry;
                if (!saved || !saved->error.empty()) throw std::runtime_error("Image save failed; read Engine response.");
                const auto admission = admit_image(saved->payload, home / "save-check");
                if (!admission.ok() || admission.tables != tables)
                    throw std::runtime_error("Image verification failed: " + admission.error);
                result.saved_image = export_image(saved->payload, destination, home);
                output << "Saved image verified: " << destination.string() << "\n"
                       << tables << " table(s), " << saved->payload.size() << " bytes. Open image to inspect and restore.\n"
                       << "Nested workspace tables share the restored workspace; workspace ownership is not serialized.\n";
                break;
            }
            case Action::TableCommand: {
                auto& area = engine->area(engine->currentArea());
                if (!area.isOpen() || !request.area_handle || area.areaHandle() != request.area_handle || request.slot != engine->currentArea())
                    throw std::runtime_error("Table selection is stale; refresh the view.");
                const auto& op = request.name;
                if (request.payload.find_first_of("\r\n") != std::string::npos || request.payload.find('\0') != std::string::npos)
                    throw std::runtime_error("Enter one line for this operation.");
                const bool writes = op == "append" || op == "delete" || op == "recall";
                if (writes && sqlsel::transaction_active()) throw std::runtime_error("End the active SQL transaction first.");
                if ((op == "append" || op == "recall") && (dottalk::table::is_enabled(request.slot) ||
                    !dottalk::table::get_tb_const(request.slot).empty() || dottalk::table::is_dirty(request.slot)))
                    throw std::runtime_error("TABLE ON prevents this write. Native append/recall buffering is not implemented. Finish edits and explicitly use TABLE OFF first.");
                if (op == "delete" || op == "recall" || op == "go") {
                    if (!request.record || request.record > area.recCount64()) throw std::runtime_error("Record is no longer available.");
                }
                std::string command;
                if (op == "first") command = "GO TOP";
                else if (op == "last") command = "GO BOTTOM";
                else if (op == "back") command = "SKIP -1";
                else if (op == "forward") command = "SKIP 1";
                else if (op == "go") command = "GO " + std::to_string(request.record);
                else if (op == "filter") command = "SET FILTER TO " + request.payload;
                else if (op == "order") command = "SET ORDER " + (request.payload.empty() ? "NATURAL" : request.payload);
                else if (op == "seek") {
                    if (request.payload.empty()) throw std::runtime_error("Enter a key expression.");
                    if (request.payload.find_first_of(" \t") != std::string::npos)
                        throw std::runtime_error("Native SEEK does not preserve keys containing spaces. Use a filter for this value.");
                    command = "SEEK " + request.payload;
                } else if (op == "deleted") command = request.enabled ? "SET DELETED OFF" : "SET DELETED ON";
                else if (op == "append") command = "APPEND BLANK";
                else if (op == "delete" || op == "recall") command = op == "delete" ? "DELETE" : "RECALL";
                else throw std::runtime_error("Unknown table operation.");
                if (op == "delete") {
                    if (!dottalk::table::is_enabled(request.slot)) { std::istringstream on("ON"); cmd_TABLE_BUFFER(area, on); }
                    if (!dottalk::table::is_enabled(request.slot)) throw std::runtime_error("Could not enable the table buffer.");
                }
                if (op == "delete" || op == "recall") area.gotoRec64(request.record);
                const auto count = area.recCount64();
                output << "> " << command << '\n';
                (void)shell_execute_line(area, command);
                if (!command_refusal.empty()) throw std::runtime_error(command_refusal);
                if (op == "append" && area.recCount64() != count + 1) throw std::runtime_error("Append did not add one record; read Engine response.");
                if (op == "recall" && area.isDeleted()) throw std::runtime_error("Recall did not clear the deletion; read Engine response.");
                if (op == "delete" && !(dottalk::table::Table(*engine, request.slot).overlay_for(request.record).flags & dottalk::table::CHANGE_DELETE))
                    throw std::runtime_error("Delete was not buffered; read Engine response.");
                browse_active = browse_requested = true; browse_offset = 0; break;
            }
            case Action::SetNullField:
            case Action::EditField: {
                const auto error = request.action == Action::SetNullField ? set_field_null(*engine, request.edit) : stage_field_edit(*engine, request.edit);
                if (!error.empty()) throw std::runtime_error(error);
                output << "Field value verified: " << request.edit.field_name << " / record " << request.edit.record << '\n';
                browse_active = browse_requested = true; break;
            }
            case Action::CommitTable:
            case Action::RollbackTable: {
                auto& area = engine->area(engine->currentArea());
                if (!area.isOpen() || !request.area_handle || area.areaHandle() != request.area_handle || request.slot != engine->currentArea())
                    throw std::runtime_error("Table selection is stale; refresh the view.");
                if (sqlsel::transaction_active()) throw std::runtime_error("End the active SQL transaction through the command console.");
                std::istringstream args;
                const bool commit = request.action == Action::CommitTable;
                output << "> " << (commit ? "COMMIT" : "ROLLBACK") << " (selected table)\n";
                if (commit) cmd_COMMIT(area, args); else cmd_ROLLBACK(area, args);
                if (!dottalk::table::get_tb_const(request.slot).empty() || dottalk::table::is_dirty(request.slot))
                    throw std::runtime_error("The table still has buffered changes. Read Engine response for the result.");
                browse_active = browse_requested = true; break;
            }
            case Action::Browse:
                if (request.area_handle && request.area_handle != engine->area(engine->currentArea()).areaHandle())
                    throw std::runtime_error("Table selection is stale; refresh the view.");
                browse_active = browse_requested = true; browse_offset = request.offset; break;
            case Action::SelectRecord: {
                auto& area = engine->area(engine->currentArea());
                if (!area.isOpen() || !request.area_handle || request.area_handle != area.areaHandle() || request.slot != engine->currentArea())
                    throw std::runtime_error("Table selection is stale; refresh the view.");
                if (!request.record || request.record > area.recCount64()) throw std::runtime_error("Record is no longer available");
                (void)shell_execute_line(area, "GOTO " + std::to_string(request.record));
                browse_active = browse_requested = true; break;
            }
            case Action::Command: {
                output << "> " << request.name << '\n';
                (void)shell_execute_line(engine->area(engine->currentArea()), request.name);
                if (!command_refusal.empty()) throw std::runtime_error(command_refusal);
                break;
            }
            case Action::RunScript: {
                const auto path = request.path.lexically_normal();
                auto ext = path.extension().string();
                for (auto& c : ext) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
                const auto text = path.string();
                if (!path.is_absolute() || !fs::is_regular_file(path) || ext != ".dts" ||
                    text.find_first_of("\r\n\"") != std::string::npos || text.find('\0') != std::string::npos)
                    throw std::runtime_error("Choose an existing .dts script by its full path.");
                // A picker supplies a filename, not shell text. Invoke the same
                // native runner as DO, without expanding macros in the path.
                output << "> DO \"" << text << "\"\n";
                std::istringstream input("\"" + text + "\"");
                cmd_DOTSCRIPT(engine->area(engine->currentArea()), input);
                if (!command_refusal.empty()) throw std::runtime_error(command_refusal);
                break;
            }
            case Action::OpenWorkspace: {
                // Native OPEN tokenizes on whitespace (not quotes). Feed its
                // DBF slot directly so a picker path is never parsed as options.
                const auto previous_paths = dottalk::paths::state();
                if (!request.path.empty()) {
                    const auto path = fs::absolute(request.path).lexically_normal();
                    if (!fs::is_directory(path)) throw std::runtime_error("Choose an existing table directory.");
                    dottalk::paths::set_slot(dottalk::paths::Slot::DBF, path);
                    output << "Table directory: " << path.string() << '\n';
                }
                output << "> WORKSPACE OPEN dbf\n";
                try { command("OPEN dbf"); }
                catch (...) { dottalk::paths::state() = previous_paths; throw; }
                dottalk::paths::state() = previous_paths;
                break;
            }
            case Action::LoadWorkspace: {
                require_load_ready();
                const bool saved = !request.payload.empty();
                const auto path = saved ? stage_definition(request.payload) : fs::absolute(request.path).lexically_normal();
                auto ext = path.extension().string();
                for (auto& c : ext) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
                if ((!saved && request.path.empty()) || !fs::is_regular_file(path) || (ext != ".dtschema" && ext != ".dtschemas"))
                    throw std::runtime_error("Choose an existing .dtschema or .dtschemas workspace file.");
                for (const auto& root : {request.table_root, request.index_root})
                    if (!root.empty() && !root.is_absolute()) throw std::runtime_error("Choose a full table/index directory path.");
                const auto check = cli::check_workspace_definition(path, request.table_root);
                if (!check.error.empty()) throw std::runtime_error(check.error);
                if (!check.missing.empty()) throw std::runtime_error("Cannot load " + std::to_string(check.declared) +
                    " tables: " + std::to_string(check.missing.size()) + " missing. First: " + check.missing.front() +
                    ". Choose the table directory in Load.");
                struct RestorePaths {
                    dottalk::paths::State saved{dottalk::paths::state()};
                    ~RestorePaths() { dottalk::paths::state() = saved; }
                } restore;
                if (!request.table_root.empty()) dottalk::paths::set_slot(dottalk::paths::Slot::DBF, request.table_root);
                if (!request.index_root.empty()) dottalk::paths::set_slot(dottalk::paths::Slot::INDEXES, request.index_root);
                output << "Table directory (unless saved in definition): " << dottalk::paths::get_slot(dottalk::paths::Slot::DBF).string() << '\n'
                       << "Index directory (unless saved in definition): " << dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES).string() << '\n';
                // LOAD consumes the complete remaining path. Pass directly to
                // its native dispatcher, without shell macro/comment expansion
                // or quotes that the workspace filename parser does not strip.
                output << "> WORKSPACE LOAD " << path.string() << '\n';
                if (saved) output << "Selected snapshot: " << request.provenance << '\n';
                command("LOAD " + path.string());
                break;
            }
            case Action::SetPath: {
                const auto slot = dottalk::paths::slot_from_string(request.name);
                const auto value = request.path.string();
                if (!slot || value.empty() || value.find_first_of("\r\n") != std::string::npos || value.find('\0') != std::string::npos)
                    throw std::runtime_error("Choose a path slot and a single directory value.");
                // A directory editor must not reinterpret a path as an IN target.
                std::istringstream words(value); std::vector<std::string> tokens; std::string word;
                while (words >> word) tokens.push_back(word);
                if (tokens.size() >= 3) {
                    auto in = tokens[tokens.size() - 2];
                    for (auto& c : in) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
                    if (in == "IN") throw std::runtime_error("Directory ends with SET PATH's IN clause. Use the command line to specify the intended workspace.");
                }
                const auto args = dottalk::paths::slot_name(*slot) + " " + value;
                output << "> SET PATH " << args << '\n';
                std::istringstream input(args); cmd_SETPATH(engine->area(engine->currentArea()), input);
                break;
            }
            case Action::NewWorkspace: {
                validate_name(request.name);
                if (request.workspace && xbase::workspace::name_of(request.workspace).empty())
                    throw std::runtime_error("Parent workspace no longer exists. Reopen the form.");
                command("NEW " + request.name + (request.workspace ? " UNDER " + std::to_string(request.workspace) : ""));
                const auto h = xbase::workspace::find_by_name_ci(request.name);
                if (!h || !xbase::workspace::ws_id_of(h)) throw std::runtime_error("Workspace creation refused; see engine response");
                break;
            }
            case Action::Hydrate: {
                require_load_ready();
                validate_name(request.name);
                if (request.workspace && xbase::workspace::name_of(request.workspace).empty())
                    throw std::runtime_error("Parent workspace no longer exists; reopen the form.");
                const auto root = home / "ram" / ("image-" + std::to_string(++image_sequence));
                const auto admission = admit_image(request.payload, root);
                if (!admission.ok()) throw std::runtime_error(admission.error);
                if (admission.tables > xbase::MAX_AREA - cli::workdesk::observe().open_area_count)
                    throw std::runtime_error("Not enough free work areas for this image");
                if (admission.scan.ram_file_bytes + xbase::ramfs::used_bytes() > 128ull * 1024 * 1024)
                    throw std::runtime_error("Image exceeds the private session's 128 MiB RAM budget");
                const auto previous_workspace = xbase::workspace::current_handle();
                const auto previous_area = engine->currentArea();
                const auto previous_paths = dottalk::paths::state();
                std::uint64_t created = 0;
                try {
                    command("NEW " + request.name + (request.workspace ? " UNDER " + std::to_string(request.workspace) : ""));
                    created = xbase::workspace::find_by_name_ci(request.name);
                    if (!created || !xbase::workspace::ws_id_of(created)) throw std::runtime_error("Workspace creation refused");
                    attach_image(request, created);
                    command("SWITCH " + std::to_string(created));
                    if (xbase::workspace::current_handle() != created) throw std::runtime_error("Cannot select hydration workspace");
                    fs::create_directories(root);
                    dottalk::paths::set_slot(dottalk::paths::Slot::RAM, root);
                    // Use the bounded private RAM budget without re-rooting DATA.
                    const auto mount_paths = dottalk::paths::state();
                    dottalk::paths::state().bin_root = home / "bin";
                    try {
                        std::istringstream mount("MOUNT"); cmd_VDISK(engine->area(engine->currentArea()), mount);
                    } catch (...) { dottalk::paths::state() = mount_paths; throw; }
                    dottalk::paths::state() = mount_paths;
                    if (!xbase::ramfs::mounted(root.string())) throw std::runtime_error("Private mount refused");
                    if (!cli::workspace_roots_bind_from_slots(created)) throw std::runtime_error("Cannot bind image roots");
                    command("LOAD " + request.name + " MEMO RAM");
                    std::size_t opened = 0;
                    for (auto slot : xbase::workspace::members(created))
                        if (slot >= 0 && engine->area(slot).isOpen()) ++opened;
                    if (opened != admission.tables) throw std::runtime_error("Image load was incomplete; see engine response");
                    std::vector<fs::path> destinations; std::string error;
                    if (!minidb::materialization_paths(request.payload, admission.scan, root, root / "indexes", destinations, error))
                        throw std::runtime_error(error);
                    for (std::size_t i = 0; i < destinations.size(); ++i) {
                        const auto& member = admission.scan.files[i];
                        std::string bytes;
                        if (minidb::is_memo_sidecar(member.relpath)) {
                            std::ifstream in(destinations[i], std::ios::binary);
                            bytes.assign(std::istreambuf_iterator<char>(in), {});
                        } else {
                            if (fs::exists(destinations[i])) throw std::runtime_error("RAM member unexpectedly written to disk");
                            auto in = xbase::ramfs::open(destinations[i].string(), false);
                            if (!in) throw std::runtime_error("Hydrated RAM member missing");
                            bytes.assign(std::istreambuf_iterator<char>(*in), {});
                        }
                        if (bytes != request.payload.substr(member.offset, member.length))
                            throw std::runtime_error("Hydrated member differs from image: " + member.relpath);
                    }
                    images.push_back({created, admission.scan.ram_file_bytes, admission.scan.sidecar_file_bytes, root, request.provenance});
                    output << "Verified " << opened << " tables; " << admission.scan.ram_file_bytes << " RAM bytes; "
                           << admission.scan.sidecar_file_bytes << " disk memo bytes.\n";
                } catch (...) {
                    if (created) {
                        command("SWITCH " + std::to_string(created));
                        const bool recurse = xbase::workspace::recursion_enabled();
                        xbase::workspace::set_recursion_enabled(false); command("CLOSE");
                        xbase::workspace::set_recursion_enabled(recurse);
                    }
                    release_mount(root);
                    command("SWITCH " + std::to_string(previous_workspace));
                    dottalk::paths::state() = previous_paths; engine->selectArea(previous_area);
                    output << "Failed import: birth row and any disk files are retained for review.\n";
                    throw;
                }
                break;
            }
            case Action::SwitchWorkspace:
                if (xbase::workspace::name_of(request.workspace).empty()) throw std::runtime_error("Workspace no longer exists");
                {
                    const auto line = "SWITCH " + std::to_string(request.workspace);
                    output << "> " << line << '\n';
                    std::istringstream expanded(cli::ShortcutResolver::resolve(line));
                    std::string verb; expanded >> verb;
                    if (verb != "WORKSPACE") throw std::runtime_error("SWITCH did not resolve to WORKSPACE");
                    cmd_WORKSPACE(engine->area(engine->currentArea()), expanded);
                    if (xbase::workspace::current_handle() != request.workspace)
                        throw std::runtime_error("SWITCH refused; see engine response");
                }
                break;
            case Action::Recursion:
                xbase::workspace::set_recursion_enabled(request.enabled); break;
            case Action::CloseWorkspace:
                command("CLOSE"); break;
            case Action::SelectArea: {
                if (request.slot < 0 || request.slot >= xbase::MAX_AREA) throw std::runtime_error("Invalid area slot");
                auto& area = engine->area(request.slot);
                if (!area.isOpen() || !request.area_handle || area.areaHandle() != request.area_handle)
                    throw std::runtime_error("Area selection is stale; refresh the live session");
                output << "> SELECT " << request.slot << '\n';
                std::istringstream area_number(std::to_string(request.slot));
                cmd_SELECT(engine->area(engine->currentArea()), area_number);
                if (engine->currentArea() != request.slot) throw std::runtime_error("SELECT refused; see engine response");
                break;
            }
            case Action::OpenCopy: {
                auto source = fs::absolute(request.path);
                auto extension = source.extension().string();
                std::transform(extension.begin(), extension.end(), extension.begin(),
                    [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
                if (extension != ".dbf" || !fs::is_regular_file(source))
                    throw std::runtime_error("Choose an existing DBF table");
                // A directory per copy permits the same table in several workspaces.
                // Only explicit table-family inputs are copied; indexes stay detached.
                const auto dir = home / "dbf" / ("copy-" + std::to_string(++copies));
                fs::create_directory(dir);
                auto stem = source.stem().string();
                if (stem.empty() || stem.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_") != std::string::npos)
                    stem = "TABLE";
                const auto destination = dir / (stem + ".dbf");
                std::vector<fs::path> family{source};
                for (const auto& entry : fs::directory_iterator(source.parent_path())) {
                    if (entry.path() == source || !entry.is_regular_file()) continue;
                    auto stem = entry.path().stem().string(), wanted = source.stem().string();
                    auto ext = entry.path().extension().string();
                    auto lower = [](std::string& s) { for (auto& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c))); };
                    lower(stem); lower(wanted); lower(ext);
                    if (stem == wanted && (ext == ".dtx" || ext == ".dbt" || ext == ".fpt")) family.push_back(entry.path());
                }
                struct Stamp { fs::path path; std::uintmax_t size; fs::file_time_type time; };
                std::vector<Stamp> stamps;
                std::uintmax_t total = 0;
                for (const auto& file : family) {
                    const auto size = fs::file_size(file); total += size;
                    if (total > 256ull * 1024 * 1024) throw std::runtime_error("Table family exceeds the 256 MiB inspection limit");
                    stamps.push_back({file, size, fs::last_write_time(file)});
                }
                for (const auto& stamp : stamps) {
                    auto ext = stamp.path.extension().string();
                    for (auto& c : ext) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
                    fs::copy_file(stamp.path, dir / (stem + ext));
                }
                for (const auto& stamp : stamps)
                    if (stamp.size != fs::file_size(stamp.path) || stamp.time != fs::last_write_time(stamp.path))
                        throw std::runtime_error("Source changed while copying; retry when the writer is idle");
                const auto before = cli::workdesk::observe().open_area_count;
                // The WORKSPACE tokenizer does not implement quoted paths.
                // Resolve an ASCII relative token under the private DBF slot,
                // which also supports a temp root containing spaces.
                const auto saved_paths = dottalk::paths::state();
                dottalk::paths::set_slot(dottalk::paths::Slot::DBF, home / "dbf");
                try { command("ADD " + destination.lexically_relative(home / "dbf").generic_string() + " NOINDEX"); }
                catch (...) { dottalk::paths::state() = saved_paths; throw; }
                dottalk::paths::state() = saved_paths;
                if (cli::workdesk::observe().open_area_count != before + 1)
                    throw std::runtime_error("Table opening refused; see engine response");
                break;
            }
            }
        } catch (const std::exception& e) { result.error = e.what(); }
        observe_command_images = false;
        for (auto& event : command_images) {
            auto tree = inspect_images(std::move(event.payload));
            tree.provenance = event.catalog.string() + " / " + event.name;
            tree.source_label = "Command load: " + std::to_string(event.opened_areas.size()) + " tables opened at load time";
            result.command_images.push_back({std::move(tree), event.name, event.workspace, std::move(event.opened_areas)});
        }
        command_images.clear();
        result.transcript = output.str();
        result.images = images;
        result.registered_commands = dli::map().size();
        for (int i = 0; i <= static_cast<int>(dottalk::paths::Slot::CUR_TMP); ++i) {
            const auto slot = static_cast<dottalk::paths::Slot>(i);
            const auto value = dottalk::paths::get_slot(slot);
            std::error_code ec;
            result.paths.push_back({dottalk::paths::slot_name(slot), value, fs::is_directory(value, ec) && !ec});
        }
        result.default_catalog = dottalk::paths::get_slot(dottalk::paths::Slot::WORKSPACES) / "WORKSPACES.dbf";
        result.dirty_areas = dirty_areas();
        result.exit_requested = xbase::shell_exit_requested() && !result.dirty_areas;
        xbase::clear_shell_exit_request();
        if (engine) {
            const auto handle = engine->area(engine->currentArea()).areaHandle();
            if (browse_handle != handle || request.action == Action::Command || request.action == Action::RunScript) browse_offset = 0;
            browse_handle = handle;
            if (browse_active) result.table = read_table_page(*engine, browse_offset,
                request.action == Action::TableCommand || request.action == Action::SelectRecord);
            result.browse_requested = browse_requested;
            result.desk = cli::workdesk::observe();
            for (const auto& workspace : result.desk.workspaces) {
                const auto members = xbase::workspace::members(workspace.handle);
                for (std::size_t local = 0; local < members.size(); ++local) {
                    const auto slot = members[local]; if (slot < 0) continue;
                    auto& area = engine->area(slot); if (!area.isOpen()) continue;
                    result.areas.push_back({area.areaHandle(), workspace.handle, slot,
                        static_cast<int>(local), area.name(), area.filename(), area.recCount64(), xbase::ramfs::is_virtual(area.filename())});
                    if (observe_load && !previous_areas.count(area.areaHandle())) ++result.command_opened_tables;
                }
            }
        }
        return result;
    }
};
WorkbenchSession::WorkbenchSession(SessionOptions options) : impl_(std::make_unique<Impl>(std::move(options))) {}
WorkbenchSession::~WorkbenchSession() = default;
void WorkbenchSession::shutdown() { impl_->stop(); }
std::future<SessionSnapshot> WorkbenchSession::submit(Request request) {
    return impl_->enqueue<SessionSnapshot>([this, request = std::move(request)] { return impl_->perform(request); });
}
std::future<cli::WorkspaceDefinitionCheck> WorkbenchSession::check_workspace(fs::path file, fs::path table_root, std::string payload) {
    return impl_->enqueue<cli::WorkspaceDefinitionCheck>([this, file = std::move(file), table_root = std::move(table_root), payload = std::move(payload)] {
        return cli::check_workspace_definition(payload.empty() ? file : impl_->stage_definition(payload), table_root);
    });
}
std::future<CatalogSnapshot> WorkbenchSession::inspect(fs::path path, std::stop_token stop) {
    return impl_->enqueue<CatalogSnapshot>([path = std::move(path), stop] { return inspect_catalog(path, stop); });
}
std::future<ImageTree> WorkbenchSession::inspect_image_file(fs::path path, std::stop_token stop) {
    return impl_->enqueue<ImageTree>([path = std::move(path), stop] {
        ImageTree result;
        try {
            return inspect_images(read_image_file(path, stop), stop);
        } catch (const std::exception& e) { result.error = e.what(); }
        return result;
    });
}
std::future<ImageTree> WorkbenchSession::inspect_image(std::string payload, std::stop_token stop) {
    return impl_->enqueue<ImageTree>([payload = std::move(payload), stop]() mutable { return inspect_images(std::move(payload), stop); });
}
std::future<FieldValue> WorkbenchSession::inspect_field(int slot, std::uint64_t handle, std::uint64_t record, int field1, std::string field_name) {
    return impl_->enqueue<FieldValue>([slot, handle, record, field1, field_name = std::move(field_name)] {
        if (!engine) { FieldValue value; value.error = "Engine unavailable"; return value; }
        return read_field_value(*engine, slot, handle, record, field1, field_name);
    });
}
std::future<MemoTarget> WorkbenchSession::inspect_memo_target(FieldEdit edit) {
    return impl_->enqueue<MemoTarget>([edit = std::move(edit)] {
        if (!engine) { MemoTarget target; target.error = "Engine unavailable"; return target; }
        return read_memo_target(*engine, edit);
    });
}
std::future<ImageTree> WorkbenchSession::inspect_field_image(int slot, std::uint64_t handle, std::uint64_t record,
                                                           int field1, std::string field_name, std::stop_token stop) {
    return impl_->enqueue<ImageTree>([slot, handle, record, field1, field_name = std::move(field_name), stop] {
        ImageTree result;
        if (!engine) { result.error = "Engine unavailable"; return result; }
        if (stop.stop_requested()) { result.error = "Image inspection cancelled"; return result; }
        auto memo = read_field_memo(*engine, slot, handle, record, field1, field_name, 128 * 1024 * 1024);
        if (!memo.error.empty()) { result.error = std::move(memo.error); return result; }
        if (!minidb::is_container(memo.bytes)) {
            result.error = "This memo does not contain a MINIDB image. Use Open value to inspect its contents."; return result;
        }
        result = inspect_images(std::move(memo.bytes), stop);
        result.provenance = std::move(memo.provenance);
        result.source_label = std::move(memo.label);
        return result;
    });
}
}
