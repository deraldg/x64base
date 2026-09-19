// @dottalk.file v1
// subsystem: gui
// layer: service
// owns: serialized generated Workbench engine session
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#pragma once
#include "workbench_catalog.hpp"
#include "workbench_images.hpp"
#include "workbench_table.hpp"
#include "cli/cmd_workdesk.hpp"
#include "cli/workspace_definition.hpp"
#include <future>
#include <memory>
#include <optional>

namespace dottalk::workbench {
enum class Action { Observe, NewWorkspace, SwitchWorkspace, OpenCopy, SelectArea, CloseWorkspace, Recursion, Command, Hydrate, Browse, SelectRecord, EditField, CommitTable, RollbackTable, SaveImage, ExportImage, StoreImage, SetPath, OpenWorkspace, LoadWorkspace, RunScript, TableCommand, SetNullField };
struct SessionOptions {
    bool private_session{true};
    std::filesystem::path data_root;
};
std::filesystem::path find_workbench_data_root(const std::filesystem::path& executable,
                                               const std::filesystem::path& working_directory);
struct PathEntry { std::string slot; std::filesystem::path value; bool exists{}; };
struct Request {
    Action action{Action::Observe};
    std::string name;
    std::filesystem::path path;
    std::filesystem::path table_root, index_root; // defaults for one schema load
    std::uint64_t workspace{}, area_handle{};
    // Modal input is collected against this current workspace identity. The
    // worker refuses a changed context before any native command is executed.
    std::uint64_t expected_workspace{};
    std::optional<bool> include_nested;
    int slot{-1};
    bool enabled{};
    std::string payload, provenance;
    std::uint64_t offset{}, record{};
    FieldEdit edit;
};
struct LiveArea {
    std::uint64_t handle{}, workspace{};
    int slot{-1}, local_slot{-1};
    std::string name, path;
    std::uint64_t records{};
    bool ram{};
};
struct ResidentImage {
    std::uint64_t workspace{}, ram_bytes{}, disk_bytes{};
    std::filesystem::path root;
    std::string provenance;
};
struct CommandImage {
    ImageTree tree;
    std::string name;
    std::uint64_t workspace{};
    std::vector<std::uint64_t> opened_areas;
};
struct SessionSnapshot {
    cli::workdesk::Desk desk;
    std::vector<LiveArea> areas;
    std::vector<ResidentImage> images;
    // Events from this command only. Mount ownership stays with the engine.
    std::vector<CommandImage> command_images;
    std::size_t command_opened_tables{};
    std::filesystem::path home;
    std::filesystem::path saved_image;
    std::filesystem::path exported_image;
    std::filesystem::path default_catalog;
    std::vector<PathEntry> paths;
    std::string transcript, error;
    std::size_t registered_commands{};
    unsigned dirty_areas{};
    bool exit_requested{};
    bool browse_requested{};
    TablePage table;
    bool ok() const { return error.empty(); }
};
struct AreaScope {
    std::vector<std::size_t> indices;
    std::size_t workspaces{};
    std::string error;
};
// UI projection of one immutable snapshot. Never switches workspace, selects
// an area or consults the engine's separate save/close recursion setting.
AreaScope scope_areas(const SessionSnapshot& snapshot, std::uint64_t workspace,
                     bool all_workspaces, bool nested, const std::string& query = {});
struct NavigatorView {
    std::vector<std::uint64_t> workspaces;
    std::vector<std::size_t> areas;
};
// Search projects identities, never names as keys. Matching workspace branches
// and matching table owners retain their ancestors, including empty workspaces.
NavigatorView navigator_view(const SessionSnapshot& snapshot, const std::string& query = {});
// Only one instance may exist in a process. All engine calls and catalog reads
// run on the owned worker. Futures carry values, never engine/widget pointers.
class WorkbenchSession {
public:
    explicit WorkbenchSession(SessionOptions options = {});
    ~WorkbenchSession();
    WorkbenchSession(const WorkbenchSession&) = delete;
    WorkbenchSession& operator=(const WorkbenchSession&) = delete;
    std::future<SessionSnapshot> submit(Request request = {});
    std::future<cli::WorkspaceDefinitionCheck> check_workspace(std::filesystem::path file,
                                                              std::filesystem::path table_root,
                                                              std::string payload = {});
    std::future<CatalogSnapshot> inspect(std::filesystem::path path, std::stop_token stop = {});
    std::future<ImageTree> inspect_image(std::string payload, std::stop_token stop = {});
    std::future<ImageTree> inspect_image_file(std::filesystem::path path, std::stop_token stop = {});
    std::future<FieldValue> inspect_field(int slot, std::uint64_t handle, std::uint64_t record, int field1, std::string field_name);
    std::future<MemoTarget> inspect_memo_target(FieldEdit edit);
    std::future<ImageTree> inspect_field_image(int slot, std::uint64_t handle, std::uint64_t record,
                                             int field1, std::string field_name, std::stop_token stop = {});
    void shutdown();
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
