"""Shared-style async task/session layer for the Python GUI frontend."""

from __future__ import annotations

import pathlib
import queue
import threading
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from gui_cli_bridge import run_cli_command
from dottalk_gui_backend import PythonAreaSession, resolve_workspace_schema_token
from dottalk_gui_command_catalog import command_catalog
from gui_contract import EVENT_KINDS, TASK_STATES


def gui_repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


def gui_data_root() -> pathlib.Path:
    for env_name in ("DOTTALKPP_DATA", "DOTTALK_DATA"):
        value = os.environ.get(env_name)
        if value and pathlib.Path(value).is_dir():
            return pathlib.Path(value).resolve()
    root = gui_repo_root()
    for candidate in (root / "dottalkpp" / "data", root / "data", pathlib.Path.cwd()):
        if candidate.is_dir():
            return candidate.resolve()
    return pathlib.Path.cwd().resolve()


def gui_path_report() -> str:
    data = gui_data_root()
    root = data.parent
    return "\n".join([
        "GUI PATH ROOTS",
        f"ROOT       = {root}",
        f"DATA       = {data}",
        f"DBF        = {data / 'dbf'}",
        f"DBF_X64    = {data / 'dbf' / 'x64'}",
        f"INDEXES    = {data / 'indexes'}",
        f"LMDB       = {data / 'lmdb'}",
        f"WORKSPACES = {data / 'workspaces'}",
        f"SCHEMAS    = {data / 'schemas'}",
        f"SCRIPTS    = {data / 'scripts'}",
        f"LOGS       = {data / 'logs'}",
        "Startup scripts searched: init.ini, dottalkpp.ini, dotscript.ini",
        "Shutdown script searched: shutdown.ini",
    ])


def _format_cli_result(cli: Any) -> str:
    heading = "External DotTalk++ CLI"
    if cli.executable is not None:
        heading += f" ({cli.executable})"
    lines = [heading, f"exit={cli.exit_code}"]
    if cli.output:
        lines.append(cli.output.rstrip())
    if cli.detail:
        lines.append(cli.detail)
    return "\n".join(lines)


def _visible_area_id(area_id: int) -> str:
    return "none" if area_id == 0 else str(area_id - 1)


def _strip_matching_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


SHELL_SHORTCUTS = {
    "H": "HELP",
    "FH": "FOXHELP",
    "CH": "CMDHELP",
    "COMMANDSHELP": "CMDHELP",
    "CHK": "CMDHELPCHK",
    "PS": "PSHELL",
    "BT": "BROWSETUI",
    "BTV": "TVISION",
    "LU": "LMDB_UTIL",
    "REPEAT": "ECHO",
    "TURBOTALK": "FOXTALK",
    "!": "BANG",
    "?": "FORMULA",
    "UNDELETE": "RECALL",
    "EXACT": "SETCASE",
    "SET_RELATION": "SET RELATION",
    "TUP": "TUPLE",
    "TABLES": "TABLE_BUFFER",
    "TABLE": "TABLE_BUFFER",
    "DO": "DOTSCRIPT",
    "RUN": "DOTSCRIPT",
    "TESTRUN": "TEST",
    "TR": "TEST",
    "SL": "SMARTLIST",
    "LP": "LOOP",
    "EL": "ENDLOOP",
    "LL": "LIST_LMDB",
    "WH": "SQL",
    "SM": "SMARTBROWSE",
    "SMART": "SMARTBROWSE",
    "SB": "SIMPLEBROWSE",
    "WS": "SIMPLEBROWSE",
    "SMARTLISTFOR": "SMARTLIST",
    "SLFOR": "SMARTLIST",
    "SEL": "SELECT",
    "BOOL": "BOOLEAN",
    "EVAL": "EVALUATE",
    "S": "SELECT",
    "DESC": "DESCEND",
}


def _resolve_shell_shortcut(command: str) -> str:
    parts = command.strip().split(maxsplit=1)
    if not parts:
        return ""
    expanded = SHELL_SHORTCUTS.get(parts[0].upper())
    if not expanded:
        return command.strip()
    if len(parts) == 1:
        return expanded
    return f"{expanded} {parts[1]}"


