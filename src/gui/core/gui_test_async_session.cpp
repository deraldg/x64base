// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "gui/core/async_session.hpp"
#include "gui/core/localization.hpp"
#include "gui/core/session.hpp"
#include "common/path_state.hpp"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <condition_variable>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <mutex>
#include <string>
#include <vector>

namespace {

using dottalk::gui::AsyncSession;
using dottalk::gui::CloseAreaRequest;
using dottalk::gui::CommandRequest;
using dottalk::gui::GuiEvent;
using dottalk::gui::GuiEventKind;
using dottalk::gui::LocaleContext;
using dottalk::gui::OpenTableRequest;
using dottalk::gui::Severity;
using dottalk::gui::StatusMessage;
using dottalk::gui::TableSnapshotRequest;
using dottalk::gui::TaskState;

class EventCollector {
public:
    void push(GuiEvent event) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            events_.push_back(std::move(event));
        }
        changed_.notify_all();
    }

    bool wait_for_kind(GuiEventKind kind, std::chrono::milliseconds timeout) {
        std::unique_lock<std::mutex> lock(mutex_);
        return changed_.wait_for(lock, timeout, [&] {
            for (const auto& event : events_) {
                if (event.kind == kind) {
                    return true;
                }
            }
            return false;
        });
    }

    bool wait_for_progress(TaskState state, std::chrono::milliseconds timeout) {
        std::unique_lock<std::mutex> lock(mutex_);
        return changed_.wait_for(lock, timeout, [&] {
            for (const auto& event : events_) {
                if (event.kind == GuiEventKind::task_progress && event.progress.state == state) {
                    return true;
                }
            }
            return false;
        });
    }

    bool has_progress(TaskState state) const {
        std::lock_guard<std::mutex> lock(mutex_);
        for (const auto& event : events_) {
            if (event.kind == GuiEventKind::task_progress && event.progress.state == state) {
                return true;
            }
        }
        return false;
    }

    bool has_command_success() const {
        std::lock_guard<std::mutex> lock(mutex_);
        for (const auto& event : events_) {
            if (event.kind == GuiEventKind::command_finished && event.command && event.command->ok) {
                return true;
            }
        }
        return false;
    }

    bool has_command_output_containing(const std::string& text) const {
        std::lock_guard<std::mutex> lock(mutex_);
        for (const auto& event : events_) {
            if (event.kind == GuiEventKind::command_finished &&
                event.command &&
                event.command->output.find(text) != std::string::npos) {
                return true;
            }
        }
        return false;
    }

    bool has_cancelled_pending() const {
        std::lock_guard<std::mutex> lock(mutex_);
        for (const auto& event : events_) {
            if (event.kind == GuiEventKind::task_progress &&
                event.progress.state == TaskState::cancelled) {
                return true;
            }
        }
        return false;
    }

    bool has_label_code() const {
        std::lock_guard<std::mutex> lock(mutex_);
        for (const auto& event : events_) {
            if (!event.label_code.empty() || !event.progress.label_code.empty()) {
                return true;
            }
        }
        return false;
    }

    bool has_snapshot_warning() const {
        std::lock_guard<std::mutex> lock(mutex_);
        for (const auto& event : events_) {
            if (event.kind != GuiEventKind::table_snapshot_ready || !event.table_snapshot) {
                continue;
            }
            for (const auto& message : event.table_snapshot->messages) {
                if (message.severity == Severity::warning) {
                    return true;
                }
            }
        }
        return false;
    }

private:
    mutable std::mutex mutex_;
    std::condition_variable changed_;
    std::vector<GuiEvent> events_;
};

bool require(bool condition, const std::string& message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        return false;
    }
    return true;
}

} // namespace

