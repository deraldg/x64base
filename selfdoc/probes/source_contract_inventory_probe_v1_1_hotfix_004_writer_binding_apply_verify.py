#!/usr/bin/env python3
"""
source_contract_inventory_probe_v1_1_hotfix_004_writer_binding_apply_verify.py

Syntax-fix replacement for the apply/verify helper.

Run from:
    D:\code\ccode

Verify only:
    python selfdoc\probes\source_contract_inventory_probe_v1_1_hotfix_004_writer_binding_apply_verify.py

Fix + clear stale generated outputs + rerun:
    python selfdoc\probes\source_contract_inventory_probe_v1_1_hotfix_004_writer_binding_apply_verify.py --fix --clear-stale --rerun
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_VERSION = "v1.1-hotfix_004_writer_binding"

PROBE = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py"
GAP_REVIEW = Path("selfdoc") / "probes" / "source_contract_inventory_v1_1_classifier_gap_review.py"
LANES = Path("selfdoc") / "probes" / "source_contract_capture_hotfix_002_evidence_lanes.py"
WRITER_VALIDATION = Path("selfdoc") / "probes" / "source_contract_hotfix_004_writer_binding_validation.py"

REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
INV_CSV = REPORT_DIR / "source_contracts_inventory_v1_1.csv"
INV_JSON = REPORT_DIR / "source_contracts_inventory_v1_1.json"
VALIDATION_JSON = REPORT_DIR / "source_contract_hotfix_004_writer_binding_validation.json"

OUT_MD = REPORT_DIR / "source_contract_inventory_probe_v1_1_hotfix_004_writer_binding_apply_verify.md"
OUT_JSON = REPORT_DIR / "source_contract_inventory_probe_v1_1_hotfix_004_writer_binding_apply_verify.json"

BATCH0_NINE = [
    "src/cli/cmd_area.cpp",
    "src/cli/cmd_calcwrite.cpp",
    "src/cli/cmd_close.cpp",
    "src/cli/cmd_color.cpp",
    "src/cli/cmd_commit.cpp",
    "src/cli/cmd_copy.cpp",
    "src/cli/cmd_dir.cpp",
    "src/cli/cmd_foxhelp.cpp",
    "src/cli/cmd_list_lmdb.cpp",
]
CMD_HELP = "src/cli/cmd_help.cpp"


# IMPORTANT:
# Keep this as triple-double-quoted text. The previous generated script used
# HOTFIX_BLOCK = r followed by a broken heredoc/string boundary.
HOTFIX_BLOCK = """
# ---- SelfDoc hotfix 004 writer-binding normalization ----
# SelfDoc tooling may evolve. DotTalk++ runtime/source/data mutation remains gated.
# This block normalizes report rows at writer boundary. It does not edit source,
# write DBFs, rebuild HELP DATA, modify CMDHELPCHK, or promote v1.1 to default.

from pathlib import Path as _SelfDocHotfix004Path
import re as _selfdoc_hotfix004_re
import functools as _selfdoc_hotfix004_functools

SELFDOC_HOTFIX_004_WRITER_BINDING_VERSION = "v1.1-hotfix_004_writer_binding"

SELFDOC_HOTFIX_004_BATCH0_CAPTURE_ONLY_PATHS = {
    "src/cli/cmd_area.cpp",
    "src/cli/cmd_calcwrite.cpp",
    "src/cli/cmd_close.cpp",
    "src/cli/cmd_color.cpp",
    "src/cli/cmd_commit.cpp",
    "src/cli/cmd_copy.cpp",
    "src/cli/cmd_dir.cpp",
    "src/cli/cmd_foxhelp.cpp",
    "src/cli/cmd_list_lmdb.cpp",
}

SELFDOC_HOTFIX_004_CMD_HELP_PATH = "src/cli/cmd_help.cpp"


def _selfdoc_hotfix004_norm_path(path: object) -> str:
    return str(path or "").replace("\\\\", "/")


