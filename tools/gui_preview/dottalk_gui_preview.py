#!/usr/bin/env python3
"""Tkinter desktop frontend for DotTalk++."""

from __future__ import annotations

import pathlib
import queue
import sys
import os
import tkinter as tk
from enum import Enum
from tkinter import filedialog, messagebox, ttk

from dottalk_gui_async import AsyncSession, EventKind, gui_data_root
from dottalk_gui_backend import (
    PythonArea,
    PythonIndexInfo,
    PythonRelationInfo,
    field_type_name,
    read_table_record,
)
from dottalk_gui_command_catalog import CommandAction, CommandActionKind, command_catalog
from dottalk_gui_workspace_format import format_workspace_graph_text
from gui_cli_bridge import run_cli_command
from dottalk_gui_text import (
    LocaleContext,
    available_gui_message_locales,
    locale_context_from_environment,
    locale_context_from_message_locale,
    render_label,
    text,
)

GUI_VERSION = "beta-0"


def _quote_command_path(path: pathlib.Path) -> str:
    text = str(path)
    if any(ch in text for ch in " \t"):
        return f'"{text}"'
    return text


def _workbench_title(locale: LocaleContext, display_name: str = "") -> str:
    title = f"{text('gui.app.title', locale)} {GUI_VERSION} Preview"
    if display_name:
        title += f" - {display_name}"
    return title


class WorkbenchPage(Enum):
    TABLES = "tables"
    INDEXES = "indexes"
    RELATIONS = "relations"
    WORKSPACE = "workspace"
    BROWSE = "browse"
    STRUCTURE = "structure"


def _looks_like_ersatz_output(output: str) -> bool:
    upper = output.upper()
    return (
        "ERSATZ" in upper
        or "REL ENUM" in upper
        or "REL LIST" in upper
        or "RELATIONS (TREE)" in upper
    )


def _parse_ersatz_result_rows(output: str) -> list[tuple[str, list[str]]]:
    if not _looks_like_ersatz_output(output):
        return []

    rows: list[tuple[str, list[str]]] = []
    section = "ERSATZ"
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "|" not in line:
            upper = line.upper()
            if (
                "REL ENUM" in upper
                or "REL LIST" in upper
                or "CURRENT STUDENT" in upper
                or "STUDENT" in upper
                or upper.startswith("WALK ")
            ):
                section = line
            continue

        values = [part.strip() for part in line.split("|")]
        values = [value for value in values if value]
        if len(values) >= 3:
            rows.append((section, values))
    return rows


