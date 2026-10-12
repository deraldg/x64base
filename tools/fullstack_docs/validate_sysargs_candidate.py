"""Validate a report-only metacollect SYSARGS candidate.

Sibling of validate_syscmd_candidate.py. Governed by
docs/maintenance/lanes/full_stack_documentation/METACOLLECT_SYSARGS_CANDIDATE_CONTRACT_V1.md

Candidate v2 uses ARG:COMMAND:<owner>:<kind>:<name>. Legacy duplicate IDs remain rejected; no live rows are renamed by this validator.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


FIELDS = [
    "ARG_ID", "OWNER_KND", "OWNER_NAM", "ARG_NAME", "DEF_LOCALE", "REGION_ID",
    "ARG_KIND", "VAL_SHAPE", "REQUIRED", "REPEAT", "SRC_AUTH", "SRC_FILE",
    "ACTIVE", "VER_AT", "NOTES",
]

# metacollect.cpp: the keyword branch sets val_shape "literal"; the placeholder
# branch returns one of the other ten from infer_shape_from_placeholder.
# Widening either set is a contract change, not a validator change.
ARG_KINDS = {"keyword", "placeholder"}
KEYWORD_SHAPE = "literal"
PLACEHOLDER_SHAPES = {
    "expression", "field-name", "file-path", "integer", "locale-code",
    "name", "path", "predicate", "table-ref", "value",
}
VAL_SHAPES = PLACEHOLDER_SHAPES | {KEYWORD_SHAPE}
BOOLEANS = {"true", "false"}
SRC_AUTHORITY = "usage_contract_v1"
PHYSICAL_CONTRACT = Path(__file__).resolve().parents[2] / "docs/datadict/schemas/sysargs_catalog_candidate_v2.dtschema"


def candidate_widths() -> dict[str, int]:
    return {name: int(width) for name, width in re.findall(
        r"^\s+(\w+) TYPE=C LEN=(\d+)", PHYSICAL_CONTRACT.read_text(encoding="utf-8"), re.M)}


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper())


def symbol(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^A-Z0-9]+", "_", normalize(value))).strip("_")


def syscmd_names(path: Path) -> set[str]:
    """CAN_NAME values from a SYSCMD candidate emitted by the same run."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row.get("CAN_NAME", "") for row in csv.DictReader(handle)}


def validate_rows(
    rows: list[dict[str, str]],
    repo_root: Path | None = None,
    owner_names: set[str] | None = None,
) -> list[str]:
    findings: list[str] = []
    ids = Counter(row.get("ARG_ID", "") for row in rows)

    for index, row in enumerate(rows, 2):
        missing = [field for field in FIELDS if field not in row]
        if missing:
            findings.extend(f"ROW_{index}:FIELD_MISSING:{field}" for field in missing)
            continue

        if row["OWNER_KND"] != "command":
            findings.append(f"ROW_{index}:OWNER_KND_VALUE:{row['OWNER_KND']}")
        if not row["OWNER_NAM"].strip():
            findings.append(f"ROW_{index}:OWNER_NAM_EMPTY")
        if not row["ARG_NAME"].strip():
            findings.append(f"ROW_{index}:ARG_NAME_EMPTY")

        expected_id = "ARG:COMMAND:" + " ".join(row['OWNER_NAM'].upper().split()) + ":" + row['ARG_KIND'].upper() + ":" + row['ARG_NAME']
        if row["ARG_ID"] != expected_id:
            findings.append(f"ROW_{index}:ARG_ID_PROJECTION:{row['ARG_ID']}!={expected_id}")

        if row["ARG_KIND"] not in ARG_KINDS:
            findings.append(f"ROW_{index}:ARG_KIND_VALUE:{row['ARG_KIND']}")
        if row["VAL_SHAPE"] not in VAL_SHAPES:
            findings.append(f"ROW_{index}:VAL_SHAPE_VALUE:{row['VAL_SHAPE']}")
        elif row["ARG_KIND"] == "keyword" and row["VAL_SHAPE"] != KEYWORD_SHAPE:
            findings.append(f"ROW_{index}:KEYWORD_SHAPE:{row['VAL_SHAPE']}")
        elif row["ARG_KIND"] == "placeholder" and row["VAL_SHAPE"] == KEYWORD_SHAPE:
            findings.append(f"ROW_{index}:PLACEHOLDER_SHAPE_LITERAL")

        for field in ("REQUIRED", "REPEAT", "ACTIVE"):
            if row[field].strip().lower() not in BOOLEANS:
                findings.append(f"ROW_{index}:{field}_NOT_BOOLEAN:{row[field]}")
        if row["ACTIVE"].strip().lower() != "true":
            findings.append(f"ROW_{index}:ACTIVE_NOT_TRUE:{row['ACTIVE']}")

        if row["SRC_AUTH"] != SRC_AUTHORITY:
            findings.append(f"ROW_{index}:SRC_AUTH_VALUE:{row['SRC_AUTH']}")
        if not row["SRC_FILE"].strip():
            findings.append(f"ROW_{index}:SRC_FILE_EMPTY")
        elif repo_root is not None and not (repo_root / row["SRC_FILE"]).exists():
            findings.append(f"ROW_{index}:SRC_FILE_MISSING:{row['SRC_FILE']}")

        if owner_names is not None and row["OWNER_NAM"] not in owner_names:
            findings.append(f"ROW_{index}:OWNER_NOT_IN_SYSCMD:{row['OWNER_NAM']}")

    findings.extend(
        f"ARG_ID_DUPLICATE:{key}:{count}"
        for key, count in sorted(ids.items())
        if key and count > 1
    )

    owners = [row.get("OWNER_NAM", "") for row in rows]
    if owners != sorted(owners):
        findings.append("OWNER_NAM_ORDER_NOT_GROUPED")

    return findings


def read_candidate(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a report-only metacollect SYSARGS candidate."
    )
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument(
        "--syscmd-candidate",
        type=Path,
        help="SYSCMD candidate from the SAME emit; every OWNER_NAM must have a row there.",
    )
    args = parser.parse_args()

    fields, rows = read_candidate(args.candidate)
    findings = [] if fields == FIELDS else [f"HEADER_MISMATCH:{fields!r}"]
    findings.extend(
        validate_rows(
            rows,
            args.repo_root.resolve() if args.repo_root else None,
            syscmd_names(args.syscmd_candidate) if args.syscmd_candidate else None,
        )
    )
    for index, row in enumerate(rows, 2):
        for field, width in candidate_widths().items():
            if len(row[field].encode("utf-8")) > width:
                findings.append(f"ROW_{index}:{field}_EXCEEDS_X64_BYTE_WIDTH:{width}")
    for finding in findings:
        print(f"SYSARGSCHK {finding}")
    if findings:
        print(f"SYSARGSCHK FAIL rows={len(rows)} findings={len(findings)}")
        return 1
    print(f"SYSARGSCHK OK rows={len(rows)} findings=0 owner_check={'same-run' if args.syscmd_candidate else 'NOT_RUN'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
