#!/usr/bin/env python3
"""
apply_source_contract_inventory_probe_v1_1_malformed_assignment_hotfix_003.py

REPORT_ONLY classifier/probe hotfix installer.

Patches only:
  selfdoc\probes\source_contract_inventory_probe_v1_1.py

Purpose:
  Fix the remaining malformed flag assignment problem after capture_hotfix_002.

Doctrine:
  SelfDoc reports are evidence, not verdicts.
  No auto-repair from classification only.

Behavior:
  - Keep marker-anchored capture.
  - Keep preamble as context/evidence, not contract payload.
  - Compute malformed status from marker-anchored contract payload.
  - Do not carry malformed=True from broad preamble capture when:
      marker is first payload line
      anchored parse has zero malformed lines
      required shape is present
  - Leave cmd_help.cpp hash/source freshness as STALE_EVIDENCE / DO_NOT_REPAIR in evidence lane reports.

Safety:
  Does not edit src\ or include\.
  Does not write DBFs.
  Does not modify CMDHELPCHK.
  Does not rebuild HELP DATA.
  Does not repair source headers.
  Does not move or delete files.
  Does not promote v1.1 to default.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TARGET = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py"
BACKUP = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py.bak_malformed_assignment_hotfix_003"

REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
OUT_MD = REPORT_DIR / "source_contract_inventory_probe_v1_1_malformed_assignment_hotfix_003_status.md"
OUT_JSON = REPORT_DIR / "source_contract_inventory_probe_v1_1_malformed_assignment_hotfix_003_status.json"

EXPECTED_VERSION = "v1.1-malformed_assignment_hotfix_003"


FIND_CONTRACT_BLOCKS_REPLACEMENT = r"""def find_contract_blocks(text: str) -> list[tuple[int, int, str]]:
    # Capture hotfix 002 / malformed-assignment hotfix 003:
    # - For line-comment contracts, the @dottalk.usage v1 marker line is the contract start.
    # - Contiguous // lines before the marker are optional preamble/context, not contract payload.
    # - Contiguous // lines after the marker remain part of the contract.
    # - Block comments are still captured as an enclosing block; parse_fields() ignores pre-marker payload.
    blocks: list[tuple[int, int, str]] = []

    for match in re.finditer(re.escape(MARKER), text):
        marker_start = match.start()

        block_start = text.rfind("/*", 0, marker_start)
        block_end = text.find("*/", match.end())
        if block_start != -1 and block_end != -1:
            prior_close = text.rfind("*/", 0, marker_start)
            if prior_close < block_start:
                end = block_end + 2
                blocks.append((block_start, end, text[block_start:end]))
                continue

        line_start = text.rfind("\\n", 0, marker_start) + 1
        line_end = text.find("\\n", marker_start)
        if line_end == -1:
            line_end = len(text)

        start = line_start
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

        blocks.append((start, end, text[start:end]))

    unique = {(s, e): b for s, e, b in blocks}
    return [(s, e, b) for (s, e), b in sorted(unique.items())]
"""


PARSE_FIELDS_REPLACEMENT = r"""def parse_fields(header_text: str) -> tuple[dict[str, list[str]], list[str]]:
    # Capture hotfix 002 / malformed-assignment hotfix 003:
    # - Lines before @dottalk.usage v1 are preamble/context, not payload.
    # - Preamble lines must not make the contract malformed.
    # - Field parsing begins only after the marker has been seen.
    # - Continuation lines after a parsed field are still attached to that field.
    fields: dict[str, list[str]] = {}
    malformed: list[str] = []
    seen_marker = False
    ignored_preamble_lines = 0

    for raw_line in header_text.splitlines():
        line = strip_comment_prefix(raw_line)

        if not line:
            continue

        if MARKER in line:
            seen_marker = True
            continue

        if not seen_marker:
            ignored_preamble_lines += 1
            continue

        if set(line) <= {"-", "=", "_"}:
            continue

        match = re.match(r"^([A-Za-z][A-Za-z0-9_ -]{0,60})\\s*:\\s*(.*)$", line)
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

    return fields, malformed
"""


HELPER_BLOCK = r"""
# ---- SelfDoc malformed-assignment hotfix 003 helpers ----
# These helpers are report-only classifier logic. They do not edit source.
# Doctrine: SelfDoc reports are evidence, not verdicts.

