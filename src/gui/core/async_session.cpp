#include "gui/core/async_session.hpp"

#include "gui/core/localization.hpp"

#include <condition_variable>
#include <cstdint>
#include <deque>
#include <mutex>
#include <thread>
#include <utility>

namespace dottalk::gui {

namespace {

TaskProgress progress(TaskId task_id, TaskState state, GuiTextId label_id, std::string label) {
    TaskProgress value;
    value.task_id = task_id;
    value.state = state;
    value.label_code = gui_text_key(label_id);
    value.label = std::move(label);
    return value;
}

GuiEvent progress_event(TaskId task_id, TaskState state, GuiTextId label_id, std::string label) {
    GuiEvent event;
    event.kind = GuiEventKind::task_progress;
    event.task_id = task_id;
    event.label_code = gui_text_key(label_id);
    event.label = label;
    event.progress = progress(task_id, state, label_id, std::move(label));
    return event;
}

void set_label(GuiEvent& event, GuiTextId label_id, std::string label) {
    event.label_code = gui_text_key(label_id);
    event.label = std::move(label);
}

bool has_error(const std::vector<StatusMessage>& messages) {
    for (const auto& message : messages) {
        if (message.severity == Severity::error) {
            return true;
        }
    }
    return false;
}

std::shared_ptr<TableSnapshot> empty_snapshot() {
    return std::make_shared<TableSnapshot>();
}

} // namespace

struct AsyncSession::Impl {
    using Work = std::function<void(Session&, TaskId)>;

    explicit Impl(EventSink sink_in)
        : sink(std::move(sink_in)),
          worker(&Impl::run, this) {
    }

    ~Impl() {
        {
            std::lock_guard<std::mutex> lock(mutex);
            stopping = true;
            queue.clear();
        }
        changed.notify_one();
        if (worker.joinable()) {
            worker.join();
        }
    }

    TaskId submit(Work work) {
        TaskId task_id = 0;
        {
            std::lock_guard<std::mutex> lock(mutex);
            if (stopping) {
                return 0;
            }
            task_id = next_task_id++;
            queue.push_back(QueuedWork{task_id, std::move(work)});
        }
        post(progress_event(task_id, TaskState::queued, GuiTextId::TaskQueued, "Queued"));
        changed.notify_one();
        return task_id;
    }

    void cancel_pending() {
        std::deque<QueuedWork> cancelled;
        {
            std::lock_guard<std::mutex> lock(mutex);
            cancelled.swap(queue);
        }
        for (const auto& item : cancelled) {
            post(progress_event(item.task_id,
                                TaskState::cancelled,
                                GuiTextId::TaskCancelledBeforeStart,
                                "Cancelled before start"));
        }
    }

    void post(GuiEvent event) const {
        if (sink) {
            sink(std::move(event));
        }
    }

    void post_workspace_model(Session& session, TaskId task_id) const {
        auto model = std::make_shared<WorkspaceModel>(session.workspace_model());
        GuiEvent event;
        event.kind = GuiEventKind::workspace_model_ready;
        event.task_id = task_id;
        set_label(event, GuiTextId::TaskAreasListed, "Workspace model ready");
        event.messages = model->messages;
        event.workspace_model = model;
        post(std::move(event));
    }

    void run() {
        Session session;
        for (;;) {
            QueuedWork item;
            {
                std::unique_lock<std::mutex> lock(mutex);
                changed.wait(lock, [this] {
                    return stopping || !queue.empty();
                });
                if (stopping && queue.empty()) {
                    return;
                }
                item = std::move(queue.front());
                queue.pop_front();
            }
            item.work(session, item.task_id);
        }
    }

    struct QueuedWork {
        TaskId task_id {0};
        Work work;
    };

