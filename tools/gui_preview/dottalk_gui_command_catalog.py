"""Shared command catalog for the Python GUI preview.

This mirrors the C++ gui_command_catalog lane closely enough for Tkinter to
exercise the same workbench vocabulary as wx.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CommandActionKind(str, Enum):
    RUN = "run"
    PREFILL = "prefill"
    INFO = "info"


@dataclass(frozen=True)
class CommandAction:
    category: str
    label: str
    command: str
    kind: CommandActionKind = CommandActionKind.RUN
    note: str = ""


def command_catalog() -> tuple[CommandAction, ...]:
    return (
        CommandAction("Work", "Workspace Summary", "WORKSPACE"),
        CommandAction("Work", "Open DBF Workspace", "WORKSPACE OPEN DBF"),
        CommandAction("Work", "Open Workspace From Folder", "WORKSPACE OPEN ", CommandActionKind.PREFILL),
        CommandAction("Work", "Save Workspace", "WORKSPACE SAVE ", CommandActionKind.PREFILL),
        CommandAction("Work", "Load Workspace", "WORKSPACE LOAD ", CommandActionKind.PREFILL),
        CommandAction("Work", "Close Workspace", "WORKSPACE CLOSE"),
        CommandAction("Work", "Current Area", "AREA"),
        CommandAction("Work", "All DbAreas", "DBAREAS"),
        CommandAction("Work", "Workspace Report", "WSREPORT"),

        CommandAction("Table", "Structure", "STRUCT"),
        CommandAction("Table", "Fields", "FIELDS"),
        CommandAction("Table", "Table Status", "STATUS"),
        CommandAction("Table", "Metadata", "TABLEMETA"),
        CommandAction("Table", "Validate", "VALIDATE"),
        CommandAction("Table", "DDL", "DDL ", CommandActionKind.PREFILL),
        CommandAction("Table", "Show Internal State", "SHOW"),
        CommandAction("Table", "Buffering On", "TABLE ON"),
        CommandAction("Table", "Buffering Off", "TABLE OFF"),
        CommandAction("Table", "Show Stale Fields", "TABLE STALE"),
        CommandAction("Table", "Apply / Fresh", "TABLE FRESH ", CommandActionKind.PREFILL),
        CommandAction("Table", "Commit Changes", "COMMIT"),

        CommandAction("Record", "Record View", "RECORDVIEW"),
        CommandAction("Record", "Display Current", "DISPLAY"),
        CommandAction("Record", "Current Record Context", "RECORD"),
        CommandAction("Record", "Go To Record", "GOTO ", CommandActionKind.PREFILL),
        CommandAction("Record", "Top", "TOP"),
        CommandAction("Record", "Bottom", "BOTTOM"),
        CommandAction("Record", "Skip Forward", "SKIP 1"),
        CommandAction("Record", "Skip Back", "SKIP -1"),
        CommandAction("Record", "Append", "APPEND"),
        CommandAction("Record", "Append Blank", "APPEND_BLANK"),
        CommandAction("Record", "Edit", "EDIT"),
        CommandAction("Record", "Replace Field", "REPLACE ", CommandActionKind.PREFILL),
        CommandAction("Record", "Delete", "DELETE"),
        CommandAction("Record", "Recall", "RECALL"),
        CommandAction("Record", "Pack", "PACK"),
        CommandAction(
            "Record",
            "Zap All Records",
            "",
            CommandActionKind.INFO,
            "ZAP is destructive. Type ZAP manually when intentional.",
        ),
        CommandAction("Record", "Lock Record", "LOCK"),
        CommandAction("Record", "Unlock", "UNLOCK"),

        CommandAction("Index", "Set Index Container", "SET INDEX TO ", CommandActionKind.PREFILL),
        CommandAction("Index", "Set Order / Tag", "SET ORDER TO ", CommandActionKind.PREFILL),
        CommandAction("Index", "Physical Order", "SET ORDER TO 0"),
        CommandAction("Index", "Seek Key", "SEEK ", CommandActionKind.PREFILL),
        CommandAction("Index", "Find Key", "FIND ", CommandActionKind.PREFILL),
        CommandAction("Index", "IndexSeek", "INDEXSEEK ", CommandActionKind.PREFILL),
        CommandAction("Index", "Ascending", "ASCEND"),
        CommandAction("Index", "Descending", "DESCEND"),
        CommandAction("Index", "Reindex", "REINDEX"),
        CommandAction("Index", "Build LMDB-CDX", "BUILDLMDB"),
        CommandAction("Index", "CNX Container", "CNX ", CommandActionKind.PREFILL),
        CommandAction("Index", "CDX Diagnostics", "CDX ", CommandActionKind.PREFILL),
        CommandAction("Index", "LMDB Diagnostics", "LMDB ", CommandActionKind.PREFILL),

        CommandAction("Lists", "List Records", "LIST"),
        CommandAction("Lists", "List First 10", "LIST 10"),
        CommandAction("Lists", "SmartList", "SMARTLIST"),
        CommandAction("Lists", "SmartList FOR", "SMARTLIST 20 FOR ", CommandActionKind.PREFILL),
        CommandAction("Lists", "Display Current", "DISPLAY"),
        CommandAction("Lists", "Count", "COUNT FOR ", CommandActionKind.PREFILL),
        CommandAction("Lists", "Sum", "SUM ", CommandActionKind.PREFILL),
        CommandAction("Lists", "Average", "AVERAGE ", CommandActionKind.PREFILL),
        CommandAction("Lists", "WHERE / SQL-like Filter", "WHERE ", CommandActionKind.PREFILL),
        CommandAction("Lists", "Set Filter", "SET FILTER TO ", CommandActionKind.PREFILL),
        CommandAction("Lists", "Clear Filter", "SET FILTER TO"),
        CommandAction("Lists", "Predicate Help", "PREDHELP"),
        CommandAction("Lists", "Predicate Catalog", "PREDICATES"),

        CommandAction("Browse", "Browse Current Table", "BROWSE"),
        CommandAction("Browse", "Simple Browser", "SIMPLEBROWSER ", CommandActionKind.PREFILL),
        CommandAction("Browse", "Smart Browser", "SMARTBROWSER ", CommandActionKind.PREFILL),
        CommandAction("Browse", "Developer Browser", "BROWSER"),
        CommandAction("Browse", "Record View", "RECORDVIEW"),
        CommandAction("Browse", "Related Children", "SIMPLEBROWSER SHOW CHILDREN LIMIT 20", CommandActionKind.PREFILL),
        CommandAction("Browse", "Browse FOR", "SIMPLEBROWSER FOR ", CommandActionKind.PREFILL),
        CommandAction("Browse", "Browse ORDER", "SIMPLEBROWSER ORDER ", CommandActionKind.PREFILL),
        CommandAction("Browse", "ERSATZ Browser", "ERSATZ"),
        CommandAction("Browse", "ERSATZ Load", "ERSATZ LOAD"),
        CommandAction("Browse", "ERSATZ Demo Script", "DOTSCRIPT ersatz_browser"),
        CommandAction("Browse", "Relation Result Browser", "REL ENUM LIMIT 10"),
        CommandAction("Browse", "Relation List Browser", "REL LIST ALL"),

        CommandAction("Rel", "Set Relation", "SET RELATION TO ", CommandActionKind.PREFILL),
        CommandAction("Rel", "Set Relation Additive", "SET RELATION ADDITIVE TO ", CommandActionKind.PREFILL),
        CommandAction("Rel", "Relation Off Into", "SET RELATION OFF INTO ", CommandActionKind.PREFILL),
        CommandAction("Rel", "Clear Current Relations", "SET RELATION OFF ALL"),
        CommandAction("Rel", "Relation List", "REL LIST"),
        CommandAction("Rel", "Relation List All", "REL LIST ALL"),
        CommandAction("Rel", "Relation Refresh", "REL REFRESH"),
        CommandAction("Rel", "Add Native Relation", "REL ADD ", CommandActionKind.PREFILL),
        CommandAction("Rel", "Clear Native Relation", "REL CLEAR ", CommandActionKind.PREFILL),
        CommandAction("Rel", "Save Relations", "REL SAVE ", CommandActionKind.PREFILL),
        CommandAction("Rel", "Load Relations", "REL LOAD ", CommandActionKind.PREFILL),
        CommandAction("Rel", "Enumerate Relation Path", "REL ENUM LIMIT 10 ", CommandActionKind.PREFILL),

        CommandAction("Tuple", "Tuple All Fields", "TUPLE *"),
        CommandAction("Tuple", "Tuple Fields", "TUPLE ", CommandActionKind.PREFILL),
        CommandAction("Tuple", "Tuple From Area", "TUPLE #", CommandActionKind.PREFILL),
        CommandAction("Tuple", "Mixed-Area Tuple", "TUPLE #9.*,#11.LNAME", CommandActionKind.PREFILL),
        CommandAction("Tuple", "TupTalk", "TUPTALK ", CommandActionKind.PREFILL),
        CommandAction("Tuple", "Tuple Export", "TUPEXPORT ", CommandActionKind.PREFILL),
        CommandAction("Tuple", "Tuple Validate", "TUPVALIDATE"),

        CommandAction("Cmd", "Help", "HELP"),
        CommandAction("Cmd", "Fox Help", "FOXHELP"),
        CommandAction("Cmd", "Command Catalog", "CMDHELP"),
        CommandAction("Cmd", "Validate Command Catalog", "CMDHELPCHK"),
        CommandAction("Cmd", "Argument Parser Check", "CMDARGCHK"),
        CommandAction("Cmd", "Run DotScript", "DOTSCRIPT ", CommandActionKind.PREFILL),
        CommandAction("Cmd", "Test Harness", "TEST ", CommandActionKind.PREFILL),
        CommandAction("Cmd", "Set Variable", "SET VAR ", CommandActionKind.PREFILL),
        CommandAction("Cmd", "Force Set Variable", "SET VAR! ", CommandActionKind.PREFILL),
        CommandAction("Cmd", "SQL Version", "SQLVER"),
        CommandAction("Cmd", "Version", "VERSION"),
        CommandAction("Cmd", "GPS", "GPS"),
        CommandAction("Cmd", "SQLite Status", "SQLITE"),
        CommandAction("Cmd", "SQL Execute", "SQL ", CommandActionKind.PREFILL),
        CommandAction("Cmd", "SQL Select", "SQLSEL ", CommandActionKind.PREFILL),
    )