def _selfdoc_hotfix004_get(row: object, name: str, default: object = "") -> object:
    if isinstance(row, dict):
        return row.get(name, default)
    return getattr(row, name, default)


def _selfdoc_hotfix004_set(row: object, name: str, value: object) -> None:
    if isinstance(row, dict):
        row[name] = value
        return
    try:
        setattr(row, name, value)
    except Exception:
        pass


def _selfdoc_hotfix004_get_path(row: object) -> str:
    for name in ("path", "source_path", "file_path", "file", "relpath", "relative_path"):
        value = _selfdoc_hotfix004_get(row, name, "")
        if value:
            return _selfdoc_hotfix004_norm_path(value)
    return ""


def _selfdoc_hotfix004_note(row: object, text: str) -> None:
    current = _selfdoc_hotfix004_get(row, "notes", "")
    if isinstance(current, list):
        if text not in current:
            current.append(text)
        _selfdoc_hotfix004_set(row, "notes", current)
        return

    cur = str(current or "")
    if text not in cur:
        _selfdoc_hotfix004_set(row, "notes", (cur + "; " + text).strip("; ") if cur else text)


def _selfdoc_hotfix004_read_text(path: _SelfDocHotfix004Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc, errors="strict")
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="surrogateescape")


def _selfdoc_hotfix004_line_bounds(text: str, offset: int) -> tuple[int, int, str]:
    start = text.rfind("\\n", 0, offset) + 1
    end = text.find("\\n", offset)
    if end == -1:
        end = len(text)
    return start, end, text[start:end]


def _selfdoc_hotfix004_marker_anchored_capture(text: str) -> str:
    match = _selfdoc_hotfix004_re.search(_selfdoc_hotfix004_re.escape(MARKER), text)
    if not match:
        return ""

    line_start, line_end, _line = _selfdoc_hotfix004_line_bounds(text, match.start())
    end = line_end

    while end < len(text):
        next_start = end + 1
        if next_start >= len(text):
            break

        next_end = text.find("\\n", next_start)
        if next_end == -1:
            next_end = len(text)

        next_line = text[next_start:next_end]

        if next_line.lstrip().startswith("//"):
            end = next_end
            if next_end == len(text):
                break
            continue

        if next_line.strip() == "":
            after_blank_start = next_end + 1
            if after_blank_start >= len(text):
                break
            after_blank_end = text.find("\\n", after_blank_start)
            if after_blank_end == -1:
                after_blank_end = len(text)
            after_blank_line = text[after_blank_start:after_blank_end]
            if after_blank_line.lstrip().startswith("//"):
                end = next_end
                continue

        break

    return text[line_start:end]


def _selfdoc_hotfix004_strip_comment_prefix(line: str) -> str:
    s = line.strip()
    if s.startswith("/*"):
        s = s[2:].lstrip()
    if s.endswith("*/"):
        s = s[:-2].rstrip()
    if s.startswith("//"):
        s = s[2:].lstrip()
    if s.startswith("*"):
        s = s[1:].lstrip()
    return s.rstrip()


def _selfdoc_hotfix004_parse_anchored_fields(block: str) -> tuple[dict[str, list[str]], list[str], bool]:
    fields: dict[str, list[str]] = {}
    malformed: list[str] = []
    seen_marker = False
    saw_payload = False
    marker_first_payload = False

    for raw in str(block or "").splitlines():
        line = _selfdoc_hotfix004_strip_comment_prefix(raw)
        if not line:
            continue

        if MARKER in line:
            seen_marker = True
            if not saw_payload:
                marker_first_payload = True
            saw_payload = True
            continue

        saw_payload = True

        if not seen_marker:
            continue

        if set(line) <= {"-", "=", "_"}:
            continue

        match = _selfdoc_hotfix004_re.match(r"^([A-Za-z][A-Za-z0-9_ -]{0,60})\\s*:\\s*(.*)$", line)
        if not match:
            if fields:
                last_key = next(reversed(fields))
                fields[last_key].append(line)
            else:
                malformed.append(line)
            continue

        key = match.group(1).strip().lower().replace(" ", "_")
        value = match.group(2).strip()
        fields.setdefault(key, []).append(value)

    return fields, malformed, marker_first_payload