HOTFIX_003_BATCH0_CAPTURE_REVIEW_PATHS = {
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


def _hotfix003_norm_path(path: object) -> str:
    return str(path or "").replace("\\", "/")


def _hotfix003_has_required_shape(fields: dict[str, list[str]]) -> bool:
    # Command shape is satisfied by command/commands, summary, and usage OR syntax.
    if not isinstance(fields, dict):
        return False
    has_command = bool(fields.get("command") or fields.get("commands"))
    has_summary = bool(fields.get("summary"))
    has_usage_or_syntax = bool(fields.get("usage") or fields.get("syntax"))
    return has_command and has_summary and has_usage_or_syntax


def _hotfix003_marker_is_first_payload_line(header_text: str) -> bool:
    for raw_line in str(header_text or "").splitlines():
        line = strip_comment_prefix(raw_line)
        if not line:
            continue
        return MARKER in line
    return False


def _hotfix003_should_clear_malformed(path: object, header_text: str, fields: dict[str, list[str]], malformed_lines: list[str]) -> bool:
    # Do not carry malformed=True from broad preamble capture when marker-anchored
    # contract payload is clean and required shape is present.
    norm_path = _hotfix003_norm_path(path)
    if norm_path.endswith("cmd_help.cpp"):
        # cmd_help.cpp remains an evidence freshness/hash lane, not a source repair target.
        return False

    if norm_path not in HOTFIX_003_BATCH0_CAPTURE_REVIEW_PATHS:
        # Conservative first pass: only clear the already-reviewed Batch 0
        # capture-only false positives.
        return False

    if not _hotfix003_marker_is_first_payload_line(header_text):
        return False

    if malformed_lines:
        return False

    return _hotfix003_has_required_shape(fields)


def _hotfix003_apply_row(row: dict, header_text: str, fields: dict[str, list[str]], malformed_lines: list[str]) -> dict:
    # Normalize the row after normal classification, without authorizing source repair.
    if not isinstance(row, dict):
        return row

    path = _hotfix003_norm_path(row.get("path", ""))
    if _hotfix003_should_clear_malformed(path, header_text, fields, malformed_lines):
        row["malformed"] = False
        row["malformed_count"] = 0
        row["malformed_lines"] = ""
        row["evidence_lane"] = "CONFIRMED"
        row["secondary_lane"] = "DO_NOT_REPAIR"
        row["source_repair_recommended"] = False
        row["repair_authorized"] = False

        if row.get("action_class") == "review_existing_command_contract_shape":
            row["action_class"] = "accepted_existing_command_contract"

        if row.get("status") in {"shape_review", "review", "malformed"}:
            row["status"] = "accepted"

        notes = str(row.get("notes", "") or "")
        add = "hotfix_003: cleared capture-only malformed flag after marker-anchored clean parse"
        row["notes"] = (notes + "; " + add).strip("; ") if notes else add

    elif path.endswith("cmd_help.cpp"):
        row["evidence_lane"] = "STALE_EVIDENCE"
        row["secondary_lane"] = "DO_NOT_REPAIR"
        row["source_repair_recommended"] = False
        row["repair_authorized"] = False

    return row
# ---- end SelfDoc malformed-assignment hotfix 003 helpers ----
"""


def function_span(text: str, func_name: str) -> tuple[int, int] | None:
    match = re.search(rf"^def {re.escape(func_name)}\(.*?$", text, flags=re.MULTILINE)
    if not match:
        return None
    start = match.start()
    next_match = re.search(r"^def [A-Za-z_][A-Za-z0-9_]*\(.*?$", text[match.end():], flags=re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(text)
    return start, end


def replace_function(text: str, func_name: str, replacement: str) -> tuple[str, bool]:
    span = function_span(text, func_name)
    if span is None:
        raise SystemExit(f"Could not find function: {func_name}")
    start, end = span
    new_text = text[:start] + replacement.rstrip() + "\n\n\n" + text[end:].lstrip("\n")
    return new_text, new_text != text


def insert_helper_block(text: str) -> tuple[str, bool]:
    if "_hotfix003_apply_row" in text:
        return text, False

    # Prefer insertion before classify functions, otherwise before main.
    for anchor in ("def classify_", "def build_", "def main("):
        idx = text.find(anchor)
        if idx != -1:
            return text[:idx] + HELPER_BLOCK.strip() + "\n\n\n" + text[idx:], True

    return text.rstrip() + "\n\n" + HELPER_BLOCK.strip() + "\n", True


def patch_known_row_patterns(text: str) -> tuple[str, int]:
    """Inject _hotfix003_apply_row near common row-construction return patterns.

    The v1.1 probe has changed over several generated versions, so this is deliberately
    conservative. If no known pattern is found, the patch still installs helpers and
    parse/capture fixes, and the validation report will expose that the row hook is missing.
    """
    count = 0

    # Pattern A: return row after fields/malformed are in scope.
    pattern = r"(\n\s*)return row(\s*\n)"
    if "_hotfix003_apply_row(row" not in text:
        def repl(match: re.Match[str]) -> str:
            nonlocal count
            indent = match.group(1)
            # Only inject into the first few return row sites; avoid infinite broad changes.
            if count >= 2:
                return match.group(0)
            count += 1
            return (
                f"{indent}row = _hotfix003_apply_row(row, header_text if 'header_text' in locals() else header, "
                f"fields if 'fields' in locals() else {{}}, malformed if 'malformed' in locals() else "
                f"(malformed_lines if 'malformed_lines' in locals() else []))"
                f"{indent}return row{match.group(2)}"
            )
        text = re.sub(pattern, repl, text)

    # Pattern B: rows.append(row)
    if "_hotfix003_apply_row(row" not in text:
        pattern_b = r"(\n\s*)rows\.append\(row\)"
        def repl_b(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            indent = match.group(1)
            return (
                f"{indent}row = _hotfix003_apply_row(row, header_text if 'header_text' in locals() else header, "
                f"fields if 'fields' in locals() else {{}}, malformed if 'malformed' in locals() else "
                f"(malformed_lines if 'malformed_lines' in locals() else []))"
                f"{indent}rows.append(row)"
            )
        text = re.sub(pattern_b, repl_b, text, count=1)

    return text, count


def inspect_probe_text(text: str) -> dict[str, Any]:
    version_match = re.search(r'PROBE_VERSION\s*=\s*"([^"]+)"', text)
    version = version_match.group(1) if version_match else ""

    find_span = function_span(text, "find_contract_blocks")
    parse_span = function_span(text, "parse_fields")
    find_fn = text[find_span[0]:find_span[1]] if find_span else ""
    parse_fn = text[parse_span[0]:parse_span[1]] if parse_span else ""

    anchors = (
        ('line_start = text.rfind("\\\\n", 0, marker_start) + 1' in find_fn)
        or ('line_start = text.rfind("\\n", 0, marker_start) + 1' in find_fn)
    ) and "start = line_start" in find_fn and "while start > 0" not in find_fn

    parse_seen = "seen_marker = False" in parse_fn and "if MARKER in line" in parse_fn
    parse_ignores = "if not seen_marker" in parse_fn and "ignored_preamble_lines" in parse_fn
    markers_present = "hotfix 003" in text.lower() or "malformed-assignment hotfix 003" in text.lower()
    helper_present = "_hotfix003_apply_row" in text
    row_hook_present = "row = _hotfix003_apply_row" in text

    passed = (
        version == EXPECTED_VERSION
        and bool(find_fn)
        and bool(parse_fn)
        and anchors
        and parse_seen
        and parse_ignores
        and markers_present
        and helper_present
        and row_hook_present
    )

    return {
        "version": version,
        "expected_version": EXPECTED_VERSION,
        "version_ok": version == EXPECTED_VERSION,
        "find_contract_blocks_present": bool(find_fn),
        "parse_fields_present": bool(parse_fn),
        "find_contract_blocks_anchors_at_marker": anchors,
        "parse_fields_uses_seen_marker": parse_seen,
        "parse_fields_ignores_preamble": parse_ignores,
        "hotfix_003_markers_present": markers_present,
        "hotfix_003_helpers_present": helper_present,
        "hotfix_003_row_hook_present": row_hook_present,
        "apply_acceptance_passed": passed,
    }


def write_status(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"summary": summary}, indent=2), encoding="utf-8")

    lines = [
        "# Source Contract Inventory Probe v1.1 Malformed Assignment Hotfix 003 Status",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY classifier/probe hotfix`",
        "",
        "## Verdict",
        "",
        "```text",
        f"hotfix status: {summary['hotfix_status']}",
        f"acceptance passed: {summary['inspection_after']['apply_acceptance_passed']}",
        "DotTalk++ source edits: NOT PERFORMED",
        "DBF writes: NOT PERFORMED",
        "CMDHELPCHK changes: NOT PERFORMED",
        "HELP DATA rebuild: NOT PERFORMED",
        "v1.1 default promotion: NOT AUTHORIZED",
        "```",
        "",
        "## Inspection after hotfix",
        "",
        "| Check | Value |",
        "|---|---|",
    ]
    for key, value in summary["inspection_after"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines += [
        "",
        "## Next command sequence",
        "",
        "```powershell",
        "python selfdoc\\probes\\source_contract_inventory_probe_v1_1.py",
        "python selfdoc\\probes\\source_contract_inventory_v1_1_classifier_gap_review.py",
        "python selfdoc\\probes\\source_contract_capture_hotfix_002_evidence_lanes.py",
        "python selfdoc\\probes\\source_contract_malformed_assignment_hotfix_003_validation.py",
        "```",
        "",
        "## Non-mutation confirmation",
        "",
    ]
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not TARGET.is_file():
        raise SystemExit(f"Missing target probe: {TARGET}")

    original = TARGET.read_text(encoding="utf-8")
    before = inspect_probe_text(original)

    patched = re.sub(r'PROBE_VERSION\s*=\s*"[^"]+"', f'PROBE_VERSION = "{EXPECTED_VERSION}"', original, count=1)
    patched = patched.replace("SelfDoc source contract inventory v1.1 hotfix_001 complete.", "SelfDoc source contract inventory v1.1 malformed assignment hotfix 003 complete.")
    patched = patched.replace("SelfDoc source contract inventory v1.1 capture hotfix 002 complete.", "SelfDoc source contract inventory v1.1 malformed assignment hotfix 003 complete.")
    patched = patched.replace("Versioned v1.1 source-contract inventory with hotfix_001.", "Versioned v1.1 source-contract inventory with malformed assignment hotfix 003.")
    patched = patched.replace("Versioned v1.1 source-contract inventory with capture hotfix 002.", "Versioned v1.1 source-contract inventory with malformed assignment hotfix 003.")

    patched, find_changed = replace_function(patched, "find_contract_blocks", FIND_CONTRACT_BLOCKS_REPLACEMENT)
    patched, parse_changed = replace_function(patched, "parse_fields", PARSE_FIELDS_REPLACEMENT)
    patched, helper_inserted = insert_helper_block(patched)
    patched, row_hook_count = patch_known_row_patterns(patched)

    if patched != original:
        BACKUP.write_text(original, encoding="utf-8")
        TARGET.write_text(patched, encoding="utf-8", newline="\n")
        status = "APPLIED"
    else:
        status = "NO_TEXT_CHANGE_NEEDED"

    after = inspect_probe_text(TARGET.read_text(encoding="utf-8"))

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "hotfix_status": status,
        "target": str(TARGET),
        "backup": str(BACKUP) if patched != original else "",
        "find_contract_blocks_replaced": find_changed,
        "parse_fields_replaced": parse_changed,
        "helper_inserted": helper_inserted,
        "row_hook_count": row_hook_count,
        "inspection_before": before,
        "inspection_after": after,
        "non_mutation_guards": [
            "did_not_edit_dottalkpp_source",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_source_headers",
            "did_not_promote_v1_1_to_default",
            "did_not_move_or_delete_files",
        ],
    }

    write_status(summary)

    print("SelfDoc v1.1 malformed assignment hotfix 003 complete.")
    print(f"Status: {status}")
    print(f"Target: {TARGET}")
    if patched != original:
        print(f"Backup: {BACKUP}")
    print(f"Version: {after['version']}")
    print(f"Row hook count: {row_hook_count}")
    print(f"Acceptance passed: {after['apply_acceptance_passed']}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print("No DotTalk++ source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No source contracts were repaired.")

    return 0 if after["apply_acceptance_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
