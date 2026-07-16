"""LabTalk Portal P0.

Small local campus launcher for LabTalk registries.
"""

from __future__ import annotations

import os
import json
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
TOOLS_ROOT = REPO_ROOT / "tools"
if TOOLS_ROOT.exists() and str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))
try:
    from version_info import title_with_version
except Exception:  # pragma: no cover - startup fallback
    def title_with_version(name: str, root: Path | None = None, fallback_version: str = "0.6") -> str:
        return name
REGISTRY_ROOT = LABTALK_ROOT / "registries"
PORTAL_REGISTRY = REGISTRY_ROOT / "portal.yaml"
LOCAL_CONFIG = LABTALK_ROOT / "labtalk.local.yaml"
LOCAL_CONFIG_EXAMPLE = LABTALK_ROOT / "labtalk.local.example.yaml"
DEFAULT_DOTTALKPP_EXE = REPO_ROOT / "dottalkpp" / "bin" / "dottalkpp.exe"
DEFAULT_DOTTALKPP_WORKDIR = REPO_ROOT
DEFAULT_PROOF_RUNS = LABTALK_ROOT / "proofs" / "runs"
DEFAULT_PORTAL_REPORTS = LABTALK_ROOT / "reports" / "portal"
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))
from ai_portal.audit_trail import audit_closeouts as audit_ai_report_closeouts

RUNNABLE_KINDS = {
    "dottalk_script",
    "dottalk_command",
    "powershell_launcher",
    "lab_script",
    "python_tool",
    "wsl_launcher",
}
DEFAULT_DOTSCRIPT_REJECT_OUTPUT_PATTERNS = (
    "Unknown command:",
    "DOTSCRIPT: script not found",
    "DOTSCRIPT: transcript open failed",
    "DOTSCRIPT: nesting limit reached",
)
CHECKED_PATH_FIELDS = ("path", "source", "root", "script")
CHECKED_LIST_PATH_FIELDS = ("related", "evidence", "docs", "launchers")
DERIVED_FROM_FIELD = "derived_from"


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


def normalize_path(value: str, base: Path | None = None) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (base or LABTALK_ROOT) / path
    return path


def display_path(path: Path) -> str:
    try:
        return str(path.resolve())
    except OSError:
        return str(path)


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


def item_relative_base(item: PortalItem, field: str) -> Path:
    if field in {"docs", "launchers"}:
        root_value = item.data.get("root")
        if isinstance(root_value, str) and root_value.strip():
            return normalize_path(root_value)
    return LABTALK_ROOT


def item_paths(item: PortalItem) -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = []
    for field in CHECKED_PATH_FIELDS:
        value = item.data.get(field)
        if isinstance(value, str) and value.strip():
            paths.append((field, normalize_path(value)))
    for field in CHECKED_LIST_PATH_FIELDS:
        value = item.data.get(field)
        if isinstance(value, list):
            for entry in value:
                if isinstance(entry, str) and entry.strip():
                    paths.append((field, normalize_path(entry, item_relative_base(item, field))))
    return paths


def derived_from_paths(item: PortalItem) -> list[Path]:
    """Return the source artifacts from which a generated item was derived."""
    value = item.data.get(DERIVED_FROM_FIELD)
    entries = value if isinstance(value, list) else [value]
    return [
        normalize_path(entry)
        for entry in entries
        if isinstance(entry, str) and entry.strip()
    ]


def first_openable_derived_from_path(item: PortalItem) -> Path | None:
    return next((path for path in derived_from_paths(item) if path.exists()), None)


def provenance_state(item: PortalItem) -> tuple[str, list[Path]]:
    """Validate diagram-level provenance without guessing missing sources."""
    if item.kind not in {"diagram", "image"} and not item.item_id.startswith("diagram."):
        return "", []
    sources = derived_from_paths(item)
    if not sources:
        return "provenance_missing", []
    artifact = first_openable_path(item)
    artifact_resolved = artifact.resolve() if artifact else None
    if artifact_resolved and any(source.resolve() == artifact_resolved for source in sources):
        return "provenance_partial", sources
    if any(not source.exists() for source in sources):
        return "provenance_target_missing", sources
    if item.data.get("public_url") and any(source.is_absolute() for source in sources):
        return "provenance_not_public_safe", sources
    return "provenance_ok", sources


