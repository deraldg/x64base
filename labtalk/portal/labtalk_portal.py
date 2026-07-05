"""LabTalk Portal P0.

Small local campus launcher for LabTalk registries.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - visible startup failure
    raise SystemExit(f"PyYAML is required to run LabTalk Portal: {exc}") from exc


LABTALK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LABTALK_ROOT.parent
REGISTRY_ROOT = LABTALK_ROOT / "registries"
PORTAL_REGISTRY = REGISTRY_ROOT / "portal.yaml"
LOCAL_CONFIG = LABTALK_ROOT / "labtalk.local.yaml"
LOCAL_CONFIG_EXAMPLE = LABTALK_ROOT / "labtalk.local.example.yaml"
DEFAULT_DOTTALKPP_EXE = REPO_ROOT / "dottalkpp" / "bin" / "dottalkpp.exe"
DEFAULT_DOTTALKPP_WORKDIR = REPO_ROOT
DEFAULT_PROOF_RUNS = LABTALK_ROOT / "proofs" / "runs"


@dataclass
class PortalItem:
    section_id: str
    section_label: str
    item_id: str
    label: str
    kind: str
    data: dict[str, Any]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_local_config() -> dict[str, Any]:
    if LOCAL_CONFIG.exists():
        return load_yaml(LOCAL_CONFIG)
    if LOCAL_CONFIG_EXAMPLE.exists():
        return load_yaml(LOCAL_CONFIG_EXAMPLE)
    return {}


def normalize_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = LABTALK_ROOT / path
    return path


def windows_path_to_wsl(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    tail = resolved.as_posix()[2:] if resolved.drive else resolved.as_posix()
    if drive:
        return f"/mnt/{drive}{tail}"
    return tail


def open_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(str(path))
    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def slug(value: str) -> str:
    out = []
    for char in value.lower():
        if char.isalnum():
            out.append(char)
        elif char in {" ", ".", "_", "-"}:
            out.append("_")
    collapsed = "".join(out).strip("_")
    while "__" in collapsed:
        collapsed = collapsed.replace("__", "_")
    return collapsed or "labtalk_run"


def compact_scalar(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        return "{...}"
    return "" if value is None else str(value)


def render_details(item: PortalItem) -> str:
    lines = [
        item.label,
        "=" * len(item.label),
        "",
        f"ID: {item.item_id}",
        f"Section: {item.section_label}",
        f"Kind: {item.kind}",
        "",
    ]

    for key, value in item.data.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for sub_key, sub_value in value.items():
                lines.append(f"  {sub_key}: {compact_scalar(sub_value)}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for entry in value:
                lines.append(f"  - {compact_scalar(entry)}")
        else:
            lines.append(f"{key}: {compact_scalar(value)}")
    return "\n".join(lines).rstrip() + "\n"


def dottalk_paths(local_config: dict[str, Any]) -> tuple[Path, Path]:
    paths = local_config.get("paths", {}) if isinstance(local_config, dict) else {}
    exe = Path(str(paths.get("dottalkpp_exe", DEFAULT_DOTTALKPP_EXE)))
    workdir = Path(str(paths.get("dottalkpp_workdir", DEFAULT_DOTTALKPP_WORKDIR)))
    return exe, workdir


def powershell_path(local_config: dict[str, Any]) -> str:
    tools = local_config.get("tools", {}) if isinstance(local_config, dict) else {}
    return str(tools.get("powershell", "powershell.exe"))


def wsl_path(local_config: dict[str, Any]) -> str:
    tools = local_config.get("tools", {}) if isinstance(local_config, dict) else {}
    return str(tools.get("wsl", "wsl.exe"))


def wsl_command_line(item: PortalItem, local_config: dict[str, Any]) -> tuple[list[str], Path]:
    shell = str(item.data.get("shell", "bash"))
    distro = str(item.data.get("distro", "")).strip()
    workdir_value = item.data.get("workdir")
    script_value = item.data.get("script")
    command_value = item.data.get("command")

    if script_value:
        script_path = normalize_path(str(script_value))
        if not script_path.exists():
            raise FileNotFoundError(str(script_path))
        command = f"{shlex.quote(windows_path_to_wsl(script_path))}"
    else:
        command = str(command_value or "").strip()
        if not command:
            raise ValueError("wsl_launcher item is missing script or command")

    if workdir_value:
        workdir = normalize_path(str(workdir_value))
        command = f"cd {shlex.quote(windows_path_to_wsl(workdir))} && {command}"
    else:
        workdir = LABTALK_ROOT

    argv = [wsl_path(local_config)]
    if distro:
        argv.extend(["-d", distro])
    argv.extend(["-e", shell, "-lc", command])
    return argv, workdir


def proof_output_dir(item: PortalItem) -> Path:
    configured = item.data.get("proof_output_dir")
    if configured:
        return normalize_path(str(configured))
    return DEFAULT_PROOF_RUNS


def write_transcript(
    item: PortalItem,
    command_line: list[str],
    return_code: int,
    stdout: str,
    stderr: str,
) -> Path:
    out_dir = proof_output_dir(item)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"{stamp}_{slug(item.item_id)}.txt"
    body = [
        "LabTalk proof transcript",
        f"timestamp: {stamp}",
        f"item_id: {item.item_id}",
        f"label: {item.label}",
        f"kind: {item.kind}",
        f"command_line: {' '.join(command_line)}",
        f"return_code: {return_code}",
        "",
        "STDOUT",
        "======",
        stdout.rstrip(),
        "",
        "STDERR",
        "======",
        stderr.rstrip(),
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def run_item(item: PortalItem, local_config: dict[str, Any]) -> tuple[int, Path]:
    if item.kind not in {
        "dottalk_script",
        "dottalk_command",
        "powershell_launcher",
        "lab_script",
        "wsl_launcher",
    }:
        raise ValueError(f"Item is not runnable: {item.item_id}")

    if item.kind == "wsl_launcher":
        command_line, workdir = wsl_command_line(item, local_config)
        if bool(item.data.get("capture_output", False)):
            result = subprocess.run(
                command_line,
                cwd=str(workdir),
                capture_output=True,
                text=True,
                timeout=int(item.data.get("timeout_seconds", 300)),
            )
            transcript = write_transcript(
                item,
                command_line,
                result.returncode,
                result.stdout,
                result.stderr,
            )
            return result.returncode, transcript

        subprocess.Popen(command_line, cwd=str(workdir))
        transcript = write_transcript(
            item,
            command_line,
            0,
            f"Launched external WSL process for {item.item_id}",
            "",
        )
        return 0, transcript

    if item.kind in {"powershell_launcher", "lab_script"}:
        path_value = item.data.get("path")
        if item.kind == "lab_script":
            path_value = item.data.get("script", path_value)
        if not path_value:
            raise ValueError(f"{item.kind} item is missing path")
        script = normalize_path(str(path_value))
        if not script.exists():
            raise FileNotFoundError(str(script))
        command_line = [
            powershell_path(local_config),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ]
        if item.kind == "lab_script":
            result = subprocess.run(
                command_line,
                cwd=str(script.parent),
                capture_output=True,
                text=True,
                timeout=int(item.data.get("timeout_seconds", 120)),
            )
            transcript = write_transcript(
                item,
                command_line,
                result.returncode,
                result.stdout,
                result.stderr,
            )
            return result.returncode, transcript

        command_line.insert(1, "-NoExit")
        subprocess.Popen(command_line, cwd=str(script.parent))
        transcript = write_transcript(
            item,
            command_line,
            0,
            f"Launched external PowerShell process for {script}",
            "",
        )
        return 0, transcript

    exe, workdir = dottalk_paths(local_config)
    if not exe.exists():
        raise FileNotFoundError(f"DotTalk++ runtime not found: {exe}")

    temp_script: Path | None = None
    try:
        if item.kind == "dottalk_script":
            script_value = item.data.get("script")
            if not script_value:
                raise ValueError("dottalk_script item is missing script")
            script = normalize_path(str(script_value))
            if not script.exists():
                raise FileNotFoundError(str(script))
        else:
            command = str(item.data.get("command", "")).strip()
            if not command:
                raise ValueError("dottalk_command item is missing command")
            temp_dir = LABTALK_ROOT / "tmp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_script = temp_dir / f"{slug(item.item_id)}.dts"
            temp_script.write_text(f"{command}\nQUIT\n", encoding="ascii")
            script = temp_script

        command_line = [str(exe), "--script", str(script)]
        result = subprocess.run(
            command_line,
            cwd=str(workdir) if workdir.exists() else None,
            capture_output=True,
            text=True,
            timeout=60,
        )
        transcript = write_transcript(
            item,
            command_line,
            result.returncode,
            result.stdout,
            result.stderr,
        )
        return result.returncode, transcript
    finally:
        if temp_script and temp_script.exists():
            try:
                temp_script.unlink()
                temp_script.parent.rmdir()
            except OSError:
                pass


def registry_items(section: dict[str, Any]) -> list[dict[str, Any]]:
    registry_path = section.get("registry")
    if not registry_path:
        return list(section.get("items") or [])

    data = load_yaml(normalize_path(str(registry_path)))
    rows: list[dict[str, Any]] = []
    for value in data.values():
        if isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
    return rows


def load_portal_items() -> tuple[list[dict[str, Any]], list[PortalItem]]:
    portal = load_yaml(PORTAL_REGISTRY)
    sections = list(portal.get("sections") or [])
    items: list[PortalItem] = []

    for section in sections:
        if not isinstance(section, dict):
            continue
        section_id = str(section.get("id", "portal.unknown"))
        section_label = str(section.get("label", section_id))
        for row in registry_items(section):
            item_id = str(row.get("id", row.get("label", "unnamed")))
            label = str(row.get("label", row.get("name", row.get("title", item_id))))
            kind = str(row.get("kind", "registry_item"))
            items.append(
                PortalItem(
                    section_id=section_id,
                    section_label=section_label,
                    item_id=item_id,
                    label=label,
                    kind=kind,
                    data=dict(row),
                )
            )
    return sections, items


class LabTalkPortal(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("LabTalk Portal")
        self.geometry("1020x660")
        self.minsize(840, 520)

        self.sections, self.items = load_portal_items()
        self.local_config = load_local_config()
        self.items_by_section: dict[str, list[PortalItem]] = {}
        for item in self.items:
            self.items_by_section.setdefault(item.section_id, []).append(item)

        self.current_item: PortalItem | None = None

        self._build_ui()
        self._load_sections()
        self._set_status("Ready. Select a campus section.")

    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        title = ttk.Label(self, text="LabTalk Portal", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="ew", padx=12, pady=(10, 8))

        self.section_list = tk.Listbox(self, exportselection=False, width=24)
        self.section_list.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(0, 8))
        self.section_list.bind("<<ListboxSelect>>", self._on_section_selected)

        middle = ttk.Frame(self)
        middle.grid(row=1, column=1, sticky="nsew", padx=6, pady=(0, 8))
        middle.rowconfigure(1, weight=1)
        middle.columnconfigure(0, weight=1)

        self.item_heading = ttk.Label(middle, text="Items", font=("Segoe UI", 11, "bold"))
        self.item_heading.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        self.item_list = tk.Listbox(middle, exportselection=False)
        self.item_list.grid(row=1, column=0, sticky="nsew")
        self.item_list.bind("<<ListboxSelect>>", self._on_item_selected)

        right = ttk.Frame(self)
        right.grid(row=1, column=2, sticky="nsew", padx=(6, 12), pady=(0, 8))
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        actions = ttk.Frame(right)
        actions.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        actions.columnconfigure(2, weight=1)

        self.open_button = ttk.Button(actions, text="Open", command=self._open_current)
        self.open_button.grid(row=0, column=0, sticky="w")
        self.run_button = ttk.Button(actions, text="Run", command=self._run_current)
        self.run_button.grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.refresh_button = ttk.Button(actions, text="Refresh", command=self._refresh)
        self.refresh_button.grid(row=0, column=2, sticky="w", padx=(6, 0))

        self.detail = tk.Text(right, wrap="word", width=64)
        self.detail.grid(row=1, column=0, sticky="nsew")
        self.detail.configure(state="disabled")

        self.status = ttk.Label(self, text="", anchor="w")
        self.status.grid(row=2, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 8))

    def _load_sections(self) -> None:
        self.section_list.delete(0, tk.END)
        for section in self.sections:
            self.section_list.insert(tk.END, str(section.get("label", section.get("id", ""))))
        if self.sections:
            self.section_list.selection_set(0)
            self._on_section_selected()

    def _selected_section(self) -> dict[str, Any] | None:
        selection = self.section_list.curselection()
        if not selection:
            return None
        idx = int(selection[0])
        return self.sections[idx] if 0 <= idx < len(self.sections) else None

    def _on_section_selected(self, _event: Any = None) -> None:
        section = self._selected_section()
        self.item_list.delete(0, tk.END)
        self.current_item = None
        self._show_text("")
        if not section:
            return
        section_id = str(section.get("id", ""))
        label = str(section.get("label", section_id))
        self.item_heading.configure(text=label)
        items = self.items_by_section.get(section_id, [])
        for item in items:
            self.item_list.insert(tk.END, item.label)
        self._set_status(f"{label}: {len(items)} item(s)")
        if items:
            self.item_list.selection_set(0)
            self._on_item_selected()

    def _on_item_selected(self, _event: Any = None) -> None:
        section = self._selected_section()
        selection = self.item_list.curselection()
        if not section or not selection:
            return
        section_id = str(section.get("id", ""))
        items = self.items_by_section.get(section_id, [])
        idx = int(selection[0])
        if idx < 0 or idx >= len(items):
            return
        self.current_item = items[idx]
        self._show_text(render_details(self.current_item))
        self._set_status(f"Selected {self.current_item.item_id}")

    def _show_text(self, value: str) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", tk.END)
        self.detail.insert("1.0", value)
        self.detail.configure(state="disabled")

    def _set_status(self, value: str) -> None:
        self.status.configure(text=value)

    def _open_current(self) -> None:
        item = self.current_item
        if not item:
            return

        path_value = item.data.get("path") or item.data.get("source") or item.data.get("root")
        if path_value:
            try:
                path = normalize_path(str(path_value))
                open_path(path)
                self._set_status(f"Opened {path}")
            except Exception as exc:
                messagebox.showerror("Open failed", str(exc))
                self._set_status(f"Open failed: {exc}")
            return

        command = item.data.get("command")
        if command:
            messagebox.showinfo(
                "Runtime launch planned",
                f"Runtime command is registered but not executed in P0:\n\n{command}",
            )
            self._set_status(f"Runtime launch planned: {command}")
            return

        messagebox.showinfo("No action", "This item has no openable path or command yet.")

    def _dottalk_paths(self) -> tuple[Path, Path]:
        return dottalk_paths(self.local_config)

    def _proof_output_dir(self, item: PortalItem) -> Path:
        return proof_output_dir(item)

    def _write_transcript(
        self,
        item: PortalItem,
        command_line: list[str],
        return_code: int,
        stdout: str,
        stderr: str,
    ) -> Path:
        return write_transcript(item, command_line, return_code, stdout, stderr)

    def _run_current(self) -> None:
        item = self.current_item
        if not item:
            return

        if item.kind not in {
            "dottalk_script",
            "dottalk_command",
            "powershell_launcher",
            "lab_script",
            "wsl_launcher",
        }:
            messagebox.showinfo("Run unavailable", "This item is not a runtime launch target.")
            return

        if item.kind in {"powershell_launcher", "lab_script", "wsl_launcher"}:
            try:
                code, transcript = run_item(item, self.local_config)
                self._show_text(
                    f"{render_details(item)}\n\n"
                    f"Run complete\n"
                    f"============\n"
                    f"Return code: {code}\n"
                    f"Transcript: {transcript}\n"
                )
                self._set_status(f"Run complete: {item.label}")
            except Exception as exc:
                messagebox.showerror("Launch failed", str(exc))
                self._set_status(f"Launch failed: {exc}")
            return

        exe, workdir = self._dottalk_paths()
        if not exe.exists():
            messagebox.showerror(
                "DotTalk++ not found",
                f"Configured runtime does not exist:\n\n{exe}\n\n"
                "Create labtalk.local.yaml or edit labtalk.local.example.yaml.",
            )
            return

        temp_script: Path | None = None
        try:
            if item.kind == "dottalk_script":
                script_value = item.data.get("script")
                if not script_value:
                    raise ValueError("dottalk_script item is missing script")
                script = normalize_path(str(script_value))
                if not script.exists():
                    raise FileNotFoundError(str(script))
            else:
                command = str(item.data.get("command", "")).strip()
                if not command:
                    raise ValueError("dottalk_command item is missing command")
                temp_dir = LABTALK_ROOT / "tmp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_script = temp_dir / f"{slug(item.item_id)}.dts"
                temp_script.write_text(f"{command}\nQUIT\n", encoding="ascii")
                script = temp_script

            command_line = [str(exe), "--script", str(script)]
            self._set_status(f"Running {item.label}...")
            self.update_idletasks()
            result = subprocess.run(
                command_line,
                cwd=str(workdir) if workdir.exists() else None,
                capture_output=True,
                text=True,
                timeout=60,
            )
            transcript = self._write_transcript(
                item,
                command_line,
                result.returncode,
                result.stdout,
                result.stderr,
            )
            self._show_text(
                f"{render_details(item)}\n\n"
                f"Run complete\n"
                f"============\n"
                f"Return code: {result.returncode}\n"
                f"Transcript: {transcript}\n\n"
                f"Output preview\n"
                f"--------------\n"
                f"{result.stdout[-4000:]}"
            )
            self._set_status(f"Run complete. Transcript: {transcript}")
        except subprocess.TimeoutExpired as exc:
            messagebox.showerror("Run timed out", str(exc))
            self._set_status(f"Run timed out: {item.item_id}")
        except Exception as exc:
            messagebox.showerror("Run failed", str(exc))
            self._set_status(f"Run failed: {exc}")
        finally:
            if temp_script and temp_script.exists():
                try:
                    temp_script.unlink()
                    temp_script.parent.rmdir()
                except OSError:
                    pass

    def _refresh(self) -> None:
        try:
            self.sections, self.items = load_portal_items()
            self.local_config = load_local_config()
            self.items_by_section.clear()
            for item in self.items:
                self.items_by_section.setdefault(item.section_id, []).append(item)
            self._load_sections()
            self._set_status("Registries refreshed.")
        except Exception as exc:
            messagebox.showerror("Refresh failed", str(exc))
            self._set_status(f"Refresh failed: {exc}")


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--run-item":
        _, items = load_portal_items()
        item = next((candidate for candidate in items if candidate.item_id == sys.argv[2]), None)
        if not item:
            print(f"Unknown portal item: {sys.argv[2]}", file=sys.stderr)
            return 2
        try:
            code, transcript = run_item(item, load_local_config())
        except Exception as exc:
            print(f"Run failed: {exc}", file=sys.stderr)
            return 1
        print(f"return_code={code}")
        print(f"transcript={transcript}")
        return code

    try:
        app = LabTalkPortal()
    except Exception as exc:
        messagebox.showerror("LabTalk Portal startup failed", str(exc))
        return 1
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
