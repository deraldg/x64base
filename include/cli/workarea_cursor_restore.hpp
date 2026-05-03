#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace dottalk::tupleaugment {

// Workspace-wide cursor snapshot/restore helper.
//
// Relation-aware tuple commands may move the root workarea and any related
// child workareas while refreshing relations and projecting TupleRows.  This
// guard snapshots every open workarea and restores every captured cursor when
// close()/destructor runs.
class WorkAreaCursorRestore {
public:
    struct SlotState {
        std::size_t slot{0};
        std::int32_t recno{0};
        bool open{false};
        std::string name;
    };

    WorkAreaCursorRestore();
    ~WorkAreaCursorRestore();

    WorkAreaCursorRestore(const WorkAreaCursorRestore&) = delete;
    WorkAreaCursorRestore& operator=(const WorkAreaCursorRestore&) = delete;

    bool snapshot(std::string& error);
    bool restore(std::string& error) noexcept;
    void close() noexcept;

    [[nodiscard]] bool was_restored() const noexcept { return restored_; }
    [[nodiscard]] const std::vector<SlotState>& slots() const noexcept { return slots_; }

private:
    std::vector<SlotState> slots_;
    bool snapshotted_{false};
    bool restored_{false};
};

} // namespace dottalk::tupleaugment