int main() {
    LocaleContext spanish;
    spanish.message_locale = "es";
    if (!require(dottalk::gui::gui_text(dottalk::gui::GuiTextId::Ready, spanish) == "Listo",
                 "GUI localization did not resolve Spanish ready text")) {
        return EXIT_FAILURE;
    }
    LocaleContext italian;
    italian.message_locale = "it";
    if (!require(dottalk::gui::gui_text(dottalk::gui::GuiTextId::Ready, italian) == "Pronto",
                 "GUI localization did not resolve Italian ready text")) {
        return EXIT_FAILURE;
    }
    if (!require(dottalk::gui::locale_context_from_message_locale("en_US.UTF-8").message_locale == "en-US",
                 "GUI locale normalization did not handle environment-style locale")) {
        return EXIT_FAILURE;
    }
    if (!require(dottalk::gui::locale_context_from_message_locale("it_IT.UTF-8").message_locale == "it",
                 "GUI locale normalization did not handle Italian environment-style locale")) {
        return EXIT_FAILURE;
    }
    if (!require(dottalk::gui::is_gui_message_locale_supported("it"),
                 "GUI available locales did not include Italian")) {
        return EXIT_FAILURE;
    }
    if (!require(dottalk::gui::gui_text("gui.open_table.opened") == "Table opened in a new GUI work area.",
                 "GUI status code lookup did not resolve open-table status")) {
        return EXIT_FAILURE;
    }

    StatusMessage warning;
    warning.severity = Severity::warning;
    warning.code = dottalk::gui::gui_text_key(dottalk::gui::GuiTextId::NoAreaSelected);
    warning.text = "No area is selected";
    if (!require(dottalk::gui::render_status_line(warning).find("[gui.area.none_selected]") != std::string::npos,
                 "GUI status renderer did not include stable code")) {
        return EXIT_FAILURE;
    }

    EventCollector collector;

    {
        AsyncSession session([&collector](GuiEvent event) {
            collector.push(std::move(event));
        });

        const auto command_id = session.submit_command(CommandRequest{"help"});
        if (!require(command_id != 0, "submit_command returned a zero task id")) {
            return EXIT_FAILURE;
        }
        if (!require(collector.wait_for_kind(GuiEventKind::command_finished, std::chrono::seconds(5)),
                     "command completion event was not received")) {
            return EXIT_FAILURE;
        }
        if (!require(collector.has_progress(TaskState::queued), "queued progress was not published")) {
            return EXIT_FAILURE;
        }
        if (!require(collector.has_progress(TaskState::running), "running progress was not published")) {
            return EXIT_FAILURE;
        }
        if (!require(collector.wait_for_progress(TaskState::completed, std::chrono::seconds(5)),
                     "completed progress event was not received")) {
            return EXIT_FAILURE;
        }
        if (!require(collector.has_progress(TaskState::completed), "completed progress was not published")) {
            return EXIT_FAILURE;
        }
        if (!require(collector.has_label_code(), "progress/event label codes were not published")) {
            return EXIT_FAILURE;
        }
        if (!require(collector.has_command_success(), "command result was not successful")) {
            return EXIT_FAILURE;
        }
        if (!require(collector.has_command_output_containing("Active GUI commands"),
                     "GUI command lane did not return useful command output")) {
            return EXIT_FAILURE;
        }
        if (!require(collector.has_command_output_containing("cli <command>"),
                     "GUI command lane did not advertise the CLI bridge")) {
            return EXIT_FAILURE;
        }

        const auto snapshot_id = session.submit_table_snapshot(TableSnapshotRequest{});
        if (!require(snapshot_id != 0, "submit_table_snapshot returned a zero task id")) {
            return EXIT_FAILURE;
        }
        if (!require(collector.wait_for_kind(GuiEventKind::table_snapshot_ready, std::chrono::seconds(5)),
                     "snapshot event was not received")) {
            return EXIT_FAILURE;
        }
        if (!require(collector.has_snapshot_warning(), "snapshot without a table did not publish a warning")) {
            return EXIT_FAILURE;
        }

        for (int i = 0; i < 64; ++i) {
            (void)session.submit_open_table(OpenTableRequest{});
        }
        (void)session.submit_command(CommandRequest{"AFTER-CANCEL"});
        session.cancel_pending();
        if (!require(collector.has_cancelled_pending(), "pending cancellation was not published")) {
            return EXIT_FAILURE;
        }
    }

    {
        dottalk::gui::Session session;
        const auto students = dottalk::paths::get_slot(dottalk::paths::Slot::DBF_X64) / "students.dbf";
        std::error_code ec;
        if (std::filesystem::is_regular_file(students, ec) && !ec) {
            const auto opened = session.open_table(OpenTableRequest{students});
            if (!require(opened.ok, "GUI session could not open the students table for workspace save/load smoke")) {
                return EXIT_FAILURE;
            }

            const auto schema = std::filesystem::temp_directory_path() / "dottalk_gui_core_workspace_smoke.dtschema";
            std::filesystem::remove(schema, ec);

            const auto saved = session.run_command(CommandRequest{
                "workspace save " + schema.string()
            });
            if (!require(saved.ok, "workspace save command did not return success")) {
                return EXIT_FAILURE;
            }
            if (!require(std::filesystem::is_regular_file(schema, ec) && !ec,
                         "workspace save did not write the requested schema file")) {
                return EXIT_FAILURE;
            }

            (void)session.run_command(CommandRequest{"workspace close"});
            const auto loaded = session.run_command(CommandRequest{
                "workspace load " + schema.string()
            });
            if (!require(loaded.ok, "workspace load command did not return success")) {
                return EXIT_FAILURE;
            }

            const auto areas = session.list_areas();
            if (!require(areas.areas.size() == 1, "workspace load did not restore the saved GUI area")) {
                return EXIT_FAILURE;
            }
        }
    }

    {
        // ---- AIF-078: the area identity ladder ----------------------------
        //
        // AreaId used to be a private mint counter in one place and `slot + 1`
        // in three others, while three separate files reconstructed the number
        // to display as `id - 1`. Those agreed with each other only while
        // nothing was ever closed, because the counter started at 1 and so
        // `id - 1` happened to equal the open ordinal.
        //
        // So this block closes an area and then asks both rungs where things
        // are. Every assertion below compares VALUES the session reports, not
        // the shape of the reply -- a spec that asserts shape passes on a
        // blanked fixture.
        dottalk::gui::Session session;

        std::error_code ec;
        const auto dbf_root = dottalk::paths::get_slot(dottalk::paths::Slot::DBF_X64);
        std::vector<std::filesystem::path> candidates;
        for (std::filesystem::directory_iterator it(dbf_root, ec), end; !ec && it != end; it.increment(ec)) {
            if (!it->is_regular_file(ec) || ec) {
                ec.clear();
                continue;
            }
            std::string ext = it->path().extension().string();
            for (auto& ch : ext) {
                ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
            }
            if (ext == ".dbf") {
                candidates.push_back(it->path());
            }
        }
        std::sort(candidates.begin(), candidates.end());

        std::vector<dottalk::gui::OpenTableResult> opened;
        for (const auto& candidate : candidates) {
            if (opened.size() >= 2) {
                break;
            }
            auto result = session.open_table(OpenTableRequest{candidate});
            if (result.ok) {
                opened.push_back(std::move(result));
            }
        }

        if (opened.size() < 2) {
            // LOUD, never silent. A fixture that could not run has to say so in
            // the transcript, or its green means nothing -- which is exactly
            // how WSLADDER nearly shipped two arms passing against two empty
            // tables.
            std::cout << "SKIP: area ladder needs two openable tables under "
                      << dbf_root.string() << "; found " << opened.size() << "\n";
        } else {
            const auto first = opened[0];
            const auto second = opened[1];

            if (!require(first.area_id != second.area_id,
                         "two simultaneously open areas were handed one identity")) {
                return EXIT_FAILURE;
            }
            if (!require(first.ordinal == 0 && second.ordinal == 1,
                         "two opened areas did not land at positions 0 and 1")) {
                return EXIT_FAILURE;
            }

            // THE DISCRIMINATOR. Close the first. The survivor must keep its
            // IDENTITY and inherit the POSITION -- the two rungs moving in
            // opposite ways across one event, which is the whole claim.
            const auto closed = session.close_area(CloseAreaRequest{first.area_id});
            if (!require(closed.ok, "close_area did not close the first area")) {
                return EXIT_FAILURE;
            }

            const auto after = session.list_areas();
            if (!require(after.areas.size() == 1, "the close left the wrong number of areas open")) {
                return EXIT_FAILURE;
            }
            if (!require(after.areas[0].area_id == second.area_id,
                         "the surviving area changed identity across a close")) {
                return EXIT_FAILURE;
            }
            if (!require(after.areas[0].ordinal == 0,
                         "the surviving area did not inherit position 0")) {
                return EXIT_FAILURE;
            }

            // And the two rungs are now measurably different numbers. Under the
            // old spelling this could not fail, because the displayed number WAS
            // id - 1 by construction. It can fail now, which is what makes it
            // worth asserting.
            if (!require(after.areas[0].area_id != after.areas[0].ordinal + 1,
                         "identity and position are still the same number wearing two names")) {
                return EXIT_FAILURE;
            }

            // What a user types is the POSITION. It has to reach the area that
            // is actually sitting there -- asserted on the reported VALUES,
            // because run_command reports ok for a miss as well as a hit.
            const auto selected = session.run_command(CommandRequest{"select 0"});
            if (!require(selected.output.find("Selected GUI area 0.") != std::string::npos,
                         "select 0 did not report selecting position 0")) {
                return EXIT_FAILURE;
            }
            if (!require(!second.display_name.empty() &&
                             selected.output.find(second.display_name) != std::string::npos,
                         "select 0 reached a different table than the one at position 0")) {
                return EXIT_FAILURE;
            }

            // Identity is never reused. Reopening the closed table mints a NEW
            // handle rather than handing back the one that just died, so a
            // stale id held by a view resolves to GONE and never to somebody
            // else. The position, being an address, IS reused.
            const auto reopened = session.open_table(OpenTableRequest{first.path});
            if (!require(reopened.ok, "could not reopen the table that was closed")) {
                return EXIT_FAILURE;
            }
            if (!require(reopened.area_id != first.area_id,
                         "a reopened area was handed the dead area's identity")) {
                return EXIT_FAILURE;
            }
            if (!require(reopened.ordinal == 1, "the reopened area did not take the free position")) {
                return EXIT_FAILURE;
            }

            std::cout << "area ladder: position 0 was reused across a close, identity "
                      << first.area_id << " was not (reopen minted " << reopened.area_id << ")\n";
        }
    }

    std::cout << "PASS: dottalk_gui_core async smoke\n";
    return EXIT_SUCCESS;
}