def _dbf_flavor_label(snapshot: dict[str, object]) -> str:
    version = snapshot.get("version", "unknown")
    if isinstance(version, str):
        return version
    try:
        value = int(version)
    except (TypeError, ValueError):
        return "unknown"
    names = {
        0x03: "xBase/dbf v32",
        0x83: "xBase/dbf v32 memo",
        0xF5: "FoxPro v32 memo",
        0x30: "Visual FoxPro/v64",
        0x31: "Visual FoxPro/v64 autoinc",
        0x32: "Visual FoxPro/v64 variable",
        0x64: "x64base/x64",
    }
    return f"{names.get(value, 'unknown')} (version 0x{value:02X})"


def _workspace_open_directory_from_command(command: str) -> pathlib.Path | None:
    parts = command.split()
    if len(parts) >= 3 and parts[0].lower() == "workspace" and parts[1].lower() == "open":
        return pathlib.Path(parts[2])
    return None


def _workspace_add_table_from_command(command: str) -> pathlib.Path | None:
    parts = command.split()
    if len(parts) >= 3 and parts[0].lower() == "workspace" and parts[1].lower() == "add":
        return pathlib.Path(parts[2])
    return None


def _workspace_areas_text(session: PythonAreaSession) -> str:
    lines = ["WORKSPACE AREAS"]
    if not session.areas:
        lines.append("  No open areas.")
    else:
        for area in session.areas:
            marker = "*" if area.area_id == session.active_area_id else " "
            lines.append(
                f"{marker} {_visible_area_id(area.area_id)}  {area.display_name}  "
                f"records={area.snapshot.get('record_count', 0)}  path={area.path}"
            )
    return "\n".join(lines)


def _workspace_graph_text(session: PythonAreaSession) -> str:
    active = _visible_area_id(session.active_area_id)
    lines = [
        "WORKSPACE GRAPH",
        f"Areas: {len(session.areas)}",
        f"Active area: {active}",
        f"Indexes: {len(session.indexes)}",
        f"Relations: {len(session.relations)}",
        "Browsers/lists: workspace graph service pending",
        "ERSATZ presets: runtime output available; visual presets pending",
        "DTSchema load/save: bootstrap menu active; graph service pending",
    ]
    return "\n".join(lines)


def _parse_int(text: str) -> int | None:
    try:
        return int(text)
    except ValueError:
        return None


def _edit_distance_limited(left: str, right: str, limit: int = 2) -> int:
    if abs(len(left) - len(right)) > limit:
        return limit + 1
    previous = list(range(len(right) + 1))
    for index, left_char in enumerate(left, start=1):
        current = [index]
        best = index
        for j, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            value = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            current.append(value)
            best = min(best, value)
        if best > limit:
            return limit + 1
        previous = current
    return previous[-1]


def _known_command_verbs() -> set[str]:
    verbs = {
        "help", "aiuto", "about", "openarch", "architecture",
        "area", "areas", "workspace", "graph", "status", "paths", "setpath",
        "select", "dbarea", "recno", "goto", "go", "skip", "top", "bottom",
        "list", "browse", "structure", "cli", "ersatz", "dir", "area51",
        "do", "run", "dotscript", "scan", "endscan", "loop", "endloop",
        "while", "endwhile", "until", "enduntil", "var", "set",
        "smart", "sm", "smartbrowse", "smartbrowser", "smartlist", "sl",
        "use", "close", "gps", "lock", "unlock", "replace", "append",
        "delete", "recall", "seek", "find", "locate", "continue",
        "bang", "formula", "cmdhelp", "foxhelp", "pshell", "browsetui",
        "tvision", "foxtalk", "test", "lmdb_util", "table_buffer",
        "simplebrowse", "tuple", "descend", "evaluate", "boolean",
    }
    for action in command_catalog():
        parts = action.command.split()
        if parts:
            verbs.add(parts[0].lower())
    return verbs


def _command_suggestion(verb: str) -> str:
    best = ""
    best_distance = 3
    for candidate in _known_command_verbs():
        distance = _edit_distance_limited(verb, candidate, 2)
        if distance < best_distance:
            best = candidate
            best_distance = distance
    return best if best_distance <= 2 else ""