    EventSink sink;
    mutable std::mutex mutex;
    std::condition_variable changed;
    std::deque<QueuedWork> queue;
    std::thread worker;
    TaskId next_task_id {1};
    bool stopping {false};
};

AsyncSession::AsyncSession(EventSink sink)
    : impl_(std::make_unique<Impl>(std::move(sink))) {
}

AsyncSession::~AsyncSession() = default;

TaskId AsyncSession::submit_open_table(OpenTableRequest request) {
    return impl_->submit([request = std::move(request), this](Session& session, TaskId task_id) mutable {
        impl_->post(progress_event(task_id, TaskState::running, GuiTextId::TaskOpeningTable, "Opening table"));
        auto result = std::make_shared<OpenTableResult>(session.open_table(request));

        GuiEvent event;
        event.kind = GuiEventKind::open_table_finished;
        event.task_id = task_id;
        set_label(event, GuiTextId::TaskOpenTableFinished, "Open table finished");
        event.messages = result->messages;
        event.open_table = result;
        impl_->post(std::move(event));

        auto areas = std::make_shared<ListAreasResult>(session.list_areas());
        GuiEvent areas_event;
        areas_event.kind = GuiEventKind::areas_listed;
        areas_event.task_id = task_id;
        set_label(areas_event, GuiTextId::TaskAreasListed, "Work areas listed");
        areas_event.messages = areas->messages;
        areas_event.list_areas = areas;
        impl_->post(std::move(areas_event));
        impl_->post_workspace_model(session, task_id);
        if (areas->active_area_id != 0) {
            auto snapshot = std::make_shared<TableSnapshot>(session.snapshot_current_table(
                TableSnapshotRequest{areas->active_area_id, 0, 200}));
            GuiEvent snapshot_event;
            snapshot_event.kind = GuiEventKind::table_snapshot_ready;
            snapshot_event.task_id = task_id;
            set_label(snapshot_event, GuiTextId::TaskSnapshotReady, "Table snapshot ready");
            snapshot_event.messages = snapshot->messages;
            snapshot_event.table_snapshot = snapshot;
            impl_->post(std::move(snapshot_event));
        } else {
            GuiEvent snapshot_event;
            snapshot_event.kind = GuiEventKind::table_snapshot_ready;
            snapshot_event.task_id = task_id;
            set_label(snapshot_event, GuiTextId::TaskSnapshotReady, "Table snapshot ready");
            snapshot_event.table_snapshot = empty_snapshot();
            impl_->post(std::move(snapshot_event));
        }

        const TaskState state = result->ok ? TaskState::completed : TaskState::failed;
        impl_->post(progress_event(task_id,
                                   state,
                                   result->ok ? GuiTextId::TaskTableOpened : GuiTextId::TaskOpenTableFailed,
                                   result->ok ? "Table opened" : "Open table failed"));
    });
}

TaskId AsyncSession::submit_select_area(SelectAreaRequest request) {
    return impl_->submit([request, this](Session& session, TaskId task_id) {
        impl_->post(progress_event(task_id,
                                   TaskState::running,
                                   GuiTextId::TaskSelectingArea,
                                   "Selecting work area"));
        auto result = std::make_shared<SelectAreaResult>(session.select_area(request));

        GuiEvent event;
        event.kind = GuiEventKind::area_selected;
        event.task_id = task_id;
        set_label(event, GuiTextId::TaskAreaSelected, "Work area selected");
        event.messages = result->messages;
        event.select_area = result;
        impl_->post(std::move(event));
        impl_->post_workspace_model(session, task_id);

        const TaskState state = result->ok ? TaskState::completed : TaskState::failed;
        impl_->post(progress_event(task_id,
                                   state,
                                   result->ok ? GuiTextId::TaskAreaSelected : GuiTextId::TaskSelectAreaFailed,
                                   result->ok ? "Work area selected" : "Select work area failed"));
    });
}

TaskId AsyncSession::submit_move_cursor(MoveCursorRequest request) {
    return impl_->submit([request, this](Session& session, TaskId task_id) {
        impl_->post(progress_event(task_id,
                                   TaskState::running,
                                   GuiTextId::TaskBuildingSnapshot,
                                   "Moving cursor"));
        auto result = session.move_cursor(request);

        if (!result.messages.empty()) {
            GuiEvent log_event;
            log_event.kind = GuiEventKind::log_line;
            log_event.task_id = task_id;
            set_label(log_event, GuiTextId::TaskCommandFinished, "Cursor move finished");
            log_event.messages = result.messages;
            impl_->post(std::move(log_event));
        }

        if (result.ok) {
            impl_->post_workspace_model(session, task_id);
            auto snapshot = std::make_shared<TableSnapshot>(session.snapshot_current_table(
                TableSnapshotRequest{request.area_id, 0, 200}));
            GuiEvent snapshot_event;
            snapshot_event.kind = GuiEventKind::table_snapshot_ready;
            snapshot_event.task_id = task_id;
            set_label(snapshot_event, GuiTextId::TaskSnapshotReady, "Table snapshot ready");
            snapshot_event.messages = snapshot->messages;
            snapshot_event.table_snapshot = snapshot;
            impl_->post(std::move(snapshot_event));
        }

        impl_->post(progress_event(task_id,
                                   result.ok ? TaskState::completed : TaskState::failed,
                                   result.ok ? GuiTextId::TaskSnapshotReady : GuiTextId::TaskCommandFailed,
                                   result.ok ? "Cursor moved" : "Cursor move failed"));
    });
}

TaskId AsyncSession::submit_close_area(CloseAreaRequest request) {
    return impl_->submit([request, this](Session& session, TaskId task_id) {
        impl_->post(progress_event(task_id, TaskState::running, GuiTextId::TaskClosingArea, "Closing work area"));
        auto result = std::make_shared<CloseAreaResult>(session.close_area(request));

        GuiEvent event;
        event.kind = GuiEventKind::area_closed;
        event.task_id = task_id;
        set_label(event, GuiTextId::TaskAreaClosed, "Work area closed");
        event.messages = result->messages;
        event.close_area = result;
        impl_->post(std::move(event));
        impl_->post_workspace_model(session, task_id);

        const TaskState state = result->ok ? TaskState::completed : TaskState::failed;
        impl_->post(progress_event(task_id,
                                   state,
                                   result->ok ? GuiTextId::TaskAreaClosed : GuiTextId::TaskCloseAreaFailed,
                                   result->ok ? "Work area closed" : "Close work area failed"));
    });
}

TaskId AsyncSession::submit_list_areas() {
    return impl_->submit([this](Session& session, TaskId task_id) {
        auto result = std::make_shared<ListAreasResult>(session.list_areas());

        GuiEvent event;
        event.kind = GuiEventKind::areas_listed;
        event.task_id = task_id;
        set_label(event, GuiTextId::TaskAreasListed, "Work areas listed");
        event.messages = result->messages;
        event.list_areas = result;
        impl_->post(std::move(event));
        impl_->post_workspace_model(session, task_id);

        impl_->post(progress_event(task_id, TaskState::completed, GuiTextId::TaskAreasListed, "Work areas listed"));
    });
}

TaskId AsyncSession::submit_command(CommandRequest request) {
    return impl_->submit([request = std::move(request), this](Session& session, TaskId task_id) mutable {
        impl_->post(progress_event(task_id, TaskState::running, GuiTextId::TaskRunningCommand, "Running command"));
        auto result = std::make_shared<CommandResult>(session.run_command(request));

        GuiEvent event;
        event.kind = GuiEventKind::command_finished;
        event.task_id = task_id;
        set_label(event, GuiTextId::TaskCommandFinished, "Command finished");
        event.messages = result->messages;
        event.command = result;
        impl_->post(std::move(event));

        auto areas = std::make_shared<ListAreasResult>(session.list_areas());
        GuiEvent areas_event;
        areas_event.kind = GuiEventKind::areas_listed;
        areas_event.task_id = task_id;
        set_label(areas_event, GuiTextId::TaskAreasListed, "Work areas listed");
        areas_event.messages = areas->messages;
        areas_event.list_areas = areas;
        impl_->post(std::move(areas_event));
        impl_->post_workspace_model(session, task_id);

        if (areas->active_area_id != 0) {
            auto snapshot = std::make_shared<TableSnapshot>(session.snapshot_current_table(
                TableSnapshotRequest{areas->active_area_id, 0, 200}));
            GuiEvent snapshot_event;
            snapshot_event.kind = GuiEventKind::table_snapshot_ready;
            snapshot_event.task_id = task_id;
            set_label(snapshot_event, GuiTextId::TaskSnapshotReady, "Table snapshot ready");
            snapshot_event.messages = snapshot->messages;
            snapshot_event.table_snapshot = snapshot;
            impl_->post(std::move(snapshot_event));
        }

        const TaskState state = result->ok ? TaskState::completed : TaskState::failed;
        impl_->post(progress_event(task_id,
                                   state,
                                   result->ok ? GuiTextId::TaskCommandCompleted : GuiTextId::TaskCommandFailed,
                                   result->ok ? "Command completed" : "Command failed"));
    });
}

TaskId AsyncSession::submit_table_snapshot(TableSnapshotRequest request) {
    return impl_->submit([request, this](Session& session, TaskId task_id) {
        impl_->post(progress_event(task_id,
                                   TaskState::running,
                                   GuiTextId::TaskBuildingSnapshot,
                                   "Building table snapshot"));
        auto snapshot = std::make_shared<TableSnapshot>(session.snapshot_current_table(request));

        GuiEvent event;
        event.kind = GuiEventKind::table_snapshot_ready;
        event.task_id = task_id;
        set_label(event, GuiTextId::TaskSnapshotReady, "Table snapshot ready");
        event.messages = snapshot->messages;
        event.table_snapshot = snapshot;
        impl_->post(std::move(event));

        const bool failed = has_error(snapshot->messages);
        impl_->post(progress_event(task_id,
                                   failed ? TaskState::failed : TaskState::completed,
                                   failed ? GuiTextId::TaskSnapshotFailed : GuiTextId::TaskSnapshotReady,
                                   failed ? "Table snapshot failed" : "Table snapshot ready"));
    });
}

void AsyncSession::cancel_pending() {
    impl_->cancel_pending();
}

} // namespace dottalk::gui
