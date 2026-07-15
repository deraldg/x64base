#pragma once
// @dottalk.contract v1
// family: selfdoc.api_contract
// component: gui_core_session
// role: GUI-facing database/session facade over DotTalk++ services
// owner: DotTalk++ GUI open-architecture lane
// contract: Session exposes stable GUI commands, snapshots, workspace models, and area state without leaking toolkit code.
// authority: database truth flows from xbase/memo/xindex/xexpr into dottalkpp runtime/command services, then through Session into GUI models.
// database: x64base / DotTalk++ runtime remains the source of truth for DBF, index, relation, cursor, lock, loop, and variable behavior.
// gui: wx, Python, TUI, and future frontends should depend on this facade or its model shapes instead of reimplementing database rules.
// reuse: when GUI needs behavior not already exposed here, prefer shared runtime/library reuse or a CLI bridge before adding toolkit-local semantics.
// threading: callers may run Session behind an async adapter; Session itself is not a widget and must not call GUI toolkit APIs.
// docs: docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md
// @dottalk.contract.end

#include "gui/core/model.hpp"

#include <filesystem>
#include <memory>
#include <vector>

namespace dottalk::gui {

class Session {
public:
    Session();
    ~Session();

    Session(const Session&) = delete;
    Session& operator=(const Session&) = delete;

    OpenTableResult open_table(const OpenTableRequest& request);
    SelectAreaResult select_area(const SelectAreaRequest& request);
    MoveCursorResult move_cursor(const MoveCursorRequest& request);
    CloseAreaResult close_area(const CloseAreaRequest& request);
    ListAreasResult list_areas() const;
    WorkspaceModel workspace_model() const;
    CommandResult run_command(const CommandRequest& request);
    TableSnapshot snapshot_current_table(const TableSnapshotRequest& request) const;

private:
    struct Impl;
    std::size_t mirror_workspace_open_directory(const std::filesystem::path& dir,
                                                const std::string& shell_output,
                                                const std::string& index_mode,
                                                std::vector<StatusMessage>& messages);
    std::size_t mirror_workspace_load_schema(const std::filesystem::path& schema_path,
                                             std::vector<StatusMessage>& messages);
    bool save_workspace_schema(const std::filesystem::path& schema_path,
                               std::vector<StatusMessage>& messages,
                               std::filesystem::path* saved_path = nullptr) const;
    bool mirror_workspace_add_table(const std::filesystem::path& path,
                                    std::vector<StatusMessage>& messages);
    std::unique_ptr<Impl> impl_;
};

} // namespace dottalk::gui
