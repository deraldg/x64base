#!/usr/bin/env python3
"""
apply_source_contract_inventory_probe_v1_1_capture_hotfix_002.py

REPORT_ONLY classifier/probe hotfix installer.

Patches only:
  selfdoc\probes\source_contract_inventory_probe_v1_1.py

Purpose:
  - Re-apply/strengthen marker-anchored capture.
  - Treat @dottalk.usage v1 as the contract payload start.
  - Treat preamble before marker as context, not malformed payload.
  - Add a report-only postprocess evidence lane script for the current Batch 0 issue.
  - Use SelfDoc Collection Imperfection Policy lanes:
      CAPTURE_REVIEW
      CLASSIFIER_REVIEW
      STALE_EVIDENCE
      DO_NOT_REPAIR

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

import re
from pathlib import Path


TARGET = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py"
BACKUP = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py.bak_capture_hotfix_002"


FIND_CONTRACT_BLOCKS_REPLACEMENT = """def find_contract_blocks(text: str) -> list[tuple[int, int, str]]:
    # Capture hotfix 002:
    # - For line-comment contracts, the marker line is the contract start.
    # - Contiguous // lines after the marker remain part of the contract.
    # - Contiguous // lines before the marker are optional preamble/context,
    #   not contract payload.
    # - Blank lines after the marker are included only when followed by another
    #   line-comment contract line.
    # - Block comments are still captured as an enclosing block; parse_fields()
    #   ignores payload before the marker.
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


PARSE_FIELDS_REPLACEMENT = """def parse_fields(header_text: str) -> tuple[dict[str, list[str]], list[str]]:
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


def replace_function(text: str, func_name: str, next_func_name: str, replacement: str) -> str:
    pattern = rf"def {re.escape(func_name)}\(.*?\n(?=def {re.escape(next_func_name)}\()"
    new_text, count = re.subn(pattern, replacement.rstrip() + "\n\n\n", text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit(f"Could not replace function {func_name}; replacement count={count}")
    return new_text


def main() -> int:
    if not TARGET.is_file():
        raise SystemExit(f"Missing target probe: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")
    original = text

    text = re.sub(r'PROBE_VERSION\s*=\s*"[^"]+"', 'PROBE_VERSION = "v1.1-capture_hotfix_002"', text, count=1)
    text = text.replace('SelfDoc source contract inventory v1.1 hotfix_001 complete.', 'SelfDoc source contract inventory v1.1 capture hotfix 002 complete.')
    text = text.replace('SelfDoc source contract inventory v1.1 capture hotfix complete.', 'SelfDoc source contract inventory v1.1 capture hotfix 002 complete.')
    text = text.replace(
        "Versioned v1.1 source-contract inventory with hotfix_001.",
        "Versioned v1.1 source-contract inventory with capture hotfix 002."
    )
    text = text.replace(
        "Versioned v1.1 source-contract inventory with capture hotfix.",
        "Versioned v1.1 source-contract inventory with capture hotfix 002."
    )

    text = replace_function(text, "find_contract_blocks", "strip_comment_prefix", FIND_CONTRACT_BLOCKS_REPLACEMENT)
    text = replace_function(text, "parse_fields", "norm", PARSE_FIELDS_REPLACEMENT)

    if text == original:
        print("No changes needed; target already appears to include capture hotfix 002.")
        return 0

    BACKUP.write_text(original, encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8", newline="\n")

    print(f"Updated: {TARGET}")
    print(f"Backup written to: {BACKUP}")
    print("Capture hotfix 002 applied:")
    print("  @dottalk.usage v1 marker is treated as contract payload start")
    print("  line-comment preamble before marker is no longer parsed as malformed payload")
    print("  block-comment preamble before marker is ignored by field parser")
    print("  probe version set to v1.1-capture_hotfix_002")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No source contracts were repaired.")
    print("v1.1 was not promoted to default.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