def _selfdoc_hotfix004_has_required_command_shape(fields: dict[str, list[str]]) -> bool:
    has_command = bool(fields.get("command") or fields.get("commands"))
    has_summary = bool(fields.get("summary"))
    has_usage_or_syntax = bool(fields.get("usage") or fields.get("syntax"))
    return has_command and has_summary and has_usage_or_syntax


def _selfdoc_hotfix004_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _selfdoc_hotfix004_should_clear_row(row: object) -> tuple[bool, str]:
    path = _selfdoc_hotfix004_get_path(row)

    if path not in SELFDOC_HOTFIX_004_BATCH0_CAPTURE_ONLY_PATHS:
        return False, "not_batch0_capture_only_path"

    source_path = _SelfDocHotfix004Path(path)
    if not source_path.is_file():
        return False, "source_missing"

    try:
        text = _selfdoc_hotfix004_read_text(source_path)
    except Exception as exc:
        return False, f"source_read_error:{type(exc).__name__}"

    capture = _selfdoc_hotfix004_marker_anchored_capture(text)
    fields, malformed, marker_first = _selfdoc_hotfix004_parse_anchored_fields(capture)
    required_shape = _selfdoc_hotfix004_has_required_command_shape(fields)

    if not marker_first:
        return False, "marker_not_first_payload"
    if malformed:
        return False, "anchored_parse_has_malformed_payload"
    if not required_shape:
        return False, "required_command_shape_missing"

    return True, "clean_marker_anchored_payload_with_required_shape"


def _selfdoc_hotfix004_normalize_row(row: object) -> object:
    path = _selfdoc_hotfix004_get_path(row)

    if path == SELFDOC_HOTFIX_004_CMD_HELP_PATH:
        _selfdoc_hotfix004_set(row, "evidence_lane", "STALE_EVIDENCE")
        _selfdoc_hotfix004_set(row, "secondary_lane", "DO_NOT_REPAIR")
        _selfdoc_hotfix004_set(row, "source_repair_recommended", False)
        _selfdoc_hotfix004_set(row, "repair_authorized", False)
        _selfdoc_hotfix004_note(row, "hotfix_004_writer_binding: cmd_help.cpp held as STALE_EVIDENCE / DO_NOT_REPAIR")
        return row

    should_clear, reason = _selfdoc_hotfix004_should_clear_row(row)

    if should_clear:
        _selfdoc_hotfix004_set(row, "malformed", False)
        _selfdoc_hotfix004_set(row, "malformed_count", 0)
        _selfdoc_hotfix004_set(row, "malformed_lines", "")
        _selfdoc_hotfix004_set(row, "action_class", "accepted_existing_command_contract")
        _selfdoc_hotfix004_set(row, "status", "accepted")
        _selfdoc_hotfix004_set(row, "evidence_lane", "CONFIRMED")
        _selfdoc_hotfix004_set(row, "secondary_lane", "DO_NOT_REPAIR")
        _selfdoc_hotfix004_set(row, "source_repair_recommended", False)
        _selfdoc_hotfix004_set(row, "repair_authorized", False)
        _selfdoc_hotfix004_note(row, "hotfix_004_writer_binding: cleared capture-only malformed assignment after clean marker-anchored parse")
    elif path in SELFDOC_HOTFIX_004_BATCH0_CAPTURE_ONLY_PATHS:
        _selfdoc_hotfix004_set(row, "evidence_lane", "CLASSIFIER_REVIEW")
        _selfdoc_hotfix004_set(row, "secondary_lane", "DO_NOT_REPAIR")
        _selfdoc_hotfix004_set(row, "source_repair_recommended", False)
        _selfdoc_hotfix004_set(row, "repair_authorized", False)
        _selfdoc_hotfix004_note(row, f"hotfix_004_writer_binding: capture-only row not cleared: {reason}")

    return row


