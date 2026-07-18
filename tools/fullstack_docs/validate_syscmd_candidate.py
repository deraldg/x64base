from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


FIELDS = ["CMD_ID", "CAN_NAME", "TYPE", "VIS", "HANDLER", "ACTIVE"]
LENGTHS = {"CMD_ID": 32, "CAN_NAME": 80, "TYPE": 20, "VIS": 20, "HANDLER": 96}
REGISTRY_PATTERNS = [
    re.compile(r'registry\s*\(\s*\)\s*\.\s*add\s*\(\s*"([^"]+)"'),
    re.compile(r'register_(?:extension_)?command\s*\(\s*"([^"]+)"'),
]


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper())


def compact(value: str) -> str:
    return re.sub(r"[\s_-]+", "", normalize(value))


def symbol(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^A-Z0-9]+", "_", normalize(value))).strip("_")


def mask_cpp_comments(text: str) -> str:
    output = list(text)
    state = "normal"
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if state == "normal":
            if char == "/" and following == "/":
                output[index] = output[index + 1] = " "
                index += 1
                state = "line"
            elif char == "/" and following == "*":
                output[index] = output[index + 1] = " "
                index += 1
                state = "block"
            elif char == '"':
                state = "string"
                escaped = False
            elif char == "'":
                state = "character"
                escaped = False
        elif state == "line":
            if char == "\n":
                state = "normal"
            else:
                output[index] = " "
        elif state == "block":
            if char == "*" and following == "/":
                output[index] = output[index + 1] = " "
                index += 1
                state = "normal"
            elif char not in "\r\n":
                output[index] = " "
        else:
            quote = '"' if state == "string" else "'"
            if not escaped and char == quote:
                state = "normal"
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
        index += 1
    return "".join(output)


def registry_compact_names(repo_root: Path) -> set[str]:
    names: set[str] = set()
    for path in sorted((repo_root / "src").rglob("*.cpp")):
        text = mask_cpp_comments(path.read_text(encoding="utf-8", errors="replace"))
        for pattern in REGISTRY_PATTERNS:
            names.update(compact(match.group(1)) for match in pattern.finditer(text))
    return names


def validate_rows(rows: list[dict[str, str]], repo_root: Path | None = None) -> list[str]:
    findings: list[str] = []
    ids = Counter(row.get("CMD_ID", "") for row in rows)
    names = Counter(row.get("CAN_NAME", "") for row in rows)
    backing = registry_compact_names(repo_root) if repo_root else None

    for index, row in enumerate(rows, 2):
        for field in FIELDS:
            if field not in row:
                findings.append(f"ROW_{index}:FIELD_MISSING:{field}")
        if findings and any(item.startswith(f"ROW_{index}:FIELD_MISSING") for item in findings):
            continue

        for field, limit in LENGTHS.items():
            if len(row[field]) > limit:
                findings.append(f"ROW_{index}:FIELD_LENGTH:{field}:{len(row[field])}>{limit}")
        canonical = normalize(row["CAN_NAME"])
        if row["CAN_NAME"] != canonical:
            findings.append(f"ROW_{index}:CAN_NAME_NORMALIZATION:{row['CAN_NAME']}")
        expected_id = f"CMD_{symbol(canonical)}"
        if row["CMD_ID"] != expected_id:
            findings.append(f"ROW_{index}:CMD_ID_PROJECTION:{row['CMD_ID']}!={expected_id}")
        if row["TYPE"] not in {"command", "syntax-command"}:
            findings.append(f"ROW_{index}:TYPE_VALUE:{row['TYPE']}")
        if row["VIS"] not in {"public", "developer"}:
            findings.append(f"ROW_{index}:VIS_VALUE:{row['VIS']}")
        if not row["HANDLER"].strip():
            findings.append(f"ROW_{index}:HANDLER_EMPTY")
        if row["ACTIVE"].strip().lower() not in {"t", "true", "1", "y", "yes"}:
            findings.append(f"ROW_{index}:ACTIVE_NOT_TRUE:{row['ACTIVE']}")
        if backing is not None and compact(canonical) not in backing:
            findings.append(f"ROW_{index}:STATIC_REGISTRY_BACKING_MISSING:{canonical}")

    findings.extend(f"CMD_ID_DUPLICATE:{key}:{count}" for key, count in ids.items() if key and count > 1)
    findings.extend(f"CAN_NAME_DUPLICATE:{key}:{count}" for key, count in names.items() if key and count > 1)
    return findings


def read_candidate(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a report-only metacollect SYSCMD candidate.")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args()

    fields, rows = read_candidate(args.candidate)
    findings = [] if fields == FIELDS else [f"HEADER_MISMATCH:{fields!r}"]
    findings.extend(validate_rows(rows, args.repo_root.resolve() if args.repo_root else None))
    for finding in findings:
        print(f"SYSCMDCHK {finding}")
    if findings:
        print(f"SYSCMDCHK FAIL rows={len(rows)} findings={len(findings)}")
        return 1
    print(f"SYSCMDCHK OK rows={len(rows)} findings=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