def first_openable_path(item: PortalItem) -> Path | None:
    for _field, path in item_paths(item):
        if path.exists():
            return path
    return None


def item_truth_checks(item: PortalItem) -> list[str]:
    checks: list[str] = []
    paths = item_paths(item)
    if paths:
        for field, path in paths:
            state = "ok" if path.exists() else "missing"
            checks.append(f"{field}: {state} - {display_path(path)}")
    elif item.kind in RUNNABLE_KINDS and item.kind != "dottalk_command":
        checks.append("path: missing - runnable item has no checked path")

    if item.kind in RUNNABLE_KINDS:
        checks.append("runnable: registered")
    if item.data.get("proof") or item.data.get("proof_state") or item.section_id == "portal.proofs":
        checks.append("proof: linked")
    return checks


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

    checks = item_truth_checks(item)
    if checks:
        lines.extend(["", "Truth checks:"])
        for check in checks:
            lines.append(f"  - {check}")
    return "\n".join(lines).rstrip() + "\n"


def dottalk_paths(local_config: dict[str, Any]) -> tuple[Path, Path]:
    paths = local_config.get("paths", {}) if isinstance(local_config, dict) else {}
    exe_value = paths.get("dottalkpp_exe")
    workdir_value = paths.get("dottalkpp_workdir")
    exe = (
        normalize_path(str(exe_value), REPO_ROOT)
        if exe_value
        else DEFAULT_DOTTALKPP_EXE
    )
    workdir = (
        normalize_path(str(workdir_value), REPO_ROOT)
        if workdir_value
        else DEFAULT_DOTTALKPP_WORKDIR
    )
    return exe, workdir


def powershell_path(local_config: dict[str, Any]) -> str:
    tools = local_config.get("tools", {}) if isinstance(local_config, dict) else {}
    return str(tools.get("powershell", "powershell.exe"))


def python_path(local_config: dict[str, Any]) -> str:
    tools = local_config.get("tools", {}) if isinstance(local_config, dict) else {}
    return str(tools.get("python", sys.executable))


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


