#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TARGET = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py"
BACKUP = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py.bak_capture_hotfix_002_reapply"
REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
OUT_MD = REPORT_DIR / "source_contract_inventory_probe_v1_1_capture_hotfix_002_reapply_status.md"
OUT_JSON = REPORT_DIR / "source_contract_inventory_probe_v1_1_capture_hotfix_002_reapply_status.json"
EXPECTED_VERSION = "v1.1-capture_hotfix_002"

FIND_CONTRACT_BLOCKS_REPLACEMENT = r"""def find_contract_blocks(text: str) -> list[tuple[int, int, str]]:
    # Capture hotfix 002:
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
    # Capture hotfix 002:
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

def inspect_probe_text(text: str) -> dict[str, Any]:
    version_match = re.search(r'PROBE_VERSION\s*=\s*"([^"]+)"', text)
    version = version_match.group(1) if version_match else ""
    find_span = function_span(text, "find_contract_blocks")
    parse_span = function_span(text, "parse_fields")
    find_fn = text[find_span[0]:find_span[1]] if find_span else ""
    parse_fn = text[parse_span[0]:parse_span[1]] if parse_span else ""

    anchors = (
        'line_start = text.rfind("\\\\n", 0, marker_start) + 1' in find_fn
        or 'line_start = text.rfind("\\n", 0, marker_start) + 1' in find_fn
    ) and "start = line_start" in find_fn and "while start > 0" not in find_fn

    parse_seen = "seen_marker = False" in parse_fn and "if MARKER in line" in parse_fn
    parse_ignores = "if not seen_marker" in parse_fn and "ignored_preamble_lines" in parse_fn
    markers_present = "Capture hotfix 002" in find_fn and "Capture hotfix 002" in parse_fn
    passed = version == EXPECTED_VERSION and bool(find_fn) and bool(parse_fn) and anchors and parse_seen and parse_ignores and markers_present

    return {
        "version": version,
        "expected_version": EXPECTED_VERSION,
        "version_ok": version == EXPECTED_VERSION,
        "find_contract_blocks_present": bool(find_fn),
        "parse_fields_present": bool(parse_fn),
        "find_contract_blocks_anchors_at_marker": anchors,
        "parse_fields_uses_seen_marker": parse_seen,
        "parse_fields_ignores_preamble": parse_ignores,
        "hotfix_002_markers_present": markers_present,
        "apply_acceptance_passed": passed,
    }

def write_status(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"summary": summary}, indent=2), encoding="utf-8")

    lines = [
        "# Source Contract Inventory Probe v1.1 Capture Hotfix 002 Reapply Status",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY classifier/probe hotfix`",
        "",
        "## Verdict",
        "",
        "```text",
        f"reapply status: {summary['reapply_status']}",
        f"acceptance passed: {summary['inspection_after']['apply_acceptance_passed']}",
        "DotTalk++ source edits: NOT PERFORMED",
        "DBF writes: NOT PERFORMED",
        "CMDHELPCHK changes: NOT PERFORMED",
        "HELP DATA rebuild: NOT PERFORMED",
        "v1.1 default promotion: NOT AUTHORIZED",
        "```",
        "",
        "## Inspection after reapply",
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
        "python selfdoc\\probes\\source_contract_inventory_probe_v1_1_capture_hotfix_002_apply_verify.py --rerun",
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
    patched = patched.replace("SelfDoc source contract inventory v1.1 hotfix_001 complete.", "SelfDoc source contract inventory v1.1 capture hotfix 002 complete.")
    patched = patched.replace("SelfDoc source contract inventory v1.1 capture hotfix complete.", "SelfDoc source contract inventory v1.1 capture hotfix 002 complete.")
    patched = patched.replace("Versioned v1.1 source-contract inventory with hotfix_001.", "Versioned v1.1 source-contract inventory with capture hotfix 002.")
    patched = patched.replace("Versioned v1.1 source-contract inventory with capture hotfix.", "Versioned v1.1 source-contract inventory with capture hotfix 002.")

    patched, find_changed = replace_function(patched, "find_contract_blocks", FIND_CONTRACT_BLOCKS_REPLACEMENT)
    patched, parse_changed = replace_function(patched, "parse_fields", PARSE_FIELDS_REPLACEMENT)

    if patched != original:
        BACKUP.write_text(original, encoding="utf-8")
        TARGET.write_text(patched, encoding="utf-8", newline="\n")
        status = "REAPPLIED"
    else:
        status = "NO_TEXT_CHANGE_NEEDED"

    after = inspect_probe_text(TARGET.read_text(encoding="utf-8"))

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reapply_status": status,
        "target": str(TARGET),
        "backup": str(BACKUP) if patched != original else "",
        "find_contract_blocks_replaced": find_changed,
        "parse_fields_replaced": parse_changed,
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

    print("SelfDoc v1.1 capture hotfix 002 reapply complete.")
    print(f"Status: {status}")
    print(f"Target: {TARGET}")
    if patched != original:
        print(f"Backup: {BACKUP}")
    print(f"Version: {after['version']}")
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
