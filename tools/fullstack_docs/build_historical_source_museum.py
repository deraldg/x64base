#!/usr/bin/env python3
"""Build a public-safe, read-only browser for the preserved xBase source archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import sys
from pathlib import Path
from typing import Any
from zipfile import ZipFile


FAMILIES: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "xbase",
        "xBase core",
        "1993",
        ("XBASE.C", "XBASE.H", "XBCMDS.C", "XBCMDS.H", "XBINDEX.C", "XBINDEX.H"),
    ),
    (
        "xdll",
        "XDLL / xBase DLL-oriented branch",
        "1993-1996",
        ("XBASE.C", "XBASE.H", "XBCMDS.C", "XBCMDS.H", "XBINDEX.C", "XBINDEX.H"),
    ),
    (
        "xbase2",
        "xBase2 / DotTalk 1995",
        "1995",
        (
            "DOTTALK.C",
            "DOTTALK.H",
            "TEST.C",
            "XBASE.C",
            "XBASE.H",
            "XBCMDS.C",
            "XBCMDS.H",
            "XBINDEX.C",
            "XBINDEX.H",
        ),
    ),
)


def require_python_312() -> None:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError(
            f"Historical source museum requires Python 3.12; running "
            f"{sys.version_info.major}.{sys.version_info.minor}."
        )


def read_archive(archive: Path) -> tuple[str, list[dict[str, Any]], dict[str, bytes]]:
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest().upper()
    rows: list[dict[str, Any]] = []
    payloads: dict[str, bytes] = {}
    with ZipFile(archive) as bundle:
        members = {info.filename: info for info in bundle.infolist()}
        for family, family_label, era, names in FAMILIES:
            for name in names:
                member = f"xbase/{family}/{name}"
                info = members.get(member)
                if info is None:
                    raise ValueError(f"required archive member missing: {member}")
                data = bundle.read(member)
                relative = f"{family}/{name.lower()}.txt"
                viewer_relative = f"{family}/{name.lower()}.html"
                rows.append(
                    {
                        "artifact_id": f"HSRC-{family.upper()}-{name.replace('.', '-')}",
                        "family": family,
                        "family_label": family_label,
                        "era": era,
                        "file_name": name,
                        "archive_member": member,
                        "archive_timestamp": "-".join(
                            (
                                f"{info.date_time[0]:04d}",
                                f"{info.date_time[1]:02d}",
                                f"{info.date_time[2]:02d}",
                            )
                        ),
                        "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest().upper(),
                        "truth_level": "archive-byte-preserved",
                        "public_path": (
                            "/artifacts/source-lineage/historical-source/"
                            f"{relative}"
                        ),
                        "viewer_path": (
                            "/artifacts/source-lineage/historical-source/"
                            f"{viewer_relative}"
                        ),
                    }
                )
                payloads[relative] = data
    return archive_sha, rows, payloads


def render_source_view(row: dict[str, Any], data: bytes) -> str:
    source = data.decode("cp1252")
    title = f"{row['family_label']} — {row['file_name']}"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} -- x64base historical source</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{ margin: 0; background: #08111d; color: #dbeafe; font: 16px/1.5 system-ui, sans-serif; }}
    header {{ position: sticky; top: 0; padding: 1rem 1.25rem; background: #0f1d2e; border-bottom: 1px solid #29415f; }}
    h1 {{ margin: 0 0 .35rem; color: #70d8e6; font-size: 1.2rem; }}
    p {{ margin: .25rem 0; color: #a9c1df; }}
    a {{ color: #70d8e6; }}
    pre {{ margin: 0; padding: 1.25rem; overflow: auto; tab-size: 4; font: 14px/1.45 Consolas, "Courier New", monospace; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(title)}</h1>
    <p>Read-only archive view · {row['archive_timestamp']} · {row['bytes']:,} bytes · SHA-256 {row['sha256']}</p>
    <p><a href="/docs/dev/historical-source-files">Back to source browser</a> ·
       <a href="{html.escape(row['public_path'])}">Open byte-preserved text</a></p>
  </header>
  <pre>{html.escape(source)}</pre>
</body>
</html>
"""


