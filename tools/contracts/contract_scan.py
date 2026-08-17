#!/usr/bin/env python3
"""Read-only contract lane inventory scanner."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from dataclasses import dataclass


CONTRACT_DOC_RE = re.compile(r"(CONTRACT|USAGE|POLICY|GOVERNANCE|SAFETY)", re.IGNORECASE)
SOURCE_CONTRACT_RE = re.compile(r"^\s*(//|#)\s*@dottalk\.contract\b", re.MULTILINE)


@dataclass(frozen=True)
class RegistryEntry:
    name: str
    kind: str
    source: str


@dataclass(frozen=True)
class ScanResult:
    contract_docs: list[pathlib.Path]
    source_annotations: list[pathlib.Path]
    usage_markers: list[pathlib.Path]
    registry_entries: list[RegistryEntry]

    @property
    def registry_names(self) -> set[str]:
        return {entry.name.lower() for entry in self.registry_entries}


def repo_root(start: pathlib.Path) -> pathlib.Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / "docs").exists():
            return candidate
    return current


def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def relative(path: pathlib.Path, root: pathlib.Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def clean_registry_source(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        value = value[1:-1]
    return value.strip()


def active_registry_section(markdown: str) -> str:
    start_marker = "## Active Contracts"
    start = markdown.find(start_marker)
    if start == -1:
        return markdown
    next_section = markdown.find("\n## ", start + len(start_marker))
    if next_section == -1:
        return markdown[start:]
    return markdown[start:next_section]


def parse_registry_entries(markdown: str) -> list[RegistryEntry]:
    entries: list[RegistryEntry] = []
    section = active_registry_section(markdown)
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        columns = [part.strip() for part in line.strip("|").split("|")]
        if len(columns) < 5 or columns[0] == "Contract":
            continue
        entries.append(RegistryEntry(
            name=columns[0],
            kind=columns[1],
            source=clean_registry_source(columns[4]),
        ))
    return entries


def scan(root: pathlib.Path) -> ScanResult:
    docs = root / "docs"
    # bindings/ added 2026-08-17. It was absent, so `@dottalk.contract` in
    # bindings/pydottalk/src/module.cpp was invisible to this scan -- the
    # annotation existed, the contract said it was harvested, and nothing read
    # it. metacollect DOES walk bindings/ but harvests @dottalk.usage (command
    # contracts), and the binding is not a command, so neither tool saw it.
    #
    # The gap was silent in the worst direction: a declared posture that no
    # inventory knows about reads as compliant from the source side and as
    # missing from the registry side, and neither side complains.
    source_roots = [root / "include", root / "src", root / "tools", root / "bindings"]

    contract_docs: list[pathlib.Path] = []
    if docs.exists():
        for path in docs.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".md", ".txt"} and CONTRACT_DOC_RE.search(path.name):
                contract_docs.append(path)

    source_annotations: list[pathlib.Path] = []
    usage_markers: list[pathlib.Path] = []
    for source_root in source_roots:
        if not source_root.exists():
            continue
        for path in source_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".cpp", ".hpp", ".h", ".py", ".txt", ".md"}:
                continue
            text = read_text(path)
            if SOURCE_CONTRACT_RE.search(text):
                source_annotations.append(path)
            if "usage-access:" in text or "USAGE_CONTRACT" in text or "@dottalk.usage" in text:
                usage_markers.append(path)

    registry_entries: list[RegistryEntry] = []
    registry = root / "docs" / "contracts" / "CONTRACT_REGISTRY_V1.md"
    registry_text = read_text(registry)
    registry_entries = parse_registry_entries(registry_text)

    return ScanResult(
        contract_docs=sorted(set(contract_docs)),
        source_annotations=sorted(set(source_annotations)),
        usage_markers=sorted(set(usage_markers)),
        registry_entries=registry_entries,
    )


def likely_unregistered_doc(path: pathlib.Path, root: pathlib.Path, registry_names: set[str]) -> bool:
    stem = path.stem.lower()
    rel = relative(path, root).lower()
    if "docs/contracts/" in rel:
        return False
    for name in registry_names:
        normalized = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
        if normalized and normalized in stem:
            return False
        if name and name in rel:
            return False
    return True


def likely_unregistered_docs(result: ScanResult, root: pathlib.Path) -> list[pathlib.Path]:
    registered_sources = {
        entry.source.lower().replace("\\", "/")
        for entry in result.registry_entries
        if entry.source
    }
    return [
        path for path in result.contract_docs
        if relative(path, root).lower() not in registered_sources and
        likely_unregistered_doc(path, root, result.registry_names)
    ]


def discovered_paths(result: ScanResult, root: pathlib.Path) -> set[str]:
    paths = set()
    for collection in (result.contract_docs, result.source_annotations, result.usage_markers):
        for path in collection:
            paths.add(relative(path, root).lower())
    return paths


def registered_but_not_discovered(result: ScanResult, root: pathlib.Path) -> list[RegistryEntry]:
    discovered = discovered_paths(result, root)
    missing: list[RegistryEntry] = []
    for entry in result.registry_entries:
        source = entry.source.lower().replace("\\", "/")
        if source.startswith("`@dottalk.contract`") and result.source_annotations:
            continue
        if source and source not in discovered:
            missing.append(entry)
    return missing


def counts(result: ScanResult) -> dict[str, int]:
    return {
        "contract_like_docs": len(result.contract_docs),
        "source_contract_annotation_files": len(result.source_annotations),
        "source_usage_marker_files": len(result.usage_markers),
        "registry_rows": len(result.registry_entries),
    }


def to_json_payload(result: ScanResult, root: pathlib.Path) -> dict[str, object]:
    unregistered = likely_unregistered_docs(result, root)
    missing = registered_but_not_discovered(result, root)
    return {
        "root": str(root),
        "counts": counts(result),
        "likely_unregistered_contract_docs": [relative(path, root) for path in unregistered],
        "source_contract_annotation_files": [relative(path, root) for path in result.source_annotations],
        "usage_marker_files": [relative(path, root) for path in result.usage_markers],
        "registry_entries": [
            {"name": entry.name, "kind": entry.kind, "source": entry.source}
            for entry in result.registry_entries
        ],
        "registered_but_not_discovered": [
            {"name": entry.name, "kind": entry.kind, "source": entry.source}
            for entry in missing
        ],
    }


def print_counts(result: ScanResult, root: pathlib.Path) -> None:
    result_counts = counts(result)
    print(f"root={root}")
    for key, value in result_counts.items():
        print(f"{key}={value}")
    print(f"likely_unregistered_contract_docs={len(likely_unregistered_docs(result, root))}")
    print(f"registered_but_not_discovered={len(registered_but_not_discovered(result, root))}")


def print_report(result: ScanResult, root: pathlib.Path) -> None:
    print("# Contract Lane Scan")
    print()
    print(f"Root: `{root}`")
    print()
    print("## Counts")
    print()
    print(f"- contract-like docs: {len(result.contract_docs)}")
    print(f"- source `@dottalk.contract` files: {len(result.source_annotations)}")
    print(f"- source usage-marker files: {len(result.usage_markers)}")
    print(f"- registry rows: {len(result.registry_entries)}")
    print()

    unregistered = likely_unregistered_docs(result, root)
    missing = registered_but_not_discovered(result, root)

    print("## Likely Unregistered Contract Docs")
    print()
    if not unregistered:
        print("- none detected")
    else:
        for path in unregistered[:100]:
            print(f"- `{relative(path, root)}`")
        if len(unregistered) > 100:
            print(f"- ... {len(unregistered) - 100} more")
    print()

    print("## Registered But Not Discovered")
    print()
    if not missing:
        print("- none detected")
    else:
        for entry in missing[:100]:
            print(f"- `{entry.name}` -> `{entry.source}`")
        if len(missing) > 100:
            print(f"- ... {len(missing) - 100} more")
    print()

    print("## Source Contract Annotation Files")
    print()
    if not result.source_annotations:
        print("- none detected")
    else:
        for path in result.source_annotations[:100]:
            print(f"- `{relative(path, root)}`")
        if len(result.source_annotations) > 100:
            print(f"- ... {len(result.source_annotations) - 100} more")
    print()

    print("## Usage Marker Files")
    print()
    if not result.usage_markers:
        print("- none detected")
    else:
        for path in result.usage_markers[:100]:
            print(f"- `{relative(path, root)}`")
        if len(result.usage_markers) > 100:
            print(f"- ... {len(result.usage_markers) - 100} more")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan contract-like docs and source markers.")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--format", choices={"markdown", "summary", "json"}, default="markdown")
    parser.add_argument("--markdown", action="store_true", help="Print the full Markdown report.")
    parser.add_argument("--summary", action="store_true", help="Print compact key=value counts.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    root = repo_root(args.root)
    result = scan(root)
    output_format = args.format
    if args.markdown:
        output_format = "markdown"
    if args.summary:
        output_format = "summary"
    if args.json:
        output_format = "json"

    if output_format == "summary":
        print_counts(result, root)
    elif output_format == "json":
        print(json.dumps(to_json_payload(result, root), indent=2))
    else:
        print_report(result, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
