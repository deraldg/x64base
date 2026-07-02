#pragma once

#include "gui/core/model.hpp"

#include <memory>
#include <string>
#include <vector>

namespace dottalk::gui {

enum class GuiEventKind {
    task_progress,
    open_table_finished,
    area_selected,
    area_closed,
    areas_listed,
    workspace_model_ready,
    command_finished,
    table_snapshot_ready,
    log_line
};

struct GuiEvent {
    GuiEventKind kind {GuiEventKind::log_line};
    TaskId task_id {0};
    std::string label_code;
    std::string label;
    std::vector<StatusMessage> messages;
    TaskProgress progress;
    std::shared_ptr<const OpenTableResult> open_table;
    std::shared_ptr<const SelectAreaResult> select_area;
    std::shared_ptr<const CloseAreaResult> close_area;
    std::shared_ptr<const ListAreasResult> list_areas;
    std::shared_ptr<const WorkspaceModel> workspace_model;
    std::shared_ptr<const CommandResult> command;
    std::shared_ptr<const TableSnapshot> table_snapshot;
};

} // namespace dottalk::gui
