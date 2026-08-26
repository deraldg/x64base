#!/usr/bin/env python3
"""Run the fail-closed website matrix checks before publication ascent."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Callable


Runner = Callable[..., subprocess.CompletedProcess[str]]


def commands(root: Path, site_root: Path) -> list[tuple[str, list[str]]]:
    python = sys.executable
    tools = root / "tools" / "fullstack_docs"
    content = site_root / "content"
    return [
        (
            "content_inventory",
            [
                python,
                str(tools / "validate_website_content_manifest.py"),
                "--manifest",
                str(tools / "website_content_manifest.yaml"),
                "--content-root",
                str(content),
            ],
        ),
        (
            "fullstack_publication_entry",
            [
                python,
                str(tools / "docpush_preflight.py"),
                "--root",
                str(root),
                "--catalog",
                str(content / "docs" / "dottalk" / "command-catalog.mdx"),
            ],
        ),
        (
            "function_catalog",
            [
                python,
                str(tools / "command_catalog_sync.py"),
                "fn-check",
                "--source-root",
                str(root),
                "--catalog",
                str(content / "docs" / "dottalk" / "function-catalog.mdx"),
            ],
        ),
        (
            "error_codes",
            [
                python,
                str(tools / "command_catalog_sync.py"),
                "err-check",
                "--source-root",
                str(root),
                "--page",
                str(content / "docs" / "engine" / "error-codes.mdx"),
            ],
        ),
        (
            "locales",
            [
                python,
                str(tools / "command_catalog_sync.py"),
                "loc-check",
                "--source-root",
                str(root),
                "--page",
                str(content / "docs" / "engine" / "messaging-and-localization.mdx"),
            ],
        ),
    ]


def run_matrix_check(root: Path, site_root: Path, runner: Runner = subprocess.run) -> list[str]:
    failed: list[str] = []
    for label, command in commands(root, site_root):
        result = runner(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        print(f"== website matrix: {label} ==")
        if result.stdout:
            print(result.stdout.rstrip())
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        if result.returncode != 0:
            failed.append(label)
    return failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="ccode authority root")
    parser.add_argument("--site-root", type=Path, required=True, help="website source root")
    args = parser.parse_args()
    failed = run_matrix_check(args.root.resolve(), args.site_root.resolve())
    if failed:
        print("website-matrix-check: FAIL -- " + ", ".join(failed))
        return 2
    print("website-matrix-check: PASS -- all hard publication relationships are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