def render_page(archive_sha: str, rows: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    for family, family_label, era, _ in FAMILIES:
        family_rows = [row for row in rows if row["family"] == family]
        table = "\n".join(
            "| [{file_name}]({public_path}) | {archive_timestamp} | {bytes:,} | "
            "`{sha}` |".format(
                file_name=row["file_name"],
                public_path=row["viewer_path"],
                archive_timestamp=row["archive_timestamp"],
                bytes=row["bytes"],
                sha=row["sha256"][:16],
            )
            for row in family_rows
        )
        sections.append(
            f"""## {family_label}

Archive era: **{era}** · {len(family_rows)} canonical files.

| File | Archive date | Bytes | SHA-256 prefix |
| --- | --- | ---: | --- |
{table}
"""
        )

    return f"""---
title: "Historical xBase Source Files"
description: "Read-only browser for the canonical xBase, XDLL, xBase2, and DotTalk source files preserved in the original archive."
---

> **Read-only historical evidence.** These files are byte-preserved projections
> from the original archive. They are not compiled as the current product and
> must not be edited in place.

## Source museum contract

This page makes the preserved source inspectable without exposing private local
paths. Each file link opens an escaped, read-only HTML view generated from the
archived bytes and provides a link to the byte-preserved text. The file hash,
archive member name, original archive timestamp, viewer URL, and raw URL are
retained in the companion manifests.

- Archive SHA-256:
  `{archive_sha}`
- Canonical files: **{len(rows)}**
- [Download the JSON manifest](/artifacts/source-lineage/historical-source-files-v1.json)
- [Download the CSV manifest](/artifacts/source-lineage/historical-source-files-v1.csv)
- [Open the historical family tree](/docs/dev/historical-family-tree)

{chr(10).join(sections)}
## Interpretation boundary

- `xbase/`, `xdll/`, and `xbase2/` are verified siblings in the archive.
- `DOTTALK.C` is physically contained in the xBase2 branch.
- XDLL is DLL-export-oriented source; no historical `xbase.dll` binary was
  found in the reviewed archive.
- Modern x64base and DotTalk++ claims come from current source and runtime
  proof, not from these archived files.
"""


def write_outputs(
    archive: Path,
    out_files: Path,
    out_page: Path,
    out_json: Path,
    out_csv: Path,
) -> None:
    archive_sha, rows, payloads = read_archive(archive)
    for relative, data in payloads.items():
        target = out_files / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        row = next(row for row in rows if row["public_path"].endswith(relative))
        viewer = target.with_name(target.name.removesuffix(".txt") + ".html")
        viewer.write_text(render_source_view(row, data), encoding="utf-8")

    public = {
        "schema": "x64base.historical_source_files.v1",
        "generated_on": "2026-07-23",
        "archive": {
            "label": "xbase.zip",
            "sha256": archive_sha,
            "truth_level": "archive-verified",
        },
        "file_count": len(rows),
        "families": [
            {
                "id": family,
                "label": label,
                "era": era,
                "file_count": sum(row["family"] == family for row in rows),
            }
            for family, label, era, _ in FAMILIES
        ],
        "files": rows,
        "authority_note": (
            "Read-only public projection. Private source roots are intentionally omitted."
        ),
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "artifact_id",
                "family",
                "family_label",
                "era",
                "file_name",
                "archive_member",
                "archive_timestamp",
                "bytes",
                "sha256",
                "truth_level",
                "public_path",
                "viewer_path",
            ),
        )
        writer.writeheader()
        writer.writerows(rows)

    out_page.parent.mkdir(parents=True, exist_ok=True)
    out_page.write_text(render_page(archive_sha, rows), encoding="utf-8")
    print(
        f"PASS historical source museum: {len(rows)} files, "
        f"archive_sha256={archive_sha}"
    )


def main() -> int:
    require_python_312()
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out-files", type=Path, required=True)
    parser.add_argument("--out-page", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, required=True)
    args = parser.parse_args()
    write_outputs(
        args.archive,
        args.out_files,
        args.out_page,
        args.out_json,
        args.out_csv,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