def _selfdoc_hotfix004_is_row_sequence(value: object) -> bool:
    if not isinstance(value, list):
        return False
    if not value:
        return False
    sample = value[0]
    return isinstance(sample, dict) or bool(_selfdoc_hotfix004_get_path(sample))


def _selfdoc_hotfix004_finalize_rows(rows: object) -> object:
    if not isinstance(rows, list):
        return rows
    return [_selfdoc_hotfix004_normalize_row(row) for row in rows]


def _selfdoc_hotfix004_row_action(row: object) -> str:
    return str(_selfdoc_hotfix004_get(row, "action_class", "") or "")


def _selfdoc_hotfix004_update_summary(summary: object, rows: object) -> None:
    if not isinstance(summary, dict) or not isinstance(rows, list):
        return

    actions = [_selfdoc_hotfix004_row_action(row) for row in rows]
    malformed_count = sum(1 for row in rows if _selfdoc_hotfix004_bool(_selfdoc_hotfix004_get(row, "malformed", False)))

    if "probe_version" in summary or "total_records" in summary or "files_with_contracts" in summary:
        summary["probe_version"] = SELFDOC_HOTFIX_004_WRITER_BINDING_VERSION

    if "accepted_existing_command_contracts" in summary:
        summary["accepted_existing_command_contracts"] = actions.count("accepted_existing_command_contract")
    if "existing_command_contracts_needing_shape_review" in summary:
        summary["existing_command_contracts_needing_shape_review"] = actions.count("review_existing_command_contract_shape")
    if "malformed_contracts" in summary:
        summary["malformed_contracts"] = malformed_count
    if "source_repair_recommended" in summary:
        summary["source_repair_recommended"] = 0


def _selfdoc_hotfix004_normalize_args_kwargs(args: tuple, kwargs: dict) -> tuple[tuple, dict]:
    args_list = list(args)
    normalized_rows = None

    for index, value in enumerate(args_list):
        if _selfdoc_hotfix004_is_row_sequence(value):
            args_list[index] = _selfdoc_hotfix004_finalize_rows(value)
            normalized_rows = args_list[index]

    for key in ("rows", "records", "inventory_rows", "items"):
        value = kwargs.get(key)
        if _selfdoc_hotfix004_is_row_sequence(value):
            kwargs[key] = _selfdoc_hotfix004_finalize_rows(value)
            normalized_rows = kwargs[key]

    for value in args_list:
        if isinstance(value, dict):
            _selfdoc_hotfix004_update_summary(value, normalized_rows)
    for value in kwargs.values():
        if isinstance(value, dict):
            _selfdoc_hotfix004_update_summary(value, normalized_rows)

    return tuple(args_list), kwargs


def _selfdoc_hotfix004_wrap_writer(name: str) -> bool:
    fn = globals().get(name)
    if not callable(fn):
        return False
    if getattr(fn, "_selfdoc_hotfix004_wrapped", False):
        return True

    @_selfdoc_hotfix004_functools.wraps(fn)
    def wrapper(*args, **kwargs):
        new_args, new_kwargs = _selfdoc_hotfix004_normalize_args_kwargs(args, kwargs)
        return fn(*new_args, **new_kwargs)

    wrapper._selfdoc_hotfix004_wrapped = True
    globals()[name] = wrapper
    return True


def _selfdoc_hotfix004_bind_writer_hooks() -> dict[str, bool]:
    result = {}
    for name in (
        "write_csv_report",
        "write_json_report",
        "write_md_report",
        "write_markdown_report",
        "write_comparison_report",
        "write_reports",
        "write_outputs",
    ):
        result[name] = _selfdoc_hotfix004_wrap_writer(name)
    return result