def configured_string_list(item: PortalItem, field: str) -> list[str]:
    value = item.data.get(field, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(
        isinstance(entry, str) and entry.strip() for entry in value
    ):
        raise ValueError(f"{field} must be a list of nonblank strings: {item.item_id}")
    return [entry.strip() for entry in value]


def output_acceptance_issues(item: PortalItem, stdout: str, stderr: str) -> list[str]:
    """Return proof-output failures that the process exit code cannot express."""
    combined = f"{stdout}\n{stderr}"
    case_sensitive = bool(item.data.get("output_patterns_case_sensitive", False))
    searchable = combined if case_sensitive else combined.casefold()

    required = configured_string_list(item, "required_output_patterns")
    rejected = configured_string_list(item, "reject_output_patterns")
    if item.kind == "dottalk_script" and bool(
        item.data.get("use_default_dotscript_reject_patterns", True)
    ):
        rejected = [*DEFAULT_DOTSCRIPT_REJECT_OUTPUT_PATTERNS, *rejected]

    issues: list[str] = []
    for pattern in required:
        needle = pattern if case_sensitive else pattern.casefold()
        if needle not in searchable:
            issues.append(f"required output missing: {pattern}")
    for pattern in dict.fromkeys(rejected):
        needle = pattern if case_sensitive else pattern.casefold()
        if needle in searchable:
            issues.append(f"rejected output present: {pattern}")
    return issues


def write_transcript(
    item: PortalItem,
    command_line: list[str],
    return_code: int,
    stdout: str,
    stderr: str,
    acceptance_issues: list[str] | None = None,
    process_return_code: int | None = None,
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
    ]
    if process_return_code is not None:
        body.append(f"process_return_code: {process_return_code}")
    if acceptance_issues is not None:
        body.extend(
            [
                f"output_acceptance: {'rejected' if acceptance_issues else 'accepted'}",
                "",
                "OUTPUT ACCEPTANCE",
                "=================",
                *(acceptance_issues or ["accepted"]),
            ]
        )
    body.extend(
        [
            "",
            "STDOUT",
            "======",
            stdout.rstrip() or "(none)",
            "",
            "STDERR",
            "======",
            stderr.rstrip() or "(none)",
        ]
    )
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path


def audit_portal() -> dict[str, Any]:
    sections, items = load_portal_items()
    ai_report_audit = audit_ai_report_closeouts(REPO_ROOT)
    seen: dict[str, int] = {}
    duplicates: list[str] = []
    missing_paths: list[dict[str, str]] = []
    runnable_count = 0
    proof_like_count = 0
    section_rows: list[dict[str, Any]] = []
    item_rows: list[dict[str, Any]] = []

    for section in sections:
        section_id = str(section.get("id", ""))
        registry_value = section.get("registry")
        registry_state = "inline"
        registry_path = ""
        if registry_value:
            resolved = normalize_path(str(registry_value))
            registry_path = display_path(resolved)
            registry_state = "ok" if resolved.exists() else "missing"
            if not resolved.exists():
                missing_paths.append(
                    {
                        "item_id": section_id,
                        "label": str(section.get("label", section_id)),
                        "field": "registry",
                        "path": registry_path,
                    }
                )
        section_rows.append(
            {
                "id": section_id,
                "label": str(section.get("label", section_id)),
                "registry_state": registry_state,
                "registry_path": registry_path,
            }
        )

    for item in items:
        seen[item.item_id] = seen.get(item.item_id, 0) + 1
        if seen[item.item_id] == 2:
            duplicates.append(item.item_id)
        if item.kind in RUNNABLE_KINDS:
            runnable_count += 1
        if item.data.get("proof") or item.data.get("proof_state") or item.section_id == "portal.proofs":
            proof_like_count += 1

        path_states: list[dict[str, str]] = []
        for field, path in item_paths(item):
            state = "ok" if path.exists() else "missing"
            row = {"field": field, "state": state, "path": display_path(path)}
            path_states.append(row)
            if state == "missing":
                missing_paths.append(
                    {
                        "item_id": item.item_id,
                        "label": item.label,
                        "field": field,
                        "path": row["path"],
                    }
                )

        item_rows.append(
            {
                "id": item.item_id,
                "label": item.label,
                "section": item.section_id,
                "kind": item.kind,
                "status": str(item.data.get("status", "")),
                "truth_state": str(item.data.get("truth_state", "")),
                "proof_state": str(item.data.get("proof_state", item.data.get("state", ""))),
                "paths": path_states,
                "runnable": item.kind in RUNNABLE_KINDS,
                "provenance_state": provenance_state(item)[0],
                "derived_from": [display_path(path) for path in provenance_state(item)[1]],
            }
        )

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "labtalk_root": display_path(LABTALK_ROOT),
        "repo_root": display_path(REPO_ROOT),
        "portal_registry": display_path(PORTAL_REGISTRY),
        "section_count": len(sections),
        "item_count": len(items),
        "runnable_count": runnable_count,
        "proof_like_count": proof_like_count,
        "duplicate_item_ids": duplicates,
        "missing_paths": missing_paths,
        "ai_report_audit": ai_report_audit,
        "sections": section_rows,
        "items": item_rows,
    }


def portal_audit_summary(audit: dict[str, Any]) -> str:
    return (
        f"sections={audit['section_count']} "
        f"items={audit['item_count']} "
        f"runnable={audit['runnable_count']} "
        f"proof_like={audit['proof_like_count']} "
        f"missing_paths={len(audit['missing_paths'])} "
        f"duplicate_ids={len(audit['duplicate_item_ids'])} "
        f"ai_report_findings={audit['ai_report_audit']['finding_count']}"
    )


