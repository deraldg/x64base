#!/usr/bin/env python3
"""Build the complete physical command-reference index.

The historical README remains the reader-linked 164-page review index.  This
index adds the supplemental and post-baseline repair layers without erasing
their distinct provenance.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_ROOT = (
    ROOT
    / "docs/manuals/developer/manualgen/published"
    / "developer_manual_publication_v1/command_reference_v1"
)
COMMAND_DIR = REFERENCE_ROOT / "commands"
READER_INDEX = REFERENCE_ROOT / "README.md"
OUTPUT = REFERENCE_ROOT / "COMPLETE_COMMAND_REFERENCE_INDEX_V1.md"

POSTBASELINE_REPAIR = {
    "buildvectors",
    "defcmd",
    "deffn",
    "stop_on_error",
    "undefcmd",
    "undeffn",
    "user",
    "vdisk",
}


def reader_linked_slugs() -> set[str]:
    text = READER_INDEX.read_text(encoding="utf-8", errors="replace")
    return {
        match.group(1).lower()
        for match in re.finditer(r"\(commands/([a-z0-9_]+)\.md\)", text)
    }


def page_metadata(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    heading = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    status = re.search(r"^-\s+Status:\s+`([^`]+)`", text, re.MULTILINE)
    return (
        heading.group(1).strip() if heading else path.stem.upper(),
        status.group(1).strip() if status else "not-labelled",
    )


def main() -> int:
    reader = reader_linked_slugs()
    pages = sorted(COMMAND_DIR.glob("*.md"), key=lambda item: item.stem.lower())
    rows: list[tuple[str, str, str, str]] = []
    counts = {"reader-linked": 0, "supplemental": 0, "post-baseline repair": 0}

    for path in pages:
        slug = path.stem.lower()
        if slug in POSTBASELINE_REPAIR:
            layer = "post-baseline repair"
        elif slug in reader:
            layer = "reader-linked"
        else:
            layer = "supplemental"
        counts[layer] += 1
        title, status = page_metadata(path)
        rows.append((title, path.name, layer, status))

    lines = [
        "# Complete Command Reference Index",
        "",
        "This is the complete physical command-reference product. It preserves the",
        "historical reader-linked set, the accepted supplemental set, and the",
        "post-baseline coverage repair as separate provenance layers.",
        "",
        f"- Total pages: **{len(rows)}**",
        f"- Reader-linked pages: **{counts['reader-linked']}**",
        f"- Supplemental standalone pages: **{counts['supplemental']}**",
        f"- Post-baseline coverage-repair pages: **{counts['post-baseline repair']}**",
        "- Historical supported-topic debt remains tracked by the fail-closed",
        "  supported-command publication audit; this index does not conceal it.",
        "",
        "The [reader-linked review index](README.md) remains available as the",
        "historical 164-page entry set.",
        "",
        "| # | Command page | Provenance layer | Status |",
        "| ---: | --- | --- | --- |",
    ]
    for number, (title, filename, layer, status) in enumerate(rows, 1):
        lines.append(
            f"| {number} | [{title}](commands/{filename}) | {layer} | `{status}` |"
        )

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")
    print(
        "pages=%d reader=%d supplemental=%d repair=%d"
        % (
            len(rows),
            counts["reader-linked"],
            counts["supplemental"],
            counts["post-baseline repair"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