class DotTalkPreview(tk.Tk):
    def __init__(self,
                 initial_path: pathlib.Path | None = None,
                 locale: LocaleContext | None = None) -> None:
        super().__init__()
        self.locale = locale or locale_context_from_environment()
        self.title(_workbench_title(self.locale))
        self.geometry("1120x720")
        self.minsize(820, 520)

        self.session = AsyncSession()
        self.status = tk.StringVar(value=text("gui.status.ready", self.locale))
        self.detail = tk.StringVar(value=text("gui.area.none_open", self.locale))
        self.record_status = tk.StringVar(value="Recno: none | Logical row: unavailable | Order: unavailable")
        self.current_area_id = 0
        self.workspace_areas: list[PythonArea] = []
        self.workspace_indexes: list[PythonIndexInfo] = []
        self.workspace_relations: list[PythonRelationInfo] = []
        self.current_snapshot: dict[str, object] = {}
        self.current_workspace_path: pathlib.Path | None = None
        self.scan_task_ids: set[int] = set()
        self.applying_snapshot = False
        self.language_var = tk.StringVar(value=self.locale.message_locale)
        self.open_button: ttk.Button | None = None
        self.refresh_button: ttk.Button | None = None
        self.close_button: ttk.Button | None = None
        self.command_label: ttk.Label | None = None
        self.command_entry: ttk.Entry | None = None
        self.command_history: list[str] = []
        self.command_history_index: int | None = None
        self.command_history_draft = ""
        self.run_button: ttk.Button | None = None
        self.area_label: ttk.Label | None = None
        self.notebook: ttk.Notebook | None = None
        self.catalog_actions = command_catalog()

        self._build_menu()
        self._build_layout()
        self.after(50, self._drain_events)
        if initial_path is not None:
            self.after(150, lambda: self._open_initial_path(initial_path))
        self.after(200, self._run_startup_scripts)

    def _build_menu(self) -> None:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(
            label=text("gui.action.open_table", self.locale) + "...",
            accelerator="Ctrl+O",
            command=self.open_table,
        )
        file_menu.add_command(
            label=text("gui.action.refresh_snapshot", self.locale),
            accelerator="F5",
            command=self.refresh_snapshot,
        )
        file_menu.add_command(
            label=text("gui.action.close_area", self.locale),
            accelerator="Ctrl+W",
            command=self.close_area,
        )
        file_menu.add_separator()
        file_menu.add_command(label=text("gui.action.exit", self.locale), command=self.destroy)

        workspace_menu = tk.Menu(menu, tearoff=False)
        workspace_menu.add_command(
            label="WORKSPACE OPEN Directory...",
            command=self.workspace_open_directory,
        )
        workspace_menu.add_command(
            label="WORKSPACE LOAD Schema...",
            command=self.workspace_load_runtime,
        )
        workspace_menu.add_command(
            label="WORKSPACE CLOSE",
            command=lambda: self._submit_visible_command("workspace close"),
        )
        workspace_menu.add_separator()
        workspace_menu.add_command(
            label="Load Workspace Schema...",
            command=self.load_workspace,
        )
        workspace_menu.add_command(
            label=text("gui.action.save_workspace", self.locale),
            command=self.save_workspace,
        )
        workspace_menu.add_command(
            label=text("gui.action.save_workspace_as", self.locale) + "...",
            command=self.save_workspace_as,
        )
        workspace_menu.add_separator()
        workspace_menu.add_command(label="Open Workspace Root...", command=self.open_workspace_root)
        workspace_menu.add_command(label="Path Roots...", command=lambda: self._submit_visible_command("paths"))
        workspace_menu.add_separator()
        workspace_menu.add_command(label="SET DBF...", command=lambda: self._submit_visible_command("set dbf"))
        workspace_menu.add_command(label="SET INDEX...", command=lambda: self._submit_visible_command("set index"))

        run_menu = tk.Menu(menu, tearoff=False)
        run_menu.add_command(label="SCAN...ENDSCAN...", command=self.run_scan_dialog)

        language_menu = tk.Menu(menu, tearoff=False)
        self.language_var.set(self.locale.message_locale)
        for locale_code, label_key in self._language_menu_items():
            language_menu.add_radiobutton(
                label=text(label_key, self.locale),
                value=locale_code,
                variable=self.language_var,
                command=lambda code=locale_code: self.set_language(code),
            )

        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label=text("gui.action.about", self.locale), command=self.show_about)

        menu.add_cascade(label=text("gui.menu.file", self.locale), menu=file_menu)
        menu.add_cascade(label=text("gui.menu.workspace", self.locale), menu=workspace_menu)
        menu.add_cascade(label="Run", menu=run_menu)
        for category in ("Table", "Record", "Index", "Lists", "Browse", "Rel", "Tuple", "Cmd"):
            category_menu = self._catalog_menu(menu, category)
            if category_menu.index("end") is not None:
                menu.add_cascade(label=category, menu=category_menu)
        menu.add_cascade(label=text("gui.menu.language", self.locale), menu=language_menu)
        menu.add_cascade(label=text("gui.menu.help", self.locale), menu=help_menu)
        self.config(menu=menu)
        self.bind("<Control-o>", lambda _event: self.open_table())
        self.bind("<F5>", lambda _event: self.refresh_snapshot())
        self.bind("<Control-w>", lambda _event: self.close_area())

    def _catalog_menu(self, parent: tk.Menu, category: str) -> tk.Menu:
        menu = tk.Menu(parent, tearoff=False)
        for action in self.catalog_actions:
            if action.category == category:
                menu.add_command(
                    label=action.label,
                    command=lambda selected=action: self._run_catalog_action(selected),
                )
        return menu

    def _run_catalog_action(self, action: CommandAction) -> None:
        if action.kind == CommandActionKind.INFO:
            messagebox.showinfo(action.label, action.note or action.label)
            return
        if action.kind == CommandActionKind.PREFILL:
            if self.command_entry is not None:
                self.command_entry.delete(0, tk.END)
                self.command_entry.insert(0, action.command)
                self.command_entry.icursor(tk.END)
                self.command_entry.focus_set()
            self.status.set(f"Ready: {action.command}")
            return
        if action.command.upper() == "RECORDVIEW":
            self.open_record_view()
            return
        self._submit_visible_command(action.command)

    def _build_layout(self) -> None:
        outer = ttk.Frame(self, padding=8)
        outer.pack(fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(outer)
        toolbar.pack(fill=tk.X)
        self.open_button = ttk.Button(toolbar, text=text("gui.action.open_table", self.locale), command=self.open_table)
        self.open_button.pack(side=tk.LEFT)
        self.refresh_button = ttk.Button(toolbar, text=text("gui.action.refresh", self.locale), command=self.refresh_snapshot)
        self.refresh_button.pack(side=tk.LEFT, padx=(6, 0))
        self.close_button = ttk.Button(toolbar, text=text("gui.action.close_area", self.locale), command=self.close_area)
        self.close_button.pack(side=tk.LEFT, padx=(6, 0))
        self.command_label = ttk.Label(toolbar, text=text("gui.label.command", self.locale))
        self.command_label.pack(side=tk.LEFT, padx=(12, 6))
        self.command_entry = ttk.Entry(toolbar)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.command_entry.bind("<Return>", lambda _event: self.run_command())
        self.command_entry.bind("<Up>", self._on_command_history_previous)
        self.command_entry.bind("<Down>", self._on_command_history_next)
        self.run_button = ttk.Button(toolbar, text=text("gui.action.run", self.locale), command=self.run_command)
        self.run_button.pack(side=tk.LEFT, padx=(6, 0))
        ttk.Label(toolbar, textvariable=self.detail).pack(side=tk.LEFT, padx=12)

        outer_panes = ttk.PanedWindow(outer, orient=tk.HORIZONTAL)
        outer_panes.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        area_frame = ttk.Frame(outer_panes)
        self.area_label = ttk.Label(area_frame, text=text("gui.label.areas", self.locale))
        self.area_label.pack(fill=tk.X)
        self.areas = tk.Listbox(area_frame, exportselection=False, width=30)
        self.areas.insert(tk.END, text("gui.area.none_open", self.locale))
        self.areas.bind("<<ListboxSelect>>", self._on_area_selected)
        self.areas.pack(fill=tk.BOTH, expand=True)
        outer_panes.add(area_frame, weight=1)

        panes = ttk.PanedWindow(outer_panes, orient=tk.VERTICAL)
        panes.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        outer_panes.add(panes, weight=5)

        self.notebook = ttk.Notebook(panes)

        tables_frame = ttk.Frame(self.notebook)
        self.tables_tree = ttk.Treeview(
            tables_frame,
            show="tree headings",
            columns=("area", "table", "records", "fields", "path"),
        )
        self._configure_model_tree(
            self.tables_tree,
            (("area", "Area", 64), ("table", "Table", 150), ("records", "Records", 90),
             ("fields", "Fields", 80), ("path", "Path", 520)),
        )
        tables_scroll = ttk.Scrollbar(tables_frame, orient=tk.VERTICAL, command=self.tables_tree.yview)
        self.tables_tree.configure(yscrollcommand=tables_scroll.set)
        self.tables_tree.grid(row=0, column=0, sticky="nsew")
        tables_scroll.grid(row=0, column=1, sticky="ns")
        tables_frame.columnconfigure(0, weight=1)
        tables_frame.rowconfigure(0, weight=1)
        self.notebook.add(tables_frame, text="Tables")

        indexes_frame = ttk.Frame(self.notebook)
        self.indexes_tree = ttk.Treeview(
            indexes_frame,
            show="tree headings",
            columns=("area", "table", "kind", "active", "direction", "tag", "tags", "backend", "container"),
        )
        self._configure_model_tree(
            self.indexes_tree,
            (("area", "Area", 64), ("table", "Table", 140), ("kind", "Kind", 80),
             ("active", "Active", 70), ("direction", "Direction", 80), ("tag", "Active Tag", 110),
             ("tags", "Tags", 240), ("backend", "Backend", 90), ("container", "Container", 480)),
        )
        index_scroll = ttk.Scrollbar(indexes_frame, orient=tk.VERTICAL, command=self.indexes_tree.yview)
        self.indexes_tree.configure(yscrollcommand=index_scroll.set)
        self.indexes_tree.grid(row=0, column=0, sticky="nsew")
        index_scroll.grid(row=0, column=1, sticky="ns")
        indexes_frame.columnconfigure(0, weight=1)
        indexes_frame.rowconfigure(0, weight=1)
        self.notebook.add(indexes_frame, text="Indexes")

        relations_frame = ttk.Frame(self.notebook)
        self.relations_tree = ttk.Treeview(
            relations_frame,
            show="tree headings",
            columns=("parent", "child", "parent_key", "child_key", "matches", "source"),
        )
        self._configure_model_tree(
            self.relations_tree,
            (("parent", "Parent", 130), ("child", "Child", 130), ("parent_key", "Parent Key", 120),
             ("child_key", "Child Key", 120), ("matches", "Matches", 90), ("source", "Source", 160)),
        )
        relation_scroll = ttk.Scrollbar(relations_frame, orient=tk.VERTICAL, command=self.relations_tree.yview)
        self.relations_tree.configure(yscrollcommand=relation_scroll.set)
        self.relations_tree.grid(row=0, column=0, sticky="nsew")
        relation_scroll.grid(row=0, column=1, sticky="ns")
        relations_frame.columnconfigure(0, weight=1)
        relations_frame.rowconfigure(0, weight=1)
        self.notebook.add(relations_frame, text="Relations")

        graph_frame = ttk.Frame(self.notebook)
        self.workspace_graph = tk.Text(graph_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        graph_scroll = ttk.Scrollbar(graph_frame, orient=tk.VERTICAL, command=self.workspace_graph.yview)
        self.workspace_graph.configure(yscrollcommand=graph_scroll.set)
        self.workspace_graph.grid(row=0, column=0, sticky="nsew")
        graph_scroll.grid(row=0, column=1, sticky="ns")
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(0, weight=1)
        self.notebook.add(graph_frame, text=text("gui.label.workspace_graph", self.locale))

        table_frame = ttk.Frame(self.notebook)
        self.tree = ttk.Treeview(table_frame, show="tree headings")
        self.tree.heading("#0", text="#")
        self.tree.column("#0", width=64, minwidth=48, stretch=False, anchor=tk.E)
        self.tree.tag_configure("deleted", foreground="#777777")
        self.tree.bind("<<TreeviewSelect>>", self._on_browse_row_selected)
        yscroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.notebook.add(table_frame, text=text("gui.tab.browse", self.locale))

        structure_frame = ttk.Frame(self.notebook)
        self.structure_tree = ttk.Treeview(
            structure_frame,
            show="tree headings",
            columns=("name", "type", "length", "decimals"),
        )
        self._configure_model_tree(
            self.structure_tree,
            (("name", "Field", 170), ("type", "Type", 140), ("length", "Length", 90),
             ("decimals", "Decimals", 90)),
        )
        structure_scroll = ttk.Scrollbar(structure_frame, orient=tk.VERTICAL, command=self.structure_tree.yview)
        self.structure_tree.configure(yscrollcommand=structure_scroll.set)
        self.structure_tree.grid(row=0, column=0, sticky="nsew")
        structure_scroll.grid(row=0, column=1, sticky="ns")
        structure_frame.columnconfigure(0, weight=1)
        structure_frame.rowconfigure(0, weight=1)
        self.notebook.add(structure_frame, text=text("gui.tab.structure", self.locale))
        panes.add(self.notebook, weight=4)
        self._update_workspace_graph()
        self._select_workbench_page(WorkbenchPage.WORKSPACE)

        log_frame = ttk.Frame(panes)
        self.log = tk.Text(log_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        self.log.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        panes.add(log_frame, weight=1)

        status_bar = ttk.Frame(outer)
        status_bar.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(status_bar, textvariable=self.status).pack(side=tk.LEFT)
        ttk.Label(status_bar, textvariable=self.record_status).pack(side=tk.RIGHT)

    def _language_menu_items(self) -> tuple[tuple[str, str], ...]:
        return (
            ("en-US", "gui.locale.en_us"),
            ("es", "gui.locale.es"),
            ("fr", "gui.locale.fr"),
            ("de", "gui.locale.de"),
            ("it", "gui.locale.it"),
        )

    def set_language(self, locale_code: str) -> None:
        normalized = locale_context_from_message_locale(locale_code)
        if normalized.message_locale not in available_gui_message_locales():
            return
        self.locale = normalized
        self._refresh_localized_chrome()

    def _refresh_localized_chrome(self) -> None:
        self._build_menu()
        display_name = str(self.current_snapshot.get("display_name", "") or "")
        self.title(_workbench_title(self.locale, display_name))
        if self.open_button is not None:
            self.open_button.configure(text=text("gui.action.open_table", self.locale))
        if self.refresh_button is not None:
            self.refresh_button.configure(text=text("gui.action.refresh", self.locale))
        if self.close_button is not None:
            self.close_button.configure(text=text("gui.action.close_area", self.locale))
        if self.command_label is not None:
            self.command_label.configure(text=text("gui.label.command", self.locale))
        if self.run_button is not None:
            self.run_button.configure(text=text("gui.action.run", self.locale))
        if self.area_label is not None:
            self.area_label.configure(text=text("gui.label.areas", self.locale))
        if self.notebook is not None:
            self._update_workbench_page_text()
        if not self.workspace_areas:
            self.areas.delete(0, tk.END)
            self.areas.insert(tk.END, text("gui.area.none_open", self.locale))
        if self.current_snapshot:
            self._set_snapshot_status(self.current_snapshot)
        else:
            self.status.set(text("gui.status.ready", self.locale))
            if self.current_area_id == 0:
                self.detail.set(text("gui.area.none_open", self.locale))
                self.record_status.set("Recno: none | Logical row: unavailable | Order: unavailable")
        self._update_workspace_graph()

    def _workbench_page_index(self, page: WorkbenchPage) -> int:
        if page == WorkbenchPage.TABLES:
            return 0
        if page == WorkbenchPage.INDEXES:
            return 1
        if page == WorkbenchPage.RELATIONS:
            return 2
        if page == WorkbenchPage.WORKSPACE:
            return 3
        if page == WorkbenchPage.BROWSE:
            return 4
        if page == WorkbenchPage.STRUCTURE:
            return 5
        return 0

    def _select_workbench_page(self, page: WorkbenchPage) -> None:
        if self.notebook is not None:
            self.notebook.select(self._workbench_page_index(page))

    def _update_workbench_page_text(self) -> None:
        if self.notebook is None:
            return
        self.notebook.tab(
            self._workbench_page_index(WorkbenchPage.TABLES),
            text="Tables",
        )
        self.notebook.tab(
            self._workbench_page_index(WorkbenchPage.INDEXES),
            text="Indexes",
        )
        self.notebook.tab(
            self._workbench_page_index(WorkbenchPage.RELATIONS),
            text="Relations",
        )
        self.notebook.tab(
            self._workbench_page_index(WorkbenchPage.WORKSPACE),
            text=text("gui.label.workspace_graph", self.locale),
        )
        self.notebook.tab(
            self._workbench_page_index(WorkbenchPage.BROWSE),
            text=text("gui.tab.browse", self.locale),
        )
        self.notebook.tab(
            self._workbench_page_index(WorkbenchPage.STRUCTURE),
            text=text("gui.tab.structure", self.locale),
        )

    def show_about(self) -> None:
        messagebox.showinfo(
            title=text("gui.about.title", self.locale),
            message=text("gui.about.body", self.locale),
        )

    def open_table(self) -> None:
        filename = filedialog.askopenfilename(
            title="Open DBF table",
            filetypes=[("DBF files", "*.dbf"), ("All files", "*.*")],
        )
        if filename:
            self._start_load(pathlib.Path(filename))

    def load_workspace(self) -> None:
        filename = filedialog.askopenfilename(
            title="Load workspace schema",
            filetypes=[("DotTalk++ schema", "*.dtschema *.dtschemas"), ("All files", "*.*")],
        )
        if filename:
            path = pathlib.Path(filename)
            self.current_workspace_path = path
            self._submit_visible_command(f"workspace load {_quote_command_path(path)}")

    def workspace_open_directory(self) -> None:
        directory = filedialog.askdirectory(title="WORKSPACE OPEN <dir>")
        if directory:
            options = self._workspace_open_options()
            if options is None:
                return
            parts = ["workspace", "open", str(pathlib.Path(directory))]
            if options["index_mode"]:
                parts.append(options["index_mode"])
            if options["fallback"]:
                parts.append("FALLBACK")
            if options["recursive"]:
                parts.append("recursive")
            if options["table"]:
                parts.append("TABLE")
            self._submit_visible_command(" ".join(parts))

    def _workspace_open_options(self) -> dict[str, object] | None:
        dialog = tk.Toplevel(self)
        dialog.title("WORKSPACE OPEN Options")
        dialog.geometry("420x260")
        dialog.transient(self)
        dialog.grab_set()

        body = ttk.Frame(dialog, padding=12)
        body.pack(fill=tk.BOTH, expand=True)
        ttk.Label(body, text="Index/key attachment").pack(anchor=tk.W)
        index_var = tk.StringVar(value="No indexes")
        index_combo = ttk.Combobox(
            body,
            textvariable=index_var,
            values=("No indexes", "CDX indexes", "CNX indexes", "INX indexes"),
            state="readonly",
        )
        index_combo.pack(fill=tk.X, pady=(4, 8))
        fallback_var = tk.BooleanVar(value=False)
        recursive_var = tk.BooleanVar(value=False)
        table_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(body, text="FALLBACK if requested indexes are missing", variable=fallback_var).pack(anchor=tk.W)
        ttk.Checkbutton(body, text="recursive directory scan", variable=recursive_var).pack(anchor=tk.W)
        ttk.Checkbutton(body, text="TABLE state for opened areas", variable=table_var).pack(anchor=tk.W)

        result: dict[str, object] | None = None

        def ok() -> None:
            nonlocal result
            index_map = {
                "No indexes": "",
                "CDX indexes": "CDX",
                "CNX indexes": "CNX",
                "INX indexes": "INX",
            }
            result = {
                "index_mode": index_map.get(index_var.get(), ""),
                "fallback": fallback_var.get(),
                "recursive": recursive_var.get(),
                "table": table_var.get(),
            }
            dialog.destroy()

        buttons = ttk.Frame(body)
        buttons.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(buttons, text="OK", command=ok).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=(0, 6))
        self.wait_window(dialog)
        return result

    def workspace_load_runtime(self) -> None:
        filename = filedialog.askopenfilename(
            title="Load workspace schema",
            filetypes=[("DotTalk++ workspace schemas", "*.dtschemas *.dtschema"), ("All files", "*.*")],
        )
        if filename:
            path = pathlib.Path(filename)
            self.current_workspace_path = path
            self._submit_visible_command(f"workspace load {_quote_command_path(path)}")

    def save_workspace(self) -> None:
        if self.current_workspace_path is None:
            self.save_workspace_as()
            return
        self._submit_visible_command(f"workspace save {_quote_command_path(self.current_workspace_path)}")

    def save_workspace_as(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Save workspace schema",
            defaultextension=".dtschema",
            filetypes=[("DotTalk++ schema", "*.dtschema"), ("All files", "*.*")],
        )
        if filename:
            path = pathlib.Path(filename)
            self.current_workspace_path = path
            self._submit_visible_command(f"workspace save {_quote_command_path(path)}")

    def open_workspace_root(self) -> None:
        root = gui_data_root() / "workspaces"
        try:
            os.startfile(root)  # type: ignore[attr-defined]
        except Exception:
            self._show_text_window("Workspace Root", str(root))

    def run_scan_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("SCAN...ENDSCAN")
        dialog.geometry("680x420")
        editor = tk.Text(dialog, wrap=tk.NONE)
        editor.insert("1.0", "DO X64\nUSE STUDENTS\nSCAN\n  TUPLE\n  SKIP\nENDSCAN\n")
        editor.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        buttons = ttk.Frame(dialog)
        buttons.pack(fill=tk.X, padx=8, pady=(0, 8))

        def run() -> None:
            command = editor.get("1.0", tk.END).strip()
            dialog.destroy()
            if not command:
                return
            self._log("> SCAN...ENDSCAN")
            task_id = self.session.submit_command(command)
            self.scan_task_ids.add(task_id)

        ttk.Button(buttons, text="Run", command=run).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=(0, 6))

    def open_record_view(self) -> None:
        area = self._current_area()
        if area is None:
            self._log("warning: " + text("gui.area.none_selected", self.locale))
            return
        recno = self._current_record_number(area)
        try:
            record = read_table_record(area.path, recno)
        except Exception as exc:  # noqa: BLE001 - GUI boundary reports failures as a dialog.
            messagebox.showerror("Record View", str(exc))
            return
        self._show_record_view_window(area, record)

    def _current_area(self) -> PythonArea | None:
        for area in self.workspace_areas:
            if area.area_id == self.current_area_id:
                return area
        return None

    def _current_record_number(self, area: PythonArea) -> int:
        current = int(self.current_snapshot.get("current_record_number", 0) or 0)
        if current > 0 and pathlib.Path(str(self.current_snapshot.get("path", ""))) == area.path:
            return current
        selection = self.tree.selection()
        if selection:
            try:
                parsed = int(str(self.tree.item(selection[0], "text")).lstrip("*"))
                if parsed > 0:
                    return parsed
            except ValueError:
                pass
        return max(1, int(getattr(area, "recno", 1) or 1))

    def _show_record_view_window(self, area: PythonArea, record: dict[str, object]) -> None:
        row = record.get("row", {})
        if not isinstance(row, dict):
            row = {}
        recno = int(row.get("record_number", 0) or 0)
        fields = [field for field in record.get("fields", []) if isinstance(field, dict)]
        values = list(row.get("values", []))

        window = tk.Toplevel(self)
        window.title(f"Record View - {area.display_name} #{recno}")
        window.geometry(self._record_view_geometry(fields))
        window.minsize(520, 360)

        header = ttk.Frame(window, padding=(10, 8))
        header.pack(fill=tk.X)
        ttk.Label(header, text=f"{area.display_name}", font=("", 11, "bold")).pack(side=tk.LEFT)
        ttk.Label(header, text=f"Record {recno} of {record.get('record_count', 0)}").pack(side=tk.RIGHT)

        canvas = tk.Canvas(window, highlightthickness=0)
        yscroll = ttk.Scrollbar(window, orient=tk.VERTICAL, command=canvas.yview)
        body = ttk.Frame(canvas, padding=(10, 6))
        body_id = canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=yscroll.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        def configure_body(_event: tk.Event) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def configure_canvas(event: tk.Event) -> None:
            canvas.itemconfigure(body_id, width=event.width)

        body.bind("<Configure>", configure_body)
        canvas.bind("<Configure>", configure_canvas)

        columns = self._record_view_column_count(fields)
        for index, field in enumerate(fields):
            value = values[index] if index < len(values) else ""
            group = ttk.LabelFrame(
                body,
                text=f"{field.get('name', '')} {field.get('type', '')}({field.get('length', '')},{field.get('decimals', '')})",
                padding=6,
            )
            row_index = index // columns
            col_index = index % columns
            group.grid(row=row_index, column=col_index, sticky="nsew", padx=4, pady=4)
            body.columnconfigure(col_index, weight=1)
            self._populate_record_field(group, field, str(value))

        footer = ttk.Frame(window, padding=(10, 8))
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(footer, text=f"backend {record.get('backend', '')}").pack(side=tk.LEFT)
        ttk.Button(footer, text="Close", command=window.destroy).pack(side=tk.RIGHT)

    def _record_view_geometry(self, fields: list[dict[str, object]]) -> str:
        total_width = sum(max(8, int(field.get("length", 10) or 10)) for field in fields)
        if total_width > 180 or len(fields) > 16:
            return "980x720"
        if total_width > 90 or len(fields) > 8:
            return "820x640"
        return "640x520"

    def _record_view_column_count(self, fields: list[dict[str, object]]) -> int:
        long_fields = sum(1 for field in fields if str(field.get("type", "")).upper() in {"M"} or int(field.get("length", 0) or 0) > 40)
        if long_fields:
            return 1
        if len(fields) >= 12:
            return 3
        if len(fields) >= 6:
            return 2
        return 1

    def _populate_record_field(self, parent: ttk.Frame, field: dict[str, object], value: str) -> None:
        field_type = str(field.get("type", "")).upper()
        field_length = int(field.get("length", 10) or 10)
        if field_type == "M" or field_length > 60 or len(value) > 80:
            widget = tk.Text(parent, height=min(8, max(3, (len(value) // 60) + 2)), wrap=tk.WORD)
            widget.insert("1.0", value)
            widget.configure(state=tk.DISABLED)
            widget.pack(fill=tk.BOTH, expand=True)
            return
        width = min(72, max(10, field_length + 2))
        text_value = tk.StringVar(value=value)
        entry = ttk.Entry(parent, textvariable=text_value, width=width, state="readonly")
        entry.pack(fill=tk.X, expand=True)

    def _submit_visible_command(self, command: str) -> None:
        self._log("> " + command)
        self.session.submit_command(command)

    def _run_startup_scripts(self) -> None:
        for script in self._existing_lifecycle_scripts(("init.ini", "dottalkpp.ini", "dotscript.ini")):
            self._log(f"startup script: {script}")
            self.session.submit_command(f"cli DOTSCRIPT {script}")

    def _run_shutdown_scripts(self) -> None:
        for script in self._existing_lifecycle_scripts(("shutdown.ini",)):
            run_cli_command(f"DOTSCRIPT {script}", None)

    def _existing_lifecycle_scripts(self, names: tuple[str, ...]) -> list[pathlib.Path]:
        data = gui_data_root()
        root = data.parent
        gui_bin = pathlib.Path(os.environ["DOTTALKPP_GUI_BIN"]) if os.environ.get("DOTTALKPP_GUI_BIN") else None
        found: list[pathlib.Path] = []
        for name in names:
            candidates: list[pathlib.Path] = []
            if gui_bin is not None:
                candidates.append(gui_bin / name)
            candidates.extend((
                data / name,
                root / "bin" / name,
                root / name,
                pathlib.Path.cwd() / name,
            ))
            for candidate in candidates:
                if candidate.is_file():
                    found.append(candidate.resolve())
                    break
        return found

    def _show_text_window(self, title: str, body: str) -> None:
        window = tk.Toplevel(self)
        window.title(title)
        window.geometry("820x520")
        text_box = tk.Text(window, wrap=tk.NONE)
        text_box.insert("1.0", body)
        text_box.configure(state=tk.DISABLED)
        text_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _show_ersatz_results_window(self, output: str) -> None:
        rows = _parse_ersatz_result_rows(output)
        if not rows:
            return

        value_columns = max(len(values) for _section, values in rows)
        window = tk.Toplevel(self)
        window.title("ERSATZ Result Browser")
        window.geometry("980x560")

        body = ttk.Frame(window, padding=8)
        body.pack(fill=tk.BOTH, expand=True)
        ttk.Label(body, text="ERSATZ relation/tuple results").pack(anchor=tk.W)

        columns = ("section",) + tuple(f"value_{index}" for index in range(1, value_columns + 1))
        result_frame = ttk.Frame(body)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        tree = ttk.Treeview(result_frame, show="tree headings", columns=columns)
        tree.heading("#0", text="#")
        tree.column("#0", width=52, minwidth=44, stretch=False, anchor=tk.E)
        tree.heading("section", text="Section")
        tree.column("section", width=260, minwidth=160, stretch=True)
        for index in range(1, value_columns + 1):
            key = f"value_{index}"
            tree.heading(key, text=f"Value {index}")
            tree.column(key, width=130, minwidth=80, stretch=True)

        xscroll = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=tree.xview)
        yscroll = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        for row_number, (section, values) in enumerate(rows, start=1):
            padded_values = values + [""] * (value_columns - len(values))
            tree.insert("", tk.END, text=str(row_number), values=(section, *padded_values))

        close_row = ttk.Frame(body)
        close_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(close_row, text="Close", command=window.destroy).pack(side=tk.RIGHT)

    def _open_initial_path(self, path: pathlib.Path) -> None:
        if not path.exists():
            self._log(f"warning: initial table not found: {path}")
            return
        self._start_load(path)

    def refresh_snapshot(self) -> None:
        if self.current_area_id == 0:
            self._log("warning: " + text("gui.area.none_selected", self.locale))
            return
        self.session.submit_table_snapshot(self.current_area_id)

    def close_area(self) -> None:
        if self.current_area_id == 0:
            self._log("warning: " + text("gui.area.none_selected", self.locale))
            return
        self.session.submit_close_area(self.current_area_id)

    def run_command(self) -> None:
        if self.command_entry is None:
            return
        command = self.command_entry.get().strip()
        if not command:
            self._log("warning: " + text("gui.command.empty", self.locale))
            return
        self._add_command_history(command)
        if command.upper() == "RECORDVIEW":
            self.command_entry.delete(0, tk.END)
            self.open_record_view()
            return
        self._log("> " + command)
        self.status.set(text("gui.status.running_command", self.locale))
        self.command_entry.delete(0, tk.END)
        self.session.submit_command(command)

    def _add_command_history(self, command: str) -> None:
        if not command:
            return
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)
        self.command_history_index = None
        self.command_history_draft = ""

    def _recall_command_history(self, direction: int) -> str:
        if self.command_entry is None or not self.command_history:
            return "break"

        if self.command_history_index is None:
            self.command_history_draft = self.command_entry.get()
            if direction > 0:
                return "break"
            self.command_history_index = len(self.command_history) - 1
        else:
            self.command_history_index += direction

        if self.command_history_index < 0 or self.command_history_index >= len(self.command_history):
            self.command_history_index = None
            value = self.command_history_draft
        else:
            value = self.command_history[self.command_history_index]

        self.command_entry.delete(0, tk.END)
        self.command_entry.insert(0, value)
        self.command_entry.icursor(tk.END)
        return "break"

    def _on_command_history_previous(self, _event: tk.Event) -> str:
        return self._recall_command_history(-1)

    def _on_command_history_next(self, _event: tk.Event) -> str:
        return self._recall_command_history(1)

    def _start_load(self, path: pathlib.Path) -> None:
        self.status.set(text("gui.status.opening_table", self.locale))
        self.detail.set(path.name)
        self._log(f"queued: {path}")
        self.session.submit_open_table(path)

    def _drain_events(self) -> None:
        while True:
            try:
                event = self.session.events.get_nowait()
            except queue.Empty:
                break

            if event.kind == EventKind.TASK_PROGRESS and event.progress:
                self.status.set(render_label(event.progress.label_code, event.progress.label, self.locale))
            elif event.kind == EventKind.OPEN_TABLE_FINISHED:
                area = event.payload
                if isinstance(area, PythonArea):
                    self.current_area_id = area.area_id
                    self.detail.set(area.display_name)
                    self._log(f"area {area.area_id - 1}: {area.path}")
            elif event.kind == EventKind.AREA_SELECTED:
                area = event.payload
                if isinstance(area, PythonArea):
                    self.current_area_id = area.area_id
                    self._apply_snapshot(area.snapshot)
            elif event.kind == EventKind.AREA_CLOSED:
                self.current_area_id = int(event.payload or 0)
                if self.current_area_id == 0:
                    self._apply_snapshot({})
            elif event.kind == EventKind.AREAS_LISTED:
                self._apply_areas(event.payload)
            elif event.kind == EventKind.TABLE_SNAPSHOT_READY:
                self._apply_snapshot(event.payload)
            elif event.kind == EventKind.COMMAND_FINISHED:
                output = str(event.payload)
                self._log(output)
                if event.task_id in self.scan_task_ids:
                    self.scan_task_ids.discard(event.task_id)
                    self._show_text_window("SCAN Results", output)
                self._show_ersatz_results_window(output)
            elif event.messages:
                self._log("; ".join(event.messages))

        self.after(50, self._drain_events)

    def _on_area_selected(self, _event: tk.Event) -> None:
        selection = self.areas.curselection()
        if not selection:
            return
        value = self.areas.get(selection[0])
        try:
            area_id = int(value.split()[0])
        except (ValueError, IndexError):
            return
        self.current_area_id = area_id
        self.session.submit_select_area(area_id)

    def _on_browse_row_selected(self, _event: tk.Event) -> None:
        if self.applying_snapshot or self.current_area_id == 0:
            return
        selection = self.tree.selection()
        if not selection:
            return
        recno = self.tree.item(selection[0], "text")
        try:
            parsed = int(str(recno).lstrip("*"))
        except ValueError:
            return
        if parsed > 0:
            self.session.submit_move_cursor(self.current_area_id, parsed)

    def _apply_areas(self, areas: object) -> None:
        self.areas.delete(0, tk.END)
        if isinstance(areas, dict):
            self.workspace_indexes = [
                index for index in areas.get("indexes", []) if isinstance(index, PythonIndexInfo)
            ]
            self.workspace_relations = [
                relation for relation in areas.get("relations", []) if isinstance(relation, PythonRelationInfo)
            ]
            self.current_area_id = int(areas.get("active_area_id", self.current_area_id) or 0)
            areas = areas.get("areas", [])
        else:
            self.workspace_indexes = []
            self.workspace_relations = []
        if not isinstance(areas, list) or not areas:
            self.workspace_areas = []
            self.areas.insert(tk.END, text("gui.area.none_open", self.locale))
            self._refresh_workspace_model_tabs()
            self._update_workspace_graph()
            return
        self.workspace_areas = [area for area in areas if isinstance(area, PythonArea)]
        for area in areas:
            if isinstance(area, PythonArea):
                self.areas.insert(tk.END, f"{area.area_id - 1}  {area.display_name}")
                if area.area_id == self.current_area_id:
                    self.areas.selection_clear(0, tk.END)
                    self.areas.selection_set(tk.END)
        self._refresh_workspace_model_tabs()
        self._update_workspace_graph()

    def destroy(self) -> None:
        self._run_shutdown_scripts()
        self.session.stop()
        super().destroy()

    def _apply_snapshot(self, snapshot: object) -> None:
        self.applying_snapshot = True
        data = snapshot if isinstance(snapshot, dict) else {}
        self.current_snapshot = data
        fields = list(data.get("fields", []))
        rows = list(data.get("rows", []))

        columns = [str(field["name"]) for field in fields]
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = columns
        self.tree.heading("#0", text="#")
        self.tree.column("#0", width=64, minwidth=48, stretch=False, anchor=tk.E)
        for name in columns:
            self.tree.heading(name, text=name)
            self.tree.column(name, width=110, stretch=True)

        current_record = int(data.get("current_record_number", 0) or 0)
        current_item = ""
        for row in rows:
            recno = str(row.get("record_number", ""))
            plain_recno = int(row.get("record_number", 0) or 0)
            tags = ()
            if row.get("deleted"):
                recno = f"*{recno}"
                tags = ("deleted",)
            values = list(row.get("values", []))
            item = self.tree.insert("", tk.END, text=recno, values=values, tags=tags)
            if plain_recno == current_record:
                current_item = item

        if current_item:
            self.tree.selection_set(current_item)
            self.tree.focus(current_item)
            self.tree.see(current_item)

        if not data:
            self.status.set(text("gui.status.ready", self.locale))
            self.detail.set(text("gui.area.none_open", self.locale))
            self.record_status.set("Recno: none | Logical row: unavailable | Order: unavailable")
            self.title(_workbench_title(self.locale))
            self._apply_structure(data)
            self._update_workspace_graph()
            self.applying_snapshot = False
            return

        self._apply_structure(data)
        self._set_snapshot_status(data)
        self.detail.set(
            f"{data.get('path')} | fields {len(fields)} | rec len {data.get('record_length')} | "
            f"backend {data.get('backend')}"
        )
        self.title(_workbench_title(self.locale, str(data.get("display_name", "") or "")))
        self._log(f"backend: {data.get('backend')}")
        for field in fields:
            self._log(
                f"field: {field['name']} {field_type_name(str(field['type']))}"
                f"({field['length']},{field['decimals']})"
            )
        self._update_workspace_graph()
        self.applying_snapshot = False

    def _set_snapshot_status(self, data: dict[str, object]) -> None:
        rows = list(data.get("rows", []))
        record_count = int(data.get("record_count", 0))
        truncated = " (truncated)" if data.get("truncated") else ""
        self.status.set(f"{len(rows)} {text('gui.status.rows_shown_of', self.locale)} {record_count}{truncated}")
        current_record = int(data.get("current_record_number", 0) or 0)
        logical_record = int(data.get("logical_record_number", 0) or 0)
        order_label = str(data.get("order_label", "") or "unavailable")
        if current_record > 0 and logical_record > 0:
            self.record_status.set(
                f"Recno: {current_record} | Logical row: {logical_record} | Order: {order_label}"
            )
        elif current_record > 0:
            self.record_status.set(
                f"Recno: {current_record} | Logical row: unavailable | Order: {order_label}"
            )
        else:
            self.record_status.set("Recno: none | Logical row: unavailable | Order: unavailable")

    def _apply_structure(self, data: dict[str, object]) -> None:
        if not hasattr(self, "structure_tree"):
            return
        self.structure_tree.delete(*self.structure_tree.get_children())
        fields = list(data.get("fields", [])) if data else []
        for row_number, field in enumerate(fields, start=1):
            self.structure_tree.insert(
                "",
                tk.END,
                text=str(row_number),
                values=(
                    str(field.get("name", "")),
                    field_type_name(str(field.get("type", ""))),
                    field.get("length", ""),
                    field.get("decimals", ""),
                ),
            )

    def _update_workspace_graph(self) -> None:
        if not hasattr(self, "workspace_graph"):
            return
        self.workspace_graph.configure(state=tk.NORMAL)
        self.workspace_graph.delete("1.0", tk.END)
        self.workspace_graph.insert(
            tk.END,
            format_workspace_graph_text(
                self.workspace_areas,
                self.current_area_id,
                text("gui.label.workspace_graph", self.locale),
                text("gui.area.none_open", self.locale),
                self.workspace_indexes,
                self.workspace_relations,
            ),
        )
        self.workspace_graph.configure(state=tk.DISABLED)

    def _configure_model_tree(self, tree: ttk.Treeview, columns: tuple[tuple[str, str, int], ...]) -> None:
        tree.heading("#0", text="#")
        tree.column("#0", width=48, minwidth=40, stretch=False, anchor=tk.E)
        for key, label, width in columns:
            tree.heading(key, text=label)
            tree.column(key, width=width, minwidth=48, stretch=True)

    def _refresh_workspace_model_tabs(self) -> None:
        if not hasattr(self, "tables_tree"):
            return
        self.tables_tree.delete(*self.tables_tree.get_children())
        for row_number, area in enumerate(self.workspace_areas, start=1):
            fields = list(area.snapshot.get("fields", []))
            self.tables_tree.insert(
                "",
                tk.END,
                text=str(row_number),
                values=(
                    area.area_id - 1,
                    area.display_name,
                    area.snapshot.get("record_count", 0),
                    len(fields),
                    str(area.path),
                ),
            )

        self.indexes_tree.delete(*self.indexes_tree.get_children())
        for row_number, index in enumerate(self.workspace_indexes, start=1):
            self.indexes_tree.insert(
                "",
                tk.END,
                text=str(row_number),
                values=(
                    index.area_id - 1,
                    index.area_name,
                    index.kind,
                    "yes" if index.active else "",
                    index.direction,
                    index.tag,
                    ", ".join(index.tags),
                    index.backend,
                    str(index.container or ""),
                ),
            )

        self.relations_tree.delete(*self.relations_tree.get_children())
        for row_number, relation in enumerate(self.workspace_relations, start=1):
            self.relations_tree.insert(
                "",
                tk.END,
                text=str(row_number),
                values=(
                    relation.parent,
                    relation.child,
                    relation.parent_key,
                    relation.child_key,
                    relation.match_count if relation.match_count else "",
                    relation.source,
                ),
            )

    def _log(self, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)


def main() -> None:
    initial_path: pathlib.Path | None = None
    locale = locale_context_from_environment()
    index = 1
    while index < len(sys.argv):
        arg = sys.argv[index]
        if arg.startswith("--locale="):
            locale = locale_context_from_message_locale(arg.split("=", 1)[1])
        elif arg == "--locale" and index + 1 < len(sys.argv):
            index += 1
            locale = locale_context_from_message_locale(sys.argv[index])
        elif initial_path is None:
            initial_path = pathlib.Path(arg)
        index += 1

    app = DotTalkPreview(initial_path, locale)
    app.mainloop()


if __name__ == "__main__":
    main()