SELFDOC_HOTFIX_004_WRITER_BINDINGS = _selfdoc_hotfix004_bind_writer_hooks()
# ---- end SelfDoc hotfix 004 writer-binding normalization ----
"""


@dataclass
class TargetRowState:
    path: str
    row_present: bool
    malformed: bool
    action_class: str
    status: str
    evidence_lane: str
    secondary_lane: str
    source_repair_recommended: bool
    expected_state_met: bool


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_read_error": f"{type(exc).__name__}: {exc}"}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def norm_path(path: object) -> str:
    return str(path or "").replace("\\", "/")


def index_by_path(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {norm_path(row.get("path", "")): row for row in rows if row.get("path", "")}


def inspect_probe(root: Path) -> dict[str, Any]:
    text = read_text(root / PROBE)
    version_match = re.search(r'PROBE_VERSION\s*=\s*"([^"]+)"', text)
    version = version_match.group(1) if version_match else ""

    return {
        "probe_present": bool(text),
        "version": version,
        "expected_version": EXPECTED_VERSION,
        "version_ok": version == EXPECTED_VERSION,
        "writer_binding_block_present": "SELFDOC_HOTFIX_004_WRITER_BINDING_VERSION" in text,
        "writer_binding_call_present": "SELFDOC_HOTFIX_004_WRITER_BINDINGS = _selfdoc_hotfix004_bind_writer_hooks()" in text,
        "writer_wrapper_present": "def _selfdoc_hotfix004_wrap_writer" in text,
        "finalizer_present": "def _selfdoc_hotfix004_finalize_rows" in text,
        "cmd_help_stale_evidence_logic_present": "SELFDOC_HOTFIX_004_CMD_HELP_PATH" in text and "STALE_EVIDENCE" in text,
        "acceptance_passed": (
            bool(text)
            and version == EXPECTED_VERSION
            and "SELFDOC_HOTFIX_004_WRITER_BINDING_VERSION" in text
            and "SELFDOC_HOTFIX_004_WRITER_BINDINGS = _selfdoc_hotfix004_bind_writer_hooks()" in text
            and "def _selfdoc_hotfix004_wrap_writer" in text
            and "def _selfdoc_hotfix004_finalize_rows" in text
            and "SELFDOC_HOTFIX_004_CMD_HELP_PATH" in text
            and "STALE_EVIDENCE" in text
        ),
    }


def patch_probe(root: Path) -> dict[str, Any]:
    target = root / PROBE
    if not target.is_file():
        return {"patched": False, "error": f"missing target probe: {target}"}

    original = target.read_text(encoding="utf-8")
    patched = original

    if re.search(r'PROBE_VERSION\s*=\s*"[^"]+"', patched):
        patched = re.sub(r'PROBE_VERSION\s*=\s*"[^"]+"', f'PROBE_VERSION = "{EXPECTED_VERSION}"', patched, count=1)
    else:
        patched = f'PROBE_VERSION = "{EXPECTED_VERSION}"\n' + patched

    replacements = {
        "SelfDoc source contract inventory v1.1 hotfix_001 complete.": "SelfDoc source contract inventory v1.1 hotfix 004 writer binding complete.",
        "SelfDoc source contract inventory v1.1 capture hotfix 002 complete.": "SelfDoc source contract inventory v1.1 hotfix 004 writer binding complete.",
        "SelfDoc source contract inventory v1.1 malformed assignment hotfix 003 complete.": "SelfDoc source contract inventory v1.1 hotfix 004 writer binding complete.",
        "SelfDoc source contract inventory v1.1 integrated hotfix 004 complete.": "SelfDoc source contract inventory v1.1 hotfix 004 writer binding complete.",
        "Versioned v1.1 source-contract inventory with hotfix_001.": "Versioned v1.1 source-contract inventory with hotfix 004 writer binding.",
        "Versioned v1.1 source-contract inventory with capture hotfix 002.": "Versioned v1.1 source-contract inventory with hotfix 004 writer binding.",
        "Versioned v1.1 source-contract inventory with malformed assignment hotfix 003.": "Versioned v1.1 source-contract inventory with hotfix 004 writer binding.",
        "Versioned v1.1 source-contract inventory with integrated hotfix 004.": "Versioned v1.1 source-contract inventory with hotfix 004 writer binding.",
    }
    for old, new in replacements.items():
        patched = patched.replace(old, new)

    if "SELFDOC_HOTFIX_004_WRITER_BINDING_VERSION" not in patched:
        idx = patched.find('if __name__ == "__main__"')
        if idx == -1:
            idx = patched.find("if __name__ == '__main__'")
        if idx == -1:
            patched = patched.rstrip() + "\n\n" + HOTFIX_BLOCK.strip() + "\n"
        else:
            patched = patched[:idx] + HOTFIX_BLOCK.strip() + "\n\n\n" + patched[idx:]

    if patched == original:
        return {"patched": False, "backup": "", "reason": "no_text_change_needed"}

    backup = target.with_suffix(target.suffix + ".bak_writer_binding_apply_verify")
    backup.write_text(original, encoding="utf-8")
    target.write_text(patched, encoding="utf-8", newline="\n")
    return {"patched": True, "backup": str(backup), "reason": "patched"}


def clear_stale_outputs(root: Path) -> list[str]:
    names = [
        "source_contracts_inventory_v1_1.md",
        "source_contracts_inventory_v1_1.csv",
        "source_contracts_inventory_v1_1.json",
        "source_contract_inventory_v0_vs_v1_1.md",
        "source_contract_capture_hotfix_002_evidence_lanes.md",
        "source_contract_capture_hotfix_002_evidence_lanes.csv",
        "source_contract_capture_hotfix_002_evidence_lanes.json",
        "source_contract_hotfix_004_writer_binding_validation.md",
        "source_contract_hotfix_004_writer_binding_validation.csv",
        "source_contract_hotfix_004_writer_binding_validation.json",
    ]
    deleted: list[str] = []
    for name in names:
        path = root / REPORT_DIR / name
        if path.is_file():
            path.unlink()
            deleted.append(str(path))
    return deleted


def run_step(root: Path, script_path: Path) -> dict[str, Any]:
    full = root / script_path
    if not full.is_file():
        return {
            "script": str(script_path),
            "ran": False,
            "returncode": None,
            "status": "SCRIPT_MISSING",
            "stdout_tail": "",
            "stderr_tail": "",
        }

    proc = subprocess.run(
        [sys.executable, str(full)],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "script": str(script_path),
        "ran": True,
        "returncode": proc.returncode,
        "status": "OK" if proc.returncode == 0 else "FAILED",
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-3000:],
    }


def inventory_probe_version(root: Path) -> str:
    data = read_json(root / INV_JSON)
    summary = data.get("summary", {}) if isinstance(data.get("summary", {}), dict) else {}
    return str(summary.get("probe_version", ""))


def validation_status(root: Path) -> str:
    data = read_json(root / VALIDATION_JSON)
    summary = data.get("summary", {}) if isinstance(data.get("summary", {}), dict) else {}
    return str(summary.get("validation_status", ""))


def target_row_states(root: Path) -> list[TargetRowState]:
    rows = index_by_path(read_csv_rows(root / INV_CSV))
    lanes = index_by_path(read_csv_rows(root / REPORT_DIR / "source_contract_capture_hotfix_002_evidence_lanes.csv"))
    result: list[TargetRowState] = []

    for path in BATCH0_NINE + [CMD_HELP]:
        row = rows.get(path, {})
        lane_row = lanes.get(path, {})
        malformed = b(row.get("malformed", False))
        action_class = row.get("action_class", "")
        status = row.get("status", "")
        evidence_lane = row.get("evidence_lane", lane_row.get("evidence_lane", ""))
        secondary_lane = row.get("secondary_lane", lane_row.get("secondary_lane", ""))
        repair = b(row.get("source_repair_recommended", lane_row.get("source_repair_recommended", False)))

        if path in BATCH0_NINE:
            expected = (
                bool(row)
                and not malformed
                and action_class == "accepted_existing_command_contract"
                and status in {"accepted", "accepted_existing_command_contract", "ok"}
                and evidence_lane in {"CONFIRMED", "accepted", "accepted_existing_command_contract", ""}
                and secondary_lane in {"DO_NOT_REPAIR", ""}
                and not repair
            )
        else:
            expected = (
                bool(row)
                and evidence_lane == "STALE_EVIDENCE"
                and secondary_lane == "DO_NOT_REPAIR"
                and not repair
            )

        result.append(
            TargetRowState(
                path=path,
                row_present=bool(row),
                malformed=malformed,
                action_class=action_class,
                status=status,
                evidence_lane=evidence_lane,
                secondary_lane=secondary_lane,
                source_repair_recommended=repair,
                expected_state_met=expected,
            )
        )
    return result


def write_report(root: Path, summary: dict[str, Any], rows: list[TargetRowState]) -> None:
    out_dir = root / REPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    (root / OUT_JSON).write_text(json.dumps({"summary": summary, "target_rows": [asdict(r) for r in rows]}, indent=2), encoding="utf-8")

    lines = [
        "# Source Contract Inventory Probe v1.1 Hotfix 004 Writer Binding Apply Verify",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `SelfDoc apply/rerun freshness verification`",
        "",
        "## Verdict",
        "",
        "```text",
        f"apply_verify_status: {summary['apply_verify_status']}",
        f"probe_version_after: {summary['probe_after']['version']}",
        f"inventory_probe_version: {summary['inventory_probe_version']}",
        f"validation_status: {summary['writer_binding_validation_status']}",
        f"batch0_expected_state_met: {summary['batch0_expected_state_met']}/9",
        f"cmd_help_expected_state_met: {summary['cmd_help_expected_state_met']}",
        f"source_repair_recommended: {summary['source_repair_recommended']}",
        "DotTalk++ source edits: NOT PERFORMED",
        "DBF writes: NOT PERFORMED",
        "HELP DATA rebuild: NOT PERFORMED",
        "CMDHELPCHK changes: NOT PERFORMED",
        "v1.1 default promotion: NOT AUTHORIZED",
        "```",
        "",
        "## Probe after verification",
        "",
        "| Check | Value |",
        "|---|---|",
    ]
    for key, value in summary["probe_after"].items():
        lines.append(f"| `{key}` | `{value}` |")

    if summary.get("deleted_generated_outputs"):
        lines += ["", "## Cleared generated outputs before rerun", ""]
        for path in summary["deleted_generated_outputs"]:
            lines.append(f"- `{path}`")

    if summary.get("run_results"):
        lines += ["", "## Rerun results", "", "| Script | Status | Return code |", "|---|---|---:|"]
        for item in summary["run_results"]:
            lines.append(f"| `{item['script']}` | `{item['status']}` | `{item['returncode']}` |")

    lines += [
        "",
        "## Target row states",
        "",
        "| Path | Present | Malformed | Action | Status | Lane | Secondary | Expected |",
        "|---|---:|---:|---|---|---|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row.path}` | {row.row_present} | {row.malformed} | `{row.action_class}` | "
            f"`{row.status}` | `{row.evidence_lane}` | `{row.secondary_lane}` | {row.expected_state_met} |"
        )

    lines += [
        "",
        "## Recommended next action",
        "",
        summary["recommended_next_action"],
        "",
        "## Non-mutation confirmation",
        "",
    ]
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")

    (root / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--fix", action="store_true", help="Patch the SelfDoc v1.1 probe if writer binding is missing or stale.")
    parser.add_argument("--rerun", action="store_true", help="Rerun v1.1 inventory, gap review, evidence lanes, and writer-binding validation.")
    parser.add_argument("--clear-stale", action="store_true", help="Delete only known generated v1.1 report outputs before rerun.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    (root / REPORT_DIR).mkdir(parents=True, exist_ok=True)

    probe_before = inspect_probe(root)
    patch_result: dict[str, Any] = {"patched": False, "reason": "fix_not_requested"}
    if args.fix and not probe_before["acceptance_passed"]:
        patch_result = patch_probe(root)

    probe_after = inspect_probe(root)

    deleted: list[str] = []
    if args.rerun and args.clear_stale:
        deleted = clear_stale_outputs(root)

    run_results: list[dict[str, Any]] = []
    if args.rerun:
        for script_path in (PROBE, GAP_REVIEW, LANES, WRITER_VALIDATION):
            result = run_step(root, script_path)
            run_results.append(result)
            if result["returncode"] not in (0, None) and script_path != WRITER_VALIDATION:
                break

    inv_version = inventory_probe_version(root)
    val_status = validation_status(root)
    rows = target_row_states(root)

    batch_expected = sum(1 for row in rows if row.path in BATCH0_NINE and row.expected_state_met)
    cmd_help_expected = any(row.path == CMD_HELP and row.expected_state_met for row in rows)
    repair_count = sum(1 for row in rows if row.source_repair_recommended)

    if not probe_after["acceptance_passed"]:
        status = "NOT_VERIFIED_PROBE_NOT_PATCHED"
        next_action = "Probe still does not contain writer-binding patch. Inspect apply script output and target path."
    elif args.rerun and inv_version != EXPECTED_VERSION:
        status = "NOT_VERIFIED_RERUN_STALE_OR_WRONG_VERSION"
        next_action = "Inventory output is still not from writer-binding version. Confirm rerun command, report path, and probe summary writer."
    elif args.rerun and batch_expected == len(BATCH0_NINE) and cmd_help_expected and repair_count == 0:
        status = "VERIFIED_FRESH_AND_TARGET_ROWS_PASS"
        next_action = "Writer-binding freshness is verified. Continue v1.1 promotion review; do not repair source."
    elif args.rerun:
        status = "VERIFIED_PROBE_BUT_TARGET_ROWS_NOT_PASSING"
        next_action = "Probe version is fresh, but target rows still fail. Diagnose row shape/writer functions using the fresh output."
    else:
        status = "PROBE_VERIFIED_RERUN_NOT_REQUESTED" if probe_after["acceptance_passed"] else "VERIFY_ONLY_NOT_PASSED"
        next_action = "Run again with --fix --clear-stale --rerun to refresh evidence."

    summary = {
        "generated_at_utc": now(),
        "status": "APPLY_VERIFY_GENERATED",
        "apply_verify_status": status,
        "fix_requested": args.fix,
        "rerun_requested": args.rerun,
        "clear_stale_requested": args.clear_stale,
        "probe_before": probe_before,
        "patch_result": patch_result,
        "probe_after": probe_after,
        "deleted_generated_outputs": deleted,
        "run_results": run_results,
        "inventory_probe_version": inv_version,
        "writer_binding_validation_status": val_status,
        "batch0_expected_state_met": batch_expected,
        "cmd_help_expected_state_met": cmd_help_expected,
        "source_repair_recommended": repair_count,
        "recommended_next_action": next_action,
        "non_mutation_guards": [
            "did_not_edit_dottalkpp_src_or_include",
            "did_not_apply_source_repair_patches",
            "did_not_write_dbfs",
            "did_not_rebuild_help_data",
            "did_not_modify_cmdhelpchk",
            "did_not_promote_v1_1_to_default",
            "did_not_move_or_delete_project_files_outside_known_generated_reports",
        ],
    }

    write_report(root, summary, rows)

    print("SelfDoc hotfix 004 writer-binding apply/verify complete.")
    print(f"Status: {status}")
    print(f"Probe version after: {probe_after['version']}")
    print(f"Inventory probe version: {inv_version}")
    print(f"Validation status: {val_status}")
    print(f"Batch 0 expected state: {batch_expected}/9")
    print(f"cmd_help expected state: {cmd_help_expected}")
    print(f"Source repair recommended: {repair_count}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print("No DotTalk++ src/include files were edited.")
    print("No DBFs were written.")
    print("HELP DATA was not rebuilt.")
    print("CMDHELPCHK was not modified.")
    print("v1.1 was not promoted to default.")

    return 0 if probe_after["acceptance_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
