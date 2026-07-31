"""Runtime smoke DotScript generation for generated HELP candidates."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence, Any

FIELDS_BY_TABLE = {
    "HELP_ARTIFACTS": "ID,CATALOG,COMMAND,CMDKEY,OWNER,KIND,SOURCE,CONFID,SEVERITY,NAME,ORD,TEXT",
    "HELP_LINE": "LINEID,ARTID,TOPICKEY,CATALOG,TOPIC,KIND,SOURCE,CONFID,SEVERITY,NAME,ROLE,LINE_NO,PART_NO,TEXT",
    "HELP_SECTION": "SECTID,ARTID,TOPICID,TOPICKEY,KIND,SOURCE,CONFID,SEVERITY,NAME,ORD,NLINES",
    "HELP_TOPIC": "TOPICID,TOPICKEY,CATALOG,TOPIC,TOPICTYPE,STATUS,IMPLEMENT,SUPPORTED,PRIMARY,CONFID,TITLE,SUMMARY,SECTIONS,LINES",
}


def _require_real_recno(value: Any) -> int:
    if value is None or str(value).strip() in {"", "<n>"}:
        raise ValueError("runtime smoke requires a real physical recno, not a placeholder")
    recno = int(str(value).strip())
    if recno <= 0:
        raise ValueError(f"runtime smoke recno must be positive, got {recno}")
    return recno


def _dts_path(path: Path) -> str:
    return str(path)


def write_runtime_smoke(
    path: Path,
    *,
    repo_root: Path,
    smoke_rows: Sequence[Mapping[str, Any]],
    help_dbf: Path | None = None,
    help_indexes: Path | None = None,
) -> None:
    """Write a self-contained DotScript smoke file.

    This function intentionally avoids nested `DO cmdhelp`, package-local script
    shadowing, stdin pipeline assumptions, and placeholder recnos.
    """
    help_dbf = help_dbf or (repo_root / "dottalkpp" / "data" / "HELP")
    help_indexes = help_indexes or (repo_root / "dottalkpp" / "data" / "INDEXES" / "HELP")
    lines = [
        "ECHO OFF",
        "SET PAGING OFF",
        f"SETPATH DBF {_dts_path(help_dbf)}",
        f"SETPATH INDEXES {_dts_path(help_indexes)}",
        "WORKSPACE CLOSE",
        "WORKSPACE OPEN DBF",
        "WORKSPACE",
        "",
    ]
    for row in smoke_rows:
        table = str(row["table"]).upper()
        key = str(row.get("topic_key") or row.get("cmdkey") or row.get("key") or "")
        recno = _require_real_recno(row.get("recno"))
        fields = FIELDS_BY_TABLE.get(table)
        if not fields:
            raise ValueError(f"unsupported HELP smoke table: {table}")
        lines.extend([
            f"* generated HELP runtime smoke: {table} recno {recno} {key}",
            f"SELECT {table}",
            f"GOTO {recno}",
            f"TUP {fields}",
            "",
        ])
    lines.append("QUIT")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
