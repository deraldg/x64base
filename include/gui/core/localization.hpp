#pragma once

#include "gui/core/model.hpp"

#include <string>
#include <string_view>
#include <vector>

namespace dottalk::gui {

struct LocaleContext {
    std::string message_locale {"en-US"};
    std::string display_locale {"en-US"};
    std::string parse_locale {"en-US"};
    std::string region_id {"GLOBAL"};
};

enum class GuiTextId {
    AppTitle,
    Ready,
    NoOpenAreas,
    NoTableOpen,
    NoAreaSelected,
    OpenTable,
    OpenWorkspace,
    SaveWorkspace,
    SaveWorkspaceAs,
    WorkspaceGraph,
    Refresh,
    RefreshSnapshot,
    CloseArea,
    Command,
    Run,
    Areas,
    Browse,
    Structure,
    File,
    Workspace,
    Area,
    Language,
    Help,
    Exit,
    About,
    AboutTitle,
    AboutBody,
    LocaleEnUs,
    LocaleEs,
    LocaleFr,
    LocaleDe,
    LocaleIt,
    OpeningTable,
    RefreshingSnapshot,
    ClosingArea,
    SelectingArea,
    RunningCommand,
    RowsShownOf,
    SeverityInfo,
    SeverityWarning,
    SeverityError,
    TaskQueued,
    TaskCancelledBeforeStart,
    TaskOpeningTable,
    TaskOpenTableFinished,
    TaskTableOpened,
    TaskOpenTableFailed,
    TaskSelectingArea,
    TaskAreaSelected,
    TaskSelectAreaFailed,
    TaskClosingArea,
    TaskAreaClosed,
    TaskCloseAreaFailed,
    TaskAreasListed,
    TaskRunningCommand,
    TaskCommandFinished,
    TaskCommandCompleted,
    TaskCommandFailed,
    TaskBuildingSnapshot,
    TaskSnapshotReady,
    TaskSnapshotFailed,
    StatusOpenTablePathMissing,
    StatusOpenTableOpened,
    StatusOpenTableFailed,
    StatusAreaNotOpen,
    StatusAreaSelected,
    StatusAreaClosed,
    StatusCommandEmpty,
    StatusCommandSkeleton,
    StatusSnapshotNoCurrentTable,
    StatusSnapshotFirstRecordPastEnd,
    StatusSnapshotRecordReadFailed,
    StatusSnapshotFailed
};

std::string normalize_locale(std::string_view locale);
std::vector<std::string> available_gui_message_locales();
bool is_gui_message_locale_supported(std::string_view locale);
LocaleContext locale_context_from_message_locale(std::string_view locale);
LocaleContext locale_context_from_environment();

std::string gui_text_key(GuiTextId id);
std::string gui_text(GuiTextId id, const LocaleContext& locale = {});
std::string gui_text(std::string_view key, const LocaleContext& locale = {});

std::string render_label(std::string_view label_code,
                         std::string_view fallback,
                         const LocaleContext& locale = {});
std::string render_status_text(const StatusMessage& message,
                               const LocaleContext& locale = {});
std::string render_status_line(const StatusMessage& message,
                               const LocaleContext& locale = {});

} // namespace dottalk::gui
