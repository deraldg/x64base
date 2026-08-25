#!/usr/bin/env python3
"""Build the complete physical command-reference index.

The historical README remains the reader-linked 164-page review index.  This
index adds the supplemental and post-baseline repair layers without erasing
their distinct provenance.
"""

from __future__ import annotations

import re
import sys
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

# PROVENANCE IS DECLARED, NOT INHERITED BY FALLING THROUGH. Changed 2026-08-25.
#
# This file used to carry ONE hardcoded set and an `else` that labelled anything
# unrecognised "supplemental" -- a layer the index describes to the reader as
# "the accepted supplemental set". So any page dropped into commands/ silently
# acquired an acceptance it had never been given, and the index asserted it on
# every row. Same answer for "known supplemental" and "never classified": the
# AIF-118 shape, in the document that exists to keep the layers distinct.
#
# It is also the defect fixed four commits earlier in
# build_postbaseline_supported_command_pages.py, where a hardcoded July run id
# would have stamped 20 pages with a run that did not produce them. Provenance
# encoded as a literal means new work inherits an old label.
#
# Every layer is now named, and an undeclared page is UNCLASSIFIED and FAILS.
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

# The 19 that were only ever "supplemental" by falling through the else.
# Enumerated 2026-08-25 from the tree so the label is a statement rather than
# a leftover; membership is unchanged.
SUPPLEMENTAL = {
    "area", "bottom", "browse", "browser", "continue", "ersatz", "find", "go",
    "goto", "list", "locate", "schemas", "seek", "select", "skip", "smartlist",
    "top", "use", "workspace",
}

# R127 written-debt pages, generated from the promoted 2026-08-25 harvest and
# accepted 2026-08-25. Record:
# runs/DOCFLUSH-20260812-001/manualgen_phase/COMMAND_PAGES_GENERATED_V1.md
WRITTEN_DEBT_R127 = {
    "average", "boolean", "browsetui", "browsetv", "display", "echo", "first",
    "formula", "indexseek", "last", "list_lmdb", "next", "prior", "rbrowse",
    "refresh", "rel_list", "simplebrowser", "smartbrowser", "sort", "wherecache",
}

DECLARED_LAYERS = (
    ("post-baseline repair", POSTBASELINE_REPAIR),
    ("supplemental", SUPPLEMENTAL),
    ("written-debt (R127)", WRITTEN_DEBT_R127),
)


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
    counts = {name: 0 for name, _ in DECLARED_LAYERS}
    counts["reader-linked"] = 0
    counts["UNCLASSIFIED"] = 0
    unclassified: list[str] = []

    for path in pages:
        slug = path.stem.lower()
        layer = next((name for name, slugs in DECLARED_LAYERS if slug in slugs), None)
        if layer is None:
            layer = "reader-linked" if slug in reader else "UNCLASSIFIED"
        if layer == "UNCLASSIFIED":
            unclassified.append(slug)
        counts[layer] += 1
        title, status = page_metadata(path)
        rows.append((title, path.name, layer, status))

    lines = [
        "# Complete Command Reference Index",
        "",
        "This is the complete physical command-reference product. It preserves the",
        "historical reader-linked set, the accepted supplemental set, the",
        "post-baseline coverage repair, and the R127 written-debt pages as",
        "separate provenance layers. A page in none of them is UNCLASSIFIED and",
        "the build fails rather than labelling it as an accepted layer.",
        "",
        f"- Total pages: **{len(rows)}**",
        f"- Reader-linked pages: **{counts['reader-linked']}**",
        f"- Supplemental standalone pages: **{counts['supplemental']}**",
        f"- Post-baseline coverage-repair pages: **{counts['post-baseline repair']}**",
        f"- Written-debt pages (R127): **{counts['written-debt (R127)']}**",
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

    if unclassified:
        # FAIL CLOSED. Writing an index that calls an undeclared page
        # "supplemental" is the behaviour this replaces.
        print(
            "UNCLASSIFIED page(s), index NOT written: " + ", ".join(sorted(unclassified)),
            file=sys.stderr,
        )
        print(
            "  Declare each slug in one of DECLARED_LAYERS with the run that "
            "produced it, then re-run.",
            file=sys.stderr,
        )
        return 2
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")
    print(
        "pages=%d reader=%d supplemental=%d repair=%d written_debt=%d"
        % (
            len(rows),
            counts["reader-linked"],
            counts["supplemental"],
            counts["post-baseline repair"],
            counts["written-debt (R127)"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
