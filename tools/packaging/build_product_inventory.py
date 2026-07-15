#!/usr/bin/env python3
"""Validate a product allow-list and emit a hash inventory.

Only git-tracked files can be selected. This keeps product packaging separate
from both the universal .gitignore deny-list and the promotion allow-list.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath


FORBIDDEN_SUFFIXES = {".exe", ".dll", ".pdb", ".obj", ".lib", ".exp", ".mdb"}
FORBIDDEN_PARTS = {"lmdb", "og", "scratch", "tmp"}


def manifest_patterns(path: Path) -> list[str]:
    patterns: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            patterns.append(line.replace("\\", "/"))
    return patterns


def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    # The working tree may intentionally delete a tracked file before its next
    # commit. Package the present tracked inputs, never a stale index entry.
    return [
        p
        for p in result.stdout.decode("utf-8").split("\0")
        if p and (root / p).is_file()
    ]


def matches(path: str, pattern: str) -> bool:
    # PurePosixPath keeps '*' scoped to one path segment. Recursive selection
    # is intentionally available only through an explicit trailing '/**'.
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-3].rstrip("/") + "/")
    return PurePosixPath(path).match(pattern)


def forbidden_reason(path: str) -> str | None:
    posix = PurePosixPath(path)
    lowered_parts = {part.lower() for part in posix.parts}
    if lowered_parts & FORBIDDEN_PARTS:
        return "forbidden path component"
    if posix.suffix.lower() in FORBIDDEN_SUFFIXES:
        return "forbidden generated/binary suffix"
    if any(part.lower().endswith(".cdx.d") for part in posix.parts):
        return "LMDB sidecar directory"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--product", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cmake-list-output", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    manifest = args.manifest.resolve()
    patterns = manifest_patterns(manifest)
    tracked = tracked_files(root)

    selected = sorted({p for p in tracked for pattern in patterns if matches(p, pattern)})
    unmatched = [pattern for pattern in patterns if not any(matches(p, pattern) for p in tracked)]
    if unmatched:
        raise SystemExit("manifest patterns matched no tracked files: " + ", ".join(unmatched))

    entries: list[dict[str, object]] = []
    total = 0
    for rel in selected:
        reason = forbidden_reason(rel)
        if reason:
            raise SystemExit(f"refusing {rel}: {reason}")
        source = root / rel
        if not source.is_file():
            raise SystemExit(f"tracked package entry is not a file: {rel}")
        data = source.read_bytes()
        total += len(data)
        entries.append(
            {"path": rel, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        )

    payload = {
        "schema": "dottalk-product-inventory-v1",
        "inventory_scope": "tracked_source_inputs",
        "product": args.product.upper(),
        "project_license": "To be determined.",
        "source_manifest": manifest.relative_to(root).as_posix(),
        "file_count": len(entries),
        "total_bytes": total,
        "files": entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.cmake_list_output:
        args.cmake_list_output.parent.mkdir(parents=True, exist_ok=True)
        args.cmake_list_output.write_text("\n".join(selected) + "\n", encoding="utf-8")
    print(f"{args.product.upper()}: {len(entries)} tracked files, {total} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
