#!/usr/bin/env python3
"""Build the complete file-name inventory for a documentation-flush run."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory every file in one full-stack documentation run."
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_root = args.run_root.resolve()
    output = args.output.resolve()
    if not run_root.is_dir():
        raise SystemExit(f"Run root is not a directory: {run_root}")
    if output.parent != run_root:
        raise SystemExit("Output must be written directly in the run root.")

    rows: list[dict[str, object]] = []
    for path in sorted(run_root.rglob("*"), key=lambda item: item.as_posix().lower()):
        if not path.is_file() or path.resolve() == output:
            continue
        relative = path.relative_to(run_root)
        stat = path.stat()
        rows.append(
            {
                "relative_path": relative.as_posix(),
                "phase": relative.parts[0] if len(relative.parts) > 1 else "run_root",
                "file_name": path.name,
                "extension": path.suffix.lower() or "[none]",
                "bytes": stat.st_size,
                "modified_utc": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(timespec="seconds"),
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=(
                "relative_path",
                "phase",
                "file_name",
                "extension",
                "bytes",
                "modified_utc",
            ),
        )
        writer.writeheader()
        writer.writerows(rows)

    total_bytes = sum(int(row["bytes"]) for row in rows)
    print(f"run_root={run_root}")
    print(f"output={output}")
    print(f"files={len(rows)}")
    print(f"bytes={total_bytes}")
    print("self_excluded=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