def write_portal_audit(audit: dict[str, Any]) -> tuple[Path, Path]:
    DEFAULT_PORTAL_REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = DEFAULT_PORTAL_REPORTS / "portal_truth_audit_latest.json"
    md_path = DEFAULT_PORTAL_REPORTS / "portal_truth_audit_latest.md"

    json_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    lines = [
        "# LabTalk Portal Truth Audit",
        "",
        f"Generated: {audit['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Sections: {audit['section_count']}",
        f"- Items: {audit['item_count']}",
        f"- Runnable items: {audit['runnable_count']}",
        f"- Proof-like records: {audit['proof_like_count']}",
        f"- Missing paths: {len(audit['missing_paths'])}",
        f"- Duplicate item IDs: {len(audit['duplicate_item_ids'])}",
        f"- AI report audit findings: {audit['ai_report_audit']['finding_count']}",
        "",
        "## Missing Paths",
        "",
    ]
    if audit["missing_paths"]:
        lines.append("| Item | Field | Path |")
        lines.append("|---|---|---|")
        for row in audit["missing_paths"]:
            lines.append(f"| `{row['item_id']}` | `{row['field']}` | `{row['path']}` |")
    else:
        lines.append("No missing paths found.")

    lines.extend(["", "## Duplicate IDs", ""])
    if audit["duplicate_item_ids"]:
        for item_id in audit["duplicate_item_ids"]:
            lines.append(f"- `{item_id}`")
    else:
        lines.append("No duplicate item IDs found.")

    report_audit = audit["ai_report_audit"]
    lines.extend(
        [
            "",
            "## AI Report Identity and Provenance",
            "",
            f"- Schema: `{report_audit['schema']}`",
            f"- Enforced closeouts: {report_audit['enforced_count']}",
            f"- Valid closeouts: {report_audit['valid_count']}",
            f"- Grandfathered closeouts: {report_audit['grandfathered_count']}",
            f"- Findings: {report_audit['finding_count']}",
            "",
        ]
    )
    if report_audit["findings"]:
        lines.extend(["| Report | Field | Finding |", "|---|---|---|"])
        for finding in report_audit["findings"]:
            lines.append(
                f"| `{finding['report']}` | `{finding['field']}` | {finding['issue']} |"
            )
    else:
        lines.append("All enforced AI-authored closeouts have valid identity and provenance envelopes.")

    lines.extend(["", "## Sections", "", "| Section | Registry |", "|---|---|"])
    for section in audit["sections"]:
        registry = section["registry_state"]
        if section["registry_path"]:
            registry = f"{registry}: `{section['registry_path']}`"
        lines.append(f"| `{section['id']}` | {registry} |")

    lines.extend(["", "## Items", "", "| Item | Section | Kind | Paths |", "|---|---|---|---|"])
    for item in audit["items"]:
        path_text = "none"
        if item["paths"]:
            path_text = "<br>".join(
                f"`{row['field']}` {row['state']}: `{row['path']}`" for row in item["paths"]
            )
        lines.append(f"| `{item['id']}` | `{item['section']}` | `{item['kind']}` | {path_text} |")

    lines.extend(["", "## Diagram Provenance", "", "| Diagram | State | Sources |", "|---|---|---|"])
    provenance_items = [item for item in audit["items"] if item["provenance_state"]]
    if provenance_items:
        for item in provenance_items:
            sources = "<br>".join(f"`{source}`" for source in item["derived_from"]) or "none"
            lines.append(f"| `{item['id']}` | `{item['provenance_state']}` | {sources} |")
    else:
        lines.append("| none | `provenance_missing` | none |")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path, json_path


