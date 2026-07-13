#!/usr/bin/env python3
"""Headless smoke test for the DotTalk++ Python GUI backend."""

from __future__ import annotations

import pathlib
import sys

import dottalk_gui_backend as backend
from dottalk_gui_async import AsyncSession, EventKind, command_output
from dottalk_gui_command_catalog import CommandActionKind, command_catalog
from dottalk_gui_text import (
    LocaleContext,
    available_gui_message_locales,
    locale_context_from_message_locale,
    render_label,
    text,
)
from dottalk_gui_workspace_format import format_workspace_graph_text
from gui_contract import (
    AREA_LIFECYCLE,
    EVENT_KINDS,
    GUI_TEXT_KEYS,
    GUI_MESSAGE_LOCALES,
    LOCALE_CONTEXT_FIELDS,
    STATUS_FIELDS,
    TASK_STATES,
)


def sample_dbf(repo: pathlib.Path) -> pathlib.Path:
    candidates = [
        repo / "build" / "src" / "Release" / "dbf" / "RM_BROWSE_V1.dbf",
        repo / "dottalkpp" / "data" / "dbf" / "x64" / "COURSES.DBF",
        repo / "dottalkpp" / "data" / "dbf" / "x64" / "ENROLL.DBF",
        repo / "dottalkpp" / "data" / "dbf" / "x64" / "STUDENTS.DBF",
        repo / "dottalkpp" / "data" / "dbf" / "X64SAMPLE.dbf",
        repo / ".mdo_backups" / "docs_20260523_195019" / "diagrams" / "dbf_isolated_v1" / "DIAGART.DBF",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No GUI backend sample DBF was found.")


def sample_x64_dbf(repo: pathlib.Path) -> pathlib.Path:
    candidates = [
        repo / "dottalkpp" / "data" / "dbf" / "x64" / "COURSES.DBF",
        repo / "dottalkpp" / "data" / "dbf" / "x64" / "ENROLL.DBF",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No x64 GUI backend sample DBF was found.")


def sample_x64_dir(repo: pathlib.Path) -> pathlib.Path:
    candidate = repo / "dottalkpp" / "data" / "dbf" / "x64"
    if candidate.is_dir():
        return candidate
    raise FileNotFoundError("No x64 GUI backend sample DBF directory was found.")


def sample_x64_schema(repo: pathlib.Path) -> pathlib.Path:
    candidates = [
        repo / "dottalkpp" / "user" / "default" / "workspaces" / "mcc_x64.dtschema",
        repo / "dottalkpp" / "data" / "workspaces" / "mcc_x64.dtschema",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No x64 GUI backend sample workspace schema was found.")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    require("queued" in TASK_STATES and "completed" in TASK_STATES, "task contract missing states")
    require("areas_listed" in EVENT_KINDS, "event contract missing areas_listed")
    require({"open", "list", "select", "refresh", "close"} <= AREA_LIFECYCLE, "area lifecycle contract incomplete")
    require({"severity", "code", "text", "detail"} <= STATUS_FIELDS, "status field contract incomplete")
    require(
        {"message_locale", "display_locale", "parse_locale", "region_id"} <= LOCALE_CONTEXT_FIELDS,
        "locale context contract incomplete",
    )
    require("it" in GUI_MESSAGE_LOCALES, "GUI locale contract missing Italian seam")
    require("gui.task.queued" in GUI_TEXT_KEYS, "GUI text contract missing queued task key")
    require("gui.menu.workspace" in GUI_TEXT_KEYS, "GUI text contract missing workspace menu key")
    require("gui.menu.language" in GUI_TEXT_KEYS, "GUI text contract missing language menu key")
    require("gui.menu.help" in GUI_TEXT_KEYS, "GUI text contract missing help menu key")
    require("gui.action.about" in GUI_TEXT_KEYS, "GUI text contract missing about action key")
    require("gui.label.workspace_graph" in GUI_TEXT_KEYS, "GUI text contract missing workspace graph key")
    require("es" in available_gui_message_locales(), "GUI message locales missing Spanish seam")
    require("it" in available_gui_message_locales(), "GUI message locales missing Italian seam")
    require(text("gui.status.ready", LocaleContext(message_locale="es")) == "Listo", "GUI text lookup failed")
    require(
        text("gui.status.ready", LocaleContext(message_locale="it")) == "Pronto",
        "GUI Italian text lookup failed",
    )
    require(
        text("gui.open_table.opened", LocaleContext(message_locale="en-US")) ==
        "Table opened in a new GUI work area.",
        "GUI status code lookup failed",
    )
    require(
        text("gui.menu.workspace", LocaleContext(message_locale="en-US")) == "Workspace",
        "GUI workspace menu text lookup failed",
    )
    require(
        text("gui.label.workspace_graph", LocaleContext(message_locale="en-US")) == "Workspace Graph",
        "GUI workspace graph text lookup failed",
    )
    require(
        text("gui.menu.language", LocaleContext(message_locale="it")) == "Lingua",
        "GUI language menu Italian lookup failed",
    )
    require(
        text("gui.locale.de", LocaleContext(message_locale="en-US")) == "German",
        "GUI locale label lookup failed",
    )
    require(
        text("gui.action.about", LocaleContext(message_locale="en-US")) == "About",
        "GUI about action lookup failed",
    )
    require(
        text("gui.menu.help", LocaleContext(message_locale="it")) == "Aiuto",
        "GUI help menu Italian lookup failed",
    )
    require(
        locale_context_from_message_locale("en_US.UTF-8").message_locale == "en-US",
        "GUI locale normalization failed",
    )
    require(
        locale_context_from_message_locale("it_IT.UTF-8").message_locale == "it",
        "GUI Italian locale normalization failed",
    )
    require(
        render_label("gui.task.queued", "Queued", LocaleContext(message_locale="en-US")) == "Queued",
        "GUI label rendering failed",
    )
    catalog = command_catalog()
    categories = {action.category for action in catalog}
    require(
        {"Table", "Record", "Index", "Lists", "Browse", "Rel", "Tuple", "Cmd"} <= categories,
        "Python GUI command catalog missing DotTalk++ Workbench-derived categories",
    )
    require(
        any(action.command == "ZAP" or (action.label.startswith("Zap") and action.kind == CommandActionKind.INFO)
            for action in catalog),
        "Python GUI command catalog missing guarded ZAP action",
    )
    require(
        any(action.command == "WORKSPACE OPEN DBF" for action in catalog),
        "Python GUI command catalog missing workspace open action",
    )

    repo = backend.repo_root()
    path = sample_dbf(repo)
    snapshot = backend.read_table_snapshot(path, 3)

    require(snapshot.get("path") == path, "snapshot path mismatch")
    require(int(snapshot.get("record_count", 0)) >= 0, "record_count missing")
    require(len(snapshot.get("fields", [])) > 0, "no fields returned")
    require(len(snapshot.get("rows", [])) <= 3, "row limit was not honored")
    require(bool(snapshot.get("backend")), "backend label missing")
    require("@" not in {str(field.get("name")) for field in snapshot.get("fields", [])}, "x64 header parsed as a field")
    require(
        all(len(row.get("values", [])) == len(snapshot.get("fields", [])) for row in snapshot.get("rows", [])),
        "row values do not align with fields",
    )
    record = backend.read_table_record(path, 1)
    require(record.get("path") == path, "record view path mismatch")
    require(int(record.get("record_count", 0)) >= 1, "record view record_count missing")
    record_row = record.get("row", {})
    require(isinstance(record_row, dict) and record_row.get("record_number") == 1, "record view row mismatch")
    require(
        len(record_row.get("values", [])) == len(record.get("fields", [])),
        "record view values do not align with fields",
    )

    x64_snapshot = backend.read_dbf_fallback(sample_x64_dbf(repo), 3)
    x64_fields = list(x64_snapshot.get("fields", []))
    x64_rows = list(x64_snapshot.get("rows", []))
    require("@" not in {str(field.get("name")) for field in x64_fields}, "x64 descriptor start was not honored")
    require(x64_fields and x64_rows, "x64 fallback snapshot is empty")
    require(
        all(len(row.get("values", [])) == len(x64_fields) for row in x64_rows),
        "x64 fallback row values do not align with fields",
    )

    session = backend.PythonAreaSession()
    first = session.open_table(path, 3)
    second = session.open_table(path, 2)
    require(first.area_id == second.area_id, "opening an already-open table did not select the existing area")
    require(len(session.areas) == 1, "opening an already-open table created a duplicate GUI area")
    require(session.active_area_id == second.area_id, "latest opened area was not active")
    require(session.select_area(first.area_id).area_id == first.area_id, "select_area failed")
    require("WORKSPACE AREAS" in command_output("areas", session), "areas command did not summarize workspace areas")
    require("BROWSE SUMMARY" in command_output("list", session), "list command did not summarize active browse")
    require("STRUCTURE" in command_output("structure", session), "structure command did not summarize fields")
    require("WORKSPACE GRAPH" in command_output("workspace graph", session), "workspace graph command failed")
    require("Active GUI commands" in command_output("help", session), "help command did not report GUI commands")
    require("cli <command>" in command_output("help", session), "help command did not report CLI bridge")
    require("Selected GUI area 0" in command_output("select 0", session), "select command did not use visible area id")
    require(command_output("goto 2", session).strip() == "Recno: 2", "goto command did not update GUI cursor")
    require(command_output("recno", session).strip() == "2", "recno command did not persist GUI cursor")
    require(command_output("skip -1", session).strip() == "Recno: 1", "skip command did not update GUI cursor")
    require("DBAREA" in command_output("dbarea", session), "dbarea command did not summarize GUI area")

    workspace_session = backend.PythonAreaSession()
    opened = workspace_session.mirror_workspace_open_directory(sample_x64_dir(repo), 1)
    require(opened >= 10, "workspace directory mirror did not open expected x64 tables")
    require(len(workspace_session.areas) == opened, "workspace directory mirror area count mismatch")
    require(workspace_session.areas[0].area_id == 1, "workspace mirror internal handle did not stay nonzero")
    require(
        command_output("areas", workspace_session).splitlines()[1].startswith("* 0  "),
        "workspace mirror did not present zero-based area numbering",
    )
    require(
        "Selected GUI area 0" in command_output("select 0", workspace_session),
        "workspace command select did not select by visible area id",
    )
    graph_text = format_workspace_graph_text(workspace_session.areas, workspace_session.active_area_id,
                                             "Workspace Graph", "No open areas")
    require("fields:" in graph_text and "records:" in graph_text, "workspace graph formatter missing area facts")
    first_workspace_count = len(workspace_session.areas)
    add_output = command_output(f"workspace add {sample_x64_dbf(repo)}", workspace_session)
    require("WORKSPACE ADD" in add_output, "workspace add did not mirror into GUI output")
    require(
        len(workspace_session.areas) == first_workspace_count,
        "workspace add duplicated an already-open GUI table",
    )
    attached = workspace_session.attach_default_indexes("CDX", sample_x64_dir(repo))
    require(attached > 0, "workspace directory mirror did not attach default CDX index rows")
    require(any(index.kind == "CDX" for index in workspace_session.indexes), "CDX index model row missing")

    schema_session = backend.PythonAreaSession()
    schema_output = command_output(f"workspace load {sample_x64_schema(repo)}", schema_session)
    require("WORKSPACE LOAD" in schema_output, "workspace load command did not report load")
    require(len(schema_session.areas) >= 10, "workspace load did not open schema areas")
    require(len(schema_session.indexes) >= 10, "workspace load did not mirror schema index rows")
    require(len(schema_session.relations) >= 10, "workspace load did not mirror schema relations")
    require(
        any(relation.parent == "STUDENTS" and relation.child == "ENROLL" for relation in schema_session.relations),
        "workspace load did not mirror STUDENTS->ENROLL relation",
    )
    graph_text = format_workspace_graph_text(schema_session.areas, schema_session.active_area_id,
                                             "Workspace Graph", "No open areas",
                                             schema_session.indexes, schema_session.relations)
    require("Indexes" in graph_text and "Relations" in graph_text, "workspace graph formatter missing model sections")
    close_output = command_output("workspace close", schema_session)
    require("Closed GUI areas" in close_output, "workspace close did not report closed areas")
    require(not schema_session.areas and not schema_session.indexes and not schema_session.relations,
            "workspace close did not clear complete Python workspace model")

    async_session = AsyncSession()
    try:
        async_session.submit_open_table(path)
        seen = set()
        saw_label_code = False
        for _ in range(100):
            event = async_session.events.get(timeout=2)
            seen.add(event.kind)
            saw_label_code = saw_label_code or bool(event.label_code)
            saw_label_code = saw_label_code or bool(event.progress and event.progress.label_code)
            if EventKind.TABLE_SNAPSHOT_READY in seen and EventKind.AREAS_LISTED in seen:
                break
        require(EventKind.OPEN_TABLE_FINISHED in seen, "async open event missing")
        require(EventKind.AREAS_LISTED in seen, "async areas listed event missing")
        require(EventKind.TABLE_SNAPSHOT_READY in seen, "async snapshot event missing")
        require(saw_label_code, "async progress label_code missing")
    finally:
        async_session.stop()

    print(f"PASS: gui backend smoke via {snapshot.get('backend')}")
    print(f"  table: {path}")
    print(f"  fields: {len(snapshot.get('fields', []))}")
    print(f"  rows: {len(snapshot.get('rows', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
