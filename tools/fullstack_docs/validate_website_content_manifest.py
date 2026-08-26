#!/usr/bin/env python3
"""Validate that the website content manifest classifies every MDX page once."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import yaml


CLASSES = {
    "generated",
    "derived",
    "maintained",
    "maintained_current",
    "reported",
    "static",
}


def page_path(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("path"), str):
        return value["path"]
    raise ValueError(f"invalid page declaration: {value!r}")


def validate(manifest: Path, content_root: Path) -> list[str]:
    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    classes = data.get("classes")
    findings: list[str] = []
    if not isinstance(classes, dict):
        return ["manifest classes must be a mapping"]
    unknown_classes = sorted(set(classes) - CLASSES)
    missing_classes = sorted(CLASSES - set(classes))
    if unknown_classes:
        findings.append("unknown classes: " + ", ".join(unknown_classes))
    if missing_classes:
        findings.append("missing classes: " + ", ".join(missing_classes))

    declared: list[tuple[str, str]] = []
    for class_name, spec in classes.items():
        if not isinstance(spec, dict) or not isinstance(spec.get("pages"), list):
            findings.append(f"{class_name} pages must be a list")
            continue
        for value in spec["pages"]:
            try:
                declared.append((class_name, page_path(value)))
            except ValueError as exc:
                findings.append(str(exc))

    counts = Counter(path for _class_name, path in declared)
    duplicates = sorted(path for path, count in counts.items() if count != 1)
    if duplicates:
        findings.append("duplicate declarations: " + ", ".join(duplicates))

    actual = {
        path.relative_to(content_root).as_posix()[:-4]
        for path in content_root.rglob("*.mdx")
    }
    declared_set = set(counts)
    missing = sorted(actual - declared_set)
    phantom = sorted(declared_set - actual)
    if missing:
        findings.append("pages missing from manifest: " + ", ".join(missing))
    if phantom:
        findings.append("manifest pages missing on disk: " + ", ".join(phantom))

    measured = Counter(class_name for class_name, _path in declared)
    totals = data.get("totals") or {}
    for class_name in sorted(CLASSES):
        if totals.get(class_name) != measured[class_name]:
            findings.append(
                f"total {class_name}: declared {totals.get(class_name)!r} "
                f"!= measured {measured[class_name]}"
            )
    if totals.get("total") != len(declared):
        findings.append(
            f"total: declared {totals.get('total')!r} != measured {len(declared)}"
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--content-root", type=Path, required=True)
    args = parser.parse_args()
    findings = validate(args.manifest.resolve(), args.content_root.resolve())
    if findings:
        print("website-content-manifest: FAIL")
        for finding in findings:
            print(f"  - {finding}")
        return 2
    data = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    print(
        "website-content-manifest: PASS -- "
        f"{data['totals']['total']} pages classified exactly once"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