def run_item(item: PortalItem, local_config: dict[str, Any]) -> tuple[int, Path]:
    if item.kind not in RUNNABLE_KINDS:
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

    if item.kind == "python_tool":
        script_value = item.data.get("script")
        if not script_value:
            raise ValueError("python_tool item is missing script")
        script = normalize_path(str(script_value))
        if not script.exists():
            raise FileNotFoundError(str(script))
        arguments = item.data.get("arguments", [])
        if not isinstance(arguments, list) or not all(
            isinstance(argument, (str, int, float)) for argument in arguments
        ):
            raise ValueError("python_tool arguments must be a list of scalar values")
        command_line = [
            python_path(local_config),
            str(script),
            *(str(value) for value in arguments),
        ]
        result = subprocess.run(
            command_line,
            cwd=str(LABTALK_ROOT),
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
        acceptance_issues = output_acceptance_issues(item, result.stdout, result.stderr)
        return_code = result.returncode
        if acceptance_issues and return_code == 0:
            return_code = 3
        transcript = write_transcript(
            item,
            command_line,
            return_code,
            result.stdout,
            result.stderr,
            acceptance_issues=acceptance_issues,
            process_return_code=result.returncode,
        )
        return return_code, transcript
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
        self.title(title_with_version("LabTalk Portal", REPO_ROOT))
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
        self.open_source_button = ttk.Button(
            actions, text="Open source artifact", command=self._open_current_source
        )
        self.open_source_button.grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.run_button = ttk.Button(actions, text="Run", command=self._run_current)
        self.run_button.grid(row=0, column=2, sticky="w", padx=(6, 0))
        self.refresh_button = ttk.Button(actions, text="Refresh", command=self._refresh)
        self.refresh_button.grid(row=0, column=3, sticky="w", padx=(6, 0))
        self.audit_button = ttk.Button(actions, text="Audit", command=self._audit)
        self.audit_button.grid(row=0, column=4, sticky="w", padx=(6, 0))

        self.detail = tk.Text(right, wrap="word", width=64)
        self.detail.grid(row=1, column=0, sticky="nsew")
        self.detail.configure(state="disabled")

        self.status = ttk.Label(self, text="", anchor="w")
        self.status.grid(row=2, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 8))
        self._sync_action_buttons()

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
        self._sync_action_buttons()
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
        self._sync_action_buttons()
        self._set_status(f"Selected {self.current_item.item_id}")

    def _show_text(self, value: str) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", tk.END)
        self.detail.insert("1.0", value)
        self.detail.configure(state="disabled")

    def _set_status(self, value: str) -> None:
        self.status.configure(text=value)

    def _sync_action_buttons(self) -> None:
        item = self.current_item
        can_open = bool(item and first_openable_path(item))
        can_open_source = bool(item and first_openable_derived_from_path(item))
        can_run = bool(item and item.kind in RUNNABLE_KINDS)
        self.open_button.configure(state="normal" if can_open else "disabled")
        self.open_source_button.configure(state="normal" if can_open_source else "disabled")
        self.run_button.configure(state="normal" if can_run else "disabled")

    def _open_current(self) -> None:
        item = self.current_item
        if not item:
            return

        path = first_openable_path(item)
        if not path:
            self._set_status(f"No openable path for {item.item_id}")
            return

        try:
            open_path(path)
            self._set_status(f"Opened {path}")
        except Exception as exc:
            messagebox.showerror("Open failed", str(exc))
            self._set_status(f"Open failed: {exc}")

    def _open_current_source(self) -> None:
        item = self.current_item
        if not item:
            return

        paths = [path for path in derived_from_paths(item) if path.exists()]
        if not paths:
            self._set_status(f"No source artifact for {item.item_id}")
            return

        path = paths[0]
        if len(paths) > 1:
            chooser = tk.Toplevel(self)
            chooser.title("Choose source artifact")
            ttk.Label(chooser, text=f"Sources for {item.label}").pack(anchor="w", padx=12, pady=8)
            for source in paths:
                ttk.Button(
                    chooser,
                    text=display_path(source),
                    command=lambda selected=source, window=chooser: (open_path(selected), window.destroy()),
                ).pack(fill="x", padx=12, pady=3)
            return

        try:
            open_path(path)
            self._set_status(f"Opened source artifact {path}")
        except Exception as exc:
            messagebox.showerror("Open source artifact failed", str(exc))
            self._set_status(f"Open source artifact failed: {exc}")

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

        if item.kind not in RUNNABLE_KINDS:
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
            self._sync_action_buttons()
            self._set_status("Registries refreshed.")
        except Exception as exc:
            messagebox.showerror("Refresh failed", str(exc))
            self._set_status(f"Refresh failed: {exc}")

    def _audit(self) -> None:
        try:
            audit = audit_portal()
            md_path, json_path = write_portal_audit(audit)
            self._show_text(
                "Portal truth audit complete\n"
                "===========================\n\n"
                f"{portal_audit_summary(audit)}\n\n"
                f"Markdown: {md_path}\n"
                f"JSON: {json_path}\n"
            )
            self._set_status(f"Audit written: {md_path}")
        except Exception as exc:
            messagebox.showerror("Audit failed", str(exc))
            self._set_status(f"Audit failed: {exc}")


def main() -> int:
    if len(sys.argv) in {2, 3} and sys.argv[1] in {"--audit", "--audit-write"}:
        try:
            audit = audit_portal()
            print(portal_audit_summary(audit))
            if sys.argv[1] == "--audit-write":
                md_path, json_path = write_portal_audit(audit)
                print(f"markdown={md_path}")
                print(f"json={json_path}")
        except Exception as exc:
            print(f"Audit failed: {exc}", file=sys.stderr)
            return 1
        return 0

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
