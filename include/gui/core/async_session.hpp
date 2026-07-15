#pragma once
// @dottalk.contract v1
// family: selfdoc.ui_contract
// component: gui_core_async_session
// role: GUI worker dispatch and lifetime boundary
// owner: DotTalk++ GUI open-architecture lane
// contract: AsyncSession owns the worker thread through RAII; destruction must stop the queue and join the worker.
// authority: AsyncSession schedules Session-backed work; it does not own alternate database semantics.
// threading: UI adapters submit work and consume events; worker code must not touch toolkit widgets directly.
// database: database behavior belongs to Session / DotTalk++ runtime services, not toolkit-specific GUI code.
// reuse: queued GUI work may orchestrate shared services or CLI bridges, but must not invent a frontend-only DBF/index/relation behavior layer.
// safety: queued work is mutex-protected; pending work may be cancelled, but active work completes before join.
// docs: docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md
// @dottalk.contract.end

#include "gui/core/events.hpp"
#include "gui/core/session.hpp"

#include <functional>
#include <memory>

namespace dottalk::gui {

class AsyncSession {
public:
    using EventSink = std::function<void(GuiEvent)>;

    explicit AsyncSession(EventSink sink);
    ~AsyncSession();

    AsyncSession(const AsyncSession&) = delete;
    AsyncSession& operator=(const AsyncSession&) = delete;

    TaskId submit_open_table(OpenTableRequest request);
    TaskId submit_select_area(SelectAreaRequest request);
    TaskId submit_move_cursor(MoveCursorRequest request);
    TaskId submit_close_area(CloseAreaRequest request);
    TaskId submit_list_areas();
    TaskId submit_command(CommandRequest request);
    TaskId submit_table_snapshot(TableSnapshotRequest request);

    void cancel_pending();

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace dottalk::gui
