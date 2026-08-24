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
                         "two opened areas did not claim engine slots 0 and 1")) {
                return EXIT_FAILURE;
            }

            // THE DISCRIMINATOR, REPOINTED BY RULING R120 (AIF-078 step 3).
            //
            // What this block asserted before step 3: the survivor keeps its
            // IDENTITY and INHERITS the position, the two rungs moving in
            // opposite directions across one close. That was true of a dense
            // list index and is false of an engine slot, so the expectations
            // below are INVERTED rather than adjusted, and they are inverted
            // deliberately -- a test whose subject moves must be repointed on
            // purpose, not left to pass for a new reason.
            //
            // What it asserts now: the survivor keeps BOTH rungs. Its identity
            // does not change and neither does its slot. The rungs no longer
            // move in opposite directions, because there is now only one
            // positional answer for an area and the engine already owned it.
            //
            // AND THE VACATED SLOT IS NOT REFILLED, which is the part the
            // author got wrong and this test caught. find_free_area_for_workspace
            // grows CONTIGUOUSLY: it takes highest_member + 1 and only scans for
            // the lowest free slot when that block is boxed in (and says so
            // through broke_contiguity when it does). close() leaves the
            // workspace (dbarea.cpp), so after closing slot 0 the members are
            // {1}, the highest is 1, and the reopen lands on 2. Slot 0 stays
            // empty.
            //
            // The first draft of this block asserted 0 -- "falls into the
            // hole" -- on an unmeasured guess about the allocator. It went red
            // here, which is the whole reason to run a discriminator against a
            // prediction instead of writing the prediction into the doctrine.
            //
            // This still cannot pass by accident. Under the old rung the
            // survivor's number CHANGED on close and the reopen landed at the
            // end; both of those now fail. The two spellings disagree on every
            // assertion in this block, which is what makes it a discriminator
            // in both directions.
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
            if (!require(after.areas[0].ordinal == 1,
                         "the surviving area did not KEEP its engine slot 1 "
                         "across the close of another area")) {
                return EXIT_FAILURE;
            }

            // And the two rungs are now measurably different numbers. Under the
            // old spelling this could not fail, because the displayed number WAS
            // id - 1 by construction. It can fail now, which is what makes it
            // worth asserting.
            //
            // The position is dereferenced explicitly, and that is R6.3 showing
            // its work: since the ordinal became std::optional, arithmetic on an
            // UNSET one does not compile. Under the old sentinel this line would
            // have cheerfully computed on ~0 and compared it.
            if (!require(after.areas[0].ordinal.has_value(),
                         "the surviving area reported no position at all")) {
                return EXIT_FAILURE;
            }
            if (!require(after.areas[0].area_id != *after.areas[0].ordinal + 1,
                         "identity and position are still the same number wearing two names")) {
                return EXIT_FAILURE;
            }

            // What a user types is the POSITION, and after R120 that is the
            // engine slot -- so this now selects 1, the slot the survivor kept,
            // and `select 0` would reach NOTHING because slot 0 is a hole.
            // Asserted on the reported VALUES, because run_command reports ok
            // for a miss as well as a hit.
            const auto selected = session.run_command(CommandRequest{"select 1"});
            if (!require(selected.output.find("Selected GUI area 1.") != std::string::npos,
                         "select 1 did not report selecting engine slot 1")) {
                return EXIT_FAILURE;
            }
            if (!require(!second.display_name.empty() &&
                             selected.output.find(second.display_name) != std::string::npos,
                         "select 1 reached a different table than the one at slot 1")) {
                return EXIT_FAILURE;
            }

            // AND THE HOLE IS REALLY A HOLE. Slot 0 was vacated by the close
            // and nothing has refilled it yet, so selecting it must MISS.
            // Without this the block would pass just as well if find_area_by
            // _ordinal had silently kept indexing the list -- where 0 is
            // always the first live area and can never be empty.
            const auto miss = session.run_command(CommandRequest{"select 0"});
            if (!require(miss.output.find("Selected GUI area 0.") == std::string::npos,
                         "select 0 claimed to select a slot that was vacated")) {
                return EXIT_FAILURE;
            }

            // Identity is never reused. Reopening the closed table mints a NEW
            // handle rather than handing back the one that just died, so a
            // stale id held by a view resolves to GONE and never to somebody
            // else. The position, being an address, COULD be reused -- but
            // under this allocator it is not reused eagerly: the workspace's
            // block grows past its highest member, so a reopen takes a fresh
            // slot and the vacated one is left standing empty until the block
            // is boxed in.
            const auto reopened = session.open_table(OpenTableRequest{first.path});
            if (!require(reopened.ok, "could not reopen the table that was closed")) {
                return EXIT_FAILURE;
            }
            if (!require(reopened.area_id != first.area_id,
                         "a reopened area was handed the dead area's identity")) {
                return EXIT_FAILURE;
            }
            // 2, not 0. This is the assertion that separates CONTIGUOUS
            // GROWTH from lowest-free-wins, and the two policies are
            // indistinguishable until something is closed out of the middle.
            // Asserting 0 here would have quietly encoded the wrong allocator.
            if (!require(reopened.ordinal == 2,
                         "the reopened area did not grow the workspace block to "
                         "slot 2 -- the allocator takes highest_member + 1, it "
                         "does not refill the vacated slot")) {
                return EXIT_FAILURE;
            }

            // AND THE SESSION IS NOW GENUINELY SPARSE: slots 1 and 2, with 0
            // standing empty. The old dense-list rung could not represent this
            // state at all -- it would have reported 0 and 1 -- so this is the
            // shape that only exists after R120.
            const auto sparse = session.list_areas();
            if (!require(sparse.areas.size() == 2, "expected two open areas")) {
                return EXIT_FAILURE;
            }
            bool holds_1 = false, holds_2 = false, holds_0 = false;
            for (const auto& a : sparse.areas) {
                if (a.ordinal == 0) holds_0 = true;
                if (a.ordinal == 1) holds_1 = true;
                if (a.ordinal == 2) holds_2 = true;
            }
            if (!require(holds_1 && holds_2 && !holds_0,
                         "the session did not report the sparse set {1, 2} with "
                         "slot 0 vacant")) {
                return EXIT_FAILURE;
            }

            std::cout << "area ladder: the survivor kept slot 1, the reopen grew "
                         "the block to slot 2 leaving slot 0 vacant, and identity "
                      << first.area_id << " was not reused (reopen minted "
                      << reopened.area_id << ")\n";
        }
    }

    std::cout << "PASS: dottalk_gui_core async smoke\n";
    return EXIT_SUCCESS;
}
