"""Shared GUI contract names mirrored from the C++ GUI core."""

from __future__ import annotations


TASK_STATES = {
    "queued",
    "running",
    "completed",
    "cancelled",
    "failed",
}

EVENT_KINDS = {
    "task_progress",
    "open_table_finished",
    "area_selected",
    "area_closed",
    "areas_listed",
    "table_snapshot_ready",
    "command_finished",
    "log_line",
}

AREA_LIFECYCLE = {
    "open",
    "list",
    "select",
    "refresh",
    "close",
}

STATUS_FIELDS = {
    "severity",
    "code",
    "text",
    "detail",
}

LOCALE_CONTEXT_FIELDS = {
    "message_locale",
    "display_locale",
    "parse_locale",
    "region_id",
}

GUI_MESSAGE_LOCALES = {
    "en-US",
    "es",
    "fr",
    "de",
    "it",
}

GUI_TEXT_KEYS = {
    "gui.app.title",
    "gui.status.ready",
    "gui.area.none_open",
    "gui.table.none_open",
    "gui.area.none_selected",
    "gui.action.open_table",
    "gui.action.open_workspace",
    "gui.action.save_workspace",
    "gui.action.save_workspace_as",
    "gui.action.refresh",
    "gui.action.refresh_snapshot",
    "gui.action.close_area",
    "gui.label.command",
    "gui.action.run",
    "gui.label.areas",
    "gui.label.workspace_graph",
    "gui.menu.workspace",
    "gui.menu.language",
    "gui.menu.help",
    "gui.action.about",
    "gui.about.title",
    "gui.about.body",
    "gui.locale.en_us",
    "gui.locale.es",
    "gui.locale.fr",
    "gui.locale.de",
    "gui.locale.it",
    "gui.tab.browse",
    "gui.tab.structure",
    "gui.task.queued",
    "gui.task.opening_table",
    "gui.task.snapshot_ready",
    "gui.open_table.opened",
    "gui.open_table.failed",
    "gui.area.not_open",
    "gui.snapshot.no_current_table",
}
