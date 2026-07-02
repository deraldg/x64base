"""Compatibility bridge from the GUI preview to the DotTalk++ CLI executable."""

from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass


@dataclass
class CliResult:
    attempted: bool = False
    ok: bool = False
    exit_code: int = -1
    executable: pathlib.Path | None = None
    output: str = ""
    detail: str = ""


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


def _exe_name() -> str:
    return "dottalkpp.exe" if os.name == "nt" else "dottalkpp"


def _first_existing(paths: list[pathlib.Path]) -> pathlib.Path | None:
    for path in paths:
        try:
            if path.is_file():
                return path.resolve()
        except OSError:
            continue
    return None


def find_dottalkpp_executable() -> pathlib.Path | None:
    exe_name = _exe_name()
    candidates: list[pathlib.Path] = []
    for env_name in ("DOTTALKPP_GUI_CLI", "DOTTALKPP_EXE"):
        env_value = os.environ.get(env_name)
        if env_value:
            candidates.append(pathlib.Path(env_value))

    root = _repo_root()
    candidates.extend([
        root / "build" / "src" / "Release" / exe_name,
        root / "build-msvc" / "src" / "Release" / exe_name,
        root / "build-wx-fixed-local" / "src" / "Release" / exe_name,
        root / "build-wx-fixed-local" / "src" / "Debug" / exe_name,
        root / "build-gui-local" / "src" / "Release" / exe_name,
    ])
    return _first_existing(candidates)


def _first_token(command: str) -> str:
    return command.strip().split(maxsplit=1)[0].lower() if command.strip() else ""


def _should_seed_active_table(command: str) -> bool:
    return _first_token(command) not in {
        "",
        "help",
        "?",
        "about",
        "do",
        "dotscript",
        "workspace",
        "use",
        "close",
        "quit",
        "exit",
    }


def _script_path_usable(path: pathlib.Path) -> bool:
    return not any(ch in str(path) for ch in " \t\r\n\"'")


def _gui_data_root() -> pathlib.Path | None:
    for env_name in ("DOTTALKPP_DATA", "DOTTALK_DATA"):
        env_value = os.environ.get(env_name)
        if env_value:
            return pathlib.Path(env_value)
    root = _repo_root()
    for candidate in (root / "dottalkpp" / "data", root / "data", pathlib.Path.cwd()):
        try:
            if candidate.is_dir():
                return candidate.resolve()
        except OSError:
            continue
    return None


def run_cli_command(
    command: str,
    active_table_path: pathlib.Path | None = None,
    active_record_number: int = 0,
) -> CliResult:
    command = command.strip()
    if not command:
        return CliResult(detail="No CLI command text was provided.")
    exe = find_dottalkpp_executable()
    if exe is None:
        return CliResult(
            detail="DotTalk++ CLI bridge is not available. Set DOTTALKPP_GUI_CLI or DOTTALKPP_EXE to dottalkpp."
        )

    script = pathlib.Path(tempfile.gettempdir()) / (
        f"dottalk_gui_cli_{time.monotonic_ns()}_{threading.get_ident()}.dts"
    )
    try:
        lines: list[str] = []
        data_root = _gui_data_root()
        if data_root:
            if _script_path_usable(data_root):
                lines.append(f"SETPATH DATA {data_root}")
            else:
                lines.append("* GUI CLI bridge skipped DATA path seeding because the path needs shell quoting.")
        if active_table_path and _should_seed_active_table(command):
            if _script_path_usable(active_table_path):
                lines.append(f"USE {active_table_path} NOINDEX")
                if active_record_number > 0:
                    lines.append(f"GOTO {active_record_number}")
            else:
                lines.append("* GUI CLI bridge skipped active-table seeding because the path needs shell quoting.")
        lines.append(command)
        script.write_text("\n".join(lines) + "\n", encoding="utf-8")

        completed = subprocess.run(
            [str(exe), "--script", str(script)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        output = completed.stdout
        if completed.stderr:
            output += completed.stderr
        return CliResult(
            attempted=True,
            ok=completed.returncode == 0,
            exit_code=completed.returncode,
            executable=exe,
            output=output,
        )
    except Exception as exc:  # noqa: BLE001 - compatibility boundary reports failures as text.
        return CliResult(attempted=True, executable=exe, detail=str(exc))
    finally:
        try:
            script.unlink(missing_ok=True)
        except OSError:
            pass