def command_output(text: str, session: PythonAreaSession) -> str:
    command = text.strip()
    dispatch_command = _resolve_shell_shortcut(command)
    verb = dispatch_command.split(maxsplit=1)[0].lower() if dispatch_command else ""
    if verb in {"help", "aiuto", "?"}:
        return (
            "DotTalk++ Workbench command lane\n\n"
            "Active GUI commands:\n"
            "  help | aiuto      show this command summary\n"
            "  about             show workbench identity\n"
            "  area              summarize the active GUI work area\n"
            "  areas | workspace list\n"
            "                    list open workspace areas\n"
            "  workspace open <dir> [CDX]\n"
            "                    open every DBF in a directory as GUI areas\n"
            "  workspace close   close all GUI work areas\n"
            "  workspace load|save <name.dtschema>\n"
            "                    load/save DTSchema workspace files\n"
            "  list | browse     summarize the active browse snapshot\n"
            "  status            summarize GUI session status\n"
            "  structure         list fields for the active area\n"
            "  graph | workspace graph\n"
            "                    summarize the current workspace graph\n"
            "  paths | setpath   show GUI path roots\n"
            "  openarch          summarize the GUI open architecture rule\n"
            "  select <area>     select a persistent GUI work area\n"
            "  dbarea            summarize persistent runtime area state\n"
            "  recno             show the active area record pointer\n"
            "  goto <n>          move the active area record pointer\n"
            "  skip [n]          move relative in the active area\n"
            "  top | bottom      move to first or last record\n"
            "  set dbf|index     command skeleton for path/index settings\n"
            "  scan ... endscan  send multiline SCAN block to the CLI bridge\n"
            "  do | dotscript    run a DotTalk++ script through the CLI bridge\n"
            "  loop/endloop      CLI control block family; use through the bridge\n"
            "  var | set var     CLI variable family; use through the bridge\n"
            "  cli <command>     force the DotTalk++ CLI bridge\n\n"
            "Unknown commands stay in the GUI so typos do not start a throwaway CLI process.\n"
            "Runtime lane: external DotTalk++ script bridge (not persistent yet).\n"
            "Known menu commands may use the compatibility bridge while native GUI services mature.\n"
            "Set DOTTALKPP_GUI_CLI or DOTTALKPP_EXE to select a dottalkpp executable."
        )
    if verb == "about":
        return (
            "DotTalk++ Workbench\n"
            "A windowed workspace for areas, tables, indexes, relations, browsers, and command lanes."
        )
    if verb in {"openarch", "architecture"}:
        return "\n".join([
            "DOTTALK++ GUI OPENARCH",
            "GUI grows top-down: workbench, workspace graph, areas, projections, scripts, diagnostics.",
            "Database behavior remains bottom-up and authoritative in DotTalk++ runtime services.",
            "wx owns native desktop presentation; Python owns fast scripted inspection.",
            "Commands and scripts flow through the CLI bridge until native GUI services own them.",
            "Skeleton actions must stay explicit; widget code must not fork database semantics.",
        ])
    if verb == "area":
        area = session.active_area()
        if area is None:
            return "No current GUI work area is selected."
        return "\n".join([
            "ACTIVE GUI AREA",
            f"Area: {_visible_area_id(area.area_id)}",
            f"Table: {area.display_name}",
            f"Records: {area.snapshot.get('record_count', 0)}",
            f"Fields: {len(area.snapshot.get('fields', []))}",
            f"File type: {_dbf_flavor_label(area.snapshot)}",
            f"Path: {area.path}",
        ])
    if verb == "areas" or dispatch_command.lower() in {"workspace", "workspace list"}:
        return _workspace_areas_text(session)
    if verb == "workspace":
        parts = dispatch_command.split()
        action = parts[1].lower() if len(parts) >= 2 else ""
        if action == "open":
            if len(parts) < 3:
                return "Usage: workspace open <directory> [CDX]"
            target = pathlib.Path(parts[2])
            opened = session.mirror_workspace_open_directory(target)
            index_mode = ""
            for part in parts[3:]:
                if part.upper() in {"CDX", "CNX", "INX", "IDX"}:
                    index_mode = part.upper()
                    break
            attached = session.attach_default_indexes(index_mode, target) if index_mode else 0
            lines = [
                "WORKSPACE OPEN",
                f"Directory: {target}",
                f"Opened GUI areas: {opened}",
            ]
            if index_mode:
                lines.append(f"Index mode: {index_mode}")
                lines.append(f"Attached GUI index containers: {attached}")
            area = session.active_area()
            if area is not None:
                lines.append(f"Active area: {_visible_area_id(area.area_id)}  {area.display_name}")
            return "\n".join(lines)
        if action == "add":
            if len(parts) < 3:
                return "Usage: workspace add <table.dbf>"
            target = pathlib.Path(parts[2])
            if target.is_file() and target.suffix.lower() == ".dbf":
                area = session.open_table(target)
                return "\n".join([
                    "WORKSPACE ADD",
                    f"Table: {target}",
                    f"GUI area selected/opened: {_visible_area_id(area.area_id)}",
                ])
            return "\n".join(["WORKSPACE ADD", f"Table: {target}", "No GUI area opened."])
        if action == "close":
            closed = session.clear_workspace()
            return "\n".join(["WORKSPACE CLOSE", f"Closed GUI areas: {closed}"])
        if action == "graph":
            return _workspace_graph_text(session)
        if action == "load":
            name = dispatch_command.split(maxsplit=2)[2] if len(dispatch_command.split(maxsplit=2)) >= 3 else "(not provided)"
            schema = resolve_workspace_schema_token(pathlib.Path(_strip_matching_quotes(name))) if name != "(not provided)" else None
            if schema is None:
                return "\n".join([
                    "WORKSPACE LOAD",
                    f"DTSchema: {name}",
                    "Schema file was not found by the Python workbench resolver.",
                ])
            opened = session.mirror_workspace_load_schema(schema)
            return "\n".join([
                "WORKSPACE LOAD",
                f"DTSchema: {schema}",
                f"Opened GUI areas: {opened}",
                f"Indexes: {len(session.indexes)}",
                f"Relations: {len(session.relations)}",
            ])
        if action in {"save", "saveas"}:
            name = dispatch_command.split(maxsplit=2)[2] if len(dispatch_command.split(maxsplit=2)) >= 3 else "(not provided)"
            return "\n".join([
                f"WORKSPACE {action}",
                f"DTSchema: {name}",
                "Schema save remains a GUI bootstrap file operation in this Python lane.",
            ])
        return "\n".join([
            "WORKSPACE COMMANDS",
            "  workspace list",
            "  workspace open <directory> [CDX]",
            "  workspace add <table.dbf>",
            "  workspace close",
            "  workspace load <name.dtschema>",
            "  workspace save <name.dtschema>",
        ])
    if verb == "graph" or dispatch_command.lower() == "workspace graph":
        return _workspace_graph_text(session)
    if verb in {"list", "browse"}:
        area = session.active_area()
        if area is None:
            return "No current table is selected."
        return "\n".join([
            "BROWSE SUMMARY",
            f"Area: {_visible_area_id(area.area_id)}",
            f"Table: {area.display_name}",
            f"Records: {area.snapshot.get('record_count', 0)}",
            f"Fields: {len(area.snapshot.get('fields', []))}",
            "Use the Browse tab for row data.",
        ])
    if verb == "status":
        area = session.active_area()
        lines = [
            "GUI SESSION STATUS",
            f"Open areas: {len(session.areas)}",
            f"Active area: {_visible_area_id(area.area_id) if area is not None else 'none'}",
        ]
        if area is not None:
            lines.extend([
                f"Active table: {area.display_name}",
                f"Records: {area.snapshot.get('record_count', 0)}",
                f"Path: {area.path}",
            ])
        lines.append("Runtime lane: external DotTalk++ script bridge (not persistent yet)")
        lines.append("CLI bridge: use cli <command> to force the compatibility bridge.")
        return "\n".join(lines)
    if verb in {"paths", "setpath"}:
        return gui_path_report()
    if dispatch_command.lower() in {"set dbf", "set database", "set index", "set indexes"}:
        return (
            f"Command accepted by the Workbench command lane: {command}\n"
            "SET DBF / SET INDEX GUI controls are skeletons for now.\n"
            "Use SETPATH DBF <path> or SETPATH INDEXES <path> through the CLI bridge while the native GUI controls mature."
        )
    if verb == "select":
        target = dispatch_command.split(maxsplit=1)[1].strip() if len(dispatch_command.split(maxsplit=1)) > 1 else ""
        try:
            area = session.select_area_by_user_token(target)
        except KeyError:
            return f"No matching GUI work area is open: {target}"
        return "\n".join([
            f"Selected GUI area {_visible_area_id(area.area_id)}.",
            f"Table: {area.display_name}",
            f"Recno: {area.recno}",
        ])
    if verb == "dbarea":
        area = session.active_area()
        if area is None:
            return "No current GUI work area is selected."
        return "\n".join([
            "DBAREA",
            f"Area: {_visible_area_id(area.area_id)}",
            f"Logical name: {area.path.stem}",
            f"Table: {area.display_name}",
            f"File type: {_dbf_flavor_label(area.snapshot)}",
            f"Path: {area.path}",
            "Open: yes",
            f"Records: {area.snapshot.get('record_count', 0)}",
            f"Fields: {len(area.snapshot.get('fields', []))}",
            f"Recno: {area.recno}",
            f"BOF: {'yes' if area.recno == 0 else 'no'}",
            f"EOF: {'yes' if area.recno > int(area.snapshot.get('record_count', 0)) else 'no'}",
        ])
    if verb == "recno":
        area = session.active_area()
        if area is None:
            return "No current table is selected."
        parts = dispatch_command.split()
        if len(parts) >= 2:
            parsed = _parse_int(parts[1])
            if parsed is None or parsed < 1:
                return "Usage: recno <record-number>"
            area = session.goto_record(parsed)
        return str(area.recno)
    if verb in {"goto", "go"}:
        parts = dispatch_command.split()
        if len(parts) < 2 or _parse_int(parts[1]) is None or int(parts[1]) < 1:
            return "Usage: goto <record-number>"
        try:
            area = session.goto_record(int(parts[1]))
        except KeyError:
            return "No current table is selected."
        return f"Recno: {area.recno}"
    if verb == "skip":
        parts = dispatch_command.split()
        delta = 1
        if len(parts) >= 2:
            parsed = _parse_int(parts[1])
            if parsed is None:
                return "Usage: skip [offset]"
            delta = parsed
        try:
            area = session.skip_records(delta)
        except KeyError:
            return "No current table is selected."
        return f"Recno: {area.recno}"
    if verb in {"top", "bottom"}:
        try:
            area = session.top() if verb == "top" else session.bottom()
        except KeyError:
            return "No current table is selected."
        return f"Recno: {area.recno}"
    if verb == "structure":
        area = session.active_area()
        if area is None:
            return "No current table is selected."
        lines = [f"STRUCTURE {area.display_name}"]
        for index, field in enumerate(area.snapshot.get("fields", []), start=1):
            if isinstance(field, dict):
                lines.append(
                    f"{index}  {field.get('name')}  "
                    f"{field.get('type')}({field.get('length')},{field.get('decimals')})"
                )
        return "\n".join(lines)
    if verb == "cli":
        cli_command = command.split(maxsplit=1)[1].strip() if len(command.split(maxsplit=1)) > 1 else ""
        area = session.active_area()
        active_path = area.path if area is not None else None
        active_recno = area.recno if area is not None else 0
        cli = run_cli_command(cli_command, active_path, active_recno)
        if not cli.attempted:
            return cli.detail
        output = _format_cli_result(cli)
        if cli.ok:
            for note in session.mirror_cli_output(cli_command, cli.output):
                output += "\n" + note
        return output
    if verb not in _known_command_verbs():
        lines = [f"Unknown GUI command: {verb}"]
        suggestion = _command_suggestion(verb)
        if suggestion:
            lines.append(f"Did you mean: {suggestion}?")
        lines.extend([
            "No external CLI process was started.",
            f"Use cli {command} to force the DotTalk++ CLI bridge.",
        ])
        return "\n".join(lines)

    area = session.active_area()
    cli = run_cli_command(
        dispatch_command,
        area.path if area is not None else None,
        area.recno if area is not None else 0,
    )
    if cli.attempted:
        output = _format_cli_result(cli)
        if cli.ok:
            for note in session.mirror_cli_output(dispatch_command, cli.output):
                output += "\n" + note
        target = _workspace_open_directory_from_command(dispatch_command)
        if cli.ok and target is not None and not session.areas:
            opened = session.mirror_workspace_open_directory(target)
            output += f"\nGUI mirror: WORKSPACE OPEN created {opened} GUI area(s) from {target}\n"
        target = _workspace_add_table_from_command(dispatch_command)
        if cli.ok and target is not None:
            if target.is_file() and target.suffix.lower() == ".dbf":
                area = session.open_table(target)
                output += (
                    f"\nGUI mirror: WORKSPACE ADD selected/opened GUI area "
                    f"{_visible_area_id(area.area_id)} for {target}\n"
                )
            else:
                output += f"\nGUI mirror: WORKSPACE ADD did not open GUI area for {target}\n"
        return output
    return (
        f"Command accepted by the Workbench command lane: {command}\n"
        "DotTalk++ CLI bridge is not available yet.\n"
        f"{cli.detail}"
    )


class TaskState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class EventKind(str, Enum):
    TASK_PROGRESS = "task_progress"
    OPEN_TABLE_FINISHED = "open_table_finished"
    AREA_SELECTED = "area_selected"
    AREA_CLOSED = "area_closed"
    AREAS_LISTED = "areas_listed"
    TABLE_SNAPSHOT_READY = "table_snapshot_ready"
    COMMAND_FINISHED = "command_finished"
    LOG_LINE = "log_line"


assert {state.value for state in TaskState} == TASK_STATES
assert {kind.value for kind in EventKind} == EVENT_KINDS


@dataclass
class TaskProgress:
    task_id: int
    state: TaskState
    label_code: str
    label: str


@dataclass
class GuiEvent:
    kind: EventKind
    task_id: int = 0
    label_code: str = ""
    label: str = ""
    payload: Any = None
    messages: list[str] = field(default_factory=list)
    progress: TaskProgress | None = None


class AsyncSession:
    def __init__(self) -> None:
        self.events: queue.Queue[GuiEvent] = queue.Queue()
        self._work: queue.Queue[tuple[int, str, tuple[Any, ...]]] = queue.Queue()
        self._session = PythonAreaSession()
        self._next_task_id = 1
        self._stopping = False
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._stopping = True
        self._work.put((0, "stop", ()))
        self._worker.join(timeout=2)

    def submit_open_table(self, path: pathlib.Path) -> int:
        return self._submit("open_table", path)

    def submit_select_area(self, area_id: int) -> int:
        return self._submit("select_area", area_id)

    def submit_move_cursor(self, area_id: int, record_number: int) -> int:
        return self._submit("move_cursor", area_id, record_number)

    def submit_close_area(self, area_id: int) -> int:
        return self._submit("close_area", area_id)

    def submit_list_areas(self) -> int:
        return self._submit("list_areas")

    def submit_table_snapshot(self, area_id: int = 0) -> int:
        return self._submit("table_snapshot", area_id)

    def submit_command(self, text: str) -> int:
        return self._submit("command", text)

    def _submit(self, kind: str, *args: Any) -> int:
        task_id = self._next_task_id
        self._next_task_id += 1
        self._post_progress(task_id, TaskState.QUEUED, "gui.task.queued", "Queued")
        self._work.put((task_id, kind, args))
        return task_id

    def _workspace_payload(self) -> dict[str, object]:
        return {
            "areas": list(self._session.areas),
            "indexes": list(self._session.indexes),
            "relations": list(self._session.relations),
            "active_area_id": self._session.active_area_id,
        }

    def _run(self) -> None:
        while True:
            task_id, kind, args = self._work.get()
            if self._stopping or kind == "stop":
                return
            try:
                self._dispatch(task_id, kind, args)
            except Exception as exc:  # noqa: BLE001 - async boundary converts failures to events.
                self.events.put(GuiEvent(
                    kind=EventKind.LOG_LINE,
                    task_id=task_id,
                    label_code="gui.task.command_failed",
                    label="Task failed",
                    messages=[str(exc)],
                ))
                self._post_progress(task_id, TaskState.FAILED, "gui.task.command_failed", "Task failed")

    def _dispatch(self, task_id: int, kind: str, args: tuple[Any, ...]) -> None:
        if kind == "open_table":
            self._post_progress(task_id, TaskState.RUNNING, "gui.task.opening_table", "Opening table")
            area = self._session.open_table(args[0])
            self.events.put(GuiEvent(
                EventKind.OPEN_TABLE_FINISHED,
                task_id,
                "gui.task.open_table_finished",
                "Open table finished",
                area,
            ))
            self._post_progress(task_id, TaskState.COMPLETED, "gui.task.table_opened", "Table opened")
            self.submit_list_areas()
            self.submit_table_snapshot(area.area_id)
        elif kind == "select_area":
            self._post_progress(task_id, TaskState.RUNNING, "gui.task.selecting_area", "Selecting work area")
            area = self._session.select_area(int(args[0]))
            self.events.put(GuiEvent(
                EventKind.AREA_SELECTED,
                task_id,
                "gui.task.area_selected",
                "Work area selected",
                area,
            ))
            self._post_progress(task_id, TaskState.COMPLETED, "gui.task.area_selected", "Work area selected")
            self.events.put(GuiEvent(
                EventKind.AREAS_LISTED,
                task_id,
                "gui.task.areas_listed",
                "Work areas listed",
                self._workspace_payload(),
            ))
            self.submit_table_snapshot(area.area_id)
        elif kind == "move_cursor":
            self._post_progress(task_id, TaskState.RUNNING, "gui.task.building_snapshot", "Moving cursor")
            area = self._session.select_area(int(args[0]))
            area = self._session.goto_record(int(args[1]))
            snapshot = dict(area.snapshot)
            snapshot["current_record_number"] = area.recno
            self.events.put(GuiEvent(
                EventKind.TABLE_SNAPSHOT_READY,
                task_id,
                "gui.task.snapshot_ready",
                "Table snapshot ready",
                snapshot,
            ))
            self.events.put(GuiEvent(
                EventKind.AREAS_LISTED,
                task_id,
                "gui.task.areas_listed",
                "Work areas listed",
                self._workspace_payload(),
            ))
            self._post_progress(task_id, TaskState.COMPLETED, "gui.task.snapshot_ready", "Cursor moved")
        elif kind == "close_area":
            self._post_progress(task_id, TaskState.RUNNING, "gui.task.closing_area", "Closing work area")
            self._session.close_area(int(args[0]))
            self.events.put(GuiEvent(
                EventKind.AREA_CLOSED,
                task_id,
                "gui.task.area_closed",
                "Work area closed",
                self._session.active_area_id,
            ))
            self._post_progress(task_id, TaskState.COMPLETED, "gui.task.area_closed", "Work area closed")
            self.submit_list_areas()
            if self._session.active_area_id:
                self.submit_table_snapshot(self._session.active_area_id)
            else:
                self.submit_table_snapshot(0)
        elif kind == "list_areas":
            self.events.put(GuiEvent(
                EventKind.AREAS_LISTED,
                task_id,
                "gui.task.areas_listed",
                "Work areas listed",
                self._workspace_payload(),
            ))
            self._post_progress(task_id, TaskState.COMPLETED, "gui.task.areas_listed", "Work areas listed")
        elif kind == "table_snapshot":
            self._post_progress(task_id, TaskState.RUNNING, "gui.task.building_snapshot", "Building table snapshot")
            area_id = int(args[0])
            area = self._session.select_area(area_id) if area_id else self._session.active_area()
            snapshot = dict(area.snapshot) if area else {"fields": [], "rows": [], "record_count": 0}
            if area is not None:
                snapshot["current_record_number"] = area.recno
            self.events.put(GuiEvent(
                EventKind.TABLE_SNAPSHOT_READY,
                task_id,
                "gui.task.snapshot_ready",
                "Table snapshot ready",
                snapshot,
            ))
            self._post_progress(task_id, TaskState.COMPLETED, "gui.task.snapshot_ready", "Table snapshot ready")
        elif kind == "command":
            text = str(args[0])
            self._post_progress(task_id, TaskState.RUNNING, "gui.task.running_command", "Running command")
            self.events.put(GuiEvent(
                EventKind.COMMAND_FINISHED,
                task_id,
                "gui.task.command_finished",
                "Command finished",
                command_output(text, self._session),
            ))
            self.events.put(GuiEvent(
                EventKind.AREAS_LISTED,
                task_id,
                "gui.task.areas_listed",
                "Work areas listed",
                self._workspace_payload(),
            ))
            if self._session.active_area_id:
                area = self._session.active_area()
                if area is not None:
                    snapshot = dict(area.snapshot)
                    snapshot["current_record_number"] = area.recno
                    self.events.put(GuiEvent(
                        EventKind.TABLE_SNAPSHOT_READY,
                        task_id,
                        "gui.task.snapshot_ready",
                        "Table snapshot ready",
                        snapshot,
                    ))
            else:
                self.events.put(GuiEvent(
                    EventKind.TABLE_SNAPSHOT_READY,
                    task_id,
                    "gui.task.snapshot_ready",
                    "Table snapshot ready",
                    {"fields": [], "rows": [], "record_count": 0},
                ))
            self._post_progress(task_id, TaskState.COMPLETED, "gui.task.command_completed", "Command completed")

    def _post_progress(self, task_id: int, state: TaskState, label_code: str, label: str) -> None:
        self.events.put(GuiEvent(
            kind=EventKind.TASK_PROGRESS,
            task_id=task_id,
            label_code=label_code,
            label=label,
            progress=TaskProgress(task_id, state, label_code, label),
        ))
